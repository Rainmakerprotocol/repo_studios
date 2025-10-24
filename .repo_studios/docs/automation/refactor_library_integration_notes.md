# Refactor Library Integration Notes

**Status:** Draft (2025-10-24)

**Purpose:** Capture our current understanding of the refactor_library drop-in bundle while we decide which portions, if any, align with Repo Studios priorities.

**Disclaimer:** The source package describes an aspirational end state. Everything below records intent, open questions, and preliminary assessments—it is **not** a commitment to implement.

---

## Phase Snapshot

| Phase | Intent Described in Package | Repo Studios Reality Check | Follow-up Actions |
|-------|-----------------------------|----------------------------|-------------------|
| Phase 1 – Foundation Setup | Scaffold `.repo_studios/library/` domains via `setup_library_structure.py`; enforce naming conventions and library README. | Structure already exists in Repo Studios, but we must confirm parity with package conventions. | ✓ Inventory existing library tree vs. proposed; 🔄 decide whether to adopt naming rule deltas; ❓ evaluate need for generator script. |
| Phase 2 – Duplicate Detection Tool | `scan_code_duplicates.py` + tests to surface exact/near duplicates with recommended library destinations. | Repo Studios has duplicate awareness via other health reports; this tool could complement but overlaps with existing plans. | 🔄 Compare detection schema to current health-suite outputs; 🚧 evaluate test harness portability; ❓ confirm dependency footprint. |
| Phase 3 – Manual Extraction Validation | Prove workflow by extracting `_copy_latest` → `create_latest_link`, adding tests, swapping imports manually. | Docs outline process; actual library module/tests are included, but we have not verified they match Repo Studios APIs. | ✅ Captured step-by-step guide; 🔄 confirm targeted scripts still contain duplicates; ⚠️ ensure test fixtures fit Repo Studios layout. |
| Phase 4 – Automated Extraction | Orchestrator `refactor_from_report.py` automates extraction, test generation, replacements. | No assets provided; intent requires significant integration effort. | 📌 Determine automation appetite; ❓ design safeguards before adoption. |
| Phase 5 – Repo Wiring | Make targets (`studio-detect-duplicates`, `studio-refactor-duplicates`), health-suite linkage, documentation updates. | Repo processes already dense; introducing new targets demands governance review. | 📌 Map overlap with existing Make/CI flows; ❓ assess maintenance ownership. |
| Phase 6 – AI Prompt Engineering | Copilot instructions, prompt templates guiding library-first mindset. | Repo Studios prompt surfacing handled via `repo_prompts.md`; this work would need harmonization. | 📌 Evaluate duplication vs. existing instructions; ❓ capture required deltas. |
| Phase 7 – Validation & Hardening | Run on full codebase, refactor remaining duplicates, wire into CI (warning mode). | Requires production readiness, time-intensive. | 🚧 Estimate runtime/impact; ❓ define success criteria; 📊 identify monitoring hooks. |
| Phase 8 – Scale | Package as template, onboarding collateral, day-one prevention story. | Out-of-scope until earlier phases validated. | 💤 Park for later; document assumptions for future revisit. |

Legend: ✓ complete, 🔄 in-progress research, 🚧 blocked by dependencies, ⚠️ risk, 📌 planned decision, ❓ unanswered question, 💤 deferred.

---

## Key Assets Provided (Phases 1–3)

- `phase_1/`
  - `setup_library_structure.py`: Idempotent generator for the recommended library hierarchy.
  - `naming_conventions.md`: Detailed path/filename taxonomy; deviates slightly from current Repo Studios layout (needs diff review).
  - `library_README.md` and `library__init__.py`: Orientation material and import surface scaffolding.
- `phase_2/`
  - `scan_code_duplicates.py`: AST walker comparing function bodies by hash + similarity; outputs AI-oriented JSON, expects local report staging.
  - `scan_code_duplicates_USAGE.md` & `PHASE_2_QUICKSTART.md`: CLI, configuration flags, performance tips, path exclusions.
  - `test_scan_code_duplicates.py`: Unit coverage for baseline scenarios; imports assume placement under `.repo_studios/tests/tests_producers/`.
- `phase_3/`
  - `PHASE_3_MANUAL_EXTRACTION_GUIDE.md`: 10-step validation checklist, test expectations, rollback plan.
  - `create_latest_link.py` + `test_create_latest_link.py`: Example extraction target and 11-test suite verifying hardlink vs. copy fallbacks.
  - `replace_duplicate.py`: Helper applying imports/replacements based on detection reports.
  - `phase3_lessons_learned_template.md`: Post-mortem template to capture outcomes.

---

## Alignment Considerations

1. **Naming & Structure Drift** – Repo Studios already curates `.repo_studios/library/`. Adopting the supplied hierarchy may require renaming existing modules or reconciling overlaps (e.g., artifact lifecycle vs. current taxonomy).
2. **Duplicate Detection Overlap** – Health suite artifacts (lizard, churn complexity, etc.) partially cover duplication risk. Adding another AST scanner increases maintenance burden unless we consolidate reporting.
3. **Tooling Hygiene** – Scripts assume UNIX-like paths and may need adjustments for Windows CI agents. Also rely on `jq` for report inspection; we should note PowerShell equivalents.
4. **Testing Footprint** – Provided tests create new directories under `.repo_studios/tests/tests_library/`; we must ensure they do not collide with current fixtures.
5. **Automation Appetite** – Phase 4 automation introduces mutation of production code. We need guardrails (dry-run, code review checkpoints, backup strategy) beyond what manual guide documents.
6. **Prompt Integration** – Copilot instruction changes must coordinate with `repo_prompts.md` governance to avoid conflicting guidance.
7. **Maintenance Ownership** – Determine which team owns the resulting library and duplicate tooling; plan for schema versioning, dependency updates, and CI monitoring.

---

## Research Actions (Open)

1. **Library Diff Audit**
   - Compare existing `.repo_studios/library/` tree to `setup_library_structure.py` output.
   - Flag rename/addition conflicts; decide whether to partially adopt.
2. **Detection Report Fit**
   - Review sample `example.json` duplicate report; map fields to Repo Studios reporting needs.
   - Assess whether we can ingest into existing analytics (e.g., health suite dashboards).
3. **Manual Extraction Viability**
   - Verify `_copy_latest` duplicates still exist in `generate_standards_index.py`, `generate_dependency_hygiene_report.py`, and `generate_anchor_inventory.py`.
   - Determine if `create_latest_link.py` matches current call semantics.
4. **Testing Strategy**
   - Evaluate bringing `test_create_latest_link.py` into Repo Studios test suite (fixture requirements, runtime impact).
   - Decide whether to port `test_scan_code_duplicates.py` or build new targeted coverage.
5. **Automation Guardrails**
   - Identify rollback expectations if automated extraction (Phase 4) fails mid-run.
   - Document code review checkpoints before auto-applied replacements land in main.
6. **Governance Touchpoints**
   - Loop in maintainers for `.repo_studios/scripts/producers/` and library components to validate appetite for new automation.
   - Engage documentation owners regarding additional guides or modifications to `script_inventory_architecture.md`.

---

## Decision Log (Pending)

| Decision Topic | Current Thinking | Owner | Due |
|----------------|------------------|-------|-----|
| Adopt full library structure? | Lean toward selective adoption; need diff analysis. | Repo Studios Library Maintainers | TBD |
| Introduce duplicate scanner? | Requires redundancy review with health suite outputs. | Automation Team | TBD |
| Manual extraction pilot? | Candidate for limited trial on `_copy_latest` if duplicates confirmed. | Refactor Pod | TBD |
| Proceed to automation (Phase 4)? | Blocked until manual validation outcome documented. | Leadership | TBD |

---

## References

- `que_for_integration/refactor_library/README_ALL_PHASES.md`
- `que_for_integration/refactor_library/refactor_library_phase_plan.md`
- `que_for_integration/refactor_library/example.json`
- `que_for_integration/refactor_library/phase_3/PHASE_3_MANUAL_EXTRACTION_GUIDE.md`
- `.repo_studios/docs/script_inventory_architecture.md` (needs update per Phase H if we proceed)

---

*Next update:* After library diff audit and duplicate report evaluation are completed, refresh statuses and convert open questions into concrete tasks or decision memos.
