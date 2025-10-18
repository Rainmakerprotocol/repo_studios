---
title: Python Engineering Standards
audience:
  - coding_agent
  - human_developer
owners:
    - repo_studios_ai
    - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.1.0
updated: 2025-10-18
summary: >-
  Baseline Python engineering guardrails for Repo Studios automation and human contributors building AI-ready services.
tags:
  - python
  - standards
  - ai-ingestion
legacy_source: .repo_studios_legacy/repo_docs/copilot_standards_python.md
---

# Repo Studios Python Engineering Standards

Audience: Repo Studios automation | Human developers | Partner agents

This standard codifies Repo Studios' Python conventions so agents, CI jobs, and humans ship reliable, agent-compatible code. Treat the guidance as non-optional unless a documented exception exists.

---

## Primary Scope

- Applies to any Python authored or modified within Repo Studios workspaces.
- Covers style, structure, async patterns, logging, configuration, testing, and complexity guardrails.
- Works in tandem with `std-global-code-cleanup.md` and mission parameters when scoping tasks.

---

## Style and Formatting

- Enforce Ruff formatting and linting (`ruff format`, `ruff check --fix`) with repo configuration files.
- Follow PEP 8 plus Repo Studios extensions: 4-space indent, snake_case functions, PascalCase classes, UPPER_CASE constants.
- Keep logical line length to 88 characters unless readability suffers.
- Order module layout as: imports, constants, public classes, public functions, module internals.
- Include a module-level docstring describing purpose and key entry points.

```python
"""tasks/reporting.py: schedule and emit health reports for automation."""
```

---

## Structural Requirements

- Add docstrings to every public class, function, and method documenting intent, arguments, returns, and raised exceptions when applicable.
- Annotate all parameters and return values with explicit type hints; prefer `typing` or `collections.abc` generics (`Iterable`, `Mapping`).
- Use data containers (`dataclasses.dataclass`, `typing.NamedTuple`, or Pydantic models) for structured payloads.
- Separate I/O (filesystem, network, database) from pure computation so agents can mock or reuse logic.
- Avoid circular imports by pushing integration glue to `__main__` or dedicated wiring modules.

---

## Docstring Patterns

```python
class QueueMetrics:
    """Summarize queue depth trends for orchestration alerts."""

    def __init__(self, name: str, depth: int) -> None:
        self.name = name
        self.depth = depth


def render_report(window: str) -> str:
    """Return the serialized health report for the provided ISO8601 window.

    Args:
        window: Timebox in YYYY-MM-DD or YYYY-MM-DDTHH:MM format.

    Returns:
        JSON document string synthesized for downstream ingestion.
    """
```

---

## Async and API Guidance

- Prefer `async def` for FastAPI routes or I/O-heavy orchestrators.
- Wrap blocking calls with `anyio.to_thread.run_sync` or `starlette.concurrency.run_in_threadpool`.
- Validate request payloads using Pydantic models with constrained fields (`Annotated`, validators).
- Inject dependencies with `fastapi.Depends` or lightweight containers; avoid module-level singletons.
- Return JSON-serializable responses or typed models only.

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/inventory", tags=["inventory"])

class InventoryItem(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=0, le=1_000_000)

async def get_service() -> "InventoryService":
    return InventoryService()

@router.post("/", response_model=InventoryItem, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: InventoryItem,
    service: Annotated["InventoryService", Depends(get_service)],
) -> InventoryItem:
    try:
        return await service.create(payload)
    except ValueError as exc:  # narrow exception mapping
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

---

## Logging and Metrics

- Use the standard library `logging` module; never use `print()` in runtime paths.
- Configure module loggers with `logging.getLogger(__name__)` and structured `extra` fields.
- Emit timing or count metrics through the shared metrics facade so backends remain swappable.

```python
import logging
from contextlib import contextmanager
from time import perf_counter

logger = logging.getLogger(__name__)

@contextmanager
def timing(operation: str):
    start = perf_counter()
    try:
        yield
    finally:
        duration_ms = (perf_counter() - start) * 1000
        logger.info("timing", extra={"op": operation, "ms": round(duration_ms, 2)})
```

---

## Configuration and Secrets

- No hardcoded secrets, tokens, or absolute file paths. Use environment variables plus typed settings objects.
- Centralize configuration in one module and cache construction with `functools.lru_cache`.
- Document default values and override mechanisms in README or standards.

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_token: str
    db_path: str = "/var/lib/repo_studios/data.sqlite"
    log_level: str = "INFO"

    class Config:
        env_prefix = "REPO_"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

---

## Error Handling Expectations

- Raise explicit exceptions with contextual messages; catch only what you can remediate.
- In FastAPI, translate domain exceptions to `HTTPException` with precise status codes.
- For background jobs, surface errors through structured logs and metrics so CI can flag regressions.

---

## Database and Performance Hygiene

- Always use parameterized queries and connection pooling helpers.
- Enable SQLite WAL mode when appropriate; keep transactions short and batched.
- Guard long-running operations with timeouts or cancellation hooks.

```python
import sqlite3

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn
```

---

## Testing Expectations

- Provide pytest coverage for every public function or class.
- Include success, edge, and error-path assertions; use fixtures to isolate external dependencies.
- Make tests deterministic, idempotent, and automation-friendly.
- When refactoring, add regression tests capturing the improved behavior.

---

## Complexity Guardrails

- Cyclomatic complexity target: ≤ 12 per function. Anything between 13 and 18 requires reviewer sign-off and a documented remediation plan; > 18 demands refactor plus ADR.
- Function length target: ≤ 60 logical lines. Between 61 and 80 requires a follow-up task; > 80 is disallowed without ADR.
- Modules should stay under 800 LOC and expose ≤ 12 public call points.
- Run `lizard --CCN 15 --length 80` and attach summaries for PRs that touch complex areas.

```python
def _filter_valid(records: Iterable[Record]) -> list[Record]:
    """Filter records while logging invalid entries."""
    valid: list[Record] = []
    for record in records:
        if not record.is_valid():
            logger.warning("invalid_record", extra={"id": record.id})
            continue
        valid.append(record)
    return valid
```

---

## Tooling Checklist

- `ruff format <paths>` and `ruff check --fix <paths>` before committing.
- `mypy <paths>` for type safety on modified modules.
- `pytest <paths>` covering new or changed units.
- `make studio-check-inventory-health` after substantial migrations to confirm standards coverage.

---

## Anti-Patterns to Avoid

- Global mutable state, magic numbers, or vague identifiers (`data1`, `tmp`).
- Broad `except Exception:` blocks without re-raising with context.
- Inline lambdas for multi-branch logic; prefer named helpers.
- Log spam, redundant prints, or unstructured console output.
- Silent failure of background jobs or tasks without escalation in logs/metrics.

---

## Continuous Improvement

- Update this standard when new automation surfaces recurring issues.
- Log debt in `repo_clean_log/` or project ADRs if you must defer improvements.
- Cross-link additions to mission parameters when scope or policy changes.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: py-standards-validate
      title: Validate Python standards in changed files
      steps:
        - ensure-docstrings: [module, public-classes, public-functions]
        - ensure-type-hints: true
        - check-formatters: [ruff, mypy]
        - verify-tests: true
    - ensure-async-fastapi:
        path-ops-async: true
        no-blocking-io: true
    - ensure-logging:
        no-print: true
        module-logger: true
    - ensure-config-secrets:
        no-hardcoded-secrets: true
        uses-settings: true
    - ensure-complexity:
        max-cc: 12
        max-function-lines: 60
        adr-required-overrides: true
    - ensure-sqlite-safety:
        parameterized-queries: true
        wal-enabled: recommended
        indexes-present: recommended
        severity: warn
```
<!-- agents:end:agent_instructions -->
