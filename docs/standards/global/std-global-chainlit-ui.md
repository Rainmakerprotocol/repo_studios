---
title: Global Chainlit UI Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ai
tags:
	- chainlit
	- ui
	- accessibility
---

<!-- markdownlint-disable MD013 -->

# Global Chainlit UI Standard

This document outlines the baseline experience guidelines for Repo Studios Chainlit applications so agents
deliver consistent, accessible workflows.

## Layout & Navigation

- Keep primary actions visible within the first viewport; avoid scrolling to complete critical task flows.
- Use consistent panel ordering (context → controls → results) so operators can rely on muscle memory.
- Provide breadcrumb-like headers when branching to secondary views and offer a "Back to task" affordance.

## Visual Design

- Follow the shared design tokens (spacing, typography, colour palette) defined in the frontend library to
	retain parity with the wider Control Tower UI.
- Communicate live states using text plus iconography; colour alone must not indicate status.
- Present long-running operations with progress indicators and estimated completion messaging to prevent
	duplicate submissions.

## Accessibility & Internationalisation

- Ensure every interactive element has an accessible name and keyboard focus order matches visual order.
- Provide text alternatives for generated images or charts and expose raw data through downloadable assets
	when possible.
- Avoid hard-coding locale-specific strings; pull copy from the shared i18n bundle so localisation can be
	applied without code changes.

## Error Handling

- Display actionable error states inline with remediation steps or retry options; surface correlation IDs for
	operational diagnostics.
- Log structured error payloads via the automation logging helper so incidents can be traced after the fact.
- When third-party APIs fail, summarise the upstream status and link to the relevant runbook entry.

<!-- markdownlint-enable MD013 -->
