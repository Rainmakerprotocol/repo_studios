# DB Integration: Anchor Health Report Consumer

## Script Identity

- **Script**: `generate_anchor_health_report.py`
- **Path**: `.repo_studios/scripts/consumers/generate_anchor_health_report.py`
- **Category**: Consumer
- **Topic Slug**: `anchor_health`
- **Status**: Active (Stage 11.1 orchestrator integration complete)

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Anchor inventory artifacts | Producer | From `generate_anchor_inventory.py` |
| Baseline file | File | `tests/docs/anchor_slug_baseline.json` |
| Docs directory | Directory | Fallback: scans `docs/` if no inventory exists |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| summary.json | `<output_dir>/<run-id>/summary.json` | Structured JSON report |
| SUMMARY.md | `<output_dir>/<run-id>/SUMMARY.md` | Markdown report |
| bundle_summary.json | `<output_dir>/<run-id>/bundle_summary.json` | Bundle metadata |
| clusters.tsv | `<output_dir>/<run-id>/clusters.tsv` | TSV cluster data |

**Default Output Directory**: `.repo_studios/anchor_health/`

## Purpose

Generates machine and human consumable snapshot of top-level (H1/H2) markdown anchor slug duplication. Designed to integrate with AI assistance workflows for:

1. Detecting drift vs committed baseline
2. Surfacing remaining cross-file duplicates
3. Recommending next slugs to collapse (largest clusters first)
4. Emitting artifacts for dashboards/summaries

## Exit Code

- **0**: Always (pipeline decides policy)
- Use `strict_duplicate_count` JSON field to gate if desired

## Dependencies

- Upstream: `generate_anchor_inventory.py` (producer)
- Internal: `anchor_inventory_loader` utility module

## Notes

- Consumer that analyzes anchor inventory for duplications
- Falls back to in-process docs scan when no inventory exists
- Multi-root scanning: scans both `docs/` and `.repo_studios/docs/`
- Orchestrator integration: Stage 11.1 `run_available_scripts_oversight.py`
- Phase 4 compliance: Complete (2026-01-28)

## Storage Integration

- Uses `build_topic_path("consumer", TOPIC_SLUG)` for default output path
- Uses `_prune_old_runs()` for retention
- **Does NOT use `create_storage()`** — uses direct file writes
- **No `latest_*` pointers** — HOP-compliant

> **DB Integration Status:** This script does NOT currently have `DB_INTEGRATION_MARKER`
> tags. To enable dual-write support, markers would need to be added at the artifact
> write locations in `write_artifacts()` (lines 405-513).

## Update Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-28 | Agent | Updated status to Active, noted missing DB markers, corrected storage integration |
