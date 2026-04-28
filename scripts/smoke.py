"""End-to-end smoke test against a running pi-chat-api stack."""

import argparse
import asyncio
import uuid

import httpx


async def _login_existing_user(
    client: httpx.AsyncClient, email: str, password: str
) -> tuple[dict[str, str], str]:
    response = await client.post("/auth/login", json={"email": email, "password": password})
    response.raise_for_status()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


async def _register_and_login_random_user(client: httpx.AsyncClient) -> tuple[dict[str, str], str]:
    email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    return await _login_existing_user(client, email, password)


async def main(base_url: str, show_stream: bool = False, use_demo_user: bool = False) -> int:
    """Run a live HTTP smoke test."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        response = await client.get("/health")
        response.raise_for_status()

        if use_demo_user:
            headers, email = await _login_existing_user(
                client, email="demo@example.com", password="password123"
            )
        else:
            headers, email = await _register_and_login_random_user(client)

        saw_token = False
        saw_done = False
        saw_error = False
        collected_chunks: list[str] = []
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
                if line.startswith("data: ") and saw_token:
                    chunk = line.removeprefix("data: ").strip()
                    collected_chunks.append(chunk)
                if line == "event: done":
                    saw_done = True
                if line == "event: error":
                    saw_error = True
                if show_stream and line:
                    print(line)

        if not (saw_token and saw_done):
            raise RuntimeError("missing SSE events")

        response = await client.get("/chat/history", headers=headers)
        response.raise_for_status()
        if not response.json()["conversations"]:
            raise RuntimeError("history is empty")

    if show_stream and collected_chunks:
        print(f"stream_chunks={len(collected_chunks)}")
    if saw_error:
        raise RuntimeError("provider stream returned error event")

    print(f"OK - health, register, login, chat, history passed for {email}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run live smoke test against running API")
    parser.add_argument("base_url", nargs="?", default="http://localhost:8000")
    parser.add_argument(
        "--show-stream",
        action="store_true",
        help="Print SSE lines from /chat for debugging",
    )
    parser.add_argument(
        "--use-demo-user",
        action="store_true",
        help="Use demo@example.com/password123 instead of creating a random account",
    )
    args = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            main(
                args.base_url,
                show_stream=args.show_stream,
                use_demo_user=args.use_demo_user,
            )
        )
    )
