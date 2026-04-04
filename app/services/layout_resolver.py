from app.models.render_spec import (
    ResolvedBlock,
    ResolvedItem,
    ResolvedPresentation,
    ResolvedSlide,
    SlidePattern,
)
from app.models.schema import Presentation, Slide
from app.utils.slide_design import (
    content_card_heading,
    is_parallel_content_slide,
    layout_label,
    layout3_panel_headings,
    slide_role_label,
    slide_type_label,
    split_bullets_for_columns,
)


class LayoutResolver:
    def resolve_presentation(self, presentation: Presentation) -> ResolvedPresentation:
        return ResolvedPresentation(
            deck_title=presentation.deck_title,
            slides=tuple(
                self.resolve_slide(slide)
                for slide in presentation.slides
            ),
        )

    def resolve_slide(self, slide: Slide) -> ResolvedSlide:
        pattern = self._resolve_pattern(slide)
        blocks = self._resolve_blocks(slide, pattern)
        return ResolvedSlide(
            id=slide.id,
            slide_type=slide.type,
            layout=slide.layout,
            title=slide.title,
            pattern=pattern,
            role_label=slide_role_label(slide),
            type_label=slide_type_label(slide.type),
            layout_label=layout_label(slide.layout),
            blocks=blocks,
        )

    def _resolve_pattern(self, slide: Slide) -> SlidePattern:
        if slide.type == "title":
            return "title_hero"
        if slide.type == "agenda":
            return "agenda_steps"
        if slide.type == "summary":
            return "action_summary"
        if slide.layout == "layout3":
            return "split_columns"
        if slide.type == "content" and is_parallel_content_slide(slide):
            return "parallel_cards"
        return "standard_list"

    def _resolve_blocks(self, slide: Slide, pattern: SlidePattern) -> tuple[ResolvedBlock, ...]:
        indexed_items = tuple(
            ResolvedItem(text=bullet, bullet_index=index)
            for index, bullet in enumerate(slide.bullets)
        )

        if pattern == "title_hero":
            return (ResolvedBlock(heading=None, items=indexed_items),)

        if pattern == "agenda_steps":
            return tuple(
                ResolvedBlock(heading=f"{index:02d}", items=(item,))
                for index, item in enumerate(indexed_items, start=1)
            )

        if pattern == "parallel_cards":
            total = max(len(indexed_items), 1)
            return tuple(
                ResolvedBlock(
                    heading=content_card_heading(index, total),
                    items=(item,),
                )
                for index, item in enumerate(indexed_items, start=1)
            ) or (
                ResolvedBlock(
                    heading=content_card_heading(1, 1),
                    items=(ResolvedItem(text="補足事項なし", bullet_index=None),),
                ),
            )

        if pattern == "split_columns":
            left_heading, right_heading = layout3_panel_headings(slide)
            left_items, right_items = split_bullets_for_columns(indexed_items)
            return (
                ResolvedBlock(heading=left_heading, items=tuple(left_items)),
                ResolvedBlock(
                    heading=right_heading,
                    items=tuple(right_items) or (ResolvedItem(text="補足事項なし", bullet_index=None),),
                ),
            )

        if pattern == "standard_list":
            return (
                ResolvedBlock(
                    heading=None,
                    items=indexed_items or (ResolvedItem(text="補足事項なし", bullet_index=None),),
                ),
            )

        action_blocks = [
            ResolvedBlock(heading=f"アクション {index}", items=(item,))
            for index, item in enumerate(indexed_items[:2], start=1)
        ]
        if len(action_blocks) == 1:
            action_blocks.append(
                ResolvedBlock(
                    heading="アクション 2",
                    items=(ResolvedItem(text="次回までの確認事項を整理する", bullet_index=None),),
                )
            )
        return tuple(action_blocks)
