from __future__ import annotations

from ..config import get_settings
from ..storage import Storage, default_storage


def storage() -> Storage:
    settings = get_settings()
    return default_storage(settings.data_dir)
