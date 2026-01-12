from app.models import CheckResult
from app.scoring import compute_score


def test_compute_score_excludes_skip_and_error() -> None:
    results = [
        CheckResult(
            id="a",
            title="a",
            severity="low",
            status="pass",
            domain="D1",
            evidence={},
            recommendation="x",
            references=[],
            weight=10,
        ),
        CheckResult(
            id="b",
            title="b",
            severity="low",
            status="warn",
            domain="D1",
            evidence={},
            recommendation="x",
            references=[],
            weight=10,
        ),
        CheckResult(
            id="c",
            title="c",
            severity="low",
            status="skip",
            domain="D2",
            evidence={},
            recommendation="x",
            references=[],
            weight=10,
        ),
    ]
    score, breakdown = compute_score(results)
    assert score == 75
    assert breakdown["total_weight"] == 20
