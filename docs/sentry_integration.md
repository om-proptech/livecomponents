# Sentry Integration

Livecomponents include optional support for [Sentry](https://sentry.io/) performance monitoring and error tracking. When Sentry is available in your project, the library automatically instruments component rendering, state management, and command execution.

## Installation

The Sentry integration is completely optional and requires no additional configuration. Simply install Sentry in your Django project:

```bash
pip install sentry-sdk
```

Then configure Sentry in your Django settings as usual:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,  # Adjust for production
    profiles_sample_rate=1.0,  # Adjust for production
)
```

If `sentry-sdk` is not installed, all Sentry-related code is automatically disabled with zero overhead.

## What Gets Tracked

When Sentry is available, Live Components automatically creates performance spans for the component lifecycle and command execution.

## Transaction Names

HTTP requests to Live Components endpoints are automatically tagged with meaningful transaction names:

```
lc.call_command([component_id].command_name)
```

This makes it easy to identify and track specific component interactions in your Sentry dashboard.
