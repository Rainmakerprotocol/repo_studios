---
title: Project Operating Standard
status: draft
version: 2025-10-23
last_updated: 2025-10-23
---

This standard outlines the baseline project hygiene practices that every contributor should apply until the long-form documentation is synced.

## Dependency Management

- Maintain lockfiles or pinned requirement sets (for example `requirements.txt`, `requirements-dev.txt`, or `pyproject.toml`) to guarantee deterministic environments.
- Review dependency updates in pull requests, noting security and compatibility impacts before merging.
- Coordinate dependency upgrades with runtime owners to prevent cascading breakage across shared services.

## Automation Visibility

- Document every new automation target or script addition in the repository Makefile and supporting docs to keep contributors informed.
- Provide a short description, example usage, and cross-links to logs or generated artifacts so that downstream agents can troubleshoot quickly.
- Update existing automation references when renaming or deprecating tasks to avoid drift between tooling and documentation.
