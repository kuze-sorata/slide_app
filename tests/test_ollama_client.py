import httpx
import pytest

from app.llm.ollama import OllamaClient
from app.utils.config import Settings


@pytest.mark.asyncio
async def test_ollama_client_raises_read_timeout_with_context(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(
        base_url="http://127.0.0.1:11434",
        model="phi3:mini",
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
    )

    class DummyAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        async def post(self, url: str, json: dict[str, object]) -> httpx.Response:
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    with pytest.raises(RuntimeError) as exc_info:
        await client.generate_text("prompt")

    message = str(exc_info.value)
    assert "url=http://127.0.0.1:11434/api/generate" in message
    assert "model=phi3:mini" in message
    assert "connect=10.0" in message
    assert isinstance(exc_info.value.__cause__, httpx.ReadTimeout)


def test_settings_read_ollama_timeout_overrides() -> None:
    settings = Settings(
        OLLAMA_CONNECT_TIMEOUT=11.0,
        OLLAMA_READ_TIMEOUT=90.0,
        OLLAMA_WRITE_TIMEOUT=22.0,
        OLLAMA_POOL_TIMEOUT=9.0,
    )

    assert settings.ollama_connect_timeout == 11.0
    assert settings.ollama_read_timeout == 90.0
    assert settings.ollama_write_timeout == 22.0
    assert settings.ollama_pool_timeout == 9.0


@pytest.mark.asyncio
async def test_ollama_client_ping_returns_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(
        base_url="http://127.0.0.1:11434",
        model="phi3:mini",
    )

    class DummyAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        async def post(self, url: str, json: dict[str, object]) -> httpx.Response:
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={"response": '{"ok": true}', "done": True},
            )

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    result = await client.ping()

    assert result["base_url"] == "http://127.0.0.1:11434"
    assert result["model"] == "phi3:mini"
    assert '{"ok": true}' in result["response_preview"]
