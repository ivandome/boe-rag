import sqlite3
import tempfile
from pathlib import Path
from tasks.database import init_db, insert_article


def test_init_db_creates_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test.db"
        init_db.fn(str(db_file))
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        conn.close()
        assert "articles" in tables
        assert "metadata" in tables


def test_insert_article_and_replace():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test.db"
        init_db.fn(str(db_file))
        record = {
            "id": "1",
            "date": "2023-01-01",
            "title": "Title",
            "department": "Dept",
            "rank": "Rank",
            "url_xml": "xml",
            "url_pdf": "pdf",
        }
        insert_article.fn(record, "Text", str(db_file))
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT text FROM articles WHERE id=?", ("1",))
        first_text = cur.fetchone()[0]
        assert first_text == "Text"
        cur.execute("SELECT count(*) FROM metadata")
        assert cur.fetchone()[0] == 1
        # Replace with new data
        record["title"] = "New"  # modify field to verify replace
        insert_article.fn(record, "New Text", str(db_file))
        cur.execute("SELECT title, text FROM articles WHERE id=?", ("1",))
        title, new_text = cur.fetchone()
        assert title == "New"
        assert new_text == "New Text"
        cur.execute("SELECT count(*) FROM articles")
        assert cur.fetchone()[0] == 1
        conn.close()
