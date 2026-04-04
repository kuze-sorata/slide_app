import pytest
from pydantic import ValidationError

from app.models.schema import Presentation, SlideGenerationRequest


def test_presentation_validates_sequence() -> None:
    presentation = Presentation.model_validate(
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
    assert presentation.slides[0].type == "title"


def test_presentation_rejects_missing_content_slide() -> None:
    with pytest.raises(ValidationError):
        Presentation.model_validate(
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
                        "type": "agenda",
                        "title": "共有項目",
                        "bullets": ["背景", "課題"],
                        "layout": "layout2",
                    },
                    {
                        "id": "slide-3",
                        "type": "summary",
                        "title": "今週の要点",
                        "bullets": ["重点案件を確認する"],
                        "layout": "layout4",
                    },
                ],
            }
        )


def test_slide_generation_request_requires_at_least_three_slides() -> None:
    with pytest.raises(ValidationError):
        SlideGenerationRequest(
            theme="AIとは何か",
            objective="初心者に説明する",
            audience="大学生",
            slide_count=2,
        )
