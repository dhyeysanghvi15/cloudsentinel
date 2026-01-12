from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .models import ScanMeta, ScanSnapshot


@dataclass(frozen=True)
class StorageConfig:
    mode: str  # local|aws
    artifact_bucket: str | None
    scans_table: str
    region: str
    ddb_endpoint: str | None = None


class Storage:
    def __init__(self, session: boto3.session.Session, cfg: StorageConfig):
        self._session = session
        self._cfg = cfg

        self._dynamodb = session.resource(
            "dynamodb",
            region_name=cfg.region,
            endpoint_url=cfg.ddb_endpoint if cfg.mode == "local" else None,
        )
        self._table = self._dynamodb.Table(cfg.scans_table)

        self._s3 = session.client("s3", region_name=cfg.region)
        self._local_root = Path("api/.local/artifacts")

    def ensure_table(self) -> None:
        if self._cfg.mode != "local":
            return

        try:
            self._dynamodb.create_table(
                TableName=self._cfg.scans_table,
                AttributeDefinitions=[
                    {"AttributeName": "scan_id", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "S"},
                ],
                KeySchema=[{"AttributeName": "scan_id", "KeyType": "HASH"}],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "created_at_index",
                        "KeySchema": [
                            {"AttributeName": "created_at", "KeyType": "HASH"},
                            {"AttributeName": "scan_id", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
                    }
                ],
                ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "ResourceInUseException":
                raise

    def put_snapshot(self, snapshot: ScanSnapshot) -> str:
        key = f"scans/{snapshot.scan_id}.json"
        payload = snapshot.model_dump(mode="json")

        if self._cfg.mode == "aws":
            assert self._cfg.artifact_bucket
            self._s3.put_object(
                Bucket=self._cfg.artifact_bucket,
                Key=key,
                Body=json.dumps(payload).encode("utf-8"),
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )
            return key

        self._local_root.mkdir(parents=True, exist_ok=True)
        (self._local_root / f"{snapshot.scan_id}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        return key

    def get_snapshot(self, scan_id: str) -> dict[str, Any] | None:
        if self._cfg.mode == "aws":
            assert self._cfg.artifact_bucket
            key = f"scans/{scan_id}.json"
            try:
                obj = self._s3.get_object(Bucket=self._cfg.artifact_bucket, Key=key)
                return json.loads(obj["Body"].read().decode("utf-8"))
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") in {"NoSuchKey", "NoSuchBucket"}:
                    return None
                raise

        path = self._local_root / f"{scan_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put_meta(self, meta: ScanMeta) -> None:
        item = {
            "scan_id": meta.scan_id,
            "created_at": meta.created_at.isoformat(),
            "account_id": meta.account_id or "",
            "region": meta.region,
            "score": meta.score,
            "domain_scores": meta.domain_scores,
            "s3_key": meta.s3_key,
        }
        self._table.put_item(Item=item)

    def get_meta(self, scan_id: str) -> ScanMeta | None:
        resp = self._table.get_item(Key={"scan_id": scan_id})
        item = resp.get("Item")
        if not item:
            return None
        return ScanMeta(
            scan_id=item["scan_id"],
            created_at=datetime.fromisoformat(item["created_at"]),
            account_id=item.get("account_id") or None,
            region=item["region"],
            score=int(item["score"]),
            domain_scores={k: int(v) for k, v in (item.get("domain_scores") or {}).items()},
            s3_key=item["s3_key"],
        )

    def list_scans(self, limit: int = 25) -> list[ScanMeta]:
        # For simplicity/cost: scan + client-side sort (MVP).
        resp = self._table.scan(Limit=limit)
        items = resp.get("Items") or []

        metas: list[ScanMeta] = []
        for item in items:
            try:
                metas.append(
                    ScanMeta(
                        scan_id=item["scan_id"],
                        created_at=datetime.fromisoformat(item["created_at"]),
                        account_id=item.get("account_id") or None,
                        region=item["region"],
                        score=int(item["score"]),
                        domain_scores={k: int(v) for k, v in (item.get("domain_scores") or {}).items()},
                        s3_key=item["s3_key"],
                    )
                )
            except Exception:
                continue

        metas.sort(key=lambda m: m.created_at, reverse=True)
        return metas[:limit]

