"""
Point-in-time read endpoints (sketch).
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.running_balance_service import RunningBalanceService

router = APIRouter()


class BalanceReply(BaseModel):
    account_ref: str
    as_of: datetime
    total: float
    last_event_id: int


@router.get("/at", response_model=BalanceReply)
def balance_at(account_ref: str, ts: Optional[datetime] = None,
               db: Session = Depends(get_db)):
    svc = RunningBalanceService(db)
    snap = svc.point_in_time(account_ref, ts or datetime.utcnow())
    if snap is None:
        raise HTTPException(404, "no rows for that account")
    return BalanceReply(**snap)


@router.get("/series")
def balance_series(account_ref: str, days: int = 30,
                   db: Session = Depends(get_db)):
    svc = RunningBalanceService(db)
    return svc.daily_series(account_ref, days)
