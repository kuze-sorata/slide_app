from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.schema import Presentation


class RenderService:
    def __init__(self, template_dir: str | Path | None = None) -> None:
        resolved_template_dir = (
            Path(template_dir)
            if template_dir is not None
            else Path(__file__).resolve().parents[1] / "templates"
        )
        self.environment = Environment(
            loader=FileSystemLoader(resolved_template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_preview_html(self, presentation: Presentation) -> str:
        template = self.environment.get_template("slides_fragment.html")
        return template.render(presentation=presentation)
