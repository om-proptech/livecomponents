from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, CommandError

from livecomponents.management.commands._templates import (
    COMPONENT_HTML_TEMPLATE,
    COMPONENT_PYTHON_TEMPLATE,
    STATELESS_COMPONENT_PYTHON_TEMPLATE,
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
            help=(
                "Component name in snake case. The name can use directory separator "
                "for creating namespaces. Normally, the first namespace is the "
                "app name. E.g., 'counters/click_counter'"
            ),
        )
        parser.add_argument(
            "--class-name",
            type=str,
            help=(
                "Optional class name for the component. "
                "E.g., 'ClickCounter'. If not given, the component name, "
                "converted to PascalCase, is used."
            ),
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Overwrite existing files",
        )
        parser.add_argument(
            "--stateless",
            action="store_true",
            help="Create a stateless component",
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        component_name = options["component_name"]
        stateless = options["stateless"]
        proper_name = component_name.split("/")[-1]

        class_name = options["class_name"]
        if class_name is None:
            class_name = generate_class_name(proper_name)
        module_name = (
            f"{app_name}.components.{component_name.replace('/', '.')}.{proper_name}"
        )

        self.stdout.write(
            f"Creating a new live component {component_name!r} in app {app_name!r}"
        )

        app_path = self.get_app_path(app_name)
        component_path = app_path / "components" / component_name
        component_path.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files for all the parent directories of the component
        # file down to "components" directory.
        parent_path = component_path.parent
        while parent_path != app_path / "components":
            init_py = parent_path / "__init__.py"
            if not init_py.exists():
                init_py.touch()
            parent_path = parent_path.parent

        component_py = component_path / f"{proper_name}.py"
        component_html = component_path / f"{proper_name}.html"

        if component_py.exists() and not options["force"]:
            raise CommandError(f"Component file already exists: {component_py}")
        if component_html.exists() and not options["force"]:
            raise CommandError(f"Component file already exists: {component_html}")

        context = {
            "component_name": component_name,
            "proper_name": proper_name,
            "class_name": class_name,
        }
        component_py.write_text(self.get_python_template(stateless).format(**context))
        component_html.write_text(COMPONENT_HTML_TEMPLATE.format(**context))
        self.stdout.write(
            self.style.SUCCESS(
                f"Created component files: {component_py} and {component_html}"
            )
        )
        self.stdout.write(
            f"- If necessary, add {module_name!r} "
            f"to COMPONENTS['libraries'] of your settings"
        )
        self.stdout.write(
            f'- Use component as {{% livecomponent "{component_name}" %}}'
        )
        self.stdout.write(
            f"- If the component is called from a parent component, use it as "
            f'{{% livecomponent "{component_name}" parent_id=component_id %}}'
        )

    def get_python_template(self, stateless: bool) -> str:
        if stateless:
            return STATELESS_COMPONENT_PYTHON_TEMPLATE
        return COMPONENT_PYTHON_TEMPLATE

    def get_app_path(self, app_name: str) -> Path:
        for app_config in apps.get_app_configs():
            if app_config.name == app_name:
                return Path(app_config.path)
        raise CommandError(f"App not found: {app_name}")


def generate_class_name(proper_name: str) -> str:
    """Generate a class name from the component name."""
    return "".join(word.capitalize() for word in proper_name.split("_"))
