---
title: repo Standards — Python Coding Practices for AI and Agent Compatibility
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@docs-owners"]
status: approved
version: 1.0.0
updated_at: 2025-08-22
tags: [python, standards, ai-ingestion, agents]
related_files:
  - ./repo_standards_markdown.md
  - ./repo_standards_project.md
---

## 📘 repo Standards — Python Coding Practices for AI and Agent Compatibility

Audience: repo | Jarvis2 | Developer | All

This document defines comprehensive Python coding standards for GitHub repo to
follow when generating, cleaning, or refactoring Python code. These rules align
with both community-accepted best practices (PEP8, PEP257) and extended
conventions suitable for AI-driven systems such as Jarvis2, modular agents, and
autonomous codebases.

repo must treat this document as a persistent reference during all
generation workflows.

---

## ✅ Style & Formatting (PEP8 + AI Extensions)

* Use 4-space indentation (no tabs)
* Line length ≤ 88 characters (unless breaking logic is worse)
* Use snake_case for variables and functions
* Use PascalCase for class names
* Use UPPER_CASE for constants
* Avoid inline comments except for clarifying logic; prefer block-level docstrings
* One blank line between functions, two between class definitions
* Avoid trailing commas unless in multiline structures
* Use consistent ordering: imports → constants → classes → functions

---

## 🧱 Structural Standards for AI/Agent Codebases

* Every .py file must contain a module-level docstring
* Every public function, method, and class must include a docstring
* Use type hints for all parameters and return values, even in internal methods
* Use dataclass, NamedTuple, or Pydantic for structured data models
* Avoid circular imports by using lazy-loading techniques or separation of concerns
* Prefer single-responsibility functions — no function should do more than one
  distinct thing
* Separate I/O operations from business logic and pure computations

---

## 📚 Documentation & Docstrings

* Module docstring format:

```python
"""
Module Name: user_metrics
Purpose: Provides functions to calculate user activity metrics for AI analysis.
"""
```

* Class docstring format:

```python
class UserActivity:
  """
  Represents user activity metrics for a specific day.

  Attributes:
    user_id (str): Unique identifier for the user.
    activity_count (int): Number of activities recorded.
  """
```

* Function docstring format:

```python
from typing import List

def get_active_users(day: str) -> List[str]:
  """
  Return a list of active user IDs based on activity recorded on a given day.

  Args:
    day (str): Date string in YYYY-MM-DD format.

  Returns:
    List[str]: List of user IDs.
  """
```

* Always include Args, Returns, and Raises (if applicable)

---

## 🧠 AI & Agent Design Guidelines

* Avoid global state or hardcoded paths — all configs must be parameterized
* Design components as modular and composable units
* Ensure all logic can be accessed via class, function, or command entrypoint
* Prepare interfaces that can be reused by Jarvis2 or other agents:
  * Accept dictionaries, strings, or data models as inputs
  * Return structured objects, JSON-serializable responses, or typed results
* Log to a central log handler using structured logging (e.g., logger.info())
* Provide `__repr__` and `__str__` in all public classes for agent readability

---

## ⚡ Async & FastAPI Patterns

* Prefer `async def` for FastAPI path operations and I/O-bound work
* Do not block the event loop; wrap CPU or blocking I/O with
  `anyio.to_thread.run_sync` or `starlette.concurrency.run_in_threadpool`
* Validate all inputs with Pydantic models; use `Annotated` and validators for
  clearer constraints
* Inject dependencies via FastAPI `Depends`; avoid global singletons
* Return Pydantic models or JSON-serializable dicts; never raw DB cursors
* Keep endpoint thin: parse/validate → call service → map to response model

Example:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/items", tags=["items"])

class ItemIn(BaseModel):
  name: str = Field(min_length=1, max_length=128)
  quantity: int = Field(ge=0, le=1_000_000)

class ItemOut(ItemIn):
  id: int

async def get_service() -> "ItemService":
  # ... construct or fetch from container ...
  return ItemService()

@router.post("/", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
  payload: ItemIn,
  svc: Annotated["ItemService", Depends(get_service)],
):
  try:
    item = await svc.create(payload)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  return item
```

---

## 📈 Logging & Metrics

* Never use `print()` in library or API code; use the standard `logging` module
* Create module loggers with `logger = logging.getLogger(__name__)`
* Use structured, concise messages; include stable keys in `extra={...}`
* Choose levels intentionally: debug for diagnostics, info for state changes,
  warning for recoverable anomalies, error for failures, critical for outages
* Emit timing or count metrics for critical paths (DB calls, external requests)
* Prefer a single metrics facade so backends (Prometheus/SQLite) can swap

Example logger and timing helper:

```python
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def timing(name: str):
  start = time.perf_counter()
  try:
    yield
  finally:
    dur_ms = (time.perf_counter() - start) * 1000
    logger.info("timing", extra={"op": name, "ms": round(dur_ms, 2)})
```

---

## 🔐 Config & Secrets

* No hardcoded secrets, tokens, or file paths; load via environment or a
  settings object
* Use Pydantic `BaseSettings` (or `pydantic-settings`) for typed config
* Centralize configuration in one module; access via a cached getter
* Support overrides for tests with env vars or dependency injection

Example settings:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  api_token: str
  db_path: str = "/home/founder/jarvis2/data/metrics.db"
  log_level: str = "INFO"

  class Config:
    env_prefix = "JARVIS_"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()  # reads from environment
```

---

## 🧯 Error Handling

* Fail fast with explicit exceptions; catch narrow exceptions where recovery is
  possible and add context
* In FastAPI, map domain errors to `HTTPException` with precise status codes
* Do not swallow exceptions silently; log with level and actionable detail
* Prefer `Result`-like returns only when it simplifies callsites; otherwise
  raise and handle at boundaries (API/job entrypoints)

Example handler registration:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class DomainError(Exception):
  pass

def attach_handlers(app: FastAPI) -> None:
  @app.exception_handler(DomainError)
  async def _domain_error(_: Request, exc: DomainError):  # noqa: D401
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

---

## 🚀 Performance & SQLite

* Use parameterized queries; never f-strings with user input
* Reuse connections or connection pools; enable WAL when appropriate
* Keep transactions short; batch writes; avoid N+1 query patterns
* Create indexes for filter and join columns; verify with `EXPLAIN QUERY PLAN`
* For async workloads, favor `aiosqlite` or delegate blocking calls to a
  threadpool
* Guard long-running operations with timeouts and cancellation

Example connection setup:

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

## 🧪 Testing Expectations

* Each testable unit (public function or class) must have a corresponding test
* Group tests in files named test_*.py using pytest
* Use mocks or fixtures to avoid dependency on external services
* Test files must:
  * Validate success cases
  * Handle edge cases or exceptions
  * Match expected input/output formats
* Tests should be idempotent, environment-independent, and agent-compatible

---

## 🧼 Code Quality Enforcement

* Use ruff to lint and auto-correct style violations
* Use black to enforce formatting
* Use mypy to validate type safety
* Use pytest to confirm runtime correctness

---

## 🚫 Anti-Patterns and Practices to Avoid

* No print() statements — use logging with appropriate levels
* No vague variable names like x, tmp, data1, stuff
* Avoid nesting more than 3 levels deep — use helper functions
* No catching broad Exception unless re-raised with context
* No hardcoded strings, tokens, paths, or magic numbers
* Avoid inline lambdas for readability unless trivial

---

## 🧮 Complexity Management

To keep the codebase maintainable and performant, adhere to these guardrails:

* **Cyclomatic complexity:** target ≤ 12. Anything between 13–18 needs reviewer sign-off
  with rationale. Anything > 18 must be refactored or backed by an ADR exception.
* **Function length:** keep functions ≤ 60 logical lines. If 61–80, include a decomposition
  plan in the PR. Anything > 80 requires an ADR note and a linked follow-up ticket.
* **Module scope:** avoid modules > 800 LOC or with more than 12 public definitions—split
  them following the File Decomposition Policy.
* **Hot-path exceptions:** when complexity is unavoidable (parsers, evaluators), add
  benchmarks plus a debt entry scheduled within the next sprint.

### Tooling & automation

* Run `lizard --CCN 15 --length 80 <paths>` locally (pre-commit hook recommended) before
  sending a PR.
* `make lint` now runs the complexity check; PRs must pass without new warnings.
* Record complexity baselines for new modules in commit messages or ADRs when applicable.

### Code review checklist (add to PR description)

* [ ] Attached lizard summary for touched modules (or confirmed no changes)  
* [ ] Highlighted any functions exceeding thresholds with remediation plan  
* [ ] Added/updated tests for extracted helpers or decomposed modules  
* [ ] Logged debt item in `repo_clean_log/` if complexity not reduced immediately

### Helper extraction example

```python
# Before: mixed concerns inflate complexity
def process_and_emit(records: list[Record]) -> None:
  validated = []
  for record in records:
    if record.is_valid():
      validated.append(record)
    else:
      logger.warning("invalid_record", extra={"id": record.id})
  totals = aggregate_totals(validated)
  emit_totals(totals)


# After: helper encapsulates validation branch and reduces CC/length
def _filter_valid(records: Iterable[Record]) -> list[Record]:
  valid: list[Record] = []
  for record in records:
    if not record.is_valid():
      logger.warning("invalid_record", extra={"id": record.id})
      continue
    valid.append(record)
  return valid


def process_and_emit(records: Iterable[Record]) -> None:
  valid_records = _filter_valid(records)
  totals = aggregate_totals(valid_records)
  emit_totals(totals)
```

---

## 🔁 Continuous Learning Loop

* After each cleanup, repo must analyze the last 10 logs in repo_clean_log/
* Identify high-frequency issues or structural gaps
* Update this standards file if a new principle becomes system-wide
* Each update must follow the same structured and markdown-ready format

---

## 🤖 Agent Block (machine-readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: py-standards-validate
      title: Validate Python standards in changed files
      steps:
        - ensure-docstrings: [module, public-classes, public-functions]
        - ensure-type-hints: true
        - check-formatters: [ruff, black, mypy]
        - verify-tests: true
    - ensure-async-fastapi: {path-ops-async: true, no-blocking-io: true}
    - ensure-logging: {no-print: true, module-logger: true}
    - ensure-config-secrets: {no-hardcoded-secrets: true, uses-settings: true}
    - ensure-error-mapping: {http-exceptions: true, narrow-catches: true}
    - ensure-sqlite-safety:
      parameterized-queries: true
      wal-enabled: recommended
      indexes-present: recommended
      severity: warn
```
<!-- agents:end:agent_instructions -->

---

By following these standards, repo ensures its code is not only correct and
clean, but also future-compatible with agent orchestration, AI traceability,
modular automation, and human collaboration.

### 🔁 File Decomposition Policy

#### 📏 File Complexity Thresholds

* Decompose any `.py` file if:
  * > 1000 lines of code
  * > 12 function/class definitions
  * Function complexity > 15 (cyclomatic)
  * More than 3 deep nesting levels

#### 🪓 Decomposition Process

* Only decompose the part of the file currently being modified.
* Create a new module for that part (e.g., `cache/negative_cache.py`)
* Leave remaining parts of the original file intact until assigned
* Each new module must include:
  * Unit tests (`tests/...`)
  * Inline docstrings
  * Updates to related `.md` documentation files
* Log decomposition steps to `repo_clean_log/clean_YYYY-MM-DD_HHMM.txt` including:
  * File/line split
  * Destination path
  * Test file created
  * `.md` docs touched
