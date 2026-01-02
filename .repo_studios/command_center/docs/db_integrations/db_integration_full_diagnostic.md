# DB Integration: Full Diagnostic Meta-Orchestrator

## Script Identity

- **Script**: `orchestrate_full_diagnostic.py`
- **Path**: `.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py`
- **Category**: Meta-Orchestrator
- **Viewer Slug**: `healthview`
- **Topic Slug**: `full_diagnostic`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--reports-root` | CLI | Reports root directory |
| `--log-level` | CLI | Logging verbosity |
| `--timestamp` | CLI | ISO-8601 timestamp forwarded to topic orchestrators |
| `--artifacts-to-keep` | CLI | Retention budget (default: 3) |
| `--include` | CLI | Limit execution to provided topic slug(s) |
| `--exclude` | CLI | Skip provided topic slug(s) |
| `--stop-on-first-failure` | CLI | Abort remaining topics after first failure |
| `--keep-going` | CLI | Continue running topics even when failures occur |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| HealthView bundle | `<reports_root>/<timestamp>/` | Manifest, summary, telemetry |

**Default Reports Root**: `.repo_studios/command_center/reports/healthview/full_diagnostic/`

## Topic Definitions

The meta-orchestrator sequentially executes the following topic orchestrators:

| # | Slug | Module | Description |
|---|------|--------|-------------|
| 1 | `test-execution-telemetry` | `command_center.scripts.orchestrators.run_test_execution_telemetry` | Test execution telemetry |
| 2 | `docs-health` | `command_center.scripts.orchestrators.run_docs_health_overview` | Docs health overview |
| 3 | `fault-diagnostics` | `command_center.scripts.orchestrators.run_fault_diagnostics_overview` | Fault diagnostics |
| 4 | `dependency-import-hygiene` | `command_center.scripts.orchestrators.run_dependency_import_hygiene` | Dependency and import hygiene |
| 5 | `monkey-patch-oversight` | `command_center.scripts.orchestrators.run_monkey_patch_oversight` | Monkey patch oversight |
| 6 | `standards-integrity` | `command_center.scripts.orchestrators.run_standards_integrity` | Standards integrity |

## CLI Arguments

```text
--repo-root PATH          Repository root override
--reports-root PATH       Reports root directory
--log-level LEVEL         Logging verbosity (default: INFO)
--timestamp ISO8601       Timestamp forwarded to topic orchestrators
--artifacts-to-keep N     Retention budget (default: 3)
--include SLUG [SLUG...]  Limit to these topic slug(s)
--exclude SLUG [SLUG...]  Skip these topic slug(s)
--stop-on-first-failure   Abort after first failure (default)
--keep-going              Continue despite failures
```

## Storage Integration

- **Library**: Uses `write_report_artifacts` for output
- **Metrics**: Uses `measure_artifact_directory` for artifact metrics
- **Registry**: Uses standard PathsConfig and OptionsConfig

## Invocation Pattern

### Full Suite

```bash
python .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py \
  --repo-root . \
  --log-level INFO
```

### Selective Topics

```bash
python .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py \
  --repo-root . \
  --include test-execution-telemetry docs-health \
  --log-level INFO
```

### Skip Specific Topics

```bash
python .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py \
  --repo-root . \
  --exclude monkey-patch-oversight \
  --keep-going \
  --log-level INFO
```

## Execution Behavior

- **Default**: Stops on first failure (`--stop-on-first-failure`)
- **Alternative**: Continue despite failures (`--keep-going`)
- **Topic selection**: `--include` takes precedence; if not specified, all topics run
- **Dynamic loading**: Orchestrator modules loaded via `importlib.import_module`

## Topic Run Record

Each topic execution produces a record with:

- `slug`: Topic identifier
- `module`: Python module path
- `viewer`/`topic`: HealthView coordinates
- `status`: success/failure/skipped
- `exit_code`: Process exit code
- `started_at`/`finished_at`: Timestamps
- `run_slug`: Run directory identifier
- `artifact_dir`: Output artifact directory
- `argv`: Command-line arguments used
- `message`: Status message

## Dependencies

- Internal: `write_report_artifacts`, `measure_artifact_directory`, `build_topic_path`
- Topic orchestrators: All 6 topic orchestrators listed above

## Notes

- Master orchestrator for complete HealthView diagnostic suite (Stage 7)
- Coordinates all 6 topic pipelines in sequence
- Provides unified summary of all topic executions
- Supports selective execution via `--include`/`--exclude`
- Emits consolidated manifest, summary, and telemetry
