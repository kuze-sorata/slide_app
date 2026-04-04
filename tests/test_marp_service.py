from app.models.schema import Presentation
from app.services.marp_service import MarpService


def test_render_markdown_outputs_marp_slides() -> None:
    service = MarpService()
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
                    "title": "背景",
                    "bullets": ["案件数は横ばい", "優先順位の見直しが必要"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "まとめ",
                    "bullets": ["重点案件を絞る"],
                    "layout": "layout4",
                },
            ],
        }
    )

    markdown = service.render_markdown(presentation)

    assert markdown.startswith("---\nmarp: true")
    assert "paginate: true" in markdown
    assert "size: 16:9" in markdown
    assert "# 営業進捗の共有" in markdown
    assert "# 背景" in markdown
    assert "- 案件数は横ばい" in markdown
    assert "- 優先順位の見直しが必要" in markdown
    assert "<!-- _class: title-slide -->" in markdown
    assert markdown.count("\n---\n") == 3


def test_render_markdown_keeps_standard_list_for_non_parallel_layout2() -> None:
    service = MarpService()
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
                    "title": "対応方針",
                    "bullets": ["優先案件を見直す"],
                    "layout": "layout4",
                },
            ],
        }
    )

    markdown = service.render_markdown(presentation)

    assert "# 全体進捗は計画を下回る" in markdown
    assert "- 主要案件の受注時期が遅延" in markdown
    assert "- 新規リード獲得が目標未達" in markdown
