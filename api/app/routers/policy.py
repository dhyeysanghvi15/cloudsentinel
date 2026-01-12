from __future__ import annotations

from fastapi import APIRouter

from ..aws_client import boto_session
from ..config import get_settings
from ..models import PolicyValidateRequest, PolicyValidateResponse
from ..policy_doctor import validate_policy

router = APIRouter()


@router.post("/api/policy/validate", response_model=PolicyValidateResponse)
def policy_validate(req: PolicyValidateRequest) -> PolicyValidateResponse:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    return validate_policy(session, req.policy_json, req.policy_type)

