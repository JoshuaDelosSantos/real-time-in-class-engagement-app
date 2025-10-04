"""Data access helpers for the health check audit table."""

from __future__ import annotations

from typing import Tuple

from psycopg import sql  # type: ignore

from app.db import db_connection

_HEALTH_TABLE = "app_health_checks"


class HealthCheckRepository:
    """Manage reads and writes for the health check audit table."""

    def __init__(self, table_name: str = _HEALTH_TABLE) -> None:
        self._table_name = table_name

    def record_ping(self) -> Tuple[int, int]:
        """Insert a ping row and return the inserted id and total row count."""
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id SERIAL PRIMARY KEY,
                            checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    ).format(table_name=sql.Identifier(self._table_name))
                )
                cur.execute(
                    sql.SQL("INSERT INTO {table_name} DEFAULT VALUES RETURNING id").format(
                        table_name=sql.Identifier(self._table_name)
                    )
                )
                inserted_id_row = cur.fetchone()
                if not inserted_id_row:  # pragma: no cover - defensive branch
                    msg = "INSERT operation failed to return an id"
                    raise RuntimeError(msg)
                inserted_id = inserted_id_row[0]
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {table_name}").format(
                        table_name=sql.Identifier(self._table_name)
                    )
                )
                total_rows_row = cur.fetchone()
                total_rows = total_rows_row[0] if total_rows_row else 0
        return inserted_id, total_rows
