from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from command_center.scripts.orchestrators import run_standards_integrity as orchestrator


def _arg_value(argv: list[str], option: str, default: Path) -> Path:
    if option in argv:
        try:
            return Path(argv[argv.index(option) + 1])
        except (ValueError, IndexError):  # pragma: no cover - defensive fallback
            return default
    return default


def _build_args(
    *,
    repo_root: Path,
    index_output_dir: Path,
    gap_output_dir: Path,
    diff_output_dir: Path,
    prompt_output_dir: Path,
    pending_path: Path,
    categories_path: Path,
    healthview_root: Path,
    timestamp: str,
) -> list[str]:
    return [
        "--repo-root",
        str(repo_root),
        "--index-output-dir",
        str(index_output_dir),
        "--index-path",
        str(index_output_dir / "latest_index.yaml"),
        "--categories-path",
        str(categories_path),
        "--gap-output-dir",
        str(gap_output_dir),
        "--diff-output-dir",
        str(diff_output_dir),
        "--prompt-output-dir",
        str(prompt_output_dir),
        "--pending-path",
        str(pending_path),
        "--healthview-root",
        str(healthview_root),
        "--artifacts-to-keep",
        "2",
        "--index-artifacts-to-keep",
        "2",
        "--gap-artifacts-to-keep",
        "2",
        "--prompt-artifacts-to-keep",
        "2",
        "--timestamp",
        timestamp,
        "--log-level",
        "DEBUG",
    ]


@contextmanager
def _patched_loader(
    repo_root: Path,
    index_output_dir: Path,
    gap_output_dir: Path,
    prompt_output_dir: Path,
):
    original_loader = orchestrator._load_callable

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        resolved = script_path.resolve()

        if resolved == (repo_root / orchestrator.GENERATE_SCRIPT).resolve():
            def _fake_generate(argv: list[str] | None = None) -> int:
                argv_list = argv or []
                output_dir = _arg_value(argv_list, "--output-dir", index_output_dir)
                index_path = _arg_value(argv_list, "--index-path", index_output_dir / "latest_index.yaml")
                output_dir.mkdir(parents=True, exist_ok=True)
                slug = "20240102_120000"
                run_dir = output_dir / f"{orchestrator.INDEX_RUN_PREFIX}{slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "report.json").write_text(
                    json.dumps({"summary": {"rule_count": 123}, "status": "ok"}),
                    encoding="utf-8",
                )
                latest_payload = {
                    "timestamp": slug,
                    "status": "ok",
                    "summary": {"rule_count": 123},
                    "integrity_hash": "hash-123",
                }
                (output_dir / "latest_report.json").write_text(
                    json.dumps(latest_payload),
                    encoding="utf-8",
                )
                index_path.parent.mkdir(parents=True, exist_ok=True)
                index_path.write_text("rules: []\n", encoding="utf-8")
                return 0

            return _fake_generate

        if resolved == (repo_root / orchestrator.GAP_SCRIPT).resolve():
            def _fake_gap(argv: list[str] | None = None) -> dict[str, object]:
                argv_list = argv or []
                output_dir = _arg_value(argv_list, "--output-dir", gap_output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                run_dir = output_dir / "commandview" / "standards_index_gaps" / "20240102-1200"
                run_dir.mkdir(parents=True, exist_ok=True)

                manifest_path = run_dir / "manifest.json"
                manifest_path.write_text(
                    json.dumps({"viewer_slug": "commandview", "topic": "standards_index_gaps"}),
                    encoding="utf-8",
                )
                summary_md = run_dir / "summary.md"
                summary_md.write_text("# Standards Index Gaps\n", encoding="utf-8")
                telemetry_path = run_dir / "telemetry.json"
                telemetry_path.write_text(
                    json.dumps(
                        {
                            "viewer_slug": "commandview",
                            "topic": "standards_index_gaps",
                            "metrics": {"total_candidates": 3, "sources_with_candidates": 2},
                        }
                    ),
                    encoding="utf-8",
                )
                return {
                    "run_dir": str(run_dir),
                    "manifest_json": str(manifest_path),
                    "summary_md": str(summary_md),
                    "telemetry_json": str(telemetry_path),
                    "summary": {"total_candidates": 3, "sources_with_candidates": 2},
                }

            return _fake_gap

        if resolved == (repo_root / orchestrator.PROMPT_SCRIPT).resolve():
            def _fake_prompt(argv: list[str] | None = None) -> dict[str, object]:
                argv_list = argv or []
                output_dir = _arg_value(argv_list, "--output-dir", prompt_output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                run_dir = output_dir / "standards_prompt_seed-20240102_1200"
                run_dir.mkdir(parents=True, exist_ok=True)
                return {
                    "run_id": run_dir.name,
                    "status": "ok",
                    "summary": {"total_rules": 5, "category_count": 2},
                }

            return _fake_prompt

        if resolved == (repo_root / orchestrator.SUMMARY_SCRIPT).resolve():
            def _fake_summarize(*_args, **_kwargs) -> int:
                return 0

            return _fake_summarize

        return original_loader(script_path, module_name, attribute)

    orchestrator._load_callable = _fake_loader
    try:
        yield
    finally:
        orchestrator._load_callable = original_loader

def test_orchestrator_emits_healthview_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    index_output_dir = tmp_path / "index"
    gap_output_dir = tmp_path / "gap"
    diff_output_dir = tmp_path / "diff"
    prompt_output_dir = tmp_path / "prompts"
    healthview_root = tmp_path / "healthview"
    pending_path = tmp_path / "pending.yaml"
    pending_path.write_text("- item: test\n", encoding="utf-8")

    categories_path = (
        repo_root / ".repo_studios/scripts/.repo_studios/standards_categories.yaml"
    )

    args = _build_args(
        repo_root=repo_root,
        index_output_dir=index_output_dir,
        gap_output_dir=gap_output_dir,
        diff_output_dir=diff_output_dir,
        prompt_output_dir=prompt_output_dir,
        pending_path=pending_path,
        categories_path=categories_path,
        healthview_root=healthview_root,
        timestamp="2024-01-02T12:00:00+00:00",
    )

    with _patched_loader(repo_root, index_output_dir, gap_output_dir, prompt_output_dir):
        exit_code = orchestrator.run(args)

    assert exit_code == 0

    manifest_paths = list(healthview_root.glob("healthview/standards_integrity/*/manifest.json"))
    assert manifest_paths
    manifest_path = manifest_paths[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "standards_integrity"

    telemetry_steps = {step["name"]: step for step in manifest["telemetry"]["steps"]}
    assert telemetry_steps["index"]["status"] == "success"
    assert telemetry_steps["gap"]["status"] == "success"
    assert telemetry_steps["diff"]["status"] == "skipped"
    assert telemetry_steps["prompts"]["status"] == "success"
    assert telemetry_steps["summary"]["status"] == "success"

    summary_path = manifest_path.with_name("summary.md")
    assert summary_path.exists()
    summary_content = summary_path.read_text(encoding="utf-8")
    assert "# Standards Integrity Summary" in summary_content
    assert "pipeline_status" in summary_content

    telemetry_path = manifest_path.with_name("telemetry.json")
    assert telemetry_path.exists()

    artifacts_section = manifest["artifacts"]
    assert artifacts_section["index_report"].endswith("report.json")
    assert artifacts_section["gap_manifest"].endswith("manifest.json")
    assert artifacts_section["gap_summary_md"].endswith("summary.md")
    assert artifacts_section["gap_telemetry"].endswith("telemetry.json")
    assert artifacts_section["prompt_run"].endswith("standards_prompt_seed-20240102_1200")


def test_orchestrator_fails_on_invalid_topic_alias(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    index_output_dir = tmp_path / "index"
    gap_output_dir = tmp_path / "gap"
    diff_output_dir = tmp_path / "diff"
    prompt_output_dir = tmp_path / "prompts"
    healthview_root = tmp_path / "healthview"
    pending_path = tmp_path / "pending.yaml"
    pending_path.write_text("- item: test\n", encoding="utf-8")

    categories_path = (
        repo_root / ".repo_studios/scripts/.repo_studios/standards_categories.yaml"
    )

    alias_dir = healthview_root / "healthview" / "standards_integrity"
    alias_dir.mkdir(parents=True, exist_ok=True)
    (alias_dir / "latest_manifest.json").write_text("{}", encoding="utf-8")

    args = _build_args(
        repo_root=repo_root,
        index_output_dir=index_output_dir,
        gap_output_dir=gap_output_dir,
        diff_output_dir=diff_output_dir,
        prompt_output_dir=prompt_output_dir,
        pending_path=pending_path,
        categories_path=categories_path,
        healthview_root=healthview_root,
        timestamp="2024-01-03T12:00:00+00:00",
    )

    with _patched_loader(repo_root, index_output_dir, gap_output_dir, prompt_output_dir):
        exit_code = orchestrator.run(args)

    assert exit_code == 1
    assert (alias_dir / "latest_manifest.json").exists()
