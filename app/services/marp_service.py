from app.models.render_spec import ResolvedBlock, ResolvedSlide
from app.models.schema import Presentation
from app.services.layout_resolver import LayoutResolver
from app.services.slide_format import MARP_SIZE, STANDARD_WIDESCREEN_NAME


class MarpRenderError(Exception):
    pass


class MarpService:
    def __init__(self, theme: str = "default") -> None:
        self.theme = theme
        self.layout_resolver = LayoutResolver()

    def render_markdown(self, presentation: Presentation) -> str:
        resolved = self.layout_resolver.resolve_presentation(presentation)
        lines = [
            "---",
            "marp: true",
            f"theme: {self.theme}",
            "paginate: true",
            f"size: {MARP_SIZE}",
            "---",
            "",
            "<style>",
            "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800&display=swap');",
            "section {",
            "  font-family: 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;",
            "  background: linear-gradient(180deg, #deebfb 0%, #eef4fb 100%);",
            "  color: #0f172a;",
            "  padding: 44px 58px 38px;",
            "  position: relative;",
            "}",
            "section::before {",
            "  content: '';",
            "  position: absolute;",
            "  inset: 0;",
            "  background:",
            "    radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 28%),",
            "    radial-gradient(circle at bottom left, rgba(147, 197, 253, 0.25), transparent 32%);",
            "  pointer-events: none;",
            "}",
            "section::after {",
            "  content: '';",
            "  position: absolute;",
            "  inset: 34px 36px 34px 36px;",
            "  background: rgba(255, 255, 255, 0.82);",
            "  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.95);",
            "  z-index: 0;",
            "}",
            "h1 {",
            "  margin: 0 0 18px;",
            "  font-size: 32px;",
            "  font-weight: 800;",
            "  line-height: 1.25;",
            "  letter-spacing: -0.02em;",
            "  color: #0f172a;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "h2 {",
            "  margin: 24px 0 10px;",
            "  font-size: 20px;",
            "  color: #2563eb;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "h6 {",
            "  margin: 0 0 12px;",
            "  font-size: 13px;",
            "  font-weight: 700;",
            "  letter-spacing: 0.08em;",
            "  color: #0369a1;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "ul {",
            "  margin: 0;",
            "  padding-left: 1.1em;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "li {",
            "  font-size: 22px;",
            "  line-height: 1.65;",
            "  margin: 0 0 12px;",
            "  color: #334155;",
            "}",
            "blockquote {",
            "  margin: 20px 0 0;",
            "  padding: 20px 24px;",
            "  border-left: 0;",
            "  border-radius: 22px;",
            "  background: rgba(255, 255, 255, 0.94);",
            "  box-shadow: 0 18px 36px rgba(148, 163, 184, 0.14);",
            "  color: #334155;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "table {",
            "  width: 100%;",
            "  border-collapse: separate;",
            "  border-spacing: 14px 0;",
            "  table-layout: fixed;",
            "}",
            "thead, th {",
            "  display: none;",
            "}",
            "td {",
            "  vertical-align: top;",
            "  background: rgba(255, 255, 255, 0.94);",
            "  border: 1px solid rgba(148, 163, 184, 0.26);",
            "  border-radius: 18px;",
            "  padding: 18px 20px;",
            "  color: #334155;",
            "  position: relative;",
            "  z-index: 1;",
            "}",
            "section.standard-slide table,",
            "section.agenda-slide table,",
            "section.summary-slide table {",
            "  margin-top: 22px;",
            "  border-spacing: 24px 0;",
            "}",
            "section.standard-slide td,",
            "section.agenda-slide td,",
            "section.summary-slide td {",
            "  min-height: 220px;",
            "  padding: 24px 24px;",
            "}",
            "section.standard-slide strong,",
            "section.agenda-slide strong,",
            "section.summary-slide strong {",
            "  display: block;",
            "  margin-bottom: 14px;",
            "  font-size: 18px;",
            "  letter-spacing: 0.04em;",
            "  color: #2563eb;",
            "}",
            "section.title-slide {",
            "  justify-content: center;",
            "}",
            "section.title-slide h1 {",
            "  font-size: 42px;",
            "  margin-bottom: 22px;",
            "  text-align: center;",
            "  color: #2563eb;",
            "}",
            "section.title-slide blockquote {",
            "  font-size: 20px;",
            "  line-height: 1.8;",
            "  width: 78%;",
            "  margin-left: auto;",
            "  margin-right: auto;",
            "}",
            "section.title-slide h6 {",
            "  text-align: center;",
            "}",
            "section.summary-slide h2,",
            "section.two-column-slide h2 {",
            "  margin-top: 18px;",
            "}",
            "section.summary-slide h2 {",
            "  display: inline-block;",
            "  padding: 6px 12px;",
            "  background: rgba(191, 219, 254, 0.55);",
            "  border-radius: 999px;",
            "}",
            "</style>",
            "",
        ]
        last_index = len(resolved.slides) - 1
        for index, slide in enumerate(resolved.slides):
            lines.extend(self._render_slide(slide, add_separator=index != last_index))
        return "\n".join(lines).strip() + "\n"

    def _render_slide(self, slide: ResolvedSlide, *, add_separator: bool) -> list[str]:
        if slide.pattern == "title_hero":
            body = self._render_title_slide(slide)
        elif slide.pattern == "agenda_steps":
            body = self._render_agenda_slide(slide)
        elif slide.pattern == "action_summary":
            body = self._render_summary_slide(slide)
        elif slide.pattern == "split_columns":
            body = self._render_two_column_slide(slide)
        elif slide.pattern == "standard_list":
            body = self._render_linear_content_slide(slide)
        else:
            body = self._render_standard_slide(slide)

        if add_separator:
            return body + ["", "---", ""]
        return body + [""]

    def _render_title_slide(self, slide: ResolvedSlide) -> list[str]:
        bullets = [item.text.strip() for item in slide.blocks[0].items if item.text.strip()]
        body = [
            "<!-- _class: title-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            "",
            f"# {slide.title.strip()}",
        ]
        if bullets:
            body.append("")
            body.append(f"> {'  \n> '.join(bullets)}")
        return body

    def _render_agenda_slide(self, slide: ResolvedSlide) -> list[str]:
        body = [
            "<!-- _class: agenda-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            f"# {slide.title.strip()}",
        ]
        if slide.blocks:
            body.extend(["", *self._render_card_table(slide.blocks)])
        return body

    def _render_standard_slide(self, slide: ResolvedSlide) -> list[str]:
        body = [
            "<!-- _class: standard-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            f"# {slide.title.strip()}",
        ]
        if slide.blocks:
            body.extend(["", *self._render_card_table(slide.blocks)])
        return body

    def _render_linear_content_slide(self, slide: ResolvedSlide) -> list[str]:
        body = [
            "<!-- _class: standard-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            f"# {slide.title.strip()}",
            "",
        ]
        for block in slide.blocks:
            for item in block.items:
                body.append(f"- {item.text}")
        return body

    def _render_two_column_slide(self, slide: ResolvedSlide) -> list[str]:
        left_block, right_block = slide.blocks
        body = [
            "<!-- _class: two-column-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            f"# {slide.title.strip()}",
            "",
            "| 左 | 右 |",
            "| :-- | :-- |",
            f"| **{left_block.heading or '左'}**<br>{self._block_body(left_block)} | **{right_block.heading or '右'}**<br>{self._block_body(right_block)} |",
        ]
        return body

    def _render_summary_slide(self, slide: ResolvedSlide) -> list[str]:
        body = [
            "<!-- _class: summary-slide -->",
            f"<!-- format: {STANDARD_WIDESCREEN_NAME} -->",
            f"###### {slide.type_label} | {slide.layout_label}",
            f"# {slide.title.strip()}",
        ]
        if slide.blocks:
            body.extend(["", *self._render_card_table(slide.blocks)])
        return body

    def _render_card_table(self, blocks: tuple[ResolvedBlock, ...]) -> list[str]:
        headers = " | ".join(f"列{index}" for index in range(1, len(blocks) + 1))
        aligns = " | ".join(":--" for _ in blocks)
        cells = " | ".join(self._card_text(block) for block in blocks)
        return [
            f"| {headers} |",
            f"| {aligns} |",
            f"| {cells} |",
        ]

    def _card_text(self, block: ResolvedBlock) -> str:
        heading = f"**{block.heading}**<br>" if block.heading else ""
        return f"{heading}{self._block_body(block)}"

    def _block_body(self, block: ResolvedBlock) -> str:
        return "<br>".join(item.text for item in block.items if item.text.strip())
