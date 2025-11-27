# aggregate_docs_health_signals

## Purpose

`aggregate_docs_health_signals.py` will fuse disparate documentation quality signals
into a single dashboard that highlights where Repo Studios needs renewed attention.
The aggregator focuses on three questions:

1. **Are docs keeping pace with source churn?** (freshness)
1. **Do code paths expose undocumented logic?** (coverage)
1. **Are published docs structurally healthy and passing guardrails?** (integrity)

Surfacing those answers in one bundle lets orchestration layers and reviewers
triage documentation debt without walking every producer report manually.

## Upstream Inputs

The initial version ingests the latest artifacts emitted by hardened producers
and consumers. Default pointers follow existing retention conventions; overrides
stay available through CLI flags so test runs can point at fixtures.

- Churn freshness: `generate_code_doc_churn_report.py`
  (`.repo_studios/reports/producer_reports/code_doc_churn_reports/latest_report.json`)
- Docstring coverage: `generate_undocumented_logic_report.py`
  (`.repo_studios/reports/producer_reports/undocumented_logic_reports/latest_report.json`)
- Anchor coverage + duplicates: `generate_anchor_inventory.py`
  (`.repo_studios/reports/producer_reports/anchor_inventory_reports/latest_report.json`)
- Anchor validation errors: `validate_markdown_anchors.py`
  (`.repo_studios/reports/producer_reports/markdown_anchor_validation_reports/latest_report.json`)
- Docs integrity governance: `verify_docs_integrity.py`
  (`.repo_studios/reports/producer_reports/docs_integrity_reports/latest_report.json`)
- Metrics stub drift: `validate_metrics_anchor_stubs.py`
  (`.repo_studios/reports/producer_reports/metrics_anchor_stub_reports/latest_report.json`)
- Placeholder + monkey-patch hygiene (optional, flagged informational)
  - `scan_code_placeholders.py`
    (`.repo_studios/reports/producer_reports/code_placeholder_reports/latest_report.json`)
  - `scan_monkey_patches.py`
    (`.repo_studios/reports/producer_reports/monkey_patch_scans/latest_report.json`)

Future revisions can extend the roster (for example, standards index gaps,
docs-view renderers, or test hardening) once downstream consumers request it.

## Output Bundle

Each run emits a timestamped directory `docs_health_signals-YYYYMMDD_HHMMSS`
within `.repo_studios/reports/aggregator_reports/docs_health_signals/` containing:

- `report.json` – canonical structured payload with:
  - `summary` headline KPIs (overall health score, docstring coverage, churn hotspots)
  - `signals` map keyed by category (`freshness`, `coverage`, `structure`, `integrity`, `hygiene`)
    capturing status (`healthy`, `warning`, `critical`), supporting metrics, and top findings
  - `provenance` entries mapping each signal to the upstream artifact path,
    recorded schema versions, and aggregate status
- `report.md` – human-readable brief summarizing each category with tables of top offenders
  (long doc paths live inside an `<!-- markdownlint-disable MD013 -->` guard)
- `signals.tsv` – flat table of category, severity, subject, metric, and call-to-action
- `signals.csv` – spreadsheet-friendly mirror of the TSV payload for downstream tooling
- `bundle_summary.json` – quick metrics designed for orchestrator dashboards

Latest-pointer files (`latest_report.json`, `latest_report.md`, `latest_signals.tsv`,
`latest_signals.csv`, `latest_bundle_summary.json`) sit alongside timestamped runs. Retention is controlled
through `--artifacts-to-keep` (default 5) leveraging the shared
`write_report_artifacts` helper.

## CLI Surface

Baseline invocation mirrors the other aggregators and relies on shared path
builders to enforce repo-root safety:

```pwsh
PYTHON=".venv/Scripts/python.exe" make -C .repo_studios studio-aggregate-docs-health
```

Equivalent direct call:

```pwsh
$env:PYTHONPATH = ".repo_studios"
.\.venv\Scripts\python.exe -u \
  .repo_studios\scripts\aggregators\aggregate_docs_health_signals.py \
  --repo-root . \
  --output-dir .repo_studios/reports/aggregator_reports/docs_health_signals \
  --artifacts-to-keep 5 \
  --log-level INFO
```

Flags for each upstream input (`--churn-report`, `--undocumented-report`, etc.)
default to the latest-pointer paths listed above and can be overridden for tests.
Boolean toggles allow optional hygiene signals to be excluded when running focused
scans.

## Score Model

The first iteration uses a weighted average to roll category metrics into a
single `overall_score` (0–100):

- Freshness (35%) – percentage of churn findings resolved or triaged
- Coverage (35%) – docstring coverage percentile across monitored modules
- Structure (15%) – proportion of docs passing anchor validation and inventory checks
- Integrity (10%) – governed doc hash parity and metrics stub completeness
- Hygiene (5%) – inverse count of placeholder / monkey-patch doc-adjacent hits

Each category computes a normalized 0–100 value so new signals can slot in.
Future work can externalize weights into config once stakeholders calibrate
sensitivity.

## Implementation Checklist

- Scaffold CLI + shared path/options config (mirroring existing aggregators).
- Load upstream bundles defensively: warn when sources are missing, but continue
   generating a partial report with explicit gaps in `signals`.
- Build data model helpers for the summary + per-category payloads.
- Render Markdown/TSV using deterministic ordering (severity desc, name asc).
- Emit artifacts via `write_report_artifacts` with pruning and latest pointers.
- Add pytest coverage (`tests/tests_aggregators/test_aggregate_docs_health_signals.py`)
   exercising successful aggregation, missing-input fallbacks, and severity math.
- Backfill automation docs (this file), Make target wiring, and script inventory entry.

## Testing Plan

- Unit tests mock lightweight upstream payloads to validate aggregation math,
  severity thresholds, markdown rendering, and TSV generation.
- Fixture-based tests simulate missing inputs to ensure the bundle still emits
  with clear warnings.
- Optional integration smoke test runs the Make target after producing sample
  upstream artifacts (leveraging existing producers’ tests or fixtures).

## Follow-Up Opportunities

- Feed trend lines by pulling historical `bundle_summary.json` values and
  emitting sparkline-ready data in `report.json`.
- Thread doc ownership information (from doc index `owners` values) directly
  into the signals payload for rapid assignment.
- CSV export landed; gather operator feedback before expanding metric coverage.
- Wire the aggregator into the command center orchestrator once stability is confirmed.
