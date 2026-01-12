from __future__ import annotations

import json
from typing import Any

import boto3

from .models import PolicyFinding, PolicyValidateResponse


def _local_validate(policy_doc: dict[str, Any]) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    if policy_doc.get("Version") not in {"2012-10-17", "2008-10-17"}:
        findings.append(
            PolicyFinding(
                severity="warning",
                message="Policy Version is missing or unusual.",
                why="AWS IAM evaluates policies based on the version; using a standard version avoids surprises.",
                hint='Set `"Version": "2012-10-17"`.',
            )
        )

    stmts = policy_doc.get("Statement")
    if not stmts:
        return [
            PolicyFinding(
                severity="error",
                message="Policy has no Statement.",
                why="IAM policies must contain at least one statement to be meaningful.",
                hint='Add a `"Statement": [...]` array.',
            )
        ]
    if isinstance(stmts, dict):
        stmts = [stmts]

    for s in stmts:
        effect = s.get("Effect")
        action = s.get("Action")
        resource = s.get("Resource")
        principal = s.get("Principal")

        if effect not in {"Allow", "Deny"}:
            findings.append(
                PolicyFinding(
                    severity="error",
                    message="Statement Effect must be Allow or Deny.",
                    why="Invalid effects can make policies fail validation or be ignored.",
                    hint="Use Effect: Allow or Deny.",
                )
            )

        def _is_star(v: Any) -> bool:
            if v == "*":
                return True
            if isinstance(v, list) and any(x == "*" for x in v):
                return True
            return False

        if _is_star(action):
            findings.append(
                PolicyFinding(
                    severity="warning",
                    message="Statement uses Action '*'.",
                    why="Wildcard actions often grant unintended permissions across services.",
                    hint="Replace '*' with specific actions and add conditions where possible.",
                )
            )
        if _is_star(resource):
            findings.append(
                PolicyFinding(
                    severity="warning",
                    message="Statement uses Resource '*'.",
                    why="Resource wildcards can unintentionally expand access beyond intended targets.",
                    hint="Scope Resource to ARNs (and use conditions like aws:ResourceTag if appropriate).",
                )
            )
        if principal == "*" and effect == "Allow":
            findings.append(
                PolicyFinding(
                    severity="warning",
                    message="Resource policy allows Principal '*'.",
                    why="Public access is a common cause of data exposure.",
                    hint="Scope Principal to specific AWS accounts/roles, or require auth via conditions.",
                )
            )

        if effect == "Allow" and not s.get("Condition"):
            findings.append(
                PolicyFinding(
                    severity="suggestion",
                    message="Consider adding conditions (MFA, source IP, tags).",
                    why="Conditions reduce blast radius even if identities are compromised.",
                    hint="Add Condition with aws:MultiFactorAuthPresent, aws:SourceIp, aws:RequestTag, etc.",
                )
            )

    return findings


def validate_policy(
    session: boto3.session.Session | None,
    policy_json: str,
    policy_type: str,
    *,
    aws_enabled: bool = False,
) -> PolicyValidateResponse:
    try:
        parsed = json.loads(policy_json)
    except Exception as e:
        return PolicyValidateResponse(
            mode="local",
            findings=[
                PolicyFinding(
                    severity="error",
                    message="Invalid JSON.",
                    why="IAM policies must be valid JSON to be evaluated by AWS.",
                    hint=str(e),
                )
            ],
        )

    if not aws_enabled or session is None:
        return PolicyValidateResponse(mode="local", findings=_local_validate(parsed))

    # Prefer Access Analyzer ValidatePolicy (read-only), but fall back if unavailable.
    try:
        aa = session.client("accessanalyzer")
        resp = aa.validate_policy(policyDocument=json.dumps(parsed), policyType=policy_type)
        findings: list[PolicyFinding] = []
        for f in resp.get("findings", []):
            sev = str(f.get("findingType", "SUGGESTION")).lower()
            mapped = "suggestion"
            if "error" in sev:
                mapped = "error"
            elif "warning" in sev:
                mapped = "warning"
            findings.append(
                PolicyFinding(
                    severity=mapped,  # type: ignore[arg-type]
                    message=f.get("findingDetails") or f.get("issueCode") or "Finding",
                    why="Reported by IAM Access Analyzer policy validation.",
                    hint=f.get("learnMoreLink"),
                )
            )
        if not findings:
            findings = [
                PolicyFinding(
                    severity="suggestion",
                    message="No findings returned by Access Analyzer.",
                    why="The policy passed basic validation checks.",
                    hint="Still review for least privilege and add conditions.",
                )
            ]
        return PolicyValidateResponse(mode="access-analyzer", findings=findings)
    except Exception:
        return PolicyValidateResponse(mode="local", findings=_local_validate(parsed))
