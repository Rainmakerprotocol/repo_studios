---
title: Repo Studios Standards Index
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ai
tags:
  - standards
  - index
  - governance
---

# Repo Studios Standards Index

This index links the governed standards collection so automation and contributors can find the
applicable guidance without relying on generated mirrors.

## How to Use This Index

- Review the tables below when you need the canonical location for standards referenced by
  orchestrators or health checks.
- Update this file whenever a standard is added, renamed, or retired so doc integrity jobs stay
  green.
- Capture any open migration work in the notes column until the authoritative copy replaces a
  placeholder.

## Global Standards

| Document | Scope | Notes |
|----------|-------|-------|
| [Docs Integrity Handbook](global/std-docs-integrity-handbook.md) | Documents governed surfaces used by Repo Studios automation. | Missing front matter; migrate authoritative copy. |
| [Global Markdown Authoring Standard](global/std-global-markdown-authoring.md) | Canonical markdown structure and metadata expectations. | Stable source for authoring checks. |
| [Global Chainlit UI Standard](global/std-global-chainlit-ui.md) | Placeholder conventions for Chainlit-driven interfaces. | Replace with synced standard. |
| [Global Code Cleanup Standard](global/std-global-code-cleanup.md) | Interim guidance for cleanup and refactor workflows. | Placeholder content awaiting full import. |
| [Global HTML Coding Standard](global/std-global-html-coding.md) | Temporary HTML coding practices. | Placeholder content awaiting full import. |
| [Global Mission Parameters](global/std-global-mission-parameters.md) | Draft reference for mission parameters and decision logging. | Awaiting authoritative source sync. |
| [Global Monkey Patching Standard](global/std-global-monkey-patching.md) | Constraints and hygiene for monkey patch usage. | Placeholder content awaiting full import. |
| [Global Prompt Engineering Standard](global/std-global-prompt-engineering.md) | Interim prompt engineering practices with evaluation focus. | Placeholder content awaiting full import. |
| [Global Python Engineering Standard](global/std-global-python-engineering.md) | Baseline Python engineering expectations for contributors. | Placeholder content awaiting full import. |

## Project Standards

| Document | Scope | Notes |
|----------|-------|-------|
| [Project Operating Standard](project/std-project-operating-standard.md) | Core project hygiene expectations spanning dependencies, automation, and docs. | Front matter missing owner and tags. |
| [Project Python Instructions](project/std-project-python-instructions.md) | Python contributor expectations covering environment, docs, and testing. | Source of truth; keep date fields current. |

## Maintenance Notes

- The Standards Integrity orchestrator reads this index to seed healthview artifacts located under
  `.repo_studios/command_center/reports/healthview/standards_overview/`.
- When importing the authoritative standards, replace placeholder copy first, then update this table
  so downstream reports highlight the refreshed material instead of legacy gaps.
- Run `make -C .repo_studios studio-orchestrate-standards` after edits to verify the new index is
  discoverable and the integrity suite stays green.
