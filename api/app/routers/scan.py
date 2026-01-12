from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..models import ScanMeta, ScanSnapshot
from ..scan_engine import run_scan as run_scan_engine
from .deps import storage

router = APIRouter()


@router.post("/api/scan")
def run_scan() -> ScanSnapshot:
    settings = get_settings()
    st = storage()
    return run_scan_engine(st, settings)


@router.get("/api/scans")
def list_scans(limit: int = Query(default=25, ge=1, le=100)) -> list[ScanMeta]:
    return storage().list_scans(limit=limit)


@router.get("/api/scans/{scan_id}")
def get_scan(scan_id: str) -> dict:
    st = storage()
    try:
        meta, snapshot = st.get_scan(scan_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="scan not found") from None
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
