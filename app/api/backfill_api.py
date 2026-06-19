"""
Backfill API (sketch).

Two endpoints:
  POST /backfill/day   — re-derive a single day for one or all accounts
  POST /backfill/range — same, but for a date range
"""
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.backfill_service import BackfillService

router = APIRouter()


class DayRequest(BaseModel):
    day: date
    account_ref: Optional[str] = None  # None → all accounts
    repair: bool = True


class RangeRequest(BaseModel):
    start: date
    end:   date
    account_ref: Optional[str] = None
    repair: bool = True


@router.post("/day")
def backfill_day(req: DayRequest, db: Session = Depends(get_db)):
    if req.day > date.today():
        raise HTTPException(400, "cannot backfill the future")
    svc = BackfillService(db)
    report = svc.run_day(req.day, req.account_ref, repair=req.repair)
    return report


@router.post("/range")
def backfill_range(req: RangeRequest, db: Session = Depends(get_db)):
    if req.end < req.start:
        raise HTTPException(400, "end must be >= start")
    svc = BackfillService(db)
    return svc.run_range(req.start, req.end, req.account_ref, repair=req.repair)
