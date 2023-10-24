from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, CommandError

from livecomponents.management.commands._templates import (
    COMPONENT_HTML_TEMPLATE,
    COMPONENT_PYTHON_TEMPLATE,
)


class Command(BaseCommand):
    help = "Create a new live component"

    def add_arguments(self, parser):
        parser.add_argument(
            "app_name", type=str, help="The name of the app. E.g., 'counters'"
        )
        parser.add_argument(
            "component_name",
            type=str,
            help="A camel case name for the component. E.g., 'ClickCounter'",
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        component_name = options["component_name"]

        self.stdout.write(
            f"Creating a new live component {component_name!r} in app {app_name!r}"
        )

        app_path = self.get_app_path(app_name)
        component_path = app_path / "components" / component_name.lower()
        component_path.mkdir(parents=True, exist_ok=True)
        init_py = component_path / "__init__.py"
        component_py = component_path / f"{component_name.lower()}.py"
        component_html = component_path / f"{component_name.lower()}.html"

        if component_py.exists():
            raise CommandError(f"Component file already exists: {component_py}")
        if component_html.exists():
            raise CommandError(f"Component file already exists: {component_html}")

        context = {
            "component_name": component_name,
            "lowercase_component_name": component_name.lower(),
        }
        init_py.touch()
        component_py.write_text(COMPONENT_PYTHON_TEMPLATE.format(**context))
        component_html.write_text(COMPONENT_HTML_TEMPLATE.format(**context))
        self.stdout.write(
            self.style.SUCCESS(
                f"Created component files: {component_py} and {component_html}"
            )
        )

    def get_app_path(self, app_name: str) -> Path:
        for app_config in apps.get_app_configs():
            if app_config.name == app_name:
                return Path(app_config.path)
        raise CommandError(f"App not found: {app_name}")
