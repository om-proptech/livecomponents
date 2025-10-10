# Quickstart

Here's how you integrate live components:

- Install `livecomponents`.
- Modify Django settings.
- Modify base HTML template.
- Modify project `urls.py` to include live components.

## Installation

```bash
pip3 install git+https://github.com/om-proptech/livecomponents@...SHA1.HERE...
```

## Django settings

Add to installed apps following packages:

```python
INSTALLED_APPS = [
    # ...
    "django_components",
    "django_components.safer_staticfiles",  # replaces django.contrib.staticfiles
    "django_htmx",
    "livecomponents",
    # ...
]
```

Add HTMX middleware:

```python
MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
    # ...
]
```

Add template loader `django_components.template_loader.Loader`
so that component templates are found, e.g.:

```python
TEMPLATES = [
    {
        # ...
        "OPTIONS": {
            # ...
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        # ...
                        "django_components.template_loader.Loader",
                    ],
                ),
            ],
        },
    },
]
```

Add component dirs for to static files:

```python
# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    # To load django-components specific to myapp
    BASE_DIR / "app_one" / "components",
    BASE_DIR / "app_two" / "components",
]
```

You can also configure live components with the `LIVECOMPONENTS` settings dictionary. See the "Configuration" section for more details.

## Base template

There, we need support for HTMX and Live Components:

```html
{% load ... component_tags django_htmx livecomponents %}
<head>
  <!-- Configure HTMX. See https://htmx.org/docs/#config -->
  <meta name="htmx-config" content='{"defaultSwapStyle":"none","allowNestedOobSwaps":false}'>

  <!-- HTMX and plugins -->
  <script src="https://unpkg.com/htmx.org@2.x.x"></script>
  <script src="https://unpkg.com/htmx-ext-json-enc@2.x.x/json-enc.js"></script>
  <script src="https://unpkg.com/htmx-ext-alpine-morph@2.x.x/alpine-morph.js"></script>
  <!-- Alpine Plugins -->
  <script defer src="https://unpkg.com/@alpinejs/morph@3.x.x/dist/cdn.min.js"></script>
  <!-- Alpine Core -->
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>

  {% django_htmx_script %}

  {% component_css_dependencies %}
  {% livecomponents_session_id as LIVECOMPONENTS_SESSION_ID %}

  <script>
    // Optionally, clear the session on page unload.
    //
    // Firefox does not support keepalive fetches, so we need to use a workaround.
    // See https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon
    // and https://bugzilla.mozilla.org/show_bug.cgi?id=1342484
    const fetchUrl = "{% url 'livecomponents:clear-session' %}?session_id={{ LIVECOMPONENTS_SESSION_ID }}";
    const csrfmiddlewaretoken = "{{ csrf_token }}";
    window.addEventListener("beforeunload", function () {
        navigator.sendBeacon(fetchUrl, new URLSearchParams({csrfmiddlewaretoken}))
    });

    // Alternatively, use a regular fetch if you don't care about the issue above.
    // window.addEventListener("beforeunload", function () {
    //   fetch(fetchUrl, {
    //     keepalive: true,
    //     method: "POST",
    //     headers: {"X-CSRFToken": csrfmiddlewaretoken}
    //   });
    // });
  </script>
  ...
</head>
<body hx-ext="alpine-morph, json-enc" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
...
{% component_js_dependencies %}
</body>
<html>
```

## Project `urls.py`

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("livecomponents/", include("livecomponents.urls")),
    # ...
]
```

## Create new component

There is a management command to create new component:

```bash
./manage.py createlivecomponent <app_name> <directory/component_name>
```

The command with create a "components" subdirectory in the app directory and create a new component, consisting
of one Python, and one HTML file.

Make sure that your STATICFILES_DIRS setting includes the "components" directory of the app.

Optionally, you can pass a `--stateless` flag to create a stateless component.
