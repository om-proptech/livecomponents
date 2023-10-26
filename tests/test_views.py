from urllib.parse import urlencode

from django.urls import reverse


def test_missing_session_returns_410_gone(client, state_manager):
    url = reverse("livecomponents:call-command")
    kwargs = {
        "session_id": "nonexistent",
        "component_id": "/sample.0",
        "command_name": "set_body",
    }
    full_url = f"{url}?{urlencode(kwargs)}"
    resp = client.post(full_url, data={}, content_type="application/json")
    assert resp.status_code == 410
