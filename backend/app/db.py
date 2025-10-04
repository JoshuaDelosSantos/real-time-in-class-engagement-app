from __future__ import annotations

from contextlib import contextmanager

import psycopg # type: ignore

from .settings import get_psycopg_dsn


@contextmanager
def db_connection():
    """Yield a psycopg connection with autocommit enabled."""
    conn = psycopg.connect(get_psycopg_dsn(), autocommit=True)
    try:
        yield conn
    finally:
        conn.close()
