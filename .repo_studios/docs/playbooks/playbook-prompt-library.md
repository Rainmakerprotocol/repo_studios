---
title: Repo Studios Prompt Library Playbook
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.1.0
updated: 2025-10-18
summary: >-
  Guidance for selecting, updating, and governing prompts from the Repo Studios shared library.
tags:
  - prompts
  - playbook
  - ai-ingestion
legacy_source: .repo_studios_legacy/repo_docs/PROMPT_LIBRARY_USAGE.md
---

# Repo Studios Prompt Library Playbook

Audience: Repo Studios automation | Human collaborators

This playbook standardizes how we reference and update the shared prompt library now that the workspace has migrated to the `.repo_studios/` structure.

---

## Core Rules

- Use `repo_prompts.md` at the repository root as the single source of truth.
- For status/update/review/design requests, map the ask to an Atomic or Bundle prompt and paste the full prompt text without modification.
- When choices are ambiguous, list 2–3 candidate prompts with their one-line descriptions, then ask the requester to choose.
- Never invent new prompt text outside the library; propose additions by editing `repo_prompts.md` directly.

---

## Workflow Checklist

1. Locate the prompt by key or section heading in `repo_prompts.md`.
2. Copy the entire prompt body verbatim for reuse.
3. After responding, log the prompt key in context notes or agent logs when relevant.
4. If a new scenario emerges, draft the proposal in `repo_prompts.md`, mark it as pending review, and notify owners.

---

## Updating Prompts

- Keep canonical keys and anchors stable unless the prompt intent changes. Deprecate old keys explicitly when replacing intent.
- Validate heading uniqueness by running `make anchor-health` and reviewing `.repo_studios/anchor_health/anchor_report_latest.json`.
- Run `python .repo_studios/scripts/check_markdown_anchors.py` on the library file when modifying headings or anchors.
- Re-run dependent flows/tests that rely on deterministic prompt strings before merging.

---

## Reference Commands

```bash
grep -n "^##" repo_prompts.md              # list prompt headings
python .repo_studios/scripts/check_markdown_anchors.py repo_prompts.md
make anchor-health                            # generate duplicate slug report
```

---

## Governance Notes

- Maintain Markdown hygiene to align with `std-global-markdown-authoring.md`.
- Log substantial prompt changes in `memory-bank/decisionLog.md` with rationale and impacted flows.
- Link prompt updates to the mission parameters or project operating standard when scope changes.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: prompt-library-usage
      title: Use prompt library correctly
      steps:
        - select-from-file: repo_prompts.md
        - copy-verbatim: true
        - list-candidates-when-ambiguous: 3
        - run-anchor-check: make anchor-health
        - log-change: memory-bank/decisionLog.md
```
<!-- agents:end:agent_instructions -->
