# GitHub Portfolio Plan for `kuze-sorata`

## Goal

Reach a strong "ready to apply" baseline for Data Scientist / AI Engineer / Applied ML roles in Melbourne within 3 days.

Priority:

1. `slide_app`
2. `personal-os-public`
3. `lead_expansion`

Principles:

- optimize for recruiter comprehension in under 3 minutes
- prefer README, reproducibility, and project framing over new feature work
- avoid destructive changes
- keep public-safe repos easy to run locally

## Current Assessment

### `slide_app`

Strengths:

- strongest applied LLM project in the set
- clear schema-first architecture
- provider abstraction, validation, rendering, and export are separated
- includes tests and sample payloads

Weaknesses:

- README previously explained the project mostly from a refactor perspective
- business value and engineering value were not immediately clear to English-speaking reviewers
- screenshot/demo guidance is still missing

### `personal-os-public`

Strengths:

- good "production-inspired backend with mock-safe public demo" story
- practical workflow: task selection, calendar fit, summary jobs
- already has tests and mock data

Weaknesses:

- README can better explain why the scheduling/priority logic matters
- needs a crisper architecture summary and demo-first quickstart
- should more clearly separate public demo constraints from private production context

### `lead_expansion`

Strengths:

- useful applied analytics / targeting workflow
- business framing is relevant for B2B, RevOps, and GTM analytics roles
- has reusable code, tests, and output artifacts

Weaknesses:

- currently reads more like a notebook project than an applied ML/analytics portfolio piece
- README should foreground outputs, decisions, and reproducibility
- needs a clearer "what a reviewer should look at first" path

## Three-Day Plan

### Day 1

- finalize `slide_app` README and run verification
- prepare repo metadata: description, topics, pinned rationale
- identify one screenshot or GIF to capture later

### Day 2

- rewrite `personal-os-public` README for hiring review
- tighten run instructions and mock-mode explanation
- rewrite `lead_expansion` README around business problem, outputs, and reproducibility

### Day 3

- publish profile README
- update pinned repositories, descriptions, and topics
- do one final pass for consistency across all public repos

## Recommended Pinned Repositories

Recommended order:

1. `slide_app`
2. `personal-os-public`
3. `lead_expansion`
4. one smaller repo only if it shows software breadth cleanly

Rationale:

- `slide_app` shows applied LLM engineering
- `personal-os-public` shows backend/product thinking
- `lead_expansion` shows analytics and business framing

## Repository Description Drafts

### `slide_app`

FastAPI app that generates Japanese internal slide drafts from natural language using API-hosted LLMs, structured JSON validation, and HTML/PPTX export.

### `personal-os-public`

Public-safe FastAPI demo of a personal productivity backend that prioritizes daily tasks, estimates free time, and generates summary messages from mock data.

### `lead_expansion`

Applied analytics project for B2B target account prioritization using simulated company data, ICP assumptions, and an explainable scoring pipeline.

## Suggested Topics

### `slide_app`

- `fastapi`
- `python`
- `llm`
- `applied-ai`
- `structured-output`
- `prompt-engineering`
- `pydantic`
- `pptx`

### `personal-os-public`

- `fastapi`
- `python`
- `productivity`
- `automation`
- `task-prioritization`
- `backend`
- `mock-data`

### `lead_expansion`

- `python`
- `data-science`
- `applied-ml`
- `sales-analytics`
- `lead-scoring`
- `b2b`
- `notebook`
- `pytest`

## GitHub Profile README Draft

```md
# Hi, I'm Sorata Kuze

I build practical AI and data products with Python, FastAPI, and applied machine learning workflows.
Currently based in Melbourne on a Working Holiday visa, and looking for Data Scientist, AI Engineer, or Applied ML opportunities.

## What I work on

- LLM applications with structured outputs and evaluation-minded pipelines
- FastAPI backends for automation and decision-support tools
- Applied analytics projects that turn business assumptions into reproducible workflows

## Selected Projects

### Slide Draft Generator
FastAPI app that generates Japanese internal slide drafts from natural language using API-hosted LLMs, schema validation, and preview/export flows.

### Personal OS
Public-safe productivity backend demo that scores tasks, estimates available time, and generates daily summaries from mock data.

### Lead Expansion
B2B lead prioritization workflow that converts ICP assumptions into an explainable target-account ranking pipeline.

## Stack

Python, FastAPI, Pydantic, httpx, pytest, pandas, scikit-learn basics, SQL, Git, GitHub Actions

## Looking For

Data Scientist / AI Engineer / Applied ML roles in Melbourne.
Open to backend-heavy ML application work, internal tools, analytics products, and automation systems.
```

## GitHub Bio Draft

Applied AI / Data projects with Python and FastAPI. Based in Melbourne. Open to Data Scientist / AI Engineer / Applied ML roles.

## Hiring Readiness Judgment

Current judgment: close, but not fully ready until the other two core repos and the profile README are aligned.

After the planned README and metadata updates:

- yes, application outreach can start
- portfolio will be good enough for the first screening stage
- remaining weakness will be visual polish and explicit impact metrics, not basic professionalism

## Remaining Gaps After This Pass

- add screenshots or a short demo GIF for `slide_app`
- ensure each repo has consistent badges or at least consistent quickstart sections
- add one line on datasets, privacy, and mock/public-safe boundaries where relevant
- optionally add lightweight CI status if workflows already exist
