"""Tests for the LLM provider boundary."""

import httpx

from app.config import Settings
from app.services.llm import MockClient, OpenRouterClient, ProviderError, get_llm_client


async def test_mock_client_streams_deterministic_chunks_with_delay(monkeypatch):
    sleeps = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("app.services.llm.asyncio.sleep", fake_sleep)

    client = MockClient()
    chunks = []
    async for chunk in client.stream([{"role": "user", "content": "hello"}]):
        chunks.append(chunk)

    response = "".join(chunks)
    assert len(chunks) > 1
    assert response.startswith("The quick brown fox")
    assert response.endswith("real LLM responses.")
    assert sleeps == [0.2] * len(chunks)


async def test_get_llm_client_uses_mock_without_key():
    client = get_llm_client(Settings(openrouter_api_key=None))
    assert isinstance(client, MockClient)


async def test_openrouter_client_stream_parses_sse(mocked_openrouter):
    response_text = (
        'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    mocked_openrouter.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=response_text)
    )

    client = OpenRouterClient(
        api_key="secret",
        model="model-x",
        base_url="https://openrouter.ai/api/v1",
    )
    chunks = []
    async for chunk in client.stream([{"role": "user", "content": "hello"}]):
        chunks.append(chunk)
    assert chunks == ["Hello", " world"]


async def test_openrouter_client_maps_rate_limit_to_provider_error(mocked_openrouter):
    mocked_openrouter.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "rate limited"})
    )

    client = OpenRouterClient(
        api_key="secret",
        model="model-x",
        base_url="https://openrouter.ai/api/v1",
    )

    try:
        async for _ in client.stream([{"role": "user", "content": "hello"}]):
            pass
    except ProviderError as exc:
        assert exc.code == "provider_rate_limited"
        assert exc.public_detail == "provider rate limited"
        assert exc.status_code == 429
    else:
        raise AssertionError("expected ProviderError")
