from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


SlideType = Literal["title", "agenda", "content", "summary"]
SlideLayout = Literal["layout1", "layout2", "layout3", "layout4"]


class Slide(BaseModel):
    id: str = Field(..., min_length=1, max_length=40, description="Unique slide identifier.")
    type: SlideType
    title: str = Field(..., min_length=1, max_length=30)
    bullets: list[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Short bullet phrases for the slide.",
    )
    layout: SlideLayout

    @field_validator("id")
    @classmethod
    def id_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("id must not be blank")
        return cleaned

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        if len(cleaned) > 30:
            raise ValueError("title must be at most 30 characters")
        return cleaned

    @field_validator("bullets")
    @classmethod
    def bullets_must_be_short_phrases(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        if not cleaned:
            raise ValueError("bullets must contain at least 1 item")
        if len(cleaned) > 4:
            raise ValueError("bullets must contain at most 4 items")
        for bullet in cleaned:
            if len(bullet) > 40:
                raise ValueError("each bullet must be at most 40 characters")
        return cleaned

    @model_validator(mode="after")
    def validate_layout_for_type(self) -> "Slide":
        expected = {
            "title": {"layout1"},
            "agenda": {"layout2"},
            "content": {"layout2", "layout3"},
            "summary": {"layout4"},
        }
        if self.layout not in expected[self.type]:
            raise ValueError(f"layout {self.layout} is invalid for slide type {self.type}")
        return self


class Presentation(BaseModel):
    deck_title: str = Field(..., min_length=1, max_length=60)
    slides: list[Slide] = Field(..., min_length=3, max_length=10)

    @field_validator("deck_title")
    @classmethod
    def deck_title_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("deck_title must not be blank")
        return cleaned

    @model_validator(mode="after")
    def validate_slide_sequence(self) -> "Presentation":
        if self.slides[0].type != "title":
            raise ValueError("the first slide must be of type 'title'")
        if self.slides[-1].type != "summary":
            raise ValueError("the last slide must be of type 'summary'")
        if not any(slide.type == "content" for slide in self.slides):
            raise ValueError("at least one content slide is required")

        ids = [slide.id for slide in self.slides]
        if len(ids) != len(set(ids)):
            raise ValueError("slide ids must be unique")
        return self


class SlideGenerationRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    objective: str = Field(..., min_length=1, max_length=200)
    audience: str = Field(..., min_length=1, max_length=200)
    slide_count: int = Field(..., ge=3, le=10)
    tone: str | None = Field(default=None, max_length=100)
    extra_notes: str | None = Field(default=None, max_length=1000)
    required_points: list[str] = Field(default_factory=list, max_length=10)
    forbidden_expressions: list[str] = Field(default_factory=list, max_length=10)
    debug_mode: bool = Field(
        default=False,
        description="Use a shorter debug prompt to verify model JSON generation.",
    )

    @field_validator(
        "theme",
        "objective",
        "audience",
        "tone",
        "extra_notes",
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("required_points", "forbidden_expressions")
    @classmethod
    def strip_text_list(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]
