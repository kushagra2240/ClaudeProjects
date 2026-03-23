"""
Helpers that build synthetic Mi Fitness and Runkeeper ZIP files in memory.
The data mirrors the real export formats so the parsers see realistic input.
"""
import io
import zipfile


# ── Mi Fitness ────────────────────────────────────────────────────────────────

MI_FITNESS_STEPS_CSV = """\
date,steps,calories,active_minutes
2025-10-01,8432,312,45
2025-10-02,11205,415,72
2025-10-03,6891,255,38
2025-10-04,14023,519,91
2025-10-05,9340,346,55
"""

MI_FITNESS_HEARTRATE_CSV = """\
time,bpm
2025-10-01 08:00:00,62
2025-10-01 08:30:00,65
2025-10-01 09:00:00,70
2025-10-02 08:00:00,58
2025-10-02 14:00:00,88
2025-10-03 08:00:00,61
"""

MI_FITNESS_SLEEP_CSV = """\
date,total,deep,light,rem,awake
2025-10-01,452,90,210,110,42
2025-10-02,398,72,185,95,46
2025-10-03,480,105,220,120,35
2025-10-04,420,85,195,105,35
2025-10-05,461,92,208,115,46
"""

# Sport type IDs: 1=outdoor run, 5=walk, 3=outdoor cycle
MI_FITNESS_ACTIVITIES_CSV = """\
date,type,duration,distance,avg_heart_rate,calorie
2025-10-01,1,1820,5230,152,387
2025-10-03,5,2700,3100,98,210
2025-10-05,1,3120,8450,158,612
2025-10-07,3,4500,22300,135,540
2025-10-10,1,2240,6200,160,472
"""


def build_mi_fitness_zip() -> bytes:
    """Return a ZIP file bytes object shaped like a real Mi Fitness export."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("STEP_DAILY.csv", MI_FITNESS_STEPS_CSV)
        zf.writestr("HEARTRATE_AUTO.csv", MI_FITNESS_HEARTRATE_CSV)
        zf.writestr("SLEEP_DATA.csv", MI_FITNESS_SLEEP_CSV)
        zf.writestr("ACTIVITY_SPORT_RECORD.csv", MI_FITNESS_ACTIVITIES_CSV)
    return buf.getvalue()


# ── Runkeeper ─────────────────────────────────────────────────────────────────

RUNKEEPER_ACTIVITIES_CSV = """\
Activity Id,Date,Type,Route Name,Distance (km),Duration,Average Heart Rate (bpm),Calories Burned,GPX File,Notes
12345001,2025-10-02 07:14:00,Running,,5.23,0:28:11,156,387,,
12345002,2025-10-04 08:00:00,Walking,,3.10,0:45:00,98,210,,
12345003,2025-10-06 06:45:00,Running,,8.45,0:52:00,161,612,Running_2025-10-06_0645.gpx,
12345004,2025-10-09 07:30:00,Cycling,,22.30,1:15:00,136,540,,
"""

RUNKEEPER_GPX = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Runkeeper" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Running 2025-10-06 06:45</name>
    <trkseg>
      <trkpt lat="51.5074" lon="-0.1278">
        <ele>10.0</ele>
        <time>2025-10-06T06:45:00Z</time>
        <extensions><gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
          <gpxtpx:hr>158</gpxtpx:hr>
        </gpxtpx:TrackPointExtension></extensions>
      </trkpt>
      <trkpt lat="51.5080" lon="-0.1265">
        <ele>11.5</ele>
        <time>2025-10-06T06:50:00Z</time>
        <extensions><gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
          <gpxtpx:hr>162</gpxtpx:hr>
        </gpxtpx:TrackPointExtension></extensions>
      </trkpt>
      <trkpt lat="51.5090" lon="-0.1250">
        <ele>12.0</ele>
        <time>2025-10-06T06:55:00Z</time>
        <extensions><gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
          <gpxtpx:hr>165</gpxtpx:hr>
        </gpxtpx:TrackPointExtension></extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""


def build_runkeeper_zip() -> bytes:
    """Return a ZIP file bytes object shaped like a real Runkeeper export."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("cardioActivities.csv", RUNKEEPER_ACTIVITIES_CSV)
        zf.writestr("Running_2025-10-06_0645.gpx", RUNKEEPER_GPX)
    return buf.getvalue()
