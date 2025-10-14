# Home

Django Live Component is a library for creating dynamic web applications that handle user interactions with server side rendering (SSR). It leverages Django, HTMX, and Alpine.js to provide a seamless experience for both developers and users.

To get started, follow the [quickstart guide](quickstart.md).

!!! warning "Leaky Abstractions"

    There is a concept known as [leaky abstractions](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/). This occurs when a software component's abstraction does not fully hide the implementation details of its underlying layers, causing them to "leak through" in non-trivial cases.

    In this sense, livecomponents are quite leaky. Think of it as a "glue" that helps you combine HTMX and Django with django-components without writing too much boilerplate code. However, be prepared to deal with implementation details when they surface in your application.
