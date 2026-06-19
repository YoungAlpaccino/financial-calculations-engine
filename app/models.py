"""
Abstract ledger tables (sketch).

These names are placeholders — your real domain has more columns and
different verbiage. The shape is what matters: an append-only event log
plus a denormalised running-total table the API reads from.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, DateTime, Index,
)
from app.database import Base


class LedgerEvent(Base):
    """Append-only. Never updated, only inserted."""
    __tablename__ = "ledger_events"
    id            = Column(BigInteger, primary_key=True)
    account_ref   = Column(String(64), index=True)
    kind          = Column(String(32), index=True)      # opaque category
    amount        = Column(Float)                       # signed delta
    occurred_at   = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_ledger_account_occurred", "account_ref", "occurred_at"),
    )


class RunningTotal(Base):
    """Denormalised — what the API reads."""
    __tablename__ = "running_totals"
    id            = Column(BigInteger, primary_key=True)
    account_ref   = Column(String(64), index=True)
    as_of_date    = Column(DateTime, index=True)        # day bucket
    total         = Column(Float)
    last_event_id = Column(BigInteger)                  # idempotency anchor


class DriftReport(Base):
    """Where the backfill writes its findings."""
    __tablename__ = "drift_reports"
    id            = Column(BigInteger, primary_key=True)
    account_ref   = Column(String(64), index=True)
    as_of_date    = Column(DateTime, index=True)
    expected      = Column(Float)
    actual        = Column(Float)
    delta         = Column(Float)
    repaired      = Column(Integer, default=0)
    reported_at   = Column(DateTime, default=datetime.utcnow)
