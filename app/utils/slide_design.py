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


def build_prompt_design_rules_text() -> str:
    return "\n".join(f"- {rule}" for rule in DESIGN_RULES)


def slide_type_label(slide_type: str) -> str:
    return SLIDE_TYPE_LABELS.get(slide_type, slide_type)


def layout_label(layout: str) -> str:
    return LAYOUT_LABELS.get(layout, layout)


def slide_role_label(slide: Slide) -> str | None:
    if slide.type == "summary":
        return "次のアクション"
    if slide.type == "agenda":
        return "共有トピック"
    if slide.type == "title":
        return None
    if slide.layout == "layout3":
        return "比較して整理"
    return "要点整理"


def layout3_panel_headings(slide: Slide) -> tuple[str, str]:
    title = slide.title
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
