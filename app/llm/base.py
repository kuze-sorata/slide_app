from abc import ABC, abstractmethod

from app.models.schema import Presentation, SlideGenerationRequest


class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    async def generate_structured_slides(
        self,
        input_data: SlideGenerationRequest,
    ) -> Presentation:
        raise NotImplementedError

    async def health_check(self) -> dict[str, object]:
        return {"ok": True, "provider": self.__class__.__name__}

    def is_configured(self) -> bool:
        return True


LocalLLMClient = LLMProvider
