from __future__ import annotations

import os

import psycopg # type: ignore
import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore

from app.main import app
from app.settings import get_psycopg_dsn

client = TestClient(app)


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:  # pragma: no cover - enforced during test runtime
    pytest.skip("DATABASE_URL must be configured to run integration tests", allow_module_level=True)


def reset_health_table() -> None:
    with psycopg.connect(get_psycopg_dsn(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS app_health_checks")


def test_db_ping_inserts_and_counts_rows() -> None:
    reset_health_table()

    first = client.post("/db/ping")
    assert first.status_code == 200
    body = first.json()
    assert body["total_rows"] == 1

    second = client.post("/db/ping")
    assert second.status_code == 200
    body_two = second.json()
    assert body_two["total_rows"] == 2
