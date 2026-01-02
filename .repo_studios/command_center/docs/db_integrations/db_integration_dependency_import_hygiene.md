# DB Integration: Dependency Import Hygiene Orchestrator

## Script Identity

- **Script**: `run_dependency_import_hygiene.py`
- **Path**: `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py`
- **Category**: Orchestrator
- **Topic Slug**: `dependency-import-hygiene`
- **HealthView Topic**: `dependency_import_hygiene`

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--dependency-output-dir` | CLI | Dependency hygiene output directory |
| `--import-graph-output-dir` | CLI | Import graph output directory |
| `--placeholder-output-dir` | CLI | Placeholder scan output directory |
| `--typecheck-output-dir` | CLI | Typecheck output directory |
| `--mypy-baselines-output-dir` | CLI | Mypy baselines output directory |
| `--healthview-root` | CLI | HealthView root directory |
| `--artifacts-to-keep` | CLI | Retention budget for orchestrator runs (default: 3) |
| `--log-level` | CLI | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--timestamp` | CLI | ISO8601 timestamp forwarded to producers |

### Skip/Optional Flags

| Flag | Description |
|------|-------------|
| `--skip-import-graph` | Skip the import graph producer |
| `--skip-typecheck` | Skip the typecheck producer |
| `--trigger-batch-cleanup` | Execute run_batch_cleanup in dry-run mode |
| `--refresh-mypy-baselines` | Invoke the mypy baseline refresher after typecheck |

### Retention Flags (per-producer)

| Flag | Default | Description |
|------|---------|-------------|
| `--dependency-artifacts-to-keep` | 10 | Dependency hygiene producer retention |
| `--import-graph-artifacts-to-keep` | 10 | Import graph producer retention |
| `--placeholder-artifacts-to-keep` | 5 | Placeholder scanner retention |
| `--cleanup-artifacts-to-keep` | 5 | Batch cleanup retention |
| `--typecheck-artifacts-to-keep` | 10 | Typecheck producer retention |
| `--baseline-artifacts-to-keep` | 5 | Mypy baselines retention |

### Producer-Specific Passthrough Flags

| Flag | Description |
|------|-------------|
| `--dependency-requirements-pattern` | Glob pattern(s) for dependency hygiene producer |
| `--dependency-skip-pyproject` | Skip pyproject.toml in dependency hygiene |
| `--import-owned` | Owned packages for import graph producer |
| `--placeholder-include-ext` | File extensions for placeholder scanner |
| `--placeholder-pattern` | Placeholder tokens for scanner |
| `--placeholder-exclude-prefix` | Prefixes to exclude from placeholder scan |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Run bundle | `<healthview_root>/dependency_import_hygiene/<timestamp>/` | Orchestrator run bundle |

**Default HealthView Root**: `.repo_studios/command_center/reports/healthview/`

## Invoked Scripts

| # | Script | Category | Condition |
|---|--------|----------|-----------|
| 1 | `generate_dependency_hygiene_report.py` | Producer | Always |
| 2 | `generate_import_graph_report.py` | Producer | Unless `--skip-import-graph` |
| 3 | `scan_code_placeholders.py` | Producer | Always |
| 4 | `generate_typecheck_report.py` | Producer | Unless `--skip-typecheck` |
| 5 | `refresh_mypy_baselines.py` | Utility | Only if `--refresh-mypy-baselines` |

## CLI Arguments

```text
--repo-root PATH                         Repository root override
--dependency-output-dir PATH             Dependency hygiene output directory
--import-graph-output-dir PATH           Import graph output directory
--placeholder-output-dir PATH            Placeholder scan output directory
--placeholder-allowlist PATH             Placeholder allowlist file
--batch-cleanup-output-base PATH         Batch cleanup output base
--typecheck-output-dir PATH              Typecheck output directory
--mypy-baselines-output-dir PATH         Mypy baselines output directory
--healthview-root PATH                   HealthView root directory
--artifacts-to-keep N                    Orchestrator retention budget (default: 3)
--dependency-artifacts-to-keep N         Dependency producer retention (default: 10)
--import-graph-artifacts-to-keep N       Import graph retention (default: 10)
--placeholder-artifacts-to-keep N        Placeholder retention (default: 5)
--cleanup-artifacts-to-keep N            Cleanup retention (default: 5)
--typecheck-artifacts-to-keep N          Typecheck retention (default: 10)
--baseline-artifacts-to-keep N           Baselines retention (default: 5)
--dependency-requirements-pattern GLOB   Requirements pattern (repeatable)
--dependency-skip-pyproject              Skip pyproject.toml scanning
--import-owned PKG [PKG ...]             Owned packages list
--placeholder-include-ext EXT [EXT ...]  File extensions for scanner
--placeholder-pattern PAT [PAT ...]      Placeholder tokens
--placeholder-exclude-prefix PFX [PFX...] Exclude prefixes
--skip-import-graph                      Skip import graph step
--skip-typecheck                         Skip typecheck step
--trigger-batch-cleanup                  Run batch cleanup in dry-run
--refresh-mypy-baselines                 Refresh mypy baselines after typecheck
--timestamp ISO8601                      Timestamp override
--log-level LEVEL                        Logging verbosity (default: INFO)
```

## Storage Integration

- **Registry**: Uses `CatalogRegistry` for topic context
- **Context**: Uses `TopicContext` and `TopicStep` for structured execution
- **Retention Strategy**: Per-producer retention budgets with orchestrator-level pruning

## Invocation Pattern

### Standalone

```bash
python .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py \
  --repo-root . \
  --log-level INFO
```

### Full Pipeline

```bash
python .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py \
  --repo-root . \
  --refresh-mypy-baselines \
  --log-level DEBUG
```

### Skip Expensive Steps

```bash
python .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py \
  --repo-root . \
  --skip-import-graph \
  --skip-typecheck \
  --log-level INFO
```

## Runtime

- **Typical Duration**: 7-11 minutes in CI (with all steps enabled)
- **Fast Mode**: 2-3 minutes with `--skip-import-graph --skip-typecheck`

## Dependencies

- External: mypy (for typecheck step)
- Internal: `CatalogRegistry`, `TopicContext`, `TopicStep` from libraries

## Notes

- Primary orchestrator for code quality hygiene checks (Stage 4.1)
- Coordinates 5 scripts with conditional execution based on flags
- Supports granular retention budgets per invoked producer
- Contributes to HealthView catalog under `dependency_import_hygiene` topic
