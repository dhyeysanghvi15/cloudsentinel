from __future__ import annotations

from datetime import datetime, timezone

from ulid import ULID

from .aws_client import boto_session, get_account_id
from .checks.registry import all_checks
from .config import Settings
from .local_checks import local_checks
from .models import ScanSnapshot
from .scoring import compute_score
from .storage import Storage


def run_scan(st: Storage, settings: Settings) -> ScanSnapshot:
    scan_id = str(ULID())
    created_at = datetime.now(timezone.utc)

    account_id = None
    results = None

    aws_note = None
    if settings.aws_scan_enabled:
        session = boto_session(settings.aws_region)
        account_id = get_account_id(session)
        if not account_id:
            results = local_checks(st)
            aws_note = "AWS_SCAN_ENABLED=true but credentials were not detected; ran offline checks instead."
        else:
            results = [fn(session, settings.aws_region) for fn in all_checks()]
    else:
        results = local_checks(st)

    score, breakdown = compute_score(results)
    if aws_note:
        breakdown = {**breakdown, "aws": {"enabled": True, "account_id": account_id, "note": aws_note}}
    else:
        breakdown = {**breakdown, "aws": {"enabled": bool(settings.aws_scan_enabled), "account_id": account_id}}
    snapshot = ScanSnapshot(
        scan_id=scan_id,
        created_at=created_at,
        account_id=account_id,
        region=settings.aws_region,
        results=results,
        score=score,
        breakdown=breakdown,
    )
    st.put_scan(snapshot)
    return snapshot
