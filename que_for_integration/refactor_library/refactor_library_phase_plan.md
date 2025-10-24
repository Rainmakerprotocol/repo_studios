AI-Guided Refactoring Pipeline - Implementation Plan
Phase 1: Foundation Setup

Create library folder structure at .repo_studios/library/ with all parent/child folders from hybrid design
Create naming_conventions.md documenting folder/file naming rules
Add __init__.py files to make library importable
Create .repo_studios/library/README.md explaining library purpose and navigation

Phase 2: Build Detection Tool

Create scan_code_duplicates.py in .repo_studios/scripts/producers/
Implement AST parser to extract function signatures and bodies
Build hash-based comparison for exact duplicates
Build AST-similarity scoring for near-duplicates (>85% similar)
Generate JSON report following the AI-first schema structure
Include library path recommendations using naming convention rules
Include refactoring action steps with line numbers and import statements
Add targeted test file recommendations

Phase 3: First Extraction (Manual Validation)

Run detection tool on your 3 sample files
Review generated JSON report
Manually extract _copy_latest to artifact_lifecycle/versioning/create_latest_link.py
Write pytest for the extracted function
Replace all 3 occurrences with imports
Run targeted tests - confirm green
Run full suite - confirm no regressions
Document lessons learned

Phase 4: Automate Extraction

Create refactor_from_report.py orchestrator
Implement: read duplicate detection JSON
Implement: check if library target already exists
Implement: extract code to library location
Implement: generate pytest template
Implement: replace duplicates with imports
Implement: run targeted tests
Add rollback on test failure

Phase 5: Integration with Repo Studios

Add Make target: studio-detect-duplicates
Add Make target: studio-refactor-duplicates
Wire into health suite orchestrator
Add duplicate detection to remediation tracker
Update script_inventory_architecture.md with library section

Phase 6: AI Prompt Engineering

Create .github/copilot-instructions.md teaching Copilot about library structure
Add instruction: "Check .repo_studios/library/ before writing utility functions"
Add instruction: "Follow naming conventions in naming_conventions.md"
Create prompt template for "extract this duplicate to library"

Phase 7: Validation & Hardening

Run detection on full Jarvis codebase
Review library recommendations for accuracy
Refactor all 9 duplicate categories in your sample files
Measure: lines saved, files cleaned, test coverage
Document edge cases and false positives
Add detection tool to CI pipeline (warning-only mode)

Phase 8: Scale to New Projects

Package as repo_studios template
Test on new blank repo
Verify day-one prevention: Copilot checks library first
Document workflow for future contributors
Create video/guide showing AI-assisted refactoring