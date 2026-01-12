from fastapi.testclient import TestClient


def test_health_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    from app.main import app

    c = TestClient(app)
    assert c.get("/health").json() == {"ok": True}


def test_scan_timeline_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AWS_SCAN_ENABLED", "0")
    from app.main import app

    c = TestClient(app)
    c.post("/api/simulate/cleanup")
    c.post("/api/simulate/iam-user")

    timeline = c.get("/api/timeline").json()["items"]
    assert any(e.get("eventName") == "CreateUser" for e in timeline)

    snap = c.post("/api/scan").json()
    assert isinstance(snap.get("scan_id"), str)
    assert isinstance(snap.get("score"), int)

    scans = c.get("/api/scans?limit=5").json()
    assert any(s.get("scan_id") == snap["scan_id"] for s in scans)

    detail = c.get(f"/api/scans/{snap['scan_id']}").json()
    assert detail["meta"]["scan_id"] == snap["scan_id"]
    assert detail["snapshot"]["scan_id"] == snap["scan_id"]
