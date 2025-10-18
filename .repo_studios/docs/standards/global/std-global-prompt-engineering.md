---
title: Repo Studios Prompt Engineering Standards
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: needs_review
version: 0.3.0
updated: 2025-10-18
summary: >-
  Operational guidance for designing prompts and agent instructions used across Repo Studios projects.
tags:
  - prompts
  - standards
  - ai-ingestion
legacy_source: .repo_studios_legacy/repo_docs/copilot_prompt_engineering_standards.md
---

<!-- markdownlint-disable MD025 -->
# Repo Studios Prompt Engineering Standards
<!-- markdownlint-enable MD025 -->

These standards provide reusable guardrails for prompts, agent instructions, and automation hand-offs. Apply them whenever you write or refresh Repo Studios guidance.

---

## Purpose

- Ground prompts in real repository context and explicit requirements.
- Prefer structured, deterministic responses that downstream tooling can parse.
- Capture acceptance criteria so maintainers can judge success quickly.

---

## Core Principles

- Phrase requests with concrete scope, inputs, and success criteria.
- Declare assumptions or ask for clarification instead of guessing.
- Use lightweight formatting (bullets, tables, YAML) unless richer output is required.
- Preserve task history by linking to relevant `agent_notes/` entries.

---

## Prompt Patterns

- **Command prompts**: start with an actionable verb, specify target files or modules, and include a "Done when" checklist.
- **Diagnostic prompts**: request minimal repro steps, logs, and the next action.
- **Generation prompts**: describe interfaces, constraints, and test expectations; list precise file destinations.
- **Refactor prompts**: note invariants, edge cases, before/after behavior, and required tests.

---

## Validation Practices

- Attach quick contracts (inputs, outputs, error modes) for code-related tasks.
- Include at least one happy path and one edge case when asking for tests.
- Prefer verifiable commands (`pytest`, `ruff`, `mypy`) over prose claims.
- Record validation expectations in trailing bullet lists so they are copyable into checklists.

---

## File Decomposition Policy

### Complexity Thresholds

Decompose or extract code into new modules when any of the following thresholds are exceeded for the area under change:

- File > 1000 lines of code.

- More than 12 function or class definitions.

- Cyclomatic complexity > 15 for the function under review.

- Nesting depth greater than 3 levels.

### Decomposition Steps

- Limit decomposition to the sections being modified.
- Create dedicated modules for the extracted logic (for example `cache/negative_cache.py`).
- Ensure each new module ships with unit tests, docstrings, and updated documentation.
- Log the operation in `agent_notes/` (timestamped entry) noting file splits, new paths, tests added, and docs touched.

---

## Machine-Readable Contract Example

```yaml
contract:
  inputs: ["path/to/file.py", "flag:bool"]
  outputs: ["diff", "tests"]
  done_when:
    - tests: pass
    - lint: clean
    - typecheck: clean
```

---

## Quick Checklists

### Drafting a new prompt

- [ ] Establish context, scope, and explicit success criteria.
- [ ] Provide structure (bullets, tables, YAML) that downstream tools can parse.
- [ ] Include validation commands or expectations.
- [ ] Cross-link to related standards, playbooks, or inventory entries.

### Reviewing an existing prompt

- [ ] Confirm assumptions are stated or unanswered questions are surfaced.
- [ ] Ensure machine-readable blocks line up with the latest repo schema.
- [ ] Verify acceptance criteria reflect current CI and validation commands.
- [ ] Update `repo_prompts.md` or the prompt library playbook when reusable patterns emerge.

---

## Anti-Patterns

- Prompting without repository context or explicit file paths.
- Omitting success criteria or verification steps.
- Using free-form paragraphs when structured output is required.
- Mixing multiple distinct tasks into a single prompt without checklist separation.
- Leaving legacy agent names (`repo`, `Jarvis2`) without clarifying modern equivalents.

---

## References

- `repo_prompts.md`
- `.repo_studios/docs/playbooks/playbook-prompt-library.md`
- `.repo_studios/docs/standards/project/std-project-operating-standard.md`

---

## Anchor Health Reminder

When adjusting headings or adding new sections, run `make anchor-health` and review `.repo_studios/anchor_health/anchor_report_latest.json` for duplicate slug regressions.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->

```yaml

agents:

  tasks:

    - id: prompt-validate-structure

      title: Validate prompt structure and contracts

      steps:

        - ensure-context: true

        - ensure-acceptance-criteria: true

        - ensure-structured-output: true

      severity: warn

    - id: prompt-library-sync

      title: Sync prompt with shared library

      steps:

        - update-repo-prompts: true

        - log-agent-notes: true

      severity: info

```

<!-- agents:end:agent_instructions -->

---

## Change History

- 2025-10-18: Migrated to `.repo_studios/docs/standards/global/` with expanded metadata and checklists.

- 2025-09-04: Initial draft captured in legacy repo standards.

