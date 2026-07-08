# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### ⚠️ Behavior change: `{% fill %}` blocks and context processor variables

Since django-components v0.140, slot fills are rendered **lazily**. As a result, a
for-loop variable that shadows a context processor variable — such as `user` from
`django.contrib.auth`, `perms`, or `messages` — is **overshadowed by the context
processor** inside `{% fill %}` blocks:

```django
{% for user in users %}
  {% livecomponent_block "modal" own_id=user.username %}
    {% fill "modal_title" %}
      {{ user.username }}  {# ⚠️ renders request.user (e.g. AnonymousUser), NOT the loop variable! #}
    {% endfill %}
  {% endlivecomponent_block %}
{% endfor %}
```

**Audit your templates for `{% fill %}` blocks inside loops (or `{% with %}` blocks)
whose variable names collide with context processor variables, and rename the
variables.** This affects `{% component %}` fills the same way — it is upstream
django-components behavior, not specific to livecomponents. The modals demo was
updated accordingly (loop variable renamed from `user` to `account`).

### Other breaking changes

- Upgraded `django-components` from `^0.28.3` to `^0.151.1`. The `{% livecomponent %}` / `{% livecomponent_block %}` tag syntax and the `LiveComponent` class API are largely unchanged, with the exceptions listed below.
- **Django 5.2 is now the minimum supported version** (required by django-components 0.151).
- **The component name must be a quoted string literal**: `{% livecomponent comp_name_var %}` (name passed as a template variable) is no longer supported and raises `TemplateSyntaxError` at template compile time. This matches the upstream `{% component %}` tag behavior.
- Components must now be registered with `from django_components import register` and `@register("name")` (the old `from django_components import component` / `@component.register("name")` module was removed upstream).
- **Component template variables that collide with context processor variables now raise `ValueError`** (upstream behavior since django-components 0.140). A `LiveComponent` whose state fields, tag kwargs, or `get_extra_context_data()` keys include names like `user`, `perms`, or `messages` crashes when rendered on a page with the corresponding context processors. Rename such fields.
- Removed `django_components.safer_staticfiles` from the example project and docs (the app was removed upstream). Use `django.contrib.staticfiles` **plus** the `django_components.finders.ComponentsFileSystemFinder` static files finder. Do NOT list component directories in `STATICFILES_DIRS` — plain staticfiles would expose the components' Python source files.

### Changed

- Command re-renders (HTMX fragments) are post-processed with django-components' dependencies machinery. The strategy is configurable via the new `LIVECOMPONENTS["rerender_deps_strategy"]` setting (default: `"simple"`). Note that with the recommended htmx setup (out-of-band swaps only), htmx discards scripts outside the swapped elements, so JS/CSS of components used in fragments should already be present on the initial page.
- The `only` isolation flag (and `context_behavior: "isolated"`) is now supported by the livecomponent tags: session lookups inside isolated component templates fall back to the component's own template context.
- Rendering a `LiveComponent` directly with `Component.render()` (without the livecomponent tags) now raises a descriptive `RuntimeError` instead of a `KeyError`.

## 1.20.0 (2026-04-30)

- Fixed `StatelessLiveComponent` commands returning 410 on pages that only contain stateless components (#33).
- Fixed incorrect `@classmethod` decorator on the `login_required` helper.
- Use Django's `require_POST` decorator for the `call_command` view (#21).
- Started checking Subresource Integrity (SRI) for vendored frontend assets (#29).
- `createlivecomponent` management command now also creates missing leaf `__init__.py` files (#28).
- Documentation: added component lifecycle and API reference, fixed several errors, and improved the quickstart guide (#18, #25).
- Documentation: noted `manage.py load_coffee_beans` and the local Redis server requirement in the example project guide (#17).
- Examples: use `django.urls.reverse` in `UrlnavigationComponent` (#19); dropped out-of-sync comment in `RegistrationFormState` (#24).
- CI: enforce pre-commit-clean code (#16), report test coverage (#20), and cover oldest and most recent supported Python versions (#26).

## 1.19.0 (2025-10-27)

- Added TriggerEvents execution result to trigger custom browser events.

## 1.18.0 (2025-10-09)

- Added PushUrl execution result and URL navigation demo

## 1.17.1 (2025-10-01)

- Improved performance by delegating state saving to component instances

## 1.17.0 (2025-09-30)

- Added documentation for execution results.
- Added optional Sentry integration.

## 1.16.0 (2025-08-05)

- Updated livecomponent documentation.
- Added simple counter example.
- Fixed no_morph templatetag to return mark_safe output
- Simplified example project (replaced multiple apps with a single "myapp" app)
- Updated HTMX and Alpine.js configurations in quickstart and example templates

## 1.15.0 (2025-04-08)

- Added `xframe_options_exempt` setting to allow embedding livecomponents views in iframes.

## 1.14.0 (2024-12-26)

- Relaxed Python and Django dependencies: Python: 3.11 and newer (3.12, etc.), Django: 4.x and 5.x.

## 1.13.3 (2024-10-09)

- Addressed more client input validation issues.

## 1.13.1 (2024-10-09)

- Fixed createlivecomponent management command
- Raised BadRequest on invalid client input

## 1.13.0 (2024-09-24)

- Created documentation for the project. The documentation is available in the "docs" directory and on the https://om-proptech.github.io/livecomponents/ website.
- Improved the createlivecomponent management command: fixed the Python template and added --stateless and --minimal options to create stateless components or minimal components (without sample methods).
- Add --base-class option to the createlivecomponent management command to specify the base class for the component. Make it possible to define the base classes for stateful and stateless components in the settings.
- Added "no_morph" and "component_selector" templatetags.

## 1.12.4 (2024-08-15)

- Improved serialization for Django forms and models: pickle now correctly handles unsaved Django model instances and validates bound forms during unpickling.

## 1.12.3 (2024-08-14)

- Created populate_form_with_data() utility function to populate a form with data from the user input.

## 1.12.2 (2024-08-14)

- Improved support for ModelForm with instances.

## 1.12.1 (2024-08-13)

- Added support for ModelForm in livecomponents (fixed pickling error).

## 1.12.0 (2024-07-29)

- Added a "registration" app to show how to use livecomponents with Django forms.

## 1.11.1 (2024-02-26)

- Added `livecomponents_login_required` decorator to require a user to be logged in to call a component method.

## 1.11.0 (2024-02-08)

- Kept sessions marked as deleted for an hour before purging them from the Redis store. This change is to allow the client to recover from a session deletion when the user navigates back to the page.

## 1.10.0 (2024-01-25)

- Added CancelRendering() exception. The exception makes it possible to cancel the command execution and return an empty string instead of a half-rendered component or an exception.

## 1.9.0 (2023-12-22)

- Added ComponentId, which is a str subclass that can be used to create child component IDs from a parent component ID using the "|" separator.
- Added ReplaceUrl execution result. This result is used to replace the current URL in the browser as a result of a command execution.
- Improved support for stateless live components. They don't store mock state objects in Redis anymore.

## 1.8.0 (2023-12-18)

- Added helper method StateAddress.with_component_id() to create a StateAddress with the same session ID, but a different component ID.
- Added reference to the state manager to InitStateContext and UpdateStateContext.
- Added "find_ancestor(ancestor_type)" method to StateAddress and CallContext.
- 🚨 **Breaking Change**. Modified get_extra_context_data() to accept an instance of ExtraContextRequest(). This instance includes the component state, component_kwargs, current request, component state address, and the state manager. By including the state manager and address, it becomes possible to access stores for other components.
- 🚨 **Breaking Change**. Removed the passing of component kwargs to init_state() and update_state(). These kwargs are redundant since both InitStateContext and UpdateStateContext already have them.
- Added StatelessLiveComponent as a base class for components that do not need to store state.

## 1.7.0 (2023-12-13)

- Added `key={component_id}` to the output of the `{% component_attrs %}` templatetag. The "key" attribute is used as a hint for Apline Morph to identify
  elements that need to be updated.
- 🚨 **Breaking Change**. Modified get_extra_context_data() method to accept component_kwargs, allowing extra context population from parent components without storing in Redis. Note: This change is backward incompatible, altering the method signature to include \*\*component_kwargs.

## 1.6.0 (2023-12-05)

- Added {% component_ancestor %} templatetag.
- Documented templatetags. See "Templatetags" in the README.md.

## 1.5.0 (2023-12-05)

- Made it possible to use nested components. The change required updating the hierarchy separator from "/" to "|" and type separator from "." to ":".
- Updated the "createlivecomponent" command. The new command accepts the component path and deduces the component name from it.

## 1.4.2 (2023-11-10)

- Marked LiveComponent as abstract base class.

## 1.4.1 (2023-11-10)

- Made UpdateStateContext importable directly from livecomponents

## 1.4.0 (2023-11-10)

- Made it possible to re-render the component state on re-render.

## 1.3.0 (2023-11-06)

- Added support for handling uploads and provide a sample app to demonstrate the functionality. Refer to "Handling Uploads" in the README.md.

## 1.2.0 (2023-10-26)

- Returned HTTP 410 Gone status code on missing session ID. See "Error handling" in the README.md.

## 1.1.0 (2023-10-25)

- Added support for saving context to a Redis store. See "Storing Component Context" in the README.md.

## 1.0.0 (2023-10-24)

- Implemented the first version of livecomponents.
