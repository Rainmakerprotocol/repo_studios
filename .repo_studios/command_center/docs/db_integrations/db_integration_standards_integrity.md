# DB Integration: Standards Integrity Orchestrator

## Script Identity

- **Script**: `run_standards_integrity.py`
- **Path**: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
- **Category**: Orchestrator
- **Topic Slug**: `standards-integrity`
- **HealthView Topic**: `standards_integrity`
- **Viewer Slug**: `healthview`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--index-output-dir` | CLI | Standards index output directory |
| `--index-path` | CLI | Path to standards index YAML |
| `--categories-path` | CLI | Path to standards categories YAML |
| `--gap-output-dir` | CLI | Gap analysis output directory |
| `--diff-output-dir` | CLI | Diff output directory |
| `--prompt-output-dir` | CLI | Prompt seeds output directory |
| `--pending-path` | CLI | Path to pending rules YAML |
| `--healthview-root` | CLI | HealthView root directory |
| `--diff-old-index` | CLI | Baseline index YAML for diff step |
| `--diff-fail-on` | CLI | Fail policy for diff script (default: any) |
| `--gap-max-show` | CLI | Max gap candidates to log per source (default: 8) |
| `--prompt-include-warn` | CLI | Include warn severity rules in seed |
| `--prompt-formats` | CLI | Artifact formats for prompt seed (text, yaml, json) |
| `--timestamp` | CLI | ISO8601 timestamp for delegated scripts |
| `--log-level` | CLI | Logging verbosity |

### Retention Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--artifacts-to-keep` | 3 | Orchestrator retention |
| `--index-artifacts-to-keep` | 5 | Standards index retention |
| `--gap-artifacts-to-keep` | 5 | Gap analysis retention |
| `--diff-artifacts-to-keep` | 10 | Diff retention |
| `--prompt-artifacts-to-keep` | 5 | Prompt seed retention |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| HealthView bundle | `<healthview_root>/<timestamp>/` | Manifest, summary, telemetry |

**Default HealthView Root**: `.repo_studios/command_center/reports/healthview/standards_integrity/`

## Invoked Scripts

| # | Script | Category | Module |
|---|--------|----------|--------|
| 1 | `generate_standards_index.py` | Producer | `scripts.producers.generate_standards_index` |
| 2 | `analyze_standards_index_gaps.py` | Producer | `command_center.scripts.producers.analyze_standards_index_gaps` |
| 3 | `diff_standards_index.py` | Producer | `scripts.producers.diff_standards_index` |
| 4 | `seed_standards_prompts.py` | Producer | `scripts.producers.seed_standards_prompts` |
| 5 | `summarize_standards.py` | Summarizer | `scripts.summarizers.summarize_standards` |

## CLI Arguments

```text
--repo-root PATH                    Repository root override
--index-output-dir PATH             Standards index output directory
--index-path PATH                   Standards index YAML path
--categories-path PATH              Standards categories YAML path
--gap-output-dir PATH               Gap analysis output directory
--diff-output-dir PATH              Diff output directory
--prompt-output-dir PATH            Prompt seeds output directory
--pending-path PATH                 Pending rules YAML path
--healthview-root PATH              HealthView root directory
--diff-old-index PATH               Baseline index for diff step
--diff-fail-on POLICY               Diff fail policy (default: any)
--gap-max-show N                    Max gap candidates per source (default: 8)
--prompt-include-warn               Include warn severity in seeds
--prompt-formats FMT...             Prompt artifact formats
--artifacts-to-keep N               Orchestrator retention (default: 3)
--index-artifacts-to-keep N         Index retention (default: 5)
--gap-artifacts-to-keep N           Gap analysis retention (default: 5)
--diff-artifacts-to-keep N          Diff retention (default: 10)
--prompt-artifacts-to-keep N        Prompt seed retention (default: 5)
--timestamp ISO8601                 Timestamp override
--log-level LEVEL                   Logging verbosity (default: INFO)
```

## Storage Integration

- **Registry**: Uses `CatalogRegistry` for topic context
- **Context**: Uses `TopicContext` and `TopicStep` for structured execution
- **Artifacts**: Uses `write_report_artifacts` for output

## Invocation Pattern

### Full Pipeline

```bash
python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py \
  --repo-root . \
  --log-level INFO
```

### With Diff Baseline

```bash
python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py \
  --repo-root . \
  --diff-old-index .repo_studios/scripts/repo_standards_index.yaml.bak \
  --log-level DEBUG
```

## Runtime

- **Typical Duration**: 5-8 minutes
- **Variable factors**: Diff scope and prompt generation drive upper bound

## Supersedes

- `scripts/orchestrators/run_standards_gap_suite.py`
- `scripts/orchestrators/run_standards_index_cli.py`

## Dependencies

- External: pyyaml
- Internal: `CatalogRegistry`, `TopicContext`, `TopicStep`, `write_report_artifacts`

## Notes

- Primary orchestrator for Standards Integrity (Stage 6.1)
- Coordinates 5 scripts: index → gap → diff → prompt → summary
- Aligns HealthView and CommandView outputs
- Emits consolidated manifest, summary, and telemetry
