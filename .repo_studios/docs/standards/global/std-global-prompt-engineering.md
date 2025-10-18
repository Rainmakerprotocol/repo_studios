---
title: Prompt Engineering Standards
version: 0.2.0
updated: 2025-10-18
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
summary: >-
  Operational guidance for designing prompts and agent instructions used across Repo Studios projects.
---

# Prompt Engineering Standards

These standards provide reusable guardrails for prompts, agent instructions, and automation hand-offs. Apply them whenever you write or refresh Repo Studios guidance.

## Purpose

- Ground prompts in real repository context and explicit requirements.
- Prefer structured, deterministic responses that downstream tooling can parse.
- Capture acceptance criteria so maintainers can judge success quickly.

## Core Principles

- Phrase requests with concrete scope, inputs, and success criteria.
- Declare assumptions or ask for clarification instead of guessing.
- Use lightweight formatting (bullets, tables, YAML) unless richer output is required.
- Preserve task history by linking to relevant `agent_notes/` entries.

## Prompt Patterns

- **Command prompts**: start with an actionable verb, specify target files or modules, and include a "Done when" checklist.
- **Diagnostic prompts**: request minimal repro steps, logs, and the next action.
- **Generation prompts**: describe interfaces, constraints, and test expectations; list precise file destinations.
- **Refactor prompts**: note invariants, edge cases, before/after behavior, and required tests.

## Validation Practices

- Attach quick contracts (inputs, outputs, error modes) for code-related tasks.
- Include at least one happy path and one edge case when asking for tests.
- Prefer verifiable commands (`pytest`, `ruff`, `mypy`) over prose claims.

## File Decomposition Policy

### Complexity Thresholds

Decompose or extract code into new modules when any of the following thresholds are exceeded for the area under change:

- File > 1000 lines of code.
- More than 12 function or class definitions.
- Cyclomatic complexity > 15 for the function under review.
- Nesting depth greater than 3 levels.

### Decomposition Steps

- Limit decomposition to the sections being modified.
- Create dedicated modules for the extracted logic (for example `cache/negative_cache.py`).
- Ensure each new module ships with unit tests, docstrings, and updated documentation.
- Log the operation in `agent_notes/` (timestamped entry) noting file splits, new paths, tests added, and docs touched.

## Machine-Readable Contract Example

```yaml
contract:
  inputs: ["path/to/file.py", "flag:bool"]
  outputs: ["diff", "tests"]
  done_when:
    - tests: pass
    - lint: clean
    - typecheck: clean
```

## Change History

- 2025-10-18: Migrated to `.repo_studios/docs/standards/global/` with updated metadata.
- 2025-09-04: Initial draft captured in legacy repo standards.
