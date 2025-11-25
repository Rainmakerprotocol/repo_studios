---
title: Global Monkey Patching Standard
status: draft
version: 2025-10-23
last_updated: 2025-10-23
---

<!-- markdownlint-disable MD013 -->

Placeholder content describing acceptable monkey patch usage. Update with official guidelines when the source document is available.

## Builtin Constraints

- Avoid patching Python builtins (`len`, `open`, `list`, etc.) outside of tightly scoped, clearly documented tests.
- When a patch is unavoidable, wrap it in fixtures or context managers that guarantee timely teardown.
- Record rationale and risk mitigation steps in the pull request description so future contributors understand the trade-offs.

<!-- markdownlint-enable MD013 -->
