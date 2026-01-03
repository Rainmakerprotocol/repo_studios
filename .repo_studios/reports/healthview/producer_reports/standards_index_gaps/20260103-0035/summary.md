<!-- markdownlint-disable MD013 -->

# Standards Index Gaps

Generated (UTC): 2026-01-03T00:35:50.105435+00:00
Index Path: C:\Users\genet\repo_studios\.repo_studios\scripts\repo_standards_index.yaml
Categories Path: C:\Users\genet\repo_studios\.repo_studios\scripts\.repo_studios\standards_categories.yaml

## Summary

- Total candidates: 69
- Sources with candidates: 6
- Top source candidate count: 18
- Sources scanned: 6

## Sources With Candidates

- **.repo_studios\docs\standards\global\std-global-code-cleanup.md** — 4 candidate(s)
  - L37: 8. Ensure each module, class, and function includes a clear and concise docstring.
  - L38: 9. Prefer in-place changes, but fully rewrite files if a logical restructuring results in clearer logic or better maintainability.
  - L39: 10. Use in-code annotations to explain why changes were made (to assist future agents).
  - L103: - Prefer small, focused diffs. Avoid touching unrelated files.
- **.repo_studios\docs\standards\global\std-global-html-coding.md** — 17 candidate(s)
  - L31: - Use semantic HTML5 tags ('&lt;header&gt;', '&lt;main&gt;', '&lt;footer&gt;', '&lt;nav&gt;', '&lt;section&gt;', '&lt;article&gt;', etc.).
  - L32: - Ensure every page includes:
  - L36: - Use one '&lt;h1&gt;' per page.
  - L42: - Use **kebab-case** for all 'id' and 'class' attributes:
  - L48: - Prefer reusable class names over inline styles.
  - ... (+12 more)
- **.repo_studios\docs\standards\global\std-global-markdown-authoring.md** — 18 candidate(s)
  - L47: - Use top-level headings ('#') to name the file purpose.
  - L48: - Use second-level headings ('##') for section groups (for example, '## Goals', '## File Summary', '## Agent Tasks').
  - L49: - Use third-level headings ('###') only when subdividing known sections.
  - L50: - Use bullet points or tables for enumerated items.
  - L51: - Avoid overloading a single section with too many nested points — prefer separation.
  - ... (+13 more)
- **.repo_studios\docs\standards\global\std-global-python-engineering.md** — 15 candidate(s)
  - L39: - Enforce Ruff formatting and linting ('ruff format', 'ruff check --fix') with repo configuration files.
  - L55: - Use data containers ('dataclasses.dataclass', 'typing.NamedTuple', or Pydantic models) for structured payloads.
  - L57: - Avoid circular imports by pushing integration glue to '__main__' or dedicated wiring modules.
  - L87: - Prefer 'async def' for FastAPI routes or I/O-heavy orchestrators.
  - L122: - Use the standard library 'logging' module; never use 'print()' in runtime paths.
  - ... (+10 more)
- **.repo_studios\docs\standards\project\std-project-operating-standard.md** — 8 candidate(s)
  - L25: Use this document as the single source of truth for how Repo Studios projects are structured, validated, and kept in sync with automation. The guidance applies to all code and documentation inside the project workspace unless an approved override exists in 'docs/standards/project/'.
  - L72: - Prefer installing Git hooks with 'make install-hooks' for anchor and slug hygiene.
  - L81: - Avoid global mutable state and hardcoded paths; rely on typed settings objects and dependency injection.
  - L104: Use these commands locally before opening pull requests to prevent CI churn.
  - L141: - ensure-commands-run: ["pytest", "ruff check", "mypy"]
  - ... (+3 more)
- **.repo_studios\docs\standards\project\std-project-python-instructions.md** — 7 candidate(s)
  - L25: Use this guide to prevent repeated mistakes, apply pre-approved solutions, and capture new recurring issues with precise remediation steps. Agents may append to this document when a new recurring issue emerges and a fix can be clearly defined.
  - L31: - Prefer Make targets for validation: 'make qa' (runs lint, type-check, tests).
  - L32: - Never hardcode secrets or tokens; read from environment variables such as 'METRICS_API_TOKEN' or 'INTERNAL_API_KEYS'.
  - L34: - Use 'api.server.get_db_path()' (or the injected dependency) instead of hardcoding database paths.
  - L58: * Use clear function or variable names (for example, 'convert_to_inches' not 'x').
  - ... (+2 more)

<!-- markdownlint-enable MD013 -->