---
title: repo Standards — HTML Coding Practices
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@docs-owners"]
status: approved
version: 1.0.0
updated_at: 2025-08-22
tags: [html, standards, ai-ingestion, agents]
related_files:
  - ./repo_standards_markdown.md
  - ./repo_standards_project.md
---

## 🧱 repo Standards — HTML Coding Practices

Audience: repo | Jarvis2 | Developer | All

This document defines clear and enforceable HTML coding standards for GitHub
repo and supporting AI agents. It ensures consistent structure,
accessibility, and front-end integration across all HTML components used in
Rainmaker, Jarvis2, and AI-powered systems.

These rules are designed to support:

* Semantic accuracy
* Accessibility (A11Y)
* Maintainable component structures
* Chainlit and AI-integrated UI elements

repo must treat this file as an active reference when generating or updating
HTML code.

---

## ✅ HTML Structure Best Practices

* Always begin with `<!DOCTYPE html>`
* Use semantic HTML5 tags (`<header>`, `<main>`, `<footer>`, `<nav>`,
  `<section>`, `<article>`, etc.)
* Ensure every page includes:

  * `<html lang="en">`
  * `<head>` with charset, viewport, and descriptive `<title>`
  * `<meta>` tags for responsiveness, accessibility, and SEO
* Use one `<h1>` per page
* Use heading hierarchy properly: `<h1>` → `<h2>` → `<h3>`, etc.
* Group related elements inside containers like `<div>`, `<section>`, or `<fieldset>`

---

## 🏷️ Naming & Classing Conventions

* Use **kebab-case** for all `id` and `class` attributes:

```html
<div class="user-profile-card"></div>
```
  
* Prefer reusable class names over inline styles
* Never use randomly generated or vague class names (e.g., `style1`, `x123`)

---

## 🎨 Styling & CSS

* Prefer Tailwind CSS for utility-first styling
* Never embed large `<style>` blocks inside HTML files
* Never use inline styles except for quick one-time prototypes
* Class stack order should follow layout → component → behavior (e.g., `flex
  gap-2 border p-4 hover:shadow`)
* Apply custom styling through a project-wide CSS or Tailwind extension file

---

## ♿ Accessibility (A11Y)

* All interactive elements (buttons, links, form inputs) must have accessible
  labels (`aria-label`, `<label>`, `alt`, etc.)
* Forms must associate `<label>` with inputs using the `for` and `id` attributes
* Use `role`, `aria-*`, and `tabindex` only when necessary and not semantically implied
* Avoid relying solely on color to convey meaning
* Add `lang="en"` to the `<html>` tag and include metadata for screen readers

---

## 🧠 AI & Agent Compatibility

* Wrap AI-generated UI sections in predictable containers (e.g., `<div
  id="chat-panel">`, `<div class="ai-message-block">`)
* Use clearly named `id` attributes to allow agents to target elements for
  updates or injection
* Annotate complex UI blocks with HTML comments to explain structure or logic
  for AI agents:

```html
<!-- Chat message history container (updated via Chainlit state) -->
<div id="chat-history"></div>
```

* Avoid dynamic DOM structures that rely on JavaScript injection unless using a
  declared frontend framework (React/Vue/etc.)

---

## 💡 Common Layout Patterns

* Always use a responsive container (e.g., `<div class="container mx-auto px-4">`)
* Use grid or flex layouts for columns and alignment
* Avoid absolute positioning unless required
* Use utility classes for spacing (`p-*`, `m-*`, `gap-*`, etc.)
* Use `<form>` with `<fieldset>` and `<legend>` to group related inputs

---

## 🚫 Anti-Patterns to Avoid

* Avoid inline `style=""`
* Do not leave empty tags or unclosed tags
* Do not rely on `<br>` for spacing
* Avoid deeply nested divs — use semantic wrappers
* Do not use non-descriptive class names
* Avoid excessive nesting that leads to layout instability

---

## 🔁 Self-Improvement Protocol

* repo should scan this file before generating new HTML
* If cleanup logs or human review surface a repeated bad pattern:

  * Add the issue and corrected solution to this file
  * Follow the format used in repo_studios_python.md

---

## 🤖 Agent Block (machine-readable)

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

---

By adhering to this document, repo ensures HTML is semantic, accessible,
AI-ready, and highly maintainable across the entire Rainmaker and Jarvis2 UI
ecosystem.

## Anchor Health Cross-Link

If you introduce new top-level or second-level headings here, run
`make anchor-health` and confirm no new duplicate slug clusters were added.
Use descriptive headings (e.g., "AI HTML Accessibility Enforcement") rather
than reusing generic titles already present in other standards.
