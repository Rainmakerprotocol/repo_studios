# Duplicate Detection Schema Alignment – 2025-10-24

## Goal

Translate `scan_code_duplicates.py` output into the data products Repo Studios already consumes (health-suite summaries, companion analysis exports, and future automation inputs).

## Source Schemas

### 1. Companion Analysis (current 360-occurrence export)

- Delivery: ad-hoc CSV/JSON outside the repo.
- Guaranteed fields (per latest export notes):
  - `function_name`
  - `occurrence_count`
  - `file_paths` (list)
  - Optional: `notes` (free-form rationale)
- Limitations: no line spans, similarity score, or action plan metadata.

### 2. Health Suite Summary (today)

- Markdown only; tracks documentation slug duplication (`strict duplicate count`, `baseline`, top offenders).
- No function-level records to map; needs enrichment once the scanner is integrated.

### 3. `scan_code_duplicates.py` JSON (`duplicate_groups` array)

- Rich structure: `group_id`, `signature_hash`, `canonical_name`, `purpose`, `category`.
- `occurrences[]` list with `file`, `line_start`, `line_end`, `function_name`, `code_hash`.
- Remediation helpers: `library_recommendation`, `refactoring_action`, `impact_analysis`, `ai_agent_instructions`.

## Field Mapping

| Target metric | Scanner source | Notes |
| --- | --- | --- |
| `function_name` | `duplicate_group.canonical_name` or dominant `occurrences[].function_name` | Canonical name may strip leading underscores; retain original names in detail view. |
| `occurrence_count` | `len(occurrences)` | Direct count. |
| `file_paths` | `[occurrence.file for occurrence in occurrences]` | Preserve duplicates (some functions appear multiple times in same file). |
| `line_ranges` (new) | `(line_start, line_end)` per occurrence | Enables precise navigation; optional in legacy export. |
| `similarity_score` | `duplicate_group.similarity_score` | New datapoint; can drive prioritisation. |
| `duplicate_type` | `duplicate_group.duplicate_type` | Distinguish exact vs. near duplicate. |
| `library_path` | `library_recommendation.target_path` | Introduces destination guidance missing today. |
| `priority` | `refactoring_action.priority` | Allows dashboards to sort by remediation urgency. |
| `lines_saved` | `impact_analysis.lines_saved` | Additional ROI metric derived from scanner only. |

## Translation Steps

1. **Extract raw occurrences** into a flat table (function, file, line range, group id, similarity, duplicate type).
2. **Aggregate** by canonical function to produce occurrence counts and distinct file counts for dashboards.
3. **Summarise** totals (groups, occurrences, files, estimated line savings) to mirror current companion roll-ups.
4. **Publish** two artifacts per run. The integrated
   `.repo_studios/scripts/command_center/duplicates/scan_duplicates.py`
   command now handles this automatically:
    - `duplicate_matrix.json` – structured payload with metadata, merged
      producers findings, and scanner-only groups.
    - `duplicate_matrix_summary.md` – human-readable recap of key statistics
      and recommended follow-ups.

5. **Update health-suite summary template** to ingest aggregated metrics so
   daily reports surface function-level duplication again.

## Outstanding Questions

- Confirm whether legacy exports include additional metadata (e.g., severity tags). If yes, decide whether to carry them forward or derive equivalents from scanner fields.
- Validate Windows behaviour for symlink creation (`latest_report.json`). If symlinks fail, choose fallback (copy instead) before wiring into CI.
- Determine storage location for historical companion exports (commit a snapshot vs. rely on recreated scanner output).

## Recommendations

- Treat `scan_duplicates.py` output as the source of truth once parity is
  verified; derive legacy aggregates rather than maintaining two detectors.
- Document the aggregation contract (field definitions, file locations) inside `.repo_studios/command_center/README.md` when ready.
- Schedule joint review with health-suite maintainers to decide integration point and reporting cadence.
