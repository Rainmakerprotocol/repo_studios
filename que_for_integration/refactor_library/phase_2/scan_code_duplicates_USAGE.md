# Duplicate Scanner Integration Notes# Duplicate Scanner Integration Notes# scan_code_duplicates.py - Usage Guide



The legacy `scan_code_duplicates.py` drop-in script has been retired. The

supported, repo-managed tooling now lives under

`.repo_studios/scripts/library_integration/duplicates/scan_duplicates.py`.The legacy `scan_code_duplicates.py` reference script has been superseded by the## Overview



## Quick Referencerepo-managed tooling located at:



- Invoke via PowerShell (from repo root):The `scan_code_duplicates.py` tool uses Python AST (Abstract Syntax Tree) analysis to detect exact and near-duplicate functions across your codebase. It generates AI-optimized JSON reports with library extraction recommendations and automated refactoring instructions.



  ```powershell```

  python .repo_studios/scripts/library_integration/duplicates/scan_duplicates.py --help

  ```.repo_studios/scripts/library_integration/duplicates/scan_duplicates.py---



- Timestamped reports live under```

  `.repo_studios/library_integration/reports/<timestamp>-duplicate_scan/`.

- A rolling copy is written to## Quick Start

  `.repo_studios/library_integration/reports/code_duplicate_report/latest/`.

- Each run emits `duplicate_matrix.json` (with metadata and merged producersKey changes:

  findings) plus `duplicate_matrix_summary.md` (human-readable recap).

### Basic Scan

## Documentation

- CLI entrypoint now lives within the Repo Studios source tree. Invoke it via

See the protocol references inside `.repo_studios/library_integration/` for

full workflow details:  `python .repo_studios/scripts/library_integration/duplicates/scan_duplicates.py --help`.```bash



1. `README.md` – end-to-end library integration workflow and reporting cadence.- Reports are written beneath `.repo_studios/library_integration/reports/` with# Scan default location (.repo_studios/scripts/)

2. `docs/duplicate_detection_schema_alignment.md` – field mapping between

   producers analysis, scanner output, and downstream dashboards.  both timestamped folders (e.g., `20251024-173000-duplicate_scan/`) and apython scan_code_duplicates.py

3. `checklists/library_integration_checklist.md` – phase-by-phase plan tracking

   current implementation status.  rolling `code_duplicate_report/latest/` reference copy.


- Producers analysis is merged automatically, producing a consolidated# Scan specific directories

  `duplicate_matrix.json` and `duplicate_matrix_summary.md` per run.python scan_code_duplicates.py \

    --scan-dirs .repo_studios/scripts/producers \

Refer to `.repo_studios/library_integration/README.md` and                .repo_studios/scripts/consumers

`.repo_studios/library_integration/docs/duplicate_detection_schema_alignment.md`

for the up-to-date workflow, schema expectations, and integration steps.# Specify repo root

python scan_code_duplicates.py --repo-root /path/to/repo
```

### Output Location

Default: `.repo_studios/reports/duplicate_detection_reports/`

```
duplicate_detection_reports/
├── duplicate_detection-20251023_153000/
│   ├── report.json          # Complete AI-readable report
│   └── summary.md           # Human-readable summary
├── latest_report.json       # Symlink to most recent
└── latest_summary.md        # Symlink to most recent
```

---

## Command-Line Options

### Required
None - all options have sensible defaults

### Optional

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | Path | `.` | Repository root directory |
| `--scan-dirs` | Path[] | `.repo_studios/scripts` | Directories to scan |
| `--output-dir` | Path | `.repo_studios/reports/duplicate_detection_reports` | Output location |
| `--similarity-threshold` | float | `0.85` | AST similarity threshold (0-1) |
| `--min-lines` | int | `3` | Minimum function lines to consider |
| `--artifacts-to-keep` | int | `10` | Number of historical runs to retain |
| `--log-level` | str | `INFO` | Logging verbosity |

---

## Examples

### Example 1: Scan Your Sample Files

```bash
# From repo root
python .repo_studios/scripts/producers/scan_code_duplicates.py \
    --scan-dirs .repo_studios/scripts/producers \
    --min-lines 5 \
    --log-level DEBUG
```

**Expected Output:**
```
INFO: Scanning directories: ['.repo_studios/scripts/producers']
INFO: Found 15 Python files
INFO: Extracted 127 functions
INFO: Found 9 duplicate groups
INFO: Report written to: .repo_studios/reports/duplicate_detection_reports/duplicate_detection-20251023_153045
INFO: Summary: 9 duplicate groups, 27 total occurrences
```

### Example 2: High-Sensitivity Scan

Detect even slight similarities:

```bash
python scan_code_duplicates.py \
    --similarity-threshold 0.75 \
    --min-lines 2
```

### Example 3: Strict Exact-Match Only

Only detect 100% identical duplicates:

```bash
python scan_code_duplicates.py \
    --similarity-threshold 1.0 \
    --min-lines 5
```

### Example 4: Scan Multiple Locations

```bash
python scan_code_duplicates.py \
    --scan-dirs \
        .repo_studios/scripts/producers \
        .repo_studios/scripts/consumers \
        .repo_studios/scripts/aggregators \
        src/jarvis/core
```

---

## Understanding the Report

### JSON Structure

```json
{
  "schema_version": "1.0.0",
  "generated_utc": "2025-10-23T15:30:00Z",
  "repo_root": "/path/to/repo",
  
  "duplicate_groups": [
    {
      "group_id": "dup_001",
      "canonical_name": "copy_latest",
      "similarity_score": 1.0,
      "duplicate_type": "exact_duplicate",
      
      "occurrences": [
        {
          "file": "scripts/producers/generate_standards_index.py",
          "line_start": 426,
          "line_end": 432,
          "function_name": "_copy_latest"
        }
      ],
      
      "library_recommendation": {
        "target_path": "artifact_lifecycle/versioning/create_latest_link.py",
        "import_statement": "from .repo_studios.library... import create_latest_link"
      },
      
      "refactoring_action": {
        "strategy": "extract_to_library_and_replace",
        "priority": "high",
        "steps": [...]
      }
    }
  ],
  
  "summary": {
    "total_duplicate_groups": 9,
    "total_occurrences": 27,
    "potential_lines_saved": 350
  }
}
```

### Key Fields Explained

**`duplicate_groups`** - Array of detected duplicate clusters
- **`group_id`** - Unique identifier (e.g., "dup_001")
- **`canonical_name`** - Suggested function name for library
- **`similarity_score`** - 0.0 to 1.0 (1.0 = exact match)
- **`duplicate_type`** - "exact_duplicate" or "near_duplicate_with_variations"

**`occurrences`** - Where duplicates appear
- **`file`** - Relative path from repo root
- **`line_start/line_end`** - Line numbers
- **`function_name`** - Original function name
- **`code_hash`** - Hash for exact matching

**`library_recommendation`** - Where to extract
- **`target_path`** - Recommended library location
- **`import_statement`** - How to import after extraction
- **`confidence`** - Recommendation confidence (0-1)

**`refactoring_action`** - How to refactor
- **`strategy`** - Extraction approach
- **`priority`** - high/medium/low
- **`steps`** - Ordered refactoring instructions

**`impact_analysis`** - Cost/benefit
- **`lines_saved`** - Code reduction
- **`files_affected`** - Number of files to modify
- **`risk_level`** - low/medium/high

---

## Interpreting Results

### Duplicate Types

**Exact Duplicates (similarity = 1.0)**
- Identical code, possibly different names
- **Safe to extract** - no unification needed
- **Priority:** High (easy wins)

**Near Duplicates (0.85 ≤ similarity < 1.0)**
- Similar structure with minor variations
- **Requires unification** - reconcile differences
- **Priority:** Medium (more effort)

### Priority Levels

**High Priority**
- 3+ occurrences
- Exact duplicates
- Low risk
- High line savings

**Medium Priority**
- 2 occurrences
- Near duplicates
- Medium risk
- Moderate savings

**Low Priority**
- Complex variations
- High risk
- Low savings

### Execution Phases

Report groups duplicates into phases:

**Phase 1: Safe Extractions**
- Exact duplicates
- Zero variations
- Pure functions
- **Start here!**

**Phase 2: Unification Required**
- Near duplicates
- Need reconciliation
- Test thoroughly

**Phase 3: Complex Patterns**
- Structural duplicates
- Higher risk
- Advanced refactoring

---

## AI Agent Instructions

The report includes `ai_agent_instructions` for autonomous refactoring:

```json
"ai_agent_instructions": {
  "workflow": "autonomous_refactoring_pipeline",
  "phases": [
    {
      "phase": 1,
      "name": "inspect_library",
      "instruction": "Check if target path exists before creating"
    },
    {
      "phase": 2,
      "name": "create_library_function",
      "instruction": "Extract from best source occurrence"
    },
    ...
  ]
}
```

These instructions guide Phase 4 (automated refactoring) of the implementation plan.

---

## Integration with Workflow

### Manual Review (Phase 3)

```bash
# 1. Run scan
python scan_code_duplicates.py

# 2. Review summary
cat .repo_studios/reports/duplicate_detection_reports/latest_summary.md

# 3. Inspect JSON
jq '.duplicate_groups[0]' .repo_studios/reports/duplicate_detection_reports/latest_report.json

# 4. Manual extraction (validation)
# Extract one dup_001 to library
# Write tests
# Replace occurrences
# Validate
```

### Automated Refactoring (Phase 4)

```bash
# Future: Will be automated
python refactor_from_report.py \
    --report latest_report.json \
    --phase 1
```

---

## Troubleshooting

### "No duplicates found"

**Possible causes:**
- `--min-lines` too high - try lower value
- `--similarity-threshold` too strict - try 0.80
- Scanning wrong directories - check `--scan-dirs`
- No actual duplicates (lucky you!)

**Solution:**
```bash
# More permissive scan
python scan_code_duplicates.py \
    --similarity-threshold 0.75 \
    --min-lines 2 \
    --log-level DEBUG
```

### "SyntaxError in file X"

**Cause:** File has invalid Python syntax

**Solution:** 
- Tool skips invalid files automatically
- Check file for syntax errors
- Review log warnings

### "Too many duplicates"

**Cause:** Threshold too permissive or too many actual duplicates

**Solution:**
```bash
# More strict
python scan_code_duplicates.py \
    --similarity-threshold 0.95 \
    --min-lines 10
```

---

## Performance Notes

**Scan Speed:**
- ~100-200 files/second
- AST parsing is CPU-bound
- Large files take longer

**Memory Usage:**
- ~1MB per 100 functions
- Scales linearly with codebase size

**Optimization Tips:**
- Use `--scan-dirs` to limit scope
- Increase `--min-lines` to skip trivial functions
- Run on specific modules first

---

## Next Steps

After running the scan:

1. **Review** `latest_summary.md` for overview
2. **Inspect** Phase 1 groups in `latest_report.json`
3. **Validate** by manually extracting one duplicate (Phase 3)
4. **Automate** with `refactor_from_report.py` (Phase 4)
5. **Integrate** into CI pipeline (warning-only mode)

---

## Advanced Usage

### Custom Ignore Patterns

Edit the script to add ignore patterns:

```python
# In scan_python_files function
ignore_patterns = [
    "test_*",           # Test files
    "__pycache__",      # Python cache
    ".git",             # Git directory
    "venv",             # Virtual environments
    "migrations",       # Django migrations (custom)
]
```

### Export to CSV

```bash
# Extract occurrences to CSV
jq -r '.duplicate_groups[] | .occurrences[] | [.file, .line_start, .function_name] | @csv' \
    latest_report.json > duplicates.csv
```

### Filter by Priority

```bash
# Show only high-priority groups
jq '.duplicate_groups[] | select(.refactoring_action.priority == "high")' \
    latest_report.json
```

---

## FAQs

**Q: Does this detect duplicates across different projects?**  
A: No, scans single repo only. Run separately for each project.

**Q: Can it detect duplicates in non-Python files?**  
A: No, Python AST analysis only. Use text-based tools for other languages.

**Q: Will it detect similar logic with different implementations?**  
A: Partially - catches structural similarity but not semantic equivalence.

**Q: How accurate are library path recommendations?**  
A: ~85% accuracy based on naming conventions. Always review manually.

**Q: Can I customize the recommendation logic?**  
A: Yes! Edit `infer_library_path()` function to improve domain/purpose mapping.

---

## See Also

- **Phase 1:** Library structure setup
- **Phase 3:** Manual extraction validation
- **Phase 4:** Automated refactoring (coming soon)
- **naming_conventions.md:** Library organization rules
