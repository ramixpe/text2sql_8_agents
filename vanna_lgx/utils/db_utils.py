# vanna_lgx/utils/db_utils.py - CORRECTED

import sqlite3
import re
from typing import Dict, Set
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

def get_schema_info() -> Dict[str, Set[str]]:
    """
    Connects to the DB and extracts a dictionary mapping table names to a set of their column names.
    This is used by the SQL linter for fast schema checks.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = {}
    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = {row[1] for row in cursor.fetchall()}
        schema_info[table_name] = columns
        
    conn.close()
    return schema_info