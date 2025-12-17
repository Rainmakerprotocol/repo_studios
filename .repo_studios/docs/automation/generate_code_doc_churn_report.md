---
title: generate_code_doc_churn_report
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.1.0
updated: 2025-12-16
tags:
  - producer
  - docs-health
  - telemetry
related_files:
  - ../../scripts/producers/generate_code_doc_churn_report.py
  - ../../tests/tests_producers/test_generate_code_doc_churn_report.py
  - ../../Makefile
---

# generate_code_doc_churn_report

## Purpose

`generate_code_doc_churn_report.py` scans recent git history to surface modules
that accumulated code churn without a matching documentation update. The script
produces structured artifacts (JSON, Markdown, TSV, summary) with retention and
latest pointers so downstream consumers and aggregators can plug into the
results directly.

## Inputs

- Repository root (`--repo-root`, defaults to current working directory)
- Git window (`--git-window`, defaults to `14 days`) and optional `--git-until`
- Documentation index JSON (`--doc-index`), defaults to
  `.repo_studios/reports/producer_reports/doc_index/latest_doc_index.json`
- Anchor inventory JSON (`--anchor-inventory`), defaults to
  `.repo_studios/reports/producer_reports/healthview/anchor_inventory/`
- Optional module allowlist (`--allowlist`) listing modules that should be
  skipped, one name per line
- `--output-dir` (defaults to
  `.repo_studios/reports/producer_reports/code_doc_churn_reports`)
- `--artifacts-to-keep` retention cap (default 5)
- Standard logging flag (`--log-level`)

## Outputs

Each run emits a canonical positional bundle under:

`.repo_studios/reports/producer_reports/healthview/code_doc_churn/YYYYMMDD-HHMM/`

The bundle contains exactly:

- `manifest.json` – run metadata, inputs, provenance, and headline counts
- `summary.md` – human-readable digest of missing-doc modules
- `telemetry.json` – structured metrics for DB ingestion plus the full legacy payload

The producer does not write any `latest_*` pointer files.

## Usage

```pwsh
$env:PYTHONPATH = ".repo_studios"
.\.venv\Scripts\python.exe -u \
  .repo_studios\scripts\producers\generate_code_doc_churn_report.py \
  --repo-root . \
  --git-window "30 days" \
  --output-dir .repo_studios/reports/producer_reports
```

Or invoke the Make target (mirrors the 30-day window and retention defaults):

```pwsh
PYTHON=".venv/Scripts/python.exe" make -C .repo_studios studio-generate-code-doc-churn-report
```

Log level, retention, doc index paths, anchor inventory paths, and allowlist can
be overridden as needed. When the doc index or anchor inventory is unavailable,
the script still emits the churn bundle but omits enrichment sections.

## Testing

Unit coverage lives in
`.repo_studios/tests/tests_producers/test_generate_code_doc_churn_report.py`.
The suite builds temporary git repositories to verify:

- Modules with code churn and no doc edits are flagged
- Modules with doc edits are excluded from the "missing docs" list
- Allowlisted modules are skipped

Run the focused suite with:

```pwsh
$env:PYTHONPATH = ".repo_studios"
.\.venv\Scripts\python.exe -m pytest \
  .repo_studios/tests/tests_producers/test_generate_code_doc_churn_report.py
```
