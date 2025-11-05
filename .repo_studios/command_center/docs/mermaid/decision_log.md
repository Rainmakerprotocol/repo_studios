# Mermaid Decision Log

## 2025-11-05

- **Decision:** Standardize inventory dependency categories as `internal`, `standard_library`, and `third_party`, keeping `unknown` as a fallback.
- **Context:** Required for the commandview viewer packs (Dependency Pack, Coupling Insight Pack) to differentiate internal modules from external sources.
- **Owner:** GitHub Copilot implementation assistant.
- **Evidence:** Updated `.repo_studios/command_center/scripts/producers/generate_function_inventory.py` and checklist entry in `.repo_studios/command_center/docs/mermaid/mermaid_integration_checklist.md`.
- **Decision:** Emit per-module call graph data with resolution metadata for local, imported, and builtin targets.
- **Context:** Unlocks the Code Flow and Coupling Insight packs plus cross-module duplicate analysis by providing structured call edges directly in the inventory payload.
- **Owner:** GitHub Copilot implementation assistant.
- **Evidence:** Added `_build_call_graph()` in `.repo_studios/command_center/scripts/producers/generate_function_inventory.py`, updated checklist status, and new regression coverage in `.repo_studios/tests/tests_producers/test_generate_function_inventory.py::test_call_graph_resolves_local_and_imported_calls`.
