from dataclasses import dataclass
from typing import Literal


SlidePattern = Literal[
    "title_hero",
    "agenda_steps",
    "parallel_cards",
    "standard_list",
    "split_columns",
    "action_summary",
]


@dataclass(slots=True, frozen=True)
class ResolvedItem:
    text: str
    bullet_index: int | None = None


@dataclass(slots=True, frozen=True)
class ResolvedBlock:
    heading: str | None
    items: tuple[ResolvedItem, ...]


@dataclass(slots=True, frozen=True)
class ResolvedSlide:
    id: str
    slide_type: str
    layout: str
    title: str
    pattern: SlidePattern
    role_label: str | None
    type_label: str
    layout_label: str
    blocks: tuple[ResolvedBlock, ...]


@dataclass(slots=True, frozen=True)
class ResolvedPresentation:
    deck_title: str
    slides: tuple[ResolvedSlide, ...]
