# Reviewer Quickstart

If you are reviewing `slide_app` for a portfolio or hiring screen, this is the shortest useful path.

## What To Look At First

1. [`README.md`](/home/sora/dev/llm-apps/slide_app/README.md)
2. [`samples/sample_input.json`](/home/sora/dev/llm-apps/slide_app/samples/sample_input.json)
3. [`samples/sample_output.json`](/home/sora/dev/llm-apps/slide_app/samples/sample_output.json)
4. [`app/services/generation_service.py`](/home/sora/dev/llm-apps/slide_app/app/services/generation_service.py)
5. [`app/models/schema.py`](/home/sora/dev/llm-apps/slide_app/app/models/schema.py)

## Fastest Demo Path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export MOCK_GENERATION=true
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/`

## What This Demonstrates

- provider-swappable LLM integration
- schema-first structured generation
- validation and repair before rendering
- shared JSON contract across preview and export

## Current Scope

The project is intentionally MVP-sized.
It is meant to show architecture and implementation discipline rather than polished slide design quality.
