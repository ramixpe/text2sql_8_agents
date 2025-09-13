# vanna_lgx/utils/db_utils.py - CORRECTED

import sqlite3
# WRONG: from config import DB_PATH
# RIGHT: Explicitly import from within the package
from vanna_lgx.config import DB_PATH

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def get_full_schema(conn: sqlite3.Connection) -> str:
    """
    Extracts the DDL (CREATE TABLE statements) for all tables in the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema_rows = cursor.fetchall()
    return "\n\n".join([row[0] for row in schema_rows if row[0]])