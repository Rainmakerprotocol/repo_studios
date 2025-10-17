---
title: repo Prompt Engineering Standards
audience: [repo, Jarvis2, Developer]
role: [Standards, Prompt-Engineering]
owners: ["@docs-owners"]
status: draft
version: 0.1.0
updated_at: 2025-09-04
tags: [prompts, standards, ai, docs]
related_files:
  - ./.repo_studios/repo_standards_project.md
  - ./.repo_studios/repo_standards_markdown.md
---

## 🎯 Purpose

Set practical, repeatable standards for designing prompts and agent instructions used
across Jarvis2. Keep prompts short, structured, and testable. Prefer machine-readable
sections when possible.

## 🧩 Core Principles

* Ground prompts in repo context and explicit requirements
* Avoid hallucination: state assumptions briefly or ask only when blocked
* Keep outputs deterministic: prefer bullets, JSON, or YAML
* Avoid heavy formatting unless user requests it; bullets are fine
* Include acceptance criteria or a “Done when” checklist for tasks

## 📐 Prompt Patterns

* Command prompts: start with an action verb, include scope, success criteria
* Diagnostic prompts: ask for minimal repro, logs, and next step
* Generation prompts: specify file paths, interfaces, constraints, tests
* Refactor prompts: list invariants, edge cases, and before/after behavior

## 🧪 Validation

* Add tiny contracts (inputs/outputs, error modes) for code tasks
* Include 1 happy path + 1 edge case for tests
* Prefer local verification tools (pytest, ruff, typecheck) over prose claims

## 🔁 File Decomposition Policy

### 📏 File Complexity Thresholds

* Decompose any `.py` file if:
  * > 1000 lines of code
  * > 12 function/class definitions
  * Function complexity > 15 (cyclomatic)
  * More than 3 deep nesting levels

### 🪓 Decomposition Process

* Only decompose the part of the file currently being modified.
* Create a new module for that part (e.g., `cache/negative_cache.py`).
* Leave remaining parts of the original file intact until assigned.
* Each new module must include:
  * Unit tests (`tests/...`).
  * Inline docstrings.
  * Updates to related `.md` documentation files.
* Log decomposition steps to `repo_clean_log/clean_YYYY-MM-DD_HHMM.txt` including:
  * File/line split.
  * Destination path.
  * Test file created.
  * `.md` docs touched.

## ✅ Example Machine-Readable Block

```yaml
contract:
  inputs: ["/path/to/file.py", "flag:bool"]
  outputs: ["diff", "tests"]
  done_when:
    - tests: pass
    - lint: clean
    - typecheck: clean
```
