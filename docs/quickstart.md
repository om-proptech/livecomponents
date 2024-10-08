# Quickstart

Here's how you integrate live components after you've installed the package:

- Modify Django settings.
- Modify base HTML template.
- Modify URLs to include live components.

## Django settings

Add to installed apps following packages:

```python
INSTALLED_APPS = [
    # ...
    "django_components",
    "django_components.safer_staticfiles",
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

Add component dirs for to static files:

```python
# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    # To load django-components specific to myapp
    BASE_DIR / "app_one/components",
    BASE_DIR / "app_two/components",
]
```

You can also configure live components with the `LIVECOMPONENTS` settings dictionary. See the "Configuration" section for more details.

## Base template

There, we need support for HTMX and Live Components:

```html
{% load ... component_tags django_htmx livecomponents %}
<head>
  <!-- Configure HTMX -->
  <meta name="htmx-config" content='{"defaultSwapStyle":"none"}'>

  <!-- JavaScript dependencies -->
  <script src="https://unpkg.com/htmx.org@1.9.6"></script>
  <script src="https://unpkg.com/htmx.org@1.9.6/dist/ext/json-enc.js"></script>

  <!-- Use this for idiomorph -->
  <script src="https://unpkg.com/idiomorph/dist/idiomorph-ext.min.js"></script>
  <!-- Or this for Alpine morph -->
  <script src="https://unpkg.com/htmx.org@1.9.6/dist/ext/alpine-morph.js"></script>
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
<body hx-ext="morph, json-enc" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
<!-- use hx-ext="alpine-morph, json-enc" for Alpine.js morpher -->
...
{% component_js_dependencies %}
</body>
<html>
```

## URLs

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
