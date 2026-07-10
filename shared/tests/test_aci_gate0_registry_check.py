from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "shared" / "tools" / "aci_gate0_registry_check.py"
SPEC = importlib.util.spec_from_file_location("aci_gate0_registry_check_tool", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
gate0 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate0
SPEC.loader.exec_module(gate0)


def _write_registry(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")


def test_extract_paths_ignores_prose() -> None:
    value = (
        "see docs/NON_GOALS.md; report owner_lane (native-static); "
        "shared/report/; README.md"
    )
    paths = gate0.extract_paths(value)
    assert "docs/NON_GOALS.md" in paths
    assert "shared/report" in paths or "shared/report/" in paths
    assert "README.md" in paths
    assert not any("owner_lane" in p for p in paths)


def test_repo_registry_passes_gate0() -> None:
    registry = REPO_ROOT / "docs" / "design_base_registry.yaml"
    result = gate0.check_registry(registry, REPO_ROOT)
    assert result.ok, result.errors


def test_missing_category_fails(tmp_path: Path) -> None:
    reg = tmp_path / "docs" / "design_base_registry.yaml"
    cats = "\n".join(
        f"  {c}:\n    state: filled\n    value: ok"
        for c in gate0.REQUIRED_CATEGORIES
        if c != "G.open"
    )
    _write_registry(
        reg,
        f"""
categories:
{cats}
""",
    )
    result = gate0.check_registry(reg, tmp_path)
    assert not result.ok
    assert any("missing required categories" in e for e in result.errors)


def test_filled_missing_index_path_fails(tmp_path: Path) -> None:
    reg = tmp_path / "docs" / "design_base_registry.yaml"
    cats_lines = []
    for c in gate0.REQUIRED_CATEGORIES:
        if c == "G.goal":
            cats_lines.append(
                "  G.goal:\n    state: filled\n    value: \"see docs/missing.md\""
            )
        else:
            cats_lines.append(f"  {c}:\n    state: filled\n    value: ok-no-path")
    _write_registry(reg, "categories:\n" + "\n".join(cats_lines))
    result = gate0.check_registry(reg, tmp_path)
    assert not result.ok
    assert any("does not exist" in e for e in result.errors)


def test_na_requires_reason(tmp_path: Path) -> None:
    reg = tmp_path / "docs" / "design_base_registry.yaml"
    cats_lines = []
    for c in gate0.REQUIRED_CATEGORIES:
        if c == "G.feedback":
            cats_lines.append("  G.feedback:\n    state: na\n    reason: \"\"")
        else:
            cats_lines.append(f"  {c}:\n    state: filled\n    value: ok")
    _write_registry(reg, "categories:\n" + "\n".join(cats_lines))
    # empty reason after parse may be missing key — use explicit empty
    text = reg.read_text(encoding="utf-8").replace(
        '  G.feedback:\n    state: na\n    reason: ""',
        "  G.feedback:\n    state: na\n    reason: \"\"",
    )
    reg.write_text(text, encoding="utf-8")
    result = gate0.check_registry(reg, tmp_path)
    assert not result.ok
    assert any("na requires non-empty reason" in e for e in result.errors)


def test_deferred_expired_fails(tmp_path: Path) -> None:
    reg = tmp_path / "docs" / "design_base_registry.yaml"
    cats_lines = []
    for c in gate0.REQUIRED_CATEGORIES:
        if c == "G.open":
            cats_lines.append(
                "  G.open:\n"
                "    state: deferred\n"
                "    owner: alice\n"
                "    due: \"2020-01-01\"\n"
                "    reason: later\n"
                "    exit: decide open items"
            )
        else:
            cats_lines.append(f"  {c}:\n    state: filled\n    value: ok")
    _write_registry(reg, "categories:\n" + "\n".join(cats_lines))
    result = gate0.check_registry(reg, tmp_path, today=date(2026, 7, 10))
    assert not result.ok
    assert any("expired" in e for e in result.errors)


def test_main_exit_codes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert gate0.main(["--root", str(REPO_ROOT)]) == 0

    bad = tmp_path / "empty.yaml"
    bad.write_text("categories: {}\n", encoding="utf-8")
    assert gate0.main(["--root", str(tmp_path), "--registry", "empty.yaml"]) == 1
