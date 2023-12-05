# Django Live Components


## How to run the example project

While the fully fledged documentation is not ready and the project is in flux, it's better to use the "example" project as the reference.

Run it locally and play with it to get a better understanding of how the library works.

```bash
poetry install
cd example
cp env.example .env
poetry run python manage.py migrate
poetry run python manage.py runserver
```

## Quickstart

Here's how you integrate live components after you've installed the package:

- Modify Django settings.
- Modify base HTML template.
- Modify URLs to include live components.

### Django settings

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

### Base template

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

### URLs

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("livecomponents/", include("livecomponents.urls")),
    # ...
]
```

### Create new component

There is a management command to create new component:

```bash
./manage.py createlivecomponent <app_name> <directory/component_name>
```

The command with create a "components" subdirectory in the app directory and create a new component, consisting
of one Python, and one HTML file.

Make sure that your STATICFILES_DIRS setting includes the "components" directory of the app.


## On component IDs.

- Every component must have a root element that includes its ID. The id is "id={{ component_id }}".
- Component IDs represent the component hierarchy and formatted as "|parent:id|child:id". For example, we can have a component |form:0|button:submit where "button" is the component type, "submit" is its name, and "form:0" is its parent.


## On component states


The state is defined in a separate class. The state must include parameters, passed to the component as keyword arguments, so that the component gets all necessary information to re-render itself on partial render.

For example, given the template the alert component:

```html
<alert>{{ message }}</alert>
```

that you want to use as

```html
{% component "alert" message="Hello, world!" %}
```

Assuming that the component will be re-rendered on partial render, the state must include the "message" parameter:

```python
from pydantic import BaseModel
from livecomponents.component import LiveComponent

class AlertState(BaseModel):
    message: str = ""


class Alert(LiveComponent):

    template_name = "alert.html"


    def init_state(self, **component_kwargs) -> AlertState:
        return AlertState(**component_kwargs)
```

Component states don't need to be stored if components are not expected to be re-rendered independently, and only
as part of the parent component. For example, components for buttons are rarely re-rendered independently, so
you get away without the state model.

## On calling component methods from others

There are two ways to call component methods from other components:

Using the component ID. For example, if you have a component with ID "|message.0" and a method "set_message", you can call it like this:

```python
from livecomponents import LiveComponent, command, CallContext

class MyComponent(LiveComponent):

    @command
    def do_something(self, call_context: CallContext):
        call_context.find_one("|message:0").set_message("Hello, world!")
```

Using the "parent" reference.

```python
from livecomponents import LiveComponent, command, CallContext

class MyComponent(LiveComponent):

    @command
    def do_something(self, call_context: CallContext):
        call_context.parent.set_message("Hello, world!")
```


## Returning results from command handlers

Here's the signature of the Livecomponent function:

```python
from livecomponents import LiveComponent, CallContext, command
from livecomponents.manager.execution_results import IExecutionResult

class MyComponent(LiveComponent):

    @command
    def my_command_handler(self , call_context: CallContext, **kwargs) -> list[IExecutionResult] | IExecutionResult | None :
        ...
```

Notice the type of the returned value for the handler. If set to something other than None, it can shape the
partial HTTP response.

More specifically here's what you can do:

- Return ComponentDirty() to mark the component as dirty. This will result in the component being re-rendered and sent to the client. This is the default behavior. If you don't return anything, the component will be marked as dirty.
- Return ComponentClean() to mark the component as clean (not needing re-rendering).
- Return ParentDirty() to mark the parent component as dirty.
- Return RefreshPage(). If at least one component returns RefreshPage(), a "HX-Refresh: true" header will be sent to the client.
- Return Redirect(url). If at least one component returns Redirect(), a "HX-Redirect: url" header will be sent to the client.


## Configuration

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
}
```

## Storing Component Context

During the first render, components use the entire page context to render themselves.

During subsequent renders, components by default use the context populated from their state.

However, it is possible to save some variables from the context of the first render. To do this, pass the `save_context` variable with a comma-separated list of variables that need to be sent to the `livecomponent` templatetag.

This approach is commonly used when working with live component slots.

Let's first look at an example of a "non-prepared" component that will only work on the first render:

```html
{% livecomponent_block "alert" %}
  {% fill "body" %}Sending a message to {{ user.email }}!{% endfill %}
{% endlivecomponent_block %}
```

This will not work on partial renders because the component will be rendered without the "user" variable.

To address this, add the "save_context" variable:

```diff
-{% livecomponent_block "alert" %}
+{% livecomponent_block "alert" save_context="user" %}
   {% fill "body" %}Sending a message to {{ user.email }}!{% endfill %}
 {% endlivecomponent_block %}
```

## Handling Uploads

By default, the command handler accepts JSON-encoded data passed in the POST request. The HTMX extension `json-ext`, which we include in the base template, is responsible for this behavior. However, JSON-encoded data cannot include files, so we need to use the `multipart/form-data` encoding for this purpose.

To process the files, create a file upload form in the HTML template of the component. Disable `json-ext` and explicitly set up the `multipart/form-data` encoding for the uploaded data. Then, include one or more file upload elements in the form.

In the Python handler, uploaded files are available in the `call_context.request.FILES` variable. The rest of the form goes to the command kwargs, as usual.

Here's an example of how the sample file upload form can look. Notice the ``hx-ext="ignore:json-enc"`` attribute that disables the `json-ext` extension for this form.

```html
  <form hx-ext="ignore:json-enc" hx-encoding='multipart/form-data' hx-post="{% call_command component_id "upload_file" %}">
      <input type="file" name="csv_file" placeholder="CSV file" required>
      <button type="submit">Upload CSV file</button>
  </form>
```

Here's an example of how the handler can look:

```python
    ...

    @command
    def upload_file(self, call_context: CallContext):
        csv_file = call_context.request.FILES["csv_file"]
        ...
```

You can see a full example in the [uploads](./example/project/uploads) app of the sample project.

## On Storing Raw HTML Templates

In Django-components, the same component can be represented as a flat node `{% component "name" key=value %}` or as a block node to populate slots:

```html
{% component_block "name" key=value %}
  {% fill "slot_name" %}
    {{ variable_from_outer_context }}
  {% endfill %}
{% endcomponent_block %}
```

Rendering components with slots is non-trivial for two reasons:

- We need to store the Django HTML content of the slot.
- It should be possible to re-render the component in isolation without accessing the outer context.

By the time the component is rendered with the `@register.tag()` function, we don't have access to the raw template content, only to tokens (generated from the raw template by Lexer) and to nodes (generated from the tokens by Parser).

### How Do We Store Templates

We introduce new flat tags "livecomponent" and block tags "livecomponent_block". While building the node (LiveComponentNode instead of ComponentNode of django-components), store the raw template content in the node. When the node is rendered, we associate the raw template content with the component ID to reuse it on re-render.

### More on Storing Templates

It would be wasteful to store the entire HTML template for every component, considering that most components are rendered by the same template. To optimize space, we hash the template content and use it as the cache key:

```redis
127.0.0.1:6379> get template_cache:LkAl5ah3
"{% livecomponent \"search\" parent_id=component_id search=search %}"
```

Then, we have a separate Redis HASH "templates:<session_id>" to map from component IDs to template hashes:

```redis
127.0.0.1:6379> hgetall templates:a99377ffe6a946e496542ac2c8a8cb96
 1) "/table.0"
 2) "rPOwF_re"
 3) "/table.0/search.0"
 4) "LkAl5ah3"
 ...
```

### How Do We Store the Outer Context

However, we need to store the outer context, or rather, the variables from the outer context that are necessary to re-render the template.

Here, there's not much we can do: we don't want to store the entire context in Redis because it's wasteful, hard to implement (not everything can be pickled), and can easily go out of sync.

Instead, we offload this work to the component developer. The `init_state()` method for constructing the component state is called on the first render. There, a context variable has an "outer_context" attribute. The component developer can store any variables from the outer context in the state and then use them to re-render the component. As long as the developer uses the same name for the variable, the component will be re-rendered correctly.Here's an example:

```python
class SampleState(BaseModel):
    var: str = "unset"
    ...

class Sample(LiveComponent):
    ...

    def init_state(self, context: InitStateContext, **component_kwargs) -> SampleState:
        var = context.outer_context.get("var", "unset")
        effective_kwargs = {**component_kwargs, "var": var}
        return SampleState(**effective_kwargs)
```

## Error handling

The response to calling the command can be an HTTP error. If the command handler fails to find a session, it will return
an HTTP 410 Gone error.

You can handle this error on the client side. For example, here a JavaScript code snippet to reload the page on the
error 410.

```javascript
document.addEventListener("htmx:responseError", function (event) {
	const statusCode = event.detail.xhr.status;
	if (statusCode === 410) {
		document.location.reload();
	}
});
```

If you use [hyperscript](https://hyperscript.org/), you can write the same code much shorter as a one-liner, attached
directly to the component, or to the document:

```html
<body ... _="on htmx:responseError[detail.xhr.status == 410] window.location.reload()">
...
</body>
```
