#!/usr/bin/env python3
"""Select the next Tier-1 HealthView checkbox candidate and emit an action packet.

This runner is intentionally narrow:
- Reads the hardened workflow spec YAML
- Uses checkbox_report.csv as the source of truth for *unchecked* tasks
- Filters to Tier-1 gate files and requires a Tier-2 record link+anchor
- Selects deterministically using strict stage order and line number

It does not execute changes. It emits a structured packet that a human or agent can follow.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[4]
LIBRARIES_ROOT = ROOT / ".repo_studios" / "command_center" / "scripts"
if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))

from libraries.cli import resolve_repo_root  # noqa: E402


LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


STAGE_PATTERN = re.compile(r"Stage\s+(?P<main>\d+)(?:\.(?P<sub>\d+))?")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER_PATTERN = re.compile(r"<[^>]+>")
MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(?P<text>.+?)\s*$")
HTML_ANCHOR_PATTERN = re.compile(r"<(?:a|span)\s+[^>]*(?:id|name)=\"(?P<id>[^\"]+)\"[^>]*>")


@dataclass(frozen=True)
class StageKey:
    main: int
    sub: int | None

    def sort_key(self) -> tuple[int, int]:
        # substage-less entries sort before substages within the same main stage.
        return (self.main, -1 if self.sub is None else self.sub)

    @property
    def label(self) -> str:
        return f"{self.main}.{self.sub}" if self.sub is not None else f"{self.main}"


@dataclass(frozen=True)
class CheckboxCandidate:
    file_path: str
    line_number: int
    heading_h1: str
    heading_h2: str
    heading_h3: str
    heading_h4: str
    checkbox_text: str
    kind: str
    stage: StageKey
    tier2_link: str


def _configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s", force=True)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Workflow spec must be a YAML mapping")
    return payload


def _load_module_from_path(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _validate_workflow_spec(spec_path: Path):
    utilities_dir = Path(__file__).resolve().parents[2] / "utilities"
    validator_path = utilities_dir / "validate_healthview_agent_workflow_spec.py"
    module = _load_module_from_path(
        "repo_studios.scripts.utilities.validate_healthview_agent_workflow_spec",
        validator_path,
    )
    return module.validate_workflow_spec(spec_path)


def _normalize_path(path_str: str) -> str:
    return path_str.replace("\\\\", "/")


def _slugify_heading(text: str) -> str:
    """Return a GitHub-style anchor slug for a markdown heading.

    This implementation matches the anchor scheme already used across the HealthView
    Tier-2 roster docs (for example: ``Record — collect_test_log_reports.py`` becomes
    ``record--collect_test_log_reportspy``).

    Key behaviors:
    - lowercase
    - keep ASCII letters/digits, hyphen, underscore
    - convert spaces to hyphens (does not collapse repeated hyphens)
    - drop other punctuation/symbols (including unicode dashes and periods)
    """

    value = text.strip().lower().replace("`", "")
    out: list[str] = []
    for ch in value:
        if "a" <= ch <= "z" or "0" <= ch <= "9" or ch in {"-", "_"}:
            out.append(ch)
        elif ch.isspace():
            out.append("-")
        else:
            # Drop punctuation/symbols to mirror the existing doc anchor scheme.
            continue
    return "".join(out).strip("-")


def _extract_markdown_anchors(markdown_text: str) -> set[str]:
    anchors: list[str] = []

    in_fence = False
    fence_delim = ""
    for line in markdown_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            delim = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_delim = delim
            else:
                in_fence = False
                fence_delim = ""
            continue
        if in_fence:
            continue

        html_match = HTML_ANCHOR_PATTERN.search(line)
        if html_match:
            anchors.append(html_match.group("id"))

        match = MARKDOWN_HEADING_PATTERN.match(line)
        if not match:
            continue
        heading = match.group("text")
        base = _slugify_heading(heading)
        if not base:
            continue
        anchors.append(base)

    # Apply GitHub-style de-dup suffixes: -1, -2, ...
    resolved: set[str] = set()
    counts: dict[str, int] = {}
    for item in anchors:
        n = counts.get(item, 0)
        counts[item] = n + 1
        resolved.add(item if n == 0 else f"{item}-{n}")
    return resolved


def _verify_anchor_exists(*, file_path: Path, anchor: str) -> bool:
    if not anchor:
        return False
    if not file_path.exists():
        return False
    text = file_path.read_text(encoding="utf-8")
    anchors = _extract_markdown_anchors(text)
    return anchor in anchors


def parse_stage_key(*, heading_h2: str, heading_h3: str, heading_h4: str) -> StageKey | None:
    # Prefer the most specific heading first.
    for heading in (heading_h4, heading_h3, heading_h2):
        match = STAGE_PATTERN.search(heading or "")
        if not match:
            continue
        main = int(match.group("main"))
        sub_raw = match.group("sub")
        sub = int(sub_raw) if sub_raw is not None else None
        return StageKey(main=main, sub=sub)
    return None


def classify_tier1_kind(text: str) -> str:
    if "pending until Tier-2 DONE is checked" in text:
        return "tier1_script_pending"
    if "Stop-gates" in text or "Base package complete" in text or "No pointer artifacts" in text:
        return "tier1_stop_gate"
    return "other"


def extract_tier2_link(text: str, *, prefer_prefixes: list[str], require_anchor: bool) -> str | None:
    links = MARKDOWN_LINK_PATTERN.findall(text)
    if not links:
        return None

    def score(link: str) -> int:
        link_norm = _normalize_path(link)
        for idx, prefix in enumerate(prefer_prefixes):
            if link_norm.startswith(prefix):
                return 1000 - idx
        return 0

    ranked = sorted(links, key=score, reverse=True)
    for link in ranked:
        link_norm = _normalize_path(link)
        if require_anchor and "#" not in link_norm:
            continue
        return link_norm
    return None


def is_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.search(text))


def read_checkbox_csv(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def select_next_candidate(spec: dict[str, Any], *, repo_root: Path) -> CheckboxCandidate:
    inputs = spec["inputs"]
    selection = spec["selection"]
    mapping = spec["mapping"]

    csv_path = repo_root / inputs["checkbox_report_csv"]
    if not csv_path.exists():
        raise RuntimeError(f"checkbox_report.csv not found: {csv_path}")

    tier1_gate_files = {_normalize_path(item) for item in inputs["tier1_gate_files"]}
    kind_priority = list(selection["kind_priority"])
    kind_rank = {kind: idx for idx, kind in enumerate(kind_priority)}

    rows = read_checkbox_csv(csv_path)
    candidates: list[CheckboxCandidate] = []

    for row in rows:
        file_path = _normalize_path(row.get("file_path", ""))
        if file_path not in tier1_gate_files:
            continue

        checkbox_text = row.get("checkbox_text", "")
        if selection["filters"].get("exclude_placeholders") and is_placeholder(checkbox_text):
            continue

        stage = parse_stage_key(
            heading_h2=row.get("heading_h2", ""),
            heading_h3=row.get("heading_h3", ""),
            heading_h4=row.get("heading_h4", ""),
        )
        if stage is None:
            continue

        kind = classify_tier1_kind(checkbox_text)
        tier2_link = None
        if selection["filters"].get("require_tier2_link"):
            tier2_link = extract_tier2_link(
                checkbox_text,
                prefer_prefixes=list(mapping["prefer_link_path_prefixes"]),
                require_anchor=bool(mapping["require_link_anchor"]),
            )
            if tier2_link is None:
                continue

        line_number = int(row.get("line_number", "0") or 0)
        candidates.append(
            CheckboxCandidate(
                file_path=file_path,
                line_number=line_number,
                heading_h1=row.get("heading_h1", ""),
                heading_h2=row.get("heading_h2", ""),
                heading_h3=row.get("heading_h3", ""),
                heading_h4=row.get("heading_h4", ""),
                checkbox_text=checkbox_text,
                kind=kind,
                stage=stage,
                tier2_link=tier2_link or "",
            )
        )

    if not candidates:
        raise RuntimeError("No Tier-1 checkbox candidates found (filters may be too strict)")

    def sort_key(item: CheckboxCandidate) -> tuple[tuple[int, int], int, int]:
        return (
            item.stage.sort_key(),
            kind_rank.get(item.kind, len(kind_rank) + 1),
            item.line_number,
        )

    candidates.sort(key=sort_key)
    return candidates[0]


def resolve_tier2_target(
    candidate: CheckboxCandidate,
    *,
    repo_root: Path,
    verify_anchor: bool,
) -> dict[str, str]:
    link = candidate.tier2_link
    path_part, _, anchor = link.partition("#")
    tier1_dir = (repo_root / candidate.file_path).parent
    target_path = Path(path_part)
    if not target_path.is_absolute():
        if path_part.startswith(".repo_studios/"):
            resolved = repo_root / path_part
        else:
            resolved = tier1_dir / path_part
    else:
        resolved = target_path
    resolved = resolved.resolve()

    try:
        resolved_rel = resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        resolved_rel = resolved.as_posix()

    verification = "not_performed"
    if verify_anchor:
        if _verify_anchor_exists(file_path=resolved, anchor=anchor):
            verification = "verified"
        else:
            verification = "missing"

    return {
        "link": link,
        "file_path": resolved_rel,
        "anchor": anchor,
        "anchor_verification": verification,
    }


def build_action_packet(spec_path: Path, candidate: CheckboxCandidate, tier2_target: dict[str, str], spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow_spec": spec_path.as_posix(),
        "selected_tier1_checkbox": {
            **asdict(candidate),
            "stage": candidate.stage.label,
        },
        "tier2_target": tier2_target,
        "workflow": {
            "start_step": "step_0_select_work",
            "approval_gates": list(spec.get("approval_gates", {}).get("require_user_approval_for", [])),
            "deliverables": list(spec.get("deliverable_each_iteration", [])),
        },
        "post_iteration": {
            "run_doc_index": bool(spec.get("post_iteration", {}).get("run_doc_index")),
            "doc_index_command": list(spec.get("inputs", {}).get("doc_index_command", [])),
        },
    }


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    _configure_logging(args.log_level)

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    spec_path = args.spec
    if not spec_path.is_absolute():
        spec_path = (repo_root / spec_path).resolve()

    validation = _validate_workflow_spec(spec_path)
    if not validation.ok:
        raise RuntimeError("Invalid workflow spec: " + "; ".join(validation.errors))

    spec = load_yaml(spec_path)
    candidate = select_next_candidate(spec, repo_root=repo_root)
    tier2_target = resolve_tier2_target(candidate, repo_root=repo_root, verify_anchor=args.verify_anchors)
    if args.verify_anchors and tier2_target.get("anchor_verification") != "verified":
        raise RuntimeError(
            "Tier-2 anchor verification failed: "
            + f"{tier2_target.get('file_path')}#{tier2_target.get('anchor')}"
        )
    packet = build_action_packet(spec_path, candidate, tier2_target, spec)
    return packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit the next HealthView Tier-1 checkbox candidate action packet"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(
            ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml"
        ),
        help="Workflow spec path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: %(default)s)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print only Tier-1 file+line and Tier-2 link",
    )
    parser.add_argument(
        "--verify-anchors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verify the Tier-2 markdown anchor exists in the linked file (default: true)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = run(argv)
    if args.compact:
        selected = packet["selected_tier1_checkbox"]
        tier2 = packet["tier2_target"]
        print(f"tier1={selected['file_path']}:{selected['line_number']}")
        print(f"tier2={tier2['link']}")
        return 0

    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
