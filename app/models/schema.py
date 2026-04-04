import re
from typing import Any, Literal

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
    user_request: str | None = Field(default=None, max_length=2000)
    theme: str | None = Field(default=None, max_length=200)
    objective: str | None = Field(default=None, max_length=200)
    audience: str | None = Field(default=None, max_length=200)
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
        "user_request",
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

    @model_validator(mode="before")
    @classmethod
    def derive_fields_from_user_request(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        request_text = str(data.get("user_request") or "").strip()
        if not request_text:
            return data

        if not data.get("audience"):
            inferred_audience = infer_audience_from_request(request_text)
            if inferred_audience:
                data["audience"] = inferred_audience

        if not data.get("theme"):
            inferred_theme = infer_theme_from_request(request_text)
            if inferred_theme:
                data["theme"] = inferred_theme

        if not data.get("objective"):
            inferred_objective = infer_objective_from_request(request_text)
            if inferred_objective:
                data["objective"] = inferred_objective

        if not data.get("extra_notes"):
            inferred_notes = infer_extra_notes_from_request(request_text)
            if inferred_notes:
                data["extra_notes"] = inferred_notes

        if not data.get("slide_count"):
            inferred_slide_count = infer_slide_count_from_request(request_text)
            if inferred_slide_count is not None:
                data["slide_count"] = inferred_slide_count

        if not data.get("required_points"):
            inferred_points = infer_required_points_from_request(request_text)
            if inferred_points:
                data["required_points"] = inferred_points

        return data

    @model_validator(mode="after")
    def validate_required_generation_context(self) -> "SlideGenerationRequest":
        if not self.user_request and not (self.theme and self.objective and self.audience):
            raise ValueError(
                "資料リクエストを入力してください。詳細設定だけで送る場合は theme, objective, audience をすべて埋めてください"
            )
        if not self.theme:
            raise ValueError("theme is required")
        if not self.objective:
            raise ValueError("objective is required")
        if not self.audience:
            raise ValueError("audience is required")
        return self


AUDIENCE_PATTERN = re.compile(
    r"(?P<audience>[^\s、。]{1,20})(向け|に|用)(?:に)?",
)
SLIDE_COUNT_PATTERN = re.compile(r"(?P<count>[3-9]|10)枚")


def infer_audience_from_request(text: str) -> str | None:
    match = AUDIENCE_PATTERN.search(text)
    if match:
        audience = match.group("audience").strip("、。 ")
        audience = audience.removesuffix("向け").removesuffix("用")
        if audience and audience not in {"資料", "共有", "説明"}:
            return audience
    return None


def infer_slide_count_from_request(text: str) -> int | None:
    match = SLIDE_COUNT_PATTERN.search(text)
    if match:
        return int(match.group("count"))
    return None


def infer_theme_from_request(text: str) -> str | None:
    patterns = (
        r"(?P<theme>[^。]{1,40})を(?P<count>[3-9]|10)枚で",
        r"(?P<theme>[^。]{1,40})について",
        r"(?P<theme>[^。]{1,40})の資料",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            theme = match.group("theme").strip("、。 ")
            theme = re.sub(r"^[^、。]{1,20}(向けに|向け|用に)", "", theme).strip("、。 ")
            if theme:
                return theme[:200]
    first_sentence = text.split("。", 1)[0].strip()
    if first_sentence:
        return first_sentence[:200]
    return None


def infer_objective_from_request(text: str) -> str | None:
    patterns = (
        r"(?P<objective>[^。]*整理したい)",
        r"(?P<objective>[^。]*決めたい)",
        r"(?P<objective>[^。]*相談したい)",
        r"(?P<objective>[^。]*説明したい)",
        r"(?P<objective>[^。]*共有したい)",
        r"(?P<objective>[^。]*確認したい)",
        r"(?P<objective>[^。]*報告したい)",
        r"(?P<objective>[^。]*提案したい)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            objective = match.group("objective").strip("、。 ")
            if objective:
                return objective[:200]
    if "確認" in text:
        return "現状と論点を確認する"
    if "報告" in text:
        return "現状を簡潔に報告する"
    if "レビュー" in text or "振り返り" in text:
        return "現状と課題を振り返り次の打ち手を整理する"
    if "共有" in text:
        return "要点を簡潔に共有する"
    if "提案" in text:
        return "提案内容と判断ポイントを共有する"
    if "説明" in text:
        return "要点をわかりやすく説明する"
    if "整理" in text:
        return "論点を整理して共有する"
    if text.strip():
        return "要点を整理して共有する"
    return None


def infer_extra_notes_from_request(text: str) -> str | None:
    notes: list[str] = []
    if "仮置き" in text:
        notes.append("数字は仮置きでよい")
    if "簡潔" in text:
        notes.append("簡潔にまとめる")
    if "結論" in text:
        notes.append("結論を先に示す")
    if notes:
        return " / ".join(dict.fromkeys(notes))
    return None


def infer_required_points_from_request(text: str) -> list[str]:
    mapping = (
        ("進捗", "進捗"),
        ("課題", "課題"),
        ("打ち手", "次の打ち手"),
        ("対応", "次の打ち手"),
        ("効果", "期待効果"),
        ("意思決定", "意思決定事項"),
        ("背景", "背景"),
    )
    points: list[str] = []
    for keyword, label in mapping:
        if keyword in text and label not in points:
            points.append(label)
    return points[:10]
