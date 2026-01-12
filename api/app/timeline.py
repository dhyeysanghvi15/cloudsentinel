from __future__ import annotations

from datetime import datetime, timezone

import boto3


def get_timeline(session: boto3.session.Session, region: str, since: datetime | None, prefix: str) -> list[dict]:
    ct = session.client("cloudtrail", region_name=region)
    kwargs = {"MaxResults": 50}
    if since:
        kwargs["StartTime"] = since

    events = ct.lookup_events(**kwargs).get("Events", [])
    timeline: list[dict] = []
    for e in events:
        # Filter cheaply on known resource prefix (names show up as resources in many events).
        resources = e.get("Resources") or []
        if not any((r.get("ResourceName") or "").startswith(prefix) for r in resources):
            continue
        timeline.append(
            {
                "eventTime": e.get("EventTime").isoformat() if hasattr(e.get("EventTime"), "isoformat") else None,
                "eventName": e.get("EventName"),
                "eventSource": e.get("EventSource"),
                "username": e.get("Username"),
                "resources": resources,
                "cloudTrailEvent": e.get("CloudTrailEvent"),
            }
        )
    return timeline

