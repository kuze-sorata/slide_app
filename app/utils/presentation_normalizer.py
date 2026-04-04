from collections.abc import Iterable


TYPE_ALIASES = {
    "bullet": "content",
    "bullet_list": "content",
    "bulleted_list": "content",
    "bullet_points": "content",
    "bullets": "content",
    "summary_slide": "summary",
}

LAYOUT_BY_TYPE = {
    "title": "layout1",
    "agenda": "layout2",
    "content": "layout2",
    "summary": "layout4",
}


def normalize_presentation_payload(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError("presentation payload must be a JSON object")

    raw_title = data.get("deck_title")
    if not isinstance(raw_title, str):
        raw_title = data.get("title")
    deck_title = raw_title.strip() if isinstance(raw_title, str) else ""

    slides = data.get("slides")
    if not isinstance(slides, list):
        raise ValueError("presentation slides must be a list")

    normalized_slides = [
        normalize_slide_payload(slide, index=index, total=len(slides))
        for index, slide in enumerate(slides, start=1)
    ]

    if normalized_slides:
        normalized_slides[0]["type"] = "title"
        normalized_slides[0]["layout"] = "layout1"
        normalized_slides[-1]["type"] = "summary"
        normalized_slides[-1]["layout"] = "layout4"
        if len(normalized_slides) >= 3 and not any(
            slide["type"] == "content" for slide in normalized_slides[1:-1]
        ):
            normalized_slides[1]["type"] = "content"
            normalized_slides[1]["layout"] = "layout2"

    return {
        "deck_title": deck_title or derive_deck_title(normalized_slides),
        "slides": normalized_slides,
    }


def normalize_slide_payload(
    slide: object,
    *,
    index: int,
    total: int,
) -> dict[str, object]:
    if not isinstance(slide, dict):
        raise ValueError("slide payload must be an object")

    bullets = normalize_bullets(slide.get("bullets"))
    raw_type = slide.get("type")
    slide_type = normalize_slide_type(raw_type, index=index, total=total)

    raw_title = slide.get("title")
    title = raw_title.strip() if isinstance(raw_title, str) else ""
    if not title:
        title = derive_slide_title(slide_type, index)

    raw_id = slide.get("id")
    slide_id = normalize_slide_id(raw_id, index=index)

    raw_layout = slide.get("layout")
    layout = normalize_layout(raw_layout, slide_type)

    return {
        "id": slide_id,
        "type": slide_type,
        "title": title[:30],
        "bullets": bullets,
        "layout": layout,
    }


def normalize_slide_id(value: object, *, index: int) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    if isinstance(value, int) and value > 0:
        return f"slide-{value}"
    return f"slide-{index}"


def normalize_slide_type(value: object, *, index: int, total: int) -> str:
    if index == 1:
        return "title"
    if index == total:
        return "summary"

    if isinstance(value, str):
        normalized = value.strip().lower()
        normalized = TYPE_ALIASES.get(normalized, normalized)
        if normalized in {"title", "agenda", "content", "summary"}:
            return normalized

    if index == 2 and total >= 4:
        return "agenda"
    return "content"


def normalize_layout(value: object, slide_type: str) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if slide_type == "content" and cleaned in {"layout2", "layout3"}:
            return cleaned
        if slide_type == "title" and cleaned == "layout1":
            return cleaned
        if slide_type == "agenda" and cleaned == "layout2":
            return cleaned
        if slide_type == "summary" and cleaned == "layout4":
            return cleaned
    return LAYOUT_BY_TYPE[slide_type]


def normalize_bullets(value: object) -> list[str]:
    if value is None:
        items: Iterable[object] = []
    elif isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        items = []

    cleaned: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if text:
            cleaned.append(text[:40])
        if len(cleaned) == 4:
            break

    if cleaned:
        return cleaned
    return ["要点を整理する"]


def derive_slide_title(slide_type: str, index: int) -> str:
    if slide_type == "title":
        return "表紙"
    if slide_type == "agenda":
        return "進行項目"
    if slide_type == "summary":
        return "まとめ"
    return f"論点 {index}"


def derive_deck_title(slides: list[dict[str, object]]) -> str:
    if slides:
        first_title = slides[0].get("title")
        if isinstance(first_title, str) and first_title.strip():
            return first_title.strip()
    return "資料タイトル"
