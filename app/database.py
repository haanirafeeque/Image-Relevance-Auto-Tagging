"""
Database helper functions — simple wrappers around psycopg.

Every function gets a fresh connection, runs its query, and closes.
This is simple and works fine for a small project.
For production you'd use connection pooling, but that's a non-goal here.
"""

import psycopg
from app.config import settings


def get_connection():
    """Open a new database connection."""
    return psycopg.connect(settings.database_url)


def run_query(sql, params=None):
    """Run a query that returns rows (SELECT)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def run_query_one(sql, params=None):
    """Run a query that returns exactly one row."""
    rows = run_query(sql, params)
    if rows:
        return rows[0]
    return None


def run_execute(sql, params=None):
    """Run a query that modifies data (INSERT, UPDATE, DELETE). Returns nothing."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def run_execute_returning(sql, params=None):
    """Run an INSERT/UPDATE with RETURNING clause. Returns the row as a dict."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        return dict(zip(columns, row)) if row else None
    finally:
        conn.close()


def run_migration(filepath):
    """Run a SQL migration file."""
    with open(filepath, "r") as f:
        sql = f.read()

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print(f"Migration applied: {filepath}")
    finally:
        conn.close()
