"""
Financial calculations engine — sketch entrypoint.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.api.running_balance import router as balance_router
from app.api.backfill_api import router as backfill_router
from app.cron_jobs import scheduler, register_jobs

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    register_jobs(scheduler)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sketch: ledger walker + nightly backfill.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(balance_router, prefix="/balance",  tags=["balance"])
app.include_router(backfill_router, prefix="/backfill", tags=["backfill"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": app.version}
