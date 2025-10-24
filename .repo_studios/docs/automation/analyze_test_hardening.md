# analyze_test_hardening.py

**Last updated:** 2025-10-24

## Purpose

`analyze_test_hardening.py` inspects repository test modules for maintainability risks such as missing assertions, vague test names, excessive length, global state usage, and reliance on `time.sleep()`. The producer emits structured artifacts so agents and humans can prioritize remediation, highlight long-running tests, and monitor progress toward hardened suites.

## Invocation

```bash
python .repo_studios/scripts/producers/analyze_test_hardening.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/test_hardening_reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-analyze-test-hardening` to execute the producer with repository defaults.

### Key arguments

* `--repo-root`: Repository root used to resolve relative paths. Defaults to three levels up from the script.
* `--output-dir`: Directory for structured artifacts. Defaults to `.repo_studios/reports/producer_reports/test_hardening_reports` under the repo root.
* `--artifacts-to-keep`: Number of historical runs to retain. Minimum value is `1`; default is `10`.
* `--log-level`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default is `INFO`.

The producer auto-discovers files matching `test_*.py`, `*_test.py`, and `test*.py`, skipping ignored directories such as `.git`, `.repo_studios`, `.venv`, and `__pycache__`.

## Outputs

Each execution creates `.repo_studios/reports/producer_reports/test_hardening_reports/test_hardening-<timestamp>/` containing:

* `report.json`: Structured payload describing summary statistics, top priority files, clean files, and per-file findings.
* `report.md`: Human-readable summary with severity breakdowns, key findings, and long-test highlights.
* `log.txt`: Key-value digest (`status`, `exit_code`, totals) for CI ingestion.

The producer also refreshes `.repo_studios/reports/producer_reports/test_hardening_reports/latest/` with pointers to the newest run:

* `latest_report.json`
* `latest_report.md`
* `latest_log.txt`

Historical run directories are pruned after each execution according to `--artifacts-to-keep`.

## Findings and scoring

* Severity totals (`high`, `medium`, `low`) aggregate across all scanned test files.
* Priority scores weight high severity findings most heavily (10 points high, 3 medium, 1 low) to keep focus on critical gaps.
* Long tests capture the name, line count, and starting line for fast refactoring.
* Clean files highlight test modules without detected issues, helping identify good examples for standards.

## Testing

`pytest .repo_studios/tests/tests_producers/test_analyze_test_hardening.py`

The suite validates artifact creation, priority scoring, clean file identification, pruning behavior, and the latest-directory pointers.

## Operational notes

* The producer parses files using `ast` and simple regular expressions; syntax errors are recorded as high severity issues.
* Tests lacking assertions, using global mutations, or depending on `time.sleep()` are flagged as high or medium severity to signal flakiness risk.
* Naming style checks prefer descriptive `given_when_then`-style identifiers, elevating vague names as low severity hygiene issues.
* Extend `TEST_PATTERNS` or adjust ignore lists in the script if project-specific test file conventions differ.
