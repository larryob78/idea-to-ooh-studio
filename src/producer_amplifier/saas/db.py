from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
import os


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./.data/saas.db")


def _sqlite_path_from_url(url: str) -> Path:
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", "", 1))
    # local dev fallback when postgres URL is provided but driver unavailable in this lightweight build
    return Path(".data/saas_fallback.db")


@contextmanager
def get_conn():
    path = _sqlite_path_from_url(get_database_url())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    migrations_dir = Path(__file__).parent / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    with get_conn() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        for file in files:
            exists = conn.execute("SELECT 1 FROM schema_migrations WHERE name=?", (file.name,)).fetchone()
            if exists:
                continue
            conn.executescript(file.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(name) VALUES (?)", (file.name,))
