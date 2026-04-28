"""Tests for the LLM provider boundary."""

from time import monotonic

import httpx

from app.config import Settings
from app.services.llm import MockClient, OpenRouterClient, get_llm_client


async def test_mock_client_streams_with_delay():
    client = MockClient()
    start = monotonic()
    chunks = []
    async for chunk in client.stream([{"role": "user", "content": "hello"}]):
        chunks.append(chunk)
    elapsed = monotonic() - start
    assert chunks == ["Hello", " from", " the", " mock", " provider."]
    assert elapsed >= 0.8


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
