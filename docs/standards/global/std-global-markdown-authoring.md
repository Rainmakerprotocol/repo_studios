---
title: Global Markdown Authoring Standard
status: draft
version: 2025-10-23
last_updated: 2025-10-23
---

This stub captures markdown authoring expectations until the real documentation is synchronized.

## Front Matter

- Begin each standards document with a YAML front matter block that includes `title`, `status`, `version`, and `last_updated` for governance automation.
- Keep front matter keys lowercase and avoid custom key proliferation so downstream parsers remain stable.
- Update `last_updated` whenever you touch normative content to preserve a trustworthy audit trail.

## Style Essentials

- Ensure each file has only one top-level heading and organize subsections using `##`/`###` tiers for predictable anchors.
- Wrap lines at roughly 100 characters to improve diff readability in pull requests.
- Prefer descriptive link text and repository-relative URLs to avoid rot when mirrors or forks consume the documentation.
