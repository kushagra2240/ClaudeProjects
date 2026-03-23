"""Generic GPX file parser. Returns track points and summary stats."""
import gpxpy
from typing import Optional


def parse_gpx_file(file_path: str) -> dict:
    """Parse a .gpx file and return structured data."""
    with open(file_path, "r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    points = []
    total_distance = 0.0
    hr_values = []
    prev_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                hr = _extract_hr(point)
                if hr:
                    hr_values.append(hr)

                if prev_point:
                    total_distance += point.distance_2d(prev_point) or 0.0

                points.append({
                    "lat": point.latitude,
                    "lon": point.longitude,
                    "ele": point.elevation,
                    "time": point.time.isoformat() if point.time else None,
                    "hr": hr,
                })
                prev_point = point

    avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None

    return {
        "points": points,
        "distance_meters": total_distance,
        "avg_heart_rate": avg_hr,
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
