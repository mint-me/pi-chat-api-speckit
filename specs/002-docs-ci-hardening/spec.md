# Feature Spec: Docs/CI/Smoke Hardening

## Context

A post-review pass identified clarity and reviewer-usability gaps in docs, CI
env handling, and smoke-test visibility.

## Goals

1. Remove duplicated startup instructions and keep one quickstart source.
2. Improve docs quality for architecture/testing/scaffolding/CI.
3. Clarify deterministic testing strategy for non-deterministic providers.
4. Provide practical answers for reviewer FAQs.
5. Add a clean reset command in Makefile.

## Non-Goals

- No new product features.
- No remote publishing or GitHub repository operations.
- No constitution changes unless strictly required.

## Acceptance Criteria

1. `README.md` points quickstart to `docs/quickstart.md` only.
2. `docs/quickstart.md` contains next-step links.
3. `docs/architecture.md`, `docs/testing.md`, and `docs/scaffolding.md` are
   expanded with actionable operational details.
4. `docs/ci.md` explains secret/env behavior for reviewer-safe CI.
5. A `docs/faq.md` exists for `422`, `script.py.mako`, `__pycache__`,
   `__init__.py`, and smoke visibility.
6. `scripts/smoke.py` can print SSE stream lines when requested.
7. `Makefile` includes a `clean` target.
