from contextlib import contextmanager

try:
    import sentry_sdk

    SENTRY_INTEGRATION_INSTALLED = True
except ImportError:
    SENTRY_INTEGRATION_INSTALLED = False


def set_transaction_name(transaction_name: str) -> None:
    """Set the transaction name for the current Sentry scope."""
    if not SENTRY_INTEGRATION_INSTALLED:
        return
    scope = sentry_sdk.get_current_scope()
    scope.set_transaction_name(transaction_name)


def set_span_data(**kwargs) -> None:
    """Set data for the current Sentry span."""
    if not SENTRY_INTEGRATION_INSTALLED:
        return
    current_span = sentry_sdk.get_current_span()
    if current_span:
        for key, value in kwargs.items():
            current_span.set_data(key, value)


@contextmanager
def start_span(name: str):
    """Start a Sentry span."""
    if not SENTRY_INTEGRATION_INSTALLED:
        yield
        return
    op = f"lc.{name.split('(')[0]}"
    with sentry_sdk.start_span(op=op, name=name):
        yield
