from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import ScanMeta, ScanSnapshot


def _repo_root() -> Path:
    # api/app/storage.py -> api/app -> api -> repo root
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StorageConfig:
    db_path: Path


class Storage:
    def __init__(self, cfg: StorageConfig):
        self._cfg = cfg
        self._cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._cfg.db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def _ensure_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
              scan_id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              account_id TEXT,
              region TEXT NOT NULL,
              score INTEGER NOT NULL,
              domain_scores_json TEXT NOT NULL,
              snapshot_json TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS timeline (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_time TEXT NOT NULL,
              event_name TEXT NOT NULL,
              event_source TEXT NOT NULL,
              username TEXT,
              resources_json TEXT NOT NULL,
              scenario TEXT,
              operation_id TEXT
            )
            """
        )
        self._conn.commit()

    def put_scan(self, snapshot: ScanSnapshot) -> None:
        meta = ScanMeta(
            scan_id=snapshot.scan_id,
            created_at=snapshot.created_at,
            account_id=snapshot.account_id,
            region=snapshot.region,
            score=snapshot.score,
            domain_scores={k: int(v) for k, v in (snapshot.breakdown.get("domain_scores") or {}).items()},
            s3_key=None,
        )
        self._conn.execute(
            """
            INSERT INTO scans (
              scan_id, created_at, account_id, region, score, domain_scores_json, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meta.scan_id,
                meta.created_at.isoformat(),
                meta.account_id,
                meta.region,
                int(meta.score),
                json.dumps(meta.domain_scores, separators=(",", ":")),
                json.dumps(snapshot.model_dump(mode="json"), separators=(",", ":")),
            ),
        )
        self._conn.commit()

    def list_scans(self, limit: int = 25) -> list[ScanMeta]:
        rows = self._conn.execute(
            "SELECT scan_id, created_at, account_id, region, score, domain_scores_json FROM scans ORDER BY created_at DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        metas: list[ScanMeta] = []
        for r in rows:
            metas.append(
                ScanMeta(
                    scan_id=str(r["scan_id"]),
                    created_at=datetime.fromisoformat(str(r["created_at"])),
                    account_id=str(r["account_id"]) if r["account_id"] else None,
                    region=str(r["region"]),
                    score=int(r["score"]),
                    domain_scores=json.loads(str(r["domain_scores_json"]) or "{}"),
                    s3_key=None,
                )
            )
        return metas

    def get_scan(self, scan_id: str) -> tuple[ScanMeta, dict[str, Any] | None]:
        row = self._conn.execute(
            "SELECT scan_id, created_at, account_id, region, score, domain_scores_json, snapshot_json FROM scans WHERE scan_id = ?",
            (scan_id,),
        ).fetchone()
        if not row:
            raise KeyError("scan not found")
        meta = ScanMeta(
            scan_id=str(row["scan_id"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            account_id=str(row["account_id"]) if row["account_id"] else None,
            region=str(row["region"]),
            score=int(row["score"]),
            domain_scores=json.loads(str(row["domain_scores_json"]) or "{}"),
            s3_key=None,
        )
        snapshot = json.loads(str(row["snapshot_json"])) if row["snapshot_json"] else None
        return meta, snapshot

    def append_timeline_events(
        self,
        *,
        events: Iterable[dict[str, Any]],
        scenario: str | None = None,
        operation_id: str | None = None,
    ) -> None:
        cur = self._conn.cursor()
        for e in events:
            cur.execute(
                """
                INSERT INTO timeline (
                  event_time, event_name, event_source, username, resources_json, scenario, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(e.get("eventTime") or e.get("event_time")),
                    str(e.get("eventName") or e.get("event_name")),
                    str(e.get("eventSource") or e.get("event_source")),
                    e.get("username"),
                    json.dumps(e.get("resources") or [], separators=(",", ":")),
                    scenario,
                    operation_id,
                ),
            )
        self._conn.commit()

    def list_timeline(self, since: datetime | None = None, limit: int = 200) -> list[dict[str, Any]]:
        if since:
            rows = self._conn.execute(
                """
                SELECT event_time, event_name, event_source, username, resources_json
                FROM timeline
                WHERE event_time >= ?
                ORDER BY event_time ASC
                LIMIT ?
                """,
                (since.isoformat(), int(limit)),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT event_time, event_name, event_source, username, resources_json
                FROM timeline
                ORDER BY event_time ASC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

        items: list[dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    "eventTime": str(r["event_time"]),
                    "eventName": str(r["event_name"]),
                    "eventSource": str(r["event_source"]),
                    "username": r["username"],
                    "resources": json.loads(str(r["resources_json"]) or "[]"),
                }
            )
        return items

    def reset_timeline(self) -> None:
        self._conn.execute("DELETE FROM timeline")
        self._conn.commit()


def default_storage(data_dir: str = "data") -> Storage:
    root = _repo_root()
    db_path = root / data_dir / "cloudsentinel.db"
    return Storage(StorageConfig(db_path=db_path))

