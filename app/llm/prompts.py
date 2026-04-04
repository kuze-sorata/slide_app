import json

from app.models.schema import SlideGenerationRequest


def build_prompt_payload(input_data: SlideGenerationRequest) -> dict[str, object]:
    payload: dict[str, object] = {
        "theme": input_data.theme,
        "objective": input_data.objective,
        "audience": input_data.audience,
        "slide_count": input_data.slide_count,
    }
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
                "bullets": ["対象は部長向け共有"],
                "layout": "layout1",
            },
            {
                "id": "slide-2",
                "type": "content",
                "title": "重点案件の停滞が課題",
                "bullets": ["受注見込みが後ろ倒し", "優先順位が担当別にばらつく"],
                "layout": "layout2",
            },
            {
                "id": f"slide-{input_data.slide_count}",
                "type": "summary",
                "title": "重点案件の再整理が必要",
                "bullets": ["案件優先度を即日見直す", "週次レビューを固定化する"],
                "layout": "layout4",
            },
        ],
    }
    return (
        "You are a slide generation engine.\n"
        "Output ONLY valid JSON.\n"
        "No explanations.\n"
        "No markdown.\n"
        "No comments.\n"
        "The JSON schema is:\n"
        '{"deck_title":"string","slides":[{"id":"string","type":"title|agenda|content|summary","title":"string","bullets":["string"],"layout":"layout1|layout2|layout3|layout4"}]}\n'
        "Constraints:\n"
        f"- Slides count: exactly {input_data.slide_count}\n"
        "- bullets per slide: 1 to 4\n"
        "- bullet length: max 40 characters\n"
        "- title length: max 30 characters\n"
        '- id must be unique and look like "slide-1"\n'
        "- Output language must be Japanese\n"
        "- Keep text concise and presentation-like\n"
        "- First slide must be title\n"
        "- Last slide must be summary\n"
        "- Include at least one content slide\n"
        "- title uses layout1\n"
        "- agenda uses layout2\n"
        "- content uses layout2 or layout3\n"
        "- summary uses layout4\n"
        "- Use short phrases, not long sentences\n"
        "- Avoid repetition\n"
        '- Avoid vague words like "いろいろ", "その他"\n'
        "- deck_title and slides must stay centered around structured JSON\n"
        f"Input: {json.dumps(payload, ensure_ascii=False)}\n"
        f"Example: {json.dumps(schema_hint, ensure_ascii=False)}"
    )


def build_simple_slide_generation_prompt(input_data: SlideGenerationRequest) -> str:
    sample = {
        "deck_title": "資料タイトル",
        "slides": [
            {
                "id": "slide-1",
                "type": "title",
                "title": "資料タイトル",
                "bullets": ["部長向け共有"],
                "layout": "layout1",
            },
            {
                "id": "slide-2",
                "type": "content",
                "title": "論点を整理する",
                "bullets": ["現状を短く共有する"],
                "layout": "layout2",
            },
            {
                "id": "slide-3",
                "type": "summary",
                "title": "次の打ち手を決める",
                "bullets": ["優先対応を明確にする"],
                "layout": "layout4",
            },
        ],
    }
    return (
        "Return this JSON exactly.\n"
        "JSON only.\n"
        f"{json.dumps(sample, ensure_ascii=False)}"
    )
