# Execution Results

Execution results are objects returned from command handlers that control how components respond to user actions. They determine which components need re-rendering, what HTTP headers to set, and how the browser should behave after processing a command.

## Overview

Command handlers can return different types of execution results to control the response behavior:

- **Component rendering control** - Mark components as dirty (needing re-render) or clean
- **Navigation control** - Redirect to different pages or refresh the current page
- **URL management** - Update the browser URL without full page reload

If a command handler returns `None` (or doesn't return anything), the component is automatically marked as dirty and will be re-rendered.

## Available Execution Results

::: livecomponents.manager.execution_results.ComponentClean
    options:
      heading_level: 3
      show_root_heading: true
      members: false



::: livecomponents.manager.execution_results.ComponentDirty
    options:
      heading_level: 3
      show_root_heading: true
      members: false

::: livecomponents.manager.execution_results.ParentDirty
    options:
      heading_level: 3
      show_root_heading: true
      members: false

::: livecomponents.manager.execution_results.RedirectPage
    options:
      heading_level: 3
      show_root_heading: true
      members: false

::: livecomponents.manager.execution_results.RefreshPage
    options:
      heading_level: 3
      show_root_heading: true
      members: false

::: livecomponents.manager.execution_results.ReplaceUrl
    options:
      heading_level: 3
      show_root_heading: true
      members: false

::: livecomponents.manager.execution_results.PushUrl
    options:
      heading_level: 3
      show_root_heading: true
      members: false

## More Usage Examples

### Basic Component Control

When you need explicit control over component rendering:

```python
from livecomponents import LiveComponent, command, CallContext
from livecomponents.manager.execution_results import ComponentDirty, ComponentClean

class DataComponent(LiveComponent):

    @command
    def update_data(self, call_context: CallContext[DataState]):
        """Update component state and trigger re-render"""
        call_context.state.data = "new value"
        # Component will be re-rendered (default behavior)
        return ComponentDirty()

    @command
    def log_action(self, call_context: CallContext[DataState]):
        """Log user action without triggering component re-render"""
        self.analytics.track("button_clicked", call_context.state.user_id)
        return ComponentClean()
```

### Cross-Component Updates

When child components need to update their parents or siblings:

```python
class ProductRowComponent(LiveComponent):

    @command
    def update_sibling(self, call_context: CallContext[ProductRowState]):
        """Update product data and refresh related sidebar component"""
        self.update_product_stats()
        return ComponentDirty("product-sidebar")

    @command
    def delete_product(self, call_context: CallContext[ProductRowState]):
        """Delete product and refresh parent product list"""
        call_context.state.product.delete()
        return ParentDirty()
```

### Multiple Results

Command handlers can return a list of execution results to perform multiple actions:

```python
class OrderComponent(LiveComponent):

    @command
    def complete_order(self, call_context: CallContext[OrderState]):
        """Complete order with multiple UI updates"""
        order = call_context.state.order
        order.status = "completed"
        order.save()

        return [
            ComponentDirty(),
            ComponentDirty("cart-counter"),
            ReplaceUrl(f"/orders/{order.id}/confirmation/")
        ]
```

### URL Management: PushUrl vs ReplaceUrl

Understanding when to use `PushUrl` versus `ReplaceUrl`:

```python
class NavigationComponent(LiveComponent):

    @command
    def navigate_with_history(self, call_context: CallContext[NavState], page: str):
        """Navigate to a new page, adding to browser history.

        Users can use the browser's back button to return to previous pages.
        Use this for navigation between distinct pages or steps.
        """
        call_context.state.current_page = page
        return [ComponentDirty(), PushUrl(f'/app/{page}/')]

    @command
    def update_filters(self, call_context: CallContext[NavState], filter_value: str):
        """Update URL to reflect current filters without adding to history.

        Prevents cluttering browser history with every filter change.
        Use this for transient state like search queries or filters.
        """
        call_context.state.filter = filter_value
        return [ComponentDirty(), ReplaceUrl(f'/app/?filter={filter_value}')]
```

Note that most of the time you need to re-render the component when you are updating the URL, so `ComponentDirty()` is included in the list of execution results.
