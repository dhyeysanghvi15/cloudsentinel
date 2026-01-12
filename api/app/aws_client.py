from __future__ import annotations

import os
from dataclasses import dataclass

import boto3


@dataclass(frozen=True)
class AwsContext:
    region: str


def boto_session(region: str) -> boto3.session.Session:
    profile = os.getenv("AWS_PROFILE") or None
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    return boto3.Session(region_name=region)


def get_account_id(session: boto3.session.Session) -> str | None:
    try:
        return session.client("sts").get_caller_identity().get("Account")
    except Exception:
        return None

