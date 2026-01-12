from __future__ import annotations

import boto3

from ..models import CheckResult


def check_cloudtrail_enabled(session: boto3.session.Session, region: str) -> CheckResult:
    ct = session.client("cloudtrail", region_name=region)
    try:
        trails = ct.describe_trails(includeShadowTrails=False).get("trailList", [])
        enabled = []
        for t in trails:
            name = t.get("Name")
            arn = t.get("TrailARN")
            status = ct.get_trail_status(Name=name)
            if status.get("IsLogging"):
                enabled.append({"name": name, "arn": arn, "home_region": t.get("HomeRegion")})

        ok = len(enabled) > 0
        return CheckResult(
            id="logging.cloudtrail_enabled",
            title="CloudTrail enabled (logging)",
            severity="critical",
            status="pass" if ok else "fail",
            domain="Logging & Traceability",
            evidence={"logging_trails": enabled, "count": len(enabled)},
            recommendation="Enable CloudTrail and ensure it is logging to an S3 bucket (and optionally CloudWatch Logs).",
            references=["https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail.html"],
            weight=15,
        )
    except Exception as e:
        return CheckResult(
            id="logging.cloudtrail_enabled",
            title="CloudTrail enabled (logging)",
            severity="critical",
            status="error",
            domain="Logging & Traceability",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call cloudtrail:DescribeTrails and cloudtrail:GetTrailStatus.",
            references=[],
            weight=15,
        )


def check_cloudtrail_multiregion(session: boto3.session.Session, region: str) -> CheckResult:
    ct = session.client("cloudtrail", region_name=region)
    try:
        trails = ct.describe_trails(includeShadowTrails=False).get("trailList", [])
        multi = [t for t in trails if t.get("IsMultiRegionTrail")]
        status = "pass" if multi else "warn"
        return CheckResult(
            id="logging.cloudtrail_multiregion",
            title="CloudTrail multi-region trail recommended",
            severity="high",
            status=status,
            domain="IR Readiness",
            evidence={"multi_region_trails": [{"name": t.get("Name"), "home_region": t.get("HomeRegion")} for t in multi]},
            recommendation="Use a multi-region trail to capture management events across regions.",
            references=["https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html#cloudtrail-concepts-management-events"],
            weight=10,
        )
    except Exception as e:
        return CheckResult(
            id="logging.cloudtrail_multiregion",
            title="CloudTrail multi-region trail recommended",
            severity="high",
            status="error",
            domain="IR Readiness",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call cloudtrail:DescribeTrails.",
            references=[],
            weight=10,
        )


def check_log_group_retention(session: boto3.session.Session, region: str) -> CheckResult:
    logs = session.client("logs", region_name=region)
    try:
        groups = []
        paginator = logs.get_paginator("describe_log_groups")
        for page in paginator.paginate(limit=10):
            for g in page.get("logGroups", []):
                retention = g.get("retentionInDays")
                if retention is None or retention > 90:
                    groups.append({"logGroupName": g.get("logGroupName"), "retentionInDays": retention})
            break  # keep it cheap for MVP

        status = "pass" if not groups else "warn"
        return CheckResult(
            id="logging.log_group_retention",
            title="CloudWatch Logs retention set (avoid infinite retention)",
            severity="low",
            status=status,
            domain="Logging & Traceability",
            evidence={"noncompliant_samples": groups[:20], "count": len(groups)},
            recommendation="Set log retention to a reasonable period (e.g., 7–90 days) to control cost and exposure.",
            references=["https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html"],
            weight=8,
        )
    except Exception as e:
        return CheckResult(
            id="logging.log_group_retention",
            title="CloudWatch Logs retention set (avoid infinite retention)",
            severity="low",
            status="error",
            domain="Logging & Traceability",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call logs:DescribeLogGroups.",
            references=[],
            weight=8,
        )

