---
title: "DB Integrations"
audience: [Developers, Copilot, Agents]
role: [Reference]
owners: [repo_studios_ai]
status: "active"
version: "1.0"
updated_at: "2025-12-16"
tags: [db, integrations, command_center]
related_files:
  - "../../.repo_studios/command_center/docs/db_integrations"
---

# DB Integrations

## Goals

- Provide a stable entry point for DB integration mapping docs.
- Point to the authoritative Command Center integration specs.

## System Context

DB integration documents live under the Command Center documentation tree so they stay close to the report-writing code that owns the database dual-write scaffolding.

Authoritative location:
- [../../.repo_studios/command_center/docs/db_integrations/](../../.repo_studios/command_center/docs/db_integrations/)

## Reference Docs

- [Analyze standards index gaps](../../.repo_studios/command_center/docs/db_integrations/db_integration_analyze_standards_index_gaps.md)
- [Analyze test hardening](../../.repo_studios/command_center/docs/db_integrations/db_integration_analyze_test_hardening.md)
- [Check inventory health](../../.repo_studios/command_center/docs/db_integrations/db_integration_check_inventory_health.md)
- [Collect faulthandler reports](../../.repo_studios/command_center/docs/db_integrations/db_integration_collect_faulthandler_reports.md)
- [Fault diagnostics overview orchestrator](../../.repo_studios/command_center/docs/db_integrations/db_integration_fault_diagnostics_overview_orchestrator.md)
- [Diff standards index](../../.repo_studios/command_center/docs/db_integrations/db_integration_diff_standards_index.md)
- [Test log reports](../../.repo_studios/command_center/docs/db_integrations/db_integration_test_log_reports.md)

## Agent Instructions

- When adding a new DB integration mapping doc, follow the template at
  [../../.repo_studios/command_center/docs/db_integration_template.md](../../.repo_studios/command_center/docs/db_integration_template.md).
- Keep integration docs in the Command Center folder unless a repo-wide convention changes.

## Update Log

- 2025-12-16 — Added repo-root index for DB integration docs.
