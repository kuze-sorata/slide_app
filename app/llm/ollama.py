import logging

import httpx

from app.llm.base import LocalLLMClient
from app.models.schema import Presentation


logger = logging.getLogger(__name__)


def truncate_for_log(value: str, limit: int = 160) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


class OllamaClient(LocalLLMClient):
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: httpx.Timeout | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout or httpx.Timeout(timeout_seconds)

    async def generate_text(self, prompt: str) -> str:
        return await self._post_generate(prompt)

    async def ping(self, prompt: str = 'JSONだけ返してください。{"ok": true}') -> dict[str, object]:
        text = await self._post_generate(prompt)
        return {
            "base_url": self.base_url,
            "model": self.model,
            "response_preview": truncate_for_log(text, 240),
        }

    async def _post_generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": Presentation.model_json_schema(),
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 256,
            },
        }
        try:
            logger.info(
                "Sending Ollama generate request. url=%s model=%s timeout=%s prompt_chars=%s prompt_preview=%s",
                url,
                self.model,
                self.timeout,
                len(prompt),
                truncate_for_log(prompt),
            )
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                logger.info(
                    "Received Ollama response. url=%s model=%s status_code=%s",
                    url,
                    self.model,
                    response.status_code,
                )
                response.raise_for_status()
        except httpx.ReadTimeout as exc:
            raise RuntimeError(
                "Ollama request timed out while waiting for model output. "
                f"url={url}, model={self.model}, timeout={self.timeout}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Ollama request failed. "
                f"url={url}, model={self.model}, timeout={self.timeout}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Ollama returned a non-JSON response")

        if data.get("error"):
            raise RuntimeError(
                f"Ollama returned an error for model={self.model}: {data['error']}"
            )

        text = data.get("response", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(
                f"Ollama returned an empty response for model={self.model}. payload={data}"
            )
        return text
