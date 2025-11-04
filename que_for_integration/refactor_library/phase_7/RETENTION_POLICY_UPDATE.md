# Phase 7 Retention Policy Update (Draft 2025-11-04)

## Objectives

- Extend existing guardrail retention (keep=3 with `.keep` override) to cover remediation run folders, automation bundles, and checklists.
- Prevent repository bloat while preserving audit trails required for governance and validation.

## Current State

| Artifact Type | Location | Current Policy | Gap |
| --- | --- | --- | --- |
| Duplicate scan outputs | `.repo_studios/command_center/reports/.../scripts_duplicate_matrix-*.json` | Keep latest 3 per target via helper | Need explicit cleanup cadence documentation |
| Automation bundles | `.repo_studios/command_center/reports/.../automation_manifest-*/` | Retention handled manually | Requires scripted pruning + `.keep` respect |
| Run logs/checklists | `.repo_studios/command_center/checklists/` | No pruning | Risk of uncontrolled growth |
| Validation transcripts | `phase_6/validation_runs/` | Manual archive | Define archival cadence (e.g., keep latest 2 per prompt version) |

## Proposed Policy

| Artifact Type | Retention Rule | Implementation Notes |
| --- | --- | --- |
| Duplicate scan outputs | Keep latest 3 timestamped directories; delete older unless `.keep` present. | Extend `write_report_artifacts` helper to enforce across producers; document in README. |
| Automation bundles | Keep latest 2 dry-run bundles per target + any with `.keep`; archive older to `phase_4/archive/`. | Add pruning step to automation manifest CLI post-run. |
| Run logs/checklists | Keep most recent 6 weeks of daily checklists; archive older copies to `command_center/checklists/archive/`. | Add Make target housekeeping command + README guidance. |
| Validation transcripts | Keep latest 2 per prompt version; move older to `phase_6/archive/`. | Update validation plan to include archival step after reruns. |
| Decision log entries | Retain indefinitely (append-only). | No change. |

## Enforcement Plan

1. Document retention rules in `.repo_studios/command_center/README.md` and guardrail doc.
2. Update automation manifest CLI to hook pruning step after artifact write.
3. Add housekeeping Make target (`command-center-prune-artifacts`) invoking retention helpers.
4. Schedule monthly review to confirm archive directories remain under size threshold (<50 MB).

## Next Actions

- Draft PR to extend `write_report_artifacts` helper for automation bundle pruning.
- Update weighted progress briefing template to note when archives grow close to threshold.
- Train operators via prompt updates (`bundle_review`, `after_coding_alignment`) to confirm pruning occurred.
