# Repo Studios Database Integration Guide

**Status:** Groundwork Phase - Inserting Dormant Connectors During Refactoring  
**Last Updated:** 2024-12-07  
**Version:** 1.1

---

## Executive Summary

This guide documents the strategy for adding database persistence to Repo Studios' reporting
infrastructure. The database will be hosted in the main repo (air-gapped environment), with Repo
Studios scripts performing **parallel writes** to both files (current) and database (new) during
the transition phase.

**Groundwork Strategy:** Insert dormant database connectors NOW during script refactoring,
controlled by `REPO_STUDIOS_DB_ENABLED=false` default. When the main repo adds agent orchestration
layer (6-12 months), simply flip the flag to activate writes.

### Key Principles

1. **Positional Encoding:** Filesystem paths mirror database schema (viewer/topic/timestamp = columns)
2. **Dual-Write Pattern:** All scripts write to files AND database simultaneously (when enabled)
3. **Graceful Degradation:** Database failures are logged but don't abort scripts
4. **Marker-Based Tracking:** All integration points tagged with `DB_INTEGRATION_MARKER`
5. **Per-Script Documentation:** Each script gets a dedicated DB schema doc
6. **Provenance Metadata:** Track WHO (requested_by) and WHY (trigger_type) outside filesystem paths

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Main Repo (Air-Gapped)                                      │
│  ┌────────────────┐         ┌──────────────────────┐        │
│  │  Agent Orch    │ ───────>│  PostgreSQL Database │        │
│  │  Layer         │ Request │  - report_runs       │        │
│  │                │ Reports │  - report_artifacts  │        │
│  └────────────────┘         │  - test_metrics      │        │
│         │                   │  - functions         │        │
│         │                   │  - duplicate_groups  │        │
│         ▼                   └──────────────────────┘        │
│  ┌────────────────┐                   ▲                     │
│  │  Agents        │                   │ Parallel Writes     │
│  │  (consume      │                   │ (files + DB)        │
│  │   report data) │                   │                     │
│  └────────────────┘                   │                     │
└───────────────────────────────────────┼─────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────┐
│  Repo Studios                         │                     │
│  ┌─────────────────────────┐          │                     │
│  │  Repo Studios Agent     │          │                     │
│  │  Orchestration Layer    │          │                     │
│  │  (future - not designed)│          │                     │
│  └─────────────────────────┘          │                     │
│         │                              │                     │
│         │ Fulfills requests            │                     │
│         ▼                              │                     │
│  ┌─────────────────────────┐          │                     │
│  │  Script Pipeline        │ ─────────┘                     │
│  │  (producers →           │                                │
│  │   consumers →           │  ┌────────────────────┐        │
│  │   aggregators →         │  │  File System       │        │
│  │   orchestrators →       ├─>│  (timestamped      │        │
│  │   summarizers)          │  │   artifacts)       │        │
│  └─────────────────────────┘  └────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Positional Encoding: Filesystem as Self-Documenting Schema

### Philosophy

**Positional encoding** means each segment of a file path encodes specific metadata in a fixed
position. This approach:

- **Eliminates parsing ambiguity** for AI agents and scripts
- **Mirrors database schema** (viewer_slug, topic, run_timestamp columns match path positions)
- **Reduces cognitive load** (no config lookups, regex guessing, or metadata files)
- **Enables filesystem-as-API** for simple queries without database access

### Path Contract

```
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

**Database Mirror:**

```sql
CREATE TABLE report_runs (
    viewer_slug VARCHAR(50),  -- Position 1
    topic VARCHAR(100),       -- Position 2
    run_timestamp TIMESTAMPTZ -- Position 3 (parsed from folder name)
);
```

**Path Parsing Helper:**

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

### Provenance Metadata (NOT in Paths)

Some metadata should NOT pollute filesystem paths but still belongs in the database:

- `requested_by`: Agent ID or "scheduled" or "manual" (WHO)
- `trigger_type`: investigation, routine, ci_triggered, git_hook (WHY)
- `request_id`: Correlation ID for agent request tracking

**Rationale:** These fields change with each request context, making them unsuitable for path-based
encoding. The database stores them for audit/debugging without cluttering file paths.

---

## Database Design

### Core Tables

#### 1. `report_runs`
Main orchestrator run records with metadata.

**Purpose:** Track every script execution with viewer, topic, timestamp, and git context.

**Key Fields:**

- `viewer_slug`: healthview, commandview, rawview, jarvis, vscode
- `topic`: test_execution_telemetry, duplicate_scan, function_analysis, etc.
- `run_timestamp`: UTC timestamp from folder name (YYYYMMDD-HHMM)
- `git_sha`: Current commit hash for traceability
- `status`: ok, warning, error
- `inputs`: JSONB of script configuration
- `catalog`: JSONB array of pipeline scripts involved

**Indexes:**

- `(viewer_slug, topic)` - Fast viewer queries
- `run_timestamp DESC` - Time-series queries
- `git_sha` - Commit-based lookups

#### 2. `report_artifacts`

Full artifact storage for all JSON/Markdown files.

**Purpose:** Store complete file contents with JSONB indexing for flexible queries.

**Key Fields:**

- `run_id`: FK to report_runs
- `artifact_role`: manifest, summary, matrix, telemetry, report, metrics
- `artifact_type`: json, md, csv
- `content_json`: Full JSON payload (GIN indexed)
- `content_text`: Markdown/text content (FTS indexed)

**Indexes:**

- `content_json` - JSONB GIN for nested queries
- `content_text` - Full-text search for AI agents

#### 3. `test_metrics`

Extracted time-series metrics for fast queries.

**Purpose:** Pre-extracted metrics avoid JSONB parsing for common queries.

**Key Fields:**

- Coverage: `coverage_pct`, `covered_functions`, `total_functions`
- Tests: `total_tests`, `passed_tests`, `failed_tests`, `slow_tests_count`
- Quality: `duplicate_function_count`, `high_complexity_count`
- JSONB: `hardening_issues`, `churn_stats`, `coverage_details`

**Indexes:**

- `metric_timestamp DESC` - Time-series queries
- `coverage_pct` - Coverage threshold queries
- `failed_tests` - Failure detection

#### 4. `functions`

Function-level inventory from CommandView.

**Purpose:** Track every function with git churn, complexity, and duplicates.

**Key Fields:**

- Location: `module_id`, `function_name`, `relative_path`, `line_number`
- Metadata: `signature`, `complexity_score`, `is_test`, `is_abstract`
- JSONB: `git_churn`, `code_smells`, `call_graph`, `dependency_summary`

**Indexes:**

- `function_name` - Find all instances of a function
- `relative_path` - File-level queries
- `complexity_score` - High-complexity detection

#### 5. `duplicate_groups`

Duplicate function groups from scan reports.

**Purpose:** Track duplicate code over time for remediation tracking.

**Key Fields:**

- `group_identifier`: Stable ID (e.g., `duplicate-def-configure-logging...`)
- `duplicate_count`: Number of instances
- `instances`: JSONB array of locations

### Materialized Views

Pre-computed aggregations for fast AI agent queries:

1. **`test_coverage_trends`** - Daily coverage rollups
2. **`top_duplicates`** - Most frequently duplicated functions
3. **`high_risk_files`** - Files with high complexity + churn

---

## Integration Pattern

### 1. Import the Library

```python
# DB_INTEGRATION_MARKER: Database integration for parallel writes
from libraries.database_integration import create_storage
```

### 2. Create Storage Instance

```python
# DB_INTEGRATION_MARKER: Create dual-write storage
storage = create_storage(
    output_dir=Path(".repo_studios/command_center/reports"),
    viewer_slug="healthview",
    topic="test_execution_telemetry",
    timestamp="20251211-1430",  # Or None for auto-generate
    enable_db=None,  # Auto-detect from config
)
```

### 3. Replace File Writes

```python
# OLD (file-only):
manifest_path = bundle_dir / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))

# NEW (dual-write):
# DB_INTEGRATION_MARKER: Dual-write manifest
storage.write_manifest(manifest)
```

### Available Write Methods

```python
storage.write_manifest(data: dict) -> None
storage.write_summary(data: dict, format: str = "json") -> None
storage.write_telemetry(data: dict) -> None
storage.write_matrix(data: dict) -> None
storage.write_metrics(data: dict) -> None
```

---

## Configuration

### Option 1: Config File (Air-Gapped)

Create `.repo_studios/db_config.json`:

```json
{
    "host": "localhost",
    "port": 5432,
    "database": "repo_studios",
    "user": "repo_agent",
    "password": "",
    "enabled": true
}
```

### Option 2: Environment Variables

```bash
export REPO_STUDIOS_DB_URL="postgresql://user:pass@localhost:5432/repo_studios"
export REPO_STUDIOS_DB_ENABLED="true"
```

### Option 3: Explicit Override

```python
storage = create_storage(..., enable_db=True)
```

---

## Per-Script Documentation

Each script being refactored should get a corresponding documentation file following the
template in [db_integration_template.md](db_integration_template.md).

### Documentation Structure

1. **Purpose & Scope** - What the script does, inputs, outputs
2. **Database Integration Plan** - Target tables, field mappings
3. **Data Mapping** - Current files → DB tables
4. **Extracted Metrics** - Time-series metric extraction logic
5. **Integration Points** - Exact line numbers where DB writes occur
6. **Validation & Testing** - Test strategy and commands
7. **Migration Checklist** - Tracking integration status
8. **Agent Query Examples** - Sample queries AI agents will run

### Example Documentation

See [db_integration_test_execution_telemetry.md](db_integration_test_execution_telemetry.md) for
a complete reference implementation.

---

## Marker Convention

**Tag:** `DB_INTEGRATION_MARKER`

**Usage:** Every integration point should include this comment so we can:

1. Grep for all integration locations
2. Generate CSV tracking reports
3. Ensure no orphaned code during migration

**Examples:**

```python
# DB_INTEGRATION_MARKER: Database integration for parallel writes
from libraries.database_integration import create_storage

# DB_INTEGRATION_MARKER: Create dual-write storage
storage = create_storage(...)

# DB_INTEGRATION_MARKER: Dual-write manifest
storage.write_manifest(manifest)

# DB_INTEGRATION_MARKER: Target schema
# INSERT INTO report_runs (viewer_slug, topic, ...) VALUES (...)
```

### Tracking Script

Generate integration status reports:

```bash
# CSV for project tracking
python .repo_studios/command_center/scripts/utilities/list_db_markers.py \
    --format csv \
    --output db_integration_status.csv

# JSON for automation
python .repo_studios/command_center/scripts/utilities/list_db_markers.py \
    --format json \
    --output db_integration_status.json

# Markdown checklist
python .repo_studios/command_center/scripts/utilities/list_db_markers.py \
    --format md \
    --output db_integration_status.md
```

---

## Script Refactoring Workflow

### Phase 1: Prepare (Per Script)

1. Read the script and understand current outputs
2. Copy template: `cp db_integration_template.md db_integration_<script_name>.md`
3. Fill in documentation:
   - Purpose & scope
   - Current outputs
   - Target DB tables
   - Data mapping
   - Metric extraction (if time-series)
4. Review with team

### Phase 2: Implement (Per Script)

1. Add import: `from libraries.database_integration import create_storage`
2. Initialize storage: `storage = create_storage(...)`
3. Replace each file write:
   ```python
   # OLD: path.write_text(json.dumps(data))
   # NEW: storage.write_manifest(data)  # DB_INTEGRATION_MARKER
   ```
4. Add markers at each integration point
5. Test with DB disabled (verify no functional change)
6. Test with DB enabled (verify dual-writes work)

### Phase 3: Validate (Per Script)

1. Run script with `--log-level DEBUG`
2. Check for `DB_INTEGRATION_MARKER` in logs
3. Verify file outputs unchanged: `diff -r old/ new/`
4. Enable DB and verify writes don't crash
5. Update migration checklist in doc
6. Commit with message: `feat(db): Add DB integration to <script_name>`

### Phase 4: Track Progress

1. Run marker tracking script weekly
2. Update CSV with completion status
3. Monitor for regressions in file outputs
4. Document any schema changes in `db_schema.sql`

---

## Time-Series vs. Non-Time-Series Reports

### Time-Series Reports

**Characteristics:**

- Generate periodic metrics (daily, per-commit, etc.)
- Need trend analysis over time
- Queried for "show me coverage over last 30 days"

**Examples:**

- Test execution telemetry
- Code coverage reports
- Churn-complexity heatmaps
- Duplicate scan trends

**DB Strategy:**

- Write to `test_metrics` table for extraction
- Keep 90 days in main table
- Aggregate to daily/weekly rollups
- Consider TimescaleDB hypertables

### Non-Time-Series Reports

**Characteristics:**

- Snapshot reports (current state only)
- Latest run is most relevant
- Queried for "show me current standards gaps"

**Examples:**

- Standards integrity checks
- Docs health reports
- Current function inventory
- Active monkey patches

**DB Strategy:**

- Write to `report_artifacts` only
- Keep last N runs (10-20)
- No time-series extraction needed
- Use materialized views for summaries

---

## Agent Query Patterns

### Common Agent Questions

#### Q1: "Is test coverage improving?"

```sql
SELECT date, avg_coverage
FROM test_coverage_trends
WHERE date > NOW() - INTERVAL '30 days'
  AND topic = 'test_execution_telemetry'
ORDER BY date;
```

#### Q2: "Which functions are duplicated most?"

```sql
SELECT function_name, max_count, run_occurrences
FROM top_duplicates
ORDER BY max_count DESC
LIMIT 20;
```

#### Q3: "Show me files with high churn and complexity"

```sql
SELECT relative_path, avg_complexity, avg_churn
FROM high_risk_files
ORDER BY (avg_complexity * avg_churn) DESC
LIMIT 50;
```

#### Q4: "What tests are failing lately?"

```sql
SELECT rr.run_timestamp, rr.git_sha, tm.failed_tests
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE tm.failed_tests > 0
  AND rr.run_timestamp > NOW() - INTERVAL '7 days'
ORDER BY rr.run_timestamp DESC;
```

#### Q5: "Find hardening issues in recent runs"

```sql
SELECT 
    rr.run_timestamp,
    tm.hardening_issues->>'summary' as summary
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE tm.hardening_issues IS NOT NULL
  AND rr.topic = 'test_execution_telemetry'
ORDER BY rr.run_timestamp DESC
LIMIT 10;
```

---

## Testing Strategy

### Unit Tests

```python
def test_dual_write_file_behavior_unchanged():
    """Verify file outputs identical with DB disabled."""
    storage = create_storage(..., enable_db=False)
    storage.write_manifest(test_data)
    
    # Assert file exists and matches expected content
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text()) == test_data

def test_db_writes_when_enabled():
    """Verify DB writes attempted when enabled."""
    storage = create_storage(..., enable_db=True)
    
    with mock.patch("database_integration.DatabaseStorage.write_manifest") as mock_write:
        storage.write_manifest(test_data)
        mock_write.assert_called_once_with(test_data)

def test_db_failure_doesnt_abort():
    """Verify graceful degradation on DB errors."""
    storage = create_storage(..., enable_db=True)
    
    with mock.patch("database_integration.DatabaseStorage.write_manifest", side_effect=Exception):
        # Should not raise
        storage.write_manifest(test_data)
        
        # File should still be written
        assert manifest_path.exists()
```

### Integration Tests

```bash
# Test full pipeline with DB disabled
make command-center COMMAND_CENTER_TARGET=scripts PYTHON=python

# Test with DB enabled (mock)
REPO_STUDIOS_DB_ENABLED=true make command-center COMMAND_CENTER_TARGET=scripts

# Verify no file differences
diff -r <old_reports> <new_reports>
```

---

## Migration Timeline

### Phase 1: Foundation (Week 1-2)

- [x] Database schema design
- [x] Integration library (`database_integration.py`)
- [x] Documentation template
- [x] Reference implementation (test_execution_telemetry)
- [x] Marker tracking utility
- [ ] Deploy schema to main repo DB

### Phase 2: Orchestrators (Week 3-4)

- [ ] Document each orchestrator
- [ ] Add DB integration to orchestrators
- [ ] Test dual-writes
- [ ] Update tests

### Phase 3: Producers (Week 5-6)

- [ ] Document producers
- [ ] Add DB integration
- [ ] Test extraction logic

### Phase 4: Consumers & Aggregators (Week 7-8)

- [ ] Document consumers/aggregators
- [ ] Add DB integration
- [ ] Validate time-series metrics

### Phase 5: Validation (Week 9-10)

- [ ] End-to-end pipeline tests
- [ ] Agent query tests
- [ ] Performance benchmarks
- [ ] Documentation review

### Phase 6: Deployment (Week 11-12)

- [ ] Enable DB in production
- [ ] Monitor dual-writes
- [ ] Train agents on DB queries
- [ ] Plan file phase-out (Q2 2026)

---

## Open Questions & Decisions Needed

1. **Connection Pooling:** Should we use asyncpg for async writes or stick with synchronous psycopg2?
2. **Retry Logic:** Do DB writes need retries, or is fire-and-forget acceptable?
3. **Schema Evolution:** How do we handle `schema_version` migrations in reports?
4. **Agent Interface:** REST API, GraphQL, or direct SQL access for agents?
5. **File Phase-Out:** When can we safely remove file outputs? Need agent training timeline.
6. **TimescaleDB:** Worth the added complexity for time-series optimization?
7. **Backup Strategy:** How often to backup DB? What's the retention policy?

---

## Resources

### Files Created

1. `.repo_studios/command_center/scripts/libraries/database_integration.py` - Core integration library
2. `.repo_studios/command_center/docs/db_integration_template.md` - Per-script doc template
3. `.repo_studios/command_center/docs/db_integration_test_execution_telemetry.md` - Reference example
4. `.repo_studios/db_schema.sql` - PostgreSQL schema
5. `.repo_studios/command_center/scripts/utilities/list_db_markers.py` - Marker tracking utility
6. This file - Comprehensive integration guide

### Key Commands

```bash
# Track integration progress
python .repo_studios/command_center/scripts/utilities/list_db_markers.py --format csv

# Deploy database schema
psql -U postgres -d repo_studios -f .repo_studios/db_schema.sql

# Test script with DB enabled
REPO_STUDIOS_DB_ENABLED=true python <script>.py --repo-root . --log-level DEBUG

# Find all integration markers
grep -r "DB_INTEGRATION_MARKER" .repo_studios/command_center/scripts/
```

---

## Next Steps

1. **Review this guide** with the team
2. **Deploy database schema** to main repo's PostgreSQL instance
3. **Choose first script** to refactor (recommend starting with an orchestrator)
4. **Create per-script documentation** using the template
5. **Implement dual-write pattern** following the reference example
6. **Test thoroughly** with DB enabled/disabled
7. **Track progress** using the marker utility

---

## Contact

**Questions?** Open an issue with `db-integration` label  
**Documentation:** See `.repo_studios/command_center/docs/db_integration_*.md` files  
**Schema:** See `.repo_studios/db_schema.sql` for complete table definitions
