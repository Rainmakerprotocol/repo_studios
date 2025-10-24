# Test Analyzer Usage Guide

## What It Does

The `test_analyzer.py` script scans your repository for test files and identifies:

✅ **Long tests** that should be decomposed (>30 lines)  
✅ **Missing mocks** for external dependencies (HTTP, DB, cloud services)  
✅ **Global state usage** that creates test dependencies  
✅ **Hard-coded paths and URLs** that make tests brittle  
✅ **Missing assertions** - tests that don't actually verify anything  
✅ **Flaky patterns** like `time.sleep()`  
✅ **Poor naming** - unclear test names  
✅ **Debug code** - leftover print statements  

## Quick Start

### 1. Run the analyzer on your repo:

```bash
python test_analyzer.py /path/to/your/repo
```

This will print the report to your terminal.

### 2. Save the report to a file:

```bash
python test_analyzer.py /path/to/your/repo hardening_report.txt
```

### 3. Review the output:

The report shows:
- **Summary statistics** - total files, tests, issues
- **Issues by category** - what types of problems are most common
- **Top priority files** - sorted by urgency (files with most critical issues first)
- **Specific issues** with line numbers
- **Long tests** that need decomposing
- **Clean files** that are already in good shape

## Understanding the Output

### Priority Score
Files are ranked by priority score:
- **High severity issue** = 10 points
- **Medium severity issue** = 3 points  
- **Low severity issue** = 1 point

Higher score = fix this file first.

### Severity Levels

🔴 **HIGH** - Fix these first:
- Missing assertions (test doesn't verify anything)
- External dependencies without mocks (flaky, slow)
- Global state usage (tests affect each other)
- Real URLs in tests (network dependency)
- Very long tests (>50 lines)

🟡 **MEDIUM** - Fix these next:
- Hard-coded file paths
- Tests using `time.sleep()` (slow, flaky)
- Moderately long tests (30-50 lines)

🔵 **LOW** - Fix when you have time:
- Poor naming conventions
- Debug code (print statements)
- Commented-out code

## Example Workflow

### Step 1: Generate initial report
```bash
python test_analyzer.py ~/myproject > initial_report.txt
```

### Step 2: Start with top priority file
The report shows files ranked by priority. Start with #1.

### Step 3: As you migrate, re-run on that folder
```bash
# After moving scripts/tests/ to tests/scripts/
python test_analyzer.py ~/myproject | grep "tests/scripts"
```

### Step 4: Track progress
Keep the initial report and generate new ones periodically:
```bash
python test_analyzer.py ~/myproject > progress_day1.txt
# ... work on hardening ...
python test_analyzer.py ~/myproject > progress_day2.txt

# Compare
diff progress_day1.txt progress_day2.txt
```

## Integration with Your Migration

Use this tool at each step of your migration:

```bash
# 1. Move the folder
mkdir -p tests/scripts
mv scripts/tests/* tests/scripts/

# 2. Fix imports
sed -i 's/from \. import/from scripts import/g' tests/scripts/*.py

# 3. Run analyzer on just that folder
python test_analyzer.py ~/myproject | grep -A 30 "tests/scripts"

# 4. Harden based on issues found
# Edit the test files to fix HIGH and MEDIUM issues

# 5. Run tests
pytest tests/scripts/ -v

# 6. Commit
git commit -m "Migrate and harden scripts tests"
```

## Tips for Maximum Efficiency

1. **Focus on high severity first** - Don't get distracted by naming issues when there are missing assertions

2. **Decompose in chunks** - If a test is 200 lines, break it into 3-5 focused tests

3. **Add fixtures as you go** - When you see repeated setup code, extract to a fixture

4. **Mock early** - Any external call should be mocked immediately

5. **Run tests after each change** - Don't harden 10 files at once; do one at a time

## Common Patterns & Fixes

### Pattern: Long test with multiple scenarios
```python
# Before: 80 lines testing everything
def test_user_workflow():
    # Create user
    # Update profile  
    # Add friends
    # Send message
    # Delete account
```

**Fix:** Decompose into 5 focused tests with fixtures
```python
@pytest.fixture
def test_user():
    user = create_user("test@example.com")
    yield user
    cleanup_user(user)

def test_user_creation_succeeds():
    ...

def test_user_profile_update_with_valid_data():
    ...
```

### Pattern: External dependency without mock
```python
# Before
def test_api():
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200
```

**Fix:** Mock the call
```python
def test_api(mocker):
    mocker.patch('requests.get', return_value=Mock(status_code=200))
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200
```

### Pattern: Hard-coded paths
```python
# Before
def test_load_config():
    config = load_file("/home/dev/project/config.json")
```

**Fix:** Use fixtures
```python
def test_load_config(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"key": "value"}')
    config = load_file(str(config_file))
```

## Customizing the Analyzer

You can modify `test_analyzer.py` to:
- Adjust line length thresholds (currently 30/50)
- Add custom patterns to detect
- Change severity levels
- Add your own issue categories

Look for these in the code:
```python
# Line 142: Long test threshold
if func_length > 50:  # Change this number

# Line 197: Risky imports
risky_imports = {  # Add your risky imports
    'requests', 'urllib', ...
}
```

## Questions?

The script is well-commented. Read through it to understand what it's checking and customize it for your needs.

Happy hardening! 🔧
