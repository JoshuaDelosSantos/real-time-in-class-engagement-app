"""Repository helpers for working with users."""

from __future__ import annotations

from typing import Optional

import psycopg # type: ignore
from psycopg.rows import dict_row # type: ignore


def get_user_by_display_name(conn: psycopg.Connection, display_name: str) -> Optional[dict]:
    """Fetch a user by display name."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, display_name, created_at FROM users WHERE display_name = %s",
            (display_name,),
        )
        return cur.fetchone()


def get_user_by_id(conn: psycopg.Connection, user_id: int) -> Optional[dict]:
    """Fetch a user by ID."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, display_name, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()


def create_user(conn: psycopg.Connection, display_name: str) -> dict:
    """Insert a new user row and return it."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO users (display_name)
            VALUES (%s)
            RETURNING id, display_name, created_at
            """,
            (display_name,),
        )
        return cur.fetchone()
