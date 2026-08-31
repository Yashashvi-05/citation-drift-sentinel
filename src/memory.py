import sqlite3
import hashlib
import os
import re
from datetime import datetime

DB_PATH = os.environ.get('SENTINEL_DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentinel_cache.db"))

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citation_cache (
                    article TEXT,
                    citation_url TEXT,
                    source TEXT,
                    live_text_hash TEXT,
                    baseline_live BOOLEAN,
                    sentinel_live BOOLEAN,
                    sentinel_archived BOOLEAN,
                    sentinel_status TEXT,
                    last_checked TIMESTAMP,
                    PRIMARY KEY (article, citation_url, source)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wayback_cache (
                    url TEXT,
                    insertion_date TEXT,
                    archived_url TEXT,
                    archived_text TEXT,
                    snapshot_timestamp TEXT,
                    PRIMARY KEY (url, insertion_date)
                )
            """)
            conn.commit()
    except sqlite3.Error as e:
        print(f"WARNING: SQLite error - {e}")

def _robust_hash(text: str) -> str:
    if not text:
        return "empty"
    # Retain alphanumeric characters (a-z, A-Z, 0-9) to preserve dates and version numbers
    clean_text = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    return hashlib.sha256(clean_text.encode('utf-8')).hexdigest()

def get_cache(article: str, url: str, live_text: str, source: str) -> dict | None:
    text_hash = _robust_hash(live_text)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM citation_cache 
                WHERE article = ? AND citation_url = ? AND source = ?
            """, (article, url, source))
            row = cursor.fetchone()
            
            if row and row["live_text_hash"] == text_hash:
                return dict(row)
    except sqlite3.Error as e:
        print(f"WARNING: SQLite error - {e}")
            
    return None

def set_cache(article: str, url: str, live_text: str, source: str, sentinel_status: str, sentinel_live: bool, sentinel_archived: bool, baseline_live: bool = None):
    text_hash = _robust_hash(live_text)
    now = datetime.utcnow().isoformat()
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO citation_cache 
                (article, citation_url, source, live_text_hash, baseline_live, sentinel_live, sentinel_archived, sentinel_status, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (article, url, source, text_hash, baseline_live, sentinel_live, sentinel_archived, sentinel_status, now))
            conn.commit()
    except sqlite3.Error as e:
        print(f"WARNING: SQLite error - {e}")

def get_wayback_cache(url: str, insertion_date: str) -> dict | None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM wayback_cache 
                WHERE url = ? AND insertion_date = ?
            """, (url, insertion_date))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
    except sqlite3.Error as e:
        print(f"WARNING: SQLite error - {e}")
            
    return None

def set_wayback_cache(url: str, insertion_date: str, archived_url: str, archived_text: str, snapshot_timestamp: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO wayback_cache 
                (url, insertion_date, archived_url, archived_text, snapshot_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (url, insertion_date, archived_url, archived_text, snapshot_timestamp))
            conn.commit()
    except sqlite3.Error as e:
        print(f"WARNING: SQLite error - {e}")
