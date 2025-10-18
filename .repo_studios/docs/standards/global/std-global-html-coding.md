---
title: HTML Coding Practices
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.0.0
updated: 2025-08-22
summary: >-
  Enforceable HTML standards that ensure semantic structure, accessibility, and AI readiness across Repo Studios interfaces.
tags:
  - html
  - standards
  - accessibility
legacy_source: .repo_studios_legacy/repo_docs/copilot_standards_html.md
---

<!-- markdownlint-disable MD025 -->
# Repo Studios HTML Coding Practices
<!-- markdownlint-enable MD025 -->

Audience: Repo Studios | Agents | Developers | All

This document defines clear and enforceable HTML coding standards for Repo Studios automation and supporting AI agents. It ensures consistent structure, accessibility, and integration across HTML components used in Rainmaker, Chainlit, and other AI-powered systems.

## ✅ HTML Structure Best Practices

- Always begin with `<!DOCTYPE html>`.
- Use semantic HTML5 tags (`<header>`, `<main>`, `<footer>`, `<nav>`, `<section>`, `<article>`, etc.).
- Ensure every page includes:
  - `<html lang="en">`.
  - `<head>` with charset, viewport, and descriptive `<title>`.
  - `<meta>` tags for responsiveness, accessibility, and SEO.
- Use one `<h1>` per page.
- Follow heading hierarchy properly: `<h1>` → `<h2>` → `<h3>`.
- Group related elements inside containers like `<div>`, `<section>`, or `<fieldset>`.

## 🏷️ Naming & Class Conventions

- Use **kebab-case** for all `id` and `class` attributes:

```html
<div class="user-profile-card"></div>
```

- Prefer reusable class names over inline styles.
- Avoid vague class names (for example, `style1`, `x123`).

## 🎨 Styling & CSS

- Prefer Tailwind CSS or a shared utility layer for styling.
- Do not embed large `<style>` blocks inside HTML files.
- Avoid inline styles except for throwaway prototypes.
- Order utility classes layout → component → behavior (for example, `flex gap-2 border p-4 hover:shadow`).
- Apply custom styling through project-wide CSS or Tailwind extension files.

## ♿ Accessibility (A11Y)

- All interactive elements (buttons, links, form inputs) must have accessible labels (`aria-label`, `<label>`, `alt`, etc.).
- Forms must associate `<label>` with inputs using `for` and `id`.
- Use `role`, `aria-*`, and `tabindex` only when semantic tags do not provide the behavior.
- Avoid using color alone to convey meaning.
- Add `lang="en"` to the `<html>` tag and include metadata for screen readers.

## 🧠 AI & Agent Compatibility

- Wrap AI-generated UI sections in predictable containers (for example, `<div id="chat-panel">`, `<div class="ai-message-block">`).
- Use descriptive `id` attributes so agents can target elements for updates.
- Annotate complex UI blocks with HTML comments to explain structure for agents:

```html
<!-- Chat message history container (updated via Repo Studios state) -->
<div id="chat-history"></div>
```

- Avoid dynamic DOM structures that rely on unchecked JavaScript injection unless using a declared frontend framework.

## 💡 Common Layout Patterns

- Wrap pages in a responsive container (for example, `<div class="container mx-auto px-4">`).
- Use grid or flex layouts for columns and alignment.
- Avoid absolute positioning unless required.
- Use utility classes for spacing (`p-*`, `m-*`, `gap-*`, etc.).
- Group related inputs with `<form>`, `<fieldset>`, and `<legend>`.

## 🚫 Anti-Patterns to Avoid

- Inline `style=""` attributes.
- Empty or unclosed tags.
- Using `<br>` for spacing.
- Deeply nested anonymous `<div>` elements.
- Non-descriptive class names.
- Layouts that depend on fragile nesting.

## 🔁 Self-Improvement Protocol

- Review this standard before generating new HTML.
- When cleanup logs or reviews surface repeated issues:
  - Add the issue and corrected solution to this file using the established format.
  - Cross-reference supporting standards in Markdown or Python if helpful.

## ✅ Quick Checklists

### Shipping new HTML

- [ ] Start with semantic containers and a single `<h1>`.
- [ ] Ensure every interactive control has labels and keyboard focus support.
- [ ] Avoid inline styles; prefer Tailwind or shared utility classes.
- [ ] Document complex blocks with HTML comments so agents can target them.

### Reviewing or refactoring existing HTML

- [ ] Replace anonymous `<div>` stacks with semantic tags.
- [ ] Confirm accessibility metadata (`aria-*`, `role`, `lang`) remains accurate.
- [ ] Verify responsive behavior using container utilities and flex/grid layouts.
- [ ] Update related standards or inventory notes if new patterns emerge.

## 📚 References

- `.repo_studios/docs/standards/global/std-global-markdown-authoring.md`
- `.repo_studios/docs/standards/project/std-project-operating-standard.md`
- `.repo_studios/docs/playbooks/playbook-migration.md`

## 🤖 Agent Block (machine-readable)

````markdown
<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: html-validate-structure
      title: Validate HTML structure & a11y basics
      steps:
        - ensure-single-h1: true
        - check-lang-attribute: true
        - require-labelled-controls: true
        - forbid-inline-styles: true
      severity: warn
    - id: html-doc-anchor-scan
      title: Scan HTML standards doc for heading collisions
      steps:
        - run_anchor_health_optional: true
        - inspect_anchor_report_latest: true
      severity: info
```
<!-- agents:end:agent_instructions -->
````

## 🗂️ Change History

- 2025-10-18: Migrated into `.repo_studios/docs/standards/global/` with quick checklists and references.
- 2025-08-22: Initial Repo Studios-aligned revision of HTML coding standards.

## Anchor Health Cross-Link

If you introduce new top-level or second-level headings here, run `make anchor-health` and confirm no duplicate slug clusters were added. Use descriptive headings (for example, "AI HTML Accessibility Enforcement") to avoid collisions with other standards.
