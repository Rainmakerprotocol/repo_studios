---
title: Repo Studios Project Operating Standard
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
  Project-level guardrails covering technology stack, behavioral expectations, and documentation hygiene for Repo Studios contributors and agents.
tags:
  - project
  - standards
  - ai-ingestion
legacy_source: .repo_studios_legacy/repo_docs/copilot_standards_project.md
---

# Repo Studios Project Operating Standard

Audience: Repo Studios automation | Human developers | Partner agents

Use this document as the single source of truth for how Repo Studios projects are structured, validated, and kept in sync with automation. The guidance applies to all code and documentation inside the project workspace unless an approved override exists in `docs/standards/project/`.

---

## Primary Responsibilities

- Deliver modular, well-documented Python services, HTML artifacts, and Chainlit UIs that follow the global standards.
- Keep project documentation, automation scripts, and CI configuration aligned when introducing new metrics, environment flags, or interfaces.
- Record impactful refactors or migrations in timestamped notes under `.repo_studios/agent_notes/` using the standard naming convention.

---

## Technology Baseline

| Surface        | Standard                                                     |
| -------------- | ------------------------------------------------------------ |
| Language       | Python 3.11+                                                 |
| UI Engine      | Chainlit (async-first chat UI)                               |
| Frontend       | HTML5 with Tailwind utility classes where applicable         |
| Documentation  | Markdown with Repo Studios metadata headers                  |
| Testing        | Pytest suites grouped by module                              |
| Logging        | `logging` module (Python) and structured Chainlit emitters   |
| Formatting     | Ruff (lint + format) with repo configuration                 |

Only add new frameworks or packages when they improve modularity, observability, or AI compatibility. Capture rationale in an ADR or agent note.

---

## Dependencies & Environment

Minimal baseline packages include `python-dotenv`, `pydantic`, `fastapi`, `chainlit`, `ruff`, `mypy`, `pytest`, `httpx`, `jinja2`, and `uvicorn`. Additions require:

1. Documented justification tied to product or automation goals.
2. Updated bootstrap instructions in `SETUP.md` and relevant plan checklists.
3. Passing security review via `make studio-check-inventory-health` and Codacy scanners.

---

## Testing & QA Expectations

- Provide unit, integration, and failure-case coverage for every public function or module touchpoint.
- Run `pytest`, `ruff check`, `ruff format --check`, and `mypy` before pushing changes; CI mirrors these gates.
- For documentation that changes metrics or environment switches, update:
  1. `docs/agents/config_quickstart.md`
  2. Root `README.md` agent configuration tables
  3. Any affected phased plan checklist files
- Execute `python .repo_studios/scripts/check_markdown_anchors.py` (or `make docs-anchors`) whenever headings or anchors move; ensure zero regressions.
- Prefer installing Git hooks with `make install-hooks` for anchor and slug hygiene.

---

## Behavioral Standards

- Infer file purpose by directory context and follow the paired global standard (Python, Markdown, HTML, Chainlit, etc.).
- Refactor functions longer than 60 logical lines or with more than three nested branches; log intentional exceptions via ADR or cleanup notes.
- Separate business logic from I/O, UI, and orchestration code to keep agents composable.
- Avoid global mutable state and hardcoded paths; rely on typed settings objects and dependency injection.
- Log meaningful changes in `.repo_studios/cleanup_logs/` when executing large-scale cleanups.

---

## Documentation & Inventory Hygiene

- Every new operational doc requires YAML front matter and cross-links to related assets.
- When migrating or renaming artifacts, update `.repo_studios/inventory_schema/*.yaml` and rerun `python .repo_studios/scripts/check_inventory_health.py`.
- Keep project-specific overrides in `docs/standards/project/` with clear delta notes compared to global standards.
- Archive large reference trees or diagrams separately; link to them instead of embedding raw dumps in standards.

---

## Operational Commands

```bash
make studio-render-views            # refresh inventory views and summaries
make studio-validate-inventory      # enforce schema correctness and file presence
make studio-check-inventory-health  # compare summary deltas against thresholds
python .repo_studios/scripts/check_markdown_anchors.py  # validate docs anchors
```

Use these commands locally before opening pull requests to prevent CI churn.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: project-standards-review
      title: Enforce project operating guardrails
      steps:
        - ensure-commands-run: ["pytest", "ruff check", "mypy"]
        - ensure-docs-updated:
            files:
              - docs/agents/config_quickstart.md
              - README.md
              - docs/**/checklist*.md
        - ensure-anchor-check: true
    - ensure-global-standards
      python: std-global-python-engineering.md
      markdown: std-global-markdown-authoring.md
      html: std-global-html-coding.md
      chainlit: std-global-chainlit-ui.md
```
<!-- agents:end:agent_instructions -->
