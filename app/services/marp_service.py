from app.models.schema import Presentation, Slide


class MarpRenderError(Exception):
    pass


class MarpService:
    def __init__(self, theme: str = "default") -> None:
        self.theme = theme

    def render_markdown(self, presentation: Presentation) -> str:
        lines = [
            "---",
            "marp: true",
            f"theme: {self.theme}",
            "---",
            "",
            "<style>",
            "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');",
            "section {",
            "  font-family: 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;",
            "}",
            "h1, h2, h3, h4, h5, h6, p, li {",
            "  font-family: 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;",
            "}",
            "</style>",
            "",
        ]
        last_index = len(presentation.slides) - 1
        for index, slide in enumerate(presentation.slides):
            lines.extend(self._render_slide(slide, add_separator=index != last_index))
        return "\n".join(lines).strip() + "\n"

    def _render_slide(self, slide: Slide, *, add_separator: bool) -> list[str]:
        title = slide.title.strip()
        bullets = [bullet.strip() for bullet in slide.bullets if bullet.strip()]

        body = [f"# {title}"]
        body.extend(f"- {bullet}" for bullet in bullets)

        if add_separator:
            return body + ["", "---", ""]
        return body + [""]
