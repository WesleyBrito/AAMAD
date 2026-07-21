"""Fail when committed artifact bundles are stale vs source trees."""

from __future__ import annotations

import hashlib
import importlib.util
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_update_bundle():
    path = ROOT / "scripts" / "update_bundle.py"
    spec = importlib.util.spec_from_file_location("aamad_update_bundle", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _zip_fingerprint(path: Path) -> dict[str, str]:
    """Map archive member name -> sha256 of content (dirs omitted)."""
    out: dict[str, str] = {}
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            data = zf.read(info.filename)
            out[info.filename] = hashlib.sha256(data).hexdigest()
    return out


def test_cursor_bundle_is_fresh(tmp_path: Path) -> None:
    ub = _load_update_bundle()
    committed = ROOT / "src" / "aamad" / "data" / "aamad_bundle.zip"
    assert committed.is_file()
    rebuilt = ub.build_cursor_bundle(tmp_path / "aamad_bundle.zip")
    assert _zip_fingerprint(rebuilt) == _zip_fingerprint(committed), (
        "Cursor bundle is stale. Run: python3 scripts/update_bundle.py"
    )


def test_claude_bundle_is_fresh(tmp_path: Path) -> None:
    ub = _load_update_bundle()
    committed = ROOT / "src" / "aamad" / "data" / "aamad_claude_bundle.zip"
    assert committed.is_file()
    rebuilt = ub.build_claude_bundle(tmp_path / "aamad_claude_bundle.zip")
    assert _zip_fingerprint(rebuilt) == _zip_fingerprint(committed), (
        "Claude Code bundle is stale. Run: python3 scripts/update_bundle.py"
    )


def test_agents_md_includes_framework_version(tmp_path: Path) -> None:
    from aamad.installer import write_agents_md

    path = write_agents_md(tmp_path, ide="cursor", overwrite=True)
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "Framework version:" in text
    assert "@devops.eng" in text
