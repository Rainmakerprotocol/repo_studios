# Command Center Helper Usage Patterns — 2025-11-30

## Scope

Capture how the Phase 2 shared helpers are intended to be wired into topic orchestrators so
engineers and agents can reuse them consistently. Each section lists the helper location,
dependencies, execution contract, and verification tests.

## Topic Pipeline Assembly

- **Module:** `.repo_studios/command_center/scripts/libraries/topic_pipeline.py`
- **Primary exports:** `TopicContext`, `TopicStep`, `TopicPipeline`, `build_topic_pipeline`,
  `step_success`, `step_skipped`, `step_failed`, `SkipTopicStep`
- **Usage pattern:**

  ```python
  from command_center.scripts.libraries import (
      TopicContext,
      TopicStep,
      build_topic_pipeline,
      step_failed,
      step_success,
  )

  context = TopicContext(paths=paths_cfg, options=options_cfg)

  def generate_inventory(ctx: TopicContext):
      inventory_path = producers.generate_inventory(ctx.paths.inventory_args())
      ctx.add_metadata("inventory_path", inventory_path)
      return step_success(payload={"inventory_path": inventory_path})

  def analyse_inventory(ctx: TopicContext):
      try:
          return step_success(detail="analysis_complete")
      except ValueError as exc:
          return step_failed(detail=str(exc))

  pipeline = build_topic_pipeline(
      steps=[
          TopicStep(name="inventory", runner=generate_inventory),
          TopicStep(name="analysis", runner=analyse_inventory, continue_on_failure=False),
      ],
      stop_on_failure=True,
  )

  result = pipeline.run(context)
  result.raise_for_failure()
  ```

- **Notes:**
  - `TopicContext` travels across steps; store shared data via `add_metadata`.
  - Prefer `step_success` / `step_failed` over plain dicts so downstream logging stays uniform.
  - Raise `SkipTopicStep` when a step should register as skipped without failing the run.
  - The pipeline logger emits DEBUG/INFO messages that respect the orchestrator log level.
- **Verification:** `pytest .repo_studios/tests/tests_command_center/test_topic_pipeline.py`
  exercises ordering, skip handling, failure propagation, and logging expectations.

## Summarizer Runner Integration

- **Module:** `.repo_studios/command_center/scripts/libraries/summarizer_runner.py`
- **Primary exports:** `load_summarizer`, `run_summarizer`, `SummarizerError`
- **Usage pattern:**

  ```python
  from pathlib import Path
  from command_center.scripts.libraries import load_summarizer, run_summarizer

  summarizer_path = Path(".repo_studios/command_center/scripts/summarizers/generate_function_analysis.py")
  run_helper = load_summarizer(summarizer_path, module_name="generate_function_analysis")
  run_summarizer(run_helper, argv=["--repo-root", str(repo_root)], name="function_analysis")
  ```

- **Notes:**
  - Always pass a stable `module_name` so repeated runs reuse the import cache across orchestration
    steps.
  - Call `run_summarizer` immediately after loading; non-zero exit codes raise `SummarizerError`
    for consistent pipeline failure handling.
  - Keep summarizers importing from `command_center.scripts.libraries.cli` to share CLI config.
- **Verification:** `pytest .repo_studios/tests/tests_command_center/test_summarizer_runner.py`
  covers module loading, error surfacing, and missing `run()` safeguards.

## Telemetry Emitters

- **Module:** `.repo_studios/command_center/scripts/libraries/telemetry_emitters.py`
- **Primary exports:** `TopicTelemetry`, `build_pipeline_telemetry`
- **Usage pattern:**

  ```python
  from command_center.scripts.libraries import build_pipeline_telemetry

  telemetry = build_pipeline_telemetry(
      pipeline_result,
      viewer="healthview",
      topic="test-execution-telemetry",
      run_slug=timestamp_slug,
  )
  manifest_writer.write_manifest(telemetry.as_dict())
  ```

- **Notes:**
  - Feed the `TopicPipelineResult` returned by `TopicPipeline.run` to capture per-step timings and
    payloads.
  - `run_slug` should match the timestamp used in report artifact names so manifest lookups stay in
    sync.
  - `TopicTelemetry.as_dict()` produces ISO-8601 timestamps; no additional serialization required
    before JSON encoding.
- **Verification:** `pytest .repo_studios/tests/tests_command_center/test_telemetry_emitters.py`
  validates payload structure, timestamps, and metadata propagation.

## Catalog Registry

- **Module:** `.repo_studios/command_center/scripts/libraries/catalog_registry.py`
- **Primary exports:** `CatalogRegistry`, `CatalogEntry`
- **Usage pattern:**

  ```python
  from command_center.scripts.libraries import CatalogRegistry

  registry = CatalogRegistry()
  registry.register(
      script_path=".repo_studios/scripts/producers/generate_test_log_health_report.py",
      topic="test-execution-telemetry",
      role="producer",
  )

  seen_topics = registry.topics()
  topic_entries = registry.entries_for_topic("test-execution-telemetry")
  ```

- **Notes:**
  - Paths are normalised to POSIX style, so pass repo-relative strings to avoid duplicate keys.
  - `register` raises if the same script is registered with conflicting topic metadata—handle this
    in tests to catch misclassified orchestrator wiring.
  - Use `all_entries()` when building parity matrices or documentation tables.
- **Verification:** `pytest .repo_studios/tests/tests_command_center/test_catalog_registry.py`
  ensures registration, conflict detection, and bulk extension stay reliable.

## CLI Integration Checklist

- Build CLI configs with `command_center.scripts.libraries.cli.build_standard_paths` and
   `build_standard_options` before invoking the helpers above.
- Wrap orchestration steps inside `TopicStep` definitions, reuse the shared `TopicPipeline`, and
   propagate failure state with `TopicPipelineResult.raise_for_failure()` when you need hard exits.
- Emit telemetry via `build_pipeline_telemetry(...).as_dict()` and persist with
   `write_report_artifacts` so CommandView and Healthview remain aligned.
- When summarizers are part of the pipeline, load the script dynamically and route failures through
   `SummarizerError` so a single error path governs retries.
- Record helper adoption in documentation or parity matrices by extracting registered entries from
   `CatalogRegistry`.

## References

- Helper source tree: `.repo_studios/command_center/scripts/libraries/`
- Test coverage: `.repo_studios/tests/tests_command_center/test_topic_pipeline.py`,
  `test_summarizer_runner.py`, `test_telemetry_emitters.py`, `test_catalog_registry.py`
- Orchestrator implementation plan: `docs/automation/orchestrator_implementation.md`
- Naming conventions: `.repo_studios/command_center/docs/naming_conventions.md`
