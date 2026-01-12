from __future__ import annotations

import json

import boto3

from ..models import CheckResult


def check_s3_public_access_block(session: boto3.session.Session, region: str) -> CheckResult:
    s3 = session.client("s3", region_name=region)
    try:
        # Sample 10 buckets max to keep costs down.
        buckets = s3.list_buckets().get("Buckets", [])[:10]
        bad: list[dict] = []
        for b in buckets:
            name = b["Name"]
            try:
                pab = s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
                if not all(
                    [
                        pab.get("BlockPublicAcls"),
                        pab.get("IgnorePublicAcls"),
                        pab.get("BlockPublicPolicy"),
                        pab.get("RestrictPublicBuckets"),
                    ]
                ):
                    bad.append({"bucket": name, "public_access_block": pab})
            except Exception as e:
                bad.append({"bucket": name, "error": str(e)})

        status = "pass" if not bad else "warn"
        return CheckResult(
            id="s3.public_access_block",
            title="S3 public access block enabled (sampled buckets)",
            severity="high",
            status=status,
            domain="Data Protection",
            evidence={"noncompliant_samples": bad[:10], "sampled": len(buckets)},
            recommendation="Enable S3 Public Access Block at account and bucket level; avoid public ACLs/policies.",
            references=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html"],
            weight=12,
        )
    except Exception as e:
        return CheckResult(
            id="s3.public_access_block",
            title="S3 public access block enabled (sampled buckets)",
            severity="high",
            status="error",
            domain="Data Protection",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call s3:ListAllMyBuckets and s3:GetBucketPublicAccessBlock.",
            references=[],
            weight=12,
        )


def check_s3_default_encryption_sampled(session: boto3.session.Session, region: str) -> CheckResult:
    s3 = session.client("s3", region_name=region)
    try:
        buckets = s3.list_buckets().get("Buckets", [])[:10]
        missing: list[dict] = []
        for b in buckets:
            name = b["Name"]
            try:
                enc = s3.get_bucket_encryption(Bucket=name)["ServerSideEncryptionConfiguration"]
                rules = enc.get("Rules") or []
                if not rules:
                    missing.append({"bucket": name, "encryption": "no rules"})
            except Exception as e:
                # If bucket has no encryption config, AWS returns an error.
                missing.append({"bucket": name, "error": str(e)})

        status = "pass" if not missing else "warn"
        return CheckResult(
            id="s3.default_encryption",
            title="S3 default encryption enabled (sampled buckets)",
            severity="high",
            status=status,
            domain="Data Protection",
            evidence={"noncompliant_samples": missing[:10], "sampled": len(buckets)},
            recommendation="Enable default encryption (SSE-S3 or SSE-KMS) for all buckets storing sensitive data.",
            references=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html"],
            weight=10,
        )
    except Exception as e:
        return CheckResult(
            id="s3.default_encryption",
            title="S3 default encryption enabled (sampled buckets)",
            severity="high",
            status="error",
            domain="Data Protection",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call s3:GetEncryptionConfiguration and s3:ListAllMyBuckets.",
            references=[],
            weight=10,
        )


def check_s3_access_logging_sampled(session: boto3.session.Session, region: str) -> CheckResult:
    s3 = session.client("s3", region_name=region)
    try:
        buckets = s3.list_buckets().get("Buckets", [])[:10]
        no_logging: list[dict] = []
        for b in buckets:
            name = b["Name"]
            try:
                logging = s3.get_bucket_logging(Bucket=name).get("LoggingEnabled")
                if not logging:
                    no_logging.append({"bucket": name})
            except Exception as e:
                no_logging.append({"bucket": name, "error": str(e)})

        status = "pass" if not no_logging else "warn"
        return CheckResult(
            id="s3.access_logging",
            title="S3 server access logging enabled (sampled buckets)",
            severity="medium",
            status=status,
            domain="Logging & Traceability",
            evidence={"noncompliant_samples": no_logging[:10], "sampled": len(buckets)},
            recommendation="Enable S3 server access logging (or CloudTrail data events) for high-value buckets.",
            references=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html"],
            weight=8,
        )
    except Exception as e:
        return CheckResult(
            id="s3.access_logging",
            title="S3 server access logging enabled (sampled buckets)",
            severity="medium",
            status="error",
            domain="Logging & Traceability",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call s3:GetBucketLogging and s3:ListAllMyBuckets.",
            references=[],
            weight=8,
        )


def check_kms_key_policy_sanity(session: boto3.session.Session, region: str) -> CheckResult:
    kms = session.client("kms", region_name=region)
    try:
        keys = kms.list_keys(Limit=5).get("Keys", [])
        findings: list[dict] = []
        for k in keys:
            key_id = k["KeyId"]
            try:
                policy = kms.get_key_policy(KeyId=key_id, PolicyName="default")["Policy"]
                doc = json.loads(policy)
                statements = doc.get("Statement") or []
                for s in statements:
                    if s.get("Effect") != "Allow":
                        continue
                    principal = s.get("Principal")
                    action = s.get("Action")
                    resource = s.get("Resource")
                    if principal == "*" and (action == "*" or action == "kms:*"):
                        findings.append({"key_id": key_id, "issue": "Wildcard principal with broad KMS actions", "stmt": s})
                    if resource == "*" and (action == "*" or action == "kms:*"):
                        findings.append({"key_id": key_id, "issue": "Resource '*' with broad KMS actions", "stmt": s})
            except Exception:
                continue

        status = "pass" if not findings else "warn"
        return CheckResult(
            id="kms.key_policy_sanity",
            title="KMS key policy sanity (sampled keys)",
            severity="high",
            status=status,
            domain="Data Protection",
            evidence={"findings": findings[:10], "sampled": len(keys)},
            recommendation="Avoid wildcard principals and overly broad KMS permissions; scope keys to workloads and roles.",
            references=["https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html"],
            weight=10,
        )
    except Exception as e:
        return CheckResult(
            id="kms.key_policy_sanity",
            title="KMS key policy sanity (sampled keys)",
            severity="high",
            status="error",
            domain="Data Protection",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call kms:ListKeys and kms:GetKeyPolicy.",
            references=[],
            weight=10,
        )
