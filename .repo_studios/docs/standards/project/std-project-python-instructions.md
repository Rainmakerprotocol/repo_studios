---
title: Repo Studios Python Remediation Instructions
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
status: draft
version: 0.1.0
updated: 2025-10-18
summary: >-
  Repository-specific Python cleanup patterns, quick fixes, and approved practices preserved from the Jarvis2 remediation guide.
tags:
  - python
  - remediation
  - standards
legacy_source: .repo_studios_legacy/repo_docs/copilot_instructions_python.md
---

<!-- markdownlint-disable MD025 -->
# Repo Studios Python Remediation Instructions

This structured reference equips Repo Studios automation and collaborators with vetted Python patterns, anti-patterns, and fixes derived from the Jarvis2 remediation log. Any references to the legacy agent name (`repo`) map to Repo Studios automation in the current workflow.

Use this guide to prevent repeated mistakes, apply pre-approved solutions, and capture new recurring issues with precise remediation steps. Agents may append to this document when a new recurring issue emerges and a fix can be clearly defined.

---

## Project-Specific Quick Rules (Jarvis2)

- Prefer Make targets for validation: `make qa` (runs lint, type-check, tests).
- Never hardcode secrets or tokens; read from environment variables such as `METRICS_API_TOKEN` or `INTERNAL_API_KEYS`.
- For FastAPI tests, use `httpx.ASGITransport` plus `httpx.AsyncClient` with `api.server:app`.
- Use `api.server.get_db_path()` (or the injected dependency) instead of hardcoding database paths.
- Keep public APIs stable; minimize diffs; avoid reformatting unrelated code.
- Add tests for behavioral changes and run them locally before finishing.

---

## Format for Adding New Entries

Repo Studios automation must follow the format below for every new entry:

````md
## Issue: [Short name for pattern or bug]
**Example Pattern:**
```python
# Show a bad or discouraged code pattern here
```

**Solution:**
```python
# Show the clean, modern, or approved pattern here
```

**Style Rules to Follow When Adding Examples:**

* Use clear function or variable names (for example, `convert_to_inches` not `x`).
* Always add type hints when known (for example, `def add(a: int, b: int) -> int:`).
* Include docstrings for public functions.
* Use logging instead of `print` for production paths.
* Use list comprehensions where appropriate.
* Break large or nested functions into smaller ones with meaningful names.
* Apply PEP 8 spacing and indentation.
* Maintain readability: one logical idea per function or block.
````

---

## Issue Catalog

### ✅ Issue: Unused variables or imports

**Example Pattern:**

```python
import os
import sys

def process():
    data = 123
    return True
```

**Solution:**

```python
# Remove unused modules and variables

def process():
    return True
```

---

### ✅ Issue: Using print() for debugging

**Example Pattern:**

```python
print("Processing started...")
```

**Solution:**

```python
# Use logging instead, or remove if unnecessary
import logging
logging.info("Processing started...")
```

---

### ✅ Issue: Incorrect keyword case (Def vs def)

**Example Pattern:**

```python
Def my_function():
    pass
```

**Solution:**

```python
def my_function():
    pass
```

---

### ✅ Issue: No docstrings on public functions

**Example Pattern:**

```python
def add(a, b):
    return a + b
```

**Solution:**

```python
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b
```

---

### ✅ Issue: Functions too large or deeply nested

**Example Pattern:**

```python
def calculate():
    # many levels of nested logic here
    pass
```

**Solution:**

```python
def step_one():
    pass

def step_two():
    pass

def calculate():
    step_one()
    step_two()
```

---

### ✅ Issue: Poor variable names (for example, `x`, `data1`, `stuff`)

**Example Pattern:**

```python
def convert(x):
    return x * 2
```

**Solution:**

```python
def convert_to_inches(length_in_feet: float) -> float:
    return length_in_feet * 12
```

---

### ✅ Issue: Mixed indentation causing `IndentationError`

**Example Pattern:**

```python
def test_something():
    x = 1
  y = 2  # BAD: inconsistent indent (2 spaces)
    assert x + y == 3
```

**Solution:**

```python
def test_something():
    x = 1
    y = 2  # Use consistent 4-space indentation throughout
    assert x + y == 3
```

---

### ✅ Issue: FastAPI tests using deprecated clients or sync patterns

**Example Pattern:**

```python
# Using requests or TestClient sync patterns inconsistently with async code
resp = client.get('/metrics/latest')  # may not exercise ASGI app properly
```

**Solution:**

```python
import asyncio
import httpx
from api.server import app

transport = httpx.ASGITransport(app=app)

async def _call():
    async with httpx.AsyncClient(
        transport=transport,
        base_url='http://test'
    ) as c:
        return await c.get(
            '/metrics/latest',
            params={'name': 'cpu.util'},
            headers={'X-API-Key': 'secret'}
        )

resp = asyncio.run(_call())
assert resp.status_code == 200
```

---

### ✅ Issue: SQLite `OperationalError: unable to open database file`

**Example Pattern:**

```python
import sqlite3
conn = sqlite3.connect('/tmp/nonexistent/folder/db.sqlite')  # path invalid
```

**Solution:**

```python
# Ensure the path is valid and prefer configured path via env/DI
import os
import sqlite3

db_path = os.getenv('METRICS_DB_PATH', '/tmp/metrics.db')
conn = sqlite3.connect(db_path)
# In tests: set METRICS_DB_PATH to a tmp file and seed schema before querying
```

---

### ✅ Issue: Cached global DB path across tests (stale `_DB_PATH`)

**Example Pattern:**

```python
# Test sets METRICS_DB_PATH but the server still uses an old cached path
```

**Solution:**

```python
# Ensure the accessor refreshes from env or tests reset the cache.
# Prefer calling the accessor (get_db_path) and avoid hardcoding.
# When needed in tests, set METRICS_DB_PATH early before importing app.
```

---

### ✅ Issue: Using print or logging secrets (tokens, API keys)

**Example Pattern:**

```python
print('Token is', os.getenv('METRICS_API_TOKEN'))  # BAD: leaks secret
```

**Solution:**

```python
import logging
logging.info('Metrics endpoint accessed')  # Do not log secret values
```

---

### ✅ Issue: Returning generic 500s instead of precise HTTP errors

**Example Pattern:**

```python
from fastapi import HTTPException
raise HTTPException(500, 'Invalid input')  # BAD: not a server error
```

**Solution:**

```python
from fastapi import HTTPException
# Use 400 for invalid client input, 401/403 for auth issues, 404 when not found
raise HTTPException(status_code=400, detail='Invalid labels JSON')
```

---

### ✅ Issue: Prefer `pathlib` over `os` for file I/O (Ruff PTH103, PTH123)

**Example Pattern:**

```python
import os
from typing import Iterable

os.makedirs(base_dir, exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
with open(path, "rb") as f:
    data = f.read()
with open(path, "w", encoding="utf-8") as f:
    for line in lines:
        f.write(f"{line}\n")
```

**Solution:**

```python
from pathlib import Path
from typing import Iterable

base = Path(base_dir)
base.mkdir(parents=True, exist_ok=True)

Path(path).write_text(content, encoding="utf-8")
data = Path(path).read_bytes()

with Path(path).open("w", encoding="utf-8") as f:
    for line in lines:
        f.write(f"{line}\n")
```

---

### ✅ Issue: Replace `try/except/pass` with `contextlib.suppress` (SIM105)

**Example Pattern:**

```python
try:
    tmp.unlink()
except Exception:
    pass
```

**Solution:**

```python
from contextlib import suppress

with suppress(Exception):
    tmp.unlink()
```

---

### ✅ Issue: Ambiguous single-letter names and E741 (`l`, `O`, `I`)

**Example Pattern:**

```python
with open(path) as f:
    return [l.rstrip("\n") for l in f]
```

**Solution:**

```python
from pathlib import Path

with Path(path).open(encoding="utf-8") as f:
    return [line.rstrip("\n") for line in f]
# For unused loop vars, use `_` or a leading underscore (for example, `_c`).
```

---

### ✅ Issue: Unicode punctuation in docstrings (RUF002 non-breaking hyphen)

**Example Pattern:**

```text
"""
Logic intentionally simple and side‑effect free.
"""
```

**Solution:**

```python
"""
Logic intentionally simple and side-effect free.
# Prefer ASCII punctuation ("-", "'", ".") in docstrings/comments.
"""
```

---

### ✅ Issue: Encourage else with try/except when returning (TRY300)

**Example Pattern:**

```python
try:
    do_work()
    return True
except SomeError:
    handle()
```

**Solution:**

```python
try:
    do_work()
except SomeError:
    handle()
else:
    return True
```

---

### ✅ Issue: Loop variable unused (B007) and dict iteration performance (PERF102)

**Example Pattern:**

```python
for c, kv in storage.items():
    if kv:
        evk = next(iter(kv))
```

**Solution:**

```python
for _kv in storage.values():
    if _kv:
        evk = next(iter(_kv))
```

---

### ✅ Issue: Optional defaults must be annotated as Optional (mypy `no_implicit_optional`)

**Example Pattern:**

```python
def make(task_type: str = None) -> str:  # type error
    ...
```

**Solution:**

```python
from typing import Optional

def make(task_type: Optional[str] = None) -> str:
    ...
# or, with Python 3.10+
def make(task_type: str | None = None) -> str:
    ...
```

---

### ✅ Issue: Don’t index `Collection[...]` — use `Sequence[...]` or materialize to list

**Example Pattern:**

```python
from typing import Collection

names: Collection[str]
first = names[0]  # type error
```

**Solution:**

```python
from typing import Sequence

def head(names: Sequence[str]) -> str:
    return names[0]

# or convert when you truly need indexing
first = list(names)[0]
```

---

### ✅ Issue: Remove unused `type: ignore` and prefer targeted ignores

**Example Pattern:**

```python
result = 42  # type: ignore  # unnecessary
```

**Solution:**

```python
result = 42  # no ignore needed
# When necessary, use a specific code:  # type: ignore[arg-type]
```

---

### ✅ Issue: Use `typing.Any`, not `any`, in type positions

**Example Pattern:**

```python
def f(x: any) -> any:
    ...
```

**Solution:**

```python
from typing import Any

def f(x: Any) -> Any:
    ...
```

---

### ✅ Issue: Arithmetic with Optional values

**Example Pattern:**

```python
delta = current - baseline  # where baseline: float | None
```

**Solution:**

```python
from typing import Optional

def compute_delta(current: float, baseline: Optional[float]) -> float:
    base = 0.0 if baseline is None else baseline
    return current - base
```

---

### ✅ Issue: Requests type stubs missing in tests (`mypy import-untyped`)

**Example Pattern:**

```python
import requests  # mypy: Library stubs not installed for "requests"
```

**Solution:**

```text
# Add to dev requirements:
#   types-requests
# Or type-narrow interfaces via Protocols instead of concrete imports in tests.
```

---

### ✅ Issue: Raise concise exceptions; avoid long inline messages (TRY003)

**Example Pattern:**

```python
raise ValueError("Unsupported format in test shim")
```

**Solution:**

```python
class UnsupportedFormatError(ValueError):
    """Unsupported format."""

raise UnsupportedFormatError()
# In small test shims, a short ValueError is acceptable; keep messages brief.
```

---

<!-- markdownlint-enable MD025 -->
