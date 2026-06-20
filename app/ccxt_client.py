import os
import ccxt
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

EXCHANGES = {}

def get_exchange(name: str):
    if name in EXCHANGES:
        return EXCHANGES[name]
    api_key = os.getenv(f"{name.upper()}_API_KEY")
    api_secret = os.getenv(f"{name.upper()}_API_SECRET")
    if name.lower() == "binance":
        ex = ccxt.binanceusdm({"apiKey": api_key, "secret": api_secret, "options": {"defaultType": "future"}, "enableRateLimit": True})
    elif name.lower() == "bybit":
        ex = ccxt.bybit({"apiKey": api_key, "secret": api_secret, "options": {"defaultType": "future"}, "enableRateLimit": True})
    else:
        raise ValueError("Unsupported exchange")
    EXCHANGES[name] = ex
    return ex

TIMEFRAME_MAP = {
    "W": "1w",
    "D": "1d",
    "H4": "4h",
    "H1": "1h",
    "M15": "15m",
    "M5": "5m",
}

async def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str, limit: int = 200):
    loop = asyncio.get_event_loop()
    ex = get_exchange(exchange_name)
    tf = TIMEFRAME_MAP.get(timeframe, timeframe)
    return await loop.run_in_executor(None, lambda: ex.fetch_ohlcv(symbol, tf, limit=limit))

async def fetch_open_interest(exchange_name: str, symbol: str):
    loop = asyncio.get_event_loop()
    ex = get_exchange(exchange_name)
    if hasattr(ex, "fetch_open_interest"):
        return await loop.run_in_executor(None, lambda: ex.fetch_open_interest(symbol))
    return None
