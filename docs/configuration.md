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
    # The django-components dependencies rendering strategy for command
    # re-renders (HTMX fragments). One of "document", "fragment", "simple",
    # "prepend", "append", "ignore".
    # Default: "simple"
    "rerender_deps_strategy": "simple",
}
```

## Dependencies rendering strategy

On command re-renders, the response is an HTMX fragment, and django-components
post-processes it with the strategy set in `rerender_deps_strategy` (see the
[django-components documentation](https://django-components.github.io/django-components/latest/concepts/advanced/rendering_js_css/)
for the full list of strategies).

The default, `"simple"`, strips the internal dependency placeholders and
inlines the JS/CSS of the re-rendered components. Note that with the
recommended htmx setup (out-of-band swaps only), htmx discards content outside
of the swapped elements — so make sure the JS/CSS of components that appear in
fragments is already loaded with the initial page (the
`{% component_js_dependencies %}` / `{% component_css_dependencies %}` tags
take care of this for components rendered on the page).

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
