"""Database connection and utilities for route history.

This module provides SQLite database connection and helpers
for storing and retrieving route planning history.
"""

import json
import sqlite3
from pathlib import Path

from .schemas import RoutePlan

# Database file path
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "route_history.db"


def get_db_connection() -> sqlite3.Connection:
    """Get SQLite database connection.

    Creates database file and tables if they don't exist.

    Returns:
        SQLite connection object.
    """
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.Connection(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name

    # Create table if not exists
    _init_database(conn)

    return conn


def _init_database(conn: sqlite3.Connection) -> None:
    """Initialize database schema.

    Args:
        conn: SQLite connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS route_plans (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at
        ON route_plans(created_at DESC)
    """)
    conn.commit()


def save_route_plan(plan: RoutePlan) -> None:
    """Save route plan to database.

    Args:
        plan: RoutePlan to save.
    """
    conn = get_db_connection()
    try:
        # Serialize plan to JSON
        plan_json = plan.model_dump_json()

        conn.execute(
            """
            INSERT OR REPLACE INTO route_plans (id, data, created_at)
            VALUES (?, ?, ?)
            """,
            (plan.id, plan_json, plan.created_at),
        )
        conn.commit()
    finally:
        conn.close()


def get_route_history(limit: int = 50) -> list[RoutePlan]:
    """Retrieve route planning history.

    Args:
        limit: Maximum number of plans to retrieve.

    Returns:
        List of RoutePlan objects, most recent first.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT data FROM route_plans
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        plans = []
        for row in cursor:
            plan_data = json.loads(row["data"])
            plans.append(RoutePlan(**plan_data))

        return plans
    finally:
        conn.close()


def get_route_plan_by_id(plan_id: str) -> RoutePlan | None:
    """Retrieve a specific route plan by ID.

    Args:
        plan_id: Route plan ID.

    Returns:
        RoutePlan if found, None otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT data FROM route_plans WHERE id = ?",
            (plan_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        plan_data = json.loads(row["data"])
        return RoutePlan(**plan_data)
    finally:
        conn.close()
