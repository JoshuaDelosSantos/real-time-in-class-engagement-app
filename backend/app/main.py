"""
FastAPI application configuration, routes, and static frontend serving.
"""

import os
from pathlib import Path

from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import FileResponse, JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore

from app.api.routes.database_health import router as database_health_router
from app.api.routes.health import router as health_router
from app.api import sessions_router

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FRONTEND_DIR = PROJECT_ROOT / "frontend" / "public"
FRONTEND_DIR = Path(os.getenv("FRONTEND_PUBLIC_DIR", DEFAULT_FRONTEND_DIR))

app = FastAPI(title="ClassEngage API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

app.include_router(health_router)
app.include_router(database_health_router)
app.include_router(sessions_router)


@app.get("/", include_in_schema=False)
def serve_index():
    if not FRONTEND_DIR.exists():
        return JSONResponse({"status": "ok", "message": "Frontend assets not found"})
    return FileResponse(FRONTEND_DIR / "index.html")
