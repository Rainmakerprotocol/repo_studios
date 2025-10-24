# Library Integration Alignment Template

**Status:** Draft alignment template (YYYY-MM-DD)

**Purpose:** Provide a repeatable scaffold for planning shared code library integrations. Customize per project before implementation work begins.

**Duplicate Snapshot:** _Summarize latest duplicate metrics (counts, files, date)._

---

## Phase Overview

| Phase | Focus | Status | Notes |
|-------|-------|--------|-------|
| Phase 1 | Foundation Setup | _Status_ | _Key blockers or references_ |
| Phase 2 | Duplicate Detection Tool | _Status_ | _Key blockers or references_ |
| Phase 3 | Manual Extraction Validation | _Status_ | _Key blockers or references_ |
| Phase 4 | Automated Extraction | _Status_ | _Key blockers or references_ |
| Phase 5 | Integration with Repo Operations | _Status_ | _Key blockers or references_ |
| Phase 6 | AI Prompt Engineering | _Status_ | _Key blockers or references_ |
| Phase 7 | Validation & Hardening | _Status_ | _Key blockers or references_ |
| Phase 8 | Scale to New Projects | _Status_ | _Key blockers or references_ |

Legend: _Define status labels (e.g., In discovery, Not started, In progress, Deferred)._ 

---

## Phase 1 – Foundation Setup

* [ ] **Inventory library structure** vs. current repository tree *(Owner → deliverable).*  
* [ ] **Confirm naming convention adoption** with examples from top duplicate targets *(Owner → deliverable).*  
* [ ] **Decide on generator usage** (run, adapt, or replace) after comparison *(Owner → recommendation).*  
* [ ] **Document onboarding README adjustments** required for the project *(Owner → deliverable).*  

_Notes:_ _Capture project-specific considerations (e.g., existing utilities to preserve)._ 

## Phase 2 – Duplicate Detection Tool

* [ ] **Compare new detection outputs** to current duplicate metrics *(Owner → deliverable).*  
* [ ] **Validate schema alignment** between reference reports and project expectations *(Owner → deliverable).*  
* [ ] **Assess testing harness compatibility** across target environments *(Owner → deliverable).*  
* [ ] **Decide integration strategy** (adopt, adapt, or reuse existing tooling) *(Owner → recommendation).*  

_Notes:_ _Add context or constraints affecting detection choices._ 

## Phase 3 – Manual Extraction Validation

* [ ] **Confirm live duplicates** for prioritized functions using latest analysis *(Owner(s) → deliverable).*  
* [ ] **Establish priority order** for extraction targets *(Owner(s) → decision).*  
* [ ] **Map each target** to library destination paths following conventions *(Owner → deliverable).*  
* [ ] **Define test coverage approach** (library tests plus producer regression) *(Owner → plan).*  
* [ ] **Capture manual checklist** tailored to project tooling *(Owner → deliverable).*  

_Notes:_ _Clarify acceptance criteria before automation._ 

## Phase 4 – Automated Extraction

* [ ] **Outline guardrails** (dry-run, backups, reviews) prior to automation *(Owner → plan).*  
* [ ] **Determine success criteria** based on manual pilot outcomes *(Owner → metrics).*  
* [ ] **Identify dependencies** (schema stability, detection accuracy, library readiness) *(Owner → checklist).*  

_Notes:_ _Indicate when this phase returns to backlog._ 

## Phase 5 – Integration with Repo Operations

* [ ] **Sketch Make/CI target design** for duplicate detection/refactoring flows *(Owner → design).*  
* [ ] **Review orchestrator impacts** if integrating with existing remediation suites *(Owner → analysis).*  
* [ ] **Plan documentation updates** contingent on adoption *(Owner → list).*  

_Notes:_ _Document approvals required before wiring into CI/automation._ 

## Phase 6 – AI Prompt Engineering

* [ ] **Audit existing AI prompts** to prevent conflicting guidance *(Owner → inventory).*  
* [ ] **Draft candidate instruction updates** aligned with library conventions *(Owner → proposal).*  

_Notes:_ _Delay until library structure stabilizes._ 

## Phase 7 – Validation & Hardening

* [ ] **Define metrics** (duplicates resolved, tests added, coverage) *(Owner → metrics).*  
* [ ] **Plan CI integration strategy** (warning-only vs. blocking) *(Owner → plan).*  
* [ ] **Collect false-positive feedback loop** if new detection tooling is adopted *(Owner → process).*  

_Notes:_ _Capture monitoring cadence and owners._ 

## Phase 8 – Scale to New Projects

* [ ] **Package templates or tooling** for reuse *(Owner → plan).*  
* [ ] **Test on new repositories** for day-one prevention *(Owner → pilot).*  
* [ ] **Document onboarding workflow** for contributors *(Owner → documentation).*  

_Notes:_ _Mark as deferred if out of scope._ 

---

## Decisions Captured

| Decision | Status | Notes |
|----------|--------|-------|
| _Example: Extraction remains manual until pilot success_ | _Pending/Confirmed_ | _Add supporting details._ |
| _Decision title_ | _Status_ | _Notes or references._ |

---

## Outstanding Considerations

1. _Context to resolve_ – _Notes or desired outcome._
2. _Context to resolve_ – _Notes or desired outcome._
3. _Context to resolve_ – _Notes or desired outcome._

---

## Design Decisions Required

| Decision | Current Direction | Next Step | Owner |
|----------|-------------------|-----------|-------|
| _Decision title_ | _Brief description or leaning._ | _Action needed before implementation._ | _Responsible party._ |
| _Decision title_ | _Brief description or leaning._ | _Action needed before implementation._ | _Responsible party._ |

---

*Next alignment touchpoint:* _Describe trigger for revisiting this template (e.g., after structure diff, after duplicate priority confirmation)._ 
