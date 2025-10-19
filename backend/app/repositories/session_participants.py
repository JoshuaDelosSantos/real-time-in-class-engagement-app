"""Repository helpers for session participants."""

from __future__ import annotations

from typing import Optional

import psycopg # type: ignore
from psycopg.rows import dict_row # type: ignore


def add_participant(
    conn: psycopg.Connection,
    *,
    session_id: int,
    user_id: int,
    role: str,
) -> dict:
    """Insert a participant row and return it."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO session_participants (session_id, user_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id, user_id) DO UPDATE SET role = EXCLUDED.role
            RETURNING id, session_id, user_id, role, joined_at
            """,
            (session_id, user_id, role),
        )
        return cur.fetchone()


def get_participant(conn: psycopg.Connection, session_id: int, user_id: int) -> Optional[dict]:
    """Fetch a participant record for a session/user combination."""

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, session_id, user_id, role, joined_at
            FROM session_participants
            WHERE session_id = %s AND user_id = %s
            """,
            (session_id, user_id),
        )
        return cur.fetchone()


def list_session_participants(conn: psycopg.Connection, session_id: int) -> list[dict]:
    """List all participants for a session with user details.
    
    Returns participants ordered by role (host first), then join time (earliest first).
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT 
                sp.user_id,
                u.display_name,
                sp.role,
                sp.joined_at
            FROM session_participants sp
            JOIN users u ON sp.user_id = u.id
            WHERE sp.session_id = %s
            ORDER BY 
                CASE WHEN sp.role = 'host' THEN 0 ELSE 1 END,
                sp.joined_at ASC
            """,
            (session_id,),
        )
        return cur.fetchall()
