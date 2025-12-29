# Groundwork and Database Alignment Plan

## Executive Summary

This document captures the strategic groundwork being laid in **Repo Studios** for future
database integration with the air-gapped main repository. The plan encompasses the dual-write
pattern, positional encoding philosophy, and the transition from file-centric to
database-centric AI agent workflows.

**Status:** Groundwork phase - inserting dormant connectors NOW during script refactoring
for future activation.

**Timeline Horizon:** Database becomes primary when main repo adds agent orchestration layer
(6-12 months estimated).

---

## Table of Contents

1. [Architectural Context](#architectural-context)
1. [Positional Encoding: The Cornerstone](#positional-encoding-the-cornerstone)
1. [Dual-Write Strategy](#dual-write-strategy)
1. [Database Schema Design](#database-schema-design)
1. [Integration Mechanics](#integration-mechanics)
1. [File Outputs Phase-Out Plan](#file-outputs-phase-out-plan)
1. [Agent Consumption Patterns](#agent-consumption-patterns)
1. [Marker Convention](#marker-convention)
1. [Timeline and Migration Phases](#timeline-and-migration-phases)
1. [Validation Checkpoints](#validation-checkpoints)

---

## Architectural Context

### Current State: Repo Studios as Standalone Add-On

**Repo Studios** is a diagnostic automation suite designed to integrate with an air-gapped main repository:

- **Repo Studios Role:** Generate test reports, analysis artifacts, and diagnostic
  outputs
- **File Outputs:** Currently the ONLY consumer interface (673 report files as of Dec 2024)
- **Main Repo Role:** Will consume reports via autonomous AI agents for issue detection,
  trend analysis, and fix proposals
- **Air-Gap Constraint:** Local PostgreSQL only, no external connectivity

### Future State: Database-Centric Agent Workflows

When the main repo adds its agent orchestration layer:

1. **Agents query database directly** for complex correlation queries (e.g., "Which files
   have both high complexity AND low test coverage AND recent duplicate increases?")
1. **File outputs continue** for human review and legacy tooling compatibility
1. **Parallel writes maintained** until agents prove trustworthy and file outputs become redundant
1. **Phase-out timeline** determined by agent maturity, not calendar deadlines

### Why Insert Database Connectors NOW

- **Refactoring Opportunity:** Scripts are being restructured (tier migration, library consolidation)
- **Future-Proof Instrumentation:** Avoid revisiting every script later when database activates
- **Marker-Driven Tracking:** `DB_INTEGRATION_MARKER` tags enable grep-based progress audits
- **Zero Operational Impact:** Dormant writes controlled by `REPO_STUDIOS_DB_ENABLED=false` default
- **Agent Training Alignment:** Positional encoding in filesystem prepares agents for DB
  schema mirroring

---

## Positional Encoding: The Cornerstone

### Philosophy

**Positional encoding** means each segment of a file path encodes specific metadata in a
fixed position. This creates a self-documenting filesystem structure that:

- **Eliminates parsing ambiguity** for AI agents and scripts
- **Mirrors database schema** (viewer_slug, topic, run_timestamp columns match path positions)
- **Reduces cognitive load** (no config lookups, regex guessing, or metadata files)
- **Enables filesystem-as-API** for simple queries without touching the database

### Path Contract

```text
<reports_root>/<viewer_slug>/<topic>/<timestamp>/<artifact>
     ↓              ↓           ↓         ↓          ↓
  Position 0   Position 1  Position 2  Position 3  Position 4

Example:
.repo_studios/command_center/reports/healthview/test_execution_telemetry/20251207-0330/manifest.json
                                         ↓                ↓                    ↓            ↓
                                  viewer_slug=        topic=           run_timestamp=  artifact=
                                  "healthview"   "test_execution_   "2024-12-07       "manifest.json"
                                                   telemetry"          03:30 UTC"
```

### Positional Components

| Position | Name | Values | Purpose |
|----------|------|--------|---------|
| 1 | `viewer_slug` | healthview, commandview, rawview, jarvis, vscode | WHO consumes (monitoring, ops, diagnostics, agents, IDE) |
| 2 | `topic` | test_execution_telemetry, duplicate_scan, complexity_analysis | WHAT data (report subject/scope) |
| 3 | `timestamp` | YYYYMMDD-HHMM (UTC) | WHEN generated (sortable, no special chars) |
| 4 | `artifact` | manifest.json, summary.md, matrix.json | FORMAT/TYPE of output |

### Database Mirror

The database schema **directly mirrors** this positional encoding:

```sql
CREATE TABLE report_runs (
    viewer_slug VARCHAR(50),  -- Position 1
    topic VARCHAR(100),       -- Position 2
    run_timestamp TIMESTAMPTZ -- Position 3 (parsed from folder name)
);
```

**Agent Query Benefits:**

- Simple questions use filesystem: "What's the latest healthview duplicate scan?" →
  glob `healthview/duplicate_scan/*` and sort
- Complex questions use database: "Show test failure trends across all topics for the
  last 30 days grouped by viewer" → SQL JOIN + aggregation

### Timestamp Format Contract

**Format:** `YYYYMMDD-HHMM` (13 characters, UTC timezone)

**Rationale:**

- **Sortable:** Lexicographic sort = chronological sort (no date parsing required)
- **No Special Chars:** Hyphens only (safe for URLs, shells, Windows paths)
- **Human-Readable:** 20251207-0330 reads as "December 7, 2025 at 3:30 AM UTC"
- **Collision-Resistant:** Minute-level granularity prevents same-script overlaps
- **Fixed Width:** Enables column alignment in `ls -l` output and text tables

**Migration Note:** Legacy underscores (`20251207_033000`) are being replaced with hyphens during refactoring.

---

## Dual-Write Strategy

### Pattern Overview

During the transition period, all report-generating scripts will:

1. **Write to filesystem** (existing behavior, remains source of truth)
1. **Write to database** (dormant stub, controlled by `REPO_STUDIOS_DB_ENABLED` env var)
1. **Orchestrate via DualWriteStorage** class that delegates to both backends

### Implementation

```python
# scripts/libraries/database_integration.py provides:

from command_center.scripts.libraries.database_integration import create_storage

# In each script's write path:
storage = create_storage()  # Auto-detects config and env vars

# Replace:
# write_json("manifest.json", data)
# write_markdown("summary.md", content)

# With:
storage.write_manifest(data)  # Writes to filesystem AND database (if enabled)
storage.write_summary(content)
```

### Configuration Control

**Dormant by Default:**

```bash
# .repo_studios/db_config.json (does NOT exist initially)
{
  "enabled": false,  # No-op for database writes
  "connection_string": "postgresql://localhost/repo_studios_reports"
}

# Or via environment variable (overrides config file):
export REPO_STUDIOS_DB_ENABLED=false  # Default assumption
```

**Activation When Ready:**

```bash
# Main repo deployment:
export REPO_STUDIOS_DB_ENABLED=true
export REPO_STUDIOS_DB_CONNECTION="postgresql://user:pass@localhost:5432/reports"

# Repo Studios scripts detect enabled state and execute INSERT statements
```

### Stub Behavior

When `enabled=false` (current state):

- `FileSystemStorage` writes files normally
- `DatabaseStorage.write_manifest()` executes no-op (logs `[DB] Would insert...` at DEBUG level)
- `DualWriteStorage` delegates to both but DB writes are stubbed out
- **Zero database dependencies** required until activation

When `enabled=true` (future state):

- `DatabaseStorage.write_manifest()` executes `INSERT INTO report_runs (...)`
- Database connection pooling and retry logic activate
- Failures logged but do NOT abort file writes (files remain source of truth)

---

## Database Schema Design

### Core Tables

#### `report_runs` - Main Orchestrator Records

```sql
CREATE TABLE report_runs (
    id BIGSERIAL PRIMARY KEY,
    viewer_slug VARCHAR(50) NOT NULL,        -- Position 1
    topic VARCHAR(100) NOT NULL,             -- Position 2
    run_timestamp TIMESTAMPTZ NOT NULL,      -- Position 3
    git_sha VARCHAR(40),                     -- Repo commit hash
    status VARCHAR(20),                      -- ok, warning, error
    
    -- Provenance (NOT in filesystem path)
    requested_by VARCHAR(255),               -- Agent ID or 'scheduled' or 'manual'
    trigger_type VARCHAR(50),                -- investigation, routine, ci_triggered, git_hook
    request_id VARCHAR(100),                 -- Correlation ID for agent requests
    
    -- Flexible metadata
    inputs JSONB,                            -- Script configuration
    catalog JSONB,                           -- Pipeline script manifest
    
    CONSTRAINT uniq_run UNIQUE(viewer_slug, topic, run_timestamp)
);
```

**Positional Columns:** `viewer_slug`, `topic`, `run_timestamp` mirror path positions
1-3.

**Provenance Columns:** `requested_by`, `trigger_type`, `request_id` capture WHO and WHY
(not encoded in paths).

#### `report_artifacts` - JSONB Storage for Flexible Reports

```sql
CREATE TABLE report_artifacts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL,      -- Position 4: 'manifest', 'summary', 'matrix'
    content JSONB NOT NULL,                  -- Full artifact content
    file_path TEXT,                          -- Original filesystem path (reference only)
    
    CONSTRAINT uniq_artifact UNIQUE(run_id, artifact_type)
);
```

**Artifact Type:** Maps to position 4 filename stem (manifest.json → `artifact_type='manifest'`).

**JSONB Content:** Entire JSON payload for agent queries without file I/O.

#### `test_metrics` - Time-Series Data for Trend Analysis

```sql
CREATE TABLE test_metrics (
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    metric_name VARCHAR(100),                -- passed_count, failed_count, coverage_pct
    metric_value NUMERIC,
    metric_unit VARCHAR(20),                 -- count, percentage, seconds
    
    PRIMARY KEY (run_id, metric_name)
);
```

**Time-Series Optimization:** Partitionable by `run_timestamp` when using TimescaleDB extension.

#### `functions` - Function Inventory for Complexity/Coverage Tracking

```sql
CREATE TABLE functions (
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    function_name TEXT NOT NULL,
    nloc INTEGER,                            -- Lines of code
    complexity INTEGER,                      -- Cyclomatic complexity
    token_count INTEGER,
    parameter_count INTEGER,
    start_line INTEGER,
    end_line INTEGER,
    
    PRIMARY KEY (run_id, file_path, function_name, start_line)
);
```

**Agent Use Case:** "Show functions with complexity > 15 AND no test coverage" (JOIN with coverage data).

#### `duplicate_groups` - Clone Detection Results

```sql
CREATE TABLE duplicate_groups (
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    group_id TEXT NOT NULL,                  -- "group_1", "group_2"
    file_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    token_count INTEGER,
    
    PRIMARY KEY (run_id, group_id, file_path, start_line)
);
```

**Agent Use Case:** "Which duplicate groups have grown in the last 5 runs?" (GROUP BY + LAG window function).

### Materialized Views for Agent Queries

```sql
-- Pre-aggregated coverage trends
CREATE MATERIALIZED VIEW test_coverage_trends AS
SELECT 
    viewer_slug,
    topic,
    DATE_TRUNC('day', run_timestamp) AS day,
    AVG((inputs->>'coverage_pct')::numeric) AS avg_coverage
FROM report_runs
WHERE inputs ? 'coverage_pct'
GROUP BY viewer_slug, topic, day
ORDER BY day DESC;

-- High-risk files (complexity × duplicate count × low coverage)
CREATE MATERIALIZED VIEW high_risk_files AS
SELECT 
    f.file_path,
    AVG(f.complexity) AS avg_complexity,
    COUNT(DISTINCT dg.group_id) AS duplicate_group_count,
    MIN((rr.inputs->>'coverage_pct')::numeric) AS min_coverage
FROM functions f
JOIN report_runs rr ON f.run_id = rr.id
LEFT JOIN duplicate_groups dg ON f.run_id = dg.run_id AND f.file_path = dg.file_path
GROUP BY f.file_path
HAVING AVG(f.complexity) > 10 OR COUNT(DISTINCT dg.group_id) > 2
ORDER BY (AVG(f.complexity) * COUNT(DISTINCT dg.group_id)) DESC;
```

**Agent Query:** `SELECT * FROM high_risk_files LIMIT 10` → instant results without scanning raw tables.

---

## Integration Mechanics

### Per-Script Integration Pattern

Each report-generating script follows this pattern:

1. **Import storage factory:** `from command_center.scripts.libraries.database_integration import create_storage`
1. **Create storage instance:** `storage = create_storage()`
1. **Replace file writes:** `storage.write_manifest(data)` instead of `json.dump(...)`
1. **Add DB_INTEGRATION_MARKER:** `# DB_INTEGRATION_MARKER: Dual-write to filesystem + database`
1. **Document schema mapping:** Create `db_integration_<script_name>.md` in `command_center/docs/`

### Schema Documentation Template

Every script with DB writes gets a companion doc:

**File:** `.repo_studios/command_center/docs/db_integration_<script_name>.md`

**Sections:**

1. **Script Overview:** Purpose, inputs, outputs
1. **Database Tables:** Which tables receive writes (report_runs, report_artifacts, etc.)
1. **Data Extraction Logic:** Python code showing how manifest.json maps to INSERT columns
1. **Integration Points:** Line numbers where `storage.write_*()` calls occur
1. **Example Queries:** SQL that agents might use to consume this data

**Reference Example:** `.repo_studios/command_center/docs/db_integration_test_execution_telemetry.md`

### Marker Convention

**Purpose:** Grep-based tracking of integration status across 77 scripts.

**Tag:** `# DB_INTEGRATION_MARKER: <description>`

**Placement:** Above `storage.write_*()` calls or at top of script if global.

**Examples:**

```python
# DB_INTEGRATION_MARKER: Dual-write manifest to filesystem + database (report_runs table)
storage.write_manifest({
    "viewer_slug": "healthview",
    "topic": "test_execution_telemetry",
    "run_timestamp": timestamp,
    "status": "ok",
    "inputs": {...}
})

# DB_INTEGRATION_MARKER: Store test metrics as time-series data (test_metrics table)
storage.write_metrics([
    {"metric_name": "passed_count", "metric_value": 42},
    {"metric_name": "failed_count", "metric_value": 3}
])
```

**Audit Command:**

```bash
python .repo_studios/command_center/scripts/utilities/list_db_markers.py \
    --format markdown \
    --output reports/db_integration_status.md
```

**Output:** Table showing script name, marker count, and readiness status.

---

## File Outputs Phase-Out Plan

### Timeline Triggers (NOT Calendar Dates)

File outputs will be phased out based on **agent maturity milestones**, not arbitrary deadlines:

1. **Milestone 1: Database Activation** (main repo ready)
   - Trigger: Agent orchestration layer deployed
   - Action: Set `REPO_STUDIOS_DB_ENABLED=true`
   - Result: Parallel writes to files + database

1. **Milestone 2: Agent Validation** (6-12 weeks after activation)
   - Trigger: Agents demonstrate correct query patterns in production
   - Action: Monitor agent error rates, query latencies, data accuracy
   - Result: Confidence that agents prefer database over file parsing

1. **Milestone 3: File Redundancy** (3-6 months after validation)
   - Trigger: Zero agent file reads observed for 30 consecutive days
   - Action: Deprecate file writes for agent-consumed reports (keep human-facing summaries)
   - Result: Database becomes primary interface, files become optional exports

1. **Milestone 4: Full Database Primary** (6-12 months after validation)
   - Trigger: All consumers (agents + humans) query database or use on-demand exports
   - Action: Remove `FileSystemStorage` from `DualWriteStorage` orchestrator
   - Result: File generation only on explicit request (e.g., CI artifacts, audit logs)

### What Stays as Files

Even after database becomes primary:

- **Markdown summaries:** Human-readable reports for code review and documentation
- **Audit logs:** Compliance and debugging artifacts
- **CI/CD artifacts:** Pipeline outputs uploaded to build systems
- **Ad-hoc exports:** On-demand CSV/JSON for spreadsheet analysis

---

## Agent Consumption Patterns

### Simple Queries (Filesystem API)

When agents need latest report or single-topic lookup:

```python
# Agent logic:
latest_manifest = glob("healthview/test_execution_telemetry/*/manifest.json")[-1]
data = json.load(open(latest_manifest))
```

**Why Filesystem Works:** Positional encoding + glob + sort is faster than SQL connection
for single-file reads.

### Complex Queries (Database API)

When agents need correlation, aggregation, or trend analysis:

```sql
-- Agent SQL query:
SELECT 
    rr.run_timestamp,
    rr.topic,
    COUNT(CASE WHEN tm.metric_name = 'failed_count' THEN 1 END) AS failures,
    AVG(CASE WHEN tm.metric_name = 'coverage_pct' THEN tm.metric_value END) AS avg_coverage
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE rr.viewer_slug = 'healthview'
  AND rr.run_timestamp > NOW() - INTERVAL '30 days'
GROUP BY rr.run_timestamp, rr.topic
ORDER BY failures DESC;
```

**Why Database Required:** Joining test_metrics with report_runs across 30 days of runs
requires index scans and aggregation that filesystems cannot provide.

### Materialized View Usage

For recurring agent queries (e.g., daily "high-risk file" report):

```sql
-- Agent queries pre-computed view:
SELECT file_path, avg_complexity, duplicate_group_count, min_coverage
FROM high_risk_files
WHERE min_coverage < 50.0
ORDER BY (avg_complexity * duplicate_group_count) DESC
LIMIT 20;
```

**Refresh Strategy:** Materialized views refreshed after each orchestrator run via
`REFRESH MATERIALIZED VIEW` in DatabaseStorage.

---

## Timeline and Migration Phases

### Phase 1: Groundwork (Current - 2 months)

**Objective:** Insert dormant database connectors during script refactoring.

**Tasks:**

- [x] Design PostgreSQL schema (`.repo_studios/db_schema.sql`)
- [x] Create integration library (`scripts/libraries/database_integration.py`)
- [x] Update REPORT_NAMING_STANDARDS.md with positional encoding
- [x] Create DB integration template + reference example
- [x] Build marker tracking utility (`utilities/list_db_markers.py`)
- [ ] Refactor 77 scripts to use `create_storage()` pattern
- [ ] Document each script's schema mapping
- [ ] Tag all integration points with DB_INTEGRATION_MARKER
- [ ] Run marker audit and verify 100% script coverage
- [ ] Freeze filesystem structure (no more path changes)

**Deliverables:**

- All scripts use dual-write pattern (dormant database writes)
- Every script has `db_integration_<name>.md` documentation
- Marker audit report shows readiness for activation

### Phase 2: Activation (Main Repo Ready + 1 week)

**Objective:** Enable database writes when main repo deploys agent layer.

**Prerequisites:**

- Main repo has PostgreSQL instance deployed (air-gapped)
- Agent orchestration layer can issue SQL queries
- Connection credentials configured via environment variables

**Tasks:**

- Set `REPO_STUDIOS_DB_ENABLED=true` in main repo environment
- Run first orchestrator with database writes enabled
- Verify `report_runs` table populated
- Query database from agent layer (sanity check)
- Monitor for INSERT errors and connection issues

**Rollback Plan:** Set `REPO_STUDIOS_DB_ENABLED=false` if errors exceed 5% of writes.

### Phase 3: Validation (Activation + 6-12 weeks)

**Objective:** Prove agents query database correctly and prefer it over file parsing.

**Metrics:**

- Agent query success rate > 95%
- Agent SQL error rate < 1%
- Database query latency < 100ms (p95)
- Zero data inconsistencies between files and database

**Tasks:**

- Instrument agent queries with telemetry (query patterns, latencies, errors)
- Run weekly audits comparing file contents vs database rows
- Gather agent feedback on missing columns or schema mismatches
- Optimize slow queries (add indexes, tune JSONB GIN indexes)
- Document common agent query patterns in `db_integration_guide.md`

**Success Criteria:** Agents confidently consume database for complex queries without
reverting to file parsing.

### Phase 4: File Deprecation (Validation + 3-6 months)

**Objective:** Phase out file writes for agent-consumed reports.

**Conditions:**

- Zero agent file reads for 30 consecutive days
- Humans still access markdown summaries via file paths

**Tasks:**

- Remove `FileSystemStorage` from `DualWriteStorage` for agent reports
- Keep filesystem writes for human-facing summaries (markdown, audit logs)
- Update documentation to mark file outputs as "legacy interface"
- Archive historical report files to cold storage

**Deliverable:** Database is primary interface; files are optional exports.

---

## Validation Checkpoints

### Checkpoint 1: Groundwork Complete

**When:** End of Phase 1 (2 months)

**Criteria:**

- [ ] All 77 scripts use `create_storage()` pattern
- [ ] Every script has DB_INTEGRATION_MARKER tags
- [ ] Marker audit shows 100% coverage
- [ ] All scripts have `db_integration_<name>.md` docs
- [ ] Test suite passes with `REPO_STUDIOS_DB_ENABLED=false` (no database dependencies)

**Verification:**

```bash
# Run marker audit:
python utilities/list_db_markers.py --format markdown

# Run test suite:
pytest tests/ -v

# Verify no database imports in production code paths:
grep -r "psycopg2" scripts/ | grep -v "database_integration.py"
```

### Checkpoint 2: Activation Successful

**When:** 1 week after setting `REPO_STUDIOS_DB_ENABLED=true`

**Criteria:**

- [ ] `report_runs` table contains ≥5 successful runs
- [ ] `report_artifacts` table populated with manifest/summary/matrix JSONBs
- [ ] No INSERT failures in logs
- [ ] Agent layer successfully queries database (sanity check)

**Verification:**

```sql
-- Check recent runs:
SELECT viewer_slug, topic, run_timestamp, status 
FROM report_runs 
ORDER BY run_timestamp DESC 
LIMIT 10;

-- Verify artifacts:
SELECT artifact_type, COUNT(*) 
FROM report_artifacts 
GROUP BY artifact_type;
```

### Checkpoint 3: Agent Validation

**When:** 12 weeks after activation

**Criteria:**

- [ ] Agent query success rate > 95%
- [ ] SQL error rate < 1%
- [ ] No data inconsistencies between files and database
- [ ] Agents demonstrate preference for database over file parsing

**Verification:**

```sql
-- Query agent telemetry (hypothetical table in main repo):
SELECT query_pattern, success_rate, avg_latency_ms
FROM agent_query_telemetry
WHERE query_timestamp > NOW() - INTERVAL '7 days'
ORDER BY success_rate ASC;
```

### Checkpoint 4: File Phase-Out Ready

**When:** Validation + 3-6 months

**Criteria:**

- [ ] Zero agent file reads for 30 consecutive days
- [ ] Database queries handle 100% of agent needs
- [ ] Markdown summaries still generated for humans

**Verification:**

```bash
# Check agent file access logs (hypothetical):
grep "file_read" /var/log/agent_orchestrator.log | tail -n 1000

# If empty or only human-initiated reads → ready for phase-out
```

---

## Appendices

### A. Positional Encoding Reference

| Position | Column | Type | Description | Example |
|----------|--------|------|-------------|---------|
| 0 | `reports_root` | Path | Base directory | `.repo_studios/command_center/reports` |
| 1 | `viewer_slug` | VARCHAR(50) | Target viewer | `healthview` |
| 2 | `topic` | VARCHAR(100) | Report subject | `test_execution_telemetry` |
| 3 | `timestamp` | TIMESTAMPTZ | UTC run time | `20251207-0330` |
| 4 | `artifact` | VARCHAR(50) | File type | `manifest.json` |

**Path Parsing Logic:**

```python
def parse_report_path(path: str) -> dict:
    """Extract positional metadata from report file path."""
    parts = Path(path).parts
    return {
        "viewer_slug": parts[-4],
        "topic": parts[-3],
        "timestamp": parts[-2],  # Convert YYYYMMDD-HHMM to TIMESTAMPTZ
        "artifact": parts[-1]
    }
```

### B. Viewer Registry

| Slug | Purpose | Primary Consumers | Report Types |
|------|---------|-------------------|--------------|
| `healthview` | Monitoring/alerting | Ops agents, dashboards | Test telemetry, coverage trends |
| `commandview` | Operations/debugging | Dev agents, CLI tools | Duplicate scans, complexity reports |
| `rawview` | Diagnostic deep-dives | Investigation agents | Lizard/Radon raw outputs |
| `jarvis` | AI agent interface | Agent orchestrator | Aggregated multi-source reports |
| `vscode` | IDE integration | Extensions, linters | In-editor annotations |

### C. Database vs Filesystem Decision Matrix

| Query Type | Interface | Rationale |
|------------|-----------|-----------|
| "Latest manifest for topic X" | Filesystem | Glob + sort faster than SQL for single file |
| "Last 30 days of test failures" | Database | Time-series aggregation requires indexes |
| "Files with complexity > 15 AND duplicates" | Database | JOIN + WHERE impossible with file parsing |
| "Markdown summary for human review" | Filesystem | Files are rendered directly in browsers/editors |
| "Correlation between coverage drops and test failures" | Database | Multi-table JOIN with window functions |

### D. Common Agent SQL Queries

#### 1. High-Risk Files (Complexity × Duplicates)

```sql
SELECT f.file_path, AVG(f.complexity) AS avg_complexity, COUNT(DISTINCT dg.group_id) AS dup_count
FROM functions f
LEFT JOIN duplicate_groups dg ON f.run_id = dg.run_id AND f.file_path = dg.file_path
GROUP BY f.file_path
HAVING AVG(f.complexity) > 10 OR COUNT(DISTINCT dg.group_id) > 2
ORDER BY (AVG(f.complexity) * COUNT(DISTINCT dg.group_id)) DESC
LIMIT 20;
```

#### 2. Test Coverage Trends (Last 30 Days)

```sql
SELECT 
    DATE_TRUNC('day', run_timestamp) AS day,
    AVG((inputs->>'coverage_pct')::numeric) AS avg_coverage
FROM report_runs
WHERE viewer_slug = 'healthview'
  AND topic = 'test_execution_telemetry'
  AND run_timestamp > NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day DESC;
```

#### 3. Recent Test Failures by Topic

```sql
SELECT rr.topic, SUM((tm.metric_value)::int) AS total_failures
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE tm.metric_name = 'failed_count'
  AND rr.run_timestamp > NOW() - INTERVAL '7 days'
GROUP BY rr.topic
ORDER BY total_failures DESC;
```

---

## Conclusion

This groundwork phase establishes the foundation for a seamless transition from file-centric
to database-centric AI agent workflows:

1. **Positional encoding** creates a self-documenting filesystem that mirrors the database
   schema
1. **Dual-write pattern** enables parallel file and database outputs with zero operational
   risk
1. **Marker convention** provides grep-based tracking of integration readiness across
   77 scripts
1. **Provenance columns** capture WHO and WHY without polluting filesystem paths
1. **Milestone-driven phase-out** ensures file outputs remain until agents prove trustworthy

**Next Actions:**

- Complete script refactoring to use `create_storage()` pattern (Phase 1)
- Document all schema mappings in per-script integration docs
- Run marker audit to verify 100% script coverage
- Freeze filesystem structure for agent training alignment

**Future Activation:** When main repo deploys agent orchestration layer, set
`REPO_STUDIOS_DB_ENABLED=true` and begin Phase 2 (Activation + Validation).

---

**Document Version:** 1.0  
**Last Updated:** 2024-12-07  
**Authors:** Repo Studios Team  
**Status:** Living document - update after each migration phase
