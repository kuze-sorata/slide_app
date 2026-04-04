import pytest

from app.models.schema import Presentation
from app.routes.render import render_html_preview, update_presentation
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


@pytest.mark.asyncio
async def test_render_html_keeps_title_slide_bullets() -> None:
    response = await render_html_preview(sample_presentation(), RenderService())

    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "営業進捗の共有" in body
    assert "部長向け共有" in body


@pytest.mark.asyncio
async def test_update_endpoint_revalidates_presentation() -> None:
    response = await update_presentation(sample_presentation())

    assert response.slides[0].type == "title"
    assert response.slides[-1].type == "summary"
