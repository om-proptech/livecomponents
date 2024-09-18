# Handling Uploads

By default, the command handler accepts JSON-encoded data passed in the POST request. The HTMX extension `json-ext`, which we include in the base template, is responsible for this behavior. However, JSON-encoded data cannot include files, so we need to use the `multipart/form-data` encoding for this purpose.

To process the files, create a file upload form in the HTML template of the component. Disable `json-ext` and explicitly set up the `multipart/form-data` encoding for the uploaded data. Then, include one or more file upload elements in the form.

In the Python handler, uploaded files are available in the `call_context.request.FILES` variable. The rest of the form goes to the command kwargs, as usual.

Here's an example of how the sample file upload form can look. Notice the ``hx-ext="ignore:json-enc"`` attribute that disables the `json-ext` extension for this form.

```html
  <form hx-ext="ignore:json-enc" hx-encoding='multipart/form-data' hx-post="{% call_command component_id "upload_file" %}">
      <input type="file" name="csv_file" placeholder="CSV file" required>
      <button type="submit">Upload CSV file</button>
  </form>
```

Here's an example of how the handler can look:

```python
    ...

    @command
    def upload_file(self, call_context: CallContext):
        csv_file = call_context.request.FILES["csv_file"]
        ...
```

You can see a full example in the [uploads](https://github.com/om-proptech/livecomponents/tree/main/example/uploads) app of the sample project.
