---
title: repo Standards — Project-Level Instructions & Environment Overview
audience: [repo, Jarvis2, Developer]
role: [Standards, Project-Config]
owners: ["@docs-owners"]
status: approved
version: 1.0.0
updated_at: 2025-08-22
tags: [project, standards, ai-ingestion, ci]
related_files:
  - ./repo_standards_markdown.md
  - ./repo_standards_python.md
  - ./repo_standards_html.md
  - ./repo_standards_chainlit.md
---

## 🧭 repo Standards — Project-Level Instructions & Environment Overview

This file defines the global standards, dependencies, formats, and role-based
behavioral expectations for GitHub repo when contributing to this project.
It is also used by AI agents like Jarvis2 to understand project-wide
assumptions and environmental constants.

repo must treat this document as the **master configuration of
expectations** when navigating, generating, or modifying any file across the
codebase.

---

## 🎯 Primary Instructional Role

**You are an autonomous AI code assistant embedded in a modular, AI-augmented codebase.**
**You are to generate, refactor, document, and clean Python code, HTML
layouts, markdown standards, and Chainlit-based UIs in accordance with this
project's architecture and evolution protocols.**

---

## 🧱 Formats Used Across the Project

| Type          | Format / Standard                                  |
| ------------- | -------------------------------------------------- |
| Language      | Python 3.11+                                       |
| Frontend      | HTML5 with Tailwind CSS (utility-first)            |
| UI Engine     | Chainlit (LLM interface and chat UI)               |
| Documentation | Markdown (`.md`) for AI+human instruction          |
| Tests         | Pytest, structured by module                       |
| Logging       | `logging` module (Python), `cl.error()` (Chainlit) |
| Style         | PEP8 via Black + Ruff enforcement                  |

---

## 📦 Core Dependencies

* `python-dotenv`
* `pydantic`
* `fastapi`
* `chainlit`
* `ruff`
* `black`
* `mypy`
* `pytest`
* `httpx`
* `jinja2`
* `uvicorn`

> Additional packages should only be added if:
>
> 1. They are necessary,
> 2. They support modularity or AI integration,
> 3. They do not compromise deterministic output or agent compatibility.

---

## 🧪 Testing Standards

* All public methods and functions must be tested
* Use `test_*.py` structure grouped by domain or module
* Validate not only success paths but edge cases and failures
* Use mocks for external calls, file systems, or DB I/O
* All new code must pass: `pytest`, `ruff check`, `black --check`, and `mypy`
* Documentation changes introducing new metrics or env flags MUST update:
  1. `docs/agents/config_quickstart.md` (flags + metrics tables)
  2. Root `README.md` Agent Config subsection tables
  3. Any phased plan checklist referencing those metrics (e.g., `step5_agent_config_system.md`)
  in the same commit (atomic consistency)
* After such changes, run `python scripts/check_markdown_anchors.py` and ensure zero issues
* CI Anchor Gate: `make docs-anchors` runs the same anchor/link checker and is included in `make qa`.
* Recommended local safety: install git hooks (`make install-hooks`) to enable pre-commit
  anchor + duplicate slug + metrics/flags sync heuristic.
* Anchor Health Automation: Run `make anchor-health` to generate timestamped duplicate
  heading (H1/H2) reports under `.repo_studios/anchor_health/` (JSON/MD/TSV +
  runs.log). Use it before and after large doc refactors or multi-file plan updates to
  avoid reintroducing duplicate slug clusters. Do not increase the baseline in
  `tests/docs/anchor_slug_baseline.json`; only ratchet downward after sustained reduction
  and removal of non-allowed duplicates.

---

## 🧠 Behavioral Standards for repo

### General Role

**You are to act as a proactive contributor that writes modular,
well-documented, testable code while following architectural intent.**

### You are to

* Automatically recognize file roles based on folder and filename patterns
* Generate `.md` documentation alongside all new files
* Refactor functions that exceed 50+ lines or 3+ nesting levels
* Maintain separation of business logic, API logic, and UI logic
* Annotate major changes in `.txt` logs stored in `/repo_clean_log/`
* Reference `/repo_standards_python.md` before writing any Python
* Reference `/repo_standards_html.md` before generating any layout
* Reference `/repo_standards_chainlit.md` before generating any
  LLM-integrated UI
* Reference `/repo_standards_markdown.md` before generating any `.md` file
* When adding or renaming multiple headings across docs, run `make anchor-health` and inspect
  `anchor_report_latest.json` to confirm no regression before committing.

---

## 📁 Project Folder Structure (Partial Example)

<!-- tree:begin -->
Updated: 10/17/2025_07:14:03
```text
jarvis2/
├── README.md
├── pyproject.toml
├── pytest.ini
├── requirements-dev.txt
├── ruff.toml
├── agents/
│   ├── benchmark/
│   ├── cache_inspector/
│   ├── cognitive/
│   ├── companion/
│   │   ├── voice/
│   │   │   ├── actions/
│   │   │   ├── orchestration/
│   │   │   ├── services/
│   │   │   └── tests/
│   │   ├── voice_engine/
│   │   └── whisper_listener/
│   ├── core/
│   │   ├── agent_instances/
│   │   ├── autonomy/
│   │   │   └── tests/
│   │   ├── config/
│   │   ├── messaging/
│   │   │   ├── adapters/
│   │   │   └── tests/
│   │   ├── metrics_storage/
│   │   ├── monitoring/
│   │   │   ├── alerts/
│   │   │   ├── collector/
│   │   │   ├── collectors/
│   │   │   ├── events/
│   │   │   ├── ingest/
│   │   │   ├── instrumentation/
│   │   │   ├── metrics_storage/
│   │   │   ├── recovery_logs/
│   │   │   ├── resource_monitor/
│   │   │   ├── resource_monitoring/
│   │   │   ├── tests/
│   │   │   ├── validators/
│   │   │   └── visualization/
│   │   ├── rag/
│   │   ├── service_management/
│   │   ├── tests/
│   │   ├── time_series/
│   │   ├── utils/
│   │   └── ws_backends/
│   ├── diagnostics/
│   │   ├── diagnostic_agent/
│   │   └── tests/
│   ├── event_diagnostics/
│   ├── interface/
│   │   ├── chainlit/
│   │   │   ├── components/
│   │   │   ├── tests/
│   │   │   └── widgets/
│   │   ├── export_toolkit/
│   │   └── model_comparison/
│   ├── memory_refresh/
│   ├── optimization/
│   │   └── tests/
│   ├── optimization_agent/
│   ├── orchestrator/
│   │   ├── config/
│   │   └── tests/
│   ├── repair/
│   ├── storage_retention/
│   ├── system/
│   │   ├── config/
│   │   │   └── health_reports/
│   │   ├── diagnostic_agent/
│   │   ├── recovery/
│   │   ├── test_cases/
│   │   └── tests/
│   ├── template/
│   ├── templates/
│   └── ui_contracts/
├── api/
│   ├── cache/
│   │   └── backends/
│   ├── metrics/
│   │   └── exposition/
│   ├── models/
│   ├── routers/
│   │   └── ui/
│   │       └── builders/
│   ├── server_components/
│   ├── tests/
│   └── utils/
├── artifacts/
│   ├── cache/
│   ├── fault/
│   ├── models_smoke/
│   │   └── 20250925_225505/
│   └── perf_startup/
├── backups/
│   ├── _cache/
│   ├── _verification_logs/
│   ├── critical/
│   ├── critical_copy_1/
│   ├── critical_copy_2/
│   ├── lightweight/
│   │   └── _dedup_blocks/
│   ├── metadata_only/
│   └── standard/
│       ├── cat/
│       ├── model_metrics/
│       ├── new_1755882204/
│       ├── new_1756044246/
│       ├── new_1756046143/
│       ├── new_1756047324/
│       ├── new_1756054197/
│       ├── old_1755882204/
│       ├── old_1756044246/
│       ├── old_1756046143/
│       ├── old_1756047324/
│       ├── old_1756054197/
│       ├── pagetest_0_1755882204/
│       ├── pagetest_0_1756044243/
│       ├── pagetest_0_1756046140/
│       ├── pagetest_0_1756047320/
│       ├── pagetest_0_1756054193/
│       ├── pagetest_1_1755882204/
│       ├── pagetest_1_1756044243/
│       ├── pagetest_1_1756046140/
│       ├── pagetest_1_1756047321/
│       ├── pagetest_1_1756054194/
│       ├── pagetest_2_1755882204/
│       ├── pagetest_2_1756044244/
│       ├── pagetest_2_1756046141/
│       ├── pagetest_2_1756047321/
│       ├── pagetest_2_1756054195/
│       ├── progress_item_1755882203/
│       ├── progress_item_1756044242/
│       ├── progress_item_1756046139/
│       ├── progress_item_1756047320/
│       ├── progress_item_1756054193/
│       ├── restore_item_1755882205/
│       ├── restore_item_1756044252/
│       ├── restore_item_1756046148/
│       ├── restore_item_1756047329/
│       ├── restore_item_1756054202/
│       ├── searchtok_1755882204/
│       ├── searchtok_1756044245/
│       ├── searchtok_1756046142/
│       ├── searchtok_1756047323/
│       ├── searchtok_1756054196/
│       ├── smoke_item_1755882203/
│       ├── smoke_item_1756044241/
│       ├── smoke_item_1756046138/
│       ├── smoke_item_1756047319/
│       ├── smoke_item_1756054192/
│       ├── sorttest_1755882204_a/
│       ├── sorttest_1755882204_b/
│       ├── sorttest_1755882204_c/
│       ├── sorttest_1756044249_a/
│       ├── sorttest_1756044249_b/
│       ├── sorttest_1756044249_c/
│       ├── sorttest_1756046146_a/
│       ├── sorttest_1756046146_b/
│       ├── sorttest_1756046146_c/
│       ├── sorttest_1756047326_a/
│       ├── sorttest_1756047326_b/
│       ├── sorttest_1756047326_c/
│       ├── sorttest_1756054200_a/
│       ├── sorttest_1756054200_b/
│       ├── sorttest_1756054200_c/
│       ├── stdin_item_1755882203/
│       ├── stdin_item_1756044241/
│       ├── stdin_item_1756046137/
│       ├── stdin_item_1756047318/
│       └── stdin_item_1756054191/
├── client_helpers/
├── repo_clean_log/
├── repo_session_alignment/
├── data/
│   ├── alerts/
│   ├── benchmarks/
│   ├── diagnostics/
│   ├── metrics/
│   │   ├── _archives/
│   │   ├── _backups/
│   │   ├── _cleanup_logs/
│   │   ├── errors/
│   │   ├── model_performance/
│   │   │   └── system_metrics/
│   │   ├── system_metrics/
│   │   ├── time_series/
│   │   └── user_feedback/
│   └── metrics_backup/
├── docs/
│   ├── adr/
│   ├── agents/
│   │   └── governance/
│   ├── api/
│   │   └── cache/
│   ├── architecture/
│   ├── artifacts/
│   ├── coverage_history/
│   ├── deep_dives/
│   ├── events/
│   ├── examples/
│   ├── extending/
│   ├── health/
│   ├── memory/
│   ├── metrics/
│   ├── mrp/
│   ├── observability/
│   ├── operations/
│   ├── ops/
│   ├── orchestrator/
│   ├── ownership/
│   ├── perf/
│   ├── repo/
│   ├── roadmaps/
│   ├── runbooks/
│   ├── security/
│   ├── specs/
│   ├── standards/
│   │   └── archive/
│   ├── startup/
│   ├── systemd/
│   ├── testing/
│   ├── ui/
│   └── voice/
├── external/
│   ├── agixt/
│   │   ├── agixt/
│   │   │   ├── WORKSPACE/
│   │   │   ├── agents/
│   │   │   ├── chains/
│   │   │   ├── conversations/
│   │   │   ├── endpoints/
│   │   │   ├── extensions/
│   │   │   ├── memories/
│   │   │   ├── onnx/
│   │   │   ├── prompts/
│   │   │   ├── providers/
│   │   │   └── sso/
│   │   ├── docs/
│   │   │   ├── 1-Getting started/
│   │   │   ├── 2-Concepts/
│   │   │   ├── 3-Providers/
│   │   │   ├── 4-Authentication/
│   │   │   └── images/
│   │   ├── examples/
│   │   ├── models/
│   │   └── tests/
│   ├── aider-main/
│   │   ├── aider/
│   │   │   ├── coders/
│   │   │   ├── queries/
│   │   │   ├── resources/
│   │   │   └── website/
│   │   ├── benchmark/
│   │   ├── docker/
│   │   ├── requirements/
│   │   ├── scripts/
│   │   └── tests/
│   │       ├── basic/
│   │       ├── browser/
│   │       ├── fixtures/
│   │       ├── help/
│   │       └── scrape/
│   ├── autogpt/
│   │   ├── assets/
│   │   ├── autogpt_platform/
│   │   │   ├── autogpt_libs/
│   │   │   ├── backend/
│   │   │   ├── db/
│   │   │   ├── frontend/
│   │   │   ├── graph_templates/
│   │   │   └── installer/
│   │   ├── classic/
│   │   │   ├── benchmark/
│   │   │   ├── forge/
│   │   │   ├── frontend/
│   │   │   └── original_autogpt/
│   │   └── docs/
│   │       ├── _javascript/
│   │       ├── content/
│   │       └── overrides/
│   ├── babyagi/
│   │   ├── babyagi/
│   │   │   ├── api/
│   │   │   ├── dashboard/
│   │   │   └── functionz/
│   │   └── examples/
│   ├── camel/
│   │   ├── apps/
│   │   │   ├── agents/
│   │   │   ├── common/
│   │   │   ├── data_explorer/
│   │   │   └── dilemma/
│   │   ├── camel/
│   │   │   ├── agents/
│   │   │   ├── benchmarks/
│   │   │   ├── bots/
│   │   │   ├── configs/
│   │   │   ├── data_collectors/
│   │   │   ├── datagen/
│   │   │   ├── datahubs/
│   │   │   ├── datasets/
│   │   │   ├── embeddings/
│   │   │   ├── environments/
│   │   │   ├── extractors/
│   │   │   ├── interpreters/
│   │   │   ├── loaders/
│   │   │   ├── memories/
│   │   │   ├── messages/
│   │   │   ├── models/
│   │   │   ├── personas/
│   │   │   ├── prompts/
│   │   │   ├── responses/
│   │   │   ├── retrievers/
│   │   │   ├── runtimes/
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   ├── societies/
│   │   │   ├── storages/
│   │   │   ├── tasks/
│   │   │   ├── terminators/
│   │   │   ├── toolkits/
│   │   │   ├── types/
│   │   │   ├── utils/
│   │   │   └── verifiers/
│   │   ├── data/
│   │   │   ├── ai_society/
│   │   │   └── code/
│   │   ├── docs/
│   │   │   ├── _static/
│   │   │   ├── cookbooks/
│   │   │   ├── get_started/
│   │   │   ├── images/
│   │   │   ├── key_modules/
│   │   │   ├── mcp/
│   │   │   ├── mintlify/
│   │   │   └── reference/
│   │   ├── examples/
│   │   │   ├── agents/
│   │   │   ├── ai_society/
│   │   │   ├── benchmarks/
│   │   │   ├── bots/
│   │   │   ├── code/
│   │   │   ├── data_collectors/
│   │   │   ├── datagen/
│   │   │   ├── datahubs/
│   │   │   ├── dataset/
│   │   │   ├── debug/
│   │   │   ├── deductive_reasoner_agent/
│   │   │   ├── embeddings/
│   │   │   ├── embodiment/
│   │   │   ├── environments/
│   │   │   ├── evaluation/
│   │   │   ├── external_tools/
│   │   │   ├── extractors/
│   │   │   ├── generate_text_embedding_data/
│   │   │   ├── interpreters/
│   │   │   ├── knowledge_graph/
│   │   │   ├── loaders/
│   │   │   ├── memories/
│   │   │   ├── misalignment/
│   │   │   ├── models/
│   │   │   ├── observability/
│   │   │   ├── personas/
│   │   │   ├── rag/
│   │   │   ├── role_description/
│   │   │   ├── runtimes/
│   │   │   ├── schema_outputs/
│   │   │   ├── services/
│   │   │   ├── storages/
│   │   │   ├── structured_response/
│   │   │   ├── summarization/
│   │   │   ├── tasks/
│   │   │   ├── test/
│   │   │   ├── toolkits/
│   │   │   ├── translation/
│   │   │   ├── usecases/
│   │   │   ├── verifiers/
│   │   │   ├── vision/
│   │   │   └── workforce/
│   │   ├── licenses/
│   │   ├── misc/
│   │   ├── services/
│   │   │   └── agent_mcp/
│   │   └── test/
│   │       ├── agents/
│   │       ├── benchmarks/
│   │       ├── bots/
│   │       ├── data_collectors/
│   │       ├── data_samples/
│   │       ├── datagen/
│   │       ├── datahubs/
│   │       ├── datasets/
│   │       ├── embeddings/
│   │       ├── environments/
│   │       ├── extractors/
│   │       ├── integration_test/
│   │       ├── interpreters/
│   │       ├── loaders/
│   │       ├── memories/
│   │       ├── messages/
│   │       ├── models/
│   │       ├── personas/
│   │       ├── prompts/
│   │       ├── retrievers/
│   │       ├── runtimes/
│   │       ├── schema_outputs/
│   │       ├── services/
│   │       ├── storages/
│   │       ├── tasks/
│   │       ├── terminators/
│   │       ├── toolkits/
│   │       ├── utils/
│   │       ├── verifiers/
│   │       └── workforce/
│   ├── nodered/
│   ├── superagi/
│   │   ├── gui/
│   │   │   ├── app/
│   │   │   ├── pages/
│   │   │   ├── public/
│   │   │   └── utils/
│   │   ├── migrations/
│   │   │   └── versions/
│   │   ├── nginx/
│   │   ├── static/
│   │   ├── superagi/
│   │   │   ├── agent/
│   │   │   ├── apm/
│   │   │   ├── config/
│   │   │   ├── controllers/
│   │   │   ├── helper/
│   │   │   ├── image_llms/
│   │   │   ├── jobs/
│   │   │   ├── lib/
│   │   │   ├── llms/
│   │   │   ├── models/
│   │   │   ├── resource_manager/
│   │   │   ├── tools/
│   │   │   ├── types/
│   │   │   ├── vector_embeddings/
│   │   │   └── vector_store/
│   │   ├── tests/
│   │   │   ├── integration_tests/
│   │   │   ├── tools/
│   │   │   └── unit_tests/
│   │   ├── tgwui/
│   │   │   ├── config/
│   │   │   └── scripts/
│   │   └── workspace/
│   │       ├── input/
│   │       └── output/
│   └── wheels/
├── githooks/
├── htmlcov-repo/
├── jarvis2/
├── ledger/
├── ledger_tmp/
├── libraries/
│   ├── llama.cpp/
│   │   ├── build/
│   │   │   ├── CMakeFiles/
│   │   │   ├── Testing/
│   │   │   ├── bin/
│   │   │   ├── common/
│   │   │   ├── examples/
│   │   │   ├── ggml/
│   │   │   ├── pocs/
│   │   │   ├── src/
│   │   │   ├── tests/
│   │   │   └── tools/
│   │   ├── ci/
│   │   ├── cmake/
│   │   ├── common/
│   │   ├── docs/
│   │   │   ├── backend/
│   │   │   ├── development/
│   │   │   ├── multimodal/
│   │   │   └── ops/
│   │   ├── examples/
│   │   │   ├── batched/
│   │   │   ├── batched.swift/
│   │   │   ├── convert-llama2c-to-ggml/
│   │   │   ├── deprecation-warning/
│   │   │   ├── diffusion/
│   │   │   ├── embedding/
│   │   │   ├── eval-callback/
│   │   │   ├── gen-docs/
│   │   │   ├── gguf/
│   │   │   ├── gguf-hash/
│   │   │   ├── gritlm/
│   │   │   ├── jeopardy/
│   │   │   ├── llama.android/
│   │   │   ├── llama.swiftui/
│   │   │   ├── lookahead/
│   │   │   ├── lookup/
│   │   │   ├── parallel/
│   │   │   ├── passkey/
│   │   │   ├── retrieval/
│   │   │   ├── save-load-state/
│   │   │   ├── simple/
│   │   │   ├── simple-chat/
│   │   │   ├── simple-cmake-pkg/
│   │   │   ├── speculative/
│   │   │   ├── speculative-simple/
│   │   │   ├── sycl/
│   │   │   └── training/
│   │   ├── ggml/
│   │   │   ├── cmake/
│   │   │   ├── include/
│   │   │   └── src/
│   │   ├── gguf-py/
│   │   │   ├── examples/
│   │   │   ├── gguf/
│   │   │   └── tests/
│   │   ├── grammars/
│   │   ├── include/
│   │   ├── licenses/
│   │   ├── media/
│   │   ├── models/
│   │   │   └── templates/
│   │   ├── pocs/
│   │   │   └── vdot/
│   │   ├── prompts/
│   │   ├── requirements/
│   │   ├── scripts/
│   │   │   └── apple/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── tools/
│   │   │   ├── batched-bench/
│   │   │   ├── cvector-generator/
│   │   │   ├── export-lora/
│   │   │   ├── gguf-split/
│   │   │   ├── imatrix/
│   │   │   ├── llama-bench/
│   │   │   ├── main/
│   │   │   ├── mtmd/
│   │   │   ├── perplexity/
│   │   │   ├── quantize/
│   │   │   ├── rpc/
│   │   │   ├── run/
│   │   │   ├── server/
│   │   │   ├── tokenize/
│   │   │   └── tts/
│   │   └── vendor/
│   │       ├── cpp-httplib/
│   │       ├── miniaudio/
│   │       ├── minja/
│   │       ├── nlohmann/
│   │       └── stb/
│   └── whisper.cpp/
│       ├── bindings/
│       │   ├── go/
│       │   ├── java/
│       │   ├── javascript/
│       │   └── ruby/
│       ├── build/
│       │   ├── CMakeFiles/
│       │   ├── Testing/
│       │   ├── bin/
│       │   ├── examples/
│       │   ├── ggml/
│       │   ├── src/
│       │   └── tests/
│       ├── ci/
│       ├── cmake/
│       ├── examples/
│       │   ├── addon.node/
│       │   ├── bench/
│       │   ├── bench.wasm/
│       │   ├── cli/
│       │   ├── command/
│       │   ├── command.wasm/
│       │   ├── deprecation-warning/
│       │   ├── lsp/
│       │   ├── python/
│       │   ├── quantize/
│       │   ├── server/
│       │   ├── stream/
│       │   ├── stream.wasm/
│       │   ├── sycl/
│       │   ├── talk-llama/
│       │   ├── vad-speech-segments/
│       │   ├── wchess/
│       │   ├── whisper.android/
│       │   ├── whisper.android.java/
│       │   ├── whisper.nvim/
│       │   ├── whisper.objc/
│       │   ├── whisper.swiftui/
│       │   └── whisper.wasm/
│       ├── ggml/
│       │   ├── cmake/
│       │   ├── include/
│       │   └── src/
│       ├── grammars/
│       ├── include/
│       ├── models/
│       ├── samples/
│       ├── scripts/
│       │   └── apple/
│       ├── src/
│       │   ├── coreml/
│       │   └── openvino/
│       └── tests/
│           ├── earnings21/
│           └── librispeech/
├── manifests/
├── memory-bank/
│   ├── approvals/
│   │   └── repair/
│   ├── archive/
│   │   ├── activeContext/
│   │   ├── decisions/
│   │   └── progress/
│   ├── backups/
│   │   ├── 20250830T131837Z/
│   │   ├── 20250830T133325Z/
│   │   ├── 20250830T143510Z/
│   │   ├── 20250830T144526Z/
│   │   └── patches/
│   └── notes/
│       └── alignment/
├── metrics_storage/
│   └── storage/
├── models/
│   └── whisper/
├── mrp/
│   ├── benchmark/
│   ├── offline_exports/
│   │   └── alpha/
│   ├── training_docs/
│   └── vector_db/
├── perf_history/
├── scripts/
│   ├── config/
│   ├── health/
│   ├── hooks/
│   ├── maintenance_jobs/
│   ├── memory_health/
│   ├── memory_logs/
│   ├── memory_update/
│   ├── memory_validate/
│   ├── models_cli/
│   ├── models_cli_pkg/
│   ├── phases/
│   └── service_start/
├── security/
│   ├── apparmor/
│   └── selinux/
├── src/
│   ├── audio/
│   │   ├── build/
│   │   │   ├── lib.linux-x86_64-cpython-311/
│   │   │   └── temp.linux-x86_64-cpython-311/
│   │   ├── cmake/
│   │   ├── docs/
│   │   │   └── source/
│   │   ├── examples/
│   │   │   ├── asr/
│   │   │   ├── avsr/
│   │   │   ├── dnn_beamformer/
│   │   │   ├── hubert/
│   │   │   ├── libtorchaudio/
│   │   │   ├── pipeline_tacotron2/
│   │   │   ├── pipeline_wav2letter/
│   │   │   ├── pipeline_wavernn/
│   │   │   ├── self_supervised_learning/
│   │   │   ├── source_separation/
│   │   │   └── tutorials/
│   │   ├── packaging/
│   │   │   └── torchaudio/
│   │   ├── release/
│   │   ├── src/
│   │   │   ├── libtorchaudio/
│   │   │   ├── libtorio/
│   │   │   ├── torchaudio/
│   │   │   ├── torchaudio.egg-info/
│   │   │   └── torio/
│   │   ├── test/
│   │   │   ├── cpp/
│   │   │   ├── integration_tests/
│   │   │   ├── smoke_test/
│   │   │   └── torchaudio_unittest/
│   │   ├── third_party/
│   │   │   ├── ffmpeg/
│   │   │   └── sox/
│   │   └── tools/
│   │       ├── release_notes/
│   │       ├── setup_helpers/
│   │       └── travis/
│   ├── jarvis2.egg-info/
│   └── vision/
│       ├── android/
│       │   ├── gradle/
│       │   ├── gradle_scripts/
│       │   ├── ops/
│       │   └── test_app/
│       ├── benchmarks/
│       ├── build/
│       │   ├── bdist.linux-x86_64/
│       │   ├── lib.linux-x86_64-cpython-311/
│       │   └── temp.linux-x86_64-cpython-311/
│       ├── cmake/
│       ├── dist/
│       ├── docs/
│       │   └── source/
│       ├── examples/
│       │   ├── cpp/
│       │   └── python/
│       ├── gallery/
│       │   ├── assets/
│       │   ├── others/
│       │   └── transforms/
│       ├── ios/
│       │   └── VisionTestApp/
│       ├── packaging/
│       │   ├── wheel/
│       │   └── windows/
│       ├── references/
│       │   ├── classification/
│       │   ├── depth/
│       │   ├── detection/
│       │   ├── optical_flow/
│       │   ├── segmentation/
│       │   ├── similarity/
│       │   └── video_classification/
│       ├── release/
│       ├── scripts/
│       │   └── release_notes/
│       ├── test/
│       │   ├── assets/
│       │   ├── cpp/
│       │   └── expect/
│       ├── torchvision/
│       │   ├── csrc/
│       │   ├── datasets/
│       │   ├── io/
│       │   ├── models/
│       │   ├── ops/
│       │   ├── prototype/
│       │   ├── transforms/
│       │   └── tv_tensors/
│       └── torchvision.egg-info/
├── systemd/
│   ├── jarvis-orchestrator.service.d/
│   └── legacy/
├── tests/
│   ├── _plugins/
│   ├── agents/
│   │   ├── agent_instances/
│   │   ├── benchmark/
│   │   ├── core/
│   │   │   ├── messaging/
│   │   │   └── monitoring/
│   │   ├── diagnostics/
│   │   ├── interface/
│   │   │   └── chainlit/
│   │   ├── optimization/
│   │   ├── orchestrator/
│   │   ├── repair/
│   │   ├── service_management/
│   │   ├── system/
│   │   └── template/
│   ├── api/
│   │   ├── metrics/
│   │   └── ui/
│   ├── cache_unit/
│   ├── docs/
│   ├── e2e/
│   ├── health/
│   ├── helpers/
│   ├── integration/
│   ├── interface/
│   ├── lint/
│   ├── maintenance/
│   ├── messaging/
│   ├── monitoring/
│   ├── perf/
│   ├── retention/
│   │   ├── backup/
│   │   └── scheduler/
│   ├── scripts/
│   ├── state/
│   ├── systemd/
│   ├── utils/
│   ├── visualization/
│   │   ├── dashboard/
│   │   ├── error_analytics/
│   │   └── model_performance/
│   └── voice/
├── tmp/
│   └── reltest/
│       └── a/
│           └── b/
├── tmp_bench_stub/
│   └── ui/
│       └── sidebar/
├── tmp_debug_paths/
│   ├── backups/
│   └── data/
│       └── metrics/
├── tmp_patches/
├── tmp_test_bs4/
├── tmp_test_file_store/
│   ├── alerts/
│   └── system_metrics/
├── voice_profile/
│   └── jarvis/
│       └── voices/
```
<!-- tree:end -->

Note: The tree above is curated for clarity (depth ≤ 3). Large or legacy areas
like `__pycache__/`, `perf_history/`, and `z_FUTURE_IMPIMENTATIONS/` are
omitted. An automated refresher may update this block between the markers.

---

## 🔐 Environment & Secrets

* Do not hardcode secrets, tokens, or file paths in code
* Load configuration via typed settings (see Python standards `BaseSettings`)
* Provide and maintain `.env.example` with documented keys
* Critical variables should be validated at startup with clear errors

Example keys (non-exhaustive):

```text
JARVIS_API_TOKEN=...
JARVIS_DB_PATH=/home/founder/jarvis2/data/metrics.db
LOG_LEVEL=INFO
```

---

## ✅ Local Quality Gates

Run these before submitting changes:

```bash
ruff check .
black --check .
mypy .
pytest -q
npx markdownlint-cli "**/*.md" -c .markdownlint.json
```

---

## 🧪 CI Workflows (recommended)

* Markdown lint: `.github/workflows/markdownlint.yml` (uses `npx markdownlint-cli`)
* Python CI (suggested): run `ruff`, `black --check`, `mypy`, and `pytest` on
  push/PR; prefer matrix across supported Python versions

---

## 🔁 AI Self-Improvement Loop

* If repo encounters a pattern not covered by existing standards, it must:

  1. Record the event in the next `.txt` log file
  2. Suggest or append a proposed pattern to the relevant
     `repo_standards_*.md` file
  3. Tag it with `## Learned Fix:` and format the solution accordingly

---

By treating this document as the primary context source, repo ensures its
behavior is aligned with both system-wide intelligence and human developer
intentions.

---

## 📚 Standards Index (Ratchet — 2025-09-03)

All diffs/PRs/docs/tests must conform to these enforced standards:

* Coding: `docs/standards/coding.md`
* Documentation: `docs/standards/documentation.md`
* Testing: `docs/standards/testing.md`
* Markdown: `docs/standards/markdown.md`
* File Tree Hygiene: `docs/standards/file_tree.md`

Enforcement:

* Keep edits minimal; prefer amending existing files over rewrites.
* Pin dependencies and use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
* Meet local gates (`ruff`, `black --check`, `mypy`, `pytest -q`) and target ≥80% coverage
  for lines touched.
* If a standards file is missing, create it under `docs/standards/` with a proper title block.

## 🤖 Agent Block (machine-readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: project-standards-validate
      title: Validate project-level standards and environment
      steps:
        - ensure-front-matter: true
        - ensure-markdownlint-config: .markdownlint.json
        - ensure-ci-workflows:
            - .github/workflows/markdownlint.yml
        - ensure-configs:
            - pyproject.toml
            - pytest.ini
            - ruff.toml
        - ensure-env-example: .env.example
        - ensure-cleanup-script: .repo_studios/batch_clean.py
        - verify-tools: [ruff, black, mypy, pytest, node_npx_markdownlint]
        - validate-structure:
            depth: 3
            exclude:
              - "__pycache__/**"
              - "z_FUTURE_IMPIMENTATIONS/**"
              - "logs/**"
      severity: warn
```
<!-- agents:end:agent_instructions -->

## 🔁 File Decomposition Policy

### 📏 File Complexity Thresholds

* Decompose any `.py` file if:
  * > 1000 lines of code
  * > 12 function/class definitions
  * Function complexity > 15 (cyclomatic)
  * More than 3 deep nesting levels

### 🪓 Decomposition Process

* Only decompose the part of the file currently being modified.
* Create a new module for that part (e.g., `cache/negative_cache.py`).
* Leave remaining parts of the original file intact until assigned.
* Each new module must include:
  * Unit tests (`tests/...`).
  * Inline docstrings.
  * Updates to related `.md` documentation files.
* Log decomposition steps to `repo_clean_log/clean_YYYY-MM-DD_HHMM.txt` including:
  * File/line split.
  * Destination path.
  * Test file created.
  * `.md` docs touched.
