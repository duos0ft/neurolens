from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)
from mjml import mjml2html

TEMPLATE_DIRECTORY = Path(__file__).resolve().parents[2] / "templates" / "email"

environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIRECTORY),
    autoescape=select_autoescape(
        enabled_extensions=("mjml", "html", "xml"),
        default_for_string=True,
    ),
    undefined=StrictUndefined,
)


class EmailTemplateRenderer:
    @staticmethod
    def render(template_name: str, **context: Any) -> str:
        template = environment.get_template(template_name)
        rendered = template.render(**context)

        if template_name.endswith(".mjml"):
            return mjml2html(rendered)

        return rendered
