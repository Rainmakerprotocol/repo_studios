# Database Integration Documentation

**Script:** `run_test_execution_telemetry.py`

**Tier:** orchestrator  
**Viewer:** healthview  
**Topic:** test_execution_telemetry  
**Last Updated:** 2025-12-11  
**Schema Version:** 1.0

---

## Purpose & Scope

### What This Script Does
Orchestrates the complete test execution telemetry pipeline by coordinating test coverage analysis, test hardening checks, log health reports, and churn-complexity heatmap generation into a unified health snapshot.

### Inputs
- **File-based:** 
  - JUnit XML files (optional)
  - Test log directories in `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs`
  - Git repository for churn analysis
- **Configuration:** 
  - `--repo-root`: Repository root path
  - `--log-level`: Logging verbosity
  - `--viewer`: Viewer slug (default: healthview)
- **Dependencies:** 
  - `generate_test_coverage_inventory.py` (producer)
  - `analyze_test_hardening.py` (producer)
  - `collect_test_log_reports.py` (producer)
  - `generate_test_log_health_report.py` (consumer)
  - `generate_churn_complexity_heatmap.py` (aggregator)
  - `summarize_test_execution_telemetry.py` (summarizer)

### Outputs (Current)
- **File artifacts:** 
  - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/manifest.json`
  - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/test_execution_telemetry_summary.json`
  - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/test_execution_telemetry_summary.md`
  - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/telemetry.json`
- **Logs:** Standard logging to console
- **Side effects:** Invokes 6 child scripts, creates timestamped directories

---

## Database Integration Plan

### DB_INTEGRATION_MARKER: Schema Requirements

#### Primary Table(s)

```sql
-- Main orchestrator run record
CREATE TABLE report_runs (
    id BIGSERIAL PRIMARY KEY,
    viewer_slug VARCHAR(50) NOT NULL,        -- 'healthview'
    topic VARCHAR(100) NOT NULL,             -- 'test_execution_telemetry'
    run_timestamp TIMESTAMPTZ NOT NULL,      -- From folder name YYYYMMDD-HHMM
    git_sha VARCHAR(40),                     -- Current git commit
    repo_root TEXT,                          -- Absolute repo path
    status VARCHAR(20),                      -- 'ok', 'warning', 'error'
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    inputs JSONB,                            -- Script inputs and config
    catalog JSONB,                           -- Pipeline script manifest
    
    UNIQUE(viewer_slug, topic, run_timestamp)
);

CREATE INDEX idx_runs_viewer_topic ON report_runs(viewer_slug, topic);
CREATE INDEX idx_runs_timestamp ON report_runs(run_timestamp DESC);
CREATE INDEX idx_runs_git_sha ON report_runs(git_sha);
```

#### Secondary/Related Tables

```sql
-- Artifacts storage (manifests, summaries, etc.)
CREATE TABLE report_artifacts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    artifact_role VARCHAR(50) NOT NULL,      -- 'manifest', 'summary', 'telemetry'
    artifact_type VARCHAR(10) NOT NULL,      -- 'json', 'md'
    file_path TEXT,                          -- Original file path
    file_size_bytes BIGINT,
    content_json JSONB,                      -- For JSON files
    content_text TEXT,                       -- For Markdown files
    checksum VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifacts_run ON report_artifacts(run_id);
CREATE INDEX idx_artifacts_role ON report_artifacts(artifact_role);
CREATE INDEX idx_artifacts_content ON report_artifacts USING GIN(content_json);

-- Extracted metrics for time-series queries
CREATE TABLE test_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    metric_timestamp TIMESTAMPTZ NOT NULL,
    
    -- Coverage metrics
    coverage_pct DECIMAL(5,2),
    covered_functions INTEGER,
    total_functions INTEGER,
    total_files INTEGER,
    files_below_threshold INTEGER,
    
    -- Test execution metrics
    total_tests INTEGER,
    passed_tests INTEGER,
    failed_tests INTEGER,
    slow_tests_count INTEGER,
    warnings_total INTEGER,
    
    -- Code quality metrics
    duplicate_function_count INTEGER,
    high_complexity_count INTEGER,
    high_churn_files INTEGER,
    
    -- Detailed metrics (JSONB)
    hardening_issues JSONB,                  -- Full hardening payload
    churn_stats JSONB,                       -- Churn-complexity heatmap data
    coverage_details JSONB                   -- Files below threshold, etc.
);

CREATE INDEX idx_metrics_timestamp ON test_metrics(metric_timestamp DESC);
CREATE INDEX idx_metrics_run ON test_metrics(run_id);
```

### Data Mapping

| Current File | Artifact Role | Target Table | Key Fields | Notes |
|--------------|---------------|--------------|------------|-------|
| `manifest.json` | manifest | `report_runs` | `viewer_slug`, `topic`, `run_timestamp`, `git_sha`, `inputs`, `catalog` | Main run record |
| `manifest.json` | manifest | `report_artifacts` | `run_id`, `artifact_role='manifest'`, `content_json` | Full manifest backup |
| `test_execution_telemetry_summary.json` | summary | `report_artifacts` | `run_id`, `artifact_role='summary'`, `artifact_type='json'`, `content_json` | JSON summary |
| `test_execution_telemetry_summary.md` | summary | `report_artifacts` | `run_id`, `artifact_role='summary'`, `artifact_type='md'`, `content_text` | Markdown summary |
| `telemetry.json` | telemetry | `report_artifacts` | `run_id`, `artifact_role='telemetry'`, `content_json` | Full telemetry payload |
| `telemetry.json` (extracted) | telemetry | `test_metrics` | All metrics columns + JSONB fields | Time-series metrics |

### Extracted Metrics

Extract queryable metrics from the telemetry JSON:

```python
# Extract from test_execution_telemetry_summary.json structure:
{
    # Coverage metrics
    "coverage_pct": data["components"]["coverage"]["summary"]["overall_coverage_pct"],
    "covered_functions": data["components"]["coverage"]["summary"]["covered_functions"],
    "total_functions": data["components"]["coverage"]["summary"]["total_functions"],
    "total_files": data["components"]["coverage"]["summary"]["total_files"],
    "files_below_threshold": len(data["components"]["coverage"]["summary"]["files_below_threshold"]),
    
    # Test execution (from collect step)
    "total_tests": data["components"]["collect"]["warnings_total"],  # Placeholder
    "slow_tests_count": data["components"]["collect"]["slow_tests_over_threshold"],
    "warnings_total": data["components"]["collect"]["warnings_total"],
    
    # Failures
    "failed_tests": data["failures"]["detected"],
    
    # Detailed JSONB fields
    "hardening_issues": data["components"]["hardening"]["payload"],
    "churn_stats": data["components"]["heatmap"]["payload"],
    "coverage_details": {
        "files_below_threshold": data["components"]["coverage"]["summary"]["files_below_threshold"],
        "status": data["components"]["coverage"]["summary"]["status"]
    }
}
```

**Target Table:** `test_metrics`

**Extraction Logic:**
- `coverage_pct` ← `data['components']['coverage']['summary']['overall_coverage_pct']`
- `covered_functions` ← `data['components']['coverage']['summary']['covered_functions']`
- `total_functions` ← `data['components']['coverage']['summary']['total_functions']`
- `failed_tests` ← `data['failures']['detected']`
- `hardening_issues` ← `data['components']['hardening']['payload']` (full JSONB)
- `churn_stats` ← `data['components']['heatmap']['payload']` (full JSONB)

### Time-Series Considerations

**Is this a time-series report?** Yes

**Retention Policy:** 
- Database: Keep 90 days of raw records, aggregate to daily rollups after 30 days
- Files: Keep 10 most recent runs per topic (current behavior)

**Aggregation Windows:** 
- Daily: Average coverage, total failures, warning counts
- Weekly: Trend analysis for coverage delta
- Monthly: High-level health dashboard

**Query Patterns:**
```sql
-- Q1: Show test coverage trends over last 30 days
SELECT 
    DATE_TRUNC('day', metric_timestamp) as date,
    AVG(coverage_pct) as avg_coverage,
    AVG(failed_tests) as avg_failures
FROM test_metrics tm
JOIN report_runs rr ON tm.run_id = rr.id
WHERE rr.topic = 'test_execution_telemetry'
  AND tm.metric_timestamp > NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date;

-- Q2: Find runs with coverage below threshold
SELECT 
    rr.run_timestamp,
    rr.git_sha,
    tm.coverage_pct,
    tm.files_below_threshold
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE rr.topic = 'test_execution_telemetry'
  AND tm.coverage_pct < 80.0
ORDER BY rr.run_timestamp DESC;

-- Q3: Identify files with high churn + complexity (from JSONB)
SELECT 
    rr.run_timestamp,
    jsonb_array_elements(tm.churn_stats->'high_risk_files') as risky_file
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE rr.topic = 'test_execution_telemetry'
  AND tm.churn_stats IS NOT NULL
ORDER BY rr.run_timestamp DESC
LIMIT 20;
```

---

## Integration Points

### DB_INTEGRATION_MARKER: Code Locations

#### 1. Import Section
```python
# Add near line 5-15 (after standard imports)
from libraries.database_integration import create_storage

# DB_INTEGRATION_MARKER: Database integration for parallel writes
```

#### 2. Storage Initialization
```python
# Add in run() function after paths setup (around line 100)
def run(argv):
    # ... existing setup ...
    
    # DB_INTEGRATION_MARKER: Create dual-write storage
    storage = create_storage(
        output_dir=paths.reports_root,
        viewer_slug=options.viewer,
        topic="test_execution_telemetry",
        timestamp=run_timestamp,
    )
```

#### 3. Write Operations

**Manifest Write:**
```python
# Replace existing manifest.json write (around line 300)
# OLD:
# manifest_path = bundle_dir / "manifest.json"
# manifest_path.write_text(json.dumps(manifest, indent=2))

# NEW:
# DB_INTEGRATION_MARKER: Dual-write manifest
storage.write_manifest(manifest)
```

**Summary Writes:**
```python
# Replace existing summary writes (around line 350)
# OLD:
# summary_json_path.write_text(json.dumps(summary, indent=2))
# summary_md_path.write_text(markdown_summary)

# NEW:
# DB_INTEGRATION_MARKER: Dual-write summaries
storage.write_summary(summary, format="json")
storage.write_summary({"markdown": markdown_summary}, format="md")
```

**Telemetry Write:**
```python
# Replace existing telemetry write (around line 400)
# OLD:
# telemetry_path = bundle_dir / "telemetry.json"
# telemetry_path.write_text(json.dumps(telemetry, indent=2))

# NEW:
# DB_INTEGRATION_MARKER: Dual-write telemetry (includes metric extraction)
storage.write_telemetry(telemetry)
```

### Configuration Dependencies

**Environment Variables:**
- `REPO_STUDIOS_DB_URL` - PostgreSQL connection string (future: provided by main repo)
- `REPO_STUDIOS_DB_ENABLED` - Explicit enable/disable flag (default: false)

**Config Files:**
- `.repo_studios/db_config.json` - Local air-gapped DB config (optional)

**Example config:**
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

---

## Validation & Testing

### DB_INTEGRATION_MARKER: Test Strategy

#### File Output Validation
- [x] Manifest written to `reports/healthview/test_execution_telemetry/<timestamp>/manifest.json`
- [x] JSON summary has correct schema
- [x] Markdown summary follows authoring standards
- [x] Telemetry includes all component data

#### DB Write Validation (when enabled)
- [ ] `report_runs` record created with FK to child artifacts
- [ ] `report_artifacts` contains 4 records (manifest, 2 summaries, telemetry)
- [ ] `test_metrics` record extracted with correct values
- [ ] DB failures logged without aborting script
- [ ] Coverage metrics match file-based summary

#### Idempotency Checks
- [ ] Rerunning with same timestamp updates existing DB record
- [ ] UNIQUE constraint on (viewer_slug, topic, run_timestamp) prevents duplicates
- [ ] File overwrites work as expected

### Test Commands

```bash
# Current behavior (DB disabled)
python .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py \
    --repo-root /workspaces/repo_studios \
    --log-level DEBUG

# Enable DB dual-writes
export REPO_STUDIOS_DB_ENABLED=true
python .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py \
    --repo-root /workspaces/repo_studios \
    --log-level DEBUG

# Verify no file changes
diff -r <old_reports_dir> <new_reports_dir>

# Check for DB markers in logs
grep "DB_INTEGRATION_MARKER" <log_file>
```

---

## Migration Checklist

### DB_INTEGRATION_MARKER: Integration Status

- [ ] Database schema documented in this file
- [ ] `database_integration` module imported
- [ ] Storage instance created via `create_storage()`
- [ ] Manifest write converted to `storage.write_manifest()`
- [ ] Summary writes converted to `storage.write_summary()`
- [ ] Telemetry write converted to `storage.write_telemetry()`
- [ ] DB writes tested with `enabled=True`
- [ ] DB failures tested (graceful degradation)
- [ ] Logging includes DB_INTEGRATION_MARKER tags
- [ ] Tests updated to verify dual-write behavior
- [ ] Documentation reviewed by team
- [ ] Ready for main repo integration

### Future Work

- [ ] Remove file writes once agents trained (target: Q2 2026)
- [ ] Add GraphQL endpoint for agent queries
- [ ] Implement TimescaleDB continuous aggregates for daily/weekly rollups
- [ ] Create materialized view for "test health dashboard"
- [ ] Add webhook notifications for coverage regressions

---

## Notes & Caveats

### Known Limitations
- Coverage metrics depend on pytest-cov being installed and configured
- Churn analysis requires git history (fails gracefully in bare repos)
- Large log directories (>1000 files) may slow down aggregation step
- DB writes are fire-and-forget; no retry logic in v1.0

### Dependencies
Scripts that consume this output:
- None directly (orchestrator is typically a pipeline endpoint)
- Dashboard viewers read from DB for trend visualization

Scripts this depends on (upstream):
- All producer, consumer, aggregator, summarizer scripts in the pipeline
- Git binary for churn analysis
- pytest for test execution

### Performance Considerations
- Full pipeline takes 30-60 seconds on typical repos
- DB writes add <200ms overhead per artifact
- JSONB indexes needed for efficient churn_stats queries
- Consider partitioning test_metrics by run_timestamp for large datasets

### Agent Query Examples

1. **Query:** "Is test coverage improving over time?"
   - **Tables:** `report_runs`, `test_metrics`
   - **Key fields:** `run_timestamp`, `coverage_pct`
   - **SQL:** See Q1 in Time-Series Considerations

2. **Query:** "Which files have high complexity AND high churn?"
   - **Tables:** `test_metrics`
   - **Key fields:** `churn_stats` (JSONB)
   - **SQL:** See Q3 in Time-Series Considerations

3. **Query:** "Show me all runs where tests failed"
   - **Tables:** `report_runs`, `test_metrics`
   - **Key fields:** `status`, `failed_tests`
   - **SQL:**
     ```sql
     SELECT rr.run_timestamp, rr.git_sha, tm.failed_tests
     FROM report_runs rr
     JOIN test_metrics tm ON rr.id = tm.run_id
     WHERE rr.topic = 'test_execution_telemetry'
       AND tm.failed_tests > 0
     ORDER BY rr.run_timestamp DESC;
     ```

---

## Contact & Ownership

**Primary Maintainer:** Repo Studios Team  
**Last Reviewed:** 2025-12-11  
**Next Review:** 2026-01-11  

---

**DB_INTEGRATION_MARKER Legend:**
- `DB_INTEGRATION_MARKER:` - Denotes integration points for future DB wiring
- Search codebase: `grep -r "DB_INTEGRATION_MARKER" .repo_studios/` 
- Generate status report: `python .repo_studios/scripts/utilities/list_db_markers.py`
