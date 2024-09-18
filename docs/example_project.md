# Example project

While the fully fledged documentation is not ready and the project is in flux, it's better to use the "example" project as the reference.

Run it locally and play with it to get a better understanding of how the library works.

```bash
poetry install
cd example
cp env.example .env
poetry run python manage.py migrate
poetry run python manage.py runserver
```
