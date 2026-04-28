"""End-to-end smoke test against a running pi-chat-api stack."""

import asyncio
import sys
import uuid

import httpx


async def main(base_url: str) -> int:
    """Run a live HTTP smoke test."""
    email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        response = await client.get("/health")
        response.raise_for_status()

        response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        response.raise_for_status()

        response = await client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        saw_token = False
        saw_done = False
        async with client.stream(
            "POST",
            "/chat",
            json={"message": "Say hi briefly.", "conversation_id": None},
            headers=headers,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if line == "event: token":
                    saw_token = True
                if line == "event: done":
                    saw_done = True

        if not (saw_token and saw_done):
            raise RuntimeError("missing SSE events")

        response = await client.get("/chat/history", headers=headers)
        response.raise_for_status()
        if not response.json()["conversations"]:
            raise RuntimeError("history is empty")

    print(f"OK - health, register, login, chat, history passed for {email}")
    return 0


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    raise SystemExit(asyncio.run(main(base_url)))
