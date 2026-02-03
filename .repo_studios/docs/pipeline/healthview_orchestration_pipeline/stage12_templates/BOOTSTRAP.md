---
title: "Bootstrap Metaprompt"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
status: active
version: 1.1.0
updated_at: 2026-02-02
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/stage_prefix_index.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/producer/review_metaprompts.md
---

# BOOTSTRAP — Universal Entry Point for Script Inspection

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root.

> **Purpose:** Single entry point that takes ONLY a script path and discovers everything else.
> Creates the build document and outputs all parameters needed for class-specific metaprompts.
>
> **Use this when:** Starting a new inspection for ANY script class.
> **After this:** Use the class-specific review_metaprompts.md at:
> `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/{CLASS}/review_metaprompts.md`

---

## How Bootstrap Works

```text
INPUT: Script path only
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: VALIDATE                                               │
│  ├── Script exists?                                             │
│  ├── Is Python file?                                            │
│  └── Within repo boundary?                                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: CLASSIFY                                               │
│  ├── Determine class from path (/producers/ → producer)         │
│  ├── Fallback: analyze code patterns                            │
│  └── Determine compliance tier (A or B)                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CHECK EXISTING                                         │
│  ├── Search rosters for existing assignment                     │
│  ├── Search working_docs for existing build doc                 │
│  └── Handle: none / found / conflict                            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: ASSIGN STAGE & ID                                      │
│  ├── Match script name to topic_keywords in stage_prefix_index  │
│  ├── Default: Stage 11.1 (ASR) if no match                      │
│  └── Generate next ID: scan working_docs, increment max         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: CREATE BUILD DOCUMENT                                  │
│  ├── Copy template from stage12_templates/{class}/              │
│  ├── Place in working_docs/stage_{X_X}/                         │
│  ├── Name: {PREFIX}-{NNN}_{script_stem}_build.md                │
│  └── Replace frontmatter placeholders                           │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
OUTPUT: All parameters for PROMPT-01-SETUP
```

---

## Supported Modes

| Mode | Status | Description |
|------|--------|-------------|
| **SINGLE** | ✅ Implemented | Inspect one script from scratch |
| **RESUME** | ✅ Implemented | Continue interrupted inspection |
| **DISCOVERY** | 🔜 Coming Soon | Find scripts needing inspection |
| **BATCH** | 🔜 Coming Soon | Process multiple scripts in sequence |

---

## PROMPT-00-BOOTSTRAP (SINGLE Mode)

<!-- CHECKPOINT_ID: CHECKPOINT-BOOT -->
<!-- STOP_CONDITION: Build document created and all parameters discovered -->
<!-- PROCEED_SIGNAL: "BOOTSTRAP COMPLETE — Ready for PROMPT-01-SETUP" -->

**Delivers to agent:**

```text
TASK: Bootstrap a new script inspection.

MODE: SINGLE
SCRIPT_PATH: {path to script}

You have ONE input. Discover everything else.

═══════════════════════════════════════════════════════════════════
STEP 1: VALIDATE SCRIPT
═══════════════════════════════════════════════════════════════════

1. Confirm script exists:

   ```python
   # Python (cross-platform) — PREFERRED
   from pathlib import Path
   script = Path(SCRIPT_PATH)
   if not script.exists():
       raise SystemExit(f"ERROR: Script not found at {SCRIPT_PATH}")
   ```

   ```powershell
   # PowerShell (Windows fallback)
   if (-not (Test-Path $SCRIPT_PATH)) { throw "ERROR: Script not found at $SCRIPT_PATH" }
   ```

   - If NOT exists: STOP with "ERROR: Script not found at {SCRIPT_PATH}"

2. Confirm it's a Python file:
   - Check extension is .py
   - If NOT .py: STOP with "ERROR: Not a Python file"

3. Confirm within repo boundary:
   - Path should be under .repo_studios/ or recognized project structure
   - If outside: WARNING but continue (may be external script)

═══════════════════════════════════════════════════════════════════
STEP 2: CLASSIFY SCRIPT
═══════════════════════════════════════════════════════════════════

**2A. Determine SCRIPT CLASS from path:**

| Path Contains | Class |
|---------------|-------|
| `/producers/` | producer |
| `/consumers/` | consumer |
| `/aggregators/` | aggregator |
| `/summarizers/` | summarizer |
| `/utilities/` | utility |
| `/orchestrators/` | orchestrator |
| `/libraries/` | library |

If path doesn't match any pattern, analyze the code:
- Has `ScriptConfig` definitions? → orchestrator
- Reads from producer output paths? → consumer
- Has `build_topic_path()` or `create_storage()`? → producer
- Otherwise → utility (default)

**2B. Determine COMPLIANCE TIER:**

Read the script and search for these Tier A indicators:
- `build_topic_path(`
- `create_storage(`
- `storage.write_manifest`
- `storage.write_summary`
- `storage.write_telemetry`
- Creates `manifest.json`, `summary.md`, or `telemetry.json`

**Search method (Python — cross-platform):**

```python
from pathlib import Path

TIER_A_INDICATORS = [
    'build_topic_path(',
    'create_storage(',
    'storage.write_manifest',
    'storage.write_summary',
    'storage.write_telemetry',
    'manifest.json',
    'summary.md',
    'telemetry.json',
]

content = Path(SCRIPT_PATH).read_text(encoding='utf-8')
is_tier_a = any(indicator in content for indicator in TIER_A_INDICATORS)
COMPLIANCE_TIER = 'A' if is_tier_a else 'B'
print(f"Compliance Tier: {COMPLIANCE_TIER}")
```

Decision:
- ANY indicator found → **Tier A** (Report Generator)
- NO indicators found → **Tier B** (Action Utility)

═══════════════════════════════════════════════════════════════════
STEP 3: CHECK EXISTING ASSIGNMENTS
═══════════════════════════════════════════════════════════════════

**3A. Search for existing build document:**

Search pattern:
`.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_*/*_{script_stem}_build.md`

Where `{script_stem}` = script filename without .py extension

**Build document naming convention:**
```text
{RECORD_ID}_{script_stem}_build.md
     │              │
     │              └── Script filename without .py (e.g., scan_duplicates)
     └── Stage prefix + sequence number (e.g., ASR-012, TER-003)
         Format: {PREFIX}-{NNN} where NNN is zero-padded 3 digits
```

**Search method (Python — cross-platform):**

```python
from pathlib import Path

script_stem = Path(SCRIPT_PATH).stem  # e.g., "scan_duplicates"
working_docs = Path('.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs')

# Search all stage folders
existing = list(working_docs.glob(f'stage_*/*_{script_stem}_build.md'))

if len(existing) == 0:
    print("No existing build doc found. Continue to Step 4.")
elif len(existing) == 1:
    print(f"Existing build doc found: {existing[0]}")
    print("(C)ontinue existing or (R)estart?")
else:
    print(f"CONFLICT: Multiple build docs found: {existing}")
    print("Human decision required.")
```

```powershell
# PowerShell (Windows fallback)
$scriptStem = [System.IO.Path]::GetFileNameWithoutExtension($SCRIPT_PATH)
$pattern = ".repo_studios\docs\pipeline\healthview_orchestration_pipeline\tier2_roster\working_docs\stage_*\*_${scriptStem}_build.md"
$existing = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
$existing | ForEach-Object { $_.FullName }
```

**3B. Handle results:**

| Result | Action |
|--------|--------|
| No existing build doc | Continue to Step 4 |
| One build doc found | Ask: "Existing build doc found at {path}. (C)ontinue existing or (R)estart?" |
| Multiple found | STOP: "CONFLICT: Multiple build docs found. Human decision required." |

If continuing existing:
- Extract RECORD_ID from filename
- Extract STAGE from folder name
- Skip to Step 5 output (no new doc needed)

═══════════════════════════════════════════════════════════════════
STEP 4: ASSIGN STAGE AND GENERATE RECORD ID
═══════════════════════════════════════════════════════════════════

**4A. Read stage_prefix_index.yaml:**

Location: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/stage_prefix_index.yaml`

**4B. Match script to stage using topic_keywords:**

**Matching algorithm:**
- **Case-insensitive:** "Test" matches "test"
- **Substring match:** "validate_inventory" matches keyword "validate"
- **Search scope:** Script filename AND parent folder names
- **First match wins:** Stop at first matching keyword

For each stage in the index:
- Check if any `topic_keywords` appear in the script filename or path
- First match wins

Example matches:
- `run_test_execution_telemetry.py` → matches "test", "telemetry" → Stage 1.1 (TER)
- `generate_anchor_health_report.py` → matches "health" → Stage 2.1 (S21R)
- `validate_inventory.py` → matches "validate", "inventory" → Stage 6.1 (SIR)

**4C. Default if no match:**

If no topic_keywords match: Use Stage 11.1 (ASR) — the catch-all holding stage

> **Note:** If ASR is incorrect for this script, complete the inspection then request
> human reclassification. Add a GAP entry: "Script should be in Stage X.X ({reason})".
> Do NOT create new stages without human approval.

**4D. Check Tier-2 roster for pre-existing assignment:**

BEFORE generating a new ID, check if this script is already assigned in the Tier-2 roster.

**Roster location lookup:**

| Stage | Roster File |
|-------|-------------|
| 1.1 (TER) | `tier2_roster/tier2_test_execution_roster.md` |
| 2.1 (S21R) | `tier2_roster/tier2_docs_health_overview_roster.md` |
| 6.1 (SIR) | `tier2_roster/tier2_inventory_management_roster.md` |
| 11.1 (ASR) | `tier2_roster/tier2_adhoc_scripts_roster.md` |

All rosters are under: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/`

**Search algorithm:**

```python
import re
from pathlib import Path

# ROSTER_MAP: stage_id → roster filename
ROSTER_MAP = {
    "1.1": "tier2_test_execution_roster.md",
    "2.1": "tier2_docs_health_overview_roster.md",
    "6.1": "tier2_inventory_management_roster.md",
    "11.1": "tier2_adhoc_scripts_roster.md",
}

def find_existing_roster_assignment(script_name: str, stage_id: str) -> str | None:
    """Check roster for pre-existing script assignment. Returns record_id or None."""
    roster_file = ROSTER_MAP.get(stage_id)
    if not roster_file:
        return None
    
    roster_path = Path(
        ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster"
    ) / roster_file
    
    if not roster_path.exists():
        return None
    
    content = roster_path.read_text(encoding="utf-8")
    
    # Pattern: record_id: "S21R-003" followed by script.name: "generate_anchor_inventory.py"
    # Search for YAML block containing this script name
    pattern = rf'record_id:\s*"([^"]+)"[\s\S]*?script:\s*\n\s*path:[^\n]*\n\s*name:\s*"{re.escape(script_name)}"'
    match = re.search(pattern, content)
    
    if match:
        return match.group(1)  # Return the record_id
    return None

# Usage:
existing_id = find_existing_roster_assignment(SCRIPT_NAME, STAGE_ID)
if existing_id:
    print(f"ROSTER HIT: {SCRIPT_NAME} already assigned as {existing_id}")
    RECORD_ID = existing_id  # USE THIS ID
else:
    print(f"No roster entry for {SCRIPT_NAME} — proceed to generate new ID")
    # Continue to Step 4E
```

**Decision logic:**

| Result | Action |
|--------|--------|
| Roster entry found | **USE THAT ID** — do not generate new |
| No roster entry | Proceed to Step 4E to generate new ID |

> **CRITICAL:** The roster is the authoritative source for script-to-ID mappings.
> If a script already has an assignment, you MUST use it. Generating a duplicate ID
> creates inconsistency between working_docs and the roster.

**4E. Generate next RECORD_ID (if no roster entry):**

1. Get PREFIX from matched stage (e.g., TER, ASR, S21R)
2. Get working_docs path from matched stage
3. Scan folder for pattern: `{PREFIX}-(\d+)_*_build.md`
4. Find maximum number
5. New ID = `{PREFIX}-{max+1:03d}`

Example:
- Stage 11.1, PREFIX = ASR
- Existing: ASR-001, ASR-005, ASR-011
- Max = 11
- New ID = ASR-012

> **Note:** Gaps in ID sequences (e.g., ASR-002 missing) are intentional.
> Deleted or deprecated records leave gaps. **Never reuse IDs** — always use max+1.

═══════════════════════════════════════════════════════════════════
STEP 5: CREATE BUILD DOCUMENT
═══════════════════════════════════════════════════════════════════

**5A. Determine paths:**

```text
TEMPLATE_SOURCE: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/{CLASS}/build_template.md
BUILD_DOC_DEST:  .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_{STAGE}/{RECORD_ID}_{script_stem}_build.md
DEST_FOLDER:     .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_{STAGE}/
```

Where:
- `{CLASS}` = Script class from Step 2 (producer, consumer, aggregator, etc.)
- `{STAGE}` = Stage with underscore (e.g., `11_1` for Stage 11.1)
- `{RECORD_ID}` = Generated ID from Step 4 (e.g., `ASR-012`)
- `{script_stem}` = Script filename without `.py` extension

**5B. Create destination folder (if needed):**

```python
# Python (cross-platform)
import os
os.makedirs(DEST_FOLDER, exist_ok=True)
```

```powershell
# PowerShell (Windows)
New-Item -ItemType Directory -Path $DEST_FOLDER -Force | Out-Null
```

**5C. Copy template and replace placeholders:**

Use Python for cross-platform compatibility:

```python
from pathlib import Path
from datetime import datetime, timedelta

# Read template
template_path = Path(TEMPLATE_SOURCE)
content = template_path.read_text(encoding='utf-8')

# Calculate dates
today = datetime.now().strftime('%Y-%m-%d')
valid_until = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

# Compute derived values
script_path = Path(SCRIPT_PATH)
script_name = script_path.name                    # e.g., "scan_duplicates.py"
script_stem = script_path.stem                    # e.g., "scan_duplicates"
script_dir = str(script_path.parent)              # e.g., ".repo_studios/scripts/producers"
line_count = len(script_path.read_text().splitlines())

# ═══════════════════════════════════════════════════════════════
# PLACEHOLDER REPLACEMENT TABLE
# ═══════════════════════════════════════════════════════════════
# Category: BOOTSTRAP — Replace during template copy
# ───────────────────────────────────────────────────────────────
content = content.replace('<RECORD_ID>', RECORD_ID)           # e.g., "ASR-012"
content = content.replace('<SCRIPT_PATH>', SCRIPT_PATH)       # e.g., ".repo_studios/scripts/producers/scan_duplicates.py"
content = content.replace('<SCRIPT_NAME>', script_name)       # e.g., "scan_duplicates.py"
content = content.replace('<TARGET_STAGE>', TARGET_STAGE)     # e.g., "Stage 11.1"

# Category: COMPUTED — Derived from script analysis
# ───────────────────────────────────────────────────────────────
content = content.replace('<SCRIPT_DIR>', script_dir)         # e.g., ".repo_studios/scripts/producers"
content = content.replace('<LINE_COUNT>', str(line_count))    # e.g., "450"

# Category: FRONTMATTER — Dates
# ───────────────────────────────────────────────────────────────
# Note: valid_until uses <YYYY-MM-DD> format in template
content = content.replace('valid_until: <YYYY-MM-DD>', f'valid_until: {valid_until}')
# Note: updated_at already has a date; replace with today
content = content.replace('updated_at: 2026-02-01', f'updated_at: {today}')

# Write to destination
dest_path = Path(BUILD_DOC_DEST)
dest_path.write_text(content, encoding='utf-8')

print(f"Build document created at: {dest_path}")
```

**5D. Placeholder Reference Table:**

| Placeholder | Source | Example Value | When Replaced |
|-------------|--------|---------------|---------------|
| `<RECORD_ID>` | Step 4 output | `ASR-012` | BOOTSTRAP (now) |
| `<SCRIPT_PATH>` | User input | `.repo_studios/scripts/producers/scan_duplicates.py` | BOOTSTRAP (now) |
| `<SCRIPT_NAME>` | Derived | `scan_duplicates.py` | BOOTSTRAP (now) |
| `<SCRIPT_DIR>` | Derived | `.repo_studios/scripts/producers` | BOOTSTRAP (now) |
| `<TARGET_STAGE>` | Step 4 output | `Stage 11.1` | BOOTSTRAP (now) |
| `<LINE_COUNT>` | Computed | `450` | BOOTSTRAP (now) |
| `valid_until` | Today + 90 days | `2026-05-03` | BOOTSTRAP (now) |
| `updated_at` | Today | `2026-02-02` | BOOTSTRAP (now) |
| `<TOPIC>` | Script purpose | `duplicate_scan` | PROMPT-34-PREPARE |
| `<ASSIGNEE>` | Current user/agent | `GitHub Copilot` | PROMPT-910-CLOSE |
| `<YYYY-MM-DD>` (in logs) | Inspection date | `2026-02-02` | During each prompt |
| `<path>:<line>` | Code inspection | `script.py:45` | During each prompt |
| `<evidence>` | Verification | Actual findings | During each prompt |

**Placeholders NOT replaced during BOOTSTRAP:**
- `<TOPIC>` — Filled during PROMPT-34-PREPARE based on script analysis
- `<ASSIGNEE>` — Filled during PROMPT-910-CLOSE by inspector
- `<YYYY-MM-DD>` in verification logs — Filled incrementally during each prompt
- `<path>:<line>`, `<evidence>`, `<agent/human>` — Filled during inspection

**5E. Verify creation:**

```python
# Verify file exists and has expected content
dest_path = Path(BUILD_DOC_DEST)
assert dest_path.exists(), f"Build document not created at {dest_path}"
content = dest_path.read_text(encoding='utf-8')
assert RECORD_ID in content, f"RECORD_ID {RECORD_ID} not found in build document"
assert SCRIPT_PATH in content, f"SCRIPT_PATH not found in build document"
print(f"✓ Build document verified at: {dest_path}")
```

═══════════════════════════════════════════════════════════════════
STEP 6: OUTPUT HANDOFF
═══════════════════════════════════════════════════════════════════

Print the following:

---

## BOOTSTRAP COMPLETE

**Build Document Created:**
`{BUILD_DOC_DEST}`

**Discovery Summary:**

| Property | Value | Source |
|----------|-------|--------|
| Script | {SCRIPT_NAME} | input |
| Class | {CLASS} | path analysis |
| Compliance Tier | {A or B} | code analysis |
| Stage | {STAGE} | topic keyword match |
| Record ID | {RECORD_ID} | generated |
| Template | {CLASS}/build_template.md | class mapping |

**Parameters for PROMPT-01-SETUP:**
```
BUILD_DOC: {BUILD_DOC_DEST}
SCRIPT_PATH: {SCRIPT_PATH}
RECORD_ID: {RECORD_ID}
COMPLIANCE_TIER: {A or B}
TARGET_STAGE: Stage {STAGE}
```

**Next Step:**
Open `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md` and deliver PROMPT-01-SETUP with the parameters above.

> **Note:** The review prompts are class-agnostic. The class-specific template
> (`{CLASS}/build_template.md`) was already applied during template copy.

---

PROCEED_SIGNAL: "BOOTSTRAP COMPLETE — Ready for PROMPT-01-SETUP"
```

---

## PROMPT-00-RESUME (RESUME Mode)

<!-- CHECKPOINT_ID: CHECKPOINT-RESUME -->
<!-- STOP_CONDITION: Last checkpoint identified, next prompt determined -->
<!-- PROCEED_SIGNAL: "RESUME COMPLETE — Continue from {NEXT_PROMPT}" -->

**Use when:** Continuing an interrupted inspection with an existing build document.

**Delivers to agent:**

```text
TASK: Resume an interrupted script inspection.

MODE: RESUME
BUILD_DOC: {path to existing build document}

═══════════════════════════════════════════════════════════════════
STEP R1: VALIDATE BUILD DOCUMENT
═══════════════════════════════════════════════════════════════════

1. Confirm build document exists:

   ```python
   from pathlib import Path
   build_doc = Path(BUILD_DOC)
   if not build_doc.exists():
       raise SystemExit(f"ERROR: Build document not found at {BUILD_DOC}")
   ```

2. Extract metadata from build document:

   ```python
   content = build_doc.read_text(encoding='utf-8')
   
   # Extract from filename: {RECORD_ID}_{script_stem}_build.md
   import re
   filename = build_doc.name
   match = re.match(r'([A-Z0-9]+-\d+)_(.+)_build\.md', filename)
   if match:
       RECORD_ID = match.group(1)
       script_stem = match.group(2)
   
   # Extract SCRIPT_PATH from content
   path_match = re.search(r'\*\*Path\*\*\s*\|\s*`([^`]+)`', content)
   SCRIPT_PATH = path_match.group(1) if path_match else None
   
   # Extract COMPLIANCE_TIER from content
   tier_match = re.search(r'\*\*Compliance Tier\*\*\s*\|\s*(A|B)', content)
   COMPLIANCE_TIER = tier_match.group(1) if tier_match else None
   
   print(f"RECORD_ID: {RECORD_ID}")
   print(f"SCRIPT_PATH: {SCRIPT_PATH}")
   print(f"COMPLIANCE_TIER: {COMPLIANCE_TIER}")
   ```

═══════════════════════════════════════════════════════════════════
STEP R2: DETECT LAST COMPLETED CHECKPOINT
═══════════════════════════════════════════════════════════════════

Search for checkpoint completion markers in the build document.

**Checkpoint detection patterns:**

| Checkpoint | Pattern to Search | Found In |
|------------|-------------------|----------|
| CHECKPOINT-0 | `CHECKPOINT-0:.*confirmed` or Status = `PASS` in Section 0 | Section 0.1 |
| CHECKPOINT-1 | `CHECKPOINT-1:.*captured` or Identity table populated | Section 1 |
| CHECKPOINT-2A | `CHECKPOINT-2A:.*complete` or UIC table has entries | Section 2.4 |
| CHECKPOINT-2B | `CHECKPOINT-2B:.*verified` or Truth table has TRUE verdicts | Section 2.5.5 |
| CHECKPOINT-3 | `CHECKPOINT-3:.*verified` or Tier-3 YAML status = PASS | Section 3.1 |
| CHECKPOINT-4 | `CHECKPOINT-4:.*present` or DB checklist completed | Section 4.2 |
| CHECKPOINT-5 | `CHECKPOINT-5:.*complete` or Gap table has real entries | Section 5.1 |
| CHECKPOINT-6 | `CHECKPOINT-6:.*recorded` or Change log has entries | Section 6.1 |
| CHECKPOINT-7 | `CHECKPOINT-7:.*captured` or Evidence table has entries | Section 7.1 |
| CHECKPOINT-8 | `CHECKPOINT-8:.*ready` or ScriptConfig table filled | Section 8.2 |
| CHECKPOINT-9 | `CHECKPOINT-9:.*complete` or Attestation signed | Section 9.1 |
| CHECKPOINT-10 | `CHECKPOINT-10:.*COMPLETE` or status: complete in frontmatter | Section 10 |

**Python checkpoint detection:**

```python
import re
from pathlib import Path

CHECKPOINT_ORDER = [
    ('CHECKPOINT-0', 'CHECKPOINT-0:.*confirmed|Section 0.*Status.*PASS'),
    ('CHECKPOINT-1', 'CHECKPOINT-1:.*captured|\\| \\*\\*Name\\*\\* \\| `[^<]'),
    ('CHECKPOINT-2A', 'CHECKPOINT-2A:.*complete|UIC-00[1-9].*PASS'),
    ('CHECKPOINT-2B', 'CHECKPOINT-2B:.*verified|Verdict.*TRUE'),
    ('CHECKPOINT-3', 'CHECKPOINT-3:.*verified|tier3\\.yaml.*PASS'),
    ('CHECKPOINT-4', 'CHECKPOINT-4:.*present|DB.*Status.*PASS'),
    ('CHECKPOINT-5', 'CHECKPOINT-5:.*complete|GAP-\\d{3}'),
    ('CHECKPOINT-6', 'CHECKPOINT-6:.*recorded|Change Log.*\\|.*\\d'),
    ('CHECKPOINT-7', 'CHECKPOINT-7:.*captured|Evidence.*\\|.*PASS'),
    ('CHECKPOINT-8', 'CHECKPOINT-8:.*ready|script_id.*\\|'),
    ('CHECKPOINT-9', 'CHECKPOINT-9:.*complete|Inspector.*\\|.*\\d{4}'),
    ('CHECKPOINT-10', 'CHECKPOINT-10:.*COMPLETE|^status:\\s*complete'),
]

content = Path(BUILD_DOC).read_text(encoding='utf-8')

last_completed = None
for checkpoint, pattern in CHECKPOINT_ORDER:
    if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
        last_completed = checkpoint
    else:
        break  # Stop at first incomplete checkpoint

print(f"Last completed checkpoint: {last_completed or 'None'}")
```

═══════════════════════════════════════════════════════════════════
STEP R3: DETERMINE NEXT PROMPT
═══════════════════════════════════════════════════════════════════

Based on the last completed checkpoint, determine which prompt to resume from:

| Last Completed | Next Prompt | Rationale |
|----------------|-------------|-----------|
| None | PROMPT-01-SETUP | Start from beginning |
| CHECKPOINT-0 | PROMPT-01-SETUP | Complete identity capture |
| CHECKPOINT-1 | PROMPT-2A-ANALYZE | Begin analysis |
| CHECKPOINT-2A | PROMPT-2B-VERIFY | Execute and verify |
| CHECKPOINT-2B | PROMPT-34-PREPARE | Prepare Tier-3 YAML |
| CHECKPOINT-3 | PROMPT-34-PREPARE | Complete DB integration |
| CHECKPOINT-4 | PROMPT-5-GAPS | Identify gaps |
| CHECKPOINT-5 | PROMPT-67-EVIDENCE | Record changes |
| CHECKPOINT-6 | PROMPT-67-EVIDENCE | Capture evidence |
| CHECKPOINT-7 | PROMPT-8-ORCHESTRATOR | Configure orchestrator |
| CHECKPOINT-8 | PROMPT-910-CLOSE | Final attestation |
| CHECKPOINT-9 | PROMPT-910-CLOSE | Complete finalization |
| CHECKPOINT-10 | — | Already complete! |

```python
NEXT_PROMPT_MAP = {
    None: 'PROMPT-01-SETUP',
    'CHECKPOINT-0': 'PROMPT-01-SETUP',
    'CHECKPOINT-1': 'PROMPT-2A-ANALYZE',
    'CHECKPOINT-2A': 'PROMPT-2B-VERIFY',
    'CHECKPOINT-2B': 'PROMPT-34-PREPARE',
    'CHECKPOINT-3': 'PROMPT-34-PREPARE',
    'CHECKPOINT-4': 'PROMPT-5-GAPS',
    'CHECKPOINT-5': 'PROMPT-67-EVIDENCE',
    'CHECKPOINT-6': 'PROMPT-67-EVIDENCE',
    'CHECKPOINT-7': 'PROMPT-8-ORCHESTRATOR',
    'CHECKPOINT-8': 'PROMPT-910-CLOSE',
    'CHECKPOINT-9': 'PROMPT-910-CLOSE',
    'CHECKPOINT-10': None,  # Complete
}

NEXT_PROMPT = NEXT_PROMPT_MAP.get(last_completed)

if NEXT_PROMPT is None and last_completed == 'CHECKPOINT-10':
    print("Inspection already complete! No action needed.")
else:
    print(f"Resume from: {NEXT_PROMPT}")
```

═══════════════════════════════════════════════════════════════════
STEP R4: OUTPUT HANDOFF
═══════════════════════════════════════════════════════════════════

Print the following:

---

## RESUME COMPLETE

**Build Document:**
`{BUILD_DOC}`

**Resume Summary:**

| Property | Value | Source |
|----------|-------|--------|
| Record ID | {RECORD_ID} | filename |
| Script Path | {SCRIPT_PATH} | content |
| Compliance Tier | {COMPLIANCE_TIER} | content |
| Last Checkpoint | {last_completed} | content scan |
| Next Prompt | {NEXT_PROMPT} | checkpoint map |

**Parameters for {NEXT_PROMPT}:**
```
BUILD_DOC: {BUILD_DOC}
SCRIPT_PATH: {SCRIPT_PATH}
RECORD_ID: {RECORD_ID}
COMPLIANCE_TIER: {COMPLIANCE_TIER}
```

**Next Step:**
Open `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md` and deliver {NEXT_PROMPT} with the parameters above.

---

PROCEED_SIGNAL: "RESUME COMPLETE — Continue from {NEXT_PROMPT}"
```

---

## Edge Case Handling

| Situation | Detection | Response |
|-----------|-----------|----------|
| Script not found | `Path.exists()` returns False | ERROR: Script not found |
| Not a Python file | Extension ≠ .py | ERROR: Not a Python file |
| Class indeterminate | Path and code don't match patterns | Default to `utility`, warn human |
| Existing build doc | File pattern match | Offer: Continue or Restart |
| Multiple build docs | Multiple matches | STOP: Human decision required |
| No topic keyword match | No stage matches | Default to Stage 11.1 (ASR) |
| Working docs folder missing | Folder doesn't exist | Create folder automatically |
| Template missing | Template file not found | ERROR: Template not found for class {CLASS} |

---

## Cross-Platform Command Reference

> **Principle:** Python-first for all commands. PowerShell fallback for Windows-only environments.

### File Operations

| Task | Python (Preferred) | PowerShell (Windows) |
|------|-------------------|---------------------|
| Check file exists | `Path(p).exists()` | `Test-Path $p` |
| Read file | `Path(p).read_text(encoding='utf-8')` | `Get-Content $p -Raw` |
| Write file | `Path(p).write_text(s, encoding='utf-8')` | `Set-Content $p -Value $s` |
| Create folder | `os.makedirs(p, exist_ok=True)` | `New-Item -ItemType Directory -Path $p -Force` |
| Copy file | `shutil.copy(src, dst)` | `Copy-Item $src $dst` |
| List files | `Path(p).glob(pattern)` | `Get-ChildItem -Path $p -Filter $pattern` |
| Get filename | `Path(p).name` | `[System.IO.Path]::GetFileName($p)` |
| Get stem | `Path(p).stem` | `[System.IO.Path]::GetFileNameWithoutExtension($p)` |

### Search Operations

| Task | Python (Preferred) | PowerShell (Windows) |
|------|-------------------|---------------------|
| Find pattern in file | `pattern in Path(p).read_text()` | `Select-String -Path $p -Pattern $pattern` |
| Find files by glob | `Path(root).glob('**/*.py')` | `Get-ChildItem -Path $root -Recurse -Filter *.py` |
| Count lines | `len(Path(p).read_text().splitlines())` | `(Get-Content $p).Count` |

### Python Invocation

| Environment | Command |
|-------------|--------|
| System Python | `python` or `python3` |
| Windows venv | `.venv\Scripts\python.exe` |
| Unix venv | `.venv/bin/python` |
| Programmatic | `sys.executable` (from within Python) |

**Example: Run script from Python:**
```python
import subprocess
import sys

result = subprocess.run(
    [sys.executable, SCRIPT_PATH, '--help'],
    capture_output=True, text=True
)
print(result.stdout or result.stderr)
```

---

## Quick Reference: Stage Prefix Index

| Stage | Prefix | Name | Topic Keywords |
|-------|--------|------|----------------|
| 1.1 | TER | Test Execution Record | test, telemetry, execution, pytest, coverage |
| 2.1 | S21R | Stage 2.1 Record | docs, health, documentation, overview |
| 3.1 | FDR | Fault Diagnostics Record | fault, diagnostic, error, failure |
| 4.1 | DIR | Dependency/Import Record | dependency, import, hygiene, boundary |
| 5.1 | CHR | Churn/Heatmap Record | churn, heatmap, complexity, monkey, patch |
| 6.1 | SIR | Standards/Inventory Record | standards, integrity, inventory, validate, schema |
| 10.1 | PIR | Pipeline Integration Record | pipeline, integration, orchestrator, suite, full |
| 11.1 | ASR | Available Scripts Record | *(default catch-all)* |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.5 | 2026-02-02 | RESUME mode: Added PROMPT-00-RESUME section with checkpoint detection logic, next-prompt mapping, and Python implementation; added Supported Modes table |
| 1.0.4 | 2026-02-02 | Cross-platform commands: Replaced Unix-only `test -f` with Python `Path.exists()`, added search methods for Tier A detection and existing build doc discovery, added Cross-Platform Command Reference section |
| 1.0.3 | 2026-02-02 | Route to `common/review_metaprompts.md` instead of `{CLASS}/review_metaprompts.md`; review prompts are now shared across all script classes |
| 1.0.2 | 2026-02-02 | Step 5 overhaul: Added Python copy method, folder creation, complete placeholder reference table (8 BOOTSTRAP + 6 RUNTIME), verification step |
| 1.0.1 | 2026-02-02 | Path resolution: Added HOP_ROOT constant, converted all file references to absolute paths from repo root |
| 1.0.0 | 2026-02-01 | Initial release — universal bootstrap with stage_prefix_index.yaml integration |
