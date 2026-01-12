from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import CheckResult
from .storage import Storage


def local_checks(st: Storage) -> list[CheckResult]:
    """
    Offline-first posture checks.

    These are "cloud-realistic" but do not call AWS APIs unless explicitly enabled elsewhere.
    They also react to the local simulator timeline so scans can show diffs/regressions.
    """

    items = st.list_timeline(since=datetime.now(timezone.utc) - timedelta(days=7), limit=1000)
    names = {str(i.get("eventName") or "") for i in items}

    saw_public_acl = "PutBucketAcl" in names
    saw_access_key = "CreateAccessKey" in names
    saw_admin_attach = "AttachUserPolicy" in names
    saw_any = bool(items)

    results: list[CheckResult] = [
        CheckResult(
            id="iam.root_mfa",
            title="Root account MFA enabled",
            severity="critical",
            status="warn",
            domain="Identity & Access",
            evidence={"mode": "local", "note": "offline lab: assumes break-glass exists, MFA not proven"},
            recommendation="Enable MFA on the root account and lock root credentials away.",
            references=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html"],
            weight=15,
        ),
        CheckResult(
            id="iam.password_policy",
            title="IAM account password policy strength",
            severity="high",
            status="pass",
            domain="Identity & Access",
            evidence={"mode": "local", "baseline": "strong"},
            recommendation="Prefer SSO/STS; if passwords exist, require >=12 chars and symbols+numbers.",
            references=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html"],
            weight=10,
        ),
        CheckResult(
            id="iam.old_access_keys",
            title="Access keys older than 90 days",
            severity="medium",
            status="warn" if saw_access_key else "pass",
            domain="Identity & Access",
            evidence={"mode": "local", "signal": "CreateAccessKey", "seen": saw_access_key},
            recommendation="Rotate/remove long-lived keys; prefer short-lived credentials (SSO/STS).",
            references=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#best-practices-credentials"],
            weight=10,
        ),
        CheckResult(
            id="iam.admin_attachments",
            title="AdministratorAccess/PowerUserAccess attachments",
            severity="high",
            status="warn" if saw_admin_attach else "pass",
            domain="Identity & Access",
            evidence={"mode": "local", "signal": "AttachUserPolicy", "seen": saw_admin_attach},
            recommendation="Minimize broad admin policies; use least privilege and scoped roles with conditions.",
            references=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#lock-away-credentials"],
            weight=12,
        ),
        CheckResult(
            id="log.cloudtrail_enabled",
            title="Audit trail coverage (timeline store)",
            severity="high",
            status="pass",
            domain="Logging & Monitoring",
            evidence={"mode": "local", "store": "sqlite"},
            recommendation="Capture management events and alert on sensitive actions (policy changes, public access).",
            references=[],
            weight=10,
        ),
        CheckResult(
            id="log.alerting_baseline",
            title="Detection baseline for high-risk events",
            severity="medium",
            status="warn" if saw_any else "fail",
            domain="Logging & Monitoring",
            evidence={"mode": "local", "events_last_7d": len(items)},
            recommendation="Start with a baseline: policy attachments, access key creation, and public ACL attempts.",
            references=[],
            weight=10,
        ),
        CheckResult(
            id="net.sg_open_sensitive_ports",
            title="Security groups open to 0.0.0.0/0 on sensitive ports",
            severity="critical",
            status="warn",
            domain="Network Exposure",
            evidence={"mode": "local", "note": "offline lab: no VPC inventory"},
            recommendation="Eliminate direct internet exposure on admin/database ports; use VPN/bastion/SSM.",
            references=["https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html"],
            weight=15,
        ),
        CheckResult(
            id="data.s3_public_access_block",
            title="Public access guardrails for object storage",
            severity="high",
            status="warn" if saw_public_acl else "pass",
            domain="Data Protection",
            evidence={"mode": "local", "signal": "PutBucketAcl", "seen": saw_public_acl},
            recommendation="Enable public access blocks; require explicit principals; review ACL usage.",
            references=[],
            weight=12,
        ),
        CheckResult(
            id="data.encryption_at_rest",
            title="Encryption at rest for data stores",
            severity="medium",
            status="pass",
            domain="Data Protection",
            evidence={"mode": "local", "baseline": "enabled"},
            recommendation="Use encryption by default and rotate keys where appropriate.",
            references=[],
            weight=8,
        ),
        CheckResult(
            id="ready.ticketing_workflow",
            title="Remediation workflow defined",
            severity="low",
            status="pass",
            domain="Readiness",
            evidence={"mode": "local", "note": "sample workflow"},
            recommendation="Track findings in tickets with SLA by severity; verify fixes via scan diffs.",
            references=[],
            weight=5,
        ),
    ]
    return results

