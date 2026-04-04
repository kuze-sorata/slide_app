from io import BytesIO

from pptx import Presentation as PptxPresentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.models.schema import Presentation, Slide


class PptxRenderError(Exception):
    pass


class PptxService:
    def render_pptx(self, presentation: Presentation) -> bytes:
        deck = PptxPresentation()
        deck.slide_width = Inches(13.333)
        deck.slide_height = Inches(7.5)

        for slide in presentation.slides:
            self._add_slide(deck, slide)

        output = BytesIO()
        deck.save(output)
        return output.getvalue()

    def _add_slide(self, deck: PptxPresentation, slide: Slide) -> None:
        layout_index = 0 if slide.type == "title" else 1
        pptx_slide = deck.slides.add_slide(deck.slide_layouts[layout_index])

        title_shape = pptx_slide.shapes.title
        if title_shape is not None:
            title_shape.text = slide.title
            self._style_title(title_shape.text_frame)

        body_shape = self._resolve_body_shape(pptx_slide, layout_index)
        if body_shape is None:
            return

        text_frame = body_shape.text_frame
        text_frame.clear()
        for index, bullet in enumerate(slide.bullets):
            paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0
            paragraph.alignment = PP_ALIGN.LEFT
            font = paragraph.font
            font.size = Pt(20)
            font.name = "Meiryo"

    def _resolve_body_shape(self, pptx_slide, layout_index: int):
        if layout_index == 0:
            if len(pptx_slide.placeholders) > 1:
                return pptx_slide.placeholders[1]
            textbox = pptx_slide.shapes.add_textbox(Inches(1.0), Inches(3.2), Inches(11.3), Inches(2.6))
            return textbox
        if len(pptx_slide.placeholders) > 1:
            return pptx_slide.placeholders[1]
        textbox = pptx_slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.6))
        return textbox

    def _style_title(self, text_frame) -> None:
        if not text_frame.paragraphs:
            return
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.LEFT
        font = paragraph.font
        font.size = Pt(28)
        font.bold = True
        font.name = "Meiryo"
