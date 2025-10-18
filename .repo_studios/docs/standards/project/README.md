# Project Standards Catalog

Last updated: 2025-10-18

Use this directory for repository-specific adaptations of the global standards. These documents capture local exceptions, tailored workflows, and experiment notes.

## Metadata Header

Every project standard should begin with the YAML header below so downstream tooling can surface ownership and review cadence:

```yaml
---
title: <Document Title>
version: 0.1.0
updated: 2025-10-18
upstream: ../global/std-global-<slug>.md
owners:
  - <team-or-individual>
review_cycle: quarterly
summary: >-
  Brief explanation of what differs from the global standard.
---
```

## Authoring Guidelines

- Prefix filenames with `std-project-` followed by a short slug (e.g., `std-project-api-guidance.md`).
- Document the rationale for each divergence in a `## Variations` section.
- Reference automation or CI hooks that enforce the override so maintenance stays traceable.

## Migration Notes

As legacy material is modernized, link back to its source in `.repo_studios_legacy/` and note any open tasks for full alignment.
