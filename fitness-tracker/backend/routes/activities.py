from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.activity import Activity

router = APIRouter(prefix="/api/activities", tags=["activities"])


def _fmt(a: Activity, include_gpx=False) -> dict:
    d = {
        "id": a.id,
        "source": a.source,
        "date": a.date.isoformat(),
        "activity_type": a.activity_type,
        "duration_seconds": a.duration_seconds,
        "distance_meters": a.distance_meters,
        "avg_heart_rate": a.avg_heart_rate,
        "calories": a.calories,
    }
    if include_gpx:
        d["gpx_points"] = a.gpx_points
    return d


@router.get("")
def list_activities(
    source: Optional[str] = None,
    type: Optional[str] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Activity)
    if source:
        q = q.filter(Activity.source == source)
    if type:
        q = q.filter(Activity.activity_type == type)
    if from_date:
        q = q.filter(Activity.date >= from_date)
    if to_date:
        q = q.filter(Activity.date <= to_date)

    total = q.count()
    items = q.order_by(Activity.date.desc()).offset((page - 1) * limit).limit(limit).all()

    return {"total": total, "page": page, "limit": limit, "items": [_fmt(a) for a in items]}


@router.get("/{activity_id}")
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    a = db.query(Activity).filter(Activity.id == activity_id).first()
    if not a:
        raise HTTPException(404, "Activity not found")
    return _fmt(a, include_gpx=True)
