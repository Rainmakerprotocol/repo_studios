"""Temporary script to fix long lines in tier2_available_scripts_roster.md."""
from pathlib import Path

p = Path('.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md')
lines = p.read_text(encoding='utf-8').split('\n')

new512 = """- Minimal orchestrator wrapper required: a orchestrator that calls
  `dump_snapshot()` (or `main()`), then packages the run into the HealthView
  base bundle (manifest/summary/telemetry) under the stage's canonical
  output root"""

new681 = """- Minimal orchestrator wrapper required: a orchestrator that invokes
  `run(argv)` and then emits a single HealthView bundle
  (manifest/summary/telemetry) under the stage's canonical output root;
  wrapper should surface `--strict` and thread through `--artifacts-to-keep`"""

fixed = 0
for i, line in enumerate(lines):
    if len(line) > 200:
        print(f'Long line {i+1}: {len(line)} chars')
        if 'dump_snapshot' in line:
            print('  -> contains dump_snapshot')
        if 'run(argv)' in line:
            print('  -> contains run(argv)')
    if len(line) > 200 and 'dump_snapshot' in line and 'orchestrator' in line:
        lines[i] = new512
        print(f'Fixed line {i+1} (dump_snapshot)')
        fixed += 1
    elif len(line) > 200 and 'run(argv)' in line and 'strict' in line:
        lines[i] = new681
        print(f'Fixed line {i+1} (run(argv))')
        fixed += 1

p.write_text('\n'.join(lines), encoding='utf-8')
print(f'Done - fixed {fixed} lines')
