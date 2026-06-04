"""SQLite database manager with connection pooling."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _init_tables(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    company TEXT,
                    title TEXT,
                    location TEXT,
                    url TEXT UNIQUE,
                    apply_url TEXT,
                    description TEXT,
                    score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'new',
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    status TEXT,
                    details TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            conn.commit()
    
    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def insert(self, table: str, data: Dict) -> int:
        with self._conn() as conn:
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            cursor = conn.execute(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            return cursor.lastrowid
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
