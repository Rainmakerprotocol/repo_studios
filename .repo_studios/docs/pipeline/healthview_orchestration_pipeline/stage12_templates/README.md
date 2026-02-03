# Stage 12 Templates — Agent Entry Point

> **Purpose:** Templates and metaprompts for Phase 4 script compliance.
> This directory contains everything needed to process scripts to Universal Law compliance
> and wire them into HealthView orchestrators.

---

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Quick-verify a mostly-compliant producer | [producer/QUICK_START.md](producer/QUICK_START.md) |
| Process an existing producer | [producer/review_metaprompts.md](producer/review_metaprompts.md) |
| Process an existing consumer | [consumer/review_metaprompts.md](consumer/review_metaprompts.md) |
| Process an existing aggregator | [aggregator/review_metaprompts.md](aggregator/review_metaprompts.md) |
| Process an existing summarizer | [summarizer/review_metaprompts.md](summarizer/review_metaprompts.md) |
| Process an existing utility | [utility/review_metaprompts.md](utility/review_metaprompts.md) |
| Design an orchestrator | [orchestrator/design_metaprompts.md](orchestrator/design_metaprompts.md) |
| Create a new script from scratch | [producer/create_metaprompts.md](producer/create_metaprompts.md) |
| Wire a compliant script to orchestrator (Phase 4B) | [promotion/wire_metaprompts.md](promotion/wire_metaprompts.md) |

---

## Machine-Readable Index

For programmatic discovery, see [manifest.yaml](manifest.yaml).

---

## Template Inventory

| Category | Template | Compliance Tier | Phase |
|----------|----------|-----------------|-------|
| Producer | [build_template.md](producer/build_template.md) | A (Report Generator) | 4A |
| Consumer | [build_template.md](consumer/build_template.md) | A (Report Generator) | 4A |
| Aggregator | [build_template.md](aggregator/build_template.md) | A (Report Generator) | 4A |
| Summarizer | [build_template.md](summarizer/build_template.md) | A (Report Generator) | 4A |
| Orchestrator | [build_template.md](orchestrator/build_template.md) | A (Report Generator) | 4A |
| Utility | [build_template.md](utility/build_template.md) | B (Action Utility) | 4A |
| Promotion | [build_template.md](promotion/build_template.md) | — | 4B |

---

## Workflow Overview

**Phase 4A — Build:**
1. Select category template based on script type
2. Follow review_metaprompts.md (existing script) or create_metaprompts.md (new script)
3. Produce `{RECORD_ID}_{script_stem}_build.md` working document
4. Script achieves Universal Law compliance

**Phase 4B — Promote:**
1. Script must be Phase 4A complete
2. Follow promotion/wire_metaprompts.md
3. Wire script into target orchestrator
4. Update Tier-2 roster with integration evidence

---

## Related Documents

- [Tier-1 HealthView Pipeline](../tier1_healthview_orchestration_pipeline.md)
- [Stage 12 Implementation Plan](../implementation_plans/stage12_template_development_plan.md)
- [REPORT_NAMING_STANDARDS.md](../../../../../REPORT_NAMING_STANDARDS.md)

---

## Update Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-30 | Created stage12_templates structure with manifest and README | Repo Studios |
