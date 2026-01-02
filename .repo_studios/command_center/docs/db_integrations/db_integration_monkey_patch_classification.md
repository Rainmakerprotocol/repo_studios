# DB Integration: Monkey Patch Classification Consumer

## Script Identity

- **Script**: `classify_monkey_patches.py`
- **Path**: `.repo_studios/scripts/consumers/classify_monkey_patches.py`
- **Category**: Consumer
- **Topic Slug**: `monkey_patch_risk`

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--scan-path` | CLI | Explicit scan directory path |
| `--base-dir` | CLI | Base directory containing scan runs |
| `--output-base` | CLI | Output directory override |
| `--artifacts-to-keep` | CLI | Number of bundles to retain |
| `--log-level` | CLI | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `MONKEY_DIR` | ENV | Environment variable for scan directory |

### Producer Artifact Locations

- **Structured**: `.repo_studios/reports/producer_reports/monkey_patch_scans/<run-id>/`
- **Legacy fallback**: `.repo_studios/monkey_patch/<run-id>/`
- **Expected files**: `matches.json` (structured) or `report.json` (legacy)

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| RISK_SUMMARY.json | `<output_base>/<bundle-id>/RISK_SUMMARY.json` | Structured risk classification |
| RISK_SUMMARY.md | `<output_base>/<bundle-id>/RISK_SUMMARY.md` | Markdown risk summary |

**Default Output Directory**: `.repo_studios/reports/consumer_reports/monkey_patch_risk/`

## Risk Classification

| Level | Categories |
|-------|------------|
| HIGH | `sys_modules_assignment`, `import_time_side_effect` (non-test), `global_env_mutation` (non-test, module scope) |
| MODERATE | `attribute_reassignment_on_import` (non-test), `global_env_mutation` (tests) |
| SAFE | `attribute_reassignment_on_import` (tests only) |

## CLI Arguments

```text
--repo-root PATH         Repository root override
--scan-path PATH         Explicit scan directory path
--base-dir PATH          Base directory for scan runs
--output-base PATH       Output directory override
--artifacts-to-keep N    Number of bundles to retain
--log-level LEVEL        Logging verbosity (default: INFO)
```

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/consumers/classify_monkey_patches.py \
  --repo-root . \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_monkey_patch_oversight.py` unless `--skip-consumer` is passed.

## Dependencies

- Upstream: `scan_monkey_patches.py` (producer)
- Internal: `monkey_patch_risk.py` utility module

## Notes

- Consumer that reads producer scan artifacts and classifies risk levels
- Part of the Monkey Patch Oversight pipeline (Stage 5.1)
- Exit code is always 0 (reporting only, no enforcement)
