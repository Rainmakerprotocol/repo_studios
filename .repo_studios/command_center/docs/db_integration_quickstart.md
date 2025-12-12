# Database Integration Quick Reference

**For: Developers refactoring Repo Studios scripts**  
**Version:** 1.0  
**Last Updated:** 2025-12-11

---

## TL;DR

1. Import: `from libraries.database_integration import create_storage`
2. Initialize: `storage = create_storage(output_dir, viewer_slug, topic)`
3. Replace: File writes → `storage.write_*(data)` 
4. Mark: Add `# DB_INTEGRATION_MARKER:` comments
5. Test: Run with DB disabled, then enabled

---

## Code Pattern

### Before (File-only)

```python
#!/usr/bin/env python3
"""My report script."""

import json
from pathlib import Path

def run(argv):
    output_dir = Path(".repo_studios/command_center/reports/healthview/my_topic/20251211-1430")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    manifest = {"viewer": "healthview", "topic": "my_topic", ...}
    summary = {"status": "ok", "metrics": {...}}
    
    # Write files
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
```

### After (Dual-write)

```python
#!/usr/bin/env python3
"""My report script."""

import json
from pathlib import Path

# DB_INTEGRATION_MARKER: Database integration for parallel writes
from libraries.database_integration import create_storage

def run(argv):
    # DB_INTEGRATION_MARKER: Create dual-write storage
    storage = create_storage(
        output_dir=Path(".repo_studios/command_center/reports"),
        viewer_slug="healthview",
        topic="my_topic",
    )
    
    # Generate data
    manifest = {"viewer": "healthview", "topic": "my_topic", ...}
    summary = {"status": "ok", "metrics": {...}}
    
    # DB_INTEGRATION_MARKER: Dual-write manifest and summary
    storage.write_manifest(manifest)
    storage.write_summary(summary, format="json")
```

---

## Available Methods

```python
storage.write_manifest(data: dict) -> None
    # Writes manifest.json equivalent
    # Target: report_runs table + report_artifacts

storage.write_summary(data: dict, format: str = "json") -> None
    # Writes summary.json or summary.md
    # Target: report_artifacts table
    # Format: "json" or "md"

storage.write_telemetry(data: dict) -> None
    # Writes telemetry.json + extracts metrics
    # Target: report_artifacts + test_metrics tables

storage.write_matrix(data: dict) -> None
    # Writes matrix.json + function inventory
    # Target: report_artifacts + functions + duplicate_groups tables

storage.write_metrics(data: dict) -> None
    # Writes metrics.json
    # Target: report_artifacts + test_metrics tables
```

---

## Configuration

### Option 1: Config File (Recommended for Air-Gapped)

```json
// .repo_studios/db_config.json
{
    "host": "localhost",
    "port": 5432,
    "database": "repo_studios",
    "user": "repo_agent",
    "password": "",
    "enabled": true
}
```

### Option 2: Environment Variable

```bash
export REPO_STUDIOS_DB_ENABLED="true"
export REPO_STUDIOS_DB_URL="postgresql://user:pass@localhost/repo_studios"
```

### Option 3: Explicit Override

```python
storage = create_storage(..., enable_db=True)  # Force enable
```

---

## Testing Checklist

```bash
# 1. Test with DB disabled (verify no changes)
python script.py --repo-root . --log-level DEBUG

# 2. Compare file outputs
diff -r <old_reports> <new_reports>

# 3. Test with DB enabled (verify no crashes)
REPO_STUDIOS_DB_ENABLED=true python script.py --repo-root . --log-level DEBUG

# 4. Check for DB markers in logs
grep "DB_INTEGRATION_MARKER" <log_file>

# 5. Track integration status
python .repo_studios/command_center/scripts/utilities/list_db_markers.py --format md
```

---

## Marker Convention

**Tag all integration points:**

```python
# DB_INTEGRATION_MARKER: [description]
```

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

---

## Per-Script Documentation

**Copy template:**

```bash
cp .repo_studios/command_center/docs/db_integration_template.md \
   .repo_studios/command_center/docs/db_integration_<script_name>.md
```

**Fill in sections:**
1. Purpose & Scope
2. Database Integration Plan (target tables)
3. Data Mapping (files → DB)
4. Extracted Metrics (if time-series)
5. Integration Points (line numbers)
6. Validation & Testing
7. Migration Checklist

**Reference example:**  
See `db_integration_test_execution_telemetry.md`

---

## Common Patterns

### Orchestrator (Time-Series)

```python
from libraries.database_integration import create_storage

storage = create_storage(
    output_dir=paths.reports_root,
    viewer_slug="healthview",
    topic="test_execution_telemetry",
)

storage.write_manifest(manifest)        # → report_runs
storage.write_summary(summary, "json")  # → report_artifacts
storage.write_telemetry(telemetry)      # → report_artifacts + test_metrics
```

### Producer (Inventory)

```python
storage = create_storage(
    output_dir=paths.index_dir.parent,
    viewer_slug="commandview",
    topic="function_inventory",
)

storage.write_manifest(inventory_metadata)
storage.write_matrix(function_inventory)  # → functions table
```

### Aggregator (Duplicates)

```python
storage = create_storage(
    output_dir=paths.reports_root,
    viewer_slug="commandview",
    topic="duplicate_scan",
)

storage.write_matrix(duplicate_matrix)  # → duplicate_groups table
storage.write_summary(summary, "md")
```

---

## Troubleshooting

### "Module not found: database_integration"

**Fix:** Ensure you're importing from the correct path:

```python
from libraries.database_integration import create_storage
# NOT: from database_integration import ...
```

### "DB writes failing silently"

**Check:**
1. Is `REPO_STUDIOS_DB_ENABLED=true` set?
2. Does `.repo_studios/db_config.json` have `"enabled": true`?
3. Are DB errors logged? (search for "DB_INTEGRATION_MARKER" in logs)

**Debug:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Should see: "DB_INTEGRATION_MARKER: Database writes ENABLED"
```

### "File outputs changed after integration"

**This is a bug!** File behavior should be identical.

**Debug:**
```bash
# Compare old vs new outputs
diff -r <old_dir> <new_dir>

# Verify storage always writes files first
# DB writes are secondary and shouldn't affect files
```

---

## Database Schema Reference

### Key Tables

```sql
-- Main runs (orchestrators)
report_runs (id, viewer_slug, topic, run_timestamp, git_sha, status, inputs, catalog)

-- All artifacts
report_artifacts (id, run_id, artifact_role, artifact_type, content_json, content_text)

-- Time-series metrics
test_metrics (id, run_id, metric_timestamp, coverage_pct, failed_tests, ...)

-- Function inventory
functions (id, run_id, module_id, function_name, relative_path, git_churn, ...)

-- Duplicate tracking
duplicate_groups (id, run_id, group_identifier, duplicate_count, instances)
```

**Full schema:** See `.repo_studios/db_schema.sql`

---

## Agent Query Examples

```sql
-- Coverage trends
SELECT date, avg_coverage FROM test_coverage_trends
WHERE date > NOW() - INTERVAL '30 days' ORDER BY date;

-- Recent failures
SELECT run_timestamp, failed_tests FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE tm.failed_tests > 0 ORDER BY run_timestamp DESC LIMIT 10;

-- Top duplicates
SELECT function_name, max_count FROM top_duplicates
ORDER BY max_count DESC LIMIT 20;

-- High-risk files
SELECT relative_path, avg_complexity, avg_churn FROM high_risk_files
ORDER BY (avg_complexity * avg_churn) DESC LIMIT 50;
```

---

## Resources

| Resource | Path |
|----------|------|
| Integration Library | `.repo_studios/command_center/scripts/libraries/database_integration.py` |
| Template | `.repo_studios/command_center/docs/db_integration_template.md` |
| Example Docs | `.repo_studios/command_center/docs/db_integration_test_execution_telemetry.md` |
| Full Guide | `.repo_studios/command_center/docs/db_integration_guide.md` |
| DB Schema | `.repo_studios/db_schema.sql` |
| Marker Tracker | `.repo_studios/command_center/scripts/utilities/list_db_markers.py` |

---

## Integration Status

```bash
# Generate current status
python .repo_studios/command_center/scripts/utilities/list_db_markers.py \
    --format csv \
    --output db_status.csv

# View status
cat db_status.csv
```

---

## Need Help?

1. **Read the full guide:** `.repo_studios/command_center/docs/db_integration_guide.md`
2. **Review example:** `db_integration_test_execution_telemetry.md`
3. **Check schema:** `.repo_studios/db_schema.sql`
4. **Track progress:** `python ...list_db_markers.py --format md`

---

**Last Updated:** 2025-12-11  
**Version:** 1.0  
**Maintained By:** Repo Studios Team
