from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import psycopg # type: ignore
import pytest # type: ignore

from app.settings import get_psycopg_dsn
from scripts.apply_migrations import apply_all

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    """Ensure the database schema is up to date before tests run."""

    apply_all(quiet=True)


def _truncate_all() -> None:
    tables = [
        "question_votes",
        "questions",
        "session_participants",
        "sessions",
        "users",
    ]
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE "
                + ", ".join(tables)
                + " RESTART IDENTITY CASCADE"
            )


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    """Clear relational tables before and after each test."""

    _truncate_all()
    yield
    _truncate_all()


@pytest.fixture
def db_connection() -> Iterator[psycopg.Connection]:
    """Yield a psycopg connection for direct repository testing."""

    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        yield conn
