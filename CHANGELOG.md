# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## UNRELEASED

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
- 🚨 **Breaking Change**. Modified get_extra_context_data() method to accept component_kwargs, allowing extra context population from parent components without storing in Redis. Note: This change is backward incompatible, altering the method signature to include **component_kwargs.

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
