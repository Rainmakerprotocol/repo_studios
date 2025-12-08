---
title: Global Python Engineering Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ai
tags:
  - python
  - engineering
  - automation
---

<!-- markdownlint-disable MD013 -->

# Global Python Engineering Standard

This lightweight reference captures the minimum Python engineering expectations until the full standard is
migrated.

## Error Handling

- Prefer specific exception types (`ValueError`, `KeyError`, etc.) over bare `except:` clauses to avoid masking unexpected faults.
- Log or re-raise exceptions with contextual details so operational tooling can trace failures.
- Use `try` blocks narrowly and confine remediation logic to the smallest scope that meaningfully handles the error.

## Logging

- Adopt structured logging (for example the `logging` module with contextual extras) instead of `print` statements for runtime diagnostics.
- Ensure log messages include actionable fields such as correlation IDs, user identifiers, or feature flags when applicable.
- Configure log levels sensibly—reserve `ERROR` for actionable issues and use `INFO`/`DEBUG` for normal flow insights.

## Testing Discipline

- Write unit tests for new code paths and regression tests for bug fixes; keep tests deterministic and
  isolated from external services.
- Run `pytest` with the repository-managed configuration before raising a pull request and ensure coverage
  does not drop for critical modules.
- Use fixtures to manage shared setup and prefer factory helpers over ad-hoc object construction in tests.

## Packaging & Dependencies

- Pin dependencies in `requirements.txt` or `pyproject.toml` and document rationale for each addition in the
  pull request summary.
- Avoid transitive imports from application entry points; import only what you use to keep import graphs
  shallow and type-check friendly.
- When publishing internal packages, follow semantic versioning and update changelogs before release.

<!-- markdownlint-enable MD013 -->
