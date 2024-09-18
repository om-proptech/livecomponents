# Error handling

The response to calling the command can be an HTTP error. If the command handler fails to find a session, it will return
an HTTP 410 Gone error.

You can handle this error on the client side. For example, here a JavaScript code snippet to reload the page on the
error 410.

```javascript
document.addEventListener("htmx:responseError", function (event) {
	const statusCode = event.detail.xhr.status;
	if (statusCode === 410) {
		document.location.reload();
	}
});
```

If you use [hyperscript](https://hyperscript.org/), you can write the same code much shorter as a one-liner, attached
directly to the component, or to the document:

```html
<body ... _="on htmx:responseError[detail.xhr.status == 410] window.location.reload()">
...
</body>
```
