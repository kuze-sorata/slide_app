from app.models.schema import Presentation
from app.services.render_service import RenderService


def sample_presentation() -> Presentation:
    return Presentation.model_validate(
        {
            "deck_title": "営業進捗の共有",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "営業進捗の共有",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "重点案件の停滞が課題",
                    "bullets": ["受注見込みが後ろ倒し"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "優先案件の再整理が必要",
                    "bullets": ["案件優先度を見直す"],
                    "layout": "layout4",
                },
            ],
        }
    )


def test_render_preview_html_contains_editable_slide_fields() -> None:
    service = RenderService()

    html = service.render_preview_html(sample_presentation())

    assert 'contenteditable="true"' in html
    assert "営業進捗の共有" in html
    assert 'data-slide-id="slide-2"' in html
    assert "レイアウト2" in html
