"""
Scheduler bindings (sketch).

Nightly the engine re-derives yesterday's totals for every account and
files drift reports. A second tick prunes the audit logs.
"""
import logging
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionFactory
from app.services.backfill_service import BackfillService

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def register_jobs(s: AsyncIOScheduler):
    s.add_job(_nightly_backfill, "cron", hour=2,  minute=15, id="backfill.nightly")
    s.add_job(_prune_drift,      "cron", hour=3,  minute=0,  id="drift.prune")


def _nightly_backfill():
    db = SessionFactory()
    try:
        BackfillService(db).run_day(date.today() - timedelta(days=1), None, repair=True)
    finally:
        db.close()


def _prune_drift():
    logger.info("would prune drift_reports older than 60d")
