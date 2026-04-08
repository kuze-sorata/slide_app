from collections.abc import Sequence

from app.models.schema import Slide


SLIDE_TYPE_LABELS = {
    "title": "表紙",
    "agenda": "アジェンダ",
    "content": "本文",
    "summary": "まとめ",
}

LAYOUT_LABELS = {
    "layout1": "レイアウト1",
    "layout2": "レイアウト2",
    "layout3": "レイアウト3",
    "layout4": "レイアウト4",
}

DESIGN_RULES = (
    "社内資料向けの落ち着いたトーンにする",
    "1スライド1メッセージを維持し、余白を優先する",
    "タイトルは結論先行で短くする",
    "並列な情報は同じ粒度の短いbulletでそろえる",
    "読む順番は左から右、上から下で迷わない構成にする",
    "本文 bullets は 2〜3 点を基本にする",
    "3つの並列項目は3つの同格な要点として出す",
    "agenda は並列な名詞句で流れを示す",
    "layout3 は比較や課題/対応の二分割だけに使う",
    "summary は実行可能な次アクションで終える",
    "色は増やしすぎず、強調色は限定する",
)

DESIGN_RULES_EN = (
    "Use a calm tone suitable for internal business slides",
    "Keep one main message per slide and prioritize whitespace",
    "Keep slide titles short and conclusion-first",
    "Use short bullets with parallel wording for parallel information",
    "Keep the reading order natural from left to right and top to bottom",
    "Prefer 2 to 3 bullets for content slides",
    "If there are 3 parallel points, make them equally important and comparable",
    "Use agenda slides for parallel noun phrases or discussion topics",
    "Use layout3 only for clear two-way comparisons or split themes",
    "End the summary slide with actionable next steps",
    "Limit the number of colors and keep accent colors restrained",
)


def build_prompt_design_rules_text(language: str = "ja") -> str:
    rules = DESIGN_RULES_EN if language == "en" else DESIGN_RULES
    return "\n".join(f"- {rule}" for rule in rules)


def slide_type_label(slide_type: str) -> str:
    return SLIDE_TYPE_LABELS.get(slide_type, slide_type)


def layout_label(layout: str) -> str:
    return LAYOUT_LABELS.get(layout, layout)


def is_japanese_text(text: str) -> bool:
    return any("\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff" for char in text)


def slide_language(slide: Slide) -> str:
    text = " ".join([slide.title, *slide.bullets])
    return "ja" if is_japanese_text(text) else "en"


def slide_role_label(slide: Slide) -> str | None:
    language = slide_language(slide)
    if slide.type == "summary":
        return "次のアクション" if language == "ja" else "Next actions"
    if slide.type == "agenda":
        return "共有トピック" if language == "ja" else "Topics"
    if slide.type == "title":
        return None
    if slide.layout == "layout3":
        return "比較して整理" if language == "ja" else "Comparison"
    return "要点整理" if language == "ja" else "Key points"


def layout3_panel_headings(slide: Slide) -> tuple[str, str]:
    language = slide_language(slide)
    title = slide.title
    if language == "en":
        lowered = title.lower()
        if any(keyword in lowered for keyword in ("issue", "cause", "current", "bottleneck", "delay")):
            return ("Current state", "Response")
        if any(keyword in lowered for keyword in ("action", "plan", "approach", "next step", "strategy")):
            return ("Action 1", "Action 2")
        if "comparison" in lowered or "compare" in lowered:
            return ("Group 1", "Group 2")
        return ("Point 1", "Point 2")
    if any(keyword in title for keyword in ("課題", "原因", "現状", "ボトルネック")):
        return ("現状・課題", "対応・示唆")
    if any(keyword in title for keyword in ("方針", "打ち手", "対応", "進め方", "施策")):
        return ("打ち手 1", "打ち手 2")
    if "比較" in title:
        return ("比較 1", "比較 2")
    return ("論点 1", "論点 2")


def split_bullets_for_columns(bullets: Sequence[str]) -> tuple[list[str], list[str]]:
    midpoint = (len(bullets) + 1) // 2
    return list(bullets[:midpoint]), list(bullets[midpoint:])


def content_card_heading(index: int, total: int) -> str:
    return content_card_heading_for_language(index, total, "ja")


def content_card_heading_for_language(index: int, total: int, language: str) -> str:
    if language == "en":
        if total <= 1:
            return "Point"
        return f"Point {index}"
    if total <= 1:
        return "要点"
    return f"要点 {index}"


def is_parallel_content_slide(slide: Slide) -> bool:
    bullet_count = len(slide.bullets)
    if bullet_count >= 3:
        return True

    if bullet_count < 2:
        return False

    title = slide.title
    parallel_hints = (
        "要点",
        "論点",
        "項目",
        "ポイント",
        "施策",
        "サービス",
        "機能",
        "特徴",
        "柱",
        "テーマ",
    )
    return any(hint in title for hint in parallel_hints)
