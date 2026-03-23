from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.activity import Activity
from backend.models.health import DailySteps, HeartRate, SleepRecord

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_activities = db.query(func.count(Activity.id)).scalar() or 0
    total_distance = db.query(func.sum(Activity.distance_meters)).scalar() or 0
    avg_steps = db.query(func.avg(DailySteps.steps)).scalar()
    resting_hr = (
        db.query(func.avg(HeartRate.bpm))
        .filter(HeartRate.bpm.between(40, 100))
        .scalar()
    )
    avg_sleep = db.query(func.avg(SleepRecord.total_minutes)).scalar()

    # Personal records
    best_steps = db.query(func.max(DailySteps.steps)).scalar() or 0
    longest_run = (
        db.query(func.max(Activity.distance_meters))
        .filter(Activity.activity_type == "run")
        .scalar()
        or 0
    )
    best_sleep = db.query(func.max(SleepRecord.total_minutes)).scalar() or 0

    return {
        "total_activities": total_activities,
        "total_distance_km": round((total_distance or 0) / 1000, 1),
        "avg_daily_steps": round(avg_steps) if avg_steps else None,
        "resting_hr": round(resting_hr) if resting_hr else None,
        "avg_sleep_hours": round((avg_sleep or 0) / 60, 1) if avg_sleep else None,
        "records": {
            "best_step_day": best_steps,
            "longest_run_km": round((longest_run or 0) / 1000, 2),
            "best_sleep_hours": round((best_sleep or 0) / 60, 1),
        },
    }


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


@router.get("/weekly")
def get_weekly(weeks: int = 8, db: Session = Depends(get_db)):
    today = date.today()
    result = []

    for i in range(weeks - 1, -1, -1):
        ws = _week_start(today) - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        label = ws.strftime("%b %d")

        acts = db.query(Activity).filter(Activity.date >= ws, Activity.date <= we).all()
        steps_rows = db.query(DailySteps).filter(DailySteps.date >= ws, DailySteps.date <= we).all()

        total_dist = sum((a.distance_meters or 0) for a in acts) / 1000
        total_steps = sum((s.steps or 0) for s in steps_rows)
        active_days = len(set(a.date for a in acts) | set(s.date for s in steps_rows if (s.steps or 0) > 500))

        result.append({
            "week": label,
            "week_start": ws.isoformat(),
            "activities": len(acts),
            "distance_km": round(total_dist, 1),
            "total_steps": total_steps,
            "active_days": active_days,
        })

    return result


@router.get("/monthly")
def get_monthly(months: int = 6, db: Session = Depends(get_db)):
    today = date.today()
    result = []

    for i in range(months - 1, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        ms = date(year, month, 1)
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        me = date(next_year, next_month, 1) - timedelta(days=1)

        acts = db.query(Activity).filter(Activity.date >= ms, Activity.date <= me).all()
        steps_rows = db.query(DailySteps).filter(DailySteps.date >= ms, DailySteps.date <= me).all()
        sleep_rows = db.query(SleepRecord).filter(SleepRecord.date >= ms, SleepRecord.date <= me).all()

        total_dist = sum((a.distance_meters or 0) for a in acts) / 1000
        total_steps = sum((s.steps or 0) for s in steps_rows)
        avg_sleep = (
            sum((s.total_minutes or 0) for s in sleep_rows) / len(sleep_rows) / 60
            if sleep_rows else None
        )

        result.append({
            "month": ms.strftime("%b %Y"),
            "month_start": ms.isoformat(),
            "activities": len(acts),
            "distance_km": round(total_dist, 1),
            "total_steps": total_steps,
            "avg_sleep_hours": round(avg_sleep, 1) if avg_sleep else None,
        })

    return result
