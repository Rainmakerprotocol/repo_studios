# generate_undocumented_logic_report

## Purpose

`generate_undocumented_logic_report.py` scans the repo automation scripts for
public functions, classes, and methods that lack docstrings. The report helps
identify code paths that should have documentation anchors or docstring coverage
before they feed downstream aggregators.

## Inputs

- Repository root (`--repo-root`, defaults to auto-detected root)
- Output directory (`--output-dir`, defaults to
  `.repo_studios/reports/producer_reports/undocumented_logic_reports`)
- Documentation index JSON (`--doc-index`, defaults to
  `.repo_studios/reports/producer_reports/doc_index/latest_doc_index.json`)
- Anchor inventory JSON (`--anchor-inventory`, defaults to
  `.repo_studios/reports/producer_reports/anchor_inventory_reports/latest_report.json`)
- Optional allowlist file (`--allowlist`) with module or module::qualified-name
  entries to skip
- Optional additional code roots (`--code-root` can be provided multiple times)
- Optional flag to include `.repo_studios/command_center/scripts`
  (`--include-command-center`)
- Retention cap (`--artifacts-to-keep`, default 5)
- Standard logging flag (`--log-level`)

## Outputs

Each run emits a timestamped directory named
`undocumented_logic-YYYYMMDD_HHMMSS` containing:

- `report.json` – structured payload listing modules, findings, and enrichment
  metadata
- `report.md` – human-readable summary sorted by severity
- `undocumented.tsv` – tabular output for spreadsheets
- `bundle_summary.json` – compact summary for orchestrators

Latest-pointer files (`latest_report.json`, `latest_report.md`,
`latest_undocumented.tsv`, `latest_bundle_summary.json`) live alongside the
timestamped runs. The producer enforces retention according to
`--artifacts-to-keep`.

## Usage

```pwsh
$env:PYTHONPATH = ".repo_studios"
.\.venv\Scripts\python.exe -u \
  .repo_studios\scripts\producers\generate_undocumented_logic_report.py \
  --repo-root . \
  --include-command-center \
  --output-dir .repo_studios/reports/producer_reports/undocumented_logic_reports
```

Add `--code-root <path>` to scan extra directories (for example legacy modules),
or `--allowlist <file>` to suppress known exceptions while remediation is in
progress.

## Testing

Unit coverage lives in
`.repo_studios/tests/tests_producers/test_generate_undocumented_logic_report.py`.
The suite exercises detection, allowlist handling, and missing metadata flows.
Run the focused tests with:

```pwsh
$env:PYTHONPATH = ".repo_studios"
.\.venv\Scripts\python.exe -m pytest \
  .repo_studios/tests/tests_producers/test_generate_undocumented_logic_report.py
```
