# Global Standards Catalog

Last updated: 2025-10-18

Use this folder for organization-wide standards that apply to every Repo Studios integration. Each document should include the metadata block below at the top of the file to clarify stewardship and versioning.

```yaml
---
title: <Document Title>
version: 0.1.0
updated: 2025-10-18
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
summary: >-
  One to two sentences describing the purpose of the standard.
---
```

## Authoring Guidelines

- Keep filenames prefixed with `std-global-` followed by a concise slug, for example `std-global-governance.md`.
- Link to related project overrides using relative paths (e.g., `../project/std-project-foo.md`).
- Capture decision history in a `## Changelog` section using reverse chronological order.

## Migration Notes

Most existing standards still reside in `.repo_studios_legacy/repo_docs/`. Copy relevant content into this directory as you modernize the guidance, leaving the legacy copy untouched for provenance.
