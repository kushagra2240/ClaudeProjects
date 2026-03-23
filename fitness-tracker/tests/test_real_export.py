"""
Test a real Mi Fitness or Runkeeper export ZIP.

Usage:
    python tests/test_real_export.py mi-fitness path/to/export.zip
    python tests/test_real_export.py runkeeper  path/to/export.zip

Prints a detailed breakdown of what the parser finds — useful for
diagnosing column name mismatches before doing a real import.
"""
import sys
import json
from pathlib import Path


def inspect_mi_fitness(zip_path: str):
    from backend.parsers.mi_fitness import preview_mi_fitness_zip
    print(f"\nScanning: {zip_path}\n")
    result = preview_mi_fitness_zip(zip_path)

    print("Files found in ZIP:")
    for f in result["files_found"]:
        print(f"  {f}")

    print("\nRecord counts:")
    for k, v in result["counts"].items():
        dr = result["date_ranges"].get(k, {})
        date_str = f"  ({dr.get('from')} → {dr.get('to')})" if dr else ""
        print(f"  {k:12s}: {v}{date_str}")

    if result["activity_types"]:
        print("\nActivity types:")
        for item in result["activity_types"]:
            print(f"  {item['type']:20s}: {item['count']}")

    if result["columns"]:
        print("\nDetected column names:")
        for fname, cols in result["columns"].items():
            print(f"  {fname}")
            print(f"    {', '.join(cols)}")

    if result["errors"]:
        print("\nErrors:")
        for e in result["errors"]:
            print(f"  {e['file']}: {e['error']}")

    if result["unrecognised_files"]:
        print("\nUnrecognised files (not parsed):")
        for f in result["unrecognised_files"]:
            print(f"  {f}")


def inspect_runkeeper(zip_path: str):
    from backend.parsers.runkeeper import parse_runkeeper_zip
    print(f"\nScanning: {zip_path}\n")
    result = parse_runkeeper_zip(zip_path)
    activities = result["activities"]

    if not activities:
        print("No activities found. Check that the ZIP contains cardioActivities.csv")
        return

    from collections import Counter
    types = Counter(a["activity_type"] for a in activities)
    dates = [a["date"] for a in activities]

    print(f"Activities found: {len(activities)}")
    print(f"Date range: {min(dates)} → {max(dates)}")
    print("\nActivity types:")
    for t, c in types.most_common():
        print(f"  {t:20s}: {c}")

    gpx_count = sum(1 for a in activities if a.get("gpx_points"))
    print(f"\nActivities with GPS data: {gpx_count}/{len(activities)}")

    print("\nSample (first 3 activities):")
    for a in activities[:3]:
        dist = f"{a['distance_meters']:.0f}m" if a.get("distance_meters") else "—"
        hr = f"{a['avg_heart_rate']}bpm" if a.get("avg_heart_rate") else "—"
        print(f"  {a['date']}  {a['activity_type']:10s}  {dist:8s}  HR:{hr}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("mi-fitness", "runkeeper"):
        print("Usage: python tests/test_real_export.py <mi-fitness|runkeeper> <path/to/export.zip>")
        sys.exit(1)

    source = sys.argv[1]
    path = sys.argv[2]

    if not Path(path).exists():
        print(f"File not found: {path}")
        sys.exit(1)

    if source == "mi-fitness":
        inspect_mi_fitness(path)
    else:
        inspect_runkeeper(path)
