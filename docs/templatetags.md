# Templatetags

All templatetags are loaded with the "livecomponents" tag library:

```html
{% load livecomponents %}
```

## component_attrs

Set "data-livecomponent-id", "hx-swap-oob", and "key" attributes for the root tag of the component. It is expected to be used in every component template.

The `swap_style` parameter controls how the component updates its state (defaults to "morph"). See [hx-swap-oob](https://htmx.org/attributes/hx-swap-oob/) for more details.

**Usage example:**

```html
<div {% component_attrs component_id %}>
  <!-- The actual component content -->
</div>
```

**Usage with custom swap style:**

```html
<div {% component_attrs component_id swap_style="outerHTML" %}>
  <!-- The actual component content -->
</div>
```

## call_command

Return the URL for calling a command on a component. The `component_id` argument is the component ID that is available in the render context. The `command_name` argument is the name of the command to call.

**Usage example:**

```html
<button hx-post='{% call_command component_id "my_command" %}'>Click me</button>
```

**Another example: passing arguments to the command**

Arguments are passed as JSON-encoded object in the `hx-vals` attribute.

```html
<button hx-post='{% call_command component_id "my_command" %}' hx-vals='{"param":"value"}'>Click me</button>
```

## component_id

Construct the component ID, built from type and ID pairs, following one after another.

For example:

    {% component_id "table" "primary" "row" 1 "cell" "x" as cell_x %}

will return

    |table:primary|row:1|cell:x

## component_ancestor

Return the ID of the closest ancestor component of the given type.

For example, if the current component is `|table:primary|row:1|cell:x`, then

    {% component_ancestor component_id "table" %}

Will return "|table:primary".

**Usage example:**

This is useful if the component state is stored in the root component, and managed by it. Below is a contrived example of how you can delete a specific row from the table, assuming that the table state is stored in the root component, and the current component (a row) keeps its ID in the "row_id" variable.

```html
{% component_ancestor component_id "table" as table_id %}
<button hx-post='{% call_command table_id "delete_row" %}' hx-vals='{"row_id": {{ row_id }}}'>Delete row</button>
```

## component_selector

Return the CSS selector for the component with the given ID.

Can be used to select the component in JavaScript code. For example:

```javascript
const element = document.querySelector({% component_selector component_id %});
```

Note that the returned value is already quoted, so you don't need to add quotes
around it.


## no_morph

Return a key that disables morphing for the component.

Random key is generated to prevent morphing of the component.
See [Apline.js morph keys](https://alpinejs.dev/plugins/morph#keys) for more details.

!!! warning
    `no_morph` should not be used together with `component_attrs` on the root element, as both set the `key` attribute which will cause conflicts. Instead, use `{% component_attrs swap_style="outerHTML" %}` on the root element to achieve similar behavior.

Usage example:

    <textarea {% no_morph %}></textarea>

This way, the textarea DOM element will always be replaced, not morphed, which,
for example, results in updating the component state from the server side.
