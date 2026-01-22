# summarize_standards.py

**Last updated:** 2026-01-22

## Purpose

`summarize_standards.py` provides a lightweight HealthView/HOP-compliant summary of the standards
catalog. It reads the canonical standards index YAML (`.repo_studios/scripts/repo_standards_index.yaml`)
and the optional pending extraction queue, then emits a 3-artifact bundle (`manifest.json`,
`summary.md`, `telemetry.json`) suitable for CI telemetry and human review.

This subsystem does not use `latest_*` pointer artifacts and does not fall back to legacy
`latest_index.yaml` snapshots.

## Invocation

```bash
python .repo_studios/scripts/summarizers/summarize_standards.py \
  --repo-root . \
  --label summary \
  --log-level INFO
```

### Environment overrides

- `INDEX_PATH`: alternate path to the standards index YAML (default `.repo_studios/scripts/repo_standards_index.yaml`).
- `PENDING_PATH`: alternate path to the pending extraction queue (default `.repo_studios/scripts/repo_standards_pending.yaml`).

## Outputs

Each run creates a HealthView/HOP bundle under the configured `--output-dir` (by default,
`.repo_studios/reports/healthview/summarizer_reports/standards_overview/<YYYYMMDD-HHMM>/`).

The bundle includes:

- `manifest.json`: structured summary payload (metrics, paths, notes).
- `summary.md`: human-readable synopsis.
- `telemetry.json`: HOP telemetry envelope (`metrics`).

Key fields include:

- Total rule count.
- Extraction statistics (`extracted_count`, `auto_accept`, `pending_file`).
- Markdown-derived rule identifiers (sampled) when present.
- Pending queue line count when the configured pending file exists.

The artifacts are consumed by orchestrators and CI telemetry to verify that the standards index is
current before downstream automation runs.

## Testing

`pytest .repo_studios/tests/tests_summarizers/test_summarize_standards.py`

The regression tests cover successful bundle emission and verify that legacy `latest_index.yaml`
snapshots are not used.
