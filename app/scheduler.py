from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .scanner import run_scan_once

scheduler = AsyncIOScheduler()

def start_scheduler(interval_seconds: int = 300):
    scheduler.add_job(run_scan_once, IntervalTrigger(seconds=interval_seconds), id="market_scanner", replace_existing=True)
    scheduler.start()
    print(f"[scheduler] started with interval {interval_seconds}s")

def stop_scheduler():
    scheduler.shutdown()
