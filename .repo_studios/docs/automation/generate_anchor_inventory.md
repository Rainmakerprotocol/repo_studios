# generate_anchor_inventory.py

**Status:** Live (schema version 1)

## Purpose

`generate_anchor_inventory.py` scans the documentation corpus for H1/H2
headings, normalises their slugs, and reports collision risk across files. The
producer now also captures per-document anchor coverage so AI agents can spot
missing headings or repeated anchors without rerunning a raw filesystem scan.

## Output Contract

- Timestamped bundles live under:
  `.repo_studios/reports/producer_reports/healthview/anchor_inventory/<YYYYMMDD-HHMM>/`.
- Each bundle contains exactly:
  - `manifest.json` – run metadata + artifact catalog.
  - `summary.md` – human-readable digest.
  - `telemetry.json` – structured metrics plus the historical inventory schema
    embedded as `payload` for compatibility.
- No mutable `latest_*` pointers are emitted.
- Retention defaults to 5 bundles (`--artifacts-to-keep`), with older bundle
  directories pruned automatically.
- Optional `--json-out` writes a legacy JSON mirror of the `payload` report for
  consumers that have not migrated.

## Data Shape

### Summary

- `summary.total_slugs` – unique slugs discovered across all scanned roots.
- `summary.total_documents` – markdown files inspected.
- `summary.documents_missing_h1` / `summary.documents_missing_h2` – counts of
  anchor gaps (H2 requires at least one H1).
- `summary.documents_with_repeated_anchors` – files that reuse an anchor within
  the same document.
- `summary.documents_with_cross_file_duplicates` – files participating in a
  cross-file slug collision after allowlist filtering.
- `summary.top_document_roots` – top-level directory counts (e.g. `docs`,
  `.repo_studios`).

### Duplicates

`duplicates` contains slug entries with `count`, `file_count`, `files`, and
`locations`. The list excludes allowlisted slugs (default `overview`,
`introduction`, `faq`, `notes` plus optional `--allow-file`).

### Documents

Each document entry exposes:

- `path`, `h1_count`, `h2_count`, `heading_count`, `unique_slugs`.
- `duplicate_slugs` – anchors repeated in the same file.
- `cross_file_duplicate_slugs` – anchors also present in other files (after
  allowlist filtering).
- `allowlisted_slugs` – anchors tolerated by the allowlist inputs.
- `slug_counts` – per-slug heading count map for deeper analysis.

## CLI Reference

- `--docs-root` – primary markdown root (defaults to `docs`).
- `--additional-docs-root` – repeatable flag for extra roots; the default run
  automatically includes `.repo_studios/docs` when scanning `docs`.
- `--allow-file` – newline-delimited allowlist additions.
- `--test-file` – path to `test_global_anchors.py` for historical allowlist
  sizing (surfaced in the summary).
- `--json-out` – legacy mirror output path.
- `--output-dir` – override artifact location.
- `--artifacts-to-keep` – retention count (default 5).
- `--timestamp` – ISO-8601 override to stabilise tests.
- `--log-level` – logging verbosity.

## Implementation Summary

- Uses `build_standard_paths` / `build_standard_options` for repo-root-aware
  resolution and retention handling.
- Normalises slugs with the shared helper, records H1/H2 counts per document,
  and collects line-level locations for every heading.
- Aggregates cross-file duplicate membership, builds per-document payloads, and
  renders CSV via `csv.writer` to ensure safe quoting.
- Delegates artifact creation to the shared storage abstraction
  (`create_storage(...)`) and pruning to `prune_run_directories(...)`.
- Logs headline metrics (missing headings, repeated anchors, cross-file members)
  to make command-line runs actionable without opening artifacts.
- Pytest coverage (`tests/tests_producers/test_generate_anchor_inventory.py`)
  exercises duplicate detection, per-document payloads, CSV output, and run
  retention.

## Notes for AI Consumers

- Prefer `telemetry.json` for structured ingestion; `telemetry.json["payload"]`
  preserves the historical report schema.
- `summary.md` mirrors the same information for human review.
- The bundle contains enough metadata for consumers like
  `generate_anchor_health_report.py` to avoid re-parsing markdown when the
  payload is present.
- Allowlist size from `test_global_anchors.py` is preserved in the summary so
  downstream checks can report drift against the enforced baseline.
