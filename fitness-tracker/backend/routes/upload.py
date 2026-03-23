import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from backend.database import get_db
from backend.models.activity import Activity
from backend.models.health import DailySteps, HeartRate, SleepRecord
from backend.parsers.mi_fitness import parse_mi_fitness_zip, preview_mi_fitness_zip
from backend.parsers.runkeeper import parse_runkeeper_zip, parse_gpx_folder_zip

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _save_upload(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename or "export")[1] or ".zip"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    return tmp.name


def _upsert_activities(db: Session, records: list[dict]) -> tuple[int, int]:
    added = skipped = 0
    for r in records:
        stmt = (
            insert(Activity)
            .values(**r)
            .on_conflict_do_nothing(index_elements=None)
        )
        # SQLite ON CONFLICT via unique constraint
        q = db.query(Activity).filter_by(source=r["source"], date=r["date"])
        if r["duration_seconds"] is not None:
            q = q.filter(Activity.duration_seconds == r["duration_seconds"])
        else:
            q = q.filter(Activity.activity_type == r["activity_type"])
        existing = q.first()
        if existing:
            skipped += 1
        else:
            db.add(Activity(**r))
            added += 1
    db.commit()
    return added, skipped


def _upsert_steps(db: Session, records: list[dict]) -> tuple[int, int]:
    added = skipped = 0
    for r in records:
        existing = db.query(DailySteps).filter_by(date=r["date"]).first()
        if existing:
            skipped += 1
        else:
            db.add(DailySteps(**r))
            added += 1
    db.commit()
    return added, skipped


def _upsert_heartrate(db: Session, records: list[dict]) -> tuple[int, int]:
    added = skipped = 0
    for r in records:
        existing = db.query(HeartRate).filter_by(timestamp=r["timestamp"]).first()
        if existing:
            skipped += 1
        else:
            db.add(HeartRate(**r))
            added += 1
    db.commit()
    return added, skipped


def _upsert_sleep(db: Session, records: list[dict]) -> tuple[int, int]:
    added = skipped = 0
    for r in records:
        existing = db.query(SleepRecord).filter_by(date=r["date"]).first()
        if existing:
            skipped += 1
        else:
            db.add(SleepRecord(**r))
            added += 1
    db.commit()
    return added, skipped


@router.post("/mi-fitness/preview")
async def preview_mi_fitness(file: UploadFile = File(...)):
    """Inspect a Mi Fitness ZIP and return metadata without importing anything."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip file exported from Mi Fitness")

    tmp_path = _save_upload(file)
    try:
        return preview_mi_fitness_zip(tmp_path)
    except Exception as e:
        raise HTTPException(422, f"Could not read Mi Fitness export: {e}")
    finally:
        os.unlink(tmp_path)


@router.post("/mi-fitness")
async def upload_mi_fitness(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip file exported from Mi Fitness")

    tmp_path = _save_upload(file)
    try:
        data = parse_mi_fitness_zip(tmp_path)
    except Exception as e:
        raise HTTPException(422, f"Could not parse Mi Fitness export: {e}")
    finally:
        os.unlink(tmp_path)

    a_add, a_skip = _upsert_activities(db, data["activities"])
    s_add, s_skip = _upsert_steps(db, data["steps"])
    hr_add, hr_skip = _upsert_heartrate(db, data["heartrate"])
    sl_add, sl_skip = _upsert_sleep(db, data["sleep"])

    return {
        "imported": {
            "activities": a_add,
            "steps": s_add,
            "heartrate": hr_add,
            "sleep": sl_add,
        },
        "skipped": {
            "activities": a_skip,
            "steps": s_skip,
            "heartrate": hr_skip,
            "sleep": sl_skip,
        },
    }


@router.post("/runkeeper")
async def upload_runkeeper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip file exported from Runkeeper")

    tmp_path = _save_upload(file)
    try:
        data = parse_runkeeper_zip(tmp_path)
    except Exception as e:
        raise HTTPException(422, f"Could not parse Runkeeper export: {e}")
    finally:
        os.unlink(tmp_path)

    a_add, a_skip = _upsert_activities(db, data["activities"])

    return {
        "imported": {"activities": a_add},
        "skipped": {"activities": a_skip},
    }


@router.post("/gpx-folder")
async def upload_gpx_folder(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accept a ZIP of GPX files (no CSV needed).
    Handles Runkeeper folder exports: files named YYYY-MM-DD-HHMMSS.gpx.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Please upload a .zip file containing your GPX files")

    tmp_path = _save_upload(file)
    try:
        data = parse_gpx_folder_zip(tmp_path)
    except Exception as e:
        raise HTTPException(422, f"Could not parse GPX folder: {e}")
    finally:
        os.unlink(tmp_path)

    if not data["activities"]:
        raise HTTPException(422, "No GPX files with valid track data found in this ZIP")

    a_add, a_skip = _upsert_activities(db, data["activities"])

    return {
        "imported": {"activities": a_add},
        "skipped": {"activities": a_skip},
    }
