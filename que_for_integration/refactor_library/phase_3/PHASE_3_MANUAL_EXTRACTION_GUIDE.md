# Phase 3: Manual Extraction Validation - Step-by-Step Guide

## Overview

Phase 3 validates the extraction workflow by **manually** extracting ONE duplicate function from detection to library integration. This ensures the process works before automating it in Phase 4.

**Target:** `_copy_latest` → `create_latest_link`  
**Why this one:** Exact duplicate, no variations, 3 occurrences, low risk

**Time estimate:** 45-60 minutes

---

## Prerequisites

✅ Phase 1 complete - Library structure created  
✅ Phase 2 complete - Detection tool running  
✅ Detection report generated with ~9 duplicate groups  
✅ Identified `dup_001` (copy_latest) in report

---

## Step-by-Step Process

### Step 1: Review Detection Report (5 min)

**Action:** Locate and review the duplicate group for `_copy_latest`

```bash
# View the group details
jq '.duplicate_groups[] | select(.group_id == "dup_001")' \
    .repo_studios/reports/duplicate_detection_reports/latest_report.json
```

**Verify:**
- [ ] Group ID is `dup_001`
- [ ] Canonical name is something like `copy_latest` or `create_latest_link`
- [ ] Has 3 occurrences (your sample files)
- [ ] Similarity score is 1.0 (exact duplicate)
- [ ] Library path is: `artifact_lifecycle/versioning/create_latest_link.py`

**Expected occurrences:**
1. `generate_standards_index.py` lines 426-432
2. `generate_dependency_hygiene_report.py` lines 260-265
3. `generate_anchor_inventory.py` lines 202-209 (inline)

---

### Step 2: Create Library Module (10 min)

**Action:** Extract function to library location

```bash
# Navigate to library location
cd .repo_studios/library/artifact_lifecycle/versioning/

# Copy the provided create_latest_link.py
# (from Phase 3 downloads)
cp /path/to/downloaded/create_latest_link.py .

# Verify file structure
cat create_latest_link.py
```

**What you should see:**
- Clean function definition with type hints
- Comprehensive docstring with usage example
- Proper error handling (FileNotFoundError, ValueError)
- `__all__` export list
- No external dependencies (only pathlib.Path)

**Verify:**
- [ ] File created at correct location
- [ ] Function renamed from `_copy_latest` to `create_latest_link`
- [ ] Docstring present and descriptive
- [ ] Type hints on parameters and return
- [ ] Error handling included

---

### Step 3: Create Test File (15 min)

**Action:** Write comprehensive tests for extracted function

```bash
# Navigate to test location
cd .repo_studios/tests/tests_library/

# Create directory structure
mkdir -p test_artifact_lifecycle/test_versioning/

# Copy the provided test file
cp /path/to/downloaded/test_create_latest_link.py \
   test_artifact_lifecycle/test_versioning/

# Create __init__.py files
touch test_artifact_lifecycle/__init__.py
touch test_artifact_lifecycle/test_versioning/__init__.py
```

**Run tests:**
```bash
# From repo root
pytest .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/test_create_latest_link.py -v

# Expected output:
# test_creates_hardlink_successfully ... PASSED
# test_fallback_to_copy_on_hardlink_failure ... PASSED
# test_overwrites_existing_destination ... PASSED
# test_raises_error_on_missing_source ... PASSED
# test_raises_error_on_directory_source ... PASSED
# test_creates_in_subdirectory ... PASSED
# test_preserves_file_content_exactly ... PASSED
# test_multiple_calls_to_same_destination ... PASSED
# test_handles_unicode_content ... PASSED
# test_artifact_versioning_workflow ... PASSED
# test_cross_format_linking ... PASSED
#
# ======================== 11 passed in 0.15s ========================
```

**Verify:**
- [ ] All 11 tests pass
- [ ] Tests cover success cases
- [ ] Tests cover error cases
- [ ] Tests include integration scenarios

---

### Step 4: Preview Replacement (5 min)

**Action:** Use helper script to preview changes

```bash
# Dry run to see what would change
python replace_duplicate.py \
    --group-id dup_001 \
    --dry-run

# Expected output:
# ================================================
# Processing: dup_001 - create_latest_link
# Occurrences: 3
# Import: from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link
# ================================================
#
# 📄 scripts/producers/generate_standards_index.py (lines 426-432)
# 📝 DRY RUN: ...
#   Would remove lines 426-432:
#     - def _copy_latest(src: Path, dest: Path) -> None:
#     - ...
#   Would add import at line 15:
#     + from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link
```

**Verify:**
- [ ] All 3 files identified correctly
- [ ] Line numbers match your files
- [ ] Import statement looks correct
- [ ] No unexpected changes

---

### Step 5: Apply Replacement (10 min)

**Action:** Replace duplicate code with imports

```bash
# Apply changes (creates backups automatically)
python replace_duplicate.py \
    --group-id dup_001 \
    --apply

# Check backups were created
ls -la .repo_studios/backups/phase3_replacements/
```

**What happens:**
1. Backups created for all 3 files
2. Function definitions removed (replaced with comment)
3. Import statements added at top of each file
4. Original formatting preserved

**Verify changes manually:**
```bash
# Check first file
git diff .repo_studios/scripts/producers/generate_standards_index.py

# You should see:
# - Lines 426-432 deleted (function definition)
# + Line added: "# Imported from library"
# + Import added at top: "from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link"
```

**Verify:**
- [ ] 3 backup files created
- [ ] Function definitions removed from all 3 files
- [ ] Import statements added to all 3 files
- [ ] Files still syntactically valid Python

---

### Step 6: Update Function Calls (5 min)

**Action:** Update call sites to use new name

Since function was renamed from `_copy_latest` to `create_latest_link`, update usages:

```bash
# Find all calls to old function name
grep -r "_copy_latest" .repo_studios/scripts/producers/

# Should find calls like:
# _copy_latest(src, dest)

# Replace with:
# create_latest_link(src, dest)
```

**For each file:**
1. Open in editor
2. Find calls to `_copy_latest(`
3. Replace with `create_latest_link(`
4. Save

**Typical locations:**
- `generate_standards_index.py` - in `write_artifacts()` function
- `generate_dependency_hygiene_report.py` - in `write_artifacts()` function  
- `generate_anchor_inventory.py` - in `write_artifacts()` function

**Verify:**
- [ ] All calls updated to new name
- [ ] No references to `_copy_latest` remain
- [ ] Files still syntactically valid

---

### Step 7: Run Targeted Tests (10 min)

**Action:** Test the modified scripts

```bash
# Test the library function
pytest .repo_studios/tests/tests_library/test_artifact_lifecycle/ -v

# Test the producer scripts that were modified
pytest .repo_studios/tests/tests_producers/test_generate_standards_index.py -v
pytest .repo_studios/tests/tests_producers/test_generate_dependency_hygiene_report.py -v
pytest .repo_studios/tests/tests_producers/test_generate_anchor_inventory.py -v
```

**Expected result:** ✅ All tests pass

**If tests fail:**
1. Check import statements are correct
2. Verify function calls use new name
3. Ensure library module is importable
4. Review error messages carefully
5. Restore from backup if needed:
   ```bash
   cp .repo_studios/backups/phase3_replacements/*.backup <original_location>
   ```

**Verify:**
- [ ] Library tests pass (11 tests)
- [ ] Producer script tests pass
- [ ] No import errors
- [ ] No name errors

---

### Step 8: Run Full Test Suite (5 min)

**Action:** Ensure no regressions

```bash
# Run full test suite
make studio-test-all

# Or directly:
pytest .repo_studios/tests/ -v

# Or just a subset:
pytest .repo_studios/tests/tests_producers/ \
       .repo_studios/tests/tests_library/ -v
```

**Expected result:** ✅ No NEW failures (pre-existing failures OK)

**Verify:**
- [ ] Test suite runs to completion
- [ ] No new failures introduced
- [ ] Import system working correctly
- [ ] All modified files functioning

---

### Step 9: Manual Validation (5 min)

**Action:** Run modified scripts manually

```bash
# Run one of the modified scripts
python .repo_studios/scripts/producers/generate_standards_index.py \
    --repo-root . \
    --log-level DEBUG

# Check that it:
# 1. Imports successfully
# 2. Calls create_latest_link correctly
# 3. Creates artifacts properly
# 4. No errors in log
```

**Verify:**
- [ ] Script runs without import errors
- [ ] Artifacts created successfully
- [ ] "latest" links work correctly
- [ ] No functional regressions

---

### Step 10: Document Lessons Learned (10 min)

**Action:** Fill out lessons learned template

Create: `.repo_studios/docs/phase3_lessons_learned.md`

```markdown
# Phase 3 Lessons Learned

## Extraction: _copy_latest → create_latest_link

**Date:** 2025-10-23  
**Duration:** 60 minutes  
**Outcome:** ✅ Success

### What Went Well
- [ ] Detection report accurately identified duplicates
- [ ] Library path recommendation was correct
- [ ] Tests covered all edge cases
- [ ] Replacement script worked smoothly
- [ ] No regressions introduced

### Challenges Encountered
- Challenge 1: ...
- Solution: ...

### Improvements Needed
- Improvement 1: ...
- Improvement 2: ...

### Metrics
- Lines removed: ~21 (7 lines × 3 files)
- Lines added: ~60 (library + tests)
- Net benefit: Maintainability ↑, DRY principle ✓
- Time spent: 60 minutes

### Validation Checklist
- [x] Function extracted to library
- [x] Tests written and passing
- [x] Duplicates replaced with imports
- [x] Targeted tests pass
- [x] Full suite passes
- [x] Manual validation successful

### Ready for Phase 4?
Yes / No (explain)

### Notes
- ...
```

---

## Success Criteria

Phase 3 is successful when:

- [x] Library module created at correct location
- [x] Comprehensive tests written (11+ tests)
- [x] All tests pass
- [x] 3 duplicate occurrences replaced
- [x] Import statements working
- [x] Function calls updated
- [x] No regressions introduced
- [x] Manual validation successful
- [x] Lessons documented

---

## Rollback Procedure

If anything goes wrong:

```bash
# 1. Restore from backups
cd .repo_studios/backups/phase3_replacements/
for backup in *.backup; do
    original="${backup%.*.backup}"
    cp "$backup" "../../scripts/producers/$original"
done

# 2. Remove library module
rm .repo_studios/library/artifact_lifecycle/versioning/create_latest_link.py

# 3. Remove tests
rm -rf .repo_studios/tests/tests_library/test_artifact_lifecycle/

# 4. Verify restoration
pytest .repo_studios/tests/tests_producers/ -v
```

---

## Troubleshooting

### Import Error: "No module named .repo_studios"

**Cause:** Python path not configured

**Solution:**
```bash
# Add to each modified file (temporary)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[3]))

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Function Name Mismatch

**Cause:** Forgot to update call sites

**Solution:** Search and replace all `_copy_latest` with `create_latest_link`

### Tests Failing

**Cause:** Various - check error message

**Common fixes:**
- Verify import paths
- Check function signatures match
- Ensure test fixtures available
- Review test file paths

---

## Next Steps

After Phase 3 completion:

1. ✅ **Validated:** Manual extraction process works
2. ✅ **Confidence:** Library structure is correct
3. ✅ **Ready:** Can proceed to automation

**Proceed to Phase 4:** Build automated refactoring orchestrator

**What you've proven:**
- Detection → Extraction → Testing → Replacement workflow is solid
- Library naming conventions work
- Import system functions correctly
- No unexpected blockers

---

## Quick Reference Commands

```bash
# Review report
jq '.duplicate_groups[0]' latest_report.json

# Create library file
cp create_latest_link.py .repo_studios/library/artifact_lifecycle/versioning/

# Run library tests
pytest .repo_studios/tests/tests_library/ -v

# Preview replacement
python replace_duplicate.py --group-id dup_001 --dry-run

# Apply replacement
python replace_duplicate.py --group-id dup_001 --apply

# Run targeted tests
pytest .repo_studios/tests/tests_producers/test_generate_standards_index.py

# Run full suite
make studio-test-all

# Rollback if needed
cp .repo_studios/backups/phase3_replacements/*.backup <destination>
```

---

**Time to complete:** ~60 minutes  
**Difficulty:** Moderate (manual validation requires attention to detail)  
**Outcome:** Validated extraction workflow, ready for automation
