# Fitness Tracker — Project Documentation

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [File Structure](#2-file-structure)
3. [Startup Flow](#3-startup-flow)
4. [Database Schema](#4-database-schema)
5. [Data Ingestion — Full Process Flow](#5-data-ingestion--full-process-flow)
   - 5.1 [Mi Fitness ZIP](#51-mi-fitness-zip)
   - 5.2 [Runkeeper Full Export ZIP](#52-runkeeper-full-export-zip)
   - 5.3 [GPX Folder ZIP](#53-gpx-folder-zip)
6. [GPX Data — End-to-End](#6-gpx-data--end-to-end)
7. [API Reference](#7-api-reference)
8. [Frontend Pages & Data Flow](#8-frontend-pages--data-flow)
9. [Deduplication Logic](#9-deduplication-logic)
10. [Test Suite](#10-test-suite)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Browser / Phone                   │
│   HTML pages  ←──── GET /page ────►                 │
│   JS (fetch)  ←──── GET /api/... ──►  FastAPI app   │
│   File upload ────── POST /api/upload/... ──►        │
└─────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   FastAPI (Python)  │
                    │   Uvicorn ASGI      │
                    │   backend/main.py   │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌────────────┐  ┌──────────────┐
        │  Parsers  │   │   Routes   │  │  Static files│
        │ mi_fitness│   │ activities │  │  HTML / CSS  │
        │ runkeeper │   │ health     │  │  JS          │
        │ gpx       │   │ stats      │  └──────────────┘
        └──────────┘   │ upload     │
                       └─────┬──────┘
                             │
                    ┌────────▼────────┐
                    │   SQLAlchemy    │
                    │   ORM           │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   SQLite        │
                    │  data/fitness.db│
                    └─────────────────┘
```

**Key design decisions:**
- **No build step.** The frontend is plain HTML + vanilla JS served directly by FastAPI. No React, no bundler.
- **SQLite.** Single file database (`data/fitness.db`). No server setup needed.
- **Import-only.** The app has no connection to Mi Fitness or Runkeeper servers. All data comes via manual ZIP exports that you upload.
- **LAN access.** The server binds to `0.0.0.0` (all interfaces), so any device on the same WiFi network can reach it.

---

## 2. File Structure

```
fitness-tracker/
├── backend/
│   ├── config.py              ← paths, DB URL, host/port constants
│   ├── database.py            ← SQLAlchemy engine, session factory, init_db()
│   ├── main.py                ← FastAPI app, router registration, static files
│   ├── models/
│   │   ├── activity.py        ← Activity table (workouts + GPS points)
│   │   └── health.py          ← DailySteps, HeartRate, SleepRecord tables
│   ├── parsers/
│   │   ├── gpx.py             ← Generic GPX file parser
│   │   ├── mi_fitness.py      ← Mi Fitness ZIP parser + preview
│   │   └── runkeeper.py       ← Runkeeper ZIP parser + GPX folder parser
│   └── routes/
│       ├── activities.py      ← GET /api/activities, GET /api/activities/{id}
│       ├── health.py          ← GET /api/health/steps|heartrate|sleep
│       ├── stats.py           ← GET /api/stats/summary|weekly|monthly
│       └── upload.py          ← POST /api/upload/mi-fitness|runkeeper|gpx-folder
├── frontend/
│   ├── index.html             ← Dashboard page
│   ├── activities.html        ← Activities list + detail overlay
│   ├── health.html            ← Steps / HR / sleep charts
│   ├── stats.html             ← Summary stats and personal records
│   ├── upload.html            ← Import page with export instructions
│   ├── manifest.json          ← PWA manifest (install as app on phone)
│   ├── sw.js                  ← Service worker (offline shell)
│   └── static/
│       ├── css/app.css        ← All styles
│       └── js/
│           ├── api.js         ← Shared fetch wrapper + helper functions
│           ├── dashboard.js
│           ├── activities.js  ← Includes GPX route drawing
│           ├── health.js
│           ├── stats.js
│           └── upload.js      ← Preview + import logic
├── data/
│   ├── fitness.db             ← SQLite database (auto-created)
│   └── uploads/               ← Temp storage for uploads (auto-cleaned)
├── tests/
│   ├── fixtures/
│   │   └── build_zips.py      ← Synthetic Mi Fitness + Runkeeper ZIPs for testing
│   ├── test_mi_fitness_parser.py
│   ├── test_runkeeper_parser.py
│   ├── test_upload_endpoints.py
│   └── test_real_export.py    ← CLI script to inspect a real ZIP
├── requirements.txt
├── run.bat                    ← Windows startup script
└── run.sh                     ← Mac/Linux startup script
```

---

## 3. Startup Flow

When you run `run.bat` (or `run.sh`):

```
run.bat
  │
  ├─ 1. ipconfig → find LAN IP → print http://localhost:8000 + http://<IP>:8000
  │
  └─ 2. python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
                                │
                                ▼
                    backend/main.py loads
                                │
                                ├─ 3. @app.on_event("startup") fires
                                │        └─ init_db()
                                │              ├─ imports Activity, DailySteps,
                                │              │  HeartRate, SleepRecord models
                                │              │  (registers them with SQLAlchemy metadata)
                                │              └─ Base.metadata.create_all()
                                │                   └─ creates data/fitness.db
                                │                      and all tables if they don't exist
                                │
                                ├─ 4. Routers registered:
                                │        /api/upload/...
                                │        /api/activities/...
                                │        /api/health/...
                                │        /api/stats/...
                                │
                                ├─ 5. Static files mounted:
                                │        /static/ → frontend/static/
                                │
                                └─ 6. Page routes registered:
                                         / → index.html
                                         /upload → upload.html
                                         /activities → activities.html
                                         /health → health.html
                                         /stats → stats.html
```

`--reload` means Uvicorn watches all `.py` files and restarts automatically when you save a change — no need to restart the server during development.

---

## 4. Database Schema

All data lives in a single SQLite file: `data/fitness.db`.

### `activities` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `source` | TEXT | `"runkeeper"` or `"mi_fitness"` |
| `date` | DATE | Day of the activity |
| `activity_type` | TEXT | `"run"`, `"walk"`, `"cycle"`, `"hike"`, etc. |
| `duration_seconds` | INTEGER | Elapsed time in seconds |
| `distance_meters` | FLOAT | Total distance in metres |
| `avg_heart_rate` | INTEGER | Average BPM during activity |
| `calories` | FLOAT | Calories burned |
| `gpx_points` | JSON | Array of `{lat, lon, ele, time, hr}` — nullable |
| `created_at` | DATETIME | Row insertion timestamp |

Unique constraint: `(source, date, duration_seconds)` — prevents duplicate imports.

### `daily_steps` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `date` | DATE UNIQUE | One row per calendar day |
| `steps` | INTEGER | Step count |
| `calories` | FLOAT | Calories from steps |
| `active_minutes` | INTEGER | Minutes of elevated activity |
| `source` | TEXT | Data origin |

### `heart_rate` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `timestamp` | DATETIME UNIQUE | Exact reading time |
| `bpm` | INTEGER | Heart rate |
| `source` | TEXT | Data origin |

### `sleep_records` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `date` | DATE UNIQUE | Night of sleep (start date) |
| `total_minutes` | INTEGER | Total sleep duration |
| `deep_minutes` | INTEGER | Deep sleep |
| `light_minutes` | INTEGER | Light sleep |
| `rem_minutes` | INTEGER | REM sleep |
| `awake_minutes` | INTEGER | Awake time within sleep window |
| `source` | TEXT | Data origin |

---

## 5. Data Ingestion — Full Process Flow

### 5.1 Mi Fitness ZIP

```
User selects ZIP on /upload page
        │
        ▼
[Optional] POST /api/upload/mi-fitness/preview
        │   ← no DB writes, returns metadata only
        │   ← shows counts, date ranges, activity type breakdown
        │
        ▼
POST /api/upload/mi-fitness  (multipart/form-data)
        │
        ├─ 1. Save ZIP to temp file
        │
        ├─ 2. parse_mi_fitness_zip(tmp_path)
        │        │
        │        ├─ Unzip to temp directory
        │        ├─ Walk every .csv file
        │        └─ Match filename → parser:
        │             "STEP*"        → _parse_steps()
        │             "HEART*|HR*"   → _parse_heartrate()
        │             "SLEEP*"       → _parse_sleep()
        │             "ACTIVITY*|    → _parse_activities()
        │              SPORT*|
        │              WORKOUT*"
        │
        │        Each parser:
        │          - reads CSV with pandas
        │          - fuzzy-matches column names (handles export version differences)
        │          - converts values to typed Python objects
        │          - returns list of dicts
        │
        ├─ 3. _upsert_activities()  ← checks (source, date, duration) uniqueness
        ├─ 4. _upsert_steps()       ← checks date uniqueness
        ├─ 5. _upsert_heartrate()   ← checks timestamp uniqueness
        ├─ 6. _upsert_sleep()       ← checks date uniqueness
        │
        ├─ 7. Delete temp file
        │
        └─ 8. Return { imported: {...}, skipped: {...} }
```

**Sport type mapping** (`_SPORT_TYPE_MAP` in `mi_fitness.py`):
Mi Fitness stores activities as numeric IDs. The parser maps them to readable strings:

| Numeric ID | Activity |
|-----------|----------|
| 1 | run (Outdoor Running) |
| 2 | run (Treadmill) |
| 3 | cycle (Outdoor Cycling) |
| 4 | cycle (Indoor Cycling) |
| 5 | walk |
| 6 | walk |
| 7 | hike |
| 9 | cycle |
| 10 | swim (Open Water) |
| 11 | swim (Pool) |
| 14 | hike (Trekking) |
| 21 | elliptical |
| 24 | yoga |
| 35 | hiit |
| 48 | strength |

Any unmapped ID is stored as its raw string value.

---

### 5.2 Runkeeper Full Export ZIP

The full Runkeeper export contains `cardioActivities.csv` (summary of every workout) plus individual `.gpx` files for workouts that had GPS tracking.

```
POST /api/upload/runkeeper
        │
        ├─ 1. Save ZIP to temp file
        │
        ├─ 2. parse_runkeeper_zip(tmp_path)
        │        │
        │        ├─ Unzip to temp directory
        │        ├─ Index all .gpx files by filename
        │        ├─ Find cardioActivities.csv
        │        └─ For each row in CSV:
        │              ├─ Parse date, type, distance, duration, HR, calories
        │              ├─ Look up matching GPX file by filename
        │              │    └─ If found: parse_gpx_file() → enrich with GPS points
        │              │         ├─ distance_meters overridden with GPS-calculated value
        │              │         └─ avg_heart_rate taken from GPX if not in CSV
        │              └─ Append to activities list
        │
        ├─ 3. _upsert_activities()
        └─ 4. Return { imported: {...}, skipped: {...} }
```

**Duration format:** Runkeeper CSV stores duration as `"H:MM:SS"` or `"MM:SS"`.
`_parse_duration()` splits on `:` and converts to total seconds.

**Distance:** CSV stores kilometres. Parser multiplies by 1000 → metres.

---

### 5.3 GPX Folder ZIP

Used when you have a folder of raw `.gpx` files (e.g. a Runkeeper data folder with files named `2024-03-28-070908.gpx`) and no accompanying CSV.

```
POST /api/upload/gpx-folder
        │
        ├─ 1. Save ZIP to temp file
        │
        ├─ 2. parse_gpx_folder_zip(tmp_path)
        │        │
        │        ├─ Unzip to temp directory
        │        ├─ Walk and collect all .gpx files, sorted by name
        │        └─ For each .gpx file:
        │              │
        │              ├─ parse_gpx_file() → GPS points, distance, HR, duration,
        │              │                     activity_type, track name, start/end times
        │              │
        │              ├─ Determine DATE:
        │              │    1st choice: filename regex → "2024-03-28-070908" → date
        │              │    Fallback:   first GPS point timestamp
        │              │
        │              ├─ Determine ACTIVITY TYPE:
        │              │    1st choice: GPX <type> tag (e.g. "Running")
        │              │    2nd choice: first word of track name (e.g. "Running 2024-03-28")
        │              │    Fallback:   "run"
        │              │    All values normalised via _normalise_type() → "run"/"walk"/etc.
        │              │
        │              └─ Append activity (calories = null, not available without CSV)
        │
        ├─ 3. _upsert_activities()
        └─ 4. Return { imported: {...}, skipped: {...} }
```

---

## 6. GPX Data — End-to-End

This section traces exactly what happens to GPS data from file to screen.

### Step 1 — Parsing (`backend/parsers/gpx.py`)

`parse_gpx_file(path)` uses the `gpxpy` library to read the XML file.

For every track point in the file it extracts:
- `lat`, `lon` — coordinates
- `ele` — elevation in metres
- `time` — ISO timestamp
- `hr` — heart rate, read from the Garmin `TrackPointExtension` XML namespace: `<gpxtpx:hr>158</gpxtpx:hr>`

It also computes:
- **`distance_meters`** — cumulative sum of `point.distance_2d(prev_point)` between consecutive points (2D = ignores elevation changes)
- **`avg_heart_rate`** — average of all `hr` values found
- **`duration_seconds`** — `(last_point.time - first_point.time).total_seconds()`
- **`activity_type`** — from the GPX `<type>` element on the track
- **`start_time` / `end_time`** — min/max of all point timestamps

### Step 2 — Storage (`backend/models/activity.py`)

The `gpx_points` column on the `Activity` model is typed as `JSON`:

```python
gpx_points = Column(JSON)   # [{lat, lon, ele, time, hr}, ...]
```

SQLAlchemy stores this as a JSON string in SQLite and automatically deserialises it back to a Python list when you read it. There is no limit on the number of points — a one-hour run at one point per second would store ~3600 objects in this column.

### Step 3 — API (`backend/routes/activities.py`)

The list endpoint (`GET /api/activities`) intentionally **excludes** `gpx_points` from the response — returning it for every activity in a paginated list would be very slow.

`gpx_points` is only included in the detail endpoint:

```
GET /api/activities/{id}   ← returns full activity including gpx_points array
```

### Step 4 — Frontend rendering (`frontend/static/js/activities.js`)

When you tap an activity in the list, `openDetail(id)` is called:

```javascript
const a = await API.activity(id);    // fetches /api/activities/{id}

if (a.gpx_points && a.gpx_points.length) {
    drawRoute(a.gpx_points);         // draws onto a <canvas> element
}
```

`drawRoute(points)` renders the route using the **HTML Canvas 2D API** — no mapping library, no external tiles, no internet required:

```
Points array [{lat, lon}, ...]
        │
        ├─ Find bounding box: minLat, maxLat, minLon, maxLon
        │
        ├─ Scale functions:
        │    toX(lon) → pixel X, mapped to canvas width  (with padding)
        │    toY(lat) → pixel Y, mapped to canvas height (with padding)
        │               ↑ note: lat is inverted because canvas Y grows downward
        │
        ├─ Draw polyline: ctx.lineTo(toX(lon), toY(lat)) for each point
        │    colour: #4f8ef7 (blue), lineWidth: 2.5px
        │
        └─ Draw start dot (green #22c55e) and end dot (red #ef4444)
```

The route is a flat 2D projection — it's not a real map projection, just a linear scale. For most activities (runs, walks, cycles in a local area) the distortion is negligible.

### Full GPX flow summary

```
.gpx file
    │  gpxpy parses XML
    ▼
[{lat, lon, ele, time, hr}, ...]  +  distance, avg_hr, duration, type
    │  stored as JSON column
    ▼
activities table  (gpx_points JSON blob)
    │  GET /api/activities/{id}
    ▼
JSON response to browser
    │  drawRoute(points)
    ▼
<canvas> — 2D route drawing (no map library needed)
```

---

## 7. API Reference

All routes are prefixed — API routes under `/api/`, pages served directly.

### Upload

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `POST` | `/api/upload/mi-fitness/preview` | ZIP file | Inspect ZIP, return metadata. **No DB writes.** |
| `POST` | `/api/upload/mi-fitness` | ZIP file | Import Mi Fitness export |
| `POST` | `/api/upload/runkeeper` | ZIP file | Import Runkeeper full export (CSV + GPX) |
| `POST` | `/api/upload/gpx-folder` | ZIP file | Import folder of raw GPX files |

All upload endpoints accept `multipart/form-data` with a field named `file`.

### Activities

| Method | Path | Query params | Description |
|--------|------|-------------|-------------|
| `GET` | `/api/activities` | `source`, `type`, `from`, `to`, `page`, `limit` | Paginated list. `gpx_points` excluded. |
| `GET` | `/api/activities/{id}` | — | Single activity with full `gpx_points` |

### Health

| Method | Path | Query params | Description |
|--------|------|-------------|-------------|
| `GET` | `/api/health/steps` | `from`, `to` | Daily step counts (default: last 30 days) |
| `GET` | `/api/health/heartrate` | `from`, `to`, `resolution` | HR data. `resolution`: `raw` / `hourly` / `daily` |
| `GET` | `/api/health/sleep` | `from`, `to` | Sleep records with stage breakdown |

### Stats

| Method | Path | Query params | Description |
|--------|------|-------------|-------------|
| `GET` | `/api/stats/summary` | — | Totals, averages, personal records |
| `GET` | `/api/stats/weekly` | `weeks` (default 8) | Per-week breakdown |
| `GET` | `/api/stats/monthly` | `months` (default 6) | Per-month breakdown |

### Pages (served as HTML)

| Path | File served |
|------|-------------|
| `/` | `frontend/index.html` |
| `/upload` | `frontend/upload.html` |
| `/activities` | `frontend/activities.html` |
| `/health` | `frontend/health.html` |
| `/stats` | `frontend/stats.html` |

Interactive API docs (auto-generated by FastAPI): **`http://localhost:8000/docs`**

---

## 8. Frontend Pages & Data Flow

Every page follows the same pattern:
1. Browser requests `/page` → FastAPI returns static HTML file
2. HTML loads `api.js` (shared fetch wrapper) and the page-specific JS
3. Page JS calls `API.*()` functions which `fetch()` the relevant `/api/` endpoints
4. JSON response is rendered into the DOM

### `api.js` — shared layer

`apiFetch(path)` wraps `fetch()`, checks `res.ok`, and returns parsed JSON or throws.

`API` object exposes named methods for every endpoint:
```javascript
API.summary()           → GET /api/stats/summary
API.activities(params)  → GET /api/activities?...
API.activity(id)        → GET /api/activities/{id}
API.steps(params)       → GET /api/health/steps?...
API.heartrate(params)   → GET /api/health/heartrate?...
API.sleep(params)       → GET /api/health/sleep?...
```

Shared helpers also live here: `fmtDuration(seconds)`, `fmtDist(meters)`, `activityIcon(type)`.

### Dashboard (`/`)

```
loadDashboard()
  ├─ API.summary()      → fills 4 summary cards (weekly dist, avg steps, resting HR, avg sleep)
  ├─ API.weekly(1)      → gets this-week distance for the distance card
  ├─ API.steps()        → 30-day step bar chart via Chart.js
  │                        green bars = days ≥ 10,000 steps
  │                        blue bars  = days < 10,000 steps
  └─ API.activities({limit:5}) → recent activities list (last 5)
```

### Activities (`/activities`)

```
loadActivities()
  └─ API.activities({page, type, source})
       → paginated list, 15 per page
       → filter chips update currentType / currentSource and reload

openDetail(id)
  └─ API.activity(id)
       → shows stats: distance, duration, pace, avg HR, calories
       → if gpx_points present: drawRoute(points) on <canvas>
```

### Health (`/health`)

Three sections, each fetching independently:
- **Steps** — bar chart from `API.steps()`
- **Heart Rate** — line chart from `API.heartrate({resolution: "daily"})`
- **Sleep** — stacked bar chart from `API.sleep()`

All charts rendered with Chart.js 4 (loaded from CDN).

### Stats (`/stats`)

```
API.summary()   → summary numbers + personal records cards
API.weekly(8)   → 8-week bar charts (distance, steps, active days)
API.monthly(6)  → 6-month breakdown table
```

### Upload (`/upload`)

Three import sections: Mi Fitness, GPX Folder, Runkeeper.

Mi Fitness has a two-step flow:
1. **Preview** → `POST /api/upload/mi-fitness/preview` → renders counts + date ranges before committing
2. **Import** → `POST /api/upload/mi-fitness` → commits to DB, shows imported/skipped counts

GPX Folder and Runkeeper go straight to import (no preview step).

---

## 9. Deduplication Logic

Each data type has a different uniqueness key:

| Table | Unique key | Behaviour on duplicate |
|-------|-----------|------------------------|
| `activities` | `(source, date, duration_seconds)` | Skip. If `duration_seconds` is null, falls back to `(source, date, activity_type)` |
| `daily_steps` | `date` | Skip |
| `heart_rate` | `timestamp` | Skip |
| `sleep_records` | `date` | Skip |

This means it is **always safe to re-import the same file**. The second import will show `0 imported, N skipped`.

It also means if you import from both Mi Fitness and Runkeeper and the same run appears in both (e.g. Mi Fitness records the workout and Runkeeper also has it), they are stored as **separate rows** because `source` differs. The Activities page lets you filter by source to see each separately.

---

## 10. Test Suite

Located in `tests/`. Run with:

```bash
python -m pytest tests/ -v
```

| File | What it tests |
|------|--------------|
| `test_mi_fitness_parser.py` | Steps, HR, sleep, activities parsing from synthetic ZIP; preview function |
| `test_runkeeper_parser.py` | Duration helper, type normalisation, CSV parsing, GPX enrichment |
| `test_upload_endpoints.py` | FastAPI endpoints via `TestClient` with an in-memory SQLite DB |
| `test_real_export.py` | CLI script — run against a real ZIP to inspect its contents before importing |

**Real export diagnostic:**
```bash
# Inspect a real Mi Fitness ZIP before importing
python tests/test_real_export.py mi-fitness path/to/export.zip

# Inspect a real Runkeeper ZIP
python tests/test_real_export.py runkeeper path/to/export.zip
```

This prints file names, column names, record counts, date ranges, and activity type breakdown — useful for diagnosing parsing issues before doing a real import.
