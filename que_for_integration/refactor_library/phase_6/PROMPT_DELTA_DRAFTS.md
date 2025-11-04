# Phase 6 Prompt Instruction Delta Drafts (2025-11-04)

## `session_primer`

- **Add Before Command Steps:**
  - “Review `.repo_studios/command_center/README.md` guardrail section before running any scripts.”
  - “Confirm run lock status via `make command-center-check-locks` (or documented fallback) before planning work.”
- **Add After Plan Block:**
  - “Record intended guardrail evidence (duplicate scan path, manifest output) in the session notes for later reconciliation.”

## `guardrails`

- **Guardrail Expansion:**
  - Insert bullets referencing command center guardrails: run lock existence, `max_files_per_run`, and retention policy (keep=3) with pointer to guardrail doc.
  - Append reminder to consult Phase 5 Make targets or PowerShell fallback when orchestrating duplicate remediation.

## `update_docs`

- **Cross-Link Requirement:**
  - Require checking `.repo_studios/command_center/README.md#documentation-updates` before editing docs related to automation or duplicate remediation.
  - Add reminder to note doc touch-ups in `memory-bank/decisionLog.md` when they influence guardrails or protocols.

## `bundle_review`

- **Evidence Attachment:**
  - Add explicit steps to attach duplicate scan matrices, automation manifest, and metrics summary when reviewing refactor bundles.
  - Prompt reviewer to verify guardrail compliance (locks, keep count) via command center helpers.

## `after_coding_alignment`

- **Guardrail Confirmation Step:**
  - Insert verification of guardrail artifacts (manifest, metrics summary, duplicate matrix) and run lock status.
  - Direct user to cite command center README section for any follow-up remediation.

## `bundle_post_code_align`

- **Protocol Pointer:**
  - At start, instruct user to cross-reference command center README for guardrail checklist and validation cadence.
  - Add action to log changes and guardrail evidence in decision log using prompt key reference.

## General Prompt Library Notes

- Include banner note near library header referencing Phase 6 change log once updates land.
- Schedule validation dry-run prompts (“example conversation transcripts”) once deltas are accepted.
