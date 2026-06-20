import asyncio
import pandas as pd
from typing import List, Optional
from .ccxt_client import fetch_ohlcv, fetch_open_interest
from .scoring import score_evidence
from .utils import make_fingerprint, calc_rr
from .telegram_notify import send_signal_message
from .db import AsyncSessionLocal
from .models import Signal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import aioredis
import os
from dotenv import load_dotenv
from .detectors_body_fvg import get_active_body_fvg_zones

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MIN_CONFIDENCE = int(os.getenv("MIN_CONFIDENCE", "75"))

redis = None

async def ensure_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(REDIS_URL)

def detect_htf_alignment_from_bars(htf_bars: list) -> Optional[str]:
    try:
        closes = [b[4] for b in htf_bars[-50:]]
        if len(closes) < 5:
            return None
        first_mean = sum(closes[:len(closes)//2]) / max(1, len(closes)//2)
        last_mean = sum(closes[len(closes)//2:]) / max(1, len(closes)//2)
        return "LONG" if last_mean > first_mean else "SHORT"
    except Exception:
        return None

async def process_symbol(exchange_name: str, symbol: str, htf: str, ltf: str):
    try:
        htf_bars = await fetch_ohlcv(exchange_name, symbol, htf, limit=300)
        ltf_bars = await fetch_ohlcv(exchange_name, symbol, ltf, limit=500)
    except Exception as e:
        print(f"[scanner] fetch error {symbol} {htf}/{ltf}: {e}")
        return None

    if not ltf_bars or not htf_bars:
        return None

    htf_alignment = detect_htf_alignment_from_bars(htf_bars)

    cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    try:
        ltf_df = pd.DataFrame(ltf_bars, columns=cols)
    except Exception:
        cols_short = ['timestamp', 'open', 'high', 'low', 'close']
        ltf_df = pd.DataFrame(ltf_bars, columns=cols_short)
        ltf_df['volume'] = None

    ltf_df['datetime'] = pd.to_datetime(ltf_df['timestamp'], unit='ms', errors='coerce')
    ltf_df = ltf_df.set_index('datetime')

    active_body_fvgs = get_active_body_fvg_zones(
        ltf_df,
        lookback_bars=300,
        min_size=0.0,
        min_size_pct=None,
        use_wicks_for_fill=True,
    )
    has_fvg = len(active_body_fvgs) > 0

    order_block = False
    liquidity_sweep = False
    mss = False
    cvd = False
    oi = None
    try:
        oi = await fetch_open_interest(exchange_name, symbol)
    except Exception:
        oi = None

    side = "SELL" if htf_alignment == "SHORT" else "BUY"
    try:
        entry = float(ltf_bars[-1][4])
    except Exception:
        return None

    if has_fvg:
        z = active_body_fvgs[-1]
        if z['type'] == 'bull':
            side = "BUY"
            stop = z['zone_bottom'] - (z['size'] * 0.25)
            tp = entry + (entry - stop) * 3
        else:
            side = "SELL"
            stop = z['zone_top'] + (z['size'] * 0.25)
            tp = entry - (stop - entry) * 3
    else:
        if side == "BUY":
            stop = entry * 0.99
            tp = entry * 1.03
        else:
            stop = entry * 1.01
            tp = entry * 0.97

    rr = calc_rr(entry, stop, tp, side)

    evidence = {
        "htf_alignment": htf_alignment,
        "liquidity_sweep": liquidity_sweep,
        "order_block": order_block,
        "fvg": has_fvg,
        "fvg_zones": active_body_fvgs,
        "mss": mss,
        "cvd": cvd,
        "oi_confirmation": bool(oi),
        "rr": rr,
    }

    scoring = score_evidence(evidence)
    confidence = scoring["confidence"]
    if confidence < MIN_CONFIDENCE:
        return None

    signal_payload = {
        "asset": symbol.replace("/", ""),
        "timeframe": ltf,
        "side": side,
        "entry": round(entry, 8),
        "stop_loss": round(stop, 8),
        "take_profit": round(tp, 8),
        "rr": rr,
        "confidence": confidence,
        "quality": scoring["quality"],
        "htf_context": htf_alignment,
        "htf_zone": "FVG Zone" if has_fvg else None,
        "ltf_trigger": "FVG Unfilled" if has_fvg else None,
        "liquidity_taken": None,
        "reason": scoring["reasons"],
        "raw": {
            "htf_bars_len": len(htf_bars),
            "ltf_bars_len": len(ltf_bars),
            "fvg_zones": active_body_fvgs,
            "evidence": evidence,
        },
    }

    fingerprint = make_fingerprint(signal_payload)
    signal_payload["fingerprint"] = fingerprint

    await ensure_redis()
    redis_key = f"signal_fingerprint:{fingerprint}"
    if await redis.get(redis_key):
        return None
    await redis.set(redis_key, "1", ex=24*3600)

    async with AsyncSessionLocal() as session:
        stmt = select(Signal).where(Signal.fingerprint == fingerprint)
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return None

        signal = Signal(
            asset=signal_payload["asset"],
            timeframe=signal_payload["timeframe"],
            side=signal_payload["side"],
            entry=signal_payload["entry"],
            stop_loss=signal_payload["stop_loss"],
            take_profit=signal_payload["take_profit"],
            rr=signal_payload["rr"],
            confidence=signal_payload["confidence"],
            quality=signal_payload["quality"],
            htf_context=signal_payload.get("htf_context"),
            htf_zone=signal_payload.get("htf_zone"),
            ltf_trigger=signal_payload.get("ltf_trigger"),
            liquidity_taken=signal_payload.get("liquidity_taken"),
            reason=signal_payload.get("reason"),
            raw=signal_payload.get("raw"),
            fingerprint=fingerprint,
            notified=False,
        )
        session.add(signal)
        try:
            await session.commit()
            await session.refresh(signal)
        except IntegrityError:
            await session.rollback()
            return None

        try:
            ok = await send_signal_message({
                "asset": signal.asset,
                "timeframe": signal.timeframe,
                "side": signal.side,
                "entry": signal.entry,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "rr": signal.rr,
                "confidence": signal.confidence,
                "quality": signal.quality,
                "htf_context": signal.htf_context,
                "htf_zone": signal.htf_zone,
                "ltf_trigger": signal.ltf_trigger,
                "liquidity_taken": signal.liquidity_taken,
                "reason": signal.reason or [],
            })
            if ok:
                signal.notified = True
                session.add(signal)
                await session.commit()
        except Exception as e:
            print(f"[scanner] telegram notify failed: {e}")

    return signal_payload

async def run_scan_once():
    EXCHANGE_KEYS = ["binance", "bybit"]
    ASSETS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "LINK/USDT", "XRP/USDT", "BNB/USDT"]
    PAIRS = [("D","H1"), ("H4","M15"), ("D","M5")]

    tasks = []
    for exchange in EXCHANGE_KEYS:
        for symbol in ASSETS:
            for htf, ltf in PAIRS:
                tasks.append(process_symbol(exchange, symbol, htf, ltf))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    created = sum(1 for r in results if r and not isinstance(r, Exception))
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        print(f"[scanner] errors: {len(errors)}")
    return {"created": created, "errors": len(errors)}
