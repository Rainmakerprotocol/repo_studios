---
title: Global JavaScript Engineering Standard
status: draft
version: 2025-11-06
last_updated: 2025-11-06
---

This interim reference captures the minimum JavaScript expectations until the full standard syncs from the documentation source of truth.

## Language & Syntax

- Target modern ECMAScript features that are supported by the current LTS browsers and Node runtimes; transpile only when a consumer truly requires older platforms.
- Prefer `const` and `let` over `var`; treat `const` as the default and reserve `let` for rebinding.
- Use strict equality (`===`/`!==`) to avoid coercion surprises; if coercion is intentional, document it with a short comment.
- Configure editors to auto-format with Prettier (or the repo’s canonical formatter) so indentation, trailing commas, and quote styles stay consistent across contributors.

## Modules & Imports

- Use ES modules (`import`/`export`) for all new code; CommonJS is allowed only when interoperating with legacy tooling that cannot consume ESM.
- Keep module boundaries shallow—avoid default exports for collections of unrelated helpers and prefer named exports to make refactors safer.
- When bundling for the browser, ensure tree-shaking works by exporting pure bindings and avoiding side effects at module top level beyond configuration constants.
- Resolve relative paths from the project root where possible; prefer alias maps (`@app/…`) over long `../../..` import chains to improve readability.

## Asynchrony & State

- Wrap asynchronous flows in `async`/`await` rather than nested `Promise` chains; surface errors with structured messages that include context (`operation`, `resource`, `id`).
- Guard shared mutable state behind dedicated modules or stores (Redux, Zustand, Vuex, etc.) and keep components stateless unless UI requirements dictate local state.
- Never ignore rejected promises—either `await` or attach `.catch()` with logging/metrics so observability pipelines capture failures.

## Testing & Tooling

- Co-locate unit tests near their modules (e.g., `module.test.ts` or `__tests__/module.spec.js`) and ensure coverage runs in CI.
- Exercise async utilities with fake timers or mocked fetches to avoid flakiness from real network calls.
- Enforce linting (ESLint with the repository config) before merging; treat lint warnings as failures to prevent gradual drift.
- Capture browser bundle sizes in monitoring dashboards when changes affect critical entry points; regressions over 5% require an explicit sign-off.

## Documentation & Comments

- Document exported functions and components with concise JSDoc/TSDoc blocks, including parameter and return descriptions plus noteworthy side effects.
- Prefer inline comments only for domain intent or non-obvious algorithms; avoid restating the code.
- Mirror notable runtime constraints in markdown design documents under `docs/` so automation can surface them during reviews.
