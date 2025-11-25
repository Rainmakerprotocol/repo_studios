---
title: Global Python Engineering Standard
status: draft
version: 2025-10-23
last_updated: 2025-10-23
---

<!-- markdownlint-disable MD013 -->

This lightweight reference captures the minimum Python engineering expectations until the full standard is migrated.

## Error Handling

- Prefer specific exception types (`ValueError`, `KeyError`, etc.) over bare `except:` clauses to avoid masking unexpected faults.
- Log or re-raise exceptions with contextual details so operational tooling can trace failures.
- Use `try` blocks narrowly and confine remediation logic to the smallest scope that meaningfully handles the error.

## Logging

- Adopt structured logging (for example the `logging` module with contextual extras) instead of `print` statements for runtime diagnostics.
- Ensure log messages include actionable fields such as correlation IDs, user identifiers, or feature flags when applicable.
- Configure log levels sensibly—reserve `ERROR` for actionable issues and use `INFO`/`DEBUG` for normal flow insights.

<!-- markdownlint-enable MD013 -->
