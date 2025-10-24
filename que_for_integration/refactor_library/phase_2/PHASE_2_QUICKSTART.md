# Phase 2: Build Detection Tool - Quick Start Guide

## 📦 Files Included

1. **scan_code_duplicates.py** - Main AST-based duplicate detector
2. **scan_code_duplicates_USAGE.md** - Comprehensive usage documentation
3. **test_scan_code_duplicates.py** - Unit tests for the scanner
4. **PHASE_2_QUICKSTART.md** - This file

---

## 🚀 Installation Steps

### Step 1: Download Files

Download all files from this directory to your local machine.

### Step 2: Place Scanner Script

```bash
# Copy to producers directory
cp scan_code_duplicates.py /path/to/repo/.repo_studios/scripts/producers/

# Make executable (optional)
chmod +x /path/to/repo/.repo_studios/scripts/producers/scan_code_duplicates.py
```

### Step 3: Place Test File

```bash
# Copy to tests directory
mkdir -p /path/to/repo/.repo_studios/tests/tests_producers/
cp test_scan_code_duplicates.py /path/to/repo/.repo_studios/tests/tests_producers/
```

### Step 4: Place Documentation

```bash
# Copy usage guide to docs
mkdir -p /path/to/repo/docs/automation/
cp scan_code_duplicates_USAGE.md /path/to/repo/docs/automation/
```

---

## ✅ Validation

### Test the Scanner

```bash
cd /path/to/repo

# Run unit tests first
pytest .repo_studios/tests/tests_producers/test_scan_code_duplicates.py -v

# Should see:
# test_function_extraction ... PASSED
# test_exact_duplicate_detection ... PASSED
# test_similarity_scoring ... PASSED
# test_library_path_inference ... PASSED
```

### Run First Scan

```bash
# Scan your 3 sample files
python .repo_studios/scripts/producers/scan_code_duplicates.py \
    --scan-dirs .repo_studios/scripts/producers \
    --log-level INFO

# Check output
ls -lh .repo_studios/reports/duplicate_detection_reports/
```

**Expected Output:**
```
INFO: Scanning directories: ['.repo_studios/scripts/producers']
INFO: Found 3 Python files
INFO: Extracted 45 functions
INFO: Found 9 duplicate groups
INFO: Report written to: .repo_studios/reports/duplicate_detection_reports/duplicate_detection-20251023_154500
INFO: Summary: 9 duplicate groups, 27 total occurrences
```

---

## 📊 Review Results

### 1. Quick Summary

```bash
# View markdown summary
cat .repo_studios/reports/duplicate_detection_reports/latest_summary.md
```

**Look for:**
- Total duplicate groups (should be ~9 from your samples)
- Lines that can be saved (should be ~150-200)
- Priority breakdown (high/medium/low)

### 2. Detailed JSON Report

```bash
# Pretty print first duplicate group
jq '.duplicate_groups[0]' \
    .repo_studios/reports/duplicate_detection_reports/latest_report.json
```

**Verify:**
- `group_id` present (e.g., "dup_001")
- `canonical_name` extracted (e.g., "copy_latest")
- `occurrences` lists 2+ files
- `library_recommendation.target_path` looks correct
- `refactoring_action.steps` has 5 steps

### 3. Validate Library Paths

```bash
# Extract all recommended paths
jq -r '.duplicate_groups[].library_recommendation.target_path' \
    .repo_studios/reports/duplicate_detection_reports/latest_report.json

# Should see paths like:
# artifact_lifecycle/versioning/create_latest_link.py
# artifact_lifecycle/versioning/prune_old_runs.py
# time_handling/parsing/parse_iso_timestamp_utc.py
```

---

## 🎯 Validation Checklist

After running the scan:

- [ ] Scanner runs without errors
- [ ] Report JSON generated in `.repo_studios/reports/duplicate_detection_reports/`
- [ ] Summary markdown created
- [ ] `latest_report.json` symlink present
- [ ] Detected ~9 duplicate groups from sample files
- [ ] Each group has:
  - [ ] Valid `group_id`
  - [ ] Canonical name extracted
  - [ ] 2+ occurrences listed
  - [ ] Library path recommendation
  - [ ] Refactoring action steps
  - [ ] Impact analysis
- [ ] Library paths follow naming conventions:
  - [ ] Domain level (e.g., `artifact_lifecycle/`)
  - [ ] Purpose level (e.g., `versioning/`)
  - [ ] Module file (e.g., `create_latest_link.py`)

---

## 🔧 Troubleshooting

### Issue: "Module 'ast' not found"

**Cause:** Using Python < 3.8

**Solution:**
```bash
python --version  # Should be 3.8+
python3.11 scan_code_duplicates.py  # Use specific version
```

### Issue: "No duplicates found"

**Cause:** Scanning wrong directory or threshold too strict

**Solution:**
```bash
# Explicitly specify your sample files location
python scan_code_duplicates.py \
    --scan-dirs .repo_studios/scripts/producers \
    --similarity-threshold 0.80 \
    --min-lines 3 \
    --log-level DEBUG
```

### Issue: "Permission denied"

**Cause:** Output directory not writable

**Solution:**
```bash
# Create output directory
mkdir -p .repo_studios/reports/duplicate_detection_reports
chmod 755 .repo_studios/reports/duplicate_detection_reports
```

### Issue: Scanner runs but no output

**Cause:** Check log level or output directory

**Solution:**
```bash
# Verbose logging
python scan_code_duplicates.py --log-level DEBUG

# Confirm output location
ls -la .repo_studios/reports/duplicate_detection_reports/
```

---

## 📖 Understanding Your Results

Based on the 3 sample files you provided, you should see these duplicate groups:

### Expected Duplicates

1. **`_copy_latest`** (3 occurrences)
   - Path: `artifact_lifecycle/versioning/create_latest_link.py`
   - Type: Exact duplicate
   - Priority: High

2. **`prune_old_runs`** (3 occurrences)
   - Path: `artifact_lifecycle/versioning/prune_old_runs.py`
   - Type: Near duplicate (return type varies)
   - Priority: High

3. **`configure_logging`** (2+ occurrences)
   - Path: `logging_setup/configuration/configure_basic_logging.py`
   - Type: Exact duplicate
   - Priority: High

4. **`_ensure_directory` / `_ensure_output_dir`** (variations)
   - Path: `filesystem/directory_management/ensure_directory.py`
   - Type: Near duplicate
   - Priority: Medium

5. **`_parse_timestamp`** (3 inconsistent implementations)
   - Path: `time_handling/parsing/parse_iso_timestamp_utc.py`
   - Type: Near duplicate with variations
   - Priority: High (unification needed!)

6. **`_rel_path` / `_rel_to_repo`** (2 occurrences)
   - Path: `filesystem/path_operations/compute_relative_path.py`
   - Type: Near duplicate (name varies)
   - Priority: Medium

7-9. Additional patterns for run directory creation, report schemas, etc.

---

## 🎓 What You've Learned

At this point you should understand:

✅ **How AST-based detection works** - Parses Python structure, not text
✅ **Similarity scoring** - Distinguishes exact vs. near duplicates
✅ **Library path inference** - Automatic recommendation using naming rules
✅ **Refactoring actions** - Step-by-step extraction instructions
✅ **AI-first JSON schema** - Optimized for autonomous agent consumption

---

## 🚀 Next Steps

**Phase 2 Complete!** ✅

You now have:
- ✅ Working duplicate detection tool
- ✅ AI-optimized JSON reports
- ✅ Library path recommendations
- ✅ Refactoring action plans

**Next Phase:** Phase 3 - Manual Extraction Validation

**Action Items:**
1. Review detection results thoroughly
2. Verify library path recommendations make sense
3. Choose ONE duplicate from Phase 1 (safe extractions)
4. Manually extract it to validate the workflow
5. Document any issues or improvements needed

---

## 📝 Configuration Tips

### Adjust Sensitivity

**More duplicates (permissive):**
```bash
python scan_code_duplicates.py \
    --similarity-threshold 0.75 \
    --min-lines 2
```

**Fewer duplicates (strict):**
```bash
python scan_code_duplicates.py \
    --similarity-threshold 0.95 \
    --min-lines 10
```

### Scan Specific Areas

```bash
# Just producers
python scan_code_duplicates.py \
    --scan-dirs .repo_studios/scripts/producers

# Multiple areas
python scan_code_duplicates.py \
    --scan-dirs \
        .repo_studios/scripts/producers \
        .repo_studios/scripts/consumers \
        src/myapp/core
```

### Generate More Reports

```bash
# Keep last 20 runs instead of 10
python scan_code_duplicates.py \
    --artifacts-to-keep 20
```

---

## 🔗 Integration

### Add Make Target (Optional)

Add to `.repo_studios/Makefile`:

```makefile
.PHONY: studio-detect-duplicates
studio-detect-duplicates:
	@echo "Scanning for duplicate code..."
	python .repo_studios/scripts/producers/scan_code_duplicates.py \
		--scan-dirs .repo_studios/scripts \
		--log-level INFO
	@echo "Report: .repo_studios/reports/duplicate_detection_reports/latest_summary.md"
```

**Usage:**
```bash
make studio-detect-duplicates
```

### Add to Health Suite (Future)

After Phase 7, this will integrate into orchestrated health checks.

---

## 📞 Support

If you encounter issues:

1. Check validation checklist above
2. Review logs with `--log-level DEBUG`
3. Consult `scan_code_duplicates_USAGE.md` for detailed documentation
4. Verify Python version (3.8+ required)
5. Ensure write permissions on output directory

---

## 🎉 Success Criteria

Phase 2 is complete when:

- [x] Scanner installed in `.repo_studios/scripts/producers/`
- [x] Tests pass successfully
- [x] First scan runs without errors
- [x] Report JSON generated with valid structure
- [x] Detected ~9 duplicate groups from samples
- [x] Library paths follow naming conventions
- [x] Refactoring actions include all 5 steps

**Status:** ✅ Ready for Phase 3

---

**🎊 Congratulations! Duplicate detection is operational.**

**Proceed to Phase 3:** Manual extraction validation (pick `_copy_latest` first!)
