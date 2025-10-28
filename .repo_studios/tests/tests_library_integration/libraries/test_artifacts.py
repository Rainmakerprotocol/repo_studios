from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

SCRIPTS_ROOT = (
    Path(__file__).resolve().parents[4]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - test fallback for path issues
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


copy_latest_artifact = _load_libraries().copy_latest_artifact


def test_copy_latest_artifact_creates_link(tmp_path: Path) -> None:
    src = tmp_path / "source.json"
    dest = tmp_path / "dest.json"
    content = "{\"value\": 1}"
    src.write_text(content, encoding="utf-8")

    copy_latest_artifact(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == content


def test_copy_latest_artifact_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "source.json"
    dest = tmp_path / "dest.json"
    src.write_text("payload", encoding="utf-8")
    dest.write_text("stale", encoding="utf-8")

    def _raise_oserror(self: Path, target: Path) -> None:  # pragma: no cover - exercised via test
        raise OSError("link not permitted")

    monkeypatch.setattr(Path, "hardlink_to", _raise_oserror, raising=False)

    copy_latest_artifact(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "payload"
