"""
Daily backfill (sketch).

For a given day, re-derives the running total directly from `ledger_events`
and compares it to whatever the cache currently says. If they disagree,
write a DriftReport and (optionally) repair the cached row.
"""
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models import LedgerEvent, RunningTotal, DriftReport


class BackfillService:
    def __init__(self, db: Session):
        self._db = db

    def run_day(self, day: date, account_ref: Optional[str], *, repair: bool):
        targets = [account_ref] if account_ref else self._all_accounts()
        out = []
        for a in targets:
            out.append(self._one(a, day, repair=repair))
        return {"day": day.isoformat(), "rows": out}

    def run_range(self, start: date, end: date, account_ref: Optional[str], *, repair: bool):
        out = []
        d = start
        while d <= end:
            out.append(self.run_day(d, account_ref, repair=repair))
            d += timedelta(days=1)
        return out

    # ── internals ────────────────────────────────────────────────────────────
    def _one(self, account_ref: str, day: date, *, repair: bool):
        expected = self._sum_for_day(account_ref, day)
        actual_row = self._cached_for_day(account_ref, day)
        actual = actual_row.total if actual_row else 0.0
        delta = expected - actual
        report = DriftReport(
            account_ref=account_ref, as_of_date=datetime.combine(day, datetime.min.time()),
            expected=expected, actual=actual, delta=delta, repaired=0,
        )
        if repair and abs(delta) > 1e-9:
            if actual_row is None:
                actual_row = RunningTotal(account_ref=account_ref,
                                          as_of_date=report.as_of_date,
                                          total=expected, last_event_id=0)
                self._db.add(actual_row)
            else:
                actual_row.total = expected
            report.repaired = 1
        self._db.add(report)
        self._db.commit()
        return {"account_ref": account_ref, "delta": delta, "repaired": bool(report.repaired)}

    def _sum_for_day(self, account_ref: str, day: date) -> float:
        start = datetime.combine(day, datetime.min.time())
        end   = start + timedelta(days=1)
        v = self._db.execute(
            select(func.coalesce(func.sum(LedgerEvent.amount), 0.0))
            .where(LedgerEvent.account_ref == account_ref)
            .where(LedgerEvent.occurred_at >= start)
            .where(LedgerEvent.occurred_at <  end)
        ).scalar_one()
        return float(v)

    def _cached_for_day(self, account_ref: str, day: date):
        return self._db.execute(
            select(RunningTotal)
            .where(RunningTotal.account_ref == account_ref)
            .where(func.date(RunningTotal.as_of_date) == day)
            .limit(1)
        ).scalar_one_or_none()

    def _all_accounts(self):
        return self._db.execute(
            select(LedgerEvent.account_ref).distinct()
        ).scalars().all()
