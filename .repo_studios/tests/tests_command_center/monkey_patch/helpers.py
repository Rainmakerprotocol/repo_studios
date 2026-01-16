from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Mapping, MutableMapping, Sequence

__all__ = [
    "AGGREGATORS_ROOT",
    "COMMAND_CENTER_SCRIPTS",
    "CONSUMERS_ROOT",
    "PRODUCERS_ROOT",
    "UTILITIES_ROOT",
    "load_classify_consumer_module",
    "load_monkey_patch_risk_module",
    "load_monkey_patch_trends_aggregator_module",
    "load_optional_module",
    "load_scan_producer_module",
    "write_consumer_bundle",
    "write_legacy_scan_run",
    "write_producer_run",
    "write_structured_scan_run",
]

def _resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if candidate.name != ".repo_studios" and (candidate / ".repo_studios").is_dir():
            return candidate
    raise RuntimeError("Unable to locate repository root containing .repo_studios directory")


_REPO_ROOT = _resolve_repo_root()
_REPO_STUDIOS_ROOT = _REPO_ROOT / ".repo_studios"

PRODUCERS_ROOT = _REPO_STUDIOS_ROOT / "scripts" / "producers"
CONSUMERS_ROOT = _REPO_STUDIOS_ROOT / "scripts" / "consumers"
AGGREGATORS_ROOT = _REPO_STUDIOS_ROOT / "scripts" / "aggregators"
UTILITIES_ROOT = _REPO_STUDIOS_ROOT / "scripts" / "utilities"
COMMAND_CENTER_SCRIPTS = _REPO_STUDIOS_ROOT / "command_center" / "scripts"


def _load_module(name: str, path: Path) -> ModuleType:
    if not path.exists():
        raise FileNotFoundError(str(path))
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_optional_module(name: str, path: Path) -> ModuleType | None:
    try:
        return _load_module(name, path)
    except FileNotFoundError:
        return None


def load_scan_producer_module() -> ModuleType:
    target = PRODUCERS_ROOT / "scan_monkey_patches.py"
    return _load_module("scan_monkey_patches", target)


def load_classify_consumer_module() -> ModuleType:
    target = CONSUMERS_ROOT / "classify_monkey_patches.py"
    return _load_module("classify_monkey_patches", target)


def load_monkey_patch_trends_aggregator_module() -> ModuleType:
    target = AGGREGATORS_ROOT / "analyze_monkey_patch_trends.py"
    return _load_module("analyze_monkey_patch_trends", target)


def load_monkey_patch_risk_module() -> ModuleType:
    target = UTILITIES_ROOT / "monkey_patch_risk.py"
    return _load_module("monkey_patch_risk", target)


def write_structured_scan_run(
    root: Path,
    name: str,
    matches: Sequence[Mapping[str, object]],
    metadata: Mapping[str, object] | None = None,
) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "matches.json").write_text(json.dumps(list(matches)), encoding="utf-8")
    if metadata is not None:
        (run_dir / "report.json").write_text(json.dumps(dict(metadata)), encoding="utf-8")
    return run_dir


def write_legacy_scan_run(root: Path, name: str, findings: Sequence[Mapping[str, object]]) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(list(findings)), encoding="utf-8")
    return run_dir


def write_consumer_bundle(
    root: Path,
    dt: datetime,
    *,
    total: int,
    counts: MutableMapping[str, int],
    scan_dir: Path,
) -> Path:
    name = dt.strftime("%Y%m%d-%H%M")
    bundle_dir = root / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "total_findings": total,
        "counts_by_risk": dict(counts),
        "run_metadata": {"scan_dir": str(scan_dir)},
    }
    (bundle_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "generated_at": dt.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "consumer",
        "scan_dir": str(scan_dir),
    }
    (bundle_dir / "bundle_summary.json").write_text(json.dumps(metadata), encoding="utf-8")
    return bundle_dir


def write_producer_run(root: Path, dt: datetime, findings: Sequence[Mapping[str, object]]) -> Path:
    name = dt.strftime("%Y-%m-%d_%H%M%S")
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(list(findings)), encoding="utf-8")
    return run_dir
