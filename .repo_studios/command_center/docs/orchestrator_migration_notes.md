# Orchestrator Migration Notes — 2025-11-30

## Purpose

Show how the legacy Command Center orchestrators would integrate the Phase 2 helper modules if they
were rewritten today. The goal is to give reviewers parity confidence before we begin migrating the
existing entry points.

Each section covers:

- helper wiring (topic pipeline, telemetry emission, summarizer invocation)
- retention or flag handling carryover
- relevant tests that already exercise comparable flows

## Test Execution Telemetry (legacy: `run_pytest_log_capture.py`)

### Proposed Structure

```python
from command_center.scripts.libraries import (
    TopicContext,
    TopicStep,
    build_topic_pipeline,
    build_pipeline_telemetry,
    CatalogRegistry,
    load_summarizer,
    run_summarizer,
)

registry = CatalogRegistry()
registry.register(
    script_path=".repo_studios/scripts/orchestrators/run_pytest_log_capture.py",
    topic="test-execution-telemetry",
    role="orchestrator",
)

context = TopicContext(paths=paths_cfg, options=options_cfg)

pipeline = build_topic_pipeline(
    steps=[
        TopicStep(name="collect-logs", runner=collect_log_reports_step),
        TopicStep(name="analyse", runner=analyse_logs_step, continue_on_failure=False),
        TopicStep(name="summarize", runner=summarize_logs_step),
    ]
)

result = pipeline.run(context)
result.raise_for_failure()

telemetry = build_pipeline_telemetry(
    result,
    viewer="healthview",
    topic="test-execution-telemetry",
    run_slug=context.metadata["run_slug"],
)
write_report_artifacts(
    viewer="healthview",
    topic="test_execution_telemetry",
    slug=context.metadata["run_slug"],
    manifest_payload=telemetry.as_dict(),
    artifacts=context.metadata["artifacts"],
)
```

### Step Notes

- `collect_log_reports_step` drives the existing producer sequence (inventory → collector) and caches
  artifact paths on the `TopicContext` metadata.
- `analyse_logs_step` slots in the churn heatmap and hardening analysis CLIs using standard CLI
  builders; failures stop the pipeline because downstream summarization depends on the outputs.
- `summarize_logs_step` dynamically loads `generate_test_log_health_report.py` via
  `load_summarizer` and records the Markdown run summary in `TopicContext` for mirroring.

### Validation Hooks

- Existing suites `tests/tests_command_center/orchestrators/test_run_pytest_log_capture.py` and
  `tests/tests_command_center/test_topic_pipeline.py` already cover log retention and pipeline
  error handling.

## Fault Diagnostics (replaces legacy `run_fault_pipeline.py`)

### Proposed Structure

```python
from command_center.scripts.libraries import (
    CatalogRegistry,
    TopicContext,
    TopicStep,
    build_topic_pipeline,
    build_pipeline_telemetry,
)

registry = CatalogRegistry()
registry.register(
  script_path=".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py",
  topic="fault-diagnostics",
  role="orchestrator",
)

context = TopicContext(paths=paths_cfg, options=options_cfg)

pipeline = build_topic_pipeline(
    steps=[
        TopicStep(name="producer", runner=faulthandler_producer_step),
        TopicStep(name="consumer", runner=faulthandler_consumer_step),
        TopicStep(name="summary", runner=faulthandler_summary_step, continue_on_failure=True),
    ],
    stop_on_failure=True,
)

result = pipeline.run(context)
result.raise_for_failure()

telemetry = build_pipeline_telemetry(
    result,
    viewer="healthview",
    topic="fault-diagnostics",
    run_slug=context.metadata["run_slug"],
)
```

### Step Notes

- `faulthandler_producer_step` wraps the legacy CLI flags (`--runs-dir`, `--artifacts-to-keep`) while
  storing the generated run folder in context metadata.
- `faulthandler_consumer_step` consumes the crash artifacts and appends regression matrices to
  metadata for later mirroring.
- `faulthandler_summary_step` leverages `load_summarizer` when the summarizer is available, but
  `continue_on_failure=True` keeps the telemetry flow alive if the summarizer only emits warnings.

### Validation Hooks

- `tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py` validates
  producer/consumer handoffs, summarizer wiring, and retention semantics that the migration must
  preserve.

## Docs Health (legacy suite of producer scripts)

### Proposed Structure

```python
from command_center.scripts.libraries import TopicStep, build_topic_pipeline, CatalogRegistry

registry = CatalogRegistry()
registry.register(
    script_path=".repo_studios/scripts/orchestrators/run_docs_health.py",
    topic="docs-health",
    role="orchestrator",
)

pipeline = build_topic_pipeline(
    steps=[
        TopicStep(name="index", runner=build_doc_index_step),
        TopicStep(name="anchors", runner=anchor_validation_step),
        TopicStep(name="analysis", runner=doc_health_analysis_step),
        TopicStep(name="summary", runner=docs_health_summary_step),
    ]
)
```

### Step Notes

- Utility producers such as `generate_anchor_inventory.py` would run inside step runners that pull in
  shared CLI builders.
- Final summary step mirrors Markdown and JSON artifacts using `write_report_artifacts` to ensure both
  CommandView and Healthview stay aligned.

### Validation Hooks

- `tests/tests_command_center/docs_health/` (planned) should adapt existing producer fixtures; the
  topic pipeline test already confirms skip/failure mechanics.

## Standards Integrity (legacy: `run_standards_gap_suite.py` + `run_standards_index_cli.py`)

- Merge both orchestrators into a single pipeline with steps for index regeneration, gap analysis,
  diffing, and summarization.
- Register each script through `CatalogRegistry` so the parity matrix can surface new coverage.
- `TopicPipeline` run result feeds `build_pipeline_telemetry` and the `write_report_artifacts`
  helper to publish Healthview bundles.
- Tests: reuse `tests/tests_command_center/standards/test_run_standards_gap_suite.py` plus new topic
  pipeline fixtures once orchestrator code moves.

## Dependency & Import Hygiene (legacy: `run_batch_cleanup.py`)

- Sequence lint, mypy, placeholder scan, and typecheck steps using `TopicPipeline` and capture
  retention settings in `TopicContext.options`.
- Summaries can be emitted via a small helper summarizer invoked through `load_summarizer` to keep
  parity with the existing Markdown output.
- Tests: existing batch cleanup smoke tests combine with the helper unit tests to ensure ≥80% coverage.

## Monkey Patch Oversight

- The orchestrator wraps the scan, classification, and risk scoring scripts as pipeline steps, with
  telemetry summarising counts per severity.
- Catalog entries help produce the parity matrix that confirms full coverage of the monkey patch suite.

## Implementation Checklist

1. Instantiate `TopicContext` with shared CLI builders before invoking step runners.
2. Register orchestrator scripts and major producers via `CatalogRegistry` to aid documentation
   parity checks.
3. After running `TopicPipeline`, emit telemetry with `build_pipeline_telemetry` and include the
   payload in `write_report_artifacts` calls so Healthview manifests stay in sync.
4. For summarizer integrations, load the target script dynamically and raise `SummarizerError` when
   failures occur so orchestrators can surface precise diagnostics.
5. Mirror artifacts to both `commandview/<topic>/<timestamp>/` and
   `healthview/<topic>/<timestamp>/` directories to maintain viewer parity.

## References

- Helper usage guide: `.repo_studios/command_center/docs/code_library/helper_usage_patterns.md`
- Phase 2 implementation plan: `docs/automation/orchestrator_implementation.md`
- Shared helper modules: `.repo_studios/command_center/scripts/libraries/`
- Test suites: `.repo_studios/tests/tests_command_center/`
