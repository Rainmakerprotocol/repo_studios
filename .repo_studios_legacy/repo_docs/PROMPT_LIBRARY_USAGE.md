---
title: Prompt Library Usage
audience: [repo, Jarvis2, Developer]
role: [Operational-Doc, Prompt-Standards]
owners: ["@docs-owners"]
status: active
version: 1.1.0
updated_at: 2025-09-28
tags: [prompts, standards, ai]
related_files:
  - ../repo_standards_markdown.md
  - ../repo_standards_project.md
  - ../README.md
---

# Prompt Library Usage

This repository standardizes AI prompt flows via the library at `/home/founder/jarvis2/repo_prompts.md`.
Use it as the single source of truth.

## Rules

* When asked for a status, update, review, or design flow, map the request to a
  prompt in the library under the correct group (Atomic or Bundle).
* Respond by pasting the full text of that prompt section, unchanged.
* If the request is ambiguous, list 2–3 candidate prompts with their one‑line
  descriptions from the Index and ask the user to choose.
* Never invent new prompts; only use sections from `repo_prompts.md`.
* Treat the library as authoritative; keep outputs consistent and repetitive to
  ensure alignment.

## Locations

* Library file: `repo_prompts.md` (repo root)
* Index: first section in the library (keys + one‑liners)

## Notes

* Maintain Markdown hygiene: blank lines around headings/lists, short lines,
  code fences with language fences.
* If a prompt must evolve:
  1. Update `repo_prompts.md` (edit the canonical section in place; keep existing key/anchor stable if intent is unchanged, otherwise add a new key and mark the old one deprecated in a short note).
  2. Run an anchor check (`make anchor-health`) to ensure new headings do not collide with existing H1/H2 across the repo (see Anchor Health Cross-Link below).
  3. Re-run any affected flows/tests that rely on deterministic prompt text.
  4. Commit prompt update and dependent doc/code changes atomically.
* Validation step: before using a prompt key, verify it exists by grepping the library (for example, `grep -n '^## \[KEY:' repo_prompts.md` if keys follow a bracketed naming convention) to avoid drift.
* Do not duplicate near-identical prompts—prefer parameterization instructions inside a single canonical entry.

## Anchor Health Cross-Link

When adding, renaming, or removing H1/H2 headings in `repo_prompts.md`, run `make anchor-health` and inspect `.repo_studios/anchor_health/anchor_report_latest.json` to avoid introducing duplicate slug clusters. Prefer descriptive, disambiguating headings (AI-prefixed where appropriate) over generic titles ("Overview", "Context", "Usage"). See `repo_standards_markdown.md` for governance rules.
