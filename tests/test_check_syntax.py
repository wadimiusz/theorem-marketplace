import requests

import app as app_module


def test_verifier_timeout_returns_json_busy_error(client, monkeypatch):
    calls = {}

    def slow_verifier(*args, **kwargs):
        calls["timeout"] = kwargs.get("timeout")
        raise requests.Timeout()

    monkeypatch.setattr(app_module.requests, "post", slow_verifier)
    response = client.post("/api/check_syntax", json={"code": "import Mathlib"})

    # Must stay below nginx proxy_read_timeout, or users get nginx's HTML 504.
    assert calls["timeout"] is not None and calls["timeout"] < 300
    assert response.status_code == 503
    assert response.get_json()["success"] is False
    assert "busy" in response.get_json()["message"]
