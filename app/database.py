import psycopg
from app.config import settings


def get_connection():
    """Open a new database connection."""
    return psycopg.connect(settings.database_url)


def run_query(sql, params=None):
    """Run a SELECT query and return all rows as a list of dicts."""
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
    """Run a SELECT query and return a single row as a dict, or None."""
    rows = run_query(sql, params)
    return rows[0] if rows else None


def run_execute(sql, params=None):
    """Run an INSERT, UPDATE, or DELETE query."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def run_execute_returning(sql, params=None):
    """Run an INSERT/UPDATE with RETURNING clause and return the row as a dict."""
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
