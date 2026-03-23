"""
Runkeeper ZIP export parser.

Expected contents:
  cardioActivities.csv  — one row per activity (summary)
  *.gpx                 — one GPX file per activity (GPS + optional HR)
"""
import zipfile
import tempfile
import os
from datetime import datetime
from typing import Optional

import pandas as pd

from backend.parsers.gpx import parse_gpx_file


_TYPE_MAP = {
    "running": "run",
    "walking": "walk",
    "cycling": "cycle",
    "swimming": "swim",
    "hiking": "hike",
    "elliptical": "elliptical",
    "rowing": "row",
    "yoga": "yoga",
    "strength training": "strength",
}


def _normalise_type(raw: str) -> str:
    return _TYPE_MAP.get(raw.strip().lower(), raw.strip().lower())


def _parse_duration(val: str) -> Optional[int]:
    """'1:23:45' or '23:45' → seconds."""
    try:
        parts = str(val).strip().split(":")
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    except Exception:
        pass
    return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except Exception:
        return None


def _safe_int(val) -> Optional[int]:
    try:
        return int(float(val))
    except Exception:
        return None


def _parse_date(val) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


def parse_runkeeper_zip(zip_path: str) -> dict:
    """
    Unzip a Runkeeper export and parse activities.
    Returns dict with key: activities — list of dicts.
    """
    result = {"activities": []}

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)

        # Build GPX filename index: date-prefix → filepath
        gpx_index: dict[str, str] = {}
        for root, _, files in os.walk(tmp):
            for fname in files:
                if fname.lower().endswith(".gpx"):
                    gpx_index[fname] = os.path.join(root, fname)

        # Find cardioActivities.csv
        csv_path = None
        for root, _, files in os.walk(tmp):
            for fname in files:
                if fname.lower() == "cardioactivities.csv":
                    csv_path = os.path.join(root, fname)
                    break

        if not csv_path:
            print("[runkeeper] cardioActivities.csv not found in export")
            return result

        df = pd.read_csv(csv_path, skipinitialspace=True)

        for _, row in df.iterrows():
            dt = _parse_date(row.get("Date", ""))
            if not dt:
                continue

            gpx_file = str(row.get("GPX File", "")).strip()
            gpx_data = None
            distance_m = None
            avg_hr = None

            # Distance from CSV (Runkeeper stores in km by default)
            dist_raw = _safe_float(row.get("Distance (km)", row.get("Distance", None)))
            if dist_raw:
                distance_m = dist_raw * 1000

            # Heart rate from CSV
            avg_hr = _safe_int(row.get("Average Heart Rate (bpm)", row.get("Average HR", None)))

            # Enrich with GPX data if available
            if gpx_file and gpx_file in gpx_index:
                try:
                    gpx_result = parse_gpx_file(gpx_index[gpx_file])
                    gpx_data = gpx_result["points"]
                    if gpx_result["distance_meters"]:
                        distance_m = gpx_result["distance_meters"]
                    if gpx_result["avg_heart_rate"] and not avg_hr:
                        avg_hr = gpx_result["avg_heart_rate"]
                except Exception as e:
                    print(f"[runkeeper] GPX parse error for {gpx_file}: {e}")

            result["activities"].append({
                "source": "runkeeper",
                "date": dt.date(),
                "activity_type": _normalise_type(str(row.get("Type", "run"))),
                "duration_seconds": _parse_duration(row.get("Duration", "")),
                "distance_meters": distance_m,
                "avg_heart_rate": avg_hr,
                "calories": _safe_float(row.get("Calories Burned", row.get("Calories", None))),
                "gpx_points": gpx_data,
            })

    return result
