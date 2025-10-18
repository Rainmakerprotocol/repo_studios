---
title: Repo Studios Migration Playbook
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: draft
version: 0.9.0
updated: 2025-10-18
summary: >-
  Structured procedure for moving documentation and tooling from the legacy Repo Studios layout into the `.repo_studios/` workspace.
tags:
  - migration
  - playbook
  - repo-studios
---

<!-- markdownlint-disable MD025 -->

# Repo Studios Migration Playbook

Audience: Repo Studios automation | Human collaborators

This playbook standardizes how we relocate assets from `.repo_studios_legacy/` into the canonical `.repo_studios/` workspace. Follow the sections in order and update inventories and governance logs as you proceed.

---

## Scope & Prerequisites

- Confirm the target asset has a clear owner and audience; capture them in the new document front matter.
- Decide whether the asset belongs under `docs/`, `scripts/`, `reports/`, or `tests/` in the new layout.
- Review related standards (Markdown, Python, etc.) and existing playbooks that touch the asset.
- Ensure the inventory catalogs already contain or can accept an entry for the asset (`docs_catalog.yaml`, `scripts_catalog.yaml`, etc.).

---

## Migration Checklist

1. **Prep**
   - Snapshot the legacy file path and note it for the `legacy_source` field in the new front matter when applicable.
   - Inspect the legacy content for sections that map to reusable templates.
2. **Recreate Structure**
   - Author the new file under `.repo_studios/` with front matter, consistent headings, and cross-links into relevant standards or playbooks.
   - Preserve historical sections verbatim when they carry append-only intent (e.g., ledgers, specs).
3. **Update Inventory**
   - Add or edit the catalog entry to point at the new path and update metadata (phase, governance flags, maturity).
   - Run `python .repo_studios/scripts/check_inventory_health.py` and review discrepancies before proceeding.
4. **Validate & Lint**
   - Run any domain-specific checks (e.g., `make anchor-health` for Markdown anchor validation, `ruff` for Python scripts).
   - Execute Codacy CLI analysis for each edited file per governance rules, acknowledging unsupported file types when reported.
5. **Decommission Legacy Copy**
   - Once validation passes, remove the legacy file from `.repo_studios_legacy/` and ensure git history captures the migration.
   - Log the move in `.repo_studios/agent_notes/` if it affects ongoing initiatives or requires wider awareness.

---

## Validation Signals

- `python .repo_studios/scripts/check_inventory_health.py` returns zero deltas.
- Codacy CLI reports either clean results or unsupported file type notices for each migrated asset.
- Related playbooks reference the new location without broken anchors (run `python .repo_studios/scripts/check_markdown_anchors.py <file>` when headings change).
- The decision log (`memory-bank/decisionLog.md`) captures governance-impacting migrations.

---

## Rollback Guidance

- If validation fails, restore the legacy file from git, revert the new asset, and document the failure in `agent_notes/` with command outputs.
- For partial migrations (e.g., file moved but inventory entry missing), re-run the checklist from the top after addressing blockers.
- When multistep migrations involve scripts or automation, keep a temporary branch until all dependent assets validate together.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: repo-migration
      title: Migrate asset from legacy layout
      steps:
        - capture-legacy-path: true
        - create-new-asset: .repo_studios/
        - update-inventory: .repo_studios/inventory_schema/docs_catalog.yaml
        - run-validation:
            - python .repo_studios/scripts/check_inventory_health.py
            - codacy_cli_analyze
        - remove-legacy-copy: true
        - log-governance:
            - memory-bank/decisionLog.md
            - .repo_studios/agent_notes/
```
<!-- agents:end:agent_instructions -->

<!-- markdownlint-enable MD025 -->
