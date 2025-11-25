---
title: Project Python Instructions
status: draft
version: 2025-11-25
last_updated: 2025-11-25
owner: repo_studios_ai
tags:
  - python
  - documentation
  - automation
---

<!-- markdownlint-disable MD013 -->

# Project Python Instructions

This guide documents the baseline expectations for Python contributors and automation authors.

## Environment

- Use the repository-managed virtual environment (`.venv/`) for local development and testing. Regenerate it after any dependency change.
- Pin new dependencies in `requirements.txt` or supporting lockfiles and document the reasoning in pull requests.
- Run the project formatter, lint suite, and unit tests before submitting patches.

## Documentation Expectations

- When adding or modifying Python automation, update the relevant markdown in `docs/` or `.repo_studios/docs/` the same day so the doc index reflects the latest behaviour.
- Ensure each doc adheres to the global markdown authoring standard: include front matter with `owner`, `tags`, and `status`, provide a single H1 with a descriptive summary paragraph, and add meaningful H2 sections for navigability.
- Replace temporary placeholder text with actionable guidance prior to merge. Track unfinished follow-ups via issues or TODO lists rather than leaving scaffolding in published docs.
- Review the doc index advisories after noteworthy documentation changes to confirm there are no missing descriptions, missing headings, or duplicate slugs associated with the new work.

## Testing Discipline

- Target the focused pytest modules for the automation you touched (for example, `.repo_studios/tests/tests_producers/` when editing producers).
- Add regression tests when you introduce new behaviours or fix bugs so orchestrator runs and doc index refreshes remain stable.

<!-- markdownlint-enable MD013 -->
