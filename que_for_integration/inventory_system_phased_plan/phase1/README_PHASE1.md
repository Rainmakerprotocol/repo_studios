# Phase 1: Core Script Development

## Contents

This package contains the core inventory generation script for the Jarvis Function Inventory System.

### Files Included

- **generate_inventory.py** - Main inventory generation script

## Installation

1. Copy `generate_inventory.py` to your Jarvis repository:
   ```bash
   cp generate_inventory.py /path/to/jarvis/tools/
   ```

2. Make the script executable:
   ```bash
   chmod +x /path/to/jarvis/tools/generate_inventory.py
   ```

3. Verify Python version (3.8+ required):
   ```bash
   python3 --version
   ```

## Testing the Script

### Quick Test

Create a test directory with a simple Python file:

```bash
# Create test structure
mkdir -p test_folder
cat > test_folder/sample.py << 'EOF'
"""Sample module for testing."""

def hello_world():
    """Print a greeting."""
    print("Hello, world!")

class MyClass:
    """A sample class."""
    
    def __init__(self):
        """Initialize the class."""
        pass
    
    def my_method(self):
        """A sample method."""
        return "Hello from method"
EOF

# Run the script
python3 tools/generate_inventory.py test_folder -v
```

### Expected Output

```
[INFO] Scanning directory: /path/to/test_folder
[INFO] Found 1 Python files
[INFO] Processing: sample.py
[INFO] Creating output directory: /path/to/test_folder/test_folder_index
[INFO] Writing inventory to: /path/to/test_folder/test_folder_index/test_folder_index.json
✅ Inventory generated successfully
📁 Output: /path/to/test_folder/test_folder_index/test_folder_index.json

📊 Summary:
   Files scanned: 1
   Total functions: 3
   Total classes: 1
   Lines of code: 18
   Public functions: 2
   Private functions: 1
   Async functions: 0
```

### Verify Output

Check the generated JSON:

```bash
cat test_folder/test_folder_index/test_folder_index.json
```

## Usage Examples

### Basic Usage

```bash
# Index a directory
python3 tools/generate_inventory.py modules/interface
```

### Verbose Mode

```bash
# See detailed processing information
python3 tools/generate_inventory.py modules/interface -v
```

### Different Directories

```bash
# Index various directories
python3 tools/generate_inventory.py agents/diagnostic
python3 tools/generate_inventory.py services/orchestration
python3 tools/generate_inventory.py tools
```

## Output Structure

The script creates:

```
<target_folder>/
├── (your python files)
└── <folder_name>_index/
    └── <folder_name>_index.json
```

Example for `modules/interface`:

```
modules/interface/
├── manager.py
├── handlers.py
└── interface_index/
    └── interface_index.json
```

## JSON Structure

The generated JSON contains:

```json
{
  "metadata": {
    "generated_at": "2025-10-23T14:32:15Z",
    "folder_path": "/path/to/folder",
    "folder_name": "interface",
    "total_files": 5,
    "total_functions": 23,
    "total_classes": 3,
    "scan_depth": "recursive"
  },
  "files": [
    {
      "path": "/full/path/to/file.py",
      "relative_path": "file.py",
      "line_count": 150,
      "functions": [...],
      "classes": [...],
      "imports": [...]
    }
  ],
  "statistics": {
    "total_lines_of_code": 1247,
    "files_by_type": {".py": 5},
    "private_functions": 8,
    "public_functions": 15,
    "async_functions": 6
  }
}
```

## Error Handling

The script handles:

- **Invalid paths**: Clear error message if path doesn't exist
- **Not a directory**: Error if path is a file, not a directory
- **Syntax errors**: Logs warning and continues with other files
- **Permission errors**: Reports error and skips file
- **Empty directories**: Error message if no Python files found

## Script Features

### What It Extracts

- ✅ Function names and line numbers
- ✅ Function docstrings (first line)
- ✅ Async function detection
- ✅ Private function detection (starts with `_`)
- ✅ Class definitions
- ✅ Class methods
- ✅ Import statements
- ✅ Line counts per file
- ✅ Aggregate statistics

### What It Filters

The script automatically skips:
- `__pycache__/` directories
- `.venv/` and `venv/` directories
- `.git/` directory
- Hidden directories (starting with `.`)
- `.tox/`, `build/`, `dist/` directories

## Testing Checklist

Use this checklist to validate Phase 1:

- [ ] Script runs without errors on valid directory
- [ ] Script creates `<folder>_index/` directory
- [ ] JSON file is created with correct naming
- [ ] JSON structure matches specification
- [ ] All Python files are scanned
- [ ] Functions are extracted correctly
- [ ] Classes and methods are extracted
- [ ] Imports are captured
- [ ] Statistics are calculated correctly
- [ ] Existing index files are replaced (not duplicated)
- [ ] Timestamp is in ISO format
- [ ] Error handling works (test with syntax error file)
- [ ] Verbose mode provides useful output
- [ ] Script exits with code 0 on success
- [ ] Script exits with code 1 on error

## Common Issues and Solutions

### Issue: "Path does not exist"
**Solution**: Verify the path is correct and accessible

### Issue: "No Python files found"
**Solution**: Check that directory contains .py files and isn't empty

### Issue: Syntax errors in files
**Solution**: This is expected - script logs warning and continues

### Issue: Permission denied
**Solution**: Check file/directory permissions

## Next Steps

After validating Phase 1:
1. Test on small sample directories
2. Test on nested directory structures
3. Verify JSON structure matches needs
4. Proceed to Phase 2 (Makefile integration)

## Support

For issues or questions:
- Check the phased plan YAML for detailed specifications
- Review error messages in verbose mode
- Validate Python version (3.8+)
- Ensure all paths are correct and accessible
