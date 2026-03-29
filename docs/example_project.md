# Example project

The "example" project demonstrates most library features. Run it locally to see how components work in practice.

```bash
poetry install
cd example
poetry run python manage.py migrate
poetry run python manage.py load_coffee_beans
docker run --rm -d -p 127.0.0.1:6379:6379 redis:latest
poetry run python manage.py runserver
```

See [example](https://github.com/om-proptech/livecomponents/tree/main/example).
