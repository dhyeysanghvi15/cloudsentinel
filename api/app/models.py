from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

CheckStatus = Literal["pass", "fail", "warn", "error", "skip"]
Severity = Literal["low", "medium", "high", "critical"]


class CheckResult(BaseModel):
    id: str
    title: str
    severity: Severity
    status: CheckStatus
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    references: list[str] = Field(default_factory=list)
    domain: str
    weight: int = 10


class ScanSnapshot(BaseModel):
    scan_id: str
    created_at: datetime
    account_id: str | None = None
    region: str
    results: list[CheckResult]
    score: int
    breakdown: dict[str, Any]


class ScanMeta(BaseModel):
    scan_id: str
    created_at: datetime
    account_id: str | None = None
    region: str
    score: int
    domain_scores: dict[str, int]
    s3_key: str | None = None


class PolicyValidateRequest(BaseModel):
    policy_json: str
    policy_type: Literal["IDENTITY_POLICY", "RESOURCE_POLICY"] = "IDENTITY_POLICY"


class PolicyFinding(BaseModel):
    severity: Literal["error", "warning", "suggestion"]
    message: str
    why: str
    hint: str | None = None


class PolicyValidateResponse(BaseModel):
    mode: Literal["access-analyzer", "local"]
    findings: list[PolicyFinding]


class SimulateResponse(BaseModel):
    operation_id: str
    scenario: str
    started_at: datetime
    notes: str | None = None
