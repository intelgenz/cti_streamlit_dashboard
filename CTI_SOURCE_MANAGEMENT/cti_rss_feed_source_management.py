import os
import pyodbc
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+ (use `pytz` for older versions)
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection settings from environment
SERVER = os.getenv('AZURE_SQL_SERVER')
DATABASE = os.getenv('AZURE_SQL_DATABASE')
USERNAME = os.getenv('AZURE_SQL_USERNAME')
PASSWORD = os.getenv('AZURE_SQL_PASSWORD')
SOURCE_DB_TABLE_NAME = os.getenv('SOURCE_DB_TABLE_NAME')
DRIVER = '{ODBC Driver 18 for SQL Server}'

if not all([SERVER, DATABASE, USERNAME, PASSWORD, SOURCE_DB_TABLE_NAME]):
    raise ValueError("Missing database environment variables. Check .env file.")

CONN_STR = f"""
    DRIVER={DRIVER};
    SERVER={SERVER};
    DATABASE={DATABASE};
    UID={USERNAME};
    PWD={PASSWORD};
"""

def get_ist_now():
    """Return current datetime in India Standard Time (IST) as naive datetime."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

def get_db_connection():
    """Create and return a database connection."""
    return pyodbc.connect(CONN_STR)

def get_next_source_id(cursor):
    """Get next source_id in format s<number> (e.g., s1, s2, ...)."""
    query = f"""
        SELECT MAX(CAST(SUBSTRING(source_id, 2, LEN(source_id)) AS INT))
        FROM {SOURCE_DB_TABLE_NAME}
        WHERE source_id LIKE 's%' AND TRY_CAST(SUBSTRING(source_id, 2, LEN(source_id)) AS INT) IS NOT NULL
    """
    cursor.execute(query)
    max_num = cursor.fetchone()[0]
    return "s1" if max_num is None else f"s{max_num + 1}"

def add_source(source_name, source_url, created_by):
    """Insert a new RSS source. Returns (success, message, new_source_id)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate URL
        cursor.execute(f"SELECT id FROM {SOURCE_DB_TABLE_NAME} WHERE source_url = ?", (source_url,))
        if cursor.fetchone():
            return False, "Source URL already exists.", None

        source_id = get_next_source_id(cursor)
        now = get_ist_now()
        cursor.execute(f"""
            INSERT INTO {SOURCE_DB_TABLE_NAME}
            (source_id, source_name, source_url, source_type, created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, source_name, source_url, 'RSS', created_by, created_by, now, now))
        conn.commit()
        logger.info(f"Added source: {source_name} with ID {source_id}")
        return True, "Source added successfully.", source_id
    except Exception as e:
        logger.error(f"Add error: {e}")
        if conn: conn.rollback()
        return False, f"Database error: {str(e)}", None
    finally:
        if conn: conn.close()

def update_source(source_id, source_name, source_url, updated_by):
    """Update an existing source. Returns (success, message)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if URL already used by another source
        cursor.execute(f"SELECT id FROM {SOURCE_DB_TABLE_NAME} WHERE source_url = ? AND source_id != ?", (source_url, source_id))
        if cursor.fetchone():
            return False, "Another source already uses this URL."

        now = get_ist_now()
        cursor.execute(f"""

            UPDATE {SOURCE_DB_TABLE_NAME}
            SET source_name = ?, source_url = ?, updated_by = ?, updated_at = ?
            WHERE source_id = ?
        """, (source_name, source_url, updated_by, now, source_id))
        if cursor.rowcount == 0:
            return False, "Source not found."
        conn.commit()
        logger.info(f"Updated source: {source_id}")
        return True, "Source updated successfully."
    except Exception as e:
        logger.error(f"Update error: {e}")
        if conn: conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        if conn: conn.close()

def delete_source(source_id):
    """Delete a source. Returns (success, message)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SOURCE_DB_TABLE_NAME} WHERE source_id = ?", (source_id,))
        if cursor.rowcount == 0:
            return False, "Source not found."
        conn.commit()
        logger.info(f"Deleted source: {source_id}")
        return True, "Source deleted successfully."
    except Exception as e:
        logger.error(f"Delete error: {e}")
        if conn: conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        if conn: conn.close()

def get_all_sources():
    """Retrieve all sources as a list of dictionaries."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT source_id, source_name, source_url, source_type,
                   created_by, updated_by, created_at, updated_at
            FROM {SOURCE_DB_TABLE_NAME}
            ORDER BY source_id
        """)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []
    finally:
        if conn: conn.close()
