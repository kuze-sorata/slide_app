from app.models.schema import Presentation
from app.services.layout_resolver import LayoutResolver


def test_layout_resolver_creates_parallel_cards_for_layout2_content() -> None:
    presentation = Presentation.model_validate(
        {
            "deck_title": "サービス紹介",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "サービス紹介",
                    "bullets": ["営業部向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "主要サービスを整理する",
                    "bullets": ["既存顧客向け支援", "導入初期の伴走支援", "運用改善の定着支援"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "訴求順を決める",
                    "bullets": ["見せ方を統一する"],
                    "layout": "layout4",
                },
            ],
        }
    )

    resolved = LayoutResolver().resolve_presentation(presentation)
    content_slide = resolved.slides[1]

    assert content_slide.pattern == "parallel_cards"
    assert len(content_slide.blocks) == 3
    assert content_slide.blocks[0].heading == "要点 1"
    assert content_slide.blocks[1].items[0].text == "導入初期の伴走支援"


def test_layout_resolver_keeps_non_parallel_layout2_as_standard_list() -> None:
    presentation = Presentation.model_validate(
        {
            "deck_title": "進捗共有",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "進捗共有",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "全体進捗は計画を下回る",
                    "bullets": ["主要案件の受注時期が遅延", "新規リード獲得が目標未達"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "対応方針を決める",
                    "bullets": ["優先案件を見直す"],
                    "layout": "layout4",
                },
            ],
        }
    )

    resolved = LayoutResolver().resolve_presentation(presentation)
    content_slide = resolved.slides[1]

    assert content_slide.pattern == "standard_list"
    assert len(content_slide.blocks) == 1
    assert content_slide.blocks[0].items[0].text == "主要案件の受注時期が遅延"


def test_layout_resolver_creates_split_columns_for_layout3() -> None:
    presentation = Presentation.model_validate(
        {
            "deck_title": "案件整理",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "案件整理",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "課題と対応を整理する",
                    "bullets": ["優先案件が停滞", "判断基準がばらつく", "担当を再配置する"],
                    "layout": "layout3",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "進め方を固める",
                    "bullets": ["今週中に担当を決める"],
                    "layout": "layout4",
                },
            ],
        }
    )

    resolved = LayoutResolver().resolve_presentation(presentation)
    content_slide = resolved.slides[1]

    assert content_slide.pattern == "split_columns"
    assert content_slide.blocks[0].heading == "現状・課題"
    assert content_slide.blocks[1].heading == "対応・示唆"


def test_layout_resolver_adds_fallback_summary_action_card() -> None:
    presentation = Presentation.model_validate(
        {
            "deck_title": "案件整理",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "案件整理",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "現状を整理する",
                    "bullets": ["重点案件を確認する"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "進め方を固める",
                    "bullets": ["今週中に担当を決める"],
                    "layout": "layout4",
                },
            ],
        }
    )

    resolved = LayoutResolver().resolve_presentation(presentation)
    summary_slide = resolved.slides[-1]

    assert summary_slide.pattern == "action_summary"
    assert len(summary_slide.blocks) == 2
    assert summary_slide.blocks[1].items[0].text == "次回までの確認事項を整理する"
    assert summary_slide.blocks[1].items[0].bullet_index is None


def test_layout_resolver_uses_english_labels_for_english_slides() -> None:
    presentation = Presentation.model_validate(
        {
            "deck_title": "Sales Update Review",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "Sales Update Review",
                    "bullets": ["For sales director"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "Key Deals Face Delays",
                    "bullets": ["Longer sales cycles observed", "Customer decision-making slow", "Resource allocation challenges"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "Focus on Deal Acceleration",
                    "bullets": ["Reallocate effort to top deals"],
                    "layout": "layout4",
                },
            ],
        }
    )

    resolved = LayoutResolver().resolve_presentation(presentation)

    assert resolved.slides[1].blocks[0].heading == "Point 1"
    assert resolved.slides[2].blocks[0].heading == "Action 1"
    assert resolved.slides[2].blocks[1].items[0].text == "Clarify the follow-up items for the next review"
