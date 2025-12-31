#!/usr/bin/env python3
"""Emit a structured faulthandler snapshot bundle.

This utility replaces the legacy best-effort stderr dump with structured
artifacts under
`.repo_studios/command_center/reports/rawview/fault_snapshots/` so downstream
tooling can ingest on-demand stack captures. It is safe to invoke multiple
times; the helper maintains retention and records provenance in `MANIFEST.json`
and `bundle_summary.json` beside the raw snapshot output.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


ROOT = _repo_root()
ROOT_STR = str(ROOT)
if ROOT_STR and ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

LIBRARIES_ROOT = ROOT / ".repo_studios" / "command_center" / "scripts"
LIBRARIES_ROOT_STR = str(LIBRARIES_ROOT)
if LIBRARIES_ROOT_STR and LIBRARIES_ROOT_STR not in sys.path:
    sys.path.insert(0, LIBRARIES_ROOT_STR)

from libraries import prune_run_directories
from libraries.cli import resolve_repo_root
from libraries.report_paths import build_topic_path

TOPIC_SLUG = "fault_snapshot"


def _default_base_dir(allow_legacy: bool) -> Path:
    if allow_legacy:
        return ROOT / ".repo_studios" / "faulthandler"
    # HOP-compliant path: .repo_studios/reports/healthview/rawview_reports/fault_snapshot/
    return ROOT / build_topic_path("rawview", TOPIC_SLUG)


def _is_truthy(value: Optional[str], *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _safe_int(raw: Optional[str], fallback: int) -> int:
    try:
        return int(raw) if raw is not None else fallback
    except Exception:
        return fallback


@dataclass
class SnapshotSettings:
    base_dir: Path
    outdir: Path
    derived_outdir: bool
    allow_legacy: bool
    artifacts_to_keep: int
    env_snapshot: Dict[str, str]


def _resolve_settings(env: Mapping[str, str], now: Callable[[], datetime]) -> SnapshotSettings:
    allow_legacy_flag = env.get("FAULT_LOGS_ALLOW_LEGACY", "0")
    allow_legacy = _is_truthy(allow_legacy_flag, default=False)

    base_override = env.get("FAULT_SNAPSHOT_BASE_DIR")
    base_dir = Path(base_override) if base_override else _default_base_dir(allow_legacy)

    outdir_override = env.get("FAULT_SNAPSHOT_OUTDIR") or env.get("FAULT_OUTDIR")
    if outdir_override:
        outdir = Path(outdir_override)
        derived = False
    else:
        outdir = base_dir / now().strftime("%Y-%m-%d_%H%M%S")
        derived = True

    artifacts_flag = env.get("FAULT_SNAPSHOT_TO_KEEP") or env.get("FAULT_ARTIFACTS_TO_KEEP")
    keep = max(1, _safe_int(artifacts_flag, 10))

    env_snapshot = {
        "FAULT_SNAPSHOT_BASE_DIR": base_override or "",
        "FAULT_SNAPSHOT_OUTDIR": outdir_override or "",
        "FAULT_SNAPSHOT_TO_KEEP": artifacts_flag or "",
        "FAULT_LOGS_ALLOW_LEGACY": allow_legacy_flag,
    }

    return SnapshotSettings(
        base_dir=base_dir,
        outdir=outdir,
        derived_outdir=derived,
        allow_legacy=allow_legacy,
        artifacts_to_keep=keep,
        env_snapshot=env_snapshot,
    )


def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def dump_snapshot(
    env: Optional[Mapping[str, str]] = None,
    now_factory: Optional[Callable[[], datetime]] = None,
) -> Dict[str, object]:
    env_map = dict(env or os.environ)
    now = now_factory or (lambda: datetime.now(UTC))

    settings = _resolve_settings(env_map, now)
    result: Dict[str, object] = {
        "status": "ok",
        "outdir": str(settings.outdir),
        "base_dir": str(settings.base_dir),
        "derived_outdir": settings.derived_outdir,
        "allow_legacy": settings.allow_legacy,
        "artifacts_to_keep": settings.artifacts_to_keep,
        "errors": [],
    }

    if not _ensure_dir(settings.outdir):
        result.update({"status": "error", "reason": "mkdir_failed"})
        return result

    snapshot_path = settings.outdir / "snapshot.txt"

    fh_status: Dict[str, object] = {
        "imported": False,
        "enabled_before": False,
        "enabled_after": False,
        "dumped": False,
        "errors": [],
    }

    try:
        fh = importlib.import_module("faulthandler")
        fh_status["imported"] = True
    except Exception as exc:
        fh_status["errors"].append(f"import_failed:{exc}")
        result["status"] = "warning"
        _write_bundle(settings, snapshot_path, fh_status, result, now, pruned=0)
        return result

    is_enabled = False
    try:
        is_enabled = bool(getattr(fh, "is_enabled", lambda: False)())
        fh_status["enabled_before"] = is_enabled
    except Exception as exc:
        fh_status["errors"].append(f"is_enabled_failed:{exc}")

    if not is_enabled:
        try:
            fh.enable(all_threads=True)
            fh_status["enabled_after"] = True
        except Exception as exc:
            fh_status["errors"].append(f"enable_failed:{exc}")
    else:
        fh_status["enabled_after"] = True

    try:
        with snapshot_path.open("w", encoding="utf-8", errors="replace") as handle:
            fh.dump_traceback(file=handle, all_threads=True)
        fh_status["dumped"] = True
    except Exception as exc:
        fh_status["errors"].append(f"dump_failed:{exc}")
        result["status"] = "warning"

    pruned = 0
    if settings.derived_outdir and settings.base_dir == settings.outdir.parent:
        prune_summary = prune_run_directories(
            settings.base_dir,
            keep=settings.artifacts_to_keep,
            current_run=settings.outdir,
        )
        pruned = len(prune_summary.removed)

    _write_bundle(settings, snapshot_path, fh_status, result, now, pruned=pruned)
    return result


def _write_bundle(
    settings: SnapshotSettings,
    snapshot_path: Path,
    fh_status: Dict[str, object],
    result: Dict[str, object],
    now: Callable[[], datetime],
    *,
    pruned: int,
) -> None:
    manifest = {
        "ts": now().isoformat(timespec="seconds"),
        "snapshot_file": str(snapshot_path),
        "faulthandler": fh_status,
        "resolved": {
            "outdir": str(settings.outdir),
            "base_dir": str(settings.base_dir),
            "derived_outdir": settings.derived_outdir,
            "allow_legacy": settings.allow_legacy,
            "artifacts_to_keep": settings.artifacts_to_keep,
        },
        "retention": {"keep": settings.artifacts_to_keep, "pruned": pruned},
        "environment": settings.env_snapshot,
    }
    bundle_summary = {
        "status": result.get("status", "ok"),
        "snapshot_file": str(snapshot_path),
        "errors": fh_status.get("errors", []),
        "retention": {"keep": settings.artifacts_to_keep, "pruned": pruned},
    }

    _write_json(settings.outdir / "manifest.json", manifest)
    _write_json(settings.outdir / "bundle_summary.json", bundle_summary)

    summary_lines = [
        "# Faulthandler Snapshot",
        "",
        f"- Status: {bundle_summary['status']}",
        f"- Snapshot file: `{snapshot_path.name}`",
        f"- Generated: {manifest['ts']}",
        f"- Retention: keep {settings.artifacts_to_keep}, pruned {pruned}",
    ]
    errors = fh_status.get("errors") or []
    if errors:
        summary_lines.append(f"- Errors: {', '.join(errors)}")
    (settings.outdir / "SUMMARY.md").write_text("\n".join(summary_lines), encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a faulthandler snapshot bundle")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    args = parser.parse_args(argv)
    resolved_root = resolve_repo_root(explicit=args.repo_root, origin=Path(__file__))
    if resolved_root != ROOT:
        raise SystemExit(
            f"Resolved repo root {resolved_root} does not match script repo root {ROOT}. "
            "Invoke the script from the intended repo checkout."
        )
    dump_snapshot()
    return 0


if __name__ == "__main__":
    sys.exit(main())
