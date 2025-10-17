# Prompt Library

## Index

* session_primer — Kick off a local dev session with goals, constraints, quick context.
* quick_status — One-screen snapshot: goals/doing/next/decisions + validator status.
* propose_update — Propose a minimal memory change with safety plan.
* apply_update — Prepare a unified diff and apply via local scripts; validate and report.
* revert_last — Plan and verify a revert with reverse_patch vs backup_restore.
* investigate_failure — Triage a failed validation and propose precise fixes.
* archive_preview — Preview archive rotation and interpret counts.
* end_to_end_review — Review apply→validate→ledger→revert with artifacts and checksums.
* design_kickoff — Start a design doc skeleton (bullets-only).
* guardrails — Enforce local-only, safety, minimal diffs, style.
* after_coding_alignment — Summarize edits, gates, and next steps post-change.
* prioritize_next_steps — Select top 3 highest-ROI improvements.
* update_docs — Minimal doc/link touch-ups with excerpts.
* bundle_review — Compact review across related changes (diffs, docs, risks).
* bundle_memory_update — Plan→patch→apply→validate→ledger→fallback→report.
* bundle_archiving — Archive preview + doc index refresh + notes.
* bundle_design — Design kickoff + guardrails + exit criteria.
* bundle_post_code_align — Post-change alignment + docs + status snapshot.

---

## Atomic

## session_primer

You are operating locally only (no internet/CI). Begin by:

* Reading memory-bank purpose and current state via Make targets and scripts (do not invent commands).
* Printing a concise plan: goals, what you’ll check, what success looks like (2–4 bullets).
* Constraints: minimal diffs, bullets-first docs, adhere to style (no tabs, short lines).

Do next:

* Run memory summary (make memory-summary) and validators (make memory-validate-all) using the
  local tasks.
  Report:
  * Active goals, Doing, Next, and last 3 decisions (or (none)).
  * Final VALIDATION_STATUS and VALIDATION_JSON lines verbatim.
* List any obvious safe wins (max 3), each mapped to a file or script.

## quick_status

Produce a one-screen status:

* Active Goals (up to 5); Doing (up to 5); Next (up to 5); last 3 decisions.
* Tail the validator output to show:
  * VALIDATION_STATUS: ...
  * VALIDATION_JSON: {...}
* If WARN or FAIL present, list root cause lines (max 5) and suggest a minimal fix per line.

## propose_update

Propose a minimal, safe memory-bank update:

* Scope: which file(s), what small change (bullets or table row), and why.
* Deliver a unified diff (unified format) ready for apply_update.sh.
* Safety plan: expected validator impact, rollback plan (revert_last.sh), and ledger fields expected.

## apply_update

Apply a local patch safely:

* Inputs: EDIT_ID, PATH_TO_PATCH (unified diff).
* Steps:
  * Run scripts/memory_update/apply_update.sh EDIT_ID PATH_TO_PATCH (local).
  * Then run make memory-validate-all; capture and print:
    * VALIDATION_STATUS and VALIDATION_JSON lines.
  * Read the last ledger line from memory-bank/backups/manifest.log.jsonl;
    report outcome and artifacts (if any).
* Success criteria: outcome=commit|ok and STATUS=PASS; else describe auto-rollback and next actions.

## revert_last

Plan and verify a revert:

* Run scripts/memory_update/revert_last.sh EDIT_ID (local).
* Report the last ledger revert entry with:
  * action=revert, outcome=ok|warn, revert_method=reverse_patch|backup_restore.
* Confirm presence/absence of .rej/.orig artifacts and checksum verification vs backup
  manifest; state if fallback occurred.

## investigate_failure

Triage a validation failure:

* Parse validator output and extract failing checks (files, headers, schema, style, coherence).
* Propose precise, minimal edits (bullets or table rows) to resolve each failure.
* If .orig files present: explain STRICT=1 behavior (FAIL) vs default (WARN) and recommend
  cleanup or strict gate intent.

## archive_preview

Run and interpret preview:

* Use make memory-archive (echo-only) and report:
  * Would-create dirs/files, counts (Done items, decisions rows, goals), and the “Last rotated” line.
* Call out zero counts vs non-empty sections as a note (not a failure).
* No file writes in preview.

## end_to_end_review

Summarize the full flow:

* Apply flow: backup dir layout (files, SHA256SUMS.txt, manifest.json),
  forward/reverse patches, ledger fields.
* Post-apply validation and auto-rollback on failure; artifacts capture (.rej/.orig).
* Revert flow: reverse_patch success criteria (no artifacts + checksum match),
  fallback to backup_restore, revert_method recorded.
* Durability: fsync for files and parent directories on ledger/manifest/sums.

## design_kickoff

Start a design doc skeleton (bullets-only):

* Problem statement (1–2 bullets)
* Goals / Non-goals
* Risks / Tradeoffs
* Interfaces / Files touched
* Test strategy (happy + 1–2 edge)
* Rollback plan (if applicable)

## guardrails

Operational constraints for this repo:

* Local-only; no network/CI; no secrets.
* Minimal diffs; bullets-first docs; no tabs; wrap long lines; avoid broad refactors.
* Prefer Make targets and provided scripts; do not invent file paths or commands—verify before use.
* Always report VALIDATION_STATUS and VALIDATION_JSON; on failures, propose concrete, small fixes.

## after_coding_alignment

Post-change alignment:

* Files changed, why, and the smallest verifiable impact summary.
* Quality gates: Build (N/A for docs), Lint/Typecheck (PASS/FAIL if applicable),
  Unit tests (if run), Validator status lines.
* If any WARN/FAIL remains, list next micro-fixes (max 3) with exact file anchors.

## prioritize_next_steps

Pick the top 3 ROI steps:

* Each with: goal, file/script, and expected validator/ops benefit.
* Prefer steps that reduce risk, improve reversibility, or clarify operator UX.

## update_docs

Minimal doc touch-ups:

* Scope: add cross-links or one-liners; do not rewrite content.
* Show before→after excerpts (first and last new bullet).
* Keep under 10 lines changed per file; ensure no tabs and reasonable line length.

---

## Bundle

## bundle_review

Do a compact review of a local change set:

* Summarize what changed (files, scripts, Make targets), why it matters
  (risk↓, observability↑), and how to verify.
* Quote key log/ledger lines (short excerpts).
* List 2–3 small, safe follow-ups.

## bundle_memory_update

Plan→patch→apply→validate→fallback→report, end-to-end (local-only):

* Propose minimal patch + unified diff.
* Apply via scripts/memory_update/apply_update.sh EDIT_ID PATH_TO_PATCH.
* Validate; print final lines exactly:

```text
VALIDATION_STATUS: ...
VALIDATION_JSON: {"status":"...","files":N,"errors":E,"warns":W}
```

* If artifacts or FAIL: confirm auto-rollback and list artifacts.
* Revert path: run revert_last.sh; report revert_method and checksum verification result.

## bundle_archiving

Archive preview + doc index:

* Run make memory-archive; summarize would-be actions and counts.
* Ensure memory-bank/README.md links to SCHEMA.md, UPDATE_PROTOCOL.md, ARCHIVE_POLICY.md, ARCHIVE_INDEX.md.
* Confirm “## Archives” footers in active files point to ARCHIVE_INDEX.md.

## bundle_design

Design kickoff with guardrails:

* Generate bullets-only design doc per design_kickoff.
* Restate guardrails (local-only, minimal diffs, validators observed).
* Provide exit criteria and a tiny test plan.

## bundle_post_code_align

After-code alignment:

* Summarize edits and outcomes (ledger lines + validator lines).
* Touch docs minimally (cross-links, one-liners).
* Run quick_status; list any remaining WARNs and 1–2 fixes.

---

Notes

* All prompts assume local-only execution using existing Make targets and scripts.
* Always include the final two lines from validation runs:

```text
VALIDATION_STATUS: ...
VALIDATION_JSON: {"status":"...","files":N,"errors":E,"warns":W}
```
