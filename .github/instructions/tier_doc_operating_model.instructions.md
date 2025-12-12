---
description: Operating contract for Tier-1 horizontal pipelines and Tier-2 vertical documents
applyTo: 'docs/pipeline/**/*.md'
---
# Tier Doc Operating Model

> Policy vs. Playbook: This file codifies the operating contract. For the companion “how to execute” walkthrough (5W1H, editing workflow, template usage), see `docs/templates/pipeline_templates/tier_doc_system_instructions.md`.

## Mental Model
- **Tier-1 = horizontal pipeline.** Each Tier-1 doc narrates an end-to-end route ("spinal cord") that spans every stage of the named pipeline. It should read like a control-plane storyboard: inputs → transformations → outputs → consumers. Tier-1 may reference Tier-2 and Tier-3 docs but never relies on them to stay comprehensible.
- **Tier-2 = vertical branch.** A Tier-2 doc drills into one slice of a Tier-1 stage (for example, Model Selection Stage 6). It inherits Tier-1 terminology, expands wiring diagrams, and captures module-level evidence. Tier-2 docs now identify the Tier-3 horizontals they depend on and declare placeholders when deeper treatment is required.
- **Tier-3 = horizontal depth.** Tier-3 docs capture reusable logic that spans multiple stages/verticals (safety envelopes, autonomy maturity models, severity→action mapping, rollback semantics, operator vs. agent boundaries). They live in their own files (named `tier3_<topic>.md`), receive doc-index entries, and are referenced—not embedded—by Tier-2/Tier-1 documents when the horizontal becomes a gating dependency.
- **Living artifacts.** All tiers are planning/implementation guides that evolve with the code. It is acceptable (and expected) to leave unchecked `[ ]` tasks that describe design or hardening work, provided each item is specific and discoverable by tooling later.
- **Navigation anchors.** Always start from `docs/pipeline/README.md` and `docs/pipeline/pipeline_doc_map.md`.
	They summarize folder layout, telemetry links, and the status boards you must refresh after every
	Tier edit.

## Responsibilities per Tier
| Tier | Scope | Required Output |
| --- | --- | --- |
| Tier-1 | Horizontal pipeline blueprint | Stage-by-stage narratives, cross-links to dependent tiers, contradiction/gap registry, change log. Must stay system-level (no file-level code unless cited as evidence). Tier-1 authors flag when a stage is blocked on Tier-3 work and add stop-gate checklists. |
| Tier-2 | Vertical implementation guide | Detailed wiring for a single stage/vertical, including inputs/outputs, telemetry hooks, failure modes, explicit sync note back to the parent Tier-1 stage, and a "Tier-3 dependencies" subsection listing required horizontals. |
| Tier-3 | Horizontal topic specification | Deep-dive taxonomies, safety/autonomy contracts, rollout plans, rollback semantics, or other cross-stage logic. Must enumerate dependent Tier-2/Tier-1 docs, define adoption tasks, and mirror the same evidence discipline as other tiers. |

> Templates for every tier live under `docs/templates/pipeline_templates/` (`tier1_pipeline_template.md`, `tier2_pipeline_template.md`, `tier3_pipeline_template.md`). Start from these scaffolds whenever you create or rebase a tier doc so section order, instruction blocks, and Update Log schemas stay consistent. `tier_doc_system_instructions.md` explains how to apply each template during onboarding.

## Cross-Layer Refinement Pattern
- **Tier-1 stability first.** Only edit Tier-1 when introducing/removing a stage, resolving a contradiction/gap, or adding a new stop-gate checklist. Tier-1 may gesture at Tier-3 topics (“see Tier-3 index”) but never embeds their content.
- **Tier-2 reflex.** Every Tier-2 edit must ask: _Does this concept really belong in Tier-3?_ If yes, create/update the Tier-3 doc (or add a clearly labeled placeholder), add dependency breadcrumbs, and expand gating checklists that reference the new horizontal.
- **Tier-3 stewardship.** Tier-3 edits never touch Tier-1 directly; instead they document shared semantics (safety envelopes, autonomy maturity, severity/causality mapping, rollback semantics, operator↔agent boundaries, multi-step logic, action lifecycle semantics) and reference the Tier-2/Tier-1 docs that consume them.
- **Agnostic instruction blocks.** When updating any tier, add/refresh instruction blocks that tell future contributors how to extend the doc without violating the three-layer contract. Keep the language pipeline-agnostic so the same operating model applies to every future horizontal.
- **Doc/test/index triad.** If a Tier-2 change alters behavior, always plan the follow-up code/tests plus doc-index regeneration. Tier-3 updates demand the same evidence so tooling can rely on the horizontals as canonical references.

## Tier Usage Playbook
- **When to spawn Tier-1 content:** Only when a brand-new horizontal pipeline (or major fork of an existing pipeline) comes online. Capture the lifecycle end-to-end before inviting Tier-2 authors so everyone knows where the new vertical will attach.
- **When to add or extend a Tier-2 vertical:** Whenever a Tier-1 stage needs concrete wiring, telemetry, or ownership detail. Tier-2 should be actionable enough for engineers/agents to implement work, but punt deep semantic debates to Tier-3 via placeholders and dependency breadcrumbs.
- **When to create/update Tier-3 horizontals:** As soon as a reusable concept (safety envelopes, causality taxonomies, autonomy guardrails, rollback semantics, multi-step logic, operator↔agent boundary rules) surfaces in more than one stage. Tier-3 captures the shared logic once, then each Tier-2 document references it.
- **Using instruction blocks:** Each tier includes an “Instruction Block” aimed at future editors describing prerequisites, doc-index/test expectations, and how to evaluate whether new material belongs in another tier. Keep these instructions pipeline-agnostic so other workstreams can inherit them.
- **Potential uses per tier:**
	- Tier-1 → governance dashboards, status/gap reporting, contradiction registries, and stop-gate inventories.
	- Tier-2 → subsystem design playbooks, phased checklists, telemetry diagrams, operator/agent hand-offs.
	- Tier-3 → semantic contracts, safety/autonomy playbooks, taxonomy matrices, maturity rubrics, rollback/recovery semantics, and multi-stage lifecycle rules.
- **How-to reminders:** After drafting any tier doc, (1) run doc-index regeneration, (2) update related change logs, (3) add or refresh dependency breadcrumbs, and (4) file follow-up tickets/tests for any implementation impact noted in the doc. Record the doc-index timestamp and regression suites in the Update Log table so reviewers (and automation) can verify the evidence trail.

## Authoring Guidelines
1. **Anchor Stage Order.** Tier-1 documents should keep a consistent lifecycle order. Adjustments are fine but must be justified in the doc so downstream Tier-2 authors know where to attach.
2. **Evidence, not speculation.** When referencing behavior, cite the repo artifact (file + section/test). If the behavior is aspirational, log it as a gap or `[ ]` enhancement rather than blending it with implemented flows.
3. **Agent-focused.** Treat telemetry/observability prose as instructions for future agents. Call out who consumes each signal today (often a human) and the intended agentic recipient later. Tier-2 docs should capture how an agent would hook into the vertical when the automation lands.
4. **Stable wiring surfaces.** Every Tier-1 stage should describe the seams (APIs, telemetry feeds, lifecycle markers) that Tier-2 verticals must respect. Tier-2 docs should mirror those seams and note deviations so we can reconcile them during hardening. When a seam spans multiple stages, capture it inside a Tier-3 doc instead of duplicating logic.
5. **Tier-3 placeholders & reciprocity.** Whenever a Tier-2 doc anticipates a horizontal deep dive, add a clearly labeled `Tier-3 Placeholder — <topic>` note so future passes know where to land the doc. After the Tier-3 file exists, ensure all referencing Tier-1/Tier-2 sections link to it and that the Tier-3 doc lists its dependents.
6. **Telemetry alignment.** Follow the telemetry hybrid rule from `pipeline_doc_tiers.instructions.md`: any Stage 1–12 edit touching telemetry, history, propagation, delivery, or governance must cite the relevant plan or Tier-3 horizontal under `docs/pipeline/telemetry_hybrid/` and refresh checkbox/doc-index evidence accordingly. If you need a worked example of what to log, reference the After-Editing checklist inside `tier_doc_system_instructions.md`.
7. **Status propagation.** After every Tier update, revise the status tables in `docs/pipeline/README.md`
	and `docs/pipeline/pipeline_doc_map.md` so contributors can see what is Pending, In Progress,
	Blocked, or Complete without re-reading each stage doc.

## Status & Task Hygiene
- Use the taxonomy from `.github/instructions/pipeline_doc_tiers.instructions.md` (`TODO`, `Planned`, `In Progress`, `Partial`, `Complete`, `Blocked`, etc.). Avoid marking every stage `Partial` by default; reflect reality so we can prioritize.
- `[ ]` checkboxes should appear near the relevant stage/section, describe observable work, and (when possible) mention the file/service that will change. Treat them as the source data for future discovery scripts.
- **No code edits from Tier docs.** These files coordinate implementation but never directly modify runtime behavior. Changes triggered by a doc must happen in follow-up code/infra PRs with references back to the doc section.
- **Tier-3 sync notes.** Tier-2 and Tier-1 docs must track which Tier-3 horizontals they depend on; Tier-3 docs include a "Sync with Dependents" block enumerating consuming files plus outstanding adoption tasks.

## Reciprocity checklist
- When creating/updating a Tier-3 horizontal, immediately refresh the dependent Tier-1/Tier-2 sections (stop-gates, dependency lists, checklists) and update the Tier-3 index (`docs/pipeline/telemetry_hybrid/tier3_autonomy_horizontals_index.md` or its peer) so discovery tooling stays accurate.
- When evolving a Tier-2 vertical, confirm whether new horizontals are required. Add placeholders, link to the Tier-3 template if a doc must be authored, and ensure Tier-1 reflects the same gating dependency.
- When editing Tier-1 stages, verify that every referenced Tier-2/Tier-3 artifact has a fresh doc-index entry and Update Log row (with timestamp + regression suites) describing the same change.

## Checkbox report expectations
- Before editing a Tier doc, open `docs/pipeline/checkbox_report/outputs/checkbox_report.md` (or its CSV sibling) to understand outstanding `[ ]` tasks, contradictions, and nearby work with similar attributes. The report is regenerated automatically whenever `make doc-index` runs, and you can refresh it directly with `make checkbox-report` while drafting.
- While authoring, mirror any new or resolved checkboxes in the report: regenerate it, verify the headings and tiers match the section you touched, and link to notable entries when coordinating work with other tiers.
- Use the CSV output when you need structured filtering (for example, “show all unchecked tasks under Model Selection Tier-2”), then update the originating docs so the narrative and the report stay in lockstep.

## Review Expectations
- When drafting Tier-1 content imported from outside the repo, explicitly mark assumptions until validated against repository evidence.
- Before promoting an idea from Tier-1 to Tier-2, agree on the desired behavior and consumer (human vs. agent) so the vertical stays grounded in the long-term autonomy plan.
- Keep the change logs active. Every significant update (new stage, resolved contradiction, major evidence sweep) deserves a dated entry so future contributors can trace the narrative.
- During reviews confirm that Tier-2 edits mention required Tier-3 horizontals, that placeholders are clearly labeled, and that doc-index updates include any new Tier-3 files.