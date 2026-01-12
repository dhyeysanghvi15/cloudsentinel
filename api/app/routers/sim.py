from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from ..config import get_settings
from ..local_simulator import SimConfig, simulate
from ..models import SimulateResponse
from .deps import storage

router = APIRouter()


@router.post("/api/simulate/{scenario}", response_model=SimulateResponse)
def simulate_scenario(scenario: str) -> SimulateResponse:
    settings = get_settings()
    st = storage()
    op = simulate(
        st,
        scenario,
        SimConfig(
            project_tag=settings.project_tag,
            env=settings.env,
            owner=settings.owner_tag,
            allow_admin_sim=settings.allow_admin_sim,
        ),
    )
    return SimulateResponse(operation_id=op, scenario=scenario, started_at=datetime.now(UTC))


@router.post("/api/simulate/cleanup")
def simulate_cleanup() -> dict:
    settings = get_settings()
    st = storage()
    op = simulate(
        st,
        "cleanup",
        SimConfig(
            project_tag=settings.project_tag,
            env=settings.env,
            owner=settings.owner_tag,
            allow_admin_sim=settings.allow_admin_sim,
        ),
    )
    return {"ok": True, "operation_id": op}


@router.get("/api/timeline")
def timeline(since: str | None = None) -> dict:
    st = storage()
    parsed = None
    if since:
        parsed = datetime.fromisoformat(since.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
    items = st.list_timeline(since=parsed, limit=200)
    return {"items": items}
