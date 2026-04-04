import httpx
import pytest

from app.llm.api import ApiHostedLLMClient


@pytest.mark.asyncio
async def test_api_provider_returns_message_content(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = ApiHostedLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://api.example.com/v1",
    )

    class DummyAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        async def post(
            self,
            url: str,
            json: dict[str, object],
            headers: dict[str, str],
        ) -> httpx.Response:
            assert url == "https://api.example.com/v1/chat/completions"
            assert headers["Authorization"] == "Bearer test-key"
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"deck_title":"営業進捗","slides":[]}',
                            }
                        }
                    ]
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    result = await provider.generate_text("prompt")

    assert '"deck_title":"営業進捗"' in result


@pytest.mark.asyncio
async def test_api_provider_maps_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = ApiHostedLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://api.example.com/v1",
        max_retries=0,
    )

    class DummyAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        async def post(
            self,
            url: str,
            json: dict[str, object],
            headers: dict[str, str],
        ) -> httpx.Response:
            response = httpx.Response(429, request=httpx.Request("POST", url), text="rate limited")
            raise httpx.HTTPStatusError("rate limited", request=response.request, response=response)

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    with pytest.raises(RuntimeError, match="rate limit"):
        await provider.generate_text("prompt")
