import os
import asyncio
from fastapi import FastAPI
from typing import List
from .db import AsyncSessionLocal, engine, Base
from .models import Signal, Result, Statistic
from sqlalchemy import select, func
from .scheduler import start_scheduler
import uvicorn
from dotenv import load_dotenv
import aioredis

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="ICT SMART MONEY AI SIGNAL BOT")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))
    start_scheduler(interval_seconds=interval)
    app.state.redis = await aioredis.from_url(REDIS_URL)
    print("startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    redis = getattr(app.state, "redis", None)
    if redis:
        await redis.close()

@app.get("/signals")
async def list_signals(limit: int = 50):
    async with AsyncSessionLocal() as session:
        stmt = select(Signal).order_by(Signal.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        return [ {
            "id": str(r.id),
            "created_at": r.created_at,
            "asset": r.asset,
            "timeframe": r.timeframe,
            "side": r.side,
            "entry": r.entry,
            "stop_loss": r.stop_loss,
            "take_profit": r.take_profit,
            "rr": r.rr,
            "confidence": r.confidence,
            "quality": r.quality,
            "notified": r.notified,
        } for r in rows ]

@app.get("/performance")
async def performance(limit: int = 50):
    async with AsyncSessionLocal() as session:
        stmt = select(Result).order_by(Result.closed_at.desc()).limit(limit)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        return [ {
            "id": str(r.id),
            "signal_id": str(r.signal_id),
            "closed_at": r.closed_at,
            "exit_price": r.exit_price,
            "pnl": r.pnl,
            "rr_realized": r.rr_realized,
            "win": r.win,
        } for r in rows ]

@app.get("/stats")
async def stats():
    async with AsyncSessionLocal() as session:
        stmt = select(Statistic).order_by(Statistic.computed_at.desc()).limit(10)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        return [ {"period": r.period, "metrics": r.metrics, "computed_at": r.computed_at} for r in rows ]

@app.get("/winrate")
async def winrate(window_days: int = 7):
    async with AsyncSessionLocal() as session:
        stmt_total = select(func.count()).select_from(Result).where(Result.closed_at > func.now() - func.cast(f"interval '{window_days} days'", type_=func.now().__class__))
        stmt_wins = select(func.count()).select_from(Result).where(Result.closed_at > func.now() - func.cast(f"interval '{window_days} days'", type_=func.now().__class__)).where(Result.win == True)
        total_res = await session.execute(stmt_total)
        wins_res = await session.execute(stmt_wins)
        total = total_res.scalar() or 0
        wins = wins_res.scalar() or 0
        winrate = round((wins / total * 100), 2) if total > 0 else None
        return {"window_days": window_days, "total": total, "wins": wins, "winrate": winrate}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
