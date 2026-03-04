"""
cti_rss_feed_url_management.py
--------------------------------
Database connection and data management layer for CTI RSS Feed URL Scraper.
Handles all interactions with MySQL source_db and url_db tables.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()  # loads .env file before any os.getenv() calls

# ─────────────────────────────────────────────
# CONFIG — values loaded from .env file
# ─────────────────────────────────────────────
SERVER   = os.getenv("AZURE_MYSQL_SERVER")
DATABASE = os.getenv("AZURE_MYSQL_DATABASE")
USERNAME = os.getenv("AZURE_MYSQL_USERNAME")
PASSWORD = os.getenv("AZURE_MYSQL_PASSWORD")
SSL_CA   = "DigiCertGlobalRootG2.crt.pem"  # must be in same folder as this file

CREATED_BY = "yadhavaprasanna"
IST = timezone(timedelta(hours=5, minutes=30))


# ─────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────
def get_connection():
    """Create and return an Azure MySQL Flexible Server connection."""
    if not SERVER:
        raise ValueError(
            "AZURE_MYSQL_SERVER is not set. "
            "Check your .env file or environment variables."
        )
    config = dict(
        host=SERVER,
        port=3306,         # explicit port forces TCP/IP, avoids named pipe
        user=USERNAME,
        password=PASSWORD,
        database=DATABASE,
        connection_timeout=30,
        use_pure=True,     # pure-Python connector bypasses C-extension pipe logic
    )
    if SSL_CA and os.path.exists(SSL_CA):
        config.update(ssl_ca=SSL_CA, ssl_verify_cert=False)  # encrypt only, skip chain verify
    return mysql.connector.connect(**config)


def test_connection() -> tuple[bool, str]:
    """Test DB connectivity. Returns (success, message)."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Connected successfully."
    except Error as e:
        return False, str(e)


# ─────────────────────────────────────────────
# IST DATETIME HELPERS
# ─────────────────────────────────────────────
def now_ist() -> datetime:
    """Current datetime in IST (naive, suitable for MySQL DATETIME)."""
    return datetime.now(IST).replace(tzinfo=None)


def parse_to_ist(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an RSS published date string to IST datetime (naive).
    Tries multiple common formats. Returns None if unparseable.
    """
    if not date_str:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is not None:
                dt = dt.astimezone(IST).replace(tzinfo=None)
            return dt
        except ValueError:
            continue
    return None


# ─────────────────────────────────────────────
# URL ID GENERATOR
# ─────────────────────────────────────────────
def get_next_url_id_start() -> int:
    """
    Query url_db to find the current maximum url_N number.
    e.g. if url_1212 is the highest, returns 1213.
    Returns 1 if the table is empty.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT MAX(CAST(SUBSTRING(url_id, 5) AS UNSIGNED))
            FROM url_db
            WHERE url_id REGEXP '^url_[0-9]+$'
            """
        )
        row = cursor.fetchone()
        max_num = row[0] if row and row[0] is not None else 0
        return int(max_num) + 1
    finally:
        cursor.close()
        conn.close()


def generate_url_ids_for_batch(count: int) -> list[str]:
    """
    Generate a sequential list of url_ids starting from the next available number.
    e.g. if DB max is url_1212, returns ['url_1213', 'url_1214', ...]
    """
    start = get_next_url_id_start()
    return [f"url_{start + i}" for i in range(count)]


# ─────────────────────────────────────────────
# SOURCE_DB QUERIES
# ─────────────────────────────────────────────
def fetch_all_sources() -> list[dict]:
    """
    Fetch all RSS sources from source_db.
    Returns list of dicts with keys: id, source_id, source_name, source_url, source_type.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, source_id, source_name, source_url, source_type "
            "FROM source_db ORDER BY id"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# URL_DB QUERIES
# ─────────────────────────────────────────────
def fetch_existing_urls() -> set[str]:
    """Return a set of all URLs already present in url_db (for dedup)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM url_db")
        return {row[0] for row in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def insert_urls(records: list[dict]) -> int:
    """
    Bulk-insert new URL records into url_db.
    Each record must have all required fields.
    Returns number of rows inserted.
    """
    if not records:
        return 0

    sql = """
        INSERT INTO url_db (
            url_id, url, url_source, url_source_id, url_source_type,
            url_title, url_published_date, url_status, url_created_type,
            url_created_at, url_created_by,
            url_updated_at, url_updated_by
        ) VALUES (
            %(url_id)s, %(url)s, %(url_source)s, %(url_source_id)s, %(url_source_type)s,
            %(url_title)s, %(url_published_date)s, %(url_status)s, %(url_created_type)s,
            %(url_created_at)s, %(url_created_by)s,
            %(url_updated_at)s, %(url_updated_by)s
        )
    """
    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0
    try:
        for rec in records:
            cursor.execute(sql, rec)
            inserted += 1
        conn.commit()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
    return inserted


def build_url_record(
    url_id: str,
    url: str,
    source_name: str,
    source_id: str,
    title: Optional[str],
    published_str: Optional[str],
) -> dict:
    """Build a url_db record dict ready for insertion."""
    ts = now_ist()
    return {
        "url_id":            url_id,
        "url":               url,
        "url_source":        source_name,
        "url_source_id":     source_id,
        "url_source_type":   "rss_source",
        "url_title":         title if title else None,
        "url_published_date": parse_to_ist(published_str),
        "url_status":        "unprocessed",
        "url_created_type":  "scraped",
        "url_created_at":    ts,
        "url_created_by":    CREATED_BY,
        "url_updated_at":    ts,
        "url_updated_by":    CREATED_BY,
    }


# ─────────────────────────────────────────────
# DASHBOARD QUERIES
# ─────────────────────────────────────────────
def fetch_status_counts() -> dict:
    """Return counts: total, processed, unprocessed."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*)                        AS total,
                SUM(url_status = 'processed')   AS processed,
                SUM(url_status = 'unprocessed') AS unprocessed
            FROM url_db
            """
        )
        row = cursor.fetchone()
        return {
            "total":       int(row["total"]       or 0),
            "processed":   int(row["processed"]   or 0),
            "unprocessed": int(row["unprocessed"] or 0),
        }
    finally:
        cursor.close()
        conn.close()


def fetch_source_counts() -> list[dict]:
    """Return per-source URL counts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT url_source AS source,
                   COUNT(*) AS total,
                   SUM(url_status = 'processed')   AS processed,
                   SUM(url_status = 'unprocessed') AS unprocessed
            FROM url_db
            GROUP BY url_source
            ORDER BY total DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_recent_urls(limit: int = 50) -> list[dict]:
    """Fetch the most recently added URLs from url_db."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT url_id, url, url_source, url_source_id,
                   url_title, url_published_date, url_created_type,
                   url_created_at, url_status
            FROM url_db
            ORDER BY url_created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
