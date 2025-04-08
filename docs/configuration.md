# Configuration

The application is configured with the "LIVECOMPONENTS" dictionary in the settings.py file. Here's the default settings:

```python
LIVECOMPONENTS = {
    "state_serializer": {
        "cls": "livecomponents.manager.serializers.PickleStateSerializer",
        "config": {},
    },
    "state_store": {
        # You can also use "MemoryStateStore" for tests.
        "cls": "livecomponents.manager.stores.RedisStateStore",
        # See "RedisStateStore" constructor for config options.
        "config": {},
    },
    "state_manager": {
        "cls": "livecomponents.manager.manager.StateManager",
        "config": {},
    },
    # Allow livecomponents views to be embedded in iframes.
    # Default: False
    "xframe_options_exempt": False,
}
```

## Security Considerations

### X-Frame-Options Exemption

The `xframe_options_exempt` setting allows the livecomponents views to be embedded in iframes. This is safe to enable because:

1. The views only accept POST requests, rejecting all GET requests with a 405 status code
2. Any attempt to embed these views in an iframe will result in a GET request, which is rejected
3. Even if a POST request is somehow made from an iframe, it would still require:
   - A valid CSRF token
   - A valid session ID
   - Proper component registration
   - Valid command parameters

This makes the views inherently resistant to clickjacking attacks, as there's no way to trigger meaningful actions through iframe embedding.
