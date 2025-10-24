# Standards Index Gap Report

Generated (UTC): 2025-10-22T12:05:27.540430+00:00
Index Path: C:\Users\genet\repo_studios\.repo_studios\scripts\repo_standards_index.yaml
Categories Path: C:\Users\genet\repo_studios\.repo_studios\scripts\.repo_studios\standards_categories.yaml

## Summary

- total candidates: 103
- sources with candidates: 10
- top source candidate count: 18

## Sources With Candidates

- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-chainlit-ui.md** — 15 candidate(s)
  - L34: Pin the Chainlit version in 'requirements-dev.txt' to avoid UI drift.
  - L60: - Use 'async def' and 'await' long-running calls (LLM, DB, HTTP).
  - L62: - Prefer 'cl.error()' for developer diagnostics during development.
  - L82: - Use explicit 'id' when you plan to update a message.
  - L83: - Prefer a single message that updates from "working" → final content.
  - ... (+10 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-code-cleanup.md** — 4 candidate(s)
  - L37: 8. Ensure each module, class, and function includes a clear and concise docstring.
  - L38: 9. Prefer in-place changes, but fully rewrite files if a logical restructuring results in clearer logic or better maintainability.
  - L39: 10. Use in-code annotations to explain why changes were made (to assist future agents).
  - L103: - Prefer small, focused diffs. Avoid touching unrelated files.
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-html-coding.md** — 17 candidate(s)
  - L31: - Use semantic HTML5 tags ('<header>', '<main>', '<footer>', '<nav>', '<section>', '<article>', etc.).
  - L32: - Ensure every page includes:
  - L36: - Use one '<h1>' per page.
  - L42: - Use **kebab-case** for all 'id' and 'class' attributes:
  - L48: - Prefer reusable class names over inline styles.
  - ... (+12 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-markdown-authoring.md** — 18 candidate(s)
  - L47: - Use top-level headings ('#') to name the file purpose.
  - L48: - Use second-level headings ('##') for section groups (for example, '## Goals', '## File Summary', '## Agent Tasks').
  - L49: - Use third-level headings ('###') only when subdividing known sections.
  - L50: - Use bullet points or tables for enumerated items.
  - L51: - Avoid overloading a single section with too many nested points — prefer separation.
  - ... (+13 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-mission-parameters.md** — 5 candidate(s)
  - L65: - Ensure high-quality, maintainable code.
  - L98: - Do not introduce secrets or make external network calls unless expressly requested.
  - L99: - Prefer incremental, reversible changes; avoid risky, repo-wide refactors without tests.
  - L120: - Use asterisk bullets for unordered lists.
  - L123: - Prefer idempotent, test-backed changes; document assumptions if any.
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-monkey-patching.md** — 6 candidate(s)
  - L41: - Prefer dependency injection, adapters, feature flags, or upstream fixes over monkey patches.
  - L52: - Use '--strict' to disable regex fallback and fail on parse errors for high signal.
  - L187: - ensure-inventory-entry: true
  - L188: - ensure-tests-cover: true
  - L189: - ensure-telemetry: {metrics: monkey_patch.activations, logger: true}
  - ... (+1 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-prompt-engineering.md** — 8 candidate(s)
  - L32: - Prefer structured, deterministic responses that downstream tooling can parse.
  - L41: - Use lightweight formatting (bullets, tables, YAML) unless richer output is required.
  - L59: - Prefer verifiable commands ('pytest', 'ruff', 'mypy') over prose claims.
  - L80: - Limit decomposition to the sections being modified.
  - L82: - Ensure each new module ships with unit tests, docstrings, and updated documentation.
  - ... (+3 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\global\std-global-python-engineering.md** — 15 candidate(s)
  - L39: - Enforce Ruff formatting and linting ('ruff format', 'ruff check --fix') with repo configuration files.
  - L55: - Use data containers ('dataclasses.dataclass', 'typing.NamedTuple', or Pydantic models) for structured payloads.
  - L57: - Avoid circular imports by pushing integration glue to '__main__' or dedicated wiring modules.
  - L87: - Prefer 'async def' for FastAPI routes or I/O-heavy orchestrators.
  - L122: - Use the standard library 'logging' module; never use 'print()' in runtime paths.
  - ... (+10 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\project\std-project-operating-standard.md** — 8 candidate(s)
  - L25: Use this document as the single source of truth for how Repo Studios projects are structured, validated, and kept in sync with automation. The guidance applies to all code and documentation inside the project workspace unless an approved override exists in 'docs/standards/project/'.
  - L72: - Prefer installing Git hooks with 'make install-hooks' for anchor and slug hygiene.
  - L81: - Avoid global mutable state and hardcoded paths; rely on typed settings objects and dependency injection.
  - L104: Use these commands locally before opening pull requests to prevent CI churn.
  - L141: - ensure-commands-run: ["pytest", "ruff check", "mypy"]
  - ... (+3 more)
- **C:\Users\genet\repo_studios\.repo_studios\docs\standards\project\std-project-python-instructions.md** — 7 candidate(s)
  - L25: Use this guide to prevent repeated mistakes, apply pre-approved solutions, and capture new recurring issues with precise remediation steps. Agents may append to this document when a new recurring issue emerges and a fix can be clearly defined.
  - L31: - Prefer Make targets for validation: 'make qa' (runs lint, type-check, tests).
  - L32: - Never hardcode secrets or tokens; read from environment variables such as 'METRICS_API_TOKEN' or 'INTERNAL_API_KEYS'.
  - L34: - Use 'api.server.get_db_path()' (or the injected dependency) instead of hardcoding database paths.
  - L58: * Use clear function or variable names (for example, 'convert_to_inches' not 'x').
  - ... (+2 more)

