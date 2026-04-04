import json


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        raise ValueError("response text is empty")

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in response")

    candidate = text[start : end + 1]
    json.loads(candidate)
    return candidate
