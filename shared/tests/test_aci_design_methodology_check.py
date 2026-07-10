from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "shared" / "tools" / "aci_design_methodology_check.py"
SPEC = importlib.util.spec_from_file_location("aci_design_methodology_check_tool", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_repo_ops_stack_passes() -> None:
    ok, errors, notes = mod.run_all(REPO_ROOT)
    assert ok, errors
    assert any("Gate-0 PASS" in n for n in notes)
    assert any("Gate-1 PASS" in n for n in notes)
    assert any("Seams PASS" in n for n in notes)
    assert any("Residual PASS" in n for n in notes)
    assert any("Gate-R PASS" in n for n in notes)


def test_main_exit_zero() -> None:
    assert mod.main(["--root", str(REPO_ROOT)]) == 0


def test_gate_r_closed_basic_requires_promoted_slot(tmp_path: Path) -> None:
    # Minimal failing Gate-R only (other files copied from empty fail differently)
    (tmp_path / "docs").mkdir()
    # Provide minimal stubs so we isolate Gate-R error among failures
    registry = tmp_path / "docs" / "design_base_registry.yaml"
    cats = "\n".join(
        f"  {c}:\n    state: filled\n    value: ok\n    evidence: e"
        for c in mod.gate0.REQUIRED_CATEGORIES
    )
    registry.write_text(
        f"categories:\n{cats}\npromoted_slots: {{}}\n",
        encoding="utf-8",
    )
    # Fix G.oracle for gate1
    text = registry.read_text(encoding="utf-8")
    text = text.replace(
        "  G.oracle:\n    state: filled\n    value: ok\n    evidence: e",
        "  G.oracle:\n    state: filled\n    value: machine and human judgment\n    evidence: e",
    )
    registry.write_text(text, encoding="utf-8")

    (tmp_path / "docs" / "design_seam_review.yaml").write_text(
        """
seams:
  S1: { status: residual, note: n }
  S2: { status: residual, note: n }
  S3: { status: residual, note: n }
  S4: { status: residual, note: n }
  S5: { status: na, note: n }
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "design_residuals.yaml").write_text(
        """
claimed_complete: false
statement: not complete
see: docs/design_residuals.yaml
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "design_gate_r_log.yaml").write_text(
        """
entries:
  GR-X:
    status: closed
    summary: hole
    seams: S1
    basic: "yes"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    ok, errors, _ = mod.run_all(tmp_path)
    assert not ok
    assert any("promoted_slot" in e for e in errors)
