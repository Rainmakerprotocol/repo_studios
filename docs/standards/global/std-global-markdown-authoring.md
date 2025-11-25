---
title: Global Markdown Authoring Standard
status: draft
version: 2025-11-25
last_updated: 2025-11-25
---

<!-- markdownlint-disable MD013 -->

This standard captures markdown authoring expectations until the long-form documentation is synchronized.

## Front Matter

- Begin each document with a YAML front matter block that includes `title`, `status`, `version`, `last_updated`, `owner`, and `tags` so automation can surface owners and topical filters directly from the doc index.
- Keep keys lowercase and reuse existing names before adding new ones to keep downstream parsers stable.
- Represent dates using ISO 8601 strings and ensure values remain JSON serialisable so doc index exports stay machine readable.
- Update `last_updated` whenever you touch normative content to preserve a trustworthy audit trail that aligns with repo history.

## Document Placement

- Author normative content under `docs/` or `.repo_studios/docs/` unless a playbook explicitly requires a different location; files elsewhere inflate the doc index “outside docs tree” advisory.
- Co-locate generated artifacts with their source markdown when historical retention is required, but keep operator guidance inside the governed docs tree.

## Headings & Outline

- Provide exactly one `#` heading after front matter and avoid disabling rules that enforce the lead heading.
- Ensure every substantive document includes at least one `##` subsection so the doc index can surface a meaningful table of contents.
- Use descriptive, unique headings; when cloning a template, immediately rename sections to avoid duplicate slugs across the repository.
- Replace placeholder headings with actionable TODO statements rather than “Placeholder” or similar filler text.

## Lead Summary Paragraph

- Follow the lead heading with a concise paragraph (roughly 150–250 characters) that explains the document’s intent—the doc index records this snippet as the canonical description.
- When importing legacy docs, add the summary paragraph before deeper edits so indexing remains useful during remediation.

## Metadata Hygiene

- Populate `tags` with 3–7 lower-case keywords (`standards`, `ai-ingestion`, `playbook`, etc.) so inventory searches stay consistent.
- Use `owner` to capture the accountable team or alias (for example, `repo_studios_ai`).
- Set `status` to `draft`, `review`, or `live` to align with command center reporting.
- Remove placeholder copy (`TODO`, `TBD`, “fill in later”) before publishing; scaffolding skews placeholder advisories in the doc index.

## Style Essentials

- Ensure each file has only one top-level heading and organize subsections using `##`/`###` tiers for predictable anchors.
- Wrap lines at roughly 100 characters to improve diff readability in pull requests.
- Prefer descriptive link text and repository-relative URLs to avoid rot when mirrors or forks consume the documentation.

## Cross-Document Consistency

- Reuse canonical terminology from command center playbooks to minimise duplicate content and conflicting slugs.
- Before opening a documentation PR, review the latest doc index advisories and resolve missing descriptions, absent H2 sections, and duplicate slugs where applicable.

<!-- markdownlint-enable MD013 -->
