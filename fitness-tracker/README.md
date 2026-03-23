# Fitness Tracker

A personal fitness dashboard for aggregating and visualising workout and health data from **Mi Fitness** (Redmi/Xiaomi watches) and **Runkeeper**. Import your exports, then explore your activities, steps, heart rate, sleep, and stats — all in one place.

## Features

- Import Mi Fitness ZIP exports (steps, heart rate, sleep, activities)
- Import Runkeeper ZIP exports (activities with GPS data)
- Automatic deduplication across imports
- Dashboard with weekly distance, daily steps, resting heart rate, and sleep averages
- Activities list with filtering by source, type, and date range
- Health metrics: daily steps, heart rate (raw/hourly/daily), sleep breakdown
- Statistics: personal records, 8-week and 6-month breakdowns
- Accessible on your phone over LAN (no external server needed)
- PWA-ready with service worker and offline support

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI · Uvicorn |
| Database | SQLite · SQLAlchemy 2 |
| File parsing | gpxpy · pandas |
| Frontend | Vanilla JS · HTML/CSS · Chart.js 4 |

## Prerequisites

- Python 3.9 or higher
- Git

## Local Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd fitness-tracker
```

### 2. Create and activate a virtual environment

**Mac / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

**Mac / Linux**
```bash
./run.sh
```

**Windows**
```bash
run.bat
```

Or manually:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The startup scripts will detect your local IP and print two addresses:

```
Local:  http://localhost:8000
Phone:  http://192.168.x.x:8000
```

The database (`data/fitness.db`) and upload directory (`data/uploads/`) are created automatically on first run — no configuration needed.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.111 | Web framework |
| `uvicorn[standard]` | ≥ 0.29 | ASGI server |
| `sqlalchemy` | ≥ 2.0 | ORM / database layer |
| `python-multipart` | ≥ 0.0.9 | File upload handling |
| `gpxpy` | ≥ 1.6 | GPX file parsing |
| `pandas` | ≥ 2.2 | CSV parsing and data processing |
| `aiofiles` | ≥ 23.0 | Async file I/O |

## Importing Data

Navigate to **http://localhost:8000/upload** after starting the server.

| Source | How to export |
|--------|--------------|
| **Mi Fitness** | App → Profile → Privacy → Export Personal Data → download the ZIP |
| **Runkeeper** | Settings → Export Data → download the ZIP |

Upload the ZIP directly — the app handles extraction and parsing.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/mi-fitness` | Import Mi Fitness ZIP |
| `POST` | `/api/upload/runkeeper` | Import Runkeeper ZIP |
| `GET` | `/api/activities` | List activities (supports filtering) |
| `GET` | `/api/activities/{id}` | Single activity with GPS points |
| `GET` | `/api/health/steps` | Daily steps |
| `GET` | `/api/health/heartrate` | Heart rate (raw / hourly / daily) |
| `GET` | `/api/health/sleep` | Sleep records |
| `GET` | `/api/stats/summary` | Overall stats and personal records |
| `GET` | `/api/stats/weekly` | 8-week breakdown |
| `GET` | `/api/stats/monthly` | 6-month breakdown |

Interactive API docs are available at **http://localhost:8000/docs** when the server is running.
