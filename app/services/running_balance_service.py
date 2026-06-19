"""
Running balance walker (sketch).

Two paths:
  - point_in_time(): start from the latest running_total ≤ ts, fold any
    events after `last_event_id` up to `ts`.
  - daily_series(): iterate the per-day running totals, padding gaps.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models import LedgerEvent, RunningTotal


class RunningBalanceService:
    def __init__(self, db: Session):
        self._db = db

    def point_in_time(self, account_ref: str, ts: datetime) -> Optional[dict]:
        anchor = self._latest_anchor(account_ref, ts)
        if anchor is None:
            return None
        delta = self._fold_events_since(account_ref, anchor.last_event_id, ts)
        return {
            "account_ref":   account_ref,
            "as_of":         ts,
            "total":         anchor.total + delta,
            "last_event_id": anchor.last_event_id,
        }

    def daily_series(self, account_ref: str, days: int):
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = self._db.execute(
            select(RunningTotal)
            .where(RunningTotal.account_ref == account_ref)
            .where(RunningTotal.as_of_date >= cutoff)
            .order_by(RunningTotal.as_of_date)
        ).scalars().all()
        return [
            {"day": r.as_of_date.date().isoformat(), "total": r.total}
            for r in rows
        ]

    # ── helpers ──────────────────────────────────────────────────────────────
    def _latest_anchor(self, account_ref: str, ts: datetime):
        return self._db.execute(
            select(RunningTotal)
            .where(RunningTotal.account_ref == account_ref)
            .where(RunningTotal.as_of_date <= ts)
            .order_by(desc(RunningTotal.as_of_date))
            .limit(1)
        ).scalar_one_or_none()

    def _fold_events_since(self, account_ref: str, last_event_id: int, ts: datetime):
        rows = self._db.execute(
            select(LedgerEvent.amount)
            .where(LedgerEvent.account_ref == account_ref)
            .where(LedgerEvent.id > last_event_id)
            .where(LedgerEvent.occurred_at <= ts)
        ).scalars().all()
        return float(sum(rows))
