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
            user_request="大学生向けにAIとは何かを2枚で説明したい",
            slide_count=2,
        )


def test_slide_generation_request_derives_fields_from_user_request() -> None:
    payload = SlideGenerationRequest(
        user_request=(
            "営業部長向けに営業進捗の振り返りを5枚で共有したい。"
            "進捗、課題、次の打ち手を簡潔に整理したい。数字は仮置きでよい。"
        ),
        slide_count=5,
    )

    assert payload.audience == "営業部長"
    assert payload.theme == "営業進捗の振り返り"
    assert payload.objective == "進捗、課題、次の打ち手を簡潔に整理したい"
    assert payload.required_points == ["進捗", "課題", "次の打ち手"]
    assert payload.extra_notes == "数字は仮置きでよい / 簡潔にまとめる"


def test_slide_generation_request_accepts_manual_override_with_user_request() -> None:
    payload = SlideGenerationRequest(
        user_request="役員会向けに新規商材の方針を4枚で説明したい",
        theme="新規商材の提案方針",
        objective="役員向けに判断ポイントを共有する",
        audience="役員会",
        slide_count=4,
    )

    assert payload.theme == "新規商材の提案方針"
    assert payload.objective == "役員向けに判断ポイントを共有する"
    assert payload.audience == "役員会"


def test_slide_generation_request_falls_back_objective_for_review_style_prompt() -> None:
    payload = SlideGenerationRequest(
        user_request="営業部長向けに営業進捗の振り返りを5枚でまとめる",
        slide_count=5,
    )

    assert payload.audience == "営業部長"
    assert payload.theme == "営業進捗の振り返り"
    assert payload.objective == "現状と課題を振り返り次の打ち手を整理する"


def test_slide_generation_request_uses_generic_objective_fallback() -> None:
    payload = SlideGenerationRequest(
        user_request="開発部向けに新体制のオンボーディング資料を5枚で作る",
        slide_count=5,
    )

    assert payload.audience == "開発部"
    assert payload.objective == "要点を整理して共有する"


def test_slide_generation_request_derives_fields_from_english_user_request() -> None:
    payload = SlideGenerationRequest(
        user_request=(
            "Create a 5-slide update for a sales director covering current progress, "
            "key issues, and next actions. Keep the wording short, clear, and easy "
            "to present in a meeting."
        ),
        slide_count=5,
    )

    assert payload.audience == "sales director"
    assert payload.theme == "update"
    assert payload.objective == "present in a meeting"
    assert payload.required_points == ["current progress", "key issues", "next actions"]
    assert payload.extra_notes == "Keep the wording concise / Make it easy to present in a meeting"
