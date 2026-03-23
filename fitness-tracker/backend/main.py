from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.routes import upload, activities, health, stats

app = FastAPI(title="Fitness Tracker", version="1.0.0")

# Init DB tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Register API routers
app.include_router(upload.router)
app.include_router(activities.router)
app.include_router(health.router)
app.include_router(stats.router)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# Serve HTML pages
_pages = ["index", "upload", "activities", "health", "stats"]

@app.get("/")
def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

for _page in _pages[1:]:
    def _make_handler(page):
        def handler():
            return FileResponse(str(FRONTEND_DIR / f"{page}.html"))
        handler.__name__ = f"serve_{page}"
        return handler
    app.get(f"/{_page}")((_make_handler(_page)))

@app.get("/manifest.json")
def manifest():
    return FileResponse(str(FRONTEND_DIR / "manifest.json"))

@app.get("/sw.js")
def service_worker():
    return FileResponse(str(FRONTEND_DIR / "sw.js"), media_type="application/javascript")
