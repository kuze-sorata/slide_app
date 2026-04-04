import json

from app.models.schema import SlideGenerationRequest
from app.utils.slide_design import build_prompt_design_rules_text


CONTENT_ROLES = [
    ("current_state", "現状整理", "今の状況や背景を短く共有する"),
    ("issue", "課題整理", "何が問題かを具体的に示す"),
    ("cause", "原因整理", "なぜ起きているかを整理する"),
    ("action", "対応方針", "何をするかを短く示す"),
    ("impact", "期待効果", "実行後に何が良くなるかを示す"),
]


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
    payload = build_prompt_payload(input_data)
    schema_hint = {
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
                "id": f"slide-{input_data.slide_count}",
                "type": "summary",
                "title": "優先案件の再整理が必要",
                "bullets": ["重点案件へ工数を再配分する", "週次レビューを固定化する"],
                "layout": "layout4",
            },
        ],
    }

    return (
        "You are a slide generation engine for Japanese internal business presentations.\n"
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
        "- Output language: Japanese\n"
        "- First slide must be title with layout1\n"
        "- Last slide must be summary with layout4\n"
        "- agenda uses layout2\n"
        "- content uses layout2 or layout3\n"
        "- Include at least one content slide\n"
        "- Each slide must communicate only one main message\n"
        "- Use short slide-like phrases suitable for internal documents\n"
        "- Avoid generic wording such as いろいろ, その他, 頑張る, なんとなく\n"
        "- Do not output HTML, markdown, tables, or notes\n"
        "- Do not invent concrete numbers, percentages, counts, or amounts unless they are present in the input\n"
        "- If no numeric evidence is given, prefer qualitative wording such as 進捗が弱い or 遅れがある\n"
        f"Design rules:\n{build_prompt_design_rules_text()}\n"
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
        f"Recommended slide plan:\n{build_slide_plan_text(input_data.slide_count)}\n"
        f"Content slide role menu:\n{build_content_role_text()}\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False)}\n"
        f"Example:\n{json.dumps(schema_hint, ensure_ascii=False)}"
    )


def build_simple_slide_generation_prompt(input_data: SlideGenerationRequest) -> str:
    payload = build_prompt_payload(input_data)
    return (
        "You generate Japanese internal presentation slide drafts.\n"
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
        "- Use short Japanese business phrases\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def build_slide_plan_text(slide_count: int) -> str:
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
        role_name, role_title, role_rule = CONTENT_ROLES[min(content_index - 1, len(CONTENT_ROLES) - 1)]
        layout = "layout3" if role_name in {"action", "impact"} and middle_slide_count >= 3 else "layout2"
        plan.append(
            f"- slide-{index}: content, focus={role_title}, layout={layout}, note={role_rule}"
        )
    return "\n".join(plan)


def build_content_role_text() -> str:
    return "\n".join(
        f"- {role_title}: {role_rule}"
        for _, role_title, role_rule in CONTENT_ROLES
    )
