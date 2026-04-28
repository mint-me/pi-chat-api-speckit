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

    def __init__(
        self,
        message: str,
        *,
        code: str = "provider_unavailable",
        public_detail: str = "provider unavailable",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.public_detail = public_detail
        self.status_code = status_code


def _provider_error_for_status(status_code: int) -> ProviderError:
    if status_code == 429:
        return ProviderError(
            "OpenRouter rate limited the request",
            code="provider_rate_limited",
            public_detail="provider rate limited",
            status_code=status_code,
        )
    if status_code in {401, 403}:
        return ProviderError(
            "OpenRouter rejected the configured credentials",
            code="provider_auth_failed",
            public_detail="provider authentication failed",
            status_code=status_code,
        )
    if status_code == 404:
        return ProviderError(
            "OpenRouter model or route was not found",
            code="provider_model_unavailable",
            public_detail="provider model unavailable",
            status_code=status_code,
        )
    if status_code >= 500:
        return ProviderError(
            "OpenRouter is temporarily unavailable",
            code="provider_unavailable",
            public_detail="provider temporarily unavailable",
            status_code=status_code,
        )
    return ProviderError(
        "OpenRouter rejected the request",
        code="provider_request_failed",
        public_detail="provider request failed",
        status_code=status_code,
    )


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
                    await response.aread()
                    raise _provider_error_for_status(response.status_code)

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
