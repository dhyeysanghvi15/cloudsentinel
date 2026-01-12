from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ..aws_client import boto_session
from ..config import get_settings
from ..models import SimulateResponse
from ..simulator import SimConfig, cleanup as sim_cleanup, simulate
from ..timeline import get_timeline

router = APIRouter()


@router.post("/api/simulate/{scenario}", response_model=SimulateResponse)
def simulate_scenario(scenario: str) -> SimulateResponse:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    op = simulate(
        session,
        settings.aws_region,
        scenario,
        SimConfig(
            project_tag=settings.project_tag,
            env=settings.env,
            owner=settings.owner_tag,
            allow_admin_sim=settings.allow_admin_sim,
        ),
    )
    return SimulateResponse(operation_id=op, scenario=scenario, started_at=datetime.now(timezone.utc))


@router.post("/api/simulate/cleanup")
def simulate_cleanup() -> dict:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    return sim_cleanup(
        session,
        settings.aws_region,
        SimConfig(
            project_tag=settings.project_tag,
            env=settings.env,
            owner=settings.owner_tag,
            allow_admin_sim=settings.allow_admin_sim,
        ),
    )


@router.get("/api/timeline")
def timeline(since: str | None = None) -> dict:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    parsed = None
    if since:
        parsed = datetime.fromisoformat(since.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    prefix = f"{settings.project_tag}-sim-"
    items = get_timeline(session, settings.aws_region, parsed, prefix)
    return {"items": items, "prefix": prefix}

