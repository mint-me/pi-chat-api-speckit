"""End-to-end smoke test against a running pi-chat-api stack."""

import argparse
import asyncio
import json
import sys
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


async def _wait_for_health(client: httpx.AsyncClient) -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            response = await client.get("/health")
            response.raise_for_status()
            return
        except httpx.HTTPError as exc:
            last_error = exc
            await asyncio.sleep(1)
    if last_error is not None:
        raise RuntimeError(f"health check failed: {last_error}") from last_error
    raise RuntimeError("health check failed")


async def main(base_url: str, show_stream: bool = False, use_demo_user: bool = False) -> int:
    """Run a live HTTP smoke test."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        await _wait_for_health(client)

        if use_demo_user:
            headers, email = await _login_existing_user(
                client, email="demo@example.com", password="password123"
            )
        else:
            headers, email = await _register_and_login_random_user(client)

        saw_token = False
        saw_done = False
        saw_error = False
        current_event: str | None = None
        error_detail = "provider stream returned error event"
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
                if line.startswith("event: "):
                    current_event = line.removeprefix("event: ").strip()
                if current_event == "token" and line == "event: token":
                    saw_token = True
                if line.startswith("data: ") and current_event == "token":
                    collected_chunks.append(line.removeprefix("data: ").strip())
                if current_event == "done" and line == "event: done":
                    saw_done = True
                if current_event == "error" and line == "event: error":
                    saw_error = True
                if line.startswith("data: ") and current_event == "error":
                    raw_data = line.removeprefix("data: ").strip()
                    try:
                        payload = json.loads(raw_data)
                    except json.JSONDecodeError:
                        error_detail = raw_data or error_detail
                    else:
                        detail = payload.get("detail")
                        code = payload.get("code")
                        if detail and code:
                            error_detail = f"{detail} ({code})"
                        elif detail:
                            error_detail = detail
                if show_stream and line:
                    print(line)

        if saw_error:
            raise RuntimeError(f"provider stream error: {error_detail}")
        if not (saw_token and saw_done):
            raise RuntimeError("missing SSE events")

        response = await client.get("/chat/history", headers=headers)
        response.raise_for_status()
        history = response.json()
        if not history["conversations"]:
            raise RuntimeError("history is empty")

        provider = "unknown"
        if history["conversations"] and history["conversations"][0]["messages"]:
            last_msg = history["conversations"][0]["messages"][-1]
            if isinstance(last_msg.get("provider_metadata"), dict):
                provider = last_msg["provider_metadata"].get("provider", "unknown")

    if show_stream and collected_chunks:
        print(f"stream_chunks={len(collected_chunks)}")
    print(f"OK - health, register, login, chat, history passed for {email} (provider: {provider})")
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
    try:
        exit_code = asyncio.run(
            main(
                args.base_url,
                show_stream=args.show_stream,
                use_demo_user=args.use_demo_user,
            )
        )
    except (RuntimeError, httpx.HTTPError) as exc:
        print(f"ERROR - {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    raise SystemExit(exit_code)
