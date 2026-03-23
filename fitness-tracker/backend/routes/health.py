from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.health import DailySteps, HeartRate, SleepRecord

router = APIRouter(prefix="/api/health", tags=["health"])


def _default_range():
    to = date.today()
    frm = to - timedelta(days=29)
    return frm, to


@router.get("/steps")
def get_steps(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    frm, to = from_date or _default_range()[0], to_date or _default_range()[1]
    rows = (
        db.query(DailySteps)
        .filter(DailySteps.date >= frm, DailySteps.date <= to)
        .order_by(DailySteps.date)
        .all()
    )
    return [
        {"date": r.date.isoformat(), "steps": r.steps, "calories": r.calories, "active_minutes": r.active_minutes}
        for r in rows
    ]


@router.get("/heartrate")
def get_heartrate(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    resolution: str = Query("daily", regex="^(raw|hourly|daily)$"),
    db: Session = Depends(get_db),
):
    frm, to = from_date or _default_range()[0], to_date or _default_range()[1]
    frm_dt = datetime.combine(frm, datetime.min.time())
    to_dt = datetime.combine(to, datetime.max.time())

    rows = (
        db.query(HeartRate)
        .filter(HeartRate.timestamp >= frm_dt, HeartRate.timestamp <= to_dt)
        .order_by(HeartRate.timestamp)
        .all()
    )

    if resolution == "raw":
        return [{"timestamp": r.timestamp.isoformat(), "bpm": r.bpm} for r in rows]

    # Aggregate by day
    buckets: dict[str, list[int]] = {}
    for r in rows:
        key = r.timestamp.date().isoformat() if resolution == "daily" else r.timestamp.strftime("%Y-%m-%dT%H:00")
        buckets.setdefault(key, []).append(r.bpm)

    return [
        {"time": k, "avg_bpm": round(sum(v) / len(v)), "min_bpm": min(v), "max_bpm": max(v)}
        for k, v in sorted(buckets.items())
    ]


@router.get("/sleep")
def get_sleep(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    frm, to = from_date or _default_range()[0], to_date or _default_range()[1]
    rows = (
        db.query(SleepRecord)
        .filter(SleepRecord.date >= frm, SleepRecord.date <= to)
        .order_by(SleepRecord.date)
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "total_minutes": r.total_minutes,
            "deep_minutes": r.deep_minutes,
            "light_minutes": r.light_minutes,
            "rem_minutes": r.rem_minutes,
            "awake_minutes": r.awake_minutes,
        }
        for r in rows
    ]
