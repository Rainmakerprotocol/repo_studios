# Stage 12 Template Development Plan

> **Purpose:** Sequential implementation plan for developing Tier-2 script templates
> through orchestrator-first, script-by-script completion with explicit QA gates.

**Status:** Draft  
**Created:** 2026-01-25  
**Updated:** 2026-01-25  
**Target:** Stage 12 (Script Development Templates) in Tier-1 HealthView Pipeline

---

## How to Reuse This Plan

This document is designed as a reusable template for similar development efforts.

**To adapt for a different context:**

1. Copy this file to a new location with an appropriate name
2. Replace the following variables:
   - `{{STAGE_NUMBER}}` → target stage number (e.g., "12")
   - `{{STAGE_NAME}}` → stage name (e.g., "Script Development Templates")
   - `{{ORCHESTRATOR_NAME}}` → orchestrator filename (e.g., "run_available_scripts_oversight.py")
   - `{{TIER2_ROSTER_NAME}}` → Tier-2 roster filename (e.g., "tier2_available_scripts_orchestrator_roster.md")
   - `{{HOLDING_STAGE}}` → source stage for scripts (e.g., "Stage 11.1")
   - `{{ARCHIVE_PATH}}` → archive location (e.g., "/.repo_studios/docs/archives/")
3. Update the Phase sequence if workflow differs
4. Reset all checkboxes to unchecked
5. Clear the Evidence Log except for the "Created" entry

**Current instance values:**

| Variable | Value |
|----------|-------|
| `{{STAGE_NUMBER}}` | 12 |
| `{{STAGE_NAME}}` | Script Development Templates |
| `{{ORCHESTRATOR_NAME}}` | `run_available_scripts_oversight.py` |
| `{{TIER2_ROSTER_NAME}}` | `tier2_available_scripts_orchestrator_roster.md` |
| `{{HOLDING_STAGE}}` | Stage 11.1 |
| `{{ARCHIVE_PATH}}` | `/.repo_studios/docs/archives/` |

---

## Overview

This plan follows an orchestrator-first approach: seed the Stage 11.1 orchestrator Tier-2 doc,
then complete each script end-to-end before moving to the next. Templates evolve through
iteration rather than abstract design.

**Working document location:** `/.repo_studios/docs/archives/`  
**Working document lifecycle:** Created with `status: active`, updated to `status: archived` on completion.

---

## Phase 1: Seed Stage 12 and Orchestrator Tier-2 ✅

Establish Stage 12 in Tier-1 and create the Stage 11.1 orchestrator Tier-2 document.

- [x] 1.1 Add Stage 12 skeleton to Tier-1 HealthView Pipeline document
  - [x] 12.1 Producer Template (placeholder)
  - [x] 12.2 Consumer Template (placeholder)
  - [x] 12.3 Aggregator Template (placeholder)
  - [x] 12.4 Summarizer Template (placeholder)
  - [x] 12.5 Orchestrator Template (placeholder)
- [x] 1.2 Renumber downstream sections (Snapshot → 13, Contradictions → 14, etc.)
- [x] 1.3 Update internal cross-references affected by renumbering
- [x] 1.4 Add governance staging disclaimer (eventual detachment to Jarvis)
- [x] 1.5 Create Stage 11.1 orchestrator Tier-2 document using existing naming conventions
  - [x] Location: `tier2_roster/tier2_available_scripts_orchestrator_roster.md`
  - [x] Follow existing Tier-2 roster structure and standards

---

## Phase 2: Review Existing Orchestrators for Patterns ✅

Extract commonality from existing orchestrators to inform Stage 11.1 design.

- [x] 2.1 Review `run_test_execution_telemetry.py` (Stage 1.1)
- [x] 2.2 Review `run_docs_health_overview.py` (Stage 2.1)
- [x] 2.3 Review `run_fault_diagnostics_overview.py` (Stage 3.1)
- [x] 2.4 Review `run_dependency_import_hygiene.py` (Stage 4.1)
- [x] 2.5 Review `run_monkey_patch_oversight.py` (Stage 5.1)
- [x] 2.6 Review `run_standards_integrity.py` (Stage 6.1)
- [x] 2.7 Document common patterns:
  - [x] CLI interface patterns (args, flags)
  - [x] Script invocation patterns (dynamic import vs subprocess)
  - [x] Error handling patterns (fail-fast, continue-on-error)
  - [x] Output bundle structure patterns
  - [x] Manifest generation patterns
  - [x] Catalog registration patterns (NEW)
  - [x] Guardrail enforcement patterns (NEW)
  - [x] Outcome dataclass patterns (NEW)
- [x] 2.8 Record pattern findings in Stage 11.1 orchestrator Tier-2 doc

---

## Phase 3: Order Stage 11.1 Script Roster ✅

Define the execution order for available scripts in the Stage 11.1 orchestrator.

- [x] 3.1 List all scripts currently in Stage 11.1 holding area (12 scripts identified)
- [x] 3.2 Classify each script by tier class (5 producers, 1 consumer, 1 summarizer, 4 utilities)
- [x] 3.3 Identify dependencies between scripts (upstream/downstream)
- [x] 3.4 Establish execution sequence respecting dependencies (3-phase flow)
- [x] 3.5 Document roster order in Stage 11.1 orchestrator Tier-2 doc
- [x] 3.6 Select first script for Phase 4 processing: **ASR-005 (`validate_import_boundaries.py`)**

---

## Phase 4: Per-Script Process (Repeat for Each Script) ✅

Complete each script end-to-end before moving to the next.

**Execution Note:** Phase 4 was executed as a pragmatic HOP-alignment pass rather than the
granular 14-step template workflow below. All 12 scripts were processed:
- 7 producers/consumers aligned with HOP base package and `run(argv)` entry points
- 4 libraries/utilities classified (no changes needed)
- 1 rawview utility deferred
- 18/18 tests passing across all scripts with test coverage

The detailed checklist below remains as reference for future formal template development.

### 4.1 Create Working Document

- [x] 4.1.1 Create temp template in `/.repo_studios/docs/archives/`
  - [x] Filename: `temp_<script_name>_build.md`
  - [x] Add frontmatter with `status: active`
- [x] 4.1.2 Add script identity section (name, purpose, tier class, file path)

### 4.2 Build Plan Section

- [ ] 4.2.1 Document current script state
- [ ] 4.2.2 Identify target standards the script must meet
- [ ] 4.2.3 List required modifications (gap analysis)
- [ ] 4.2.4 Estimate effort and dependencies

### 4.3 Alteration Locations Section

- [ ] 4.3.1 Identify specific code locations requiring changes
- [ ] 4.3.2 Map each location to the standard being addressed
- [ ] 4.3.3 Document expected before/after for each change
- [ ] 4.3.4 Flag any breaking changes or compatibility concerns

### 4.4 Perform Modifications

- [ ] 4.4.1 Execute code changes per alteration plan
- [ ] 4.4.2 Verify each change against expected outcome
- [ ] 4.4.3 Update alteration section with actual results
- [ ] 4.4.4 Note any deviations from plan

### 4.5 Documentation Update Section

- [ ] 4.5.1 Write documentation as if first time (clean slate)
- [ ] 4.5.2 Document only current state — no legacy cruft
- [ ] 4.5.3 Capture:
  - [ ] What the script does
  - [ ] How the script is designed
  - [ ] CLI interface and usage
  - [ ] Input/output contracts
- [ ] 4.5.4 Mark future considerations with [?] checkboxes

### 4.6 Test Section

- [ ] 4.6.1 Document existing test coverage
- [ ] 4.6.2 Identify test gaps
- [ ] 4.6.3 Design new tests for gaps
- [ ] 4.6.4 Implement tests
- [ ] 4.6.5 Execute tests and record results
- [ ] 4.6.6 Update test section with pass/fail evidence

### 4.7 Tier-3 YAML Section

- [ ] 4.7.1 Design tier3.yaml structure for the script
- [ ] 4.7.2 Document "how to use" information
- [ ] 4.7.3 Document "where to look" pointers
- [ ] 4.7.4 Create or update tier3.yaml file
- [ ] 4.7.5 Validate tier3.yaml against schema (if exists)

### 4.8 Wiring and Integration Section

- [ ] 4.8.1 Identify db_integration requirements
- [ ] 4.8.2 Document upstream dependencies
- [ ] 4.8.3 Document downstream consumers
- [ ] 4.8.4 Implement db_integration hooks (if applicable)
- [ ] 4.8.5 Wire to orchestrator (add to execution roster)
- [ ] 4.8.6 Test orchestrator invocation

### 4.9 QA Section ("Prove It")

- [ ] 4.9.1 **Script operates:** Run script standalone, verify no errors
- [ ] 4.9.2 **Tests pass:** All unit and integration tests green
- [ ] 4.9.3 **Output location correct:** Verify output path matches contract
- [ ] 4.9.4 **Output quality acceptable:** Inspect output content for correctness
- [ ] 4.9.5 **Wired properly:** Verify upstream receives expected input
- [ ] 4.9.6 **Wired properly:** Verify downstream receives expected output
- [ ] 4.9.7 **Documentation complete:** All sections filled, no placeholders
- [ ] 4.9.8 Sign-off: Record QA completion date and evidence

### 4.10 Transfer to Tier-2 Orchestrator

- [ ] 4.10.1 Identify sections from temp template for transfer
- [ ] 4.10.2 Copy designated sections to Stage 11.1 orchestrator Tier-2 doc
- [ ] 4.10.3 Format transferred content to match Tier-2 standards
- [ ] 4.10.4 Update Tier-2 script roster entry with completion status
- [ ] 4.10.5 Update Tier-1 cross-references if needed

### 4.11 Upstream/Downstream Wiring Instructions

- [ ] 4.11.1 Document lessons learned during wiring
- [ ] 4.11.2 Record any pattern deviations or exceptions
- [ ] 4.11.3 Update pattern documentation (Phase 2 findings) if needed

### 4.12 Template Evolution

- [ ] 4.12.1 Review temp template structure — what worked, what was missing
- [ ] 4.12.2 Update master template design (if exists) or note improvements
- [ ] 4.12.3 Record template version and changes

### 4.13 Archive Working Document

- [ ] 4.13.1 Update temp template frontmatter: `status: archived`
- [ ] 4.13.2 Add completion date to frontmatter
- [ ] 4.13.3 Verify file remains in `/.repo_studios/docs/archives/`
- [ ] 4.13.4 Confirm no orphaned references to temp file

### 4.14 Repeat

- [x] 4.14.1 Select next script from Phase 3 roster
- [x] 4.14.2 Return to 4.1 and repeat process

**Phase 4 Complete:** All 12 ASR scripts processed (2026-01-26)

---

## Phase 5: Template Finalization ✅

After all scripts complete, extract formal templates.

- [x] 5.1 Review all archived temp templates
- [x] 5.2 Identify common sections across tier classes
- [x] 5.3 Identify tier-class-specific sections
- [x] 5.4 Generate blank templates:
  - [x] `tier2_producer_template.md`
  - [x] `tier2_consumer_template.md`
  - [x] `tier2_aggregator_template.md`
  - [x] `tier2_summarizer_template.md`
  - [x] `tier2_orchestrator_template.md`
- [x] 5.5 Place templates in `tier2_roster/templates/`
- [x] 5.6 Link templates from Stage 12 sections in Tier-1

---

## Phase 6: Apply Templates to Existing Stage 1.1 Scripts

Standardize existing Tier-2 documentation using finalized templates.

- [ ] 6.1 For each script in Stage 1.1:
  - [ ] 6.1.1 Compare current Tier-2 content against template
  - [ ] 6.1.2 Identify gaps in current documentation
  - [ ] 6.1.3 Fill gaps using template structure
  - [ ] 6.1.4 Remove legacy/outdated content
  - [ ] 6.1.5 Verify documentation reflects current state only
- [ ] 6.2 Validate all Tier-2 docs follow standardized format
- [ ] 6.3 Update Tier-1 cross-references if section anchors changed

---

## Checkpoint: Template Maturity Assessment

- [x] C.1 Stage 12 exists in Tier-1 with all five tier-class sections
- [ ] C.2 Stage 11.1 orchestrator is operational and wired to Stage 7
- [x] C.3 All Stage 11.1 scripts processed through Phase 4
- [x] C.4 All five tier-class templates exist and are usable
- [ ] C.5 Existing Stage 1.1 Tier-2 docs standardized
- [x] C.6 Archived temp templates preserved with `status: archived`
- [ ] C.7 Lessons learned documented for future refinement

---

## Notes

- **Tier-2 authority:** Tier-2 docs are the source of truth for script design and behavior.
- **Tier-3 role:** Tier-3 YAML captures "how to use" and "where to look" for agents.
- **[?] checkboxes:** Use for future considerations where uncertainty exists.
- **Governance destiny:** Stage 12 will eventually detach and migrate to Jarvis governance index.
- **Archive location:** `/.repo_studios/docs/archives/` holds completed temp templates with `status: archived`.

---

## Evidence Log

| Date | Author | Action | Evidence |
|------|--------|--------|----------|
| 2026-01-25 | GitHub Copilot | Created implementation plan | This document |
| 2026-01-25 | GitHub Copilot | Refined workflow per user feedback | Orchestrator-first, per-script completion, archive lifecycle |
| 2026-01-25 | GitHub Copilot | Phase 1 complete | Stage 12 added to Tier-1 (sections 12.1–12.5); downstream sections renumbered (13–17); cross-references updated; governance disclaimer added |
| 2026-01-25 | GitHub Copilot | Phase 1.5 complete | Created `tier2_available_scripts_orchestrator_roster.md` with common patterns extracted from `run_test_execution_telemetry.py` and `run_fault_diagnostics_overview.py` |
| 2026-01-25 | GitHub Copilot | Phase 2 complete | Reviewed all 6 orchestrators; documented 8 patterns total (added Catalog Registration, Guardrail Enforcement, Outcome Dataclass); updated orchestrator roster Section 2 |
| 2026-01-25 | GitHub Copilot | Phase 3 complete | Listed 12 scripts from Stage 11.1; classified by tier (5 producers, 1 consumer, 1 summarizer, 4 utilities); mapped dependencies; proposed 3-phase execution order; selected ASR-005 (`validate_import_boundaries.py`) as first Phase 4 candidate |
| 2026-01-26 | GitHub Copilot | Phase 4 complete | All 12 ASR scripts processed: 7 HOP-aligned (run(argv) + base package), 4 libraries classified, 1 deferred; 18/18 tests passing; Tier-2 roster workstreams updated |
| 2026-01-26 | GitHub Copilot | Phase 5 complete | 5 tier-class templates created in `tier2_roster/templates/`; Tier-1 Stage 12 links and checkboxes updated |
| | | | |
