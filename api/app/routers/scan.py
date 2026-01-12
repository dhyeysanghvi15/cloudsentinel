from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from ulid import ULID

from ..aws_client import boto_session, get_account_id
from ..checks.registry import all_checks
from ..config import get_settings
from ..models import ScanMeta, ScanSnapshot
from ..scoring import compute_score
from .deps import storage

router = APIRouter()


@router.post("/api/scan")
def run_scan() -> ScanSnapshot:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    account_id = get_account_id(session)
    scan_id = str(ULID())
    created_at = datetime.now(timezone.utc)

    results = [fn(session, settings.aws_region) for fn in all_checks()]
    score, breakdown = compute_score(results)

    snapshot = ScanSnapshot(
        scan_id=scan_id,
        created_at=created_at,
        account_id=account_id,
        region=settings.aws_region,
        results=results,
        score=score,
        breakdown=breakdown,
    )

    st = storage()
    key = st.put_snapshot(snapshot)
    st.put_meta(
        ScanMeta(
            scan_id=scan_id,
            created_at=created_at,
            account_id=account_id,
            region=settings.aws_region,
            score=score,
            domain_scores=breakdown.get("domain_scores") or {},
            s3_key=key,
        )
    )
    return snapshot


@router.get("/api/scans")
def list_scans(limit: int = Query(default=25, ge=1, le=100)) -> list[ScanMeta]:
    return storage().list_scans(limit=limit)


@router.get("/api/scans/{scan_id}")
def get_scan(scan_id: str) -> dict:
    st = storage()
    meta = st.get_meta(scan_id)
    if not meta:
        raise HTTPException(status_code=404, detail="scan not found")
    snapshot = st.get_snapshot(scan_id)
    return {"meta": meta.model_dump(mode="json"), "snapshot": snapshot}


@router.get("/api/score/latest")
def latest_score() -> dict:
    scans = storage().list_scans(limit=10)
    if not scans:
        return {"score": None, "scan_id": None}
    latest = scans[0]
    return {
        "score": latest.score,
        "scan_id": latest.scan_id,
        "created_at": latest.created_at.isoformat(),
        "domain_scores": latest.domain_scores,
    }

