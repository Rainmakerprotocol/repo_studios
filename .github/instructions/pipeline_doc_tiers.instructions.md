---
description: Requirements for Tier-1/Tier-2 pipeline documentation and doc index usage
applyTo: 'docs/pipeline/**/*.md'
---
# Pipeline Doc Tiering & Doc Index Usage

## Mission
- Preserve a pristine canonical record for the Tier-1 Pipeline and its Tier-2 verticals.
- Keep the doc index artifacts accurate so agents can trust Tier metadata and heading structures.
- Guarantee every pipeline doc is dependable, versioned, and immediately traceable.
- For an end-to-end onboarding walkthrough (5W1H, workflows, template usage), see `docs/templates/pipeline_templates/tier_doc_system_instructions.md`; treat this file as the policy, and the system instructions as the execution playbook.
- Use `docs/pipeline/README.md` as the Copilot entry point and `docs/pipeline/pipeline_doc_map.md` for
   coverage/status lookups before editing any pipeline Markdown. Keep their status boards synchronized
   with the Tier docs you touch.

## Tier definitions
| Tier | Scope | Expectations |
| --- | --- | --- |
| Tier-1 | Canonical “spinal cord” documents (for example, `docs/pipeline/README.md`) | Must capture end-to-end flow, invariants, and cross-links to all Tier-2/Tier-3 docs. Every heading is unique repo-wide and mirrors doc index columns. |
| Tier-2 | Deep dives for a single stage or vertical (for example, `docs/pipeline/model_selection.md`) | Must inherit Tier-1 terminology, declare ownership, and describe inputs/outputs, failure modes, and telemetry hooks. Tier-2 documents now identify the Tier-3 horizontals they depend on and call out placeholders when deeper work is pending. |
| Tier-3 | Horizontal deep dives spanning multiple stages/verticals (for example, `docs/pipeline/tier3_safety_envelope_spec.md`) | Capture dense, reusable logic (safety envelopes, autonomy maturity, severity→action mapping, rollback semantics). Tier-3 docs never replace Tier-2 content; they inform multiple verticals and must be referenced by Tier-2/Tier-1 when their topics become gating dependencies. |

Templates for every tier live under `docs/templates/pipeline_templates/` (`tier1_pipeline_template.md`, `tier2_pipeline_template.md`, `tier3_pipeline_template.md`, and supporting how-tos). Duplicate the relevant template before drafting a new doc so section order, instruction blocks, and agent automation remain consistent. If you need a narrated checklist describing how to apply those templates in practice, consult `docs/templates/pipeline_templates/tier_doc_system_instructions.md`.

## Three-Layer Alignment Rules
- **Protect Tier-1 scope.** Only edit Tier-1 to add/remove a stage, resolve a contradiction, or install a stop-gate. Tier-1 may mention Tier-3 topics only via the Tier-3 index—never inline detail.
- **Tier-2 → Tier-3 reflex.** When a Tier-2 edit introduces reusable semantics (safety envelope nuance, autonomy maturity gates, severity/causality mapping, rollback semantics, operator↔agent boundaries, multi-step playbook logic, action lifecycle semantics), create/update the corresponding Tier-3 doc or add a labeled placeholder, then wire dependency breadcrumbs + gating checklists.
- **Tier-3 stewardship.** Tier-3 docs stay implementation-agnostic; they cite the Tier-2/Tier-1 dependents, define adoption tasks, and never modify Tier-1 directly.
- **Stop-gate + checklist propagation.** Any Tier-3 addition must add/refresh stop-gates in affected Tier-1/Tier-2 docs so contributors cannot bypass unfinished horizontals.
- **Doc/test/index enforcement.** Tier edits that change behavior must pair with follow-up code/tests plus `make doc-index` evidence. Treat doc-index updates as mandatory for every Tier-3 creation, Tier-2 gating change, or Tier-1 dependency shift.

## Tier Application Scenarios
- **Tier-1 use cases:** lifecycle storytelling, contradiction tracking, gap callouts, stage matrix summaries, stop-gate inventories. Tier-1 never houses semantic details; it points to Tier-2 verticals and the Tier-3 index when deeper semantics block progress.
- **Tier-2 use cases:** subsystem implementation plans, phased checklists, telemetry wiring, operator vs. agent role definitions, dependency breadcrumbs. Tier-2 owns the checklists that enforce Tier-3 adoption.
- **Tier-3 use cases:** safety/autonomy frameworks, taxonomy matrices, severity/causality mapping, rollback semantics, operator↔agent boundary contracts, multi-step playbook logic, lifecycle semantics reused across stages.
- **Instruction block guidance:** Every tier document needs an instruction block describing how future edits should be made, including when to escalate material to another tier and what evidence (tests, doc sweeps, doc_index outputs) must accompany changes.
- **Operational reflex:** After each edit, confirm whether new Tier-3 placeholders/docs, Tier-1 stop-gates, or Tier-2 dependency notes are required. Do not consider the documentation complete until those follow-up artifacts exist or are explicitly tracked.

## Doc index workflow
1. Author or update the relevant Tier file.
2. Run `make doc-index` (or `python .copilot_instructions/generate_doc_index.py --out latest`) to regenerate `.copilot_instructions/index_reports/latest_doc_index.csv` (+ bundle/md/json).
3. Query the CSV (for example, `rg -n "docs/pipeline" .copilot_instructions/index_reports/latest_doc_index.csv`) to confirm:
   - The doc appears with the right Tier label in the `tags`/`tier` columns.
   - All headings render exactly once and reflect the latest intent.
   - Tier-3 docs include horizontal topic labels (for example, `tier3_autonomy`) and the Tier-2/Tier-1 references they serve.
4. If headings collide or tiers regress, fix the Markdown before merging.
5. When editing Tier-2 or Tier-1 files that reference Tier-3 docs, rerun doc-index so the dependency graph (Tier-1 ↔ Tier-2 ↔ Tier-3) remains synchronized.
6. Record the doc-index timestamp and any regression suites you executed in the document’s Update Log table (Tier templates already include `Doc-index timestamp` and `Regression suites` columns—keep them populated so reviewers and automation can verify evidence). `tier_doc_system_instructions.md` shows what a compliant Update Log entry looks like if you need a model.
7. Update the status tables inside `docs/pipeline/README.md` and `docs/pipeline/pipeline_doc_map.md` so
   the central dashboards reflect the same state you just captured in the Tier doc.

## Checkbox report workflow
- `make doc-index` now automatically runs `make checkbox-report` first so the artifacts under `docs/pipeline/checkbox_report/outputs/` reflect the latest `[ ]` work. Launch the target directly (`make checkbox-report`) if you need a refresh while iterating on a doc.
- Treat `checkbox_report.md` as a planning aide: scan it before and after edits to understand pending work, contradictions, and similar tasks logged elsewhere. Use the CSV sibling when you need to sort by heading/file/tier or feed the data into spreadsheets.
- Whenever you add, resolve, or relocate checklists inside Tier docs, regenerate the checkbox report (or rerun `make doc-index`) and ensure the heading breadcrumbs and Tier labels align with the doc you touched.
- Link to specific checkbox entries when escalating work between tiers so reviewers and future agents can jump straight to the source section.

## Telemetry hybrid alignment rule
- For any Stage 1–12 edit that touches telemetry, history, correlation, exposure, propagation, delivery, or governance, cite the relevant plan under `docs/pipeline/telemetry_hybrid/` (TEMP files, Tier-2 verticals, or Tier-3 horizontals) so Tier-1 narratives stay grounded in the active workstreams.
- Update the checkbox report immediately after modifying those sections and ensure the CSV/MD breadcrumbs match the doc and stage you touched.
- Mirror status changes across tiers: progress recorded in a TEMP or Tier-2 plan must be echoed in the Tier-1 spine (and vice versa) before closing a task so every doc reflects the same gating decision.

## Tier reciprocity checklist
- When creating or updating a Tier-3 horizontal, immediately list the dependent Tier-1/Tier-2 sections inside that doc and refresh those dependents to point back to the new guidance (include stop-gate/checklist updates where applicable).
- When updating a Tier-2 vertical, re-evaluate whether its Tier-3 dependency list is accurate. Add placeholders for missing horizontals and link to the Tier-3 index until the doc exists.
- When editing Tier-1, document which Tier-2/Tier-3 artifacts gate each stage and ensure their Update Logs capture the same change (doc-index timestamp + regression suites).
- Update `docs/pipeline/telemetry_hybrid/tier3_autonomy_horizontals_index.md` (or the relevant index) whenever horizontals change status so discovery tooling stays accurate.

## Authoring checklist
- [ ] Include YAML front matter with `title`, `tier`, `audience`, `owners`, `status`, `version`, `updated_at`, `tags`, and `related_files` (Tier-3 docs must list the Tier-2/Tier-1 topics they serve in `related_files`).
- [ ] Declare the Tier explicitly in the first paragraph ("This is the Tier-1 canonical pipeline doc..." / "This Tier-3 horizontal covers...").
- [ ] Follow the canonical section order: Goals → System Context → Stage Narratives → Signals & Telemetry → Agent Instructions → Update Log. Tier-3 docs may add specialized sections (taxonomies, maturity matrices) but must still end with an Update Log.
- [ ] Embed agent instruction blocks so Repo_Studios can enforce invariants (for example, required sections, telemetry reminders, Tier labels).
- [ ] Document guarantees, dependencies, stop-gates, and escalation contacts for every stage or horizontal topic described. Tier-2 docs must explicitly list the Tier-3 horizontals they rely on; Tier-1 docs must call out Tier-3 contracts once they become gating items.
- [ ] Reference supporting Tier-2/Tier-3 docs with relative links and ensure each target doc reciprocates.
- [ ] After each Tier-2 pass, confirm whether new Tier-3 placeholders/docs, Tier-1 dependency tweaks, test updates, or doc-index sweeps are required—do not merge until each box is satisfied or explicitly tracked.
- [ ] Log every doc-index run and regression suite in the Update Log table so evidence remains auditable.

## Quality gates
- Tier-1 docs may only be edited in focused PRs that include doc-index regeneration evidence in the PR description.
- Tier-2 docs must include a "Sync with Tier-1" note and list the last commit hash or date of the Tier-1 source they reference.
- Tier-3 docs must include a "Sync with Dependents" note listing the Tier-2/Tier-1 documents that consume the horizontal guidance plus any open placeholders.
- No Tier doc may contain placeholder headings, TODO markers, or inline chat transcripts.
- Treat doc regressions like code regressions: add tests or lint hooks if needed.

## Update log
- 2025-11-28 — Initial tiering + doc index instructions published.