from __future__ import annotations

from collections.abc import Callable

import boto3

from ..models import CheckResult

CheckFn = Callable[[boto3.session.Session, str], CheckResult]


def all_checks() -> list[CheckFn]:
    from .identity import (
        check_iam_admin_attachments,
        check_iam_old_access_keys,
        check_iam_password_policy,
        check_root_mfa,
    )
    from .logging import (
        check_cloudtrail_enabled,
        check_cloudtrail_multiregion,
        check_log_group_retention,
    )
    from .network import check_sg_open_sensitive_ports
    from .protection import (
        check_kms_key_policy_sanity,
        check_s3_access_logging_sampled,
        check_s3_default_encryption_sampled,
        check_s3_public_access_block,
    )
    from .readiness import check_aws_config_recorder_present

    return [
        check_root_mfa,
        check_iam_password_policy,
        check_iam_old_access_keys,
        check_iam_admin_attachments,
        check_cloudtrail_enabled,
        check_cloudtrail_multiregion,
        check_log_group_retention,
        check_s3_public_access_block,
        check_s3_default_encryption_sampled,
        check_s3_access_logging_sampled,
        check_kms_key_policy_sanity,
        check_sg_open_sensitive_ports,
        check_aws_config_recorder_present,
    ]
