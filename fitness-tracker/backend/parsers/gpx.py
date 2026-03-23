"""Generic GPX file parser. Returns track points and summary stats."""
import gpxpy
from typing import Optional


def parse_gpx_file(file_path: str) -> dict:
    """
    Parse a .gpx file and return structured data.

    Returns:
        points          — list of {lat, lon, ele, time, hr}
        distance_meters — total 2D distance
        avg_heart_rate  — average HR if available
        activity_type   — from <type> tag on the track (e.g. "Running")
        name            — track name if present
        start_time      — datetime of first point
        end_time        — datetime of last point
        duration_seconds— elapsed time between first and last point
    """
    with open(file_path, "r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    points = []
    total_distance = 0.0
    hr_values = []
    prev_point = None
    all_times = []
    activity_type = None
    name = None

    for track in gpx.tracks:
        if not activity_type and track.type:
            activity_type = track.type.strip()
        if not name and track.name:
            name = track.name.strip()

        for segment in track.segments:
            for point in segment.points:
                hr = _extract_hr(point)
                if hr:
                    hr_values.append(hr)

                if prev_point:
                    total_distance += point.distance_2d(prev_point) or 0.0

                if point.time:
                    all_times.append(point.time)

                points.append({
                    "lat": point.latitude,
                    "lon": point.longitude,
                    "ele": point.elevation,
                    "time": point.time.isoformat() if point.time else None,
                    "hr": hr,
                })
                prev_point = point

    avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None
    start_time = min(all_times) if all_times else None
    end_time = max(all_times) if all_times else None
    duration_seconds = int((end_time - start_time).total_seconds()) if start_time and end_time else None

    return {
        "points": points,
        "distance_meters": total_distance,
        "avg_heart_rate": avg_hr,
        "activity_type": activity_type,
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds,
    }


def _extract_hr(point) -> Optional[int]:
    """Extract heart rate from Garmin/Runkeeper GPX extension."""
    try:
        for ext in point.extensions:
            # Garmin TrackPointExtension: <gpxtpx:hr>
            for child in ext:
                tag = child.tag.split("}")[-1].lower()
                if tag == "hr":
                    return int(child.text)
    except Exception:
        pass
    return None
