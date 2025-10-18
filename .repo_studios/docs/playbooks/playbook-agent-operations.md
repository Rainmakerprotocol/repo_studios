---
title: Repo Studios Agent Operations Playbook
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: draft
version: 0.1.0
updated: 2025-10-18
summary: >-
  Orientation and day-to-day runbook for Repo Studios automation and humans collaborating inside the workspace.
tags:
  - playbook
  - operations
  - repo-studios
legacy_source: .repo_studios_legacy/repo_docs/AGENTS_GUIDE.md
---

# Repo Studios Agent Operations Playbook

Audience: Repo Studios automation | Human developers | Partner agents

Use this playbook to understand the workspace topology, daily execution loop, and required tooling hygiene. It replaces the legacy `AGENTS_GUIDE.md` while aligning with the new inventory and standards stack.

---

## System Snapshot

| Surface | Baseline |
| --- | --- |
| Backend | Python 3.11+, FastAPI services, modular packages under `agents/` and `api/` |
| Frontend & UI | HTML5 + Tailwind snippets, Chainlit UI orchestrations |
| Tooling | Ruff, mypy, pytest, lizard complexity check, Make targets under `.repo_studios/` |
| Docs | Markdown with YAML front matter, inventories under `.repo_studios/inventory_schema/` |
| Automation | Repo Studios scripts (`render_inventory_views.py`, `check_inventory_health.py`, `batch_clean.py`) |

---

## Core Responsibilities

- Follow global standards for Python, Markdown, HTML, Chainlit, project operations, and monkey patches before modifying related files.
- Keep automation outputs (`reports/`, `cleanup_logs/`, `anchor_health/`) current and reference them when planning work.
- Log meaningful migrations or refactors in `.repo_studios/agent_notes/` using the timestamp convention `note_<topic>_YYYY-MM-DD_hhmmss.txt`.
- Update inventories when new docs, scripts, or reports are introduced, then run `python .repo_studios/scripts/check_inventory_health.py`.

---

## Daily Command Checklist

```bash
make studio-render-views            # refresh derived inventories
make studio-validate-inventory      # enforce schema and file presence
make studio-check-inventory-health  # compare summary against baseline thresholds
python .repo_studios/scripts/check_markdown_anchors.py  # anchor/slug hygiene
make qa                             # run lint, typecheck, tests
```

Run these before raising pull requests or handing work to another agent.

---

## Standards Reference Map

| Domain | Document |
| --- | --- |
| Mission & scope | `.repo_studios/docs/standards/global/std-global-mission-parameters.md` |
| Python engineering | `.repo_studios/docs/standards/global/std-global-python-engineering.md` |
| Markdown authoring | `.repo_studios/docs/standards/global/std-global-markdown-authoring.md` |
| HTML | `.repo_studios/docs/standards/global/std-global-html-coding.md` |
| Chainlit | `.repo_studios/docs/standards/global/std-global-chainlit-ui.md` |
| Monkey patches | `.repo_studios/docs/standards/global/std-global-monkey-patching.md` |
| Project operations | `.repo_studios/docs/standards/project/std-project-operating-standard.md` |

Always cite the relevant standard in commit summaries or agent notes when deviating from defaults.

---

## Logging & Observability

- Timestamped cleanup reports live in `.repo_studios/cleanup_logs/`—read the latest entry before beginning new refactors.
- Health suite artifacts live under `.repo_studios/health_suite/`; run `make health-suite` for a consolidated snapshot when onboarding or diagnosing regressions.
- Monkey patch trends surface in `.repo_studios/monkey_patch/trend_latest.md`; investigate any growth in active patches immediately.

---

## Collaboration Protocol

1. Review `alignment_notes_temp.md` or the latest agent note to confirm current objectives.
2. Announce significant migrations in a new agent note with links to affected inventories or standards.
3. Close the loop by updating the decision log (`memory-bank/decisionLog.md`) when governance-level changes land.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: agent-ops-checklist
      title: Follow agent operations checklist
      steps:
        - run-commands:
            - make studio-render-views
            - make studio-validate-inventory
            - make studio-check-inventory-health
        - reference-standards:
            - std-global-mission-parameters.md
            - std-global-python-engineering.md
            - std-global-markdown-authoring.md
        - update-agent-notes: true
        - log-decisions: memory-bank/decisionLog.md
```
<!-- agents:end:agent_instructions -->
