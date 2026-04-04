import logging
from typing import Any

import httpx

from app.llm.base import LLMProvider
from app.models.schema import Presentation


logger = logging.getLogger(__name__)


class ApiHostedLLMClient(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_ms: int = 60000,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_ms / 1000)
        self.max_retries = max_retries

    def is_configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    async def generate_text(self, prompt: str) -> str:
        if not self.is_configured():
            raise RuntimeError("API provider is not configured. Check LLM_API_KEY, LLM_MODEL, and LLM_BASE_URL.")

        payload = self._build_payload(prompt, use_structured_output=True)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        last_error: Exception | None = None
        max_attempts = self.max_retries + 1
        attempt = 1
        while attempt <= max_attempts:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                data = response.json()
                content = self._extract_content(data)
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("API provider returned an empty response")
                return content
            except httpx.TimeoutException as exc:
                last_error = RuntimeError(
                    f"API provider timed out. model={self.model}, base_url={self.base_url}"
                )
                logger.warning("API provider timeout on attempt %s/%s", attempt, self.max_retries + 1)
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if self._should_fallback_to_plain_json(exc.response, payload):
                    logger.info(
                        "API provider does not support structured output. Retrying without response_format."
                    )
                    payload = self._build_payload(prompt, use_structured_output=False)
                    max_attempts += 1
                    attempt += 1
                    continue
                if status_code == 429:
                    last_error = RuntimeError("API provider rate limit exceeded")
                elif 500 <= status_code < 600:
                    last_error = RuntimeError(
                        f"API provider temporary failure. status_code={status_code}"
                    )
                else:
                    message = exc.response.text.strip()
                    last_error = RuntimeError(
                        f"API provider request failed. status_code={status_code}. details={message}"
                    )
                    break
                logger.warning(
                    "API provider HTTP error on attempt %s/%s status=%s",
                    attempt,
                    self.max_retries + 1,
                    status_code,
                )
            except httpx.HTTPError as exc:
                last_error = RuntimeError(
                    f"API provider request failed. model={self.model}, base_url={self.base_url}"
                )
                logger.warning("API provider transport error on attempt %s/%s", attempt, self.max_retries + 1)
            except ValueError as exc:
                last_error = RuntimeError("API provider returned malformed JSON metadata")
                break
            attempt += 1

        if last_error is not None:
            raise last_error
        raise RuntimeError("API provider request failed")

    async def health_check(self) -> dict[str, object]:
        return {
            "ok": self.is_configured(),
            "provider": "api",
            "base_url": self.base_url,
            "model": self.model,
        }

    def _build_payload(self, prompt: str, *, use_structured_output: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a slide generation engine. "
                        "Return JSON only. Do not include markdown, explanations, or comments."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        }
        if use_structured_output:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "slide_deck",
                    "schema": Presentation.model_json_schema(),
                },
            }
        return payload

    def _extract_content(self, data: dict[str, Any]) -> str:
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            return "".join(text_parts)
        return content

    def _should_fallback_to_plain_json(
        self,
        response: httpx.Response,
        payload: dict[str, Any],
    ) -> bool:
        if "response_format" not in payload:
            return False
        if response.status_code not in {400, 404, 415, 422}:
            return False
        body = response.text.lower()
        keywords = (
            "response_format",
            "json_schema",
            "unsupported",
            "not supported",
            "unknown field",
            "invalid parameter",
        )
        return any(keyword in body for keyword in keywords)
