"""
database.py — SQLite persistence layer.
Tables: subscribers, bookmarks, article_cache
"""
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from config import DB_PATH, CACHE_TTL_MINUTES


# ── Connection helper ────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Schema init ──────────────────────────────────────────────────────────────

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                email     TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                active    INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS bookmarks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url         TEXT UNIQUE NOT NULL,
                title       TEXT,
                source      TEXT,
                summary     TEXT,
                saved_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS article_cache (
                cache_key   TEXT PRIMARY KEY,
                data        TEXT NOT NULL,
                cached_at   TEXT DEFAULT (datetime('now'))
            );
        """)


# ── Subscribers ──────────────────────────────────────────────────────────────

def add_subscriber(email: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO subscribers (email) VALUES (?)", (email.lower().strip(),)
            )
        return True, "Subscribed successfully."
    except sqlite3.IntegrityError:
        return False, "This email is already subscribed."


def get_all_subscribers() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT email FROM subscribers WHERE active = 1"
        ).fetchall()
    return [r["email"] for r in rows]


def unsubscribe(email: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE subscribers SET active = 0 WHERE email = ?", (email.lower().strip(),)
        )
    return cur.rowcount > 0


# ── Bookmarks ────────────────────────────────────────────────────────────────

def add_bookmark(url: str, title: str, source: str, summary: str) -> tuple[bool, str]:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO bookmarks (url, title, source, summary) VALUES (?,?,?,?)",
                (url, title, source, summary),
            )
        return True, "Bookmarked."
    except sqlite3.IntegrityError:
        return False, "Already bookmarked."


def get_bookmarks() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bookmarks ORDER BY saved_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def remove_bookmark(url: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM bookmarks WHERE url = ?", (url,))


# ── Article Cache ─────────────────────────────────────────────────────────────

def cache_articles(cache_key: str, articles: list[dict]):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO article_cache (cache_key, data) VALUES (?,?)",
            (cache_key, json.dumps(articles)),
        )


def get_cached_articles(cache_key: str) -> list[dict] | None:
    """Returns cached list if still fresh, else None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT data, cached_at FROM article_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()

    if not row:
        return None

    cached_at = datetime.fromisoformat(row["cached_at"])
    if datetime.now() - cached_at > timedelta(minutes=CACHE_TTL_MINUTES):
        return None  # stale

    return json.loads(row["data"])


def clear_cache():
    with get_conn() as conn:
        conn.execute("DELETE FROM article_cache")
