# Repo Studios Build Plan

_Last updated: 2025-10-17_

This plan converts the alignment worksheet into a phased roadmap for establishing a reusable Repo Studios toolbox that remains isolated from product code while serving AI-first workflows.

## Guiding Principles
- Keep `.repo_studios/` as the canonical hidden workspace for tooling, docs, reports, and tests.
- Maintain rich inventories with categorical tags so coding agents can locate orchestrators, CLIs, reports, and standards quickly.
- Separate global standards from project-specific overrides while retaining clear provenance (version metadata in document headers).
- Log meaningful actions in `agent_notes/<description>_YYYY-MM-DD_hhmmss.txt` to preserve history across migrations.
- Favor automation that is discoverable, composable, and namespaced (e.g., `studio-*` Make targets).

## Phase 0 — Alignment (Complete)
- Drafted and iterated on `alignment_notes_temp.md` to capture context, questions, and decisions.
- Created `alignment_protocol.md` as the reusable collaboration blueprint.
- Outcome: shared understanding of goals, constraints, and desired tooling behavior.

## Phase 1 — Foundation & Inventory

1. **Inventory Schema** _(In progress)_
   - Completed: published `inventory_schema_spec.md`, machine-readable enums, authoring template, docs/scripts/tests catalogs with Codacy validation, the `studio-validate-inventory` CLI + Make target with docs, the `render_inventory_views.py` pipeline generating docs/scripts/tests summaries and dashboard metrics, validator path-existence enforcement with config support, report artifacts relocated to `reports/<topic>/latest` with compat stubs, and `inventory_reports.md` documenting CI consumption.
   - Outstanding: expand secondary views with additional dashboards (e.g., dependency graphs) and wire reports into CI smoke jobs.
2. **Directory Layout Confirmation** _(Completed)_
   - Completed: standardized `.repo_studios/` subfolders to `docs/`, `scripts/`, `reports/`, and `tests/` to aid agent discovery, retaining legacy content read-only under `.repo_studios_legacy/`.
   - Documented legacy-to-current path mapping for human developers in `docs/directory_layout.md`, including notes on historical references.
3. **Documentation Scope Split** _(In progress)_
   - Completed: scaffolding for `docs/standards/global/` and `docs/standards/project/` with authoring guidance, metadata headers, and migrated standards (`std-global-code-cleanup.md`, `std-global-markdown-authoring.md`, `std-global-mission-parameters.md`, `std-global-prompt-engineering.md`, `std-global-chainlit-ui.md`, `std-global-html-coding.md`, `std-global-python-engineering.md`).
   - Outstanding: document any project-specific overrides that diverge from global standards and note rationale where they exist.
4. **Naming Conventions** _(Completed)_
   - Documented patterns in `docs/naming_conventions.md` covering files, scripts, tests, and inventory identifiers.
5. **Plan Artifacts** _(Completed)_
   - Added reusable templates in `docs/templates/` for agent notes and Repo Studios structural checklists, plus `docs/automation/ci_metrics_checks.md` documenting health guardrails.

## Phase 2 — Migration & Normalization

1. **Migration Playbook**
   - Author a structured guide covering scope, prerequisites, execution steps, validation, and rollback for moving assets from `repo_studios_legacy/` to `.repo_studios/`.
   - Encourage agents to log major moves in `agent_notes/` using the timestamped convention.
2. **Directory Restructuring**
   - Relocate or recreate assets in the new `.repo_studios/` layout while keeping the legacy copy read-only for reference.
   - Update imports, relative paths, and config references to match the new structure.
3. **Makefile & Automation Rewire**
   - Refactor the legacy Makefile to point at the new paths, introducing namespaced `studio-*` targets.
   - Add a manifest target (e.g., `make studio-help`) that enumerates available automation tiers and purposes.
4. **Inventory Population**
   - Fill the inventory YAML with entries for docs, scripts, reports, tests, and standards, marking mandatory vs optional components.

## Phase 3 — Automation & Quality Gates

1. **Testing Strategy**
   - Keep tests isolated inside `.repo_studios/tests` (or renamed folder) and document how CI jobs should invoke them.
   - Review existing pytest suites for path assumptions; fix or mark legacy items that require updates.
2. **Secret Handling Baseline**
   - Supply starter templates (`.env`, `.env.example`) and guidance for integrating with secret managers (Vault, AWS Secrets Manager, etc.).
   - Explain how adopting these patterns reduces ad-hoc monkey patches and hard-coded paths.
3. **Environment Configuration**
   - Decide on the baseline Python version and dependency management approach (requirements file, `pyproject.toml`, etc.).
   - Draft a living `SETUP.md` outlining bootstrap steps once tooling layout stabilizes.
4. **Access Patterns**
   - Propose layered configuration (default config file + environment variables + CLI flags) so restrictions can tighten as projects mature.

## Phase 4 — Reporting & Observability Enhancements

1. **Report Normalization**
   - Upgrade legacy report samples to meet Repo Studios standards (formatting, lint, clarity).
   - Convert multi-section, AI-centric reports to YAML for structured consumption while retaining lighter formats where appropriate.
2. **Timeline vs Latest Artifacts**
   - Implement a hybrid approach: archive suite-level snapshots with timestamps while maintaining a pointer to the most recent run.
3. **Metric Expansion**
   - Identify additional signals (dependency freshness, documentation drift, onboarding friction) to incorporate into future reports.
4. **Diff & Gap Tooling**
   - Provide automated comparisons between global standards and project overrides, highlighting additions, removals, and severity shifts.

## Phase 5 — Governance & Onboarding Assets

1. **Project Maturity Checklist**
   - Draft staged governance (scaffold → growth → mature) with entry criteria, required automation, retention policies, and secret handling expectations.
2. **Alignment Protocol Evolution**
   - Expand `alignment_protocol.md` with real-world learnings, including references to the new governance checklist and reporting cadence.
3. **Project Scope Document**
   - Maintain an up-to-date scope/roadmap document summarizing goals, dependencies, and current phase status.
4. **Automation Notifications (Optional Later)**
   - Evaluate whether to automate notifications for new `agent_notes/` entries or rely on manual review.

## Parallel Workstreams

- **Sample Data Refresh**: Improve or regenerate sample fixtures to meet current lint and formatting standards while keeping curated examples in-repo.
- **Hard-Coded Path Cleanup**: Identify stale paths (e.g., `/home/founder/jarvis2`) and replace them with configurable settings.
- **Legacy Dependency Audit**: Confirm which scripts rely on external tools (mypy, ruff, lizard, etc.) and note bootstrap requirements.

## Deliverables Snapshot

- Inventory YAML (authoritative catalog)
- Structured migration playbook
- Updated directory layout with namespaced Make targets
- Secret handling templates and guidance
- Reporting normalization plan with YAML targets
- Governance checklist and onboarding docs

_Use this plan as the living map. Update phase statuses, add sub-tasks, and link to implementation notes in `agent_notes/` as we progress._
