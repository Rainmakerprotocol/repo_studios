# Phase 3: Manual Extraction Validation - Quick Start Guide

## 📦 Files Included

1. **create_latest_link.py** - Extracted library function (ready to use)
2. **test_create_latest_link.py** - Comprehensive test suite (11 tests)
3. **replace_duplicate.py** - Helper script for code replacement
4. **PHASE_3_MANUAL_EXTRACTION_GUIDE.md** - Detailed step-by-step walkthrough
5. **phase3_lessons_learned_template.md** - Documentation template
6. **PHASE_3_QUICKSTART.md** - This file

---

## 🎯 Objective

**Validate the extraction workflow** by manually moving ONE duplicate function (`_copy_latest`) from your producer scripts into the library, proving the process works before automation.

**Time Required:** 60 minutes  
**Difficulty:** Moderate  
**Prerequisites:** Phase 1 & 2 complete

---

## 🚀 Quick Installation

### Step 1: Place Library Module

```bash
# Copy library function to correct location
cp create_latest_link.py \
   .repo_studios/library/artifact_lifecycle/versioning/

# Verify placement
ls -l .repo_studios/library/artifact_lifecycle/versioning/create_latest_link.py
```

### Step 2: Place Test File

```bash
# Create test directory structure
mkdir -p .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/

# Copy test file
cp test_create_latest_link.py \
   .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/

# Create __init__.py files
touch .repo_studios/tests/tests_library/__init__.py
touch .repo_studios/tests/tests_library/test_artifact_lifecycle/__init__.py
touch .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/__init__.py
```

### Step 3: Place Helper Script

```bash
# Copy replacement helper
cp replace_duplicate.py .repo_studios/scripts/

# Make executable
chmod +x .repo_studios/scripts/replace_duplicate.py
```

### Step 4: Place Documentation

```bash
# Copy guides to docs
mkdir -p .repo_studios/docs/phase3/
cp PHASE_3_MANUAL_EXTRACTION_GUIDE.md .repo_studios/docs/phase3/
cp phase3_lessons_learned_template.md .repo_studios/docs/phase3/
```

---

## ✅ Validation - Quick Test

### Test 1: Library Function Works

```bash
# Run library tests
pytest .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/test_create_latest_link.py -v

# Expected: 11 tests passed ✅
```

### Test 2: Helper Script Works

```bash
# Preview what would be replaced (safe dry-run)
python .repo_studios/scripts/replace_duplicate.py \
    --group-id dup_001 \
    --dry-run

# Expected: Shows 3 files with line numbers ✅
```

---

## 📋 Execution Checklist

Follow this checklist for the full validation:

### Part A: Preparation (5 min)
- [ ] All Phase 3 files downloaded and placed
- [ ] Library tests pass (11/11)
- [ ] Helper script dry-run works
- [ ] Have backup strategy ready
- [ ] Detection report reviewed (dup_001 exists)

### Part B: Extraction (10 min)
- [ ] Library function in correct location
- [ ] Function renamed correctly (no underscore)
- [ ] Docstring comprehensive
- [ ] Type hints present
- [ ] Error handling included

### Part C: Testing (15 min)
- [ ] Test file created
- [ ] All 11 tests written
- [ ] All tests pass
- [ ] Coverage >90%

### Part D: Replacement (10 min)
- [ ] Dry-run reviewed
- [ ] Backups created
- [ ] Function definitions replaced
- [ ] Imports added
- [ ] Function calls updated

### Part E: Validation (15 min)
- [ ] Library tests pass
- [ ] Producer tests pass
- [ ] Full suite passes
- [ ] Manual script execution works
- [ ] No regressions detected

### Part F: Documentation (10 min)
- [ ] Lessons learned filled out
- [ ] Challenges documented
- [ ] Improvements noted
- [ ] Ready/Not ready decision made

**Total:** ~65 minutes

---

## 🎬 The Fastest Path (Express Mode)

If you're confident and want to move quickly:

```bash
# 1. Setup (2 min)
cp create_latest_link.py .repo_studios/library/artifact_lifecycle/versioning/
mkdir -p .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/
cp test_create_latest_link.py .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/
touch .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/__init__.py
cp replace_duplicate.py .repo_studios/scripts/

# 2. Test library (2 min)
pytest .repo_studios/tests/tests_library/test_artifact_lifecycle/ -v

# 3. Apply replacement (5 min)
python .repo_studios/scripts/replace_duplicate.py --group-id dup_001 --apply

# 4. Update function calls (5 min)
# Manually edit 3 files to change _copy_latest() to create_latest_link()
# - generate_standards_index.py
# - generate_dependency_hygiene_report.py
# - generate_anchor_inventory.py

# 5. Validate (5 min)
pytest .repo_studios/tests/tests_producers/ -v
python .repo_studios/scripts/producers/generate_standards_index.py

# 6. Document (5 min)
cp phase3_lessons_learned_template.md .repo_studios/docs/phase3/lessons_learned.md
# Fill in the template

# Done! ✅
```

**Express Total:** ~25 minutes (for experienced developers)

---

## 🔧 Troubleshooting Quick Fixes

### Issue: "Import Error"

```bash
# Fix Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Tests Failing"

```bash
# Verify test file location
ls .repo_studios/tests/tests_library/test_artifact_lifecycle/test_versioning/test_create_latest_link.py

# Run with verbose output
pytest .repo_studios/tests/tests_library/ -vv
```

### Issue: "Function Not Found"

```bash
# Check library file exists
cat .repo_studios/library/artifact_lifecycle/versioning/create_latest_link.py

# Verify __init__.py files present
find .repo_studios/library -name "__init__.py"
```

### Issue: "Replacement Script Fails"

```bash
# Check report exists
ls .repo_studios/reports/duplicate_detection_reports/latest_report.json

# Verify group ID
jq '.duplicate_groups[].group_id' latest_report.json
```

### Issue: "Need to Rollback"

```bash
# Restore from backups
cp .repo_studios/backups/phase3_replacements/*.backup \
   .repo_studios/scripts/producers/
```

---

## 📊 Expected Results

After completing Phase 3:

### Metrics
- **Files Modified:** 3 (producer scripts)
- **Lines Removed:** ~21 (duplicates)
- **Lines Added:** ~120 (library + tests)
- **Tests Passing:** 11+ (library) + existing (producers)
- **Regressions:** 0

### Outcomes
- ✅ Library module functional
- ✅ Tests comprehensive
- ✅ Imports working
- ✅ No regressions
- ✅ Workflow validated

---

## 🚦 Decision Point

After Phase 3, you must decide:

### ✅ GREEN - Proceed to Phase 4
**Conditions:**
- All tests pass
- No regressions
- Process was smooth
- Confident in workflow

**Action:** Begin Phase 4 (automated refactoring)

### ⚠️ YELLOW - Fix Issues First
**Conditions:**
- Minor issues encountered
- Need tweaks to process
- Uncertain about some steps

**Action:** Address issues, repeat Phase 3 with another duplicate

### 🛑 RED - Redesign Needed
**Conditions:**
- Major blockers
- Fundamental flaws discovered
- Process doesn't scale

**Action:** Review lessons learned, redesign approach

---

## 📖 Detailed Guidance

For step-by-step detailed instructions, see:
**PHASE_3_MANUAL_EXTRACTION_GUIDE.md**

That guide includes:
- Detailed explanation of each step
- Expected outputs at each stage
- Troubleshooting for specific issues
- Rollback procedures
- Command reference

---

## 🎓 What You'll Learn

By the end of Phase 3, you'll understand:

1. **How extraction works** - Manual process from A to Z
2. **Library integration** - Import system and module structure
3. **Testing strategy** - Comprehensive coverage patterns
4. **Replacement mechanics** - How code gets swapped
5. **Validation approach** - Ensuring no regressions
6. **Documentation needs** - Capturing lessons for improvement

---

## 🔗 File Relationships

```
Phase 3 Files Workflow:

create_latest_link.py
    ↓
    Placed in library structure
    ↓
test_create_latest_link.py
    ↓
    Validates library function
    ↓
replace_duplicate.py
    ↓
    Uses detection report (Phase 2)
    ↓
    Replaces code in producer scripts
    ↓
lessons_learned_template.md
    ↓
    Documents outcomes
```

---

## 🎯 Success Criteria

Phase 3 is complete when:

- [x] Library function created and tested
- [x] 3 duplicates replaced with imports
- [x] All tests pass (library + producers)
- [x] Manual validation successful
- [x] Lessons documented
- [x] Decision made: Proceed to Phase 4 or iterate

---

## 📞 Getting Help

If stuck:

1. **Check detailed guide:** PHASE_3_MANUAL_EXTRACTION_GUIDE.md
2. **Review error logs:** Look for specific error messages
3. **Verify prerequisites:** Phase 1 & 2 must be complete
4. **Test incrementally:** Don't skip validation steps
5. **Use rollback:** Backups are there for a reason

---

## ⏭️ What's Next?

**After Phase 3 Success:**

**Phase 4: Automate Extraction**
- Build orchestrator script
- Automate library file creation
- Auto-generate tests
- Auto-replace code
- Add rollback on failure

**Phase 5: Integration with Repo Studios**
- Add Make targets
- Wire into health suite
- Add to remediation tracker
- Update architecture docs

---

## 🎉 Ready to Begin?

**Installation:**  
✅ All files downloaded and placed

**Prerequisites:**  
✅ Phase 1 complete (library structure)  
✅ Phase 2 complete (detection tool)

**Time Allocated:**  
✅ 60-90 minutes available

**Mindset:**  
✅ Ready to validate the process

---

**🚀 START HERE:** Open `PHASE_3_MANUAL_EXTRACTION_GUIDE.md` and follow Step 1

**Good luck! This is where theory becomes practice.** 💪
