"""Tests for the LLM provider boundary."""

import httpx
import pytest

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


@pytest.mark.parametrize(
    ("status_code", "expected_code", "expected_detail"),
    [
        (429, "provider_rate_limited", "provider rate limited"),
        (401, "provider_auth_failed", "provider authentication failed"),
        (403, "provider_auth_failed", "provider authentication failed"),
        (404, "provider_model_unavailable", "provider model unavailable"),
        (500, "provider_unavailable", "provider temporarily unavailable"),
        (400, "provider_request_failed", "provider request failed"),
    ],
)
async def test_openrouter_client_maps_http_errors_to_provider_errors(
    mocked_openrouter,
    status_code,
    expected_code,
    expected_detail,
):
    mocked_openrouter.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(status_code, json={"error": "provider error"})
    )

    client = OpenRouterClient(
        api_key="secret",
        model="model-x",
        base_url="https://openrouter.ai/api/v1",
    )

    with pytest.raises(ProviderError) as exc_info:
        async for _ in client.stream([{"role": "user", "content": "hello"}]):
            pass

    assert exc_info.value.code == expected_code
    assert exc_info.value.public_detail == expected_detail
    assert exc_info.value.status_code == status_code
