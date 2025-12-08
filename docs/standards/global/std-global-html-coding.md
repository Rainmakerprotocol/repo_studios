---
title: Global HTML Coding Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_web
tags:
	- html
	- frontend
	- accessibility
---

<!-- markdownlint-disable MD013 -->

# Global HTML Coding Standard

This standard captures Repo Studios HTML conventions to guarantee accessible, maintainable markup across
static docs and UI surfaces.

## Structural Conventions

- Prefer semantic elements (`<section>`, `<article>`, `<nav>`, `<header>`) rather than nested `<div>` blocks to
	retain screen-reader navigability.
- Keep heading levels sequential and ensure each page has a single `<h1>` for predictable anchor indexing.
- Co-locate ARIA landmarks with the relevant semantic element instead of adding redundant roles.

## Authoring Practices

- Wrap prose at ~100 characters when authoring raw HTML files to maintain diff readability alongside
	templated content.
- Use repository build tooling to inject repeated snippets (headers, footers) rather than duplicating markup
	across pages.
- Place inline scripts at the bottom of the body or mark them with `defer` to avoid blocking first paint.

## Accessibility Requirements

- Provide descriptive `alt` text for images; when conveying complex data use `<figure>` plus a textual summary
	or link to structured data.
- Ensure interactive controls expose `aria-label` or `aria-labelledby` attributes and respond to keyboard
	events (`keydown`, `keyup`).
- Use colour palettes that meet WCAG 2.1 AA contrast ratios; validate using automated tooling before merge.

## Testing & Validation

- Run the shared HTML lint task (`make lint-html`) prior to submitting a PR; resolve warnings instead of
	suppressing them.
- Validate significant layout changes in the latest Chromium and Firefox releases, plus the baseline mobile
	viewport referenced in QA checklists.
- When embedding third-party widgets, sandbox them in an iframe and document their update cadence in the
	relevant runbook.

<!-- markdownlint-enable MD013 -->
