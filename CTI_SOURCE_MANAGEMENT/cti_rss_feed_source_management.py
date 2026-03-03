import os
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import logging
import streamlit as st

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For local testing, ensure .env file has the correct values for these variables
SERVER   = os.getenv('AZURE_MYSQL_SERVER')
DATABASE = os.getenv('AZURE_MYSQL_DATABASE')
USERNAME = os.getenv('AZURE_MYSQL_USERNAME')
PASSWORD = os.getenv('AZURE_MYSQL_PASSWORD')
SOURCE_DB_TABLE_NAME = os.getenv('SOURCE_DB_TABLE_NAME')
SSL_CA = "DigiCertGlobalRootG2.crt.pem"  # Ensure this file is in the same directory or provide correct path

# For Streamlit Cloud deployment, set these in the Streamlit Cloud dashboard:
# SERVER   = st.secrets["AZURE_MYSQL_SERVER"]
# DATABASE = st.secrets["AZURE_MYSQL_DATABASE"]
# USERNAME = st.secrets["AZURE_MYSQL_USERNAME"]
# PASSWORD = st.secrets["AZURE_MYSQL_PASSWORD"]
# SSL_CA   = st.secrets.get("AZURE_MYSQL_SSL_CA", None)
# SOURCE_DB_TABLE_NAME = st.secrets.get("SOURCE_DB_TABLE_NAME", "source_db")

if not all([SERVER, DATABASE, USERNAME, PASSWORD, SOURCE_DB_TABLE_NAME]):
    raise ValueError("Missing database environment variables. Check .env file.")


def get_ist_now():
    """Return current datetime in IST as naive datetime."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)


def get_db_connection():
    """Create and return an Azure MySQL Flexible Server connection."""
    config = dict(
        host=SERVER,
        user=USERNAME,
        password=PASSWORD,
        database=DATABASE,
        connection_timeout=30,
    )
    if SSL_CA:
        config.update(ssl_ca=SSL_CA, ssl_verify_cert=True)
    return mysql.connector.connect(**config)


def get_next_source_id(cursor):
    """Get next source_id in format s<number> (e.g., s1, s2, ...)."""
    query = f"""
        SELECT MAX(CAST(SUBSTRING(`source_id`, 2) AS UNSIGNED))
        FROM `{SOURCE_DB_TABLE_NAME}`
        WHERE `source_id` REGEXP '^s[0-9]+$'
    """
    cursor.execute(query)
    row = cursor.fetchone()
    max_num = list(row.values())[0] if isinstance(row, dict) else row[0]
    return "s1" if max_num is None else f"s{max_num + 1}"


def add_source(source_name, source_url, created_by):
    """Insert a new RSS source. Returns (success, message, new_source_id)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            f"SELECT `id` FROM `{SOURCE_DB_TABLE_NAME}` WHERE `source_url` = %s",
            (source_url,)
        )
        if cursor.fetchone():
            return False, "Source URL already exists.", None

        source_id = get_next_source_id(cursor)
        now = get_ist_now()
        cursor.execute(f"""
            INSERT INTO `{SOURCE_DB_TABLE_NAME}`
            (`source_id`, `source_name`, `source_url`, `source_type`, `created_by`, `updated_by`, `created_at`, `updated_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (source_id, source_name, source_url, 'RSS', created_by, created_by, now, now))
        conn.commit()
        logger.info(f"Added source: {source_name} with ID {source_id}")
        return True, "Source added successfully.", source_id

    except mysql.connector.Error as e:
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
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            f"SELECT `id` FROM `{SOURCE_DB_TABLE_NAME}` WHERE `source_url` = %s AND `source_id` != %s",
            (source_url, source_id)
        )
        if cursor.fetchone():
            return False, "Another source already uses this URL."

        now = get_ist_now()
        cursor.execute(f"""
            UPDATE `{SOURCE_DB_TABLE_NAME}`
            SET `source_name` = %s, `source_url` = %s, `updated_by` = %s, `updated_at` = %s
            WHERE `source_id` = %s
        """, (source_name, source_url, updated_by, now, source_id))

        if cursor.rowcount == 0:
            return False, "Source not found."
        conn.commit()
        logger.info(f"Updated source: {source_id}")
        return True, "Source updated successfully."

    except mysql.connector.Error as e:
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

        cursor.execute(
            f"DELETE FROM `{SOURCE_DB_TABLE_NAME}` WHERE `source_id` = %s",
            (source_id,)
        )
        if cursor.rowcount == 0:
            return False, "Source not found."
        conn.commit()
        logger.info(f"Deleted source: {source_id}")
        return True, "Source deleted successfully."

    except mysql.connector.Error as e:
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
        cursor = conn.cursor(dictionary=True)  # MySQL equivalent of pymssql as_dict=True
        cursor.execute(f"""
            SELECT `source_id`, `source_name`, `source_url`, `source_type`,
                   `created_by`, `updated_by`, `created_at`, `updated_at`
            FROM `{SOURCE_DB_TABLE_NAME}`
            ORDER BY `source_id`
        """)
        return cursor.fetchall()

    except mysql.connector.Error as e:
        logger.error(f"Fetch error: {e}")
        return []
    finally:
        if conn: conn.close()
