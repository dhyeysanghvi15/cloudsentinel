from __future__ import annotations

from collections import defaultdict

from .models import CheckResult


def compute_score(results: list[CheckResult]) -> tuple[int, dict]:
    # Transparent scoring:
    # - Each check has a weight (default 10).
    # - pass = full points, warn = 50%, fail = 0%, skip/error = excluded from denominator.
    total_weight = 0
    earned = 0.0
    by_domain: dict[str, dict[str, float]] = defaultdict(lambda: {"earned": 0.0, "total": 0.0})
    status_counts: dict[str, int] = defaultdict(int)

    for r in results:
        status_counts[r.status] += 1
        if r.status in {"skip", "error"}:
            continue
        total_weight += r.weight
        by_domain[r.domain]["total"] += r.weight
        if r.status == "pass":
            earned += r.weight
            by_domain[r.domain]["earned"] += r.weight
        elif r.status == "warn":
            earned += r.weight * 0.5
            by_domain[r.domain]["earned"] += r.weight * 0.5

    score = int(round((earned / total_weight) * 100)) if total_weight else 0
    domain_scores = {
        d: int(round((v["earned"] / v["total"]) * 100)) if v["total"] else 0 for d, v in by_domain.items()
    }
    breakdown = {
        "total_weight": total_weight,
        "earned": earned,
        "status_counts": dict(status_counts),
        "domain_scores": domain_scores,
        "rules": {
            "pass": 1.0,
            "warn": 0.5,
            "fail": 0.0,
            "skip": None,
            "error": None,
        },
    }
    return score, breakdown
