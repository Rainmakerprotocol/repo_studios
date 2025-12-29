# Database Integration Documentation Template

<!-- markdownlint-disable MD013 MD036 -->
<!-- Template document with markers and inline examples; line length and emphasis-as-heading exempt -->

**DB_INTEGRATION_MARKER: Use this template for each script's per-tier documentation**

This template captures the database schema requirements, output mappings,
and integration notes for scripts undergoing refactoring.
Each script should have a corresponding documentation file following this structure.

---

## Script: `[script_name].py`

**Tier:** [producer | consumer | aggregator | orchestrator | summarizer | utility]
**Viewer:** [healthview | commandview | rawview | jarvis | vscode]
**Topic:** [topic slug from REPORT_NAMING_STANDARDS.md]
**Last Updated:** YYYY-MM-DD
**Schema Version:** [semantic version]

---

## Purpose & Scope

### What This Script Does

[1-3 sentences describing the script's role in the pipeline]

### Inputs

- **File-based:** [List expected input files/directories]
- **Configuration:** [CLI args, env vars, config files]
- **Dependencies:** [Other scripts that must run first]

### Outputs (Current)

- **File artifacts:** [List all JSON/MD files written, with paths]
- **Logs:** [Where logs are written]
- **Side effects:** [Any mutations, deletions, external calls]

---

## Database Integration Plan

### DB_INTEGRATION_MARKER: Schema Requirements

#### Primary Table(s)

List the main database table(s) this script writes to:

```sql
-- Example: report_runs table for orchestrators
CREATE TABLE report_runs (
    id BIGSERIAL PRIMARY KEY,
    viewer_slug VARCHAR(50) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    run_timestamp TIMESTAMPTZ NOT NULL,
    git_sha VARCHAR(40),
    status VARCHAR(20),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    inputs JSONB,
    catalog JSONB
);

```

#### Secondary/Related Tables

List any additional tables that receive data from this script:

```sql
-- Example: report_artifacts for telemetry files
CREATE TABLE report_artifacts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id),
    artifact_role VARCHAR(50),
    content_json JSONB
);

```

### Data Mapping

Map current file outputs to database writes:

| Current File | Artifact Role | Target Table | Key Fields | Notes |
|--------------|---------------|--------------|------------|-------|
| `manifest.json` | manifest | `report_runs` | `viewer_slug`, `topic`, `run_timestamp`, `inputs`, `catalog` | Main record, returns run_id |
| `summary.json` | summary | `report_artifacts` | `run_id`, `artifact_role='summary'`, `content_json` | Full summary payload |
| `telemetry.json` | telemetry | `report_artifacts` + `test_metrics` | Artifact storage + extracted metrics | Dual writes for time-series |
| `[custom].json` | [role] | [table] | [fields] | [notes] |

### Extracted Metrics

If this script produces time-series or queryable metrics, document the extraction logic:

```python
# Example: Extract test metrics from telemetry

{
    "coverage_pct": data["metrics"]["coverage_status"],
    "total_tests": data["components"]["coverage"]["summary"]["total_functions"],
    "failed_tests": data["failures"]["detected"],
    # ... more fields
}

```

**Target Table:** `test_metrics`

**Extraction Logic:**

- `coverage_pct` ← `data['metrics']['coverage_status']`
- `total_tests` ← `data['components']['coverage']['summary']['total_functions']`
- [additional mappings]

### Time-Series Considerations

**Is this a time-series report?** [Yes | No]

If Yes:

- **Retention Policy:** [How long to keep records in DB vs files]
- **Aggregation Windows:** [Daily, weekly, monthly rollups needed?]
- **Query Patterns:** [What queries will agents run against this data?]

**Example queries:**

```sql
-- Show test coverage trends over last 30 days
SELECT DATE_TRUNC('day', run_timestamp) as date,
       AVG(tm.coverage_pct) as avg_coverage
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE rr.topic = 'test_execution_telemetry'
  AND rr.run_timestamp > NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date;

```

---

## Integration Points

### DB_INTEGRATION_MARKER: Code Locations

Document where DB writes are inserted in the script:

1. **Import section:**

   ```python
   # Line ~XX
   from libraries.database_integration import create_storage
   ```

1. **Storage initialization:**

   ```python
   # Line ~XXX in main() or run()
   storage = create_storage(
       output_dir=paths.reports_root,
       viewer_slug="healthview",
       topic="test_execution_telemetry",
   )
   ```

1. **Write operations:**

   ```python
   # Line ~XXX - write manifest
   storage.write_manifest(manifest_data)

   # Line ~XXX - write telemetry
   storage.write_telemetry(telemetry_data)

   # [Additional writes...]
   ```

### Configuration Dependencies

**Environment Variables:**

- `REPO_STUDIOS_DB_URL` - PostgreSQL connection string
- `REPO_STUDIOS_DB_ENABLED` - Explicit enable/disable flag

**Config Files:**

- `.repo_studios/db_config.json` - Local air-gapped DB config

**Example config:**

```json
{
    "host": "localhost",
    "port": 5432,
    "database": "repo_studios",
    "user": "repo_agent",
    "password": "[secure]",
    "enabled": true
}

```

---

## Validation & Testing

### DB_INTEGRATION_MARKER: Test Strategy

#### File Output Validation

- [ ] File artifacts written to expected paths
- [ ] JSON schema validation passes
- [ ] Markdown formatting follows standards
- [ ] Timestamps properly formatted

#### DB Write Validation (when enabled)

- [ ] `report_runs` record created with correct foreign keys
- [ ] All artifact writes succeed without exceptions
- [ ] Extracted metrics match source data
- [ ] DB failures logged but don't abort script

#### Idempotency Checks

- [ ] Rerunning script with same timestamp doesn't corrupt data
- [ ] DB UNIQUE constraints prevent duplicate records
- [ ] File overwrites are safe

### Test Commands

```bash
# Run with DB disabled (current behavior)

python script.py --repo-root . --log-level DEBUG

# Run with DB enabled (dual-write mode)

REPO_STUDIOS_DB_ENABLED=true python script.py --repo-root . --log-level DEBUG

# Verify no file behavior changes

diff <old_output_dir> <new_output_dir>

```

---

## Migration Checklist

### DB_INTEGRATION_MARKER: Integration Status

- [ ] Database schema documented in this file
- [ ] `database_integration` module imported
- [ ] Storage instance created via `create_storage()`
- [ ] All file writes converted to `storage.write_*()` calls
- [ ] DB writes tested with `enabled=True`
- [ ] DB failures tested (graceful degradation)
- [ ] Logging includes DB_INTEGRATION_MARKER tags
- [ ] Tests updated to cover dual-write behavior
- [ ] Documentation reviewed by team
- [ ] Ready for main repo integration

### Future Work

- [ ] Remove file writes once agents trained (target date: ________)
- [ ] Add DB query helpers for common agent requests
- [ ] Implement connection pooling for high-volume scripts
- [ ] Add TimescaleDB hypertables for time-series data
- [ ] Create materialized views for common queries

---

## Notes & Caveats

### Known Limitations

[List any constraints, edge cases, or gotchas]

### Dependencies

[List scripts that depend on this one's output]

### Performance Considerations

[Note any scalability concerns, large datasets, etc.]

### Agent Query Examples

Document the types of questions AI agents should be able to answer using this data:

1. **Query:** "Show test coverage trends for the last month"
   - **Tables:** `report_runs`, `test_metrics`
   - **Key fields:** `run_timestamp`, `coverage_pct`

1. **Query:** "Which tests are failing most frequently?"
   - **Tables:** `test_metrics`, `report_artifacts`
   - **Key fields:** `failed_tests`, `content_json`

1. [Additional agent query patterns...]

---

## Contact & Ownership

**Primary Maintainer:** [Name/Team]
**Last Reviewed:** YYYY-MM-DD
**Next Review:** YYYY-MM-DD

---

**DB_INTEGRATION_MARKER Legend:**

- `DB_INTEGRATION_MARKER:` - Denotes integration points for future DB wiring
- Search codebase: `grep -r "DB_INTEGRATION_MARKER" .` to find all integration points
- Generate CSV: `python scripts/utilities/list_db_markers.py > db_integration_status.csv`
