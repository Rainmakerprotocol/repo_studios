---
title: repo Standards — Chainlit UI and LLM Integration
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@docs-owners"]
status: approved
version: 1.0.1
updated_at: 2025-09-28
tags: [chainlit, ui, async, standards]
related_files:
    - ./repo_standards_project.md
    - ./repo_standards_markdown.md
    - ./repo_standards_python.md
---

This guide defines standards for building Chainlit-based UI for Jarvis2/Rainmaker.
It focuses on async safety, message semantics, inputs, state, error handling,
observability, and testability.

* Scope: Chainlit apps, handlers, UI components, and integration with backend APIs/metrics.
* Goals: Predictable UX, resilient async flows, and minimal diff churn.

## Project structure

* Provide a `main.py` entrypoint.
* Organize helpers under `src/` or `modules/` (for example, `src/tools/`, `modules/prompts/`).
* Include `.chainlit/` with:
  * `config.toml`
  * `readme.md`
  * `theme.css` (optional)

Note the Chainlit version in `requirements-dev.txt` and keep it pinned to avoid
UI drift.

## Lifecycle hooks (required)

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    # initialize session-scoped state here
    cl.user_session.set("ctx", {"started": True})

@cl.on_message
async def on_message(message: cl.Message):
    # validate input and route
    text = (message.content or "").strip()
    if not text:
        await cl.Message("Please type a message.", author="system").send()
        return
    # ... business logic ...
```

Optional hooks (use when needed): `@cl.on_stop`, `@cl.on_chat_resume`, `@cl.on_chat_end`.

Requirements:

* Use `async def` and `await` long-running calls (LLM, DB, HTTP).
* Wrap handlers in `try/except` and surface user-friendly errors.
* Prefer `cl.error()` for developer diagnostics during dev.

## Async patterns and cancellation

* Apply timeouts around I/O and LLM calls to keep the UI responsive.
* Offload CPU-bound or blocking work to a thread executor.
* Respect cancellation: check for task cancellation and fail fast.

Example:

```python
import asyncio

async def call_with_timeout(coro, seconds: float):
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        return {"error": "timeout"}
```

## Message semantics: create, update, stream

* Use explicit `id` when you plan to update a message.
* Prefer a single message that updates from "working" → final content.
* Use streaming for long outputs; otherwise update in small increments.

Canonical update pattern:

```python
msg = cl.Message(content="Working…", author="ai", id="work-1")
await msg.send()

# do work
result = await call_with_timeout(llm("..."), 30)
if isinstance(result, dict) and result.get("error"):
    await msg.update(content=f"Error: {result['error']}")
else:
    await msg.update(content=str(result))
```

Streaming pattern:

```python
msg = cl.Message(content="", author="ai", id="stream-1")
await msg.send()
for chunk in generate_chunks():
    await msg.update(content=(msg.content + chunk))
```

## Inputs and actions

* Validate and sanitize user inputs.
* Prefer Chainlit inputs over `input()`.
* Use stable ids for actions; debounce rapid clicks.

Example `ActionButton`:

```python
from chainlit import Action, Message

btn = Action(name="retry", value="retry", label="Retry", description="Run again")
await Message("Ready.", actions=[btn]).send()
```

Example `Select`:

```python
from chainlit import Message, Select

sel = Select(
    id="model",
    label="Choose model",
    values=["gpt-4o", "gpt-4o-mini"],
    initial_index=0,
)
await Message("Select a model", elements=[sel]).send()
```

Uploads:

* Enforce size limits; store to a temp directory; clean up after processing.

## State management

* Use `cl.user_session` for per-session, small state blobs.
* Keys should be namespaced (for example, `ui.*`, `task.*`).
* Avoid storing large objects or cross-session references.

```python
ctx = cl.user_session.get("ctx") or {}
ctx["last_prompt"] = "..."
cl.user_session.set("ctx", ctx)
```

## Error handling and UX

* User-facing errors: `author="system"` or clear labels.
* Internal errors: log via `logging` or `cl.error()` in dev.
* Map backend errors to the unified API error envelope and render consistently.

```python
try:
    data = await api_call()
except Exception as e:  # narrow as appropriate
    await cl.Message(f"Request failed: {e}", author="system").send()
    return
```

## Observability

* Prefer structured logs with context (session id, message id).
* Emit lightweight breadcrumbs for major UI events (start, submit, error).
* When useful, record minimal metrics that align with your exporter (no PII/secrets).

## Testing and testability

* Keep handler logic thin; move business logic to pure helpers and test them directly.
* Mock LLMs/HTTP in tests; assert message sequences and content.
* Avoid global state; reset `cl.user_session` between tests.

Mini example (pseudo):

```python
async def test_on_message_happy_path(monkeypatch):
    async def fake_llm(_: str):
        return "ok"
    monkeypatch.setattr(module, "llm", fake_llm)
    # invoke on_message with a fake cl.Message and assert updates
```

## Security

* Never log secrets; load configuration from environment.
* Validate file uploads; strip executable bits; avoid path traversal.
* Rate-limit expensive flows where possible.

## Alignment with Jarvis2

* Do not reimplement monitoring widgets; use the Monitoring Sidebar and
  readiness endpoints documented in `README.md`.
* Handle API errors using the unified error envelope shape.

See also:

* Memory widget patterns: `docs/ui_memory_widget.md`

## Anchor Health Cross-Link

When adding or renaming H1/H2 headings in this UI standards file, run `make anchor-health` and inspect `.repo_studios/anchor_health/anchor_report_latest.json` for collisions. Favor precise, domain-scoped headings (e.g., "Streaming Message Update Pattern") instead of generic duplicates that may exist in other UI or standards docs.

## Learned fixes (append here)

Common issues and their corrections learned from logs go here.

### Example: Unawaited message send

Issue:

```python
cl.Message("Hello").send()
```

Fix:

```python
await cl.Message("Hello").send()
```
