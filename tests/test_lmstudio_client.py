import pytest

from app.llm.lmstudio import LMStudioClient
from app.models.schema import SlideGenerationRequest
from app.services.generation_service import GenerationService


class RetryingLMStudioClient(LMStudioClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://localhost:1234", model="local-model")
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
async def test_generation_service_retries_for_lmstudio_invalid_json() -> None:
    service = GenerationService(provider=RetryingLMStudioClient())
    payload = SlideGenerationRequest(
        theme="営業進捗の振り返り",
        objective="現状と打ち手を共有する",
        audience="営業部長",
        slide_count=3,
    )

    result = await service.generate(payload)

    assert result.slides[-1].type == "summary"
    assert service.provider.prompts[1].endswith("Return only one valid JSON object that matches the schema.")
