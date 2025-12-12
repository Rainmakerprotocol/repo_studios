# Tier3 YAML Agent Tool System - Implementation Summary

## What We Built

A complete **agent-first tool registry system** for Repo Studios that enables AI agents (including LangChain-based systems) to discover, validate, and invoke Command Center scripts through machine-readable YAML contracts.

## Architecture

### Core Components

1. **tier3_agent_pipeline_template.yaml** - Template for documenting scripts as agent tools
   - 9 comprehensive sections optimized for agent tool calling workflow
   - Inline comments explaining every field
   - Location: `.repo_studios/docs/pipeline/pipeline_templates/`

2. **tier3_scripts_index_schema.yaml** - Schema for auto-generated aggregate index
   - Statistics, discovery arrays, category indices, dependency graph
   - Location: `.repo_studios/docs/pipeline/pipeline_templates/`

3. **generate_tier3_index.py** - Generator script (419 lines)
   - Scans `tier3_*.yaml` files
   - Validates structure (optional)
   - Aggregates into `tier3_scripts_index.yaml`
   - CLI with --repo-root, --output, --validate, --log-level
   - Location: `.repo_studios/docs/pipeline/tier3_index/`

4. **test_tier3_index.py** - Comprehensive test suite (457 lines)
   - 26 tests covering file discovery, validation, indexing, CLI
   - All tests passing ✅
   - Location: `.repo_studios/docs/pipeline/tier3_index/`

5. **README.md** - Module documentation
   - Usage examples, integration guides, schema documentation
   - Location: `.repo_studios/docs/pipeline/tier3_index/`

### Folder Structure

```
.repo_studios/docs/pipeline/
├── pipeline_templates/
│   ├── tier3_agent_pipeline_template.yaml (NEW - 320 lines)
│   └── tier3_scripts_index_schema.yaml     (NEW - 150 lines)
├── tier3_index/                            (NEW folder)
│   ├── generate_tier3_index.py             (NEW - 419 lines)
│   ├── test_tier3_index.py                 (NEW - 457 lines)
│   ├── README.md                           (NEW)
│   └── outputs/
│       └── tier3_scripts_index.yaml        (auto-generated)
├── tier3_*.yaml                            (77+ to be created)
└── [existing tier documentation files updated]
```

## Agent Workflow

### Discovery → Invocation → Validation

```yaml
# 1. Agent loads index for fast discovery
tier3_scripts_index.yaml:
  scripts:
    - script_id: generate_commandview_inventory
      keywords: [commandview, inventory, producer]
      tier3_file: tier3_generate_commandview_inventory.yaml

# 2. Agent searches by keywords
query: "scan PowerShell functions"
matches: [generate_commandview_inventory]

# 3. Agent loads specific tier3 file
tier3_generate_commandview_inventory.yaml:
  invocation:
    command_template: "python {script_path} --target {target_dir}"
  parameters: [target_dir, output_path, log_level]

# 4. Agent constructs command
python .repo_studios/.../generate_commandview_inventory.py \
  --target .repo_studios/command_center

# 5. Agent validates exit codes
error_handling:
  common_errors:
    - exit_code: 1
      meaning: Target directory not found
      agent_action: Verify --target path exists
```

## 9-Section YAML Schema

Optimized for agent journey through tool lifecycle:

1. **tool** - Identity & discovery (id, name, description, keywords, use_when, dont_use_when)
2. **invocation** - Command templates, script paths, environment requirements
3. **parameters** - Name, type, required, default, validation rules, choices, examples
4. **outputs** - Primary/secondary outputs with type, format, path_pattern, structure
5. **behavior** - Idempotent, side_effects, duration_estimate, blocking, mutates flags
6. **error_handling** - Common exit codes, stderr patterns, agent_action recommendations
7. **integration** - Typical workflows, output consumers, input producers, sample output
8. **examples** - Command examples, programmatic invocation (Python, shell)
9. **metadata** - Category, tier, status, version, dependencies (tier3/tier2/tier1), testing info

## Validation Rules

Generator validates:
- **Required sections**: tool, invocation, parameters, outputs, behavior, metadata
- **tool.id**, **tool.name**, **tool.description** must exist
- **metadata.category**: producer, consumer, aggregator, orchestrator, summarizer, utility
- **metadata.status**: template, draft, active, deprecated

Exit code 1 if validation fails with `--validate` flag.

## Usage

### Generate Index

```bash
# Standard generation
python .repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py \
  --repo-root . \
  --validate

# Custom output
python generate_tier3_index.py \
  --output custom_index.yaml \
  --log-level DEBUG
```

### Run Tests

```bash
pytest .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py -v
```

### For LangChain Agents

```python
import yaml

# Load index
with open("tier3_scripts_index.yaml") as f:
    index = yaml.safe_load(f)

# Fast keyword search
tools = [s for s in index["scripts"] if "duplicate" in s["keywords"]]

# Load specific tier3 for invocation
tier3_path = f".repo_studios/docs/pipeline/{tools[0]['tier3_file']}"
with open(tier3_path) as f:
    spec = yaml.safe_load(f)

# Use spec["invocation"]["command_template"] to build command
```

## Integration Points

### With doc_index

Add post-hook in `generate_doc_index.py`:

```python
from tier3_index.generate_tier3_index import run as generate_tier3

log.info("Generating tier3 index...")
exit_code = generate_tier3(["--repo-root", str(repo_root), "--validate"])
```

### Filename Convention Decision

**Chose: Keep "tier3_" prefix**
- Reasons:
  - Human context when browsing filesystem
  - Simple glob pattern: `tier3_*.yaml`
  - Namespace safety (won't conflict with other YAML files)
  - Agents are filename-agnostic (load index first, use tool_id)
  - Industry standards (OpenAI, Anthropic, LangChain, MCP) don't care about filenames

## Proof of Concept

Created first tier3 file:
- **tier3_generate_commandview_inventory.yaml** (180 lines)
- Fully documented CommandView inventory producer
- Successfully validated and indexed
- Demonstrates complete 9-section schema in practice

Generated index shows:
```yaml
statistics:
  total_scripts: 1
  categories:
    producer: 1
  status:
    active: 1
scripts:
  - script_id: generate_commandview_inventory
    keywords: [commandview, inventory, producer, powershell, functions]
    tier3_file: tier3_generate_commandview_inventory.yaml
```

## Documentation Updates

Updated 6 tier documentation files to reference YAML tier3:
- ✅ tier_doc_system_instructions.md
- ✅ tier2_pipeline_template.md
- ✅ tier2_pipeline_howto.md
- ✅ pipeline_doc_map.md
- ✅ README.md
- ✅ (tier1 templates already updated in previous session)

## Testing

**26 tests - all passing ✅**
- File discovery (5 tests)
- YAML validation (6 tests)
- YAML loading (4 tests)
- Index entry creation (2 tests)
- Index generation (4 tests)
- CLI interface (5 tests)

Coverage: Scanner, validator, aggregator, CLI, error handling

## Next Steps

1. **Create remaining tier3 files** (~76 more scripts)
   - Producers (inventory, metrics, reports)
   - Consumers (analyzers, validators)
   - Aggregators (duplicate scan, cross-reference)
   - Orchestrators (pipelines, workflows)
   - Summarizers (digest, rollup)
   - Utilities (slugify, CLI helpers)

2. **Integrate with doc_index**
   - Add tier3 generation as post-hook
   - Include in `make command-center` targets

3. **Agent Integration**
   - Test with LangChain in other repo
   - Validate tool discovery and invocation patterns
   - Refine error_handling guidance based on agent feedback

4. **Continuous Updates**
   - Regenerate index when scripts change
   - Update tier3 files when CLIs evolve
   - Keep validation rules aligned with script reality

## Design Philosophy

**Agent-first, not documentation-first**

- Optimized for programmatic consumption, not human reading
- Discovery → Invocation → Validation → Integration lifecycle
- Machine-readable contracts enable autonomous agent workflows
- Humans use tier1/tier2 markdown; agents use tier3 YAML

This approach diverges strategically from Jarvis (which uses markdown for tier3) to better support the Repo Studios mission of agent orchestration.

---

**Status**: ✅ Implementation complete and tested
**Tests**: ✅ 26/26 passing
**Ready for**: Creating remaining tier3 files, agent integration testing
