---
title: Global CSS Authoring Standard
status: draft
version: 2025-11-06
last_updated: 2025-11-06
---

This interim reference captures Cascading Style Sheets expectations until the canonical design system handbook is synchronized.

## Source Structure

- Organise styles by feature or component rather than by selector type; prefer folders that mirror the UI architecture so deletion and refactors stay safe.
- Use modern CSS features (custom properties, cascade layers, nested syntax via tooling) when supported by the target browser matrix; provide fallbacks only when metrics show meaningful audiences on legacy platforms.
- Keep files small (<500 lines) and split large rule sets into partials so merge conflicts remain manageable.

## Naming & Specificity

- Adopt a class naming pattern that matches the active design system (e.g., BEM or utility-first). Do not mix competing conventions within the same feature.
- Favour low-specificity selectors (single class) and avoid `!important`; when specificity escalates, leave a comment that explains the constraint and plan to unwind it.
- Prefer custom properties for theme values (color, spacing, typography) and group them near the root scopes that consume them.

## Performance & Accessibility

- Minimise layout thrashing by batching transitions and animating transform/opacity rather than width/height when practical.
- Guard prefers-reduced-motion variants for all non-trivial animations and ensure colour choices meet WCAG AA contrast ratios.
- Use logical properties (`margin-inline`, `padding-block`) to support internationalisation and writing-mode changes by default.

## Tooling & Delivery

- Enforce linting (Stylelint or the repo’s canonical alternative) in CI; treat warnings as failures to avoid gradual drift.
- When bundling CSS, enable minification and purge tooling tailored to the component frameworks in use to avoid shipping unused selectors.
- Version design tokens alongside CSS changes and document breaking token updates in the changelog so downstream packs can sync safely.

## Documentation

- Capture component-level style decisions (layout strategies, breakpoints, motion guidance) in design notes stored under `docs/` so reviewers understand intent.
- Reference the relevant accessibility findings or Figma specs when introducing bespoke interactions.
- Annotate complex responsive rules with terse comments describing the breakpoint logic or constraints they satisfy.
