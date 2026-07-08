# Storing Component Context

During the first render, components use the entire page context to render themselves.

During subsequent renders, components by default use the context populated from their state.

However, it is possible to save some variables from the context of the first render. To do this, pass the `save_context` variable with a comma-separated list of variables that need to be sent to the `livecomponent` templatetag.

This approach is commonly used when working with live component slots.

Let's first look at an example of a "non-prepared" component that will only work on the first render:

```html
{% livecomponent_block "alert" %}
  {% fill "body" %}Sending a message to {{ recipient.email }}!{% endfill %}
{% endlivecomponent_block %}
```

This will not work on partial renders because the component will be rendered without the "recipient" variable.

To address this, add the "save_context" variable:

```diff
-{% livecomponent_block "alert" %}
+{% livecomponent_block "alert" save_context="recipient" %}
   {% fill "body" %}Sending a message to {{ recipient.email }}!{% endfill %}
 {% endlivecomponent_block %}
```

!!! warning "Don't shadow context processor variables in fills"

    Since django-components v0.140, slot fills are rendered lazily, and
    variables provided by context processors take precedence over template
    variables of the same name **inside `{% fill %}` blocks**. If the example
    above used a variable named `user`, then `{{ user.email }}` inside the
    fill would silently render the *logged-in* user (from
    `django.contrib.auth.context_processors.auth`) instead of the saved
    variable — sending the message to the wrong recipient.

    Avoid variable names that collide with your context processors (`user`,
    `perms`, `messages`, `debug`, ...) anywhere near `{% fill %}` blocks —
    whether they come from `save_context`, a `{% for %}` loop, or
    `{% with %}`.

## Alternative: capturing context in `init_state()`

The `save_context` approach works at the template level. You can also capture page variables in Python by reading `context.outer_context` inside `init_state()`:

```python
class SampleState(BaseModel):
    var: str = "unset"

class Sample(LiveComponent):

    def init_state(self, context: InitStateContext) -> SampleState:
        var = context.outer_context.get("var", "unset")
        return SampleState(**context.component_kwargs, var=var)
```

`outer_context` is only available during the first render. Store anything you need in the component's state so it persists across re-renders.
