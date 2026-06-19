# Financial Calculations Engine

> ## NOTE
> **The code in this repository is a demonstration of the architecture and is not a working engine.**
> All field names, entities, and accounting rules have been deliberately abstracted. Do not assume
> the math here is correct for any real ledger — it isn't meant to be. Treat the files as a
> blueprint for the moving parts (FastAPI + ledger walker + nightly backfill), not as code you can
> deploy against real money.

---

## What this project demonstrates

A FastAPI service that walks a ledger of financial events and answers two kinds of question:

1. **"What's the running balance at time T?"** — point-in-time queries served from a cached
   running-total table.
2. **"Did anything drift overnight?"** — a daily backfill job that re-derives the day's totals
   from raw events and reconciles them against the cached running totals.

The structure separates three concerns cleanly:

- **API layer** (`api/`) — typed in/out, no math.
- **Service layer** (`services/`) — the running-balance walker and the backfill comparator.
- **Persistence layer** (`models.py`) — abstract ledger tables.

The same engine answers both ad-hoc reads (fast) and nightly audits (thorough).

## High-level diagram

```
   ┌────────────────────┐        ┌──────────────────┐
   │ /balance/at?ts=... │ ─────► │ RunningBalance   │ ──► running_totals
   └────────────────────┘        │ (walker service) │      ▲
                                 └──────────────────┘      │
                                                           │ writes
   ┌────────────────────┐        ┌──────────────────┐      │
   │ POST /backfill/day │ ─────► │ Backfill Service │ ─────┘
   └────────────────────┘        └──────────────────┘
                                            │
                                            ▼
                                  re-derives day totals,
                                  flags drift, repairs running_totals
```

## Files in this showcase

| File | What it shows |
|------|---------------|
| `app/main.py`                          | FastAPI wiring, lifespan, router mount, cron startup. |
| `app/config.py`                        | Settings via pydantic. |
| `app/database.py`                      | SQLAlchemy engine + session factory. |
| `app/models.py`                        | Abstract ledger tables. |
| `app/api/running_balance.py`           | Point-in-time read endpoints. |
| `app/api/backfill_api.py`              | Triggered + scheduled backfill endpoints. |
| `app/services/running_balance_service.py` | The walker — folds events into totals. |
| `app/services/backfill_service.py`     | Re-derives a day, diffs against cache, repairs drift. |
| `app/cron_jobs.py`                     | APScheduler bindings. |
| `requirements.txt`                     | Unpinned dependency surface. |
