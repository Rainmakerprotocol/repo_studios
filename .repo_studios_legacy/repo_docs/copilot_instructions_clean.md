---
title: repo Cleanup Instructions
audience: [repo, Jarvis2, Developer]
role: [Operational-Doc, Cleanup]
owners: ["@docs-owners"]
status: active
version: 1.1.0
updated_at: 2025-09-28
tags: [cleanup, refactor, standards]
related_files:
  - ./repo_standards_python.md
  - ./repo_standards_markdown.md
  - ./repo_standards_project.md
---

# 🧠 GitHub repo: Code Cleanup Instructions

Target Folder: `metrics_storage/storage` (override with `-t <path>` when using the tool below)

---

## 🎯 Primary Objective

repo will clean and refactor all Python files in the specified folder
according to the following rules:

1. Remove debug statements (`print`, `breakpoint`, `pdb`, etc.)
1. Fix syntax errors (for example, `Dict` → `dict`, unclosed blocks)
1. Eliminate unused imports, variables, and dead code
1. Apply formatting standards (PEP 8) using Ruff (formatter + linter). Black is not used.
1. Refactor large or deeply nested functions into smaller logical units where
  appropriate
1. When touching functions already over the complexity thresholds (CC ≥ 13 or
  > 60 logical lines), either reduce them below the guardrails or record a debt
  entry in `repo_clean_log/` linking to the planned follow-up
1. Rename vague function/variable names to be descriptive and Pythonic
1. Ensure each module, class, and function includes a clear and concise
  docstring
1. Prefer in-place changes, but fully rewrite files if a logical restructuring
  results in clearer logic or better maintainability
1. Use in-code annotations to explain why changes were made (to assist future
   agents like Jarvis2)
1. Update or create test cases that reflect the cleaned or refactored code

---

## 🧪 Testing Protocol

For every testable code unit:

* [ ] Create at least one test case per public function or method
* [ ] Use descriptive test function names
* [ ] Assert expected outputs and side effects
* [ ] Add integration tests where the module orchestrates multiple components
* [ ] Ensure all tests are idempotent and do not require external state unless
      mocked

---

## 📊 Logging Protocol (repo_clean_log)

After completing the cleanup task:

* [ ] Create a `.txt` log file in `.repo_studios/cleanup_logs/` (the batch tool writes this automatically)
* [ ] Filename format: `clean_YYYY-MM-DD_HHMM.txt`
* [ ] Log must include:
  * Target folder cleaned
  * Total number of files updated
  * Types and counts of changes made (for example, "13 print statements
    removed", "4 functions refactored")
  * A list of repeated patterns/issues encountered
  * Notes on files skipped (with reasons)
  * List of tests added or updated

---

## 🔁 Self-Improvement Protocol

After logging:

1. Read the last 10 `.txt` logs in the cleanup logs folder
2. Identify recurring patterns or high-frequency issues
3. Check the file `repo_studios_python.md` for known solutions
4. If a new pattern is not listed, append a new entry in the following format:

````md
## Issue: [Short title for issue]
**Example Pattern:**
```python
# Insert bad pattern here
```

**Solution:**

```python
# Insert the approved pattern or fix here (with type hints + docstring when
# applicable)
```

Include 1–2 minimal tests to validate the fix and run `make qa` locally.
````

---

## 🧰 Operational Notes (Jarvis2 Specifics)

* Ruff is the single source of truth for both linting and formatting. Black is
  not used (remove obsolete references to Black in older docs when encountered).
* For targeted cleanup, use `.repo_studios/ruff_clean.toml` to ensure storage
  modules are included even if CI excludes them for noise reduction.
* Prefer small, focused diffs. Avoid touching unrelated files.
* Add or update tests for any non-trivial refactor.
* The batch tool will also attempt `markdownlint` via `npx markdownlint-cli`; if Node
  is unavailable it will skip markdown formatting gracefully.

### Local Commands for This Cleanup

Preferred (one‑shot orchestrator):

```bash
./.venv/bin/python ./.repo_studios/batch_clean.py -t metrics_storage/storage
```

Manual (granular control):

```bash
ruff format metrics_storage/storage --config .repo_studios/ruff_clean.toml
ruff check metrics_storage/storage --fix --config .repo_studios/ruff_clean.toml
make qa
```

---

## ✅ Completion Criteria

* Debug prints, breakpoints, unused imports, and dead code removed.
* Functions are reasonably sized and named, with docstrings on public APIs.
* Ruff format + fix applied; tests pass locally.
* Cleanup log created in `.repo_studios/cleanup_logs/` with counts and
  notes.
* If cleanup touched multiple markdown headings, run `make anchor-health` and ensure
  `strict_duplicate_count` has not regressed before submitting.

## Anchor Health Cross-Link

When a cleanup batch renames or adds H1/H2 headings across documentation, you must:

1. Run `make anchor-health`.
2. Inspect `.repo_studios/anchor_health/anchor_report_latest.json` for new duplicate clusters.
3. Rename non-canonical headings using disambiguating AI-prefixed patterns if collisions appear.
4. Re-run until no regression vs baseline (see `tests/docs/anchor_slug_baseline.json`).

This prevents drift and maintains navigability for agents consuming anchors.
