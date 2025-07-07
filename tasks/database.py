from prefect import task
import sqlite3
from pathlib import Path

@task
def init_db(db_path: str = "data/boe.db"):
    """Create SQLite database and required tables if they do not exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            id TEXT PRIMARY KEY,
            date TEXT,
            title TEXT,
            department TEXT,
            rank TEXT,
            url_xml TEXT,
            url_pdf TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            date TEXT,
            title TEXT,
            department TEXT,
            rank TEXT,
            text TEXT,
            url_xml TEXT,
            url_pdf TEXT
        )
        """
    )
    conn.commit()
    conn.close()

@task
def insert_article(record: dict, text: str, db_path: str = "data/boe.db"):
    """Insert or replace article metadata and text into the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    meta_values = (
        record.get("id"),
        record.get("date"),
        record.get("title"),
        record.get("department"),
        record.get("rank"),
        record.get("url_xml"),
        record.get("url_pdf"),
    )
    cur.execute(
        """
        INSERT OR REPLACE INTO metadata (
            id, date, title, department, rank, url_xml, url_pdf
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        meta_values,
    )
    article_values = meta_values[:5] + (text,) + meta_values[5:]
    cur.execute(
        """
        INSERT OR REPLACE INTO articles (
            id, date, title, department, rank, text, url_xml, url_pdf
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        article_values,
    )
    conn.commit()
    conn.close()
