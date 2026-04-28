"""Full end-to-end user journey test."""


async def test_full_user_journey(async_client):
    payload = {"email": "journey@example.com", "password": "password123"}
    response = await async_client.post("/auth/register", json=payload)
    assert response.status_code == 201

    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    events = []
    async with async_client.stream(
        "POST",
        "/chat",
        json={"message": "Hello", "conversation_id": None},
        headers=headers,
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                events.append(line)

    assert "event: token" in events
    assert "event: done" in events

    response = await async_client.get("/chat/history", headers=headers)
    conversations = response.json()["conversations"]
    assert len(conversations) == 1
    messages = conversations[0]["messages"]
    assert len(messages) == 2
    assert [message["role"] for message in messages] == ["user", "assistant"]
