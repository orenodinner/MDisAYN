from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class MetadataDB:
    def __init__(self, path: Path, log_events: bool = True) -> None:
        self.path = path
        self.log_events = log_events
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self.conn.close()

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_key TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                raw_path TEXT,
                extracted_path TEXT,
                obsidian_path TEXT,
                last_processed_at TEXT,
                metadata_json TEXT,
                UNIQUE(source_type, source_key)
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sources_hash
            ON sources (source_type, content_hash)
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details_json TEXT
            )
            """
        )
        self.conn.commit()

    def get_source(self, source_type: str, source_key: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM sources WHERE source_type = ? AND source_key = ?",
            (source_type, source_key),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_source_by_hash(self, source_type: str, content_hash: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM sources WHERE source_type = ? AND content_hash = ?",
            (source_type, content_hash),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert_source(
        self,
        source_type: str,
        source_key: str,
        content_hash: str,
        raw_path: Optional[str],
        extracted_path: Optional[str],
        obsidian_path: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata or {}, ensure_ascii=True)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO sources (
                source_type, source_key, content_hash, raw_path, extracted_path,
                obsidian_path, last_processed_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, source_key) DO UPDATE SET
                content_hash=excluded.content_hash,
                raw_path=excluded.raw_path,
                extracted_path=excluded.extracted_path,
                obsidian_path=excluded.obsidian_path,
                last_processed_at=excluded.last_processed_at,
                metadata_json=excluded.metadata_json
            """,
            (
                source_type,
                source_key,
                content_hash,
                raw_path,
                extracted_path,
                obsidian_path,
                now,
                metadata_json,
            ),
        )
        self.conn.commit()

    def list_sources(self, source_type: Optional[str] = None) -> list[Dict[str, Any]]:
        cur = self.conn.cursor()
        if source_type:
            cur.execute("SELECT * FROM sources WHERE source_type = ?", (source_type,))
        else:
            cur.execute("SELECT * FROM sources")
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def count_sources(self, source_type: Optional[str] = None) -> int:
        cur = self.conn.cursor()
        if source_type:
            cur.execute("SELECT COUNT(*) FROM sources WHERE source_type = ?", (source_type,))
        else:
            cur.execute("SELECT COUNT(*) FROM sources")
        return int(cur.fetchone()[0])

    def log_event(self, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        if not self.log_events:
            return
        now = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {}, ensure_ascii=True)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO events (event_time, event_type, details_json) VALUES (?, ?, ?)",
            (now, event_type, details_json),
        )
        self.conn.commit()
