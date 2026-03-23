"""
Mi Fitness ZIP export parser.

Expected files inside the ZIP:
  STEP_DAILY.csv          — daily steps
  HEARTRATE_AUTO.csv      — auto heart rate readings
  SLEEP_DATA.csv          — sleep sessions
  ACTIVITY_SPORT_RECORD.csv — workout records (no GPS)

Column names may vary slightly between app versions; we do fuzzy matching.
"""
import zipfile
import tempfile
import os
import re
from datetime import date, datetime
from typing import Optional

import pandas as pd


# ── helpers ──────────────────────────────────────────────────────────────────

def _col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    """Return the first column name that matches any candidate (case-insensitive)."""
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _parse_date(val) -> Optional[date]:
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _parse_dt(val) -> Optional[datetime]:
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


def _safe_int(val) -> Optional[int]:
    try:
        return int(float(val))
    except Exception:
        return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except Exception:
        return None


# ── per-file parsers ──────────────────────────────────────────────────────────

def _parse_steps(path: str) -> list[dict]:
    df = pd.read_csv(path, skipinitialspace=True)
    date_col = _col(df, "date", "day", "time", "Date")
    steps_col = _col(df, "steps", "step", "Steps", "totalSteps")
    cal_col = _col(df, "calories", "cal", "Calories")
    active_col = _col(df, "active_minutes", "activeMinutes", "active_time")

    records = []
    for _, row in df.iterrows():
        d = _parse_date(row[date_col]) if date_col else None
        if not d:
            continue
        records.append({
            "date": d,
            "steps": _safe_int(row[steps_col]) if steps_col else None,
            "calories": _safe_float(row[cal_col]) if cal_col else None,
            "active_minutes": _safe_int(row[active_col]) if active_col else None,
            "source": "mi_fitness",
        })
    return records


def _parse_heartrate(path: str) -> list[dict]:
    df = pd.read_csv(path, skipinitialspace=True)
    time_col = _col(df, "time", "timestamp", "date", "Time")
    bpm_col = _col(df, "bpm", "heart_rate", "heartRate", "value", "HR")

    records = []
    for _, row in df.iterrows():
        ts = _parse_dt(row[time_col]) if time_col else None
        bpm = _safe_int(row[bpm_col]) if bpm_col else None
        if not ts or not bpm:
            continue
        records.append({"timestamp": ts, "bpm": bpm, "source": "mi_fitness"})
    return records


def _parse_sleep(path: str) -> list[dict]:
    df = pd.read_csv(path, skipinitialspace=True)
    date_col = _col(df, "date", "day", "start", "Date")
    total_col = _col(df, "total", "total_minutes", "totalSleep", "duration")
    deep_col = _col(df, "deep", "deepSleep", "deep_sleep")
    light_col = _col(df, "light", "lightSleep", "light_sleep")
    rem_col = _col(df, "rem", "remSleep", "rem_sleep")
    awake_col = _col(df, "awake", "awakeSleep", "awake_time")

    records = []
    for _, row in df.iterrows():
        d = _parse_date(row[date_col]) if date_col else None
        if not d:
            continue
        records.append({
            "date": d,
            "total_minutes": _safe_int(row[total_col]) if total_col else None,
            "deep_minutes": _safe_int(row[deep_col]) if deep_col else None,
            "light_minutes": _safe_int(row[light_col]) if light_col else None,
            "rem_minutes": _safe_int(row[rem_col]) if rem_col else None,
            "awake_minutes": _safe_int(row[awake_col]) if awake_col else None,
            "source": "mi_fitness",
        })
    return records


_SPORT_TYPE_MAP = {
    # Numeric sport type IDs used by Mi Fitness / Xiaomi watches
    "1": "run",         # Outdoor Running
    "2": "run",         # Treadmill Running
    "3": "cycle",       # Outdoor Cycling
    "4": "cycle",       # Indoor Cycling
    "5": "walk",        # Outdoor Walking
    "6": "walk",        # Walking
    "7": "hike",        # Hiking
    "8": "hike",        # Mountaineering / Climbing
    "9": "cycle",       # Cycling (variant)
    "10": "swim",       # Open Water Swimming
    "11": "swim",       # Pool Swimming
    "14": "hike",       # Trekking
    "21": "elliptical", # Elliptical
    "24": "yoga",       # Yoga
    "25": "jump_rope",  # Jump Rope
    "35": "hiit",       # HIIT
    "48": "strength",   # Strength Training
    # String labels (from some export versions)
    "run": "run", "running": "run", "outdoor running": "run", "treadmill": "run",
    "walk": "walk", "walking": "walk", "outdoor walking": "walk",
    "cycling": "cycle", "cycle": "cycle", "outdoor cycling": "cycle",
    "swimming": "swim", "swim": "swim",
    "hiking": "hike", "hike": "hike",
    "elliptical": "elliptical",
    "yoga": "yoga",
    "strength": "strength", "strength training": "strength",
}


def _parse_activities(path: str) -> list[dict]:
    df = pd.read_csv(path, skipinitialspace=True)
    date_col = _col(df, "date", "startTime", "start_time", "time", "begin_time")
    type_col = _col(df, "type", "sport_type", "sportType", "activity_type")
    dur_col = _col(df, "duration", "duration_seconds", "durationSeconds", "costTime", "cost_time")
    dist_col = _col(df, "distance", "distanceMeters", "distance_meters")
    hr_col = _col(df, "avg_heart_rate", "avgHeartRate", "heart_rate", "bpm", "avgHr")
    cal_col = _col(df, "calories", "cal", "calorie")

    records = []
    for _, row in df.iterrows():
        d = _parse_date(row[date_col]) if date_col else None
        if not d:
            continue
        raw_type = str(row[type_col]).strip().lower() if type_col else "unknown"
        activity_type = _SPORT_TYPE_MAP.get(raw_type, raw_type)
        dur = _safe_int(row[dur_col]) if dur_col else None
        records.append({
            "source": "mi_fitness",
            "date": d,
            "activity_type": activity_type,
            "duration_seconds": dur,
            "distance_meters": _safe_float(row[dist_col]) if dist_col else None,
            "avg_heart_rate": _safe_int(row[hr_col]) if hr_col else None,
            "calories": _safe_float(row[cal_col]) if cal_col else None,
            "gpx_points": None,
        })
    return records


# ── file router ───────────────────────────────────────────────────────────────

_FILE_PARSERS = {
    re.compile(r"step", re.I): ("steps", _parse_steps),
    re.compile(r"heart|hr", re.I): ("heartrate", _parse_heartrate),
    re.compile(r"sleep", re.I): ("sleep", _parse_sleep),
    re.compile(r"activity|sport|workout", re.I): ("activities", _parse_activities),
}


def parse_mi_fitness_zip(zip_path: str) -> dict:
    """
    Unzip a Mi Fitness export and parse all recognised CSV files.
    Returns dict with keys: steps, heartrate, sleep, activities — each a list of dicts.
    """
    result = {"steps": [], "heartrate": [], "sleep": [], "activities": []}

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)

        for root, _, files in os.walk(tmp):
            for fname in files:
                if not fname.lower().endswith(".csv"):
                    continue
                fpath = os.path.join(root, fname)
                for pattern, (key, parser) in _FILE_PARSERS.items():
                    if pattern.search(fname):
                        try:
                            result[key].extend(parser(fpath))
                        except Exception as e:
                            print(f"[mi_fitness] Could not parse {fname}: {e}")
                        break

    return result


def preview_mi_fitness_zip(zip_path: str) -> dict:
    """
    Inspect a Mi Fitness ZIP without importing anything.
    Returns metadata: which files were found, their columns, record counts, and date ranges.
    """
    summary = {
        "files_found": [],
        "unrecognised_files": [],
        "counts": {"steps": 0, "heartrate": 0, "sleep": 0, "activities": 0},
        "date_ranges": {},
        "columns": {},
        "activity_types": [],
        "errors": [],
    }

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path, "r") as zf:
            all_names = zf.namelist()
            summary["files_found"] = [n for n in all_names if n.lower().endswith(".csv")]
            zf.extractall(tmp)

        for root, _, files in os.walk(tmp):
            for fname in files:
                if not fname.lower().endswith(".csv"):
                    continue
                fpath = os.path.join(root, fname)
                matched = False
                for pattern, (key, parser) in _FILE_PARSERS.items():
                    if pattern.search(fname):
                        matched = True
                        try:
                            df = pd.read_csv(fpath, skipinitialspace=True)
                            summary["columns"][fname] = list(df.columns)
                            records = parser(fpath)
                            summary["counts"][key] += len(records)

                            # Date range
                            dates = []
                            for r in records:
                                d = r.get("date") or (r.get("timestamp") and r["timestamp"].date())
                                if d:
                                    dates.append(d)
                            if dates:
                                summary["date_ranges"][key] = {
                                    "from": str(min(dates)),
                                    "to": str(max(dates)),
                                }

                            # Activity type breakdown
                            if key == "activities":
                                types = {}
                                for r in records:
                                    t = r.get("activity_type", "unknown")
                                    types[t] = types.get(t, 0) + 1
                                summary["activity_types"] = [
                                    {"type": t, "count": c} for t, c in sorted(types.items(), key=lambda x: -x[1])
                                ]
                        except Exception as e:
                            summary["errors"].append({"file": fname, "error": str(e)})
                        break
                if not matched:
                    summary["unrecognised_files"].append(fname)

    return summary
