# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
