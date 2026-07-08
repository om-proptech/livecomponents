from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied

from livecomponents.decorators import livecomponents_login_required


class SecuredComponent:
    """A minimal stand-in: the decorator only inspects the request user."""

    @livecomponents_login_required
    def init_state(self, context):
        return "initial-state"

    @livecomponents_login_required
    def do_something(self, call_context, value=1):
        return f"done:{value}"


def _context(user):
    request = SimpleNamespace(user=user)
    return SimpleNamespace(request=request)


def test_login_required_rejects_anonymous_init_state():
    with pytest.raises(PermissionDenied):
        SecuredComponent().init_state(_context(AnonymousUser()))


def test_login_required_rejects_anonymous_command():
    with pytest.raises(PermissionDenied):
        SecuredComponent().do_something(_context(AnonymousUser()), value=2)


def test_login_required_allows_authenticated_user():
    # An unsaved User instance is enough: is_authenticated is a property.
    user = User(username="alice")
    component = SecuredComponent()
    assert component.init_state(_context(user)) == "initial-state"
    assert component.do_something(_context(user), value=2) == "done:2"
