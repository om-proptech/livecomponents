import json
from urllib.parse import urlencode

from django.urls import reverse

from livecomponents.views import parse_body


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


def test_parse_body_understands_json_encoded_content(rf):
    request = rf.post(
        "/",
        data=json.dumps({"foo": "bar"}),
        content_type="application/json",
    )
    assert parse_body(request) == {"foo": "bar"}


def test_parse_body_understands_multipart_form_data(rf):
    request = rf.post(
        "/",
        data={"foo": "bar"},
        format="multipart",
    )
    assert parse_body(request) == {"foo": "bar"}


def test_parse_body_understands_urlencoded_form_data(rf):
    request = rf.post(
        "/",
        data=urlencode({"foo": "bar"}),
        content_type="application/x-www-form-urlencoded",
    )
    assert parse_body(request) == {"foo": "bar"}
