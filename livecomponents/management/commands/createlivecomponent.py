from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, CommandError

from livecomponents.management.commands._templates import (
    COMPONENT_HTML_TEMPLATE,
    COMPONENT_PYTHON_TEMPLATE,
    COMPONENT_PYTHON_TEMPLATE_MINIMAL,
    STATELESS_COMPONENT_PYTHON_TEMPLATE,
    STATELESS_COMPONENT_PYTHON_TEMPLATE_MINIMAL,
)
from livecomponents.settings import get_config


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
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="Create a minimal component without any commands",
        )
        parser.add_argument(
            "--base-class",
            type=str,
            help=(
                "Base class for the component. If not given,"
                "value from settings is used."
            ),
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        component_name = options["component_name"]
        stateless = options["stateless"]
        minimal = options["minimal"]
        base_class = options["base_class"]
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

        # Create __init__.py files for all the directories of the component
        # file down to "components" directory.
        package_path = component_path
        while package_path != app_path / "components":
            init_py = package_path / "__init__.py"
            if not init_py.exists():
                init_py.touch()
            package_path = package_path.parent

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
            "base_class_import": self.get_base_class_import(base_class, stateless),
            "base_class_name": self.get_base_class_name(base_class, stateless),
        }
        component_py.write_text(
            self.get_python_template(stateless, minimal).format(**context)
        )
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

    def get_python_template(self, stateless: bool, minimal: bool) -> str:
        if stateless:
            if minimal:
                return STATELESS_COMPONENT_PYTHON_TEMPLATE_MINIMAL
            return STATELESS_COMPONENT_PYTHON_TEMPLATE
        if minimal:
            return COMPONENT_PYTHON_TEMPLATE_MINIMAL
        return COMPONENT_PYTHON_TEMPLATE

    def get_app_path(self, app_name: str) -> Path:
        for app_config in apps.get_app_configs():
            if app_config.name == app_name:
                return Path(app_config.path)
        raise CommandError(f"App not found: {app_name}")

    def get_base_class(self, base_class: str | None, stateless: bool) -> str:
        if base_class:
            return base_class

        config = get_config().createlivecomponent
        return config.stateless_base_class if stateless else config.base_class

    def get_base_class_import(self, base_class: str | None, stateless: bool) -> str:
        base_class = self.get_base_class(base_class, stateless)
        module, class_name = base_class.rsplit(".", 1)
        return f"from {module} import {class_name}"

    def get_base_class_name(self, base_class: str | None, stateless: bool) -> str:
        base_class = self.get_base_class(base_class, stateless)
        return base_class.rsplit(".", 1)[-1]


def generate_class_name(proper_name: str) -> str:
    """Generate a class name from the component name."""
    return "".join(word.capitalize() for word in proper_name.split("_"))
