from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ulid import ULID

from .storage import Storage


@dataclass(frozen=True)
class SimConfig:
    project_tag: str
    env: str
    owner: str
    allow_admin_sim: bool


def _prefix(cfg: SimConfig) -> str:
    return f"{cfg.project_tag}-sim-"


def _events_for_scenario(scenario: str, cfg: SimConfig) -> list[dict]:
    now = datetime.now(timezone.utc)

    def t(delta_ms: int) -> str:
        return (now.timestamp() + delta_ms / 1000.0)

    def iso(ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    prefix = _prefix(cfg)
    if scenario == "iam-user":
        return [
            {
                "eventTime": iso(t(0)),
                "eventName": "CreateUser",
                "eventSource": "iam.amazonaws.com",
                "username": "local-user",
                "resources": [{"ResourceName": f"{prefix}user-local", "ResourceType": "AWS::IAM::User"}],
            },
            {
                "eventTime": iso(t(900)),
                "eventName": "PutUserPolicy",
                "eventSource": "iam.amazonaws.com",
                "username": "local-user",
                "resources": [{"ResourceName": f"{prefix}user-local", "ResourceType": "AWS::IAM::User"}],
            },
        ]
    if scenario == "s3-public-acl":
        return [
            {
                "eventTime": iso(t(0)),
                "eventName": "CreateBucket",
                "eventSource": "s3.amazonaws.com",
                "username": "local-user",
                "resources": [{"ResourceName": f"{prefix}bucket-local", "ResourceType": "AWS::S3::Bucket"}],
            },
            {
                "eventTime": iso(t(1200)),
                "eventName": "PutBucketAcl",
                "eventSource": "s3.amazonaws.com",
                "username": "local-user",
                "resources": [{"ResourceName": f"{prefix}bucket-local", "ResourceType": "AWS::S3::Bucket"}],
            },
        ]
    if scenario == "admin-attach-attempt":
        if not cfg.allow_admin_sim:
            raise ValueError("Admin attach simulation is disabled (set ALLOW_ADMIN_SIM=1).")
        return [
            {
                "eventTime": iso(t(0)),
                "eventName": "AttachUserPolicy",
                "eventSource": "iam.amazonaws.com",
                "username": "local-user",
                "resources": [{"ResourceName": f"{prefix}user-local", "ResourceType": "AWS::IAM::User"}],
            }
        ]
    if scenario == "cleanup":
        return [
            {
                "eventTime": iso(t(0)),
                "eventName": "Cleanup",
                "eventSource": "cloudsentinel.local",
                "username": "local-user",
                "resources": [],
            }
        ]
    raise ValueError(f"Unknown scenario: {scenario}")


def simulate(st: Storage, scenario: str, cfg: SimConfig) -> str:
    operation_id = str(ULID())
    if scenario == "cleanup":
        st.reset_timeline()
        st.append_timeline_events(events=_events_for_scenario("cleanup", cfg), scenario=scenario, operation_id=operation_id)
        return operation_id
    st.append_timeline_events(events=_events_for_scenario(scenario, cfg), scenario=scenario, operation_id=operation_id)
    return operation_id

