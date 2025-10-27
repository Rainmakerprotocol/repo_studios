# Library README Adjustments (Pre-Extraction)

Reference doc: `que_for_integration/refactor_library/phase_1/library_README.md`

| Section | Reference Content | Required Adjustment Before First Extraction | Owner |
| --- | --- | --- | --- |
| Purpose & Philosophy | Matches current direction (AI-first, single responsibility). | Add pointer to `.repo_studios/command_center/docs/naming_conventions.md` so humans and agents land on the hardened guide. | Agent draft, Developer approve |
| Directory Structure | Shows full scaffold produced by `setup_library_structure.py`. | Update language to clarify that modules are created **on demand** during manual extraction—omit placeholder references and note blank slate status. | Agent draft |
| Usage Guidelines – Manual Process | Refers to Phase 3 flow. | Ensure checklist points to run workspace reports/checklists for traceability (link to `.repo_studios/command_center/reports/`). | Agent draft |
| Usage Guidelines – Automated Process | Mentions Phase 4 automation commands (`make studio-detect-duplicates`). | Flag as "future automation" with note that automation is pending guardrails; remove command snippets until greenlit. | Agent draft |
| Testing | Mirrors blueprint layout. | Add guidance for creating tests alongside new modules only when they land (no placeholder tests). | Agent draft |
| TODO Snippets | Encourages temporary functions with TODO for extraction. | Link TODO language to `duplicate_target_mappings.md` so developers know expected destinations. | Agent draft |

## Implementation Notes

- Defer publishing the README until the first module is actually extracted to avoid empty directories lingering on main.
- Store the adjusted README draft under `.repo_studios/command_center/docs/` and copy it into `.repo_studios/library/README.md` as part of the first migration PR.
