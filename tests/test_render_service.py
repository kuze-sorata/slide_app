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
    assert "レイアウト2" not in html


def test_render_preview_html_adds_type_specific_classes() -> None:
    service = RenderService()

    html = service.render_preview_html(sample_presentation())

    assert "slide-type-title" in html
    assert "slide-type-summary" in html
    assert "次のアクション" not in html
    assert "資料の主題" not in html
    assert "title-hero" in html
    assert "title-summary-panel" in html
    assert "社内向けスライド草案" not in html


def test_render_preview_html_uses_parallel_cards_for_layout2_content() -> None:
    service = RenderService()
    presentation = Presentation.model_validate(
        {
            "deck_title": "サービス紹介",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "サービス紹介",
                    "bullets": ["部長向け共有"],
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
                    "title": "優先紹介順を決める",
                    "bullets": ["3サービスの訴求順を整理する"],
                    "layout": "layout4",
                },
            ],
        }
    )

    html = service.render_preview_html(presentation)

    assert "content-card-grid cards-3" in html
    assert "content-point-card" in html
    assert "要点 1" in html
    assert "導入初期の伴走支援" in html


def test_render_preview_html_uses_split_panels_for_layout3() -> None:
    service = RenderService()
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

    html = service.render_preview_html(presentation)

    assert "split-grid" in html
    assert "現状・課題" in html
    assert "対応・示唆" in html


def test_render_preview_html_keeps_standard_list_for_non_parallel_layout2() -> None:
    service = RenderService()
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

    html = service.render_preview_html(presentation)
    content_index = html.index("全体進捗は計画を下回る")
    content_snippet = html[content_index: content_index + 500]

    assert "standard-bullet-list" in html
    assert "content-card-grid cards-2" not in content_snippet
    assert "主要案件の受注時期が遅延" in html


def test_render_preview_html_does_not_make_derived_summary_bullet_editable() -> None:
    service = RenderService()
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

    html = service.render_preview_html(presentation)
    derived_index = html.index("次回までの確認事項を整理する")
    derived_snippet = html[max(0, derived_index - 160): derived_index + 80]

    assert "次回までの確認事項を整理する" in html
    assert 'data-derived="true"' in derived_snippet
    assert 'data-field="bullet"' not in derived_snippet
