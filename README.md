# slide_app

`slide_app` is a FastAPI app that turns natural-language requests into structured slide JSON, editable preview screens, and optional Marp/PDF/PPTX exports.

It is built as an applied LLM workflow rather than a text-only demo:
- structured JSON is the system contract
- generation, validation, rendering, and export are separated
- Japanese and English prompts are supported
- `JP / EN` UI toggle is available for demos

## Screenshots

### Input UI

![English input UI](docs/screenshots/input_en.png)

### Preview UI

![English preview UI](docs/screenshots/preview_en.png)

## What It Does

- accepts a short presentation request
- generates a constrained slide deck as JSON
- renders an editable HTML preview
- exports the same deck to Marp, PDF, and PPTX
- supports API-hosted LLM providers behind a provider abstraction

## Why It Matters

This repo shows a practical LLM application pattern:
- structured output instead of raw prose
- validation and repair before rendering
- provider-swappable inference backend
- one JSON contract shared across preview and export

## Tech Stack

Python, FastAPI, Pydantic v2, httpx, Jinja2, python-pptx, pytest

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export MOCK_GENERATION=true
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/`

Example prompt:

```text
Create a 5-slide update for a sales director covering current progress, key issues, and next actions. Keep the wording short, clear, and easy to present in a meeting.
```

## JSON Contract

```json
{
  "deck_title": "string",
  "slides": [
    {
      "id": "string",
      "type": "title | agenda | content | summary",
      "title": "string",
      "bullets": ["string"],
      "layout": "layout1 | layout2 | layout3 | layout4"
    }
  ]
}
```

Rules:
- 3 to 10 slides
- 1 to 4 bullets per slide
- first slide is `title`
- last slide is `summary`
- at least one `content` slide

## Notes

- main use case: short internal presentation drafts
- export is manual only
- quality target is draft-level, with speed and stability prioritized over polish
- tests: `./.venv/bin/pytest`
