# On Storing Raw HTML Templates

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

    def init_state(self, context: InitStateContext) -> SampleState:
        var = context.outer_context.get("var", "unset")
        effective_kwargs = {**context.component_kwargs, "var": var}
        return SampleState(**effective_kwargs)
```
