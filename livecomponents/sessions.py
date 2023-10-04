import uuid

from django.http import HttpRequest


def get_session_id(request: HttpRequest):
    """Return the session ID for the live components session."""
    # Generate a random session ID for every page reload.
    return uuid.uuid4().hex
