from fastapi import FastAPI # type: ignore

from .db import db_connection


HEALTH_TABLE = "app_health_checks"

app = FastAPI(title="ClassEngage API", version="0.1.0")


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
