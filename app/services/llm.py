"""LLM provider boundary."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Raised when a provider request fails."""


class LLMClient(ABC):
    """Async streaming interface for chat providers."""

    name: str
    model: str

    @abstractmethod
    async def stream(self, messages: Sequence[dict[str, str]]) -> AsyncIterator[str]:
        """Yield text chunks for a streaming assistant response."""


class MockClient(LLMClient):
    """Deterministic local provider used when no OpenRouter key is configured."""

    name = "mock"
    model = "mock"

    async def stream(self, messages: Sequence[dict[str, str]]) -> AsyncIterator[str]:
        chunks = [
            "The ",
            "quick ",
            "brown ",
            "fox ",
            "jumps ",
            "over ",
            "the ",
            "lazy ",
            "dog. ",
            "This ",
            "is ",
            "a ",
            "longer ",
            "response ",
            "with ",
            "multiple ",
            "chunks ",
            "that ",
            "streams ",
            "gradually. ",
            "Each ",
            "piece ",
            "arrives ",
            "with ",
            "a ",
            "realistic ",
            "200ms ",
            "delay ",
            "to ",
            "simulate ",
            "real ",
            "LLM ",
            "responses.",
        ]
        for chunk in chunks:
            await asyncio.sleep(0.2)
            yield chunk


class OpenRouterClient(LLMClient):
    """OpenRouter chat completion streaming client."""

    name = "openrouter"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def stream(self, messages: Sequence[dict[str, str]]) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "messages": list(messages), "stream": True}
        timeout = httpx.Timeout(30.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise ProviderError(
                        "OpenRouter returned "
                        f"{response.status_code}: {body.decode('utf-8', 'ignore')}"
                    )

                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = payload.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content is None:
                        continue
                    yield content


def get_llm_client(settings: Settings) -> LLMClient:
    """Return the configured provider implementation."""
    if settings.openrouter_api_key:
        return OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
        )
    return MockClient()
