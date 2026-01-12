from app.policy_doctor import validate_policy


class DummySession:
    def client(self, *_args, **_kwargs):
        raise RuntimeError("no access analyzer")


def test_policy_doctor_local_detects_wildcards() -> None:
    resp = validate_policy(
        DummySession(),  # type: ignore[arg-type]
        policy_json='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}',
        policy_type="IDENTITY_POLICY",
    )
    assert resp.mode == "local"
    assert any("Action '*'" in f.message for f in resp.findings)

