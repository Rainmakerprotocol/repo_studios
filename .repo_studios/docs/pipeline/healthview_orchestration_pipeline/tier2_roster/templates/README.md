---
title: "Tier-2 Build Templates — Instructions & Reference"
tier: reference-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - instruction-set
  - template-guide
  - phase-4-reference
status: active
version: 1.1.0
updated_at: 2026-01-27
tags:
  - stage-12
  - templates
  - phase-4
  - phase-4a
  - phase-4b
  - instructions
related_files:
  - tier2_producer_template.md
  - tier2_consumer_template.md
  - tier2_aggregator_template.md
  - tier2_summarizer_template.md
  - tier2_orchestrator_template.md
  - tier2_utility_template.md
  - tier2_promotion_template.md
  - ../tier2_available_scripts_roster.md
  - ../../implementation_plans/stage12_template_development_plan.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Build Templates — Instructions & Reference

> **Purpose:** This document explains how to use the Phase 4 script build templates, when to
> use each template, and serves as the authoritative reference for all template-related questions.
>
> **See:** `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules.

---

## 1. Overview

The **Tier-2 Build Templates** are working documents used during **Phase 4 per-script processing**.
Each template guides the systematic transformation of a pipeline script from its current state to
full compliance with the Universal Law:

> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.

### 1.1 Template Inventory

#### 1.1.1 Build Templates (Phase 4A — Make Compliant)

| Template | Script Category | Compliance Tier | HOP Bundles |
|----------|-----------------|-----------------|-------------|
| [tier2_producer_template.md](tier2_producer_template.md) | Producer | A (Report Generator) | ✅ Yes |
| [tier2_consumer_template.md](tier2_consumer_template.md) | Consumer | A (Report Generator) | ✅ Yes |
| [tier2_aggregator_template.md](tier2_aggregator_template.md) | Aggregator | A (Report Generator) | ✅ Yes |
| [tier2_summarizer_template.md](tier2_summarizer_template.md) | Summarizer | A (Report Generator) | ✅ Yes |
| [tier2_orchestrator_template.md](tier2_orchestrator_template.md) | Orchestrator | A (Report Generator) | ✅ Yes |
| [tier2_utility_template.md](tier2_utility_template.md) | Utility | B (Action Utility) | ❌ No |

#### 1.1.2 Promotion Template (Phase 4B — Wire to Orchestrator)

| Template | Purpose | Prerequisite |
|----------|---------|-------------|
| [tier2_promotion_template.md](tier2_promotion_template.md) | Wire compliant script into orchestrator | Build complete |

---

## 2. 5W1H — The Complete Picture

### 2.1 WHO — Who Uses These Templates?

| Actor | Role | Usage Pattern |
|-------|------|---------------|
| **Coding Agents** | Primary user | Follow template sections sequentially during automated script processing |
| **Human Developers** | Secondary user | Use as checklist during manual script upgrades or reviews |
| **CI Pipeline** | Validator | Reference template requirements for compliance checks |
| **Project Leads** | Oversight | Track Phase 4 progress via completed working documents |

### 2.2 WHAT — What Are These Templates?

**Templates are working documents** — not static references. Each template:

1. **Captures script identity** — Name, path, tier class, compliance tier
2. **Guides state analysis** — CLI interface, entry points, dependencies, current compliance
3. **Enforces quality gates** — Mandatory verification steps that MUST pass
4. **Documents changes** — What was modified and why
5. **Tracks completion** — Checklist-driven completion criteria

**Templates are NOT:**

- Code generators (they document, not create)
- Test harnesses (they reference tests, not run them)
- Deployment artifacts (they're archived after completion)

### 2.3 WHEN — When Do I Use a Template?

**Start a template when:**

- A script is selected for Phase 4 processing
- You need to upgrade a script to Universal Law compliance
- An existing script needs orchestrator integration
- A new script is being added to the pipeline

**Complete a template when:**

- All mandatory sections pass verification
- Tier-3 YAML is created/updated
- DB Integration markers are in place
- Tests pass (mypy, pytest, CLI execution)
- Orchestration readiness checklist is complete

**Archive a template when:**

- All completion criteria met
- Tier-2 roster record updated
- Frontmatter status changed to `archived`

### 2.4 WHERE — Where Do Templates Live?

```text
.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/templates/
├── README.md                        ← You are here
├── tier2_producer_template.md       ← Build: Tier A produces raw data
├── tier2_consumer_template.md       ← Build: Tier A single-hop analysis
├── tier2_aggregator_template.md     ← Build: Tier A multi-source blending
├── tier2_summarizer_template.md     ← Build: Tier A final digests
├── tier2_orchestrator_template.md   ← Build: Tier A suite coordination
├── tier2_utility_template.md        ← Build: Tier B actions without bundles
└── tier2_promotion_template.md      ← Promote: wire to orchestrator
```

**Working documents go to:**

```text
.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/
└── <RECORD_ID>_<SCRIPT_NAME>_build.md
```

### 2.5 WHY — Why Do These Templates Exist?

| Problem | Template Solution |
|---------|-------------------|
| Scripts have inconsistent interfaces | Universal Interface Contract enforced |
| No way for agents to discover scripts | Tier-3 YAML provides machine-readable metadata |
| Database integration is ad-hoc | DB Integration markers standardize future schema |
| Orchestrator integration is fragile | ScriptConfig and return payload contracts |
| Quality is inconsistent | Mandatory verification stop-gates |
| Progress tracking is unclear | Checklist-driven completion criteria |

**The templates implement the Universal Law** by ensuring every script:

1. Has `run(argv) -> dict` entry point
2. Returns standardized payload (status, exit_code, type-specific keys)
3. Has Tier-3 YAML for agent discoverability
4. Has DB Integration markers for future persistence
5. Can be invoked by orchestrators without modification

### 2.6 HOW — How Do I Use a Template?

**Phase 4 is a two-phase workflow:**

| Phase | Template Type | Purpose | Output |
|-------|---------------|---------|--------|
| **Phase 4A** | Build Template | Make script Universal Law compliant | Compliant script + Tier-3 YAML |
| **Phase 4B** | Promotion Template | Wire script into orchestrator | Orchestrator integration |

```text
                    ┌─────────────────────────────────────────────────────────┐
                    │                    PHASE 4 WORKFLOW                      │
                    └─────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │ PHASE 4A: BUILD (Make Compliant)                                        │
    │                                                                         │
    │  1. Select build template (producer/consumer/aggregator/summarizer/     │
    │     orchestrator/utility)                                               │
    │  2. Create working document: <RECORD_ID>_<script>_build.md              │
    │  3. Analyze current state                                               │
    │  4. Implement changes (run() entry point, Tier-3 YAML, DB markers)      │
    │  5. Verify (mypy, pytest, CLI)                                          │
    │  6. Complete checklist                                                  │
    │                                                                         │
    │  OUTPUT: Compliant script + Tier-3 YAML                                 │
    └─────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ PHASE 4B: PROMOTE (Wire to Orchestrator)                                │
    │                                                                         │
    │  1. Use tier2_promotion_template.md                                     │
    │  2. Create working document: <RECORD_ID>_<script>_promote.md            │
    │  3. Update Tier-2 roster record                                         │
    │  4. Add ScriptConfig to orchestrator                                    │
    │  5. Register in script registry                                         │
    │  6. Update orchestrator Tier-3 YAML                                     │
    │  7. Add/update orchestrator tests                                       │
    │  8. Update Makefile targets                                             │
    │  9. Verify end-to-end                                                   │
    │                                                                         │
    │  OUTPUT: Script integrated into orchestrator                            │
    └─────────────────────────────────────────────────────────────────────────┘
```

#### Step 1: Select the Right Template

**For Phase 4A (Build):**

```text
Is the script a meta-coordinator that invokes other scripts?
  └─ YES → tier2_orchestrator_template.md
  └─ NO  → Continue...

Does the script produce HOP bundles (manifest/summary/telemetry)?
  └─ NO  → tier2_utility_template.md (Tier B)
  └─ YES → Continue...

What is the script's data role?
  └─ Produces raw data from sources → tier2_producer_template.md
  └─ Analyzes single upstream source → tier2_consumer_template.md
  └─ Blends multiple sources        → tier2_aggregator_template.md
  └─ Creates final human digest     → tier2_summarizer_template.md
```

#### Step 2: Create Working Document

```bash
# Copy template to working_docs with script-specific name
cp templates/tier2_<category>_template.md \
   working_docs/<RECORD_ID>_<script_name>_build.md
```

#### Step 3: Replace Template Variables

| Variable | Example Value |
|----------|---------------|
| `<SCRIPT_NAME>` | `generate_commandview_inventory.py` |
| `<SCRIPT_PATH>` | `.repo_studios/scripts/producers/generate_commandview_inventory.py` |
| `<RECORD_ID>` | `ASR-001` |
| `<YYYY-MM-DD>` | `2026-01-26` |
| `<LINE_COUNT>` | `452` |
| `<TARGET_STAGE>` | `Stage 4.1` |

#### Step 4: Work Through Sections Sequentially

1. **Section 1** — Populate script identity
2. **Section 2** — Analyze current state, verify compliance
3. **Section 3** — Document gaps and required changes
4. **Section 4** — Record changes made
5. **Section 5** — Capture evidence (tests, references)
6. **Section 6** — Complete orchestrator integration
7. **Section 7** — Final completion checklist

#### Step 5: Respect Stop-Gates

> **⚠️ MANDATORY STOP-GATES appear throughout templates. DO NOT SKIP THEM.**

Templates contain critical verification points marked with:

```markdown
> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
```

These sections require **actual verification**, not assumptions. If a stop-gate fails,
you must fix the issue before proceeding.

#### Step 6: Archive Completed Document

1. Update frontmatter: `status: archived`
2. Update Tier-2 roster record
3. Move to archive location (if applicable)

---

## 3. Template Selection Decision Tree

### 3.1 Phase 4A — Build Template Selection

```text
                        ┌─────────────────────┐
                        │   New Script for    │
                        │  Phase 4A (BUILD)   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ Does script invoke/coordinate│
                    │     other pipeline scripts?  │
                    └──────────────┬──────────────┘
                          ┌────────┴────────┐
                         YES               NO
                          │                 │
                          ▼                 ▼
              ┌───────────────────┐  ┌──────────────────────┐
              │   ORCHESTRATOR    │  │ Does script produce  │
              │ tier2_orchestrator│  │ HOP bundles (manifest│
              │   _template.md    │  │ /summary/telemetry)? │
              └───────────────────┘  └──────────┬───────────┘
                                          ┌─────┴─────┐
                                         YES         NO
                                          │           │
                                          │           ▼
                                          │    ┌──────────────┐
                                          │    │   UTILITY    │
                                          │    │tier2_utility │
                                          │    │ _template.md │
                                          │    └──────────────┘
                                          ▼
                              ┌────────────────────────┐
                              │ What is data flow role?│
                              └────────────┬───────────┘
                    ┌──────────┬───────────┼───────────┬──────────┐
                    ▼          ▼           ▼           ▼          ▼
              ┌─────────┐┌─────────┐┌───────────┐┌───────────┐
              │PRODUCER ││CONSUMER ││AGGREGATOR ││SUMMARIZER │
              │ Generates││ Analyzes││  Blends   ││  Creates  │
              │ raw data ││ single  ││ multiple  ││  final    │
              │ from     ││ upstream││ sources   ││  digest   │
              │ sources  ││ source  ││           ││           │
              └─────────┘└─────────┘└───────────┘└───────────┘
```

### 3.2 Phase 4B — Promotion (Always Same Template)

```text
                        ┌─────────────────────┐
                        │  Phase 4A Complete? │
                        │  (run() + Tier-3)   │
                        └──────────┬──────────┘
                                   │
                          ┌────────┴────────┐
                         YES               NO
                          │                 │
                          ▼                 │
              ┌───────────────────┐         │
              │    PROMOTION      │         │
              │tier2_promotion_   │◄────────┘
              │  template.md      │   Go back to 4A
              └───────────────────┘
```

> **Note:** The promotion template is the same for ALL script categories. The only
> prerequisite is that Phase 4A build processing is complete.

---

## 4. Compliance Tiers Explained

### 4.1 Tier A — Report Generators

**Characteristics:**

- Produce HOP bundles (manifest.json, summary.md, telemetry.json)
- Output to timestamped directories (`YYYYMMDD-HHMM/`)
- Support `--output-dir` and `--artifacts-to-keep` flags
- Write to `hop_manifests`, `hop_summaries`, `hop_telemetry` DB tables

**Return Payload (Required Keys):**

```python
{
    "status": "ok",
    "exit_code": 0,
    "run_dir": Path("..."),      # Bundle directory
    "manifest": {...},           # Manifest data
    "telemetry": {...},          # Telemetry data
    "summary": "...",            # Summary path or content
    # Type-specific keys (upstream_refs, sources, aggregator_refs, etc.)
}
```

**Templates:** Producer, Consumer, Aggregator, Summarizer, Orchestrator

### 4.2 Tier B — Action Utilities

**Characteristics:**

- NO HOP bundles (`artifacts: None`)
- Perform actions (cleanup, configure, validate, diagnose)
- Support `--dry-run` and `--force` flags
- Write to `utility_actions` DB table

**Return Payload (Required Keys):**

```python
{
    "status": "ok",           # or: error, skipped, dry_run
    "exit_code": 0,
    "action_taken": "...",    # Human-readable action description
    "artifacts": None,        # Explicit None
    "details": {...}          # Optional action-specific data
}
```

**Templates:** Utility

---

## 5. Universal Interface Contract

**ALL scripts (Tier A and Tier B) MUST implement:**

| Requirement | Description |
|-------------|-------------|
| `run(argv)` entry point | Function that accepts `list[str] | None` |
| Returns `dict[str, Any]` | NOT an integer exit code |
| `status` key in return | "ok", "error", or type-specific values |
| `exit_code` key in return | 0=success, 1=warning/skipped, 2=error |
| `--repo-root` flag | Repository root override |
| `--log-level` flag | Logging verbosity control |
| Google-style docstring | Args/Returns documented |
| No `sys.exit()` in `run()` | Return error payload instead |
| No interactive prompts | Or `--force` bypass flag |

---

## 6. Tier-3 YAML Quick Reference

Every script needs a Tier-3 YAML for agent discoverability:

```yaml
# Tier-3 Metadata for <script_name>
name: <script_name>
path: <script_path>
category: producer | consumer | aggregator | summarizer | orchestrator | utility
compliance_tier: A | B
entry_point: run
description: "<one-line description>"
version: "1.0.0"

inputs:
  - name: <param>
    type: <type>
    required: true | false
    description: "<description>"

outputs:
  status: "<possible values>"
  exit_code: "<meaning>"
  # Type-specific output descriptions...

orchestrator_ready: true | false
db_integration_ready: true | false

tags:
  - <tag1>
  - <tag2>
```

---

## 7. Common Questions & Answers

### Q: Which template do I use for a script that does both analysis AND cleanup?

**A:** If it produces HOP bundles, use the appropriate Tier A template (likely Consumer or
Aggregator). Add the cleanup as a secondary action documented in the Details section. If it
ONLY does cleanup with no bundles, use Utility.

### Q: Can a Utility script be called by an orchestrator?

**A:** Yes! All scripts are orchestration-ready per the Universal Law. Utilities just don't
contribute HOP bundles to the orchestrator's output — they log actions instead.

### Q: What if my script doesn't fit any category?

**A:** Ask: Does it produce HOP bundles? If yes, pick the closest Tier A category. If no, use
Utility. Document any unique characteristics in Section 1.

### Q: Do I need to complete every section?

**A:** Yes for mandatory sections (marked with ⚠️). Optional sections can be marked N/A with
rationale. Stop-gates CANNOT be skipped.

### Q: What's the difference between `run()` returning error payload vs raising exception?

**A:** `run()` should catch exceptions and return an error payload with `status: "error"` and
`exit_code: 2`. This allows orchestrators to handle failures gracefully. Only raise for truly
unrecoverable situations (which should be rare).

### Q: How do I handle scripts that are already compliant?

**A:** Still create a working document. Use it to verify compliance, document the verification,
and ensure Tier-3 YAML exists. Mark sections as "Already Compliant" with evidence.

### Q: Where do I put the Tier-3 YAML file?

**A:** Either:

1. `<script_dir>/<script_name>.tier3.yaml` (co-located with script)
2. Embedded in a central inventory file

The template documents which approach the script uses.

---

## 8. Template Version History

| Template | Version | Last Updated | Major Changes |
|----------|---------|--------------|---------------|
| Producer | 2.0.0 | 2026-01-26 | Universal Law, Tier-3 YAML, DB Integration |
| Consumer | 2.0.0 | 2026-01-26 | Universal Law, Tier-3 YAML, DB Integration |
| Aggregator | 2.0.0 | 2026-01-26 | Universal Law, Tier-3 YAML, DB Integration |
| Summarizer | 2.0.0 | 2026-01-26 | Universal Law, Tier-3 YAML, DB Integration |
| Orchestrator | 2.0.0 | 2026-01-26 | Universal Law, Child Script Management, DB Integration |
| Utility | 2.0.0 | 2026-01-26 | Initial version with Tier B compliance |

---

## 9. Related Resources

| Resource | Path | Purpose |
|----------|------|---------|
| Tier-2 Roster | `../tier2_available_scripts_roster.md` | Master list of all scripts and their status |
| Stage 12 Plan | `../../implementation_plans/stage12_template_development_plan.md` | Template development roadmap |
| Python Standards | `.repo_studios/docs/standards/global/std-global-python-engineering.md` | Python coding standards |
| Markdown Standards | `.github/instructions/markdown.instructions.md` | Markdown authoring rules |
| Docstring Instructions | `.github/instructions/docstring.instructions.md` | Google-style docstring format |
| Database Integration | `.repo_studios/command_center/scripts/libraries/database_integration.py` | DB integration library |

---

## 10. Quick Start Checklist

- [ ] Identify script to process
- [ ] Determine script category (Producer/Consumer/Aggregator/Summarizer/Orchestrator/Utility)
- [ ] Copy appropriate template to `working_docs/`
- [ ] Replace all `<PLACEHOLDER>` variables
- [ ] Work through sections 1-7 sequentially
- [ ] Respect all stop-gates — verify, don't assume
- [ ] Create/update Tier-3 YAML
- [ ] Add DB Integration markers
- [ ] Run verification tests (mypy, pytest, CLI)
- [ ] Complete orchestration readiness checklist
- [ ] Update frontmatter to `status: archived`
- [ ] Update Tier-2 roster record

---

## Appendix: Template Section Map

| Section | Producer | Consumer | Aggregator | Summarizer | Orchestrator | Utility |
|---------|----------|----------|------------|------------|--------------|---------|
| 1. Script Identity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 1.3 Action Classification | — | — | — | — | — | ✅ |
| 2.2.1 Universal Interface | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2.2.2 Return Payload | Type-specific | Type-specific | Type-specific | Type-specific | Type-specific | Type-specific |
| 2.4.1 Universal Compliance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2.4.2 HOP Bundle Compliance | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| 2.4.2 Utility Compliance | — | — | — | — | — | ✅ |
| 2.5 Report/Action Quality | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2.6 Tier-3 YAML | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2.7 DB Integration | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2.7 Child Script Mgmt | — | — | — | — | ✅ | — |
| 6. Orchestrator Integration | ✅ | ✅ | ✅ | ✅ | Validation | ✅ |
| Appendix: Patterns | — | — | — | — | — | ✅ |

---

*For questions about templates, consult this README first. For unresolved questions, reference
the standards in Section 9 or raise an issue in the repository.*
