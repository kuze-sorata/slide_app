from collections.abc import Sequence
from io import BytesIO

from pptx import Presentation as PptxPresentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from app.models.schema import Presentation, Slide


class PptxRenderError(Exception):
    pass


class PptxService:
    SLIDE_WIDTH = Inches(13.333)
    SLIDE_HEIGHT = Inches(7.5)
    FONT_FAMILY = "Meiryo"
    TITLE_COLOR = RGBColor(15, 23, 42)
    BODY_COLOR = RGBColor(51, 65, 85)
    MUTED_COLOR = RGBColor(71, 85, 105)
    ACCENT_COLOR = RGBColor(14, 116, 144)
    BORDER_COLOR = RGBColor(148, 163, 184)
    BACKGROUND_COLOR = RGBColor(248, 250, 252)
    PANEL_COLOR = RGBColor(255, 255, 255)
    SUMMARY_PANEL_COLOR = RGBColor(226, 232, 240)

    def render_pptx(self, presentation: Presentation) -> bytes:
        deck = PptxPresentation()
        deck.slide_width = self.SLIDE_WIDTH
        deck.slide_height = self.SLIDE_HEIGHT
        deck.core_properties.title = presentation.deck_title
        deck.core_properties.subject = "Generated slide deck"
        deck.core_properties.language = "ja-JP"

        for slide_index, slide in enumerate(presentation.slides, start=1):
            pptx_slide = deck.slides.add_slide(deck.slide_layouts[6])
            self._apply_background(pptx_slide)
            self._render_slide(pptx_slide, slide, slide_index=slide_index)

        output = BytesIO()
        deck.save(output)
        return output.getvalue()

    def _render_slide(self, pptx_slide, slide: Slide, *, slide_index: int) -> None:
        if slide.type == "title":
            self._render_title_slide(pptx_slide, slide)
        elif slide.layout == "layout3":
            self._render_two_column_slide(pptx_slide, slide)
        elif slide.type == "summary":
            self._render_summary_slide(pptx_slide, slide)
        else:
            self._render_standard_slide(pptx_slide, slide)
        self._add_footer(pptx_slide, slide_index)

    def _apply_background(self, pptx_slide) -> None:
        fill = pptx_slide.background.fill
        fill.solid()
        fill.fore_color.rgb = self.BACKGROUND_COLOR

    def _render_title_slide(self, pptx_slide, slide: Slide) -> None:
        band = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            Inches(0.0),
            Inches(0.0),
            Inches(13.333),
            Inches(1.0),
        )
        self._set_shape_fill(band, self.ACCENT_COLOR)
        band.line.fill.background()

        title_box = pptx_slide.shapes.add_textbox(
            Inches(0.8),
            Inches(1.45),
            Inches(11.7),
            Inches(1.7),
        )
        self._configure_text_frame(title_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            title_box.text_frame,
            slide.title,
            font_size=Pt(28),
            bold=True,
            color=self.TITLE_COLOR,
        )

        subtitle_box = pptx_slide.shapes.add_textbox(
            Inches(0.85),
            Inches(3.2),
            Inches(8.9),
            Inches(2.3),
        )
        self._configure_text_frame(subtitle_box.text_frame)
        for bullet in slide.bullets:
            self._add_paragraph(
                subtitle_box.text_frame,
                bullet,
                font_size=Pt(20),
                color=self.BODY_COLOR,
                bullet=True,
            )

        badge = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(10.55),
            Inches(3.3),
            Inches(1.95),
            Inches(0.6),
        )
        self._set_shape_fill(badge, RGBColor(224, 242, 254))
        badge.line.color.rgb = self.ACCENT_COLOR
        badge_text = badge.text_frame
        self._configure_text_frame(badge_text, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            badge_text,
            "TITLE",
            font_size=Pt(12),
            bold=True,
            color=self.ACCENT_COLOR,
            alignment=PP_ALIGN.CENTER,
        )

    def _render_standard_slide(self, pptx_slide, slide: Slide) -> None:
        panel = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(0.65),
            Inches(0.65),
            Inches(12.0),
            Inches(5.95),
        )
        self._set_shape_fill(panel, self.PANEL_COLOR)
        panel.line.color.rgb = self.BORDER_COLOR

        title_box = pptx_slide.shapes.add_textbox(
            Inches(1.0),
            Inches(0.95),
            Inches(10.9),
            Inches(0.8),
        )
        self._configure_text_frame(title_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            title_box.text_frame,
            slide.title,
            font_size=Pt(24),
            bold=True,
            color=self.TITLE_COLOR,
        )

        body_box = pptx_slide.shapes.add_textbox(
            Inches(1.05),
            Inches(1.95),
            Inches(10.9),
            Inches(3.9),
        )
        self._configure_text_frame(body_box.text_frame)
        for bullet in slide.bullets:
            self._add_paragraph(
                body_box.text_frame,
                bullet,
                font_size=Pt(20),
                color=self.BODY_COLOR,
                bullet=True,
            )

        chip = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(10.75),
            Inches(0.92),
            Inches(1.25),
            Inches(0.45),
        )
        self._set_shape_fill(chip, RGBColor(241, 245, 249))
        chip.line.color.rgb = self.BORDER_COLOR
        chip_text = chip.text_frame
        self._configure_text_frame(chip_text, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            chip_text,
            slide.type.upper(),
            font_size=Pt(10),
            bold=True,
            color=self.MUTED_COLOR,
            alignment=PP_ALIGN.CENTER,
        )

    def _render_two_column_slide(self, pptx_slide, slide: Slide) -> None:
        title_box = pptx_slide.shapes.add_textbox(
            Inches(0.9),
            Inches(0.8),
            Inches(11.1),
            Inches(0.8),
        )
        self._configure_text_frame(title_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            title_box.text_frame,
            slide.title,
            font_size=Pt(24),
            bold=True,
            color=self.TITLE_COLOR,
        )

        left_panel = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(0.8),
            Inches(1.8),
            Inches(5.75),
            Inches(4.85),
        )
        right_panel = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(6.8),
            Inches(1.8),
            Inches(5.75),
            Inches(4.85),
        )
        for panel in (left_panel, right_panel):
            self._set_shape_fill(panel, self.PANEL_COLOR)
            panel.line.color.rgb = self.BORDER_COLOR

        left_bullets, right_bullets = self._split_bullets(slide.bullets)
        self._render_panel_bullets(pptx_slide, left_bullets, left=Inches(1.1), top=Inches(2.15))
        self._render_panel_bullets(pptx_slide, right_bullets, left=Inches(7.1), top=Inches(2.15))

    def _render_summary_slide(self, pptx_slide, slide: Slide) -> None:
        title_box = pptx_slide.shapes.add_textbox(
            Inches(0.85),
            Inches(0.75),
            Inches(11.4),
            Inches(0.9),
        )
        self._configure_text_frame(title_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            title_box.text_frame,
            slide.title,
            font_size=Pt(24),
            bold=True,
            color=self.TITLE_COLOR,
        )

        summary_panel = pptx_slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(0.85),
            Inches(1.8),
            Inches(11.55),
            Inches(4.9),
        )
        self._set_shape_fill(summary_panel, self.SUMMARY_PANEL_COLOR)
        summary_panel.line.color.rgb = self.BORDER_COLOR

        header_box = pptx_slide.shapes.add_textbox(
            Inches(1.2),
            Inches(2.15),
            Inches(3.0),
            Inches(0.5),
        )
        self._configure_text_frame(header_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            header_box.text_frame,
            "次のアクション",
            font_size=Pt(13),
            bold=True,
            color=self.ACCENT_COLOR,
        )

        body_box = pptx_slide.shapes.add_textbox(
            Inches(1.15),
            Inches(2.75),
            Inches(10.4),
            Inches(3.1),
        )
        self._configure_text_frame(body_box.text_frame)
        for bullet in slide.bullets:
            self._add_paragraph(
                body_box.text_frame,
                bullet,
                font_size=Pt(21),
                color=self.BODY_COLOR,
                bullet=True,
            )

    def _render_panel_bullets(self, pptx_slide, bullets: Sequence[str], *, left, top) -> None:
        body_box = pptx_slide.shapes.add_textbox(left, top, Inches(5.1), Inches(3.9))
        self._configure_text_frame(body_box.text_frame)
        if not bullets:
            self._add_paragraph(
                body_box.text_frame,
                "補足なし",
                font_size=Pt(18),
                color=self.MUTED_COLOR,
            )
            return
        for bullet in bullets:
            self._add_paragraph(
                body_box.text_frame,
                bullet,
                font_size=Pt(18),
                color=self.BODY_COLOR,
                bullet=True,
            )

    def _add_footer(self, pptx_slide, slide_index: int) -> None:
        footer_box = pptx_slide.shapes.add_textbox(
            Inches(11.95),
            Inches(7.0),
            Inches(0.8),
            Inches(0.25),
        )
        self._configure_text_frame(footer_box.text_frame, vertical_anchor=MSO_ANCHOR.MIDDLE)
        self._add_paragraph(
            footer_box.text_frame,
            str(slide_index),
            font_size=Pt(9),
            color=self.MUTED_COLOR,
            alignment=PP_ALIGN.RIGHT,
        )

    def _split_bullets(self, bullets: Sequence[str]) -> tuple[list[str], list[str]]:
        midpoint = (len(bullets) + 1) // 2
        left_bullets = list(bullets[:midpoint])
        right_bullets = list(bullets[midpoint:])
        return left_bullets, right_bullets

    def _configure_text_frame(self, text_frame, *, vertical_anchor=MSO_ANCHOR.TOP) -> None:
        text_frame.clear()
        text_frame.word_wrap = True
        text_frame.margin_left = 0
        text_frame.margin_right = 0
        text_frame.margin_top = 0
        text_frame.margin_bottom = 0
        text_frame.vertical_anchor = vertical_anchor

    def _add_paragraph(
        self,
        text_frame,
        text: str,
        *,
        font_size,
        color: RGBColor,
        bold: bool = False,
        bullet: bool = False,
        alignment: PP_ALIGN = PP_ALIGN.LEFT,
    ) -> None:
        paragraph = text_frame.paragraphs[0] if not text_frame.text else text_frame.add_paragraph()
        paragraph.text = text
        paragraph.alignment = alignment
        paragraph.level = 0
        paragraph.font.size = font_size
        paragraph.font.bold = bold
        paragraph.font.name = self.FONT_FAMILY
        paragraph.font.color.rgb = color
        paragraph.bullet = bullet
        if bullet:
            paragraph.space_after = Pt(8)

    def _set_shape_fill(self, shape, color: RGBColor) -> None:
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = color
