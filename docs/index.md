# Home

Django Live Components adds interactive, stateful UI to Django without a JavaScript frontend. Each component keeps its state on the server (in Redis), renders with standard Django templates, and updates the page through HTMX partial re-renders.

## Why use it?

Plain HTMX requires you to wire up each endpoint, manage state in the session or database, and write the swap logic yourself. Live components handle that plumbing: you define a state class, write command methods that modify it, and the library takes care of serialization, storage, re-rendering, and DOM patching.

If your project already uses Django and you want interactive widgets, like counters, inline editors, live search, or modals, without building a React/Vue frontend or managing HTMX boilerplate by hand, this library is a good fit. For apps that need a full client-side SPA with offline support or complex client-side state, a JS framework is a better choice.

To get started, follow the [quickstart guide](quickstart.md).

!!! warning "Leaky Abstractions"

    There is a concept known as [leaky abstractions](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/). This occurs when a software component's abstraction does not fully hide the implementation details of its underlying layers, causing them to "leak through" in non-trivial cases.

    In this sense, livecomponents are quite leaky. Think of it as a "glue" that helps you combine HTMX and Django with django-components without writing too much boilerplate code. However, be prepared to deal with implementation details when they surface in your application.
