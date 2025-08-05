# Working with JavaScript in Livecomponents

When building livecomponents, you often need client-side JavaScript to work with libraries like Chart.js, Google Maps, Monaco editor, or other interactive components. This is challenging because livecomponents use HTMX for updates, which changes how and when JavaScript runs.

This guide explains the common problems and how to fix them.

## Scripts Don't Re-Execute on Updates

**What happens**: When you include JavaScript directly in your component template, it only runs once on the initial page load. When the component updates via HTMX, the script doesn't run again.

```html
<div {% component_attrs component_id %}>
  <div id="my-chart"></div>
  <script>
    // This only runs ONCE on initial page load
    console.log("Initializing chart");
    new Chart(document.getElementById("my-chart"), config);
  </script>
</div>
```

**Why this happens**: Livecomponents use Alpine.js morphing to update the page efficiently. Alpine morph doesn't run `<script>` tags again when updating them ([Alpine morph docs](https://alpinejs.dev/plugins/morph)).

**Solutions**:

As a solution, switch to the regular HTMX update mechanism (without morphing). By default, HTMX will execute scripts on the updated element. You can do this in two ways:

- **Use `swap_style="outerHTML"`**: Forces HTMX to replace the entire element:

  ```html
  <div {% component_attrs component_id swap_style="outerHTML" %}>
    <script>
      // This will run on every update
    </script>
  </div>
  ```

- **Use `{% no_morph %}` template tag**: Prevents morphing of the script element:

  ```html
  <div {% component_attrs component_id %}>
    <script {% no_morph %}>
      // This will run on every update
    </script>
  </div>
  ```

## Multiple Script Execution with Nested Components

**What happens**: When you have nested livecomponents, scripts can execute multiple times unexpectedly.

**Why this happens**: Livecomponents use [`hx-swap-oob`](https://htmx.org/attributes/hx-swap-oob/) to update components in place. With nested components, HTMX processes multiple `hx-swap-oob` directives:

1. Parent component gets swapped
2. Child components also get swapped
3. Scripts in both parent and child run multiple times

**Solution**: Disable nested out-of-band swaps by adding this to your HTML `<head>`:

```html
<meta name="htmx-config" content='{"allowNestedOobSwaps":false}' />
```

This tells HTMX to only process the outermost swap and ignore nested ones. This configuration is recommended in the [quickstart guide](quickstart.md).

## Managing JavaScript Object References

**What happens**: JavaScript libraries create objects (like Chart instances) that you need to reuse when your component updates. You need somewhere to store these objects.

**Recommended approach**: Store objects as custom properties on DOM elements:

```javascript
const canvas = document.getElementById("my-canvas");
if (canvas.chart) {
  // Update existing chart
  canvas.chart.update();
} else {
  // Create new chart and store reference
  canvas.chart = new Chart(canvas, config);
}
```

**Why this works**:

- Objects are automatically garbage collected when DOM elements are removed
- No global namespace pollution
- Clear association between DOM elements and their JavaScript objects

## Preserving Stateful Components

For components that take time to set up (charts, maps, editors), use [`hx-preserve`](https://htmx.org/attributes/hx-preserve/) to keep DOM elements unchanged during updates:

```html
<div {% component_attrs component_id %}>
  <!-- This content can be updated -->
  <h3>{{ chart_title }}</h3>

  <!-- This element stays unchanged -->
  <canvas id="chart-{{ component_id }}" hx-preserve></canvas>

  <script {% no_morph %}>
    function updateChart() {
      const canvas = document.getElementById("chart-{{ component_id }}");
      if (canvas.chart) {
        // Update existing chart with new data
        canvas.chart.data = getNewData();
        canvas.chart.update();
      } else {
        // Initialize chart first time
        canvas.chart = new Chart(canvas, getConfig());
      }
    }
    document.addEventListener("htmx:load", updateChart);
  </script>
</div>
```

## Choosing the Right JavaScript Event

Different events work for different needs:

- **`DOMContentLoaded`** - Only runs on initial page load
- **`htmx:afterSettle`** - Runs after HTMX finishes updating content
- **`htmx:load`** - Runs when HTMX loads new content (recommended)

```javascript
// Best for component initialization
document.addEventListener("htmx:load", initializeComponent, { once: true });
```

If your component initializes itself on each re-render, consider using `{once: true}` to ensure your handler executes at most once per element.

## Important Configuration

Make sure HTMX allows script execution (this is the default):

```html
<meta name="htmx-config" content='{"allowScriptTags": true}' />
```

Stop scripts from running multiple times with nested components (not default, but recommended):

```html
<meta name="htmx-config" content='{"allowNestedOobSwaps": false}' />
```

## Working Example

See the Chart.js component in the [example project](https://github.com/om-proptech/livecomponents/tree/main/example) at `myapp/components/chart/chart.html`. This demonstrates:

- Using `hx-preserve` for the canvas element
- Storing the Chart.js instance on the DOM element
- Handling both initialization and updates
- Using `{% no_morph %}` for reliable script execution

## Summary

**Key Points**:

• **Scripts may not re-run automatically**. Use `swap_style="outerHTML"` or `{% no_morph %}` to ensure execution
• **Disable nested OOB swaps**. Add `{"allowNestedOobSwaps":false}` to prevent multiple executions
• **Store objects on DOM elements**. Avoid global variables, use element properties instead
• **Use `hx-preserve` for stateful components**. Keep expensive initializations unchanged
• **Listen to `htmx:load` events**. Best for component initialization

**Essential Links**:

- [HTMX Scripting Documentation](https://htmx.org/docs/#scripting) - Official guide to JavaScript integration
- [hx-preserve Attribute](https://htmx.org/attributes/hx-preserve/) - Keep elements unchanged during updates
- [hx-swap-oob Attribute](https://htmx.org/attributes/hx-swap-oob/) - Out-of-band swapping behavior
- [Alpine Morph Plugin](https://alpinejs.dev/plugins/morph) - How morphing affects script execution
- [HTMX Configuration](https://htmx.org/docs/#config) - Important configuration options
- [Example Project](https://github.com/om-proptech/livecomponents/tree/main/example) - Working Chart.js implementation
