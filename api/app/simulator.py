from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3


@dataclass(frozen=True)
class SimConfig:
    project_tag: str
    env: str
    owner: str
    allow_admin_sim: bool


def _tags(cfg: SimConfig) -> list[dict[str, str]]:
    return [
        {"Key": "Project", "Value": cfg.project_tag},
        {"Key": "Env", "Value": cfg.env},
        {"Key": "Owner", "Value": cfg.owner},
    ]


def simulate(session: boto3.session.Session, region: str, scenario: str, cfg: SimConfig) -> str:
    operation_id = f"op-{int(time.time())}"
    if scenario == "iam-user":
        _scenario_iam_user(session, region, cfg, operation_id)
        return operation_id
    if scenario == "s3-public-acl":
        _scenario_s3_public_acl(session, region, cfg, operation_id)
        return operation_id
    if scenario == "admin-attach-attempt":
        if not cfg.allow_admin_sim:
            raise ValueError("Admin attach simulation is disabled (set ALLOW_ADMIN_SIM=1).")
        _scenario_admin_attach_attempt(session, region, cfg, operation_id)
        return operation_id
    raise ValueError(f"Unknown scenario: {scenario}")


def cleanup(session: boto3.session.Session, region: str, cfg: SimConfig) -> dict:
    iam = session.client("iam", region_name=region)
    s3 = session.client("s3", region_name=region)
    deleted_users: list[str] = []
    deleted_buckets: list[str] = []

    prefix = f"{cfg.project_tag}-sim-"
    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for u in page.get("Users", []):
            name = u["UserName"]
            if not name.startswith(prefix):
                continue
            try:
                _delete_iam_user(iam, name)
                deleted_users.append(name)
            except Exception:
                continue

    buckets = s3.list_buckets().get("Buckets", [])
    for b in buckets:
        name = b["Name"]
        if not name.startswith(prefix):
            continue
        try:
            _empty_and_delete_bucket(s3, name)
            deleted_buckets.append(name)
        except Exception:
            continue

    return {"deleted_users": deleted_users, "deleted_buckets": deleted_buckets}


def _scenario_iam_user(session: boto3.session.Session, region: str, cfg: SimConfig, op: str) -> None:
    iam = session.client("iam", region_name=region)
    username = f"{cfg.project_tag}-sim-user-{op}"
    iam.create_user(UserName=username, Tags=_tags(cfg))
    iam.put_user_policy(
        UserName=username,
        PolicyName=f"{cfg.project_tag}-sim-inline",
        PolicyDocument="""
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets"],
      "Resource": "*"
    }
  ]
}
""".strip(),
    )


def _scenario_admin_attach_attempt(session: boto3.session.Session, region: str, cfg: SimConfig, op: str) -> None:
    iam = session.client("iam", region_name=region)
    username = f"{cfg.project_tag}-sim-admin-{op}"
    iam.create_user(UserName=username, Tags=_tags(cfg))
    try:
        iam.attach_user_policy(
            UserName=username,
            PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess",
        )
        # Immediately detach to keep it safe.
        iam.detach_user_policy(
            UserName=username,
            PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess",
        )
    finally:
        _delete_iam_user(iam, username)


def _scenario_s3_public_acl(session: boto3.session.Session, region: str, cfg: SimConfig, op: str) -> None:
    s3 = session.client("s3", region_name=region)
    bucket = f"{cfg.project_tag}-sim-s3-{op}".lower()
    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})
    s3.put_bucket_tagging(Bucket=bucket, Tagging={"TagSet": _tags(cfg)})
    try:
        # Attempt public ACL; if account has PublicAccessBlock, this will fail but still generates CloudTrail.
        s3.put_bucket_acl(Bucket=bucket, ACL="public-read")
        s3.put_bucket_acl(Bucket=bucket, ACL="private")
    finally:
        _empty_and_delete_bucket(s3, bucket)


def _delete_iam_user(iam, username: str) -> None:
    attached = iam.list_attached_user_policies(UserName=username).get("AttachedPolicies", [])
    for pol in attached:
        iam.detach_user_policy(UserName=username, PolicyArn=pol["PolicyArn"])
    inline = iam.list_user_policies(UserName=username).get("PolicyNames", [])
    for name in inline:
        iam.delete_user_policy(UserName=username, PolicyName=name)
    keys = iam.list_access_keys(UserName=username).get("AccessKeyMetadata", [])
    for k in keys:
        iam.delete_access_key(UserName=username, AccessKeyId=k["AccessKeyId"])
    iam.delete_user(UserName=username)


def _empty_and_delete_bucket(s3, bucket: str) -> None:
    # Handle both unversioned and versioned buckets.
    try:
        resp = s3.list_objects_v2(Bucket=bucket)
        for obj in resp.get("Contents", []):
            s3.delete_object(Bucket=bucket, Key=obj["Key"])
    except Exception:
        pass
    try:
        resp = s3.list_object_versions(Bucket=bucket)
        for v in resp.get("Versions", []):
            s3.delete_object(Bucket=bucket, Key=v["Key"], VersionId=v["VersionId"])
        for v in resp.get("DeleteMarkers", []):
            s3.delete_object(Bucket=bucket, Key=v["Key"], VersionId=v["VersionId"])
    except Exception:
        pass
    try:
        s3.delete_bucket_tagging(Bucket=bucket)
    except Exception:
        pass
    s3.delete_bucket(Bucket=bucket)
