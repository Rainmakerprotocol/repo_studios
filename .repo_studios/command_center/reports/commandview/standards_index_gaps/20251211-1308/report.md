<!-- markdownlint-disable MD013 -->

# Standards Index Gap Report

Generated (UTC): 2025-12-11T13:08:49.952960+00:00
Index Path: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\standards_index_reports\latest_index.yaml
Categories Path: C:\Users\genet\repo_studios\.repo_studios\scripts\.repo_studios\standards_categories.yaml

## Summary

- Total candidates: 24
- Sources with candidates: 6
- Top source candidate count: 6
- Sources scanned: 6

## Sources With Candidates

- **docs\standards\global\std-global-code-cleanup.md** — 3 candidate(s)
  - L32: never introduce regressions.
  - L33: - Prefer automated formatting and linting fixes as separate commits so behavioural changes remain easy to
  - L35: - Use repository utilities for repetitive edits (for example shared library helpers) to avoid diverging
- **docs\standards\global\std-global-markdown-authoring.md** — 5 candidate(s)
  - L32: - Ensure every substantive document includes at least one '##' subsection so the doc index can surface a meaningful table of contents.
  - L33: - Use descriptive, unique headings; when cloning a template, immediately rename sections to avoid duplicate slugs across the repository.
  - L44: - Use 'owner' to capture the accountable team or alias (for example, 'repo_studios_ai').
  - L50: - Ensure each file has only one top-level heading and organize subsections using '##'/'###' tiers for predictable anchors.
  - L52: - Prefer descriptive link text and repository-relative URLs to avoid rot when mirrors or forks consume the documentation.
- **docs\standards\global\std-global-monkey-patching.md** — 6 candidate(s)
  - L22: - Avoid patching Python builtins ('len', 'open', 'list', etc.) outside of tightly scoped, clearly documented tests.
  - L28: - Prefer dependency injection, protocol adapters, or feature flags before reaching for monkey patches; treat
  - L38: - Use 'pytest' fixtures to apply patches; avoid global state changes in module import time.
  - L39: - Ensure teardown phases restore original objects even when tests error; include 'addfinalizer' hooks for
  - L44: - Never ship monkey patches in production code paths without explicit sign-off from the service owner.
  - ... (+1 more)
- **docs\standards\global\std-global-python-engineering.md** — 6 candidate(s)
  - L22: - Prefer specific exception types ('ValueError', 'KeyError', etc.) over bare 'except:' clauses to avoid masking unexpected faults.
  - L24: - Use 'try' blocks narrowly and confine remediation logic to the smallest scope that meaningfully handles the error.
  - L29: - Ensure log messages include actionable fields such as correlation IDs, user identifiers, or feature flags when applicable.
  - L38: - Use fixtures to manage shared setup and prefer factory helpers over ad-hoc object construction in tests.
  - L42: - Pin dependencies in 'requirements.txt' or 'pyproject.toml' and document rationale for each addition in the
  - ... (+1 more)
- **docs\standards\project\std-project-operating-standard.md** — 1 candidate(s)
  - L27: - Document every new automation target or script addition in the repository Makefile and supporting docs to keep contributors informed.
- **docs\standards\project\std-project-python-instructions.md** — 3 candidate(s)
  - L21: - Use the repository-managed virtual environment ('.venv/') for local development and testing. Regenerate it after any dependency change.
  - L22: - Pin new dependencies in 'requirements.txt' or supporting lockfiles and document the reasoning in pull requests.
  - L28: - Ensure each doc adheres to the global markdown authoring standard: include front matter with 'owner', 'tags', and 'status', provide a single H1 with a descriptive summary paragraph, and add meaningful H2 sections for navigability.

<!-- markdownlint-enable MD013 -->