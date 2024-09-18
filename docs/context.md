# Storing Component Context

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
