"""Repository helpers for session persistence."""

from __future__ import annotations

from typing import Optional

import psycopg # type: ignore
from psycopg.rows import dict_row # type: ignore


def insert_session(
    conn: psycopg.Connection,
    *,
    host_user_id: int,
    title: str,
    code: str,
    status: str = "draft",
) -> dict:
    """Insert a session row and return the record."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO sessions (host_user_id, title, code, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, host_user_id, title, code, status, created_at, started_at, ended_at
            """,
            (host_user_id, title, code, status),
        )
        return cur.fetchone()


def get_session_by_code(conn: psycopg.Connection, code: str) -> Optional[dict]:
    """Retrieve a session by its join code."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, host_user_id, title, code, status, created_at, started_at, ended_at
            FROM sessions
            WHERE code = %s
            """,
            (code,),
        )
        return cur.fetchone()


def count_active_sessions_for_host(conn: psycopg.Connection, host_user_id: int) -> int:
    """Return the number of non-ended sessions for the host."""

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM sessions
            WHERE host_user_id = %s AND status IN ('draft', 'active')
            """,
            (host_user_id,),
        )
        result = cur.fetchone()
        return result[0] if result else 0


def get_session_by_id(conn: psycopg.Connection, session_id: int) -> Optional[dict]:
    """Fetch a session by primary key."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, host_user_id, title, code, status, created_at, started_at, ended_at
            FROM sessions
            WHERE id = %s
            """,
            (session_id,),
        )
        return cur.fetchone()
