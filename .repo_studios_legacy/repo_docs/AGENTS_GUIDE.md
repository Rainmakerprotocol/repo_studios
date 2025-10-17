# 🧠 Jarvis2 / Rainmaker Protocol — AI‑Augmented System

Welcome to the Rainmaker Protocol project — a modular, AI-integrated system designed for
intelligent automation, augmented decision-making, and human-aligned orchestration. This repo
includes Jarvis2, our multi-agent logic and reasoning core, along with the supporting frontend,
code standards, and instructional layers designed for both human developers and AI agents.

---

## 🚀 Project Overview

* **Backend:** Python 3.11+, FastAPI, modular business logic
* **Frontend:** HTML5 + Tailwind CSS, rendered via Jinja2 templates
* **LLM Interface:** Chainlit for reactive, contextual AI interaction
* **Documentation:** Markdown-driven, AI-ingestible `.md` standards
* **Agents:** GitHub repo + Jarvis2 multi-layered AI agent stack

---

## 📁 Folder snapshot (curated)

Top‑level (selected):

```text
jarvis2/
├── api/                         # FastAPI adapter (metrics, health, alerts)
├── agents/                      # Core logic (monitoring, collectors, interface)
│   ├── core/monitoring/         # Metrics store, alerts, collectors, tests
│   └── interface/chainlit/      # Chainlit UI assets and docs
├── docs/                        # Schema and operational docs
├── scripts/                     # CLIs (e.g., backfill, CI gates, benches)
├── tests/                       # Global tests (plus scoped tests in subpackages)
├── Makefile                     # Common lint/type/test/bench targets
├── pyproject.toml               # Tooling config (ruff, mypy) and metadata
├── ruff.toml                    # Ruff rules
├── pytest.ini                   # Pytest config
├── requirements-dev.txt         # Dev/test dependencies
└── .repo_studios/       # AI agent behavior and standards (this folder)

```

---

## 🧩 Key Components

| Layer     | Description                                                          |
| --------- | -------------------------------------------------------------------- |
| Jarvis2   | Multi-agent logic engine for decision routing and orchestration      |
| repo   | Code-writing assistant with self-improvement and standards adherence |
| Chainlit  | Frontend conversational layer for LLM interaction                    |
| Standards | Markdown-based rulesets for Python, HTML, Chainlit, and projects     |
| Logs      | Persistent `.txt` logs used for AI behavior tracking and improvement |

### 🤖 Agent Template (Subscription-driven)

Use the scaffold under `agents/template/` to create simple EventBus-driven agents.

Components:

* `AgentBase` — base class to manage subscription lifecycle and worker concurrency
* `ExampleAgent` — subscribes to `state.changed` under a namespace prefix; records events

Recommended patterns:

* Narrow filters (topics + namespace_prefix; add key_regex when possible)
* Keep handlers short/idempotent; offload heavy work to background tasks
* Start with concurrency=1–2; scale cautiously
* Use `async with` to ensure clean shutdown

Run the example test:

```bash
pytest -q tests/agents/template/test_example_agent.py
```


---

## 🧪 Lint, typecheck, tests

Use Make targets for repeatability:

```bash
make lint         # Ruff fix on key packages
make typecheck    # Mypy on core packages
make test         # Pytest (quiet)
make qa           # lint + typecheck + test
```

**Pre-submit mandate:** run `make lint` before every PR or automated commit. The
target now executes the lizard complexity check; ensure it passes without new
warnings. For continuous feedback, install a lightweight pre-commit hook:

```bash
cat <<'HOOK' > .git/hooks/pre-commit
#!/usr/bin/env bash
set -euo pipefail
lizard --CCN 15 --length 80 agents api scripts
HOOK
chmod +x .git/hooks/pre-commit
```

Adjust the directories as needed when working in other trees. Fail fast locally
so CI and Codacy remain noise-free.

Direct commands (optional):

```bash
ruff check .
mypy agents/core/monitoring agents/interface/chainlit
pytest -q
```

---

## 📘 Standards and Instructions

All AI, agent, and developer activity is governed by markdown files in
`repo_studios/`, including:

* `repo_standards_python.md`
* `repo_standards_chainlit.md`
* `repo_standards_html.md`
* `repo_standards_markdown.md`
* `repo_standards_project.md`
* `repo_standards_monkey_patch.md`
* `repo_studios_clean.md`
* `repo_studios_python.md`
* `repo_mission_parameters.md`

These files are machine-parseable, human-readable, and used to guide repo’s behavior and
Jarvis2’s learning.

## 🗂️ Standards Index & Governance Toolkit

Unified, machine‑parseable standards live in `repo_standards_index.yaml` (never hand-edit; always
rebuild). These tools enable deterministic generation, querying, diffing, gap analysis, enforcement
stubs, prompt seed extraction, and Prometheus metrics exposure.

### Core Artifacts

| Artifact | Purpose |
| -------- | ------- |
| `.repo_studios/build_standards_index.py` | Deterministic generator (hash + ordering) |
| `repo_standards_index.yaml` | Generated standards index (rules + integrity hash) |
| `scripts/standards_index_cli.py` | Query/list/show/grep rules |
| `scripts/standards_index_diff.py` | Compare two index versions (added/removed/severity shifts) |
| `scripts/standards_index_gap.py` | Heuristic gap detector (unindexed directives) |
| `scripts/standards_enforce_stub.py` | Lightweight regex enforcement proof‑of‑concept |
| `scripts/standards_prompt_seed.py` | Extract high‑severity (error/critical) prompt snippets |
| `tests/test_standards_index.py` | Schema + integrity invariants |
| `tests/api/test_standards_metrics_exposure.py` | Metrics exposure presence tests |
| `docs/agents/standards_index.md` | Full schema & governance lifecycle |

### Generation & Validation

```bash
make standards-index            # Rebuild + run structural tests
python ./.repo_studios/build_standards_index.py  # Direct invocation
```
Successful rebuild updates: `generated_at`, may update `integrity_hash` only if rule triplets change.

### CLI Usage

```bash
python scripts/standards_index_cli.py list --severity error
python scripts/standards_index_cli.py grep "logging" --category python_coding
python scripts/standards_index_cli.py show rule-id
```
Exit codes are 0 on success; non‑zero on invalid filters or missing ID.

### Diff & Gap Tools

```bash
python scripts/standards_index_diff.py old.yaml new.yaml --format table
python scripts/standards_index_gap.py > tmp_gap_report.jsonl
```
Diff output includes: added/removed rule IDs, severity changes, integrity hash delta.
Gap detector emits candidate rule JSON lines (future: confidence scoring field).

### Enforcement Stub

```bash
python scripts/standards_enforce_stub.py --format json > standards_enforcement_report.json
```
Outputs fields: `violations` (list of objects with rule_id, file, snippet), `summary`, and
pass/fail counts.
Current scope: regex heuristics for a subset of rules. Integrates with metrics when the JSON file exists.

### Prompt Seed Extraction

```bash
python scripts/standards_prompt_seed.py --min-severity error --format markdown > prompt_seeds.md
```
Formats: `markdown|json|plain`. Designed for fast injection into model contexts.

### Metrics Exposure
Standards metrics are appended to the main `/metrics` endpoint (plaintext Prometheus format):

* `standards_rules_total`
* `standards_rules_severity_count{severity="info|warn|error|critical"}`
* `standards_integrity_hash_changed` (0/1 drift against last scrape)
* `standards_enforcement_runs_total`
* `standards_enforcement_violations_total`
* `standards_enforcement_violations_total_per_rule{rule_id="..."}` (severity + cap gated)
* `standards_enforcement_rule_counter_overflow` (1 when per‑rule counters suppressed)

Test with:

```bash
pytest -q tests/api/test_standards_metrics_exposure.py
```
Ad‑hoc inspection:

```bash
curl -s localhost:8010/metrics | grep '^standards_'
```

### Environment Flags (Cardinality / Filtering)

| Variable | Default | Effect |
| -------- | ------- | ------ |
| `STANDARD_METRICS_RULE_DETAIL_MIN_SEVERITY` | error | Minimum severity for per‑rule counters |
| `STANDARD_METRICS_MAX_RULE_COUNTERS` | 100 | Max distinct `rule_id` counters before guard trigger |

Raise threshold or lower cap to control scrape payload size.

### Deprecation (Summary)
Full flow in `docs/agents/standards_index.md`. Key steps:

1. Mark candidate with future `status: deprecated` (schema v1.1) + optional `replaced_by`.
2. Retain for ≥2 quarterly cycles unless urgent.
3. Remove after checklist (references updated, metrics quiet, successor validated).
4. Record decision (ADR / decisions log) when impactful.

### Quarterly Review Checklist (Condensed)

1. `make standards-index`; snapshot hash + severity distribution.
2. Run gap + diff; classify high‑confidence additions.
3. Identify redundant / overlapping rules for merge or deprecation.
4. Revalidate top severity rules; demote if mitigated.
5. Inspect enforcement + per‑rule metrics for dead rules.
6. Batch PRs: additions, deprecations, removals (separate when possible).
7. Rebuild → verify expected hash change only.
8. Archive summary (future: `standards_reviews/YYYY-Qx.md`).

### Fast Start Cheat Sheet

```bash
make standards-index
python scripts/standards_index_cli.py list --severity warn
python scripts/standards_index_diff.py base.yaml repo_standards_index.yaml
python scripts/standards_enforce_stub.py --format json > standards_enforcement_report.json
curl -s localhost:8010/metrics | grep standards_rules_total
python scripts/standards_prompt_seed.py --min-severity error --format plain | head
```

### Agent Guidance

Agents should:

* Rebuild only when seed or categories changed.
* Cache index keyed by `integrity_hash` to avoid redundant IO.
* Avoid emitting per‑rule metrics beyond cap (handled automatically by builder).
* Defer deprecation changes unless human request present.
* Always reference rule IDs (immutable) not summaries in logs.

---

### 📚 Prompt Library usage

Use the prompt library at the repo root as the source of truth:

* Library file: `repo_prompts.md`
* Usage guide: `.repo_studios/PROMPT_LIBRARY_USAGE.md`
* Rules:
  * Map requests (status/update/review/design) to Atomic or Bundle prompts.
  * Paste the full text of the chosen prompt, unchanged.
  * If ambiguous, list 2–3 candidates with one‑liners from the Index and ask the user to choose.
  * Never invent new prompts.

## 🔒 Environment & setup

Copy and modify `.env.example` to configure local environment:

```bash
cp .env.example .env
```

Make sure to populate secure variables such as API keys or token secrets.

Install Python dependencies:

```bash
pip install -r requirements-dev.txt
```

Security/keys (common):

* METRICS_API_TOKEN — token for metrics endpoints (header X-Auth-Token or Bearer)
* INTERNAL_API_KEY / INTERNAL_API_KEYS — FastAPI adapter scoped keys (X-API-Key)
* METRICS_DB_PATH — path to SQLite metrics DB (defaults to /tmp/metrics.db)

---

## ▶️ How to run

* FastAPI adapter (dev):

```bash
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8010
```

* Chainlit UI: see `agents/interface/chainlit/chainlit.md` for entry points and theming.
* See `.chainlit/config.toml` for additional configuration and theming options.

CI/benches (optional highlights):

```bash
make perf-ci-report      # Generate perf_summary.md and perf_trend.md
make metrics-ui-ready    # Verify monitoring UI readiness checks
make ui                  # Lint + run Chainlit interface tests with coverage
```

---

## 🔍 Repo Insight & Trends

Run a compact repo health snapshot: cleanup → pytest logs → monkey‑patch scan with trends.

```bash
make repo-insight           # runs cleanup, pytest logs, strict scan + trends
make scan-monkey-patches    # strict-by-default scan + trend update
```

Artifacts:

* `.repo_studios/pytest_logs/` — timestamped pytest outputs
* `.repo_studios/monkey_patch/<ts>/` — report.json/csv, SUMMARY.md, trend.md
* `.repo_studios/monkey_patch/trend_latest.md` — overview with recent‑N table
* `.repo_studios/anchor_health/anchor_report_latest.json` — latest duplicate heading
  metrics (strict count, baseline delta, top clusters)

See also:

* Standards and reduction playbook: `repo_standards_monkey_patch.md`
* Protocol overview: “Monkey Patch Reduction Protocol” in `.github/repo-instructions.md`

## 🩺 Health Suite (one‑shot)

Run a consolidated repo health scan (typecheck, test health, import graph, dep hygiene,
monkey‑patch trends) and produce a human‑readable summary plus timestamped logs:

```bash
make health-suite
```

Outputs:

* Summary: `.repo_studios/health_suite/health_suite_<ts>.md`
* Logs: `.repo_studios/health_suite/logs/<ts>/` (per‑step `*.log` and `*.err.log`)
* Typecheck: `.repo_studios/typecheck/<ts>/report.md`
* Test health: `.repo_studios/test_health/<ts>/report.md`
* Import graph: `.repo_studios/import_graph/<ts>/report.md`
* Monkey‑patch trend: `.repo_studios/monkey_patch/trend_latest.md`
* Lizard complexity: `.repo_studios/lizard/<ts>/` — `report.md`, `report.json`, optional
  `raw.json` + `raw.txt`
* Anchor health: `.repo_studios/anchor_health/anchor_report_latest.json`

Triage quickstart:

1) Fix typecheck first — open the top issue in the typecheck report; prefer minimal, typed fixes.
2) Inspect the test health report — read the exact failing test and traceback; reproduce locally if needed.
3) If monkey‑patch counts increased, target the category deltas with the reduction playbook.

Rerun the suite after fixes to ensure the summary is green.

Security notes and parsers:

* Test log health parsing uses defusedxml.ElementTree to safely parse JUnit XML. Ensure
  `defusedxml` is installed (pinned in `requirements-dev.txt`).
* The JUnit selection heuristic skips incidental "internal-only" artifacts and prefers the
  artifact with the highest total test count, tie-breaking by mtime. This reduces false positives
  in error counts.

### 🛠️ repo scripts overview (this folder)

Core Python tools under `.repo_studios/` that support cleaning, health
snapshots, and trends. Prefer these over ad‑hoc commands; they write timestamped
artifacts and are safe to run locally.

* `batch_clean.py` — One‑shot cleanup. Runs Ruff format/fix on targets, optional
  markdownlint (via npx), mypy on gated packages, and pytest unless disabled.
  Logs to `.repo_studios/cleanup_logs/clean_<ts>.txt`.
  Env/CLI:
  * `BATCH_CLEAN_ONLY=markdown` or `--mode markdown` to lint markdown only.
  * `--no-pytest` or `BATCH_CLEAN_NO_PYTEST=1` to skip tests.
  * `-t <path>` to scope; default targets storage code.

* `pytest_log_runner.py` — Runs pytest with helpful plugins when available,
  captures full output and JUnit XML, and writes grouped failed/skip summaries
  under `.repo_studios/pytest_logs/`.
  Flags (env):
  * `PYTEST_RUNNER_DISABLE_XDIST=1` to avoid `-n auto`.
  * `PYTEST_RUNNER_ENABLE_TIMEOUT=0` to disable per‑test timeouts.
  * `PYTEST_RUNNER_ENABLE_SIGUSR1=1` to request stack dumps on idle timeouts.

* `scan_monkey_patches.py` — AST‑first scan for monkey patches across the repo.
  Excludes vendor trees; strict mode disables regex fallback. Outputs JSON/CSV
  and `SUMMARY.md` under `.repo_studios/monkey_patch/<ts>/`.
  Useful options: `--strict`, `--with-git`, `--exclude-globs`.

* `compare_monkey_patch_trends.py` — Reads recent scans and writes
  `.repo_studios/monkey_patch/trend_latest.md` and JSON with deltas.
  Focus metrics include a non‑test‑only policy slice.

* `health_suite_orchestrator.py` + `health_suite_summary.py` — Collate health
  artifacts from dependency, import graph, typecheck, tests, and lizard
  complexity runs into a single Markdown summary under
  `.repo_studios/health_suite/`.
* `lizard_report.py` — Runs Lizard with repo thresholds (CCN ≤15, length ≤80),
  captures offenders, and writes markdown/JSON/raw artifacts under
  `.repo_studios/lizard/<ts>/`.

* Additional utilities:
  * `typecheck_report.py`, `import_graph_report.py`, `dep_hygiene_report.py` —
    write reports under their respective subfolders.
  * `generate_fault_artifacts.py`, `faulthandler.py` — crash/hang aids.
  * `churn_complexity_heatmap.py` — produces a churn/complexity heatmap.

Conventions:

* Python 3.11+ runtime; tools are path‑aware to `/home/founder/jarvis2`.
* Logs are idempotent and safe to commit when requested by a task.
* Prefer `make repo-insight`/`make scan-monkey-patches` wrappers when present.
* Use `make anchor-health` prior to large documentation sweeps; rename non-canonical headings proactively.

### Anchor Health Quickstart

```bash
make anchor-health              # generate timestamped report + latest pointer
FAIL_ON_DUPES=1 make anchor-health  # fail build on disallowed duplicates/baseline regression
```

Outputs per run:

* `anchor_report.json` (machine metrics: strict_duplicate_count, delta, clusters[])
* `anchor_report.md` (human summary)
* `clusters.tsv` (tabular listing)
* `runs.log` (append-only trend)

Action Loop:

1. Inspect top clusters.
2. Choose canonical file per slug; rename others with AI-prefixed context.
3. Re-run until non-allowed duplicates gone; ratchet baseline only when stable.

## 🧠 AI developer behavior

repo and Jarvis2 are active collaborators. Every `.md` file may include:

* Tasks to complete
* Standards to follow
* Logs to ingest
* Instructions to learn and evolve from

Agents must always:

* Respect architectural separation (logic, UI, config)
* Use standardized file and function formats
* Avoid modifying documentation without format integrity
* Treat `.repo_studios/` as part of agent oversight and governance. Changes here should be
  deliberate, minimally scoped, and aligned with the standards. Prefer adding tests when scripts
  change and keep dependencies pinned.

---

## 🧰 Toolchain

* [Python](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Chainlit](https://www.chainlit.io/)
* [Ruff](https://docs.astral.sh/ruff/)
* [Mypy](https://mypy.readthedocs.io/en/stable/)
* [Pytest](https://docs.pytest.org/en/stable/)

---

## 🌐 Vision

This is not just a codebase — it is a living AI-powered infrastructure designed to:

* Decrease human cognitive load
* Increase software trust, traceability, and transparency
* Enable modular knowledge and behavior reusability
* Bridge AI tooling, agents, and human collaboration

Welcome to the future of intelligent, cooperative software.

🧩 Built for scale. Designed for clarity. Powered by alignment.

---

## 🤖 How AI agents should consume this folder

Parse-only guidance:

* Treat files in `.repo_studios/` as authoritative behavior/config for agents.
* Do not edit these files unless a human task explicitly requests it.
* Prefer Makefile targets and documented commands over ad-hoc shell invocations.
* Respect security guidance: never print or log secrets; prefer environment variables.

When generating changes:

* Keep public APIs stable unless a change request states otherwise.
* Add tests for new behavior; run `make qa` locally to validate.
* Minimize diff scope; avoid reformatting unrelated code.

Quick starts and key docs:

* Metrics schema and API contracts: `docs/metrics_schema.md`
* Backfill historical perf JSON into the metrics store: `scripts/backfill_perf_json.py`
* FastAPI adapter (dev run): `uvicorn api.server:app --reload --port 8010`
* Monitoring UI readiness check: `make metrics-ui-ready`
* Make targets reference (high value shortcuts): `.repo_studios/MAKE_TARGETS.md`
* Memory refresh protocol: `.repo_studios/agent_memory_workflow.md`
* Agent memory usage (query patterns, freshness, limits): `docs/agents/memory.md`
* UI memory widget (Chainlit patterns): `docs/ui_memory_widget.md`

---

## 🧵 Memory quick‑start

Jarvis2 includes a local‑first memory pipeline (RAG) powered by the Memory Repo Protocol (MRP).
Use these docs to understand storage layout, policies, refresh workflow, and UI patterns. Start
with the repo overview, then the runbook to (re)embed docs and validate freshness and counts.

* Memory Repo overview (layout, provenance, operations): `mrp/README.md`
* Policies: redaction, retention, access, deletion/audit: `mrp/policies.md`
* Human index of embedded sources (browseable catalog): `mrp/vector_db/INDEX.md`
* Agent memory usage (query patterns, freshness, limits): `docs/agents/memory.md`
* Embedding runbook and troubleshooting: `scripts/embed_training_docs.md`
* Automated refresh workflow for agents: `.repo_studios/agent_memory_workflow.md`
