# Typecheck Report Producer

The `generate_typecheck_report.py` producer runs `mypy` with the repository defaults and captures a structured set of artifacts for observability.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_typecheck_report.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/typecheck_reports \
  --log-level INFO
```

Key flags:

- `--timestamp` — optional ISO8601 timestamp; omit to use current UTC.
- `--artifacts-to-keep` — number of historical runs to retain (default 10).
- `--log-level` — standard logging level (INFO by default).

Environment overrides:

- `TYPECHECK_TARGETS` — whitespace separated paths to check instead of the pyproject list.
- `TYPECHECK_STRICT` — when set to a truthy value, append `--strict` to the `mypy` invocation.
- `HEALTH_TYPECHECK_FAST` — when truthy and no explicit targets are supplied, limit execution to the curated fast-mode prefixes.

## Outputs

Artifacts are written to `.repo_studios/reports/producer_reports/typecheck_reports/` with the layout:

```text
typecheck_reports/
  typecheck-<timestamp>/
    report.json
    report.md
    log.txt
    raw.txt
  latest_report.json
  latest_report.md
  latest_report.log
  latest_raw.txt
```

The JSON payload includes `status`, `summary` counters, the captured invocation, and sampled error diagnostics. Markdown and log companions mirror the same information for humans and automation. `latest_*` files update on each run for easy consumption.

Old runs are pruned after each execution according to `--artifacts-to-keep`.

## Testing

```bash
python -m pytest .repo_studios/tests/tests_producers/test_generate_typecheck_report.py
```

The test suite exercises success and failure flows, ensuring artifact creation, latest-link updates, and basic parsing of error samples.
