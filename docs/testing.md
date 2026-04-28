# Testing

The suite has three layers.

1. Router tests use `httpx.AsyncClient` with `ASGITransport` and a real SQLite
   database. OpenRouter HTTP is mocked with `respx`.
2. `tests/test_user_journey.py` covers register → login → chat → history in one
   in-process flow.
3. `scripts/smoke.py` runs against a live container stack and acts as the
   reviewer smoke test.

Use the mock provider in automated tests. Never call OpenRouter live from CI.

