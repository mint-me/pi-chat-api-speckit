"""Tests for the streaming chat endpoint."""

from collections.abc import AsyncIterator

from app.services.llm import ProviderError


async def _register_and_login(async_client, email: str) -> str:
    payload = {"email": email, "password": "password123"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/login", json=payload)
    return response.json()["access_token"]


async def test_chat_requires_auth(async_client):
    response = await async_client.post("/chat", json={"message": "hello", "conversation_id": None})
    assert response.status_code == 401


async def test_chat_streams_and_persists(async_client):
    token = await _register_and_login(async_client, "chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    events = []
    async with async_client.stream(
        "POST",
        "/chat",
        json={"message": "Say hi briefly.", "conversation_id": None},
        headers=headers,
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                events.append(line)

    assert "event: token" in events
    assert "event: done" in events

    history = await async_client.get("/chat/history", headers=headers)
    body = history.json()
    assert len(body["conversations"]) == 1
    messages = body["conversations"][0]["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]


async def test_chat_provider_failure_emits_error_and_does_not_persist_assistant(
    async_client, monkeypatch
):
    token = await _register_and_login(async_client, "fail@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    class FailingClient:
        name = "mock"
        model = "mock"

        async def stream(self, messages) -> AsyncIterator[str]:
            if False:
                yield ""
            raise ProviderError("boom")

    monkeypatch.setattr("app.routers.chat.get_llm_client", lambda settings: FailingClient())

    events = []
    async with async_client.stream(
        "POST",
        "/chat",
        json={"message": "Trigger failure.", "conversation_id": None},
        headers=headers,
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                events.append(line)

    assert "event: error" in events

    history = await async_client.get("/chat/history", headers=headers)
    messages = history.json()["conversations"][0]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
