# Tier3 Index Generator

Auto-generates `tier3_scripts_index.yaml` from individual `tier3_*.yaml` files for agent tool discovery.

## Structure

``` text
tier3_index/
├── generate_tier3_index.py  # Generator script
├── test_tier3_index.py       # Test suite
├── outputs/                  # Generated index files
│   └── tier3_scripts_index.yaml (auto-generated)
└── README.md                 # This file
```

## Usage

**Generate index:**

```bash
python .repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py \
  --repo-root . \
  --validate
```

**Custom output location:**

```bash
python generate_tier3_index.py \
  --output custom_index.yaml \
  --log-level DEBUG
```

**Run tests:**

```bash
pytest .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py -v
```

## CLI Options

- `--repo-root PATH`: Repository root directory (default: current directory)
- `--output PATH`: Custom output file path (default: `tier3_index/outputs/tier3_scripts_index.yaml`)
- `--validate`: Validate tier3 YAML structure
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## How It Works

- **Scan**: Finds all `tier3_*.yaml` files in `.repo_studios/docs/pipeline/` (non-recursive)
- **Load**: Parses each YAML file with optional validation
- **Validate** (if `--validate`): Checks required keys, categories, statuses
- **Aggregate**: Creates lightweight index entries with statistics and category indices
- **Write**: Outputs `tier3_scripts_index.yaml` with metadata

## Index Schema

The generated index contains:

- **version**: Schema version
- **generated_at**: ISO 8601 timestamp
- **generator_version**: Generator script version
- **repository**: Name, root, branch
- **statistics**: Total scripts, category counts, status counts
- **scripts**: Array of lightweight entries (id, name, category, tier3_file, summary, keywords,
    status, entry_point, importable)
- **by_category**: Index mapping categories to script IDs
- **validation** (optional): Errors and warnings from validation

## Validation Rules

Tier3 files must contain:

- **Required sections**: `tool`, `invocation`, `parameters`, `outputs`, `behavior`, `metadata`
- **tool.id**: Unique identifier
- **tool.name**: Display name
- **tool.description**: Summary
- **metadata.category**: One of: `producer`, `consumer`, `aggregator`, `orchestrator`,
    `summarizer`, `utility`
- **metadata.status**: One of: `template`, `draft`, `active`, `deprecated`

## Integration

### With doc_index

Add as post-hook in `generate_doc_index.py`:

```python
# After generating doc_index.yaml
from tier3_index.generate_tier3_index import run as generate_tier3

log.info("Generating tier3 index...")
exit_code = generate_tier3(["--repo-root", str(repo_root), "--validate"])
if exit_code != 0:
    log.warning("Tier3 index generation had validation errors")
```

### For Agents (LangChain Example)

```python
import yaml

# Load index
with open("tier3_scripts_index.yaml") as f:
    index = yaml.safe_load(f)

# Fast keyword search
def find_tools(keywords):
    matches = []
    for script in index["scripts"]:
        if any(kw in script["keywords"] for kw in keywords):
            matches.append(script)
    return matches

# Load specific tier3 for execution
tools = find_tools(["duplicate", "scan"])
for tool in tools:
    tier3_path = f".repo_studios/docs/pipeline/{tool['tier3_file']}"
    with open(tier3_path) as f:
        tier3_spec = yaml.safe_load(f)
    # Use tier3_spec for invocation
```

## Exit Codes

- `0`: Success
- `1`: Error (missing pipeline dir, validation failures)

## Dependencies

- Python 3.8+
- PyYAML
- pytest (for tests)
