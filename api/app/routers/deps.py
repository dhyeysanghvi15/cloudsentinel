from __future__ import annotations

from ..aws_client import boto_session
from ..config import get_settings
from ..storage import Storage, StorageConfig


def storage() -> Storage:
    settings = get_settings()
    session = boto_session(settings.aws_region)
    st = Storage(
        session=session,
        cfg=StorageConfig(
            mode=settings.storage_mode,
            artifact_bucket=settings.artifact_bucket,
            scans_table=settings.scans_table,
            region=settings.aws_region,
            ddb_endpoint=settings.ddb_endpoint,
        ),
    )
    st.ensure_table()
    return st

