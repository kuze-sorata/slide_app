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
    assert "# 営業進捗の共有" in markdown
    assert "# 背景" in markdown
    assert "- 案件数は横ばい" in markdown
    assert markdown.count("\n---\n") == 3
