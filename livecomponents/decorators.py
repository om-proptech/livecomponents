from functools import wraps

from django.core.exceptions import PermissionDenied

from livecomponents.manager.manager import CallContext, InitStateContext


def livecomponents_login_required(method):
    """
    A method decorator to ensure the user is authenticated.

    class Something(LiveComponent):

        @classmethod
        @livecomponents_login_required
        def init_state(cls, context: InitStateContext):
            ...

        @classmethod
        @livecomponents_login_required
        def do_something(cls, call_context: CallContext[SomethingState]):
            ...
    """
    if method.__name__ == "init_state":
        return _init_state_login_required(method)
    else:
        return _call_method_login_required(method)


def _init_state_login_required(method):
    @wraps(method)
    def wrapped(cls, context: InitStateContext, **component_kwargs):
        if not context.request.user.is_authenticated:
            raise PermissionDenied()
        return method(cls, context, **component_kwargs)

    return wrapped


def _call_method_login_required(method):
    @wraps(method)
    def wrapped(cls, call_context: CallContext, **kwargs):
        if not call_context.request.user.is_authenticated:
            raise PermissionDenied()
        return method(cls, call_context, **kwargs)

    return wrapped
