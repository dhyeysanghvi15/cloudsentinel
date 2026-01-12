from __future__ import annotations

from datetime import UTC, datetime

import boto3

from ..models import CheckResult


def check_root_mfa(session: boto3.session.Session, region: str) -> CheckResult:
    iam = session.client("iam", region_name=region)
    try:
        summary = iam.get_account_summary()["SummaryMap"]
        enabled = int(summary.get("AccountMFAEnabled", 0)) == 1
        return CheckResult(
            id="iam.root_mfa",
            title="Root account MFA enabled",
            severity="critical",
            status="pass" if enabled else "fail",
            domain="Identity & Access",
            evidence={"AccountMFAEnabled": summary.get("AccountMFAEnabled")},
            recommendation="Enable MFA on the root account and lock root credentials away.",
            references=[
                "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html"
            ],
            weight=15,
        )
    except Exception as e:
        return CheckResult(
            id="iam.root_mfa",
            title="Root account MFA enabled",
            severity="critical",
            status="error",
            domain="Identity & Access",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call iam:GetAccountSummary.",
            references=[],
            weight=15,
        )


def check_iam_password_policy(session: boto3.session.Session, region: str) -> CheckResult:
    iam = session.client("iam", region_name=region)
    try:
        policy = iam.get_account_password_policy()["PasswordPolicy"]
        required = bool(policy.get("RequireSymbols")) and bool(policy.get("RequireNumbers"))
        min_len = int(policy.get("MinimumPasswordLength", 0))
        ok = required and min_len >= 12
        return CheckResult(
            id="iam.password_policy",
            title="IAM account password policy strength",
            severity="high",
            status="pass" if ok else "warn",
            domain="Identity & Access",
            evidence={
                "MinimumPasswordLength": policy.get("MinimumPasswordLength"),
                "RequireSymbols": policy.get("RequireSymbols"),
                "RequireNumbers": policy.get("RequireNumbers"),
                "RequireUppercaseCharacters": policy.get("RequireUppercaseCharacters"),
                "RequireLowercaseCharacters": policy.get("RequireLowercaseCharacters"),
            },
            recommendation="Set a strong password policy (>=12 chars, numbers+symbols, rotation where appropriate).",
            references=[
                "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html"
            ],
            weight=10,
        )
    except iam.exceptions.NoSuchEntityException:
        return CheckResult(
            id="iam.password_policy",
            title="IAM account password policy strength",
            severity="high",
            status="warn",
            domain="Identity & Access",
            evidence={"PasswordPolicy": None},
            recommendation="Define an account password policy (even if you prefer SSO).",
            references=[],
            weight=10,
        )
    except Exception as e:
        return CheckResult(
            id="iam.password_policy",
            title="IAM account password policy strength",
            severity="high",
            status="error",
            domain="Identity & Access",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call iam:GetAccountPasswordPolicy.",
            references=[],
            weight=10,
        )


def check_iam_old_access_keys(session: boto3.session.Session, region: str) -> CheckResult:
    iam = session.client("iam", region_name=region)
    now = datetime.now(UTC)
    threshold_days = 90
    stale: list[dict] = []
    try:
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for user in page.get("Users", []):
                username = user["UserName"]
                keys = iam.list_access_keys(UserName=username).get("AccessKeyMetadata", [])
                for k in keys:
                    created = k["CreateDate"]
                    age_days = (now - created).days
                    if age_days >= threshold_days:
                        stale.append(
                            {"user": username, "access_key_id": k["AccessKeyId"], "age_days": age_days}
                        )

        status = "pass" if not stale else "warn"
        return CheckResult(
            id="iam.old_access_keys",
            title=f"Access keys older than {threshold_days} days",
            severity="medium",
            status=status,
            domain="Identity & Access",
            evidence={"stale_keys": stale[:50], "count": len(stale), "threshold_days": threshold_days},
            recommendation="Rotate or remove old access keys; prefer short-lived credentials (SSO/STS).",
            references=[
                "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#best-practices-credentials"
            ],
            weight=10,
        )
    except Exception as e:
        return CheckResult(
            id="iam.old_access_keys",
            title=f"Access keys older than {threshold_days} days",
            severity="medium",
            status="error",
            domain="Identity & Access",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call iam:ListUsers and iam:ListAccessKeys.",
            references=[],
            weight=10,
        )


def check_iam_admin_attachments(session: boto3.session.Session, region: str) -> CheckResult:
    iam = session.client("iam", region_name=region)
    admin_arns = {
        "arn:aws:iam::aws:policy/AdministratorAccess",
        "arn:aws:iam::aws:policy/PowerUserAccess",
    }
    attached: list[dict] = []
    try:
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for user in page.get("Users", []):
                username = user["UserName"]
                for pol in iam.list_attached_user_policies(UserName=username).get("AttachedPolicies", []):
                    if pol["PolicyArn"] in admin_arns:
                        attached.append({"type": "user", "name": username, "policy_arn": pol["PolicyArn"]})

        paginator = iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page.get("Roles", []):
                role_name = role["RoleName"]
                for pol in iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", []):
                    if pol["PolicyArn"] in admin_arns:
                        attached.append({"type": "role", "name": role_name, "policy_arn": pol["PolicyArn"]})

        status = "pass" if not attached else "warn"
        return CheckResult(
            id="iam.admin_attachments",
            title="AdministratorAccess/PowerUserAccess attachments",
            severity="high",
            status=status,
            domain="Identity & Access",
            evidence={"attachments": attached[:50], "count": len(attached)},
            recommendation="Minimize broad admin policies; use least privilege and scoped roles with MFA/conditions.",
            references=[
                "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#lock-away-credentials"
            ],
            weight=12,
        )
    except Exception as e:
        return CheckResult(
            id="iam.admin_attachments",
            title="AdministratorAccess/PowerUserAccess attachments",
            severity="high",
            status="error",
            domain="Identity & Access",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can list users/roles and attached policies.",
            references=[],
            weight=12,
        )
