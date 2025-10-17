# Agent Notes Index

This workspace hosts timestamped YAML entries that capture substantive actions, discoveries, and decisions made by the coding agent. Treat it as a lightweight knowledge base that agents and developers can reference over time.

## Folder Taxonomy

- `automation/` – Notes about new or updated Make targets, CI wiring, or automation behaviors.
- `governance/` – Decisions related to maturity gates, retention policies, compliance, or security posture.
- `inventory/` – Findings and updates about cataloging assets, schemas, or indexing strategies.
- `meta/` – Collaboration workflows, protocol updates, or process retrospectives.
- `migration/` – Step logs for moving artifacts from legacy locations into the refreshed `.repo_studios/` structure.
- `reports/` – Observations tied to health suites, analytics outputs, or reporting improvements.
- `standards/` – Changes to global/project standards, documentation naming, or enforcement rules.
- `_templates/` – Reusable YAML skeletons for consistent note authoring.

## File Naming Convention

- Place entries in the relevant subfolder.
- Use filenames of the form `<topic>_<YYYY-MM-DD_HHMMSS>.yaml` (24-hour clock, UTC).
  - Example: `inventory/inventory_schema_review_2025-10-17_143000.yaml`

## YAML Structure

Each note should capture:

- `title`: Concise description of the action or insight.
- `timestamp`: ISO-8601 with timezone (preferably UTC).
- `author`: Usually `copilot`, but list any human collaborators.
- `phase`: Reference the current phase from `repo_studios_build_plan.md`.
- `summary`: Short paragraph explaining the what/why.
- `details`: Bullet list or nested structure with supporting information.
- `inputs`: Source files, commands, or discussions that informed the work.
- `outputs`: Artifacts created or updated.
- `status`: `planned`, `in-progress`, `blocked`, or `complete`.
- `follow_up`: Next steps or open questions.
- `tags`: Array of quick filters (e.g., [`inventory`, `schema`, `phase1`]).

An example template is stored at `_templates/note_template.yaml`.

Maintain clean YAML (2-space indentation, UTF-8 ASCII) so notes remain machine-readable.
