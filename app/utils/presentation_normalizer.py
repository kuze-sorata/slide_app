from collections.abc import Iterable
import re


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

DEFAULT_BULLETS_BY_TYPE = {
    "title": ["資料の論点を短く共有", "判断に必要な要点を整理"],
    "agenda": ["背景", "課題", "次の打ち手"],
    "content": ["現状の要点を整理する", "次の対応を明確にする"],
    "summary": ["優先対応を決める", "次回確認点をそろえる"],
}

VAGUE_BULLETS = {
    "いろいろ",
    "その他",
    "各種対応",
    "詳細",
    "未定",
    "検討中",
    "確認中",
    "対応",
}

ACTION_KEYWORDS = (
    "整理",
    "見直す",
    "決める",
    "進める",
    "共有",
    "固定化",
    "実行",
    "再配分",
    "改善",
    "強化",
    "着手",
)

NEGATIVE_STATE_KEYWORDS = (
    "不足",
    "不明確",
    "遅れ",
    "停滞",
    "弱い",
    "ばらつく",
    "不十分",
)

LAYOUT3_HINTS = (
    "方針",
    "打ち手",
    "対応",
    "施策",
    "進め方",
    "見直し",
    "再整理",
    "優先",
)

BULLET_PREFIX_PATTERN = re.compile(r"^[\s\-*•・0-9０-９\.\)\(]+")
SPACE_PATTERN = re.compile(r"\s+")


def normalize_presentation_payload(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError("presentation payload must be a JSON object")

    raw_title = data.get("deck_title")
    if not isinstance(raw_title, str):
        raw_title = data.get("title")
    deck_title = normalize_text(raw_title) if isinstance(raw_title, str) else ""

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
        normalized_slides[0]["bullets"] = normalize_bullets(
            normalized_slides[0]["bullets"],
            slide_type="title",
            title=str(normalized_slides[0]["title"]),
        )

        normalized_slides[-1]["type"] = "summary"
        normalized_slides[-1]["layout"] = "layout4"
        normalized_slides[-1]["bullets"] = normalize_bullets(
            normalized_slides[-1]["bullets"],
            slide_type="summary",
            title=str(normalized_slides[-1]["title"]),
        )
        summary_bullets = rebuild_summary_bullets(
            normalized_slides[:-1],
            title=str(normalized_slides[-1]["title"]),
            existing_bullets=list(normalized_slides[-1]["bullets"]),
        )
        normalized_slides[-1]["bullets"] = summary_bullets

        if len(normalized_slides) >= 3 and not any(
            slide["type"] == "content" for slide in normalized_slides[1:-1]
        ):
            normalized_slides[1]["type"] = "content"
            normalized_slides[1]["layout"] = "layout2"

    return {
        "deck_title": (deck_title or derive_deck_title(normalized_slides))[:60],
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

    raw_type = slide.get("type")
    slide_type = normalize_slide_type(raw_type, index=index, total=total)

    raw_title = slide.get("title")
    title = normalize_text(raw_title) if isinstance(raw_title, str) else ""
    raw_bullets = slide.get("bullets")

    if not title:
        title = derive_slide_title(slide_type, raw_bullets, index)

    bullets = normalize_bullets(raw_bullets, slide_type=slide_type, title=title)

    raw_id = slide.get("id")
    slide_id = normalize_slide_id(raw_id, index=index)

    raw_layout = slide.get("layout")
    layout = normalize_layout(raw_layout, slide_type, title=title, bullets=bullets)

    return {
        "id": slide_id,
        "type": slide_type,
        "title": title[:30],
        "bullets": bullets,
        "layout": layout,
    }


def normalize_slide_id(value: object, *, index: int) -> str:
    if isinstance(value, str):
        cleaned = normalize_text(value)
        if cleaned:
            return cleaned[:40]
    if isinstance(value, int) and value > 0:
        return f"slide-{value}"
    return f"slide-{index}"


def normalize_slide_type(value: object, *, index: int, total: int) -> str:
    if index == 1:
        return "title"
    if index == total:
        return "summary"

    if isinstance(value, str):
        normalized = normalize_text(value).lower()
        normalized = TYPE_ALIASES.get(normalized, normalized)
        if normalized in {"title", "agenda", "content", "summary"}:
            return normalized

    if index == 2 and total >= 4:
        return "agenda"
    return "content"


def normalize_layout(
    value: object,
    slide_type: str,
    *,
    title: str,
    bullets: list[str],
) -> str:
    if slide_type == "content":
        suggested = suggest_content_layout(title, bullets)
        return suggested

    if isinstance(value, str):
        cleaned = normalize_text(value)
        if slide_type == "title" and cleaned == "layout1":
            return cleaned
        if slide_type == "agenda" and cleaned == "layout2":
            return cleaned
        if slide_type == "summary" and cleaned == "layout4":
            return cleaned
    return LAYOUT_BY_TYPE[slide_type]


def normalize_bullets(
    value: object,
    *,
    slide_type: str,
    title: str,
) -> list[str]:
    if value is None:
        items: Iterable[object] = []
    elif isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        items = []

    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        text = cleanup_bullet_text(item)
        text = adapt_bullet_for_slide_type(text, slide_type=slide_type, title=title)
        if not text:
            continue
        if text in seen:
            continue
        cleaned.append(text[:40])
        seen.add(text)
        if len(cleaned) == 4:
            break

    if cleaned:
        return cleaned
    return build_default_bullets(slide_type, title)


def cleanup_bullet_text(value: str) -> str:
    text = normalize_text(value)
    text = BULLET_PREFIX_PATTERN.sub("", text)
    text = text.strip("。")
    if text in VAGUE_BULLETS:
        return ""
    return text[:40]


def adapt_bullet_for_slide_type(text: str, *, slide_type: str, title: str) -> str:
    if not text:
        return ""

    if slide_type == "agenda":
        text = trim_sentence_ending(text)
        return text[:40]

    if slide_type == "summary":
        text = trim_sentence_ending(text)
        if not contains_action_keyword(text):
            inferred = infer_action_from_title(title)
            if inferred:
                return inferred[:40]
            return f"{text}を進める"[:40]
        return text[:40]

    if slide_type == "content":
        text = trim_sentence_ending(text)
        if text in {"背景", "課題", "打ち手"}:
            return f"{text}を整理する"[:40]
        if len(text) <= 8 and not contains_action_keyword(text):
            return f"{text}を整理する"[:40]
        return text[:40]

    return trim_sentence_ending(text)[:40]


def trim_sentence_ending(text: str) -> str:
    replacements = (
        ("しています", "する"),
        ("していく", "進める"),
        ("していきます", "進める"),
        ("すること", "する"),
        ("です", ""),
        ("ます", ""),
    )
    result = text
    for source, target in replacements:
        if result.endswith(source):
            result = result[: -len(source)] + target
            break
    return result.strip("。 ")


def contains_action_keyword(text: str) -> bool:
    return any(keyword in text for keyword in ACTION_KEYWORDS)


def infer_action_from_title(title: str) -> str:
    cleaned = normalize_text(title)
    if not cleaned:
        return "優先対応を決める"
    replacements = (
        ("の再整理が必要", "を再整理する"),
        ("の整理が必要", "を整理する"),
        ("の見直しが必要", "を見直す"),
    )
    for source, target in replacements:
        if source in cleaned:
            return cleaned.replace(source, target)[:40]
    replacements = (
        ("が課題", "を見直す"),
        ("が必要", "を進める"),
        ("を整理", "を整理する"),
        ("の整理", "を整理する"),
        ("方針", "方針を決める"),
    )
    for source, target in replacements:
        if source in cleaned:
            return cleaned.replace(source, target)[:40]
    if cleaned.endswith("課題"):
        return f"{cleaned[:-2]}を見直す"[:40]
    return f"{cleaned}を進める"[:40]


def suggest_content_layout(title: str, bullets: list[str]) -> str:
    joined = f"{title} {' '.join(bullets)}"
    action_like_bullets = sum(
        1 for bullet in bullets if contains_action_keyword(bullet) or any(hint in bullet for hint in LAYOUT3_HINTS)
    )
    if (
        len(bullets) >= 2
        and any(hint in title for hint in LAYOUT3_HINTS)
        and action_like_bullets >= 2
        and any(hint in joined for hint in LAYOUT3_HINTS)
    ):
        return "layout3"
    return "layout2"


def rebuild_summary_bullets(
    slides: list[dict[str, object]],
    *,
    title: str,
    existing_bullets: list[str],
) -> list[str]:
    candidates: list[str] = []

    for slide in reversed(slides):
        if slide.get("type") != "content":
            continue
        bullets = slide.get("bullets")
        if not isinstance(bullets, list):
            continue
        for bullet in bullets:
            if not isinstance(bullet, str):
                continue
            action = convert_content_bullet_to_action(bullet)
            if action and action not in candidates:
                candidates.append(action[:40])
            if len(candidates) == 2:
                break
        if len(candidates) == 2:
            break

    if candidates:
        return candidates

    normalized_existing = [
        adapt_bullet_for_slide_type(bullet, slide_type="summary", title=title)
        for bullet in existing_bullets
        if isinstance(bullet, str)
    ]
    normalized_existing = [bullet for bullet in normalized_existing if bullet]
    if normalized_existing:
        return normalized_existing[:2]
    return build_default_bullets("summary", title)


def convert_content_bullet_to_action(text: str) -> str:
    cleaned = trim_sentence_ending(normalize_text(text))
    if not cleaned:
        return ""
    replacements = (
        ("不足", "を強化する"),
        ("不明確", "を明確化する"),
        ("遅れ", "の進捗管理を見直す"),
        ("停滞", "の立て直しを進める"),
        ("弱い", "を改善する"),
        ("ばらつく", "を標準化する"),
        ("不十分", "を補強する"),
    )
    for source, target in replacements:
        if cleaned.endswith(source):
            stem = cleaned[:-len(source)]
            if stem.endswith("が"):
                stem = stem[:-1]
            return f"{stem}{target}"[:40]
        if source in cleaned:
            candidate = cleaned.replace(source, target)
            candidate = candidate.replace("がを", "を")
            return candidate[:40]
    if any(keyword in cleaned for keyword in NEGATIVE_STATE_KEYWORDS):
        return infer_action_from_title(cleaned)
    if contains_action_keyword(cleaned):
        return cleaned[:40]
    return f"{cleaned}を整理する"[:40]


def derive_slide_title(slide_type: str, bullets: object, index: int) -> str:
    if slide_type == "title":
        return "表紙"
    if slide_type == "agenda":
        return "共有項目"
    if slide_type == "summary":
        return "次の打ち手を決める"

    first_bullet = ""
    if isinstance(bullets, list):
        for item in bullets:
            if isinstance(item, str) and normalize_text(item):
                first_bullet = cleanup_bullet_text(item)
                break
    if first_bullet:
        if contains_action_keyword(first_bullet):
            return f"{first_bullet[:24]}"
        return f"{first_bullet[:20]}を整理する"
    return f"論点 {index}"


def derive_deck_title(slides: list[dict[str, object]]) -> str:
    if slides:
        first_title = slides[0].get("title")
        if isinstance(first_title, str) and first_title.strip():
            return normalize_text(first_title)
    return "資料タイトル"


def build_default_bullets(slide_type: str, title: str) -> list[str]:
    if slide_type == "summary":
        return [infer_action_from_title(title), "次回確認点をそろえる"]
    if slide_type == "content" and title:
        return [f"{title[:18]}を整理する"[:40], "次の対応を明確にする"]
    return DEFAULT_BULLETS_BY_TYPE[slide_type][:]


def normalize_text(value: str) -> str:
    return SPACE_PATTERN.sub(" ", value).strip()
