# Helper Adoption Audit CLI Specification

**Status:** Implemented (2025-11-03)

## Purpose

Provide a consistent, scriptable way to inventory which Repo Studios scripts import shared command center helpers so we can monitor adoption progress during Phase 4 and prepare for automated enforcement. The CLI replaces the ad-hoc spreadsheet currently maintained during manual extraction.

## Objectives

- Enumerate helper usage across `.repo_studios/scripts/**` with slug-level granularity.
- Classify each script by adoption state (e.g., "uses shared helper", "legacy inline copy", "not applicable").
- Emit machine-readable artifacts for dashboards and guardrail validation.
- Integrate with existing command center orchestration patterns (shared CLI builders, retention helpers, logging).

## CLI Contract

- **Executable:** `.repo_studios/scripts/producers/audit_helper_adoption.py` (new)
- **Entry point:** `run(argv: Sequence[str] | None = None) -> int` with `main()` shim
- **Core flags:** `--repo-root`, `--output-dir`, `--helpers=<list>`, `--format=json|markdown`, `--keep=<int>`
- **Default helpers:** `slugify_relative`, `copy_latest_artifact`, `write_report_artifacts`, `build_standard_paths`, `build_standard_options`
- **Outputs:** `helper_adoption-YYYY-MM-DD.json`, optional Markdown summary, retention via `write_report_artifacts`
- **Exit codes:** `0` success, `1` validation error (e.g., missing helper), `2` runtime failure

## Inputs & Data Sources

1. **Helper catalog** – Import from `libraries/__init__.py` to confirm helper availability; fallback to explicit path list when needed.
2. **Script inventory** – Reuse the latest Command Center inventory JSON if present; otherwise walk `.repo_studios/scripts/` using the same ignore rules captured in the inventory producer.
3. **Allow-list integration** – Cross-reference `docs/automation/guardrails/allowed_targets.yaml` to scope which directories require tracking.

## Output Artifacts

- **JSON report** – Structured payload per helper with adoption stats per slug (see Schema section below).
- **Markdown summary** (optional via `--format markdown` or default dual output) – Operator-friendly table highlighting gaps.
- **Log stream** – Structured key/value logging via `configure_basic_logging` matching existing producers.

### JSON Schema (Draft)

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-10-31T14:52:00Z",
  "repo_root": ".",
  "helpers": [
    {
      "name": "slugify_relative",
      "status": {
        "adopted": 12,
        "legacy": 3,
        "not_applicable": 45
      },
      "files": {
        "adopted": ["scripts/producers/generate_function_inventory.py"],
        "legacy": ["scripts/summarizers/legacy_slugify.py"],
        "not_applicable": []
      }
    }
  ]
}
```

## Implementation Notes

1. **Path resolution** – Reuse `build_standard_paths` / `build_standard_options` with a new `PathsConfig` entry for the adoption report directory (e.g., `.repo_studios/command_center/reports/helper_adoption/`).
2. **Analysis** – Parse each Python file, looking for imports from `command_center.scripts.libraries`; fall back to static string search for legacy alias patterns (e.g., `_slugify_relative`).
3. **Retention** – Use `write_report_artifacts` with keep-count derived from the CLI options (default `keep=3`).
4. **Integration** – Expose the CLI through the command center orchestrator once manual validation confirms accuracy.
5. **Testing** – Add unit tests under `tests/tests_producers/test_audit_helper_adoption.py` with fixtures that simulate adopted vs legacy scripts; ensure Windows paths handled correctly.
6. **Telemetry** – Feed summary stats into the planned `metrics_summary.json` during automation dry runs to quantify helper adoption impact.

## Open Questions

- Should the CLI run during every orchestrator invocation or only on demand?
- Do we need to track per-function granularity (e.g., partial helper adoption within a script)?
- How should we integrate the report into weekly progress briefings (e.g., auto-attach Markdown summary)?
- When automation begins, should the CLI block runs if adoption falls below a threshold for target helpers?

## Implementation Summary (2025-11-03)

- **CLI location:** `.repo_studios/command_center/scripts/producers/audit_helper_adoption.py`
- **Outputs:** Timestamped `helper_adoption.json` (schema version `1.0`) and optional Markdown summary written via `write_report_artifacts` with latest pointers.
- **Scope:** Loads allowed targets from `docs/automation/guardrails/allowed_targets.yaml`, audits helper imports vs. legacy definitions, and aggregates counts per slug and helper.
- **Testing:** Covered by `tests/tests_producers/test_audit_helper_adoption.py`, which exercises adoption/legacy detection, format filtering, and pointer mirroring.
- **Follow-on consumers:** Metrics summary ingestion and weighted briefing template can now source helper adoption data directly from the JSON artifact.

## Next Steps

1. Wire the helper adoption report into Phase 4 rehearsal playbooks (e.g., reference in automation dry-run README output).
2. Evaluate whether to run the CLI inside the command center orchestrator once adoption tracking stabilizes.
3. Extend the Markdown summary with guardrail guidance before automation writes begin.
