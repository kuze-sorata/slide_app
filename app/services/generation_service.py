import asyncio
import json
import logging
from time import perf_counter

import httpx
from pydantic import ValidationError

from app.llm.api import ApiHostedLLMClient
from app.llm.base import LLMProvider
from app.llm.lmstudio import LMStudioClient
from app.llm.ollama import OllamaClient
from app.llm.prompts import (
    build_simple_slide_generation_prompt,
    build_slide_generation_prompt,
)
from app.models.schema import Presentation, SlideGenerationRequest
from app.utils.config import Settings
from app.utils.json_extract import extract_json_object
from app.utils.presentation_normalizer import normalize_presentation_payload


logger = logging.getLogger(__name__)


class GenerationError(Exception):
    pass


class MockLLMClient(LLMProvider):
    async def generate_text(self, prompt: str) -> str:
        raise RuntimeError("MockLLMClient.generate_text should not be called directly")

    async def generate_structured_slides(
        self,
        input_data: SlideGenerationRequest,
    ) -> Presentation:
        slide_count = input_data.slide_count
        deck_title = input_data.theme.strip() or "資料タイトル"
        slides: list[dict[str, object]] = [
            {
                "id": "slide-1",
                "type": "title",
                "title": deck_title[:30],
                "bullets": [f"{input_data.audience}向け共有"[:40]],
                "layout": "layout1",
            }
        ]

        middle_templates = [
            ("agenda", "共有したい論点", ["背景", "課題", "打ち手"], "layout2"),
            ("content", "現状の課題を整理する", ["現状を短く整理", "重点課題を明確化"], "layout2"),
            ("content", "対応方針をそろえる", ["優先施策を決める", "担当と期限を置く"], "layout3"),
            ("content", "期待効果を確認する", ["意思決定を前進させる", "次回確認点をそろえる"], "layout2"),
        ]

        for index in range(2, slide_count):
            template = middle_templates[min(index - 2, len(middle_templates) - 1)]
            slide_type, title, bullets, layout = template
            slides.append(
                {
                    "id": f"slide-{index}",
                    "type": slide_type,
                    "title": title,
                    "bullets": bullets[:4],
                    "layout": layout,
                }
            )

        slides.append(
            {
                "id": f"slide-{slide_count}",
                "type": "summary",
                "title": "次の打ち手を決める",
                "bullets": [
                    f"{input_data.objective[:36]}",
                    "優先対応を明確にする",
                ],
                "layout": "layout4",
            }
        )

        normalized = normalize_presentation_payload(
            {
                "deck_title": deck_title,
                "slides": slides,
            }
        )
        return Presentation.model_validate(normalized)


class GenerationService:
    def __init__(
        self,
        provider: LLMProvider,
        generation_timeout_seconds: float = 120.0,
    ) -> None:
        self.provider = provider
        self.generation_timeout_seconds = generation_timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "GenerationService":
        if settings.mock_generation:
            logger.info("Using mock generation mode instead of remote provider.")
            return cls(provider=MockLLMClient())

        provider_name = settings.llm_provider.lower()
        if provider_name == "gemini":
            provider: LLMProvider = ApiHostedLLMClient(
                api_key=settings.gemini_api_key or settings.llm_api_key or "",
                model=settings.gemini_model,
                base_url=settings.gemini_base_url,
                timeout_ms=settings.llm_timeout_ms,
                max_retries=settings.llm_max_retries,
            )
        elif provider_name in {"api", "openai", "openai_compatible"}:
            provider: LLMProvider = ApiHostedLLMClient(
                api_key=settings.llm_api_key or "",
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                timeout_ms=settings.llm_timeout_ms,
                max_retries=settings.llm_max_retries,
            )
        elif provider_name == "ollama":
            provider = OllamaClient(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                timeout=httpx.Timeout(
                    connect=settings.ollama_connect_timeout,
                    read=settings.ollama_read_timeout,
                    write=settings.ollama_write_timeout,
                    pool=settings.ollama_pool_timeout,
                ),
                timeout_seconds=settings.llm_timeout_seconds,
            )
        elif provider_name == "lmstudio":
            provider = LMStudioClient(
                base_url=settings.lmstudio_base_url,
                model=settings.lmstudio_model,
                timeout_seconds=settings.llm_timeout_seconds,
            )
        else:
            raise GenerationError(f"Unsupported LLM provider: {settings.llm_provider}")

        return cls(
            provider=provider,
            generation_timeout_seconds=settings.generation_timeout_seconds,
        )

    async def generate(self, payload: SlideGenerationRequest) -> Presentation:
        provider_name = self.provider.__class__.__name__
        logger.info(
            "Starting slide generation. provider=%s slide_count=%s debug_mode=%s theme=%s",
            provider_name,
            payload.slide_count,
            payload.debug_mode,
            truncate_for_log(payload.theme, 80),
        )

        if isinstance(self.provider, MockLLMClient):
            return await self.provider.generate_structured_slides(payload)

        if not self.provider.is_configured():
            raise GenerationError("LLM provider is not configured")

        prompt = select_prompt(payload)
        try:
            initial_text = await self._generate_text_with_timeout(
                prompt,
                stage="initial",
                payload=payload,
                provider_name=provider_name,
            )
        except Exception as exc:  # noqa: BLE001
            raise map_generation_exception(
                exc,
                self.generation_timeout_seconds,
                stage="initial",
            ) from exc

        try:
            return self._validate_presentation_text(initial_text)
        except GenerationError as first_error:
            logger.warning(
                "Initial generation parse failed. provider=%s slide_count=%s response_chars=%s error=%s",
                provider_name,
                payload.slide_count,
                len(initial_text),
                first_error,
            )
            try:
                retry_text = await self._generate_text_with_timeout(
                    retry_prompt(payload),
                    stage="retry",
                    payload=payload,
                    provider_name=provider_name,
                )
                return self._validate_presentation_text(retry_text)
            except Exception as second_error:  # noqa: BLE001
                logger.exception("Retry generation failed. provider=%s", provider_name)
                mapped_error = map_generation_exception(
                    second_error,
                    self.generation_timeout_seconds,
                    stage="retry",
                )
                raise GenerationError(
                    "LLM response could not be converted into valid slide JSON. "
                    f"first_error={first_error}; retry_error={mapped_error}"
                ) from second_error

    async def _generate_text_with_timeout(
        self,
        prompt: str,
        *,
        stage: str,
        payload: SlideGenerationRequest,
        provider_name: str,
    ) -> str:
        logger.info(
            "Sending %s prompt to provider. provider=%s prompt_chars=%s prompt_preview=%s",
            stage,
            provider_name,
            len(prompt),
            truncate_for_log(prompt, 220),
        )
        started_at = perf_counter()
        try:
            async with asyncio.timeout(self.generation_timeout_seconds):
                text = await self.provider.generate_text(prompt)
        except Exception:
            logger.exception(
                "%s generation request failed. provider=%s slide_count=%s debug_mode=%s",
                stage.capitalize(),
                provider_name,
                payload.slide_count,
                payload.debug_mode,
            )
            raise

        logger.info(
            "Received %s provider response. provider=%s elapsed=%.2fs response_chars=%s response_preview=%s",
            stage,
            provider_name,
            perf_counter() - started_at,
            len(text),
            truncate_for_log(text, 220),
        )
        return text

    def _validate_presentation_text(self, raw_text: str) -> Presentation:
        try:
            extracted = extract_json_object(raw_text)
            decoded = json.loads(extracted)
            normalized = normalize_presentation_payload(decoded)
            return Presentation.model_validate(normalized)
        except (ValueError, json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Presentation validation failed: %s", exc)
            raise GenerationError(str(exc)) from exc


def retry_prompt(payload: SlideGenerationRequest) -> str:
    return (
        f"{select_prompt(payload)}\n"
        "The previous response was invalid. Return only one valid JSON object that matches the schema."
    )


def select_prompt(payload: SlideGenerationRequest) -> str:
    if payload.debug_mode:
        return build_simple_slide_generation_prompt(payload)
    return build_slide_generation_prompt(payload)


def truncate_for_log(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def map_generation_exception(
    exc: Exception,
    timeout_seconds: float,
    *,
    stage: str,
) -> GenerationError:
    if isinstance(exc, TimeoutError):
        return GenerationError(
            f"LLM request timed out during {stage} generation after {timeout_seconds:.0f}s. "
            "Retry later or reduce slide_count."
        )
    return GenerationError(str(exc))
