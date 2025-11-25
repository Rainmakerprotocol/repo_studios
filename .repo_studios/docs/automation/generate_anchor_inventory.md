# generate_anchor_inventory.py

**Status:** Live (schema version 1)

## Purpose

`generate_anchor_inventory.py` scans the documentation corpus for H1/H2
headings, normalises their slugs, and reports collision risk across files. The
producer now also captures per-document anchor coverage so AI agents can spot
missing headings or repeated anchors without rerunning a raw filesystem scan.

## Output Contract

- Timestamped run directories live under
  `.repo_studios/reports/producer_reports/anchor_inventory_reports/`.
- Each run emits:
  - `report.json` – canonical payload with summary metrics, duplicate listings,
    and per-document anchor coverage.
  - `report.md` – human-oriented digest that highlights duplicate clusters,
    per-root document totals, and remediation queues (missing H2, repeated
    anchors).
  - `slugs.tsv` – tab-separated list of every slug, its total heading count,
    participating files, and exact locations.
  - `documents.csv` – per-document metrics (H1/H2 counts, repeated anchors,
    cross-file membership, allowlisted slugs) for quick spreadsheet triage.
- Latest pointers (`latest_report.json`, `latest_report.md`,
  `latest_slugs.tsv`, `latest_documents.csv`) mirror the newest run alongside
  the timestamped directory.
- Retention defaults to 5 runs (`--artifacts-to-keep`), with older directories
  pruned automatically.
- Optional `--json-out` writes a legacy baseline mirror for consumers that have
  not yet migrated to the structured bundle.

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
- Delegates artifact creation and pruning to `write_report_artifacts`, keeping
  latest pointers in sync.
- Logs headline metrics (missing headings, repeated anchors, cross-file members)
  to make command-line runs actionable without opening artifacts.
- Pytest coverage (`tests/tests_producers/test_generate_anchor_inventory.py`)
  exercises duplicate detection, per-document payloads, CSV output, and run
  retention.

## Notes for AI Consumers

- Prefer `report.json` for structured ingestion; the Markdown digest mirrors
  the same data for human review.
- `documents.csv` is tailored for quick filtering (e.g. locate files missing H2
  headings or repeated anchors) and aligns with spreadsheet tooling.
- The producer now surfaces enough metadata for consumers like
  `generate_anchor_health_report.py` to avoid re-parsing markdown when the JSON
  bundle is present.
- Allowlist size from `test_global_anchors.py` is preserved in the summary so
  downstream checks can report drift against the enforced baseline.
