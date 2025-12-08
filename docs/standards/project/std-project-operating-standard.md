---
title: Project Operating Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ops
tags:
  - operations
  - governance
  - project-management
---

<!-- markdownlint-disable MD013 -->

# Project Operating Standard

This standard outlines the baseline project hygiene practices that every contributor should apply until the long-form documentation is synced.

## Dependency Management

- Maintain lockfiles or pinned requirement sets (for example `requirements.txt`, `requirements-dev.txt`, or `pyproject.toml`) to guarantee deterministic environments.
- Review dependency updates in pull requests, noting security and compatibility impacts before merging.
- Coordinate dependency upgrades with runtime owners to prevent cascading breakage across shared services.

## Automation Visibility

- Document every new automation target or script addition in the repository Makefile and supporting docs to keep contributors informed.
- Provide a short description, example usage, and cross-links to logs or generated artifacts so that downstream agents can troubleshoot quickly.
- Update existing automation references when renaming or deprecating tasks to avoid drift between tooling and documentation.

## Documentation Hygiene

- Follow the global markdown authoring standard when creating or editing docs: ensure a single H1, descriptive H2 sections, and a concise summary paragraph near the top.
- Store normative documentation under `docs/` or `.repo_studios/docs/` so the doc index captures it; relocating files elsewhere should be a deliberate, documented exception.
- Populate front matter with `owner`, `tags`, and `status` values so inventory tooling can route questions quickly.
- Replace placeholder prose with concrete guidance before merging; if a section still needs work, capture the remaining task in the repository issue tracker instead of leaving “TODO” copy in place.
- Review the doc index advisories during PR review to resolve missing descriptions, duplicate slugs, or other discoverability issues before shipping.

<!-- markdownlint-enable MD013 -->
