"""Tests for conversation history and ownership scoping."""


async def _register_and_login(async_client, email: str) -> str:
    payload = {"email": email, "password": "password123"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/login", json=payload)
    return response.json()["access_token"]


async def test_empty_history_returns_empty_list(async_client):
    token = await _register_and_login(async_client, "empty@example.com")
    response = await async_client.get("/chat/history", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"conversations": []}


async def test_history_orders_newest_first(async_client):
    token = await _register_and_login(async_client, "order@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    await async_client.post(
        "/chat", json={"message": "first", "conversation_id": None}, headers=headers
    )
    await async_client.post(
        "/chat", json={"message": "second", "conversation_id": None}, headers=headers
    )

    response = await async_client.get("/chat/history", headers=headers)
    assert response.status_code == 200
    conversations = response.json()["conversations"]
    assert len(conversations) == 2
    assert conversations[0]["updated_at"] >= conversations[1]["updated_at"]
    assert conversations[0]["messages"][0]["role"] == "user"
    assert conversations[0]["messages"][1]["role"] == "assistant"


async def test_cross_user_conversation_returns_404(async_client):
    token1 = await _register_and_login(async_client, "user1@example.com")
    token2 = await _register_and_login(async_client, "user2@example.com")
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    await async_client.post(
        "/chat",
        json={"message": "owned by user one", "conversation_id": None},
        headers=headers1,
    )
    history = await async_client.get("/chat/history", headers=headers1)
    conversation_id = history.json()["conversations"][0]["id"]

    response = await async_client.get(
        "/chat/history",
        params={"conversation_id": conversation_id},
        headers=headers2,
    )
    assert response.status_code == 404
