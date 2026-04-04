import httpx

from app.llm.base import LocalLLMClient
from app.models.schema import Presentation


class LMStudioClient(LocalLLMClient):
    def __init__(
        self,
        base_url: str,
        model: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds)

    async def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.model or "local-model",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a slide generation engine. "
                        "Return JSON only. Do not include markdown or explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "slide_deck",
                    "schema": Presentation.model_json_schema(),
                },
            },
        }
        url = f"{self.base_url}/v1/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"LM Studio request failed. base_url={self.base_url}, model={self.model}"
            ) from exc

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LM Studio returned an empty response")
        return content
