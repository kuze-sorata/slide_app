import json
import re

from app.models.schema import SlideGenerationRequest
from app.utils.slide_design import build_prompt_design_rules_text


CONTENT_ROLES_JA = [
    ("current_state", "現状整理", "今の状況や背景を短く共有する"),
    ("issue", "課題整理", "何が問題かを具体的に示す"),
    ("cause", "原因整理", "なぜ起きているかを整理する"),
    ("action", "対応方針", "何をするかを短く示す"),
    ("impact", "期待効果", "実行後に何が良くなるかを示す"),
]

CONTENT_ROLES_EN = [
    ("current_state", "current state", "share the current status or background briefly"),
    ("issue", "issue", "show what problem matters most"),
    ("cause", "cause", "explain why the issue is happening"),
    ("action", "action", "show what should be done next"),
    ("impact", "impact", "show the expected benefit or outcome"),
]

JAPANESE_CHAR_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
ASCII_LETTER_PATTERN = re.compile(r"[A-Za-z]")


def detect_prompt_language(input_data: SlideGenerationRequest) -> str:
    texts = [
        input_data.user_request or "",
        input_data.theme or "",
        input_data.objective or "",
        input_data.audience or "",
        input_data.tone or "",
        input_data.extra_notes or "",
        *input_data.required_points,
    ]
    combined = " ".join(texts)
    if JAPANESE_CHAR_PATTERN.search(combined):
        return "ja"
    if ASCII_LETTER_PATTERN.search(combined):
        return "en"
    return "ja"


def build_prompt_payload(input_data: SlideGenerationRequest) -> dict[str, object]:
    payload: dict[str, object] = {
        "theme": input_data.theme,
        "objective": input_data.objective,
        "audience": input_data.audience,
        "slide_count": input_data.slide_count,
    }
    if input_data.user_request:
        payload["user_request"] = input_data.user_request
    if input_data.tone:
        payload["tone"] = input_data.tone
    if input_data.extra_notes:
        payload["extra_notes"] = input_data.extra_notes
    if input_data.required_points:
        payload["required_points"] = input_data.required_points
    if input_data.forbidden_expressions:
        payload["forbidden_expressions"] = input_data.forbidden_expressions[:4]
    return payload


def build_slide_generation_prompt(input_data: SlideGenerationRequest) -> str:
    prompt_language = detect_prompt_language(input_data)
    payload = build_prompt_payload(input_data)
    schema_hint = build_schema_hint(input_data.slide_count, prompt_language)
    output_language = "Japanese" if prompt_language == "ja" else "English"
    content_roles = CONTENT_ROLES_JA if prompt_language == "ja" else CONTENT_ROLES_EN
    design_rules = build_prompt_design_rules_text(prompt_language)
    forbidden_examples = (
        "いろいろ, その他, 頑張る, なんとなく"
        if prompt_language == "ja"
        else "various, miscellaneous, try hard, somehow"
    )
    qualitative_hint = (
        "進捗が弱い or 遅れがある"
        if prompt_language == "ja"
        else "progress is behind plan or delays remain"
    )

    return (
        f"You are a slide generation engine for {output_language} internal business presentations.\n"
        "Output ONLY valid JSON.\n"
        "Output ONLY one valid JSON object.\n"
        "No markdown.\n"
        "No explanations.\n"
        "No comments.\n"
        "No surrounding text.\n"
        "The JSON schema is:\n"
        '{"deck_title":"string","slides":[{"id":"string","type":"title|agenda|content|summary","title":"string","bullets":["string"],"layout":"layout1|layout2|layout3|layout4"}]}\n'
        "Hard constraints:\n"
        f"- Slides count: exactly {input_data.slide_count}\n"
        "- bullets per slide: 1 to 4\n"
        "- bullet length: max 40 characters\n"
        "- title length: max 30 characters\n"
        '- id must be unique and look like "slide-1"\n'
        f"- Output language: {output_language}\n"
        "- First slide must be title with layout1\n"
        "- Last slide must be summary with layout4\n"
        "- agenda uses layout2\n"
        "- content uses layout2 or layout3\n"
        "- Include at least one content slide\n"
        "- Each slide must communicate only one main message\n"
        "- Use short slide-like phrases suitable for internal documents\n"
        f"- Avoid generic wording such as {forbidden_examples}\n"
        "- Do not output HTML, markdown, tables, or notes\n"
        "- Do not invent concrete numbers, percentages, counts, or amounts unless they are present in the input\n"
        f"- If no numeric evidence is given, prefer qualitative wording such as {qualitative_hint}\n"
        f"Design rules:\n{design_rules}\n"
        "Writing rules:\n"
        "- Title slide: show the document theme or decision topic\n"
        "- Title slide bullets should be context or audience notes only, ideally 1 to 2 items\n"
        "- Agenda slide: list 2 to 4 discussion topics only\n"
        "- Agenda bullets should be parallel discussion topics, not full sentences\n"
        "- Content slide: choose exactly one role such as current state, issue, cause, action, or impact\n"
        "- layout2 should be used for a single thread of points that read top to bottom\n"
        "- If a content slide has 2 to 4 parallel points, write them in parallel wording with similar grammar\n"
        "- If a content slide has exactly 3 parallel points, make all 3 bullets equally important and comparable\n"
        "- layout3 should be used only when the content naturally splits into two comparable groups\n"
        "- Reading order should stay natural from left to right and top to bottom\n"
        "- Summary slide: end with concrete next actions or decisions\n"
        "- Summary bullets should start with an action-oriented business phrase when possible\n"
        "- Prefer business-ready phrasing over abstract nouns\n"
        "- Bullet phrases should be concise but meaningful, not single-word labels\n"
        "- If the audience is executives or managers, prioritize conclusion-first titles\n"
        f"Recommended slide plan:\n{build_slide_plan_text(input_data.slide_count, content_roles)}\n"
        f"Content slide role menu:\n{build_content_role_text(content_roles)}\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False)}\n"
        f"Example:\n{json.dumps(schema_hint, ensure_ascii=False)}"
    )


def build_simple_slide_generation_prompt(input_data: SlideGenerationRequest) -> str:
    prompt_language = detect_prompt_language(input_data)
    payload = build_prompt_payload(input_data)
    output_language = "Japanese" if prompt_language == "ja" else "English"
    phrase_guidance = (
        "Use short Japanese business phrases"
        if prompt_language == "ja"
        else "Use short English business phrases"
    )
    return (
        f"You generate {output_language} internal presentation slide drafts.\n"
        "Return JSON only.\n"
        "No markdown. No explanations.\n"
        f"Generate exactly {input_data.slide_count} slides.\n"
        "Required shape:\n"
        '{"deck_title":"string","slides":[{"id":"slide-1","type":"title|agenda|content|summary","title":"string","bullets":["string"],"layout":"layout1|layout2|layout3|layout4"}]}\n'
        "Rules:\n"
        "- First slide: title with layout1\n"
        "- Last slide: summary with layout4\n"
        "- Include at least one content slide\n"
        "- 1 to 4 bullets per slide\n"
        "- Keep titles within 30 characters\n"
        "- Keep bullets within 40 characters\n"
        f"- {phrase_guidance}\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def build_schema_hint(slide_count: int, prompt_language: str) -> dict[str, object]:
    if prompt_language == "en":
        return {
            "deck_title": "Sales Update Review",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "Sales Update Review",
                    "bullets": ["For sales director", "Progress and next actions"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "agenda",
                    "title": "Discussion Topics",
                    "bullets": ["Current progress", "Key issues", "Next actions"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "content",
                    "title": "Key deals are moving slowly",
                    "bullets": ["Closing timelines slipped", "Priorities vary by owner"],
                    "layout": "layout2",
                },
                {
                    "id": f"slide-{slide_count}",
                    "type": "summary",
                    "title": "Refocus on top deals",
                    "bullets": ["Reallocate effort to top deals", "Lock weekly review cadence"],
                    "layout": "layout4",
                },
            ],
        }
    return {
        "deck_title": "営業進捗の振り返り",
        "slides": [
            {
                "id": "slide-1",
                "type": "title",
                "title": "営業進捗の振り返り",
                "bullets": ["営業部長向けの共有", "現状と次の打ち手を整理"],
                "layout": "layout1",
            },
            {
                "id": "slide-2",
                "type": "agenda",
                "title": "共有項目",
                "bullets": ["進捗の要点", "課題の整理", "次の打ち手"],
                "layout": "layout2",
            },
            {
                "id": "slide-3",
                "type": "content",
                "title": "重点案件の停滞が課題",
                "bullets": ["受注見込みが後ろ倒し", "優先順位が案件別でぶれる"],
                "layout": "layout2",
            },
            {
                "id": f"slide-{slide_count}",
                "type": "summary",
                "title": "優先案件の再整理が必要",
                "bullets": ["重点案件へ工数を再配分する", "週次レビューを固定化する"],
                "layout": "layout4",
            },
        ],
    }


def build_slide_plan_text(
    slide_count: int,
    content_roles: list[tuple[str, str, str]],
) -> str:
    plan = []
    middle_slide_count = max(slide_count - 2, 1)

    for index in range(1, slide_count + 1):
        if index == 1:
            plan.append(f"- slide-{index}: title, role=theme or conclusion, layout=layout1")
            continue
        if index == slide_count:
            plan.append(f"- slide-{index}: summary, role=decision and next action, layout=layout4")
            continue
        if index == 2 and slide_count >= 4:
            plan.append(f"- slide-{index}: agenda, role=discussion topics, layout=layout2")
            continue

        content_index = index - 1 if slide_count < 4 else index - 2
        role_name, role_title, role_rule = content_roles[min(content_index - 1, len(content_roles) - 1)]
        layout = "layout3" if role_name in {"action", "impact"} and middle_slide_count >= 3 else "layout2"
        plan.append(
            f"- slide-{index}: content, focus={role_title}, layout={layout}, note={role_rule}"
        )
    return "\n".join(plan)


def build_content_role_text(content_roles: list[tuple[str, str, str]]) -> str:
    return "\n".join(f"- {role_title}: {role_rule}" for _, role_title, role_rule in content_roles)
