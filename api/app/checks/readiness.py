from __future__ import annotations

import boto3

from ..models import CheckResult


def check_aws_config_recorder_present(session: boto3.session.Session, region: str) -> CheckResult:
    cfg = session.client("config", region_name=region)
    try:
        recorders = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])
        status = "pass" if recorders else "warn"
        return CheckResult(
            id="ir.aws_config_recorder",
            title="AWS Config presence (configuration recorder)",
            severity="medium",
            status=status,
            domain="IR Readiness",
            evidence={"recorders": [{"name": r.get("name"), "roleARN": r.get("roleARN")} for r in recorders]},
            recommendation="Enable AWS Config (at least in key regions) to support forensics and drift detection.",
            references=["https://docs.aws.amazon.com/config/latest/developerguide/WhatIsConfig.html"],
            weight=8,
        )
    except Exception as e:
        return CheckResult(
            id="ir.aws_config_recorder",
            title="AWS Config presence (configuration recorder)",
            severity="medium",
            status="error",
            domain="IR Readiness",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call config:DescribeConfigurationRecorders.",
            references=[],
            weight=8,
        )

