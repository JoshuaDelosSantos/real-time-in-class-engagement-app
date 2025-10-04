"""
FastAPI application configuration, routes, and static frontend serving.
"""

import os
from pathlib import Path

from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import FileResponse, JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore

from .db import db_connection


HEALTH_TABLE = "app_health_checks"

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


@app.get("/", include_in_schema=False)
def serve_index():
    if not FRONTEND_DIR.exists():
        return JSONResponse({"status": "ok", "message": "Frontend assets not found"})
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "Hello World!"}


@app.post("/db/ping")
def db_ping() -> dict[str, int]:
    """Exercise the database by inserting a health-check row and returning the count."""
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {HEALTH_TABLE} (
                    id SERIAL PRIMARY KEY,
                    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(f"INSERT INTO {HEALTH_TABLE} DEFAULT VALUES RETURNING id")
            inserted_id = cur.fetchone()[0]
            cur.execute(f"SELECT COUNT(*) FROM {HEALTH_TABLE}")
            total_rows = cur.fetchone()[0]
    return {"inserted_id": inserted_id, "total_rows": total_rows}
