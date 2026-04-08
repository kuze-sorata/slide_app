import pytest

from app.llm.base import LLMProvider
from app.llm.ollama import OllamaClient
from app.llm.prompts import (
    build_simple_slide_generation_prompt,
    build_slide_generation_prompt,
)
from app.models.schema import Presentation, SlideGenerationRequest
from app.services.generation_service import (
    GenerationError,
    GenerationService,
    MockLLMClient,
)
from app.utils.config import Settings
from app.utils.presentation_normalizer import normalize_presentation_payload


class StubProvider(LLMProvider):
    def __init__(self, response: str) -> None:
        self.response = response

    async def generate_text(self, prompt: str) -> str:
        return self.response


class FailingProvider(LLMProvider):
    async def generate_text(self, prompt: str) -> str:
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_generation_service_returns_presentation() -> None:
    service = GenerationService(
        provider=StubProvider(
            (
                '{"deck_title":"営業進捗の要点","slides":['
                '{"id":"slide-1","type":"title","title":"営業進捗の要点","bullets":["部長向け共有"],"layout":"layout1"},'
                '{"id":"slide-2","type":"content","title":"重点案件の停滞が課題","bullets":["受注見込みが後ろ倒し"],"layout":"layout2"},'
                '{"id":"slide-3","type":"summary","title":"優先案件の再整理が必要","bullets":["案件優先度を見直す"],"layout":"layout4"}'
                "]}"
            )
        )
    )

    result = await service.generate(
        SlideGenerationRequest(
            theme="営業進捗の振り返り",
            objective="現状と打ち手を共有する",
            audience="営業部長",
            slide_count=3,
        )
    )

    assert result.deck_title == "営業進捗の要点"
    assert result.slides[0].type == "title"
    assert result.slides[-1].type == "summary"


@pytest.mark.asyncio
async def test_generation_service_wraps_provider_error() -> None:
    service = GenerationService(provider=FailingProvider())

    with pytest.raises(GenerationError):
        await service.generate(
            SlideGenerationRequest(
                theme="営業進捗の振り返り",
                objective="現状と打ち手を共有する",
                audience="営業部長",
                slide_count=3,
            )
        )


class RetryingOllamaClient(OllamaClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://localhost:11434", model="phi3:mini")
        self.prompts: list[str] = []

    async def generate_text(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return '{"deck_title":"営業進捗","slides":[{"id":"slide-1","type":"title","title":"営業進捗"}]}'
        return (
            '{"deck_title":"営業進捗","slides":['
            '{"id":"slide-1","type":"title","title":"営業進捗","bullets":["部長向け共有"],"layout":"layout1"},'
            '{"id":"slide-2","type":"content","title":"課題を整理する","bullets":["重点案件を整理する"],"layout":"layout2"},'
            '{"id":"slide-3","type":"summary","title":"優先対応を決める","bullets":["次の打ち手を整理する"],"layout":"layout4"}'
            "]}"
        )


@pytest.mark.asyncio
async def test_generation_service_retries_with_lightweight_prompt() -> None:
    client = RetryingOllamaClient()
    service = GenerationService(provider=client)
    payload = SlideGenerationRequest(
        theme="営業進捗の振り返り",
        objective="現状と打ち手を共有する",
        audience="営業部長",
        slide_count=3,
    )

    result = await service.generate(payload)

    assert result.slides[-1].type == "summary"
    assert len(client.prompts) == 2
    assert "The previous response was invalid" in client.prompts[1]


def test_build_slide_generation_prompt_stays_json_focused() -> None:
    prompt = build_slide_generation_prompt(
        SlideGenerationRequest(
            theme="営業進捗の振り返り",
            objective="現状と打ち手を共有する",
            audience="営業部長",
            slide_count=3,
            forbidden_expressions=["気合いで", "なんとなく"],
        )
    )

    assert "Output ONLY valid JSON" in prompt
    assert '"deck_title":"string"' in prompt
    assert "layout1|layout2|layout3|layout4" in prompt
    assert "Recommended slide plan" in prompt
    assert "Content slide role menu" in prompt
    assert "Design rules:" in prompt
    assert "If a content slide has exactly 3 parallel points" in prompt
    assert "Reading order should stay natural from left to right" in prompt
    assert "layout3 should be used only when the content naturally splits" in prompt
    assert "Do not invent concrete numbers" in prompt
    assert "Input:" in prompt


def test_build_simple_slide_generation_prompt_is_shorter() -> None:
    payload = SlideGenerationRequest(
        theme="営業進捗の振り返り",
        objective="現状と打ち手を共有する",
        audience="営業部長",
        slide_count=5,
    )

    standard = build_slide_generation_prompt(payload)
    simple = build_simple_slide_generation_prompt(payload)

    assert len(simple) < len(standard)
    assert "Return JSON only." in simple
    assert "Generate exactly 5 slides." in simple
    assert "営業進捗の振り返り" in simple
    assert "Input:" in simple


def test_build_slide_generation_prompt_switches_output_language_for_english_input() -> None:
    payload = SlideGenerationRequest(
        user_request=(
            "Create a 5-slide update for a sales director covering current progress, "
            "key issues, and next actions."
        ),
        slide_count=5,
    )

    prompt = build_slide_generation_prompt(payload)

    assert "Output language: English" in prompt
    assert "Use short slide-like phrases suitable for internal documents" in prompt
    assert "Sales Update Review" in prompt
    assert "Current progress" in prompt
    assert "Japanese internal business presentations" not in prompt


def test_build_simple_slide_generation_prompt_switches_output_language_for_english_input() -> None:
    payload = SlideGenerationRequest(
        user_request=(
            "Create a 5-slide update for a sales director covering current progress, "
            "key issues, and next actions."
        ),
        slide_count=5,
    )

    prompt = build_simple_slide_generation_prompt(payload)

    assert "You generate English internal presentation slide drafts." in prompt
    assert "Use short English business phrases" in prompt


class HangingOllamaClient(OllamaClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://localhost:11434", model="phi3:mini")

    async def generate_text(self, prompt: str) -> str:
        await pytest.importorskip("asyncio").sleep(0.05)
        return ""


@pytest.mark.asyncio
async def test_generation_service_times_out_for_hanging_provider() -> None:
    client = HangingOllamaClient()
    service = GenerationService(provider=client, generation_timeout_seconds=0.01)

    with pytest.raises(GenerationError, match="timed out"):
        await service.generate(
            SlideGenerationRequest(
                theme="営業進捗の振り返り",
                objective="現状と打ち手を共有する",
                audience="営業部長",
                slide_count=3,
            )
        )


@pytest.mark.asyncio
async def test_mock_llm_client_returns_slide_like_presentation() -> None:
    client = MockLLMClient()

    result = await client.generate_structured_slides(
        SlideGenerationRequest(
            theme="営業進捗の振り返り",
            objective="現状と打ち手を簡潔に共有する",
            audience="営業部長",
            slide_count=4,
        )
    )

    assert result.deck_title == "営業進捗の振り返り"
    assert len(result.slides) == 4
    assert result.slides[0].type == "title"
    assert result.slides[-1].type == "summary"


def test_normalize_presentation_payload_repairs_common_slide_shape_errors() -> None:
    normalized = normalize_presentation_payload(
        {
            "title": "営業進捗の振り返り",
            "slides": [
                {
                    "id": 10,
                    "type": "title",
                    "title": "営業進捗のレビュー",
                    "bullets": [],
                },
                {
                    "id": 20,
                    "type": "bulleted_list",
                    "bullets": ["現状の営業概観", "次の打ち手", "数字は仮置きでよい"],
                },
                {
                    "id": 30,
                    "type": "summary_slide",
                    "title": "結論",
                    "bullets": ["重点対応を整理する"],
                },
            ],
        }
    )

    assert normalized["deck_title"] == "営業進捗の振り返り"
    slides = normalized["slides"]
    assert slides[0]["id"] == "slide-10"
    assert slides[1]["id"] == "slide-20"
    assert slides[1]["type"] == "content"
    assert slides[1]["layout"] == "layout2"
    assert slides[2]["type"] == "summary"


def test_normalize_presentation_payload_makes_summary_action_oriented() -> None:
    normalized = normalize_presentation_payload(
        {
            "deck_title": "案件整理",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "案件整理",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "重点案件の停滞が課題",
                    "bullets": ["重点案件", "重点案件", "その他"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "案件優先度の再整理が必要",
                    "bullets": ["確認中"],
                    "layout": "layout4",
                },
            ],
        }
    )

    assert normalized["slides"][1]["bullets"] == ["重点案件を整理する"]
    assert normalized["slides"][2]["bullets"][0] == "重点案件を整理する"


def test_normalize_presentation_payload_selects_layout3_for_action_content() -> None:
    normalized = normalize_presentation_payload(
        {
            "deck_title": "営業進捗",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "営業進捗",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "対応方針を整理する",
                    "bullets": ["重点案件へ工数を再配分する", "週次レビューを固定化する"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "次の打ち手を決める",
                    "bullets": ["優先対応を決める"],
                    "layout": "layout4",
                },
            ],
        }
    )

    assert normalized["slides"][1]["layout"] == "layout3"


def test_normalize_presentation_payload_keeps_layout2_for_two_cause_bullets() -> None:
    normalized = normalize_presentation_payload(
        {
            "deck_title": "営業進捗",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "営業進捗",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "主要案件の停滞要因",
                    "bullets": ["顧客ニーズの深掘り不足", "競合との差別化が不明確"],
                    "layout": "layout3",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "今後の優先対応と決定事項",
                    "bullets": ["確認中"],
                    "layout": "layout4",
                },
            ],
        }
    )

    assert normalized["slides"][1]["layout"] == "layout2"
    assert normalized["slides"][2]["bullets"] == [
        "顧客ニーズの深掘りを強化する",
        "競合との差別化を明確化する",
    ]


def test_generation_service_from_settings_supports_gemini_provider() -> None:
    service = GenerationService.from_settings(
        Settings(
            LLM_PROVIDER="gemini",
            GEMINI_API_KEY="test-key",
            GEMINI_MODEL="gemini-2.5-flash",
        )
    )

    assert service.provider.is_configured() is True
