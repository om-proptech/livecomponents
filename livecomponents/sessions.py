import secrets


def get_session_id():
    """Return the session ID for the livecomponent session."""
    # Generate a random session ID for every page reload.
    return secrets.token_urlsafe(16)
