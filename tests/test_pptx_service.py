from io import BytesIO

from pptx import Presentation as PptxPresentation

from app.models.schema import Presentation
from app.services.pptx_service import PptxService


def sample_presentation() -> Presentation:
    return Presentation.model_validate(
        {
            "deck_title": "営業進捗の共有",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "営業進捗の共有",
                    "bullets": ["部長向け共有", "現状と課題を提示"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "重点案件の進捗",
                    "bullets": ["A案件: 契約間近", "B案件: 交渉停滞中"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "今後のアクション",
                    "bullets": ["B案件の戦略見直し", "週次レビューの強化"],
                    "layout": "layout4",
                },
            ],
        }
    )


def test_render_pptx_outputs_valid_file() -> None:
    service = PptxService()

    pptx_bytes = service.render_pptx(sample_presentation())

    assert pptx_bytes.startswith(b"PK")
    deck = PptxPresentation(BytesIO(pptx_bytes))
    assert len(deck.slides) == 3
    assert deck.slides[0].shapes.title.text == "営業進捗の共有"
