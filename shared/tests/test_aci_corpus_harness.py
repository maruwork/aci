"""Smoke test for the corpus precision harness (P1-6).

Guards the harness aggregation contract against breakage. It does not measure
precision (that needs a real corpus + human labeling); it only asserts that
scan_corpus aggregates per-CI-ID counts, file sets, and bounded samples.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HARNESS = Path(__file__).parent.parent / "tools" / "aci_corpus_harness.py"
_spec = importlib.util.spec_from_file_location("aci_corpus_harness", _HARNESS)
assert _spec and _spec.loader
harness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(harness)


def test_scan_corpus_aggregates_per_ci_id(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    # A broad except -> CI-21; an unused-looking magic constant repeated is not
    # enough for cross-file detectors with one file, so keep it to a native
    # single-file signal we know fires.
    (proj / "m.py").write_text(
        "def load(p):\n"
        "    try:\n"
        "        return open(p).read()\n"
        "    except Exception:\n"
        "        return None\n",
        encoding="utf-8",
    )

    result = harness.scan_corpus([proj], samples=3)

    assert result["total_findings"] >= 1
    assert result["projects"][0]["path"].endswith("proj")
    assert "CI-21" in result["per_ci_id"], result["per_ci_id"].keys()
    ci21 = result["per_ci_id"]["CI-21"]
    assert ci21["count"] >= 1
    assert ci21["files_affected"] >= 1
    assert len(ci21["samples"]) <= 3
    assert ci21["samples"][0]["signal"].startswith("CI21_")


def test_scan_corpus_clean_project_has_no_findings(tmp_path: Path) -> None:
    proj = tmp_path / "clean"
    proj.mkdir()
    (proj / "ok.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")

    result = harness.scan_corpus([proj], samples=5)
    assert result["total_findings"] == 0
    assert result["per_ci_id"] == {}


def test_to_markdown_renders_table(tmp_path: Path) -> None:
    proj = tmp_path / "p"
    proj.mkdir()
    (proj / "m.py").write_text(
        "def f(p):\n    try:\n        return open(p).read()\n    except Exception:\n        return None\n",
        encoding="utf-8",
    )
    md = harness.to_markdown(harness.scan_corpus([proj], samples=2))
    assert "# ACI Corpus Precision Baseline" in md
    assert "Per-CI-ID density" in md


def test_scan_corpus_can_include_flat_findings_for_labeling(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "m.py").write_text(
        "def load(p):\n"
        "    try:\n"
        "        return open(p).read()\n"
        "    except Exception:\n"
        "        return None\n",
        encoding="utf-8",
    )

    result = harness.scan_corpus([proj], samples=2, include_findings=True)

    findings = result["findings"]
    assert isinstance(findings, list)
    assert findings
    first = findings[0]
    assert first["project"].endswith("proj")
    assert first["fingerprint"]
    assert first["ci_id"] == "CI-21"


def test_scan_corpus_source_only_ignores_docs_noise_by_default(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    docs = proj / "docs"
    docs.mkdir()
    (docs / "note.py").write_text("# TODO: docs reminder\n", encoding="utf-8")

    result = harness.scan_corpus([proj], samples=2)

    assert result["scope_mode"] == "source-only"
    assert result["total_findings"] == 0


def test_scan_corpus_full_repo_can_include_docs_noise_when_requested(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    docs = proj / "docs"
    docs.mkdir()
    (docs / "note.py").write_text("# TODO: docs reminder\n", encoding="utf-8")

    result = harness.scan_corpus([proj], samples=2, scope_mode="full-repo")

    assert result["scope_mode"] == "full-repo"
    assert result["total_findings"] >= 1
    assert "CI-03" in result["per_ci_id"]


def test_scan_corpus_passes_exclude_paths_through_to_scan_target(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    app = proj / "app"
    app.mkdir()
    tests = proj / "tests"
    tests.mkdir()
    (app / "bad.py").write_text("def load(p):\n    try:\n        return open(p).read()\n    except Exception:\n        return None\n", encoding="utf-8")
    (tests / "todo.py").write_text("# TODO: noisy support file\n", encoding="utf-8")

    result = harness.scan_corpus([proj], samples=5, scope_mode="full-repo", exclude_paths=("tests",))

    assert result["exclude_paths"] == ["tests"]
    assert "CI-03" not in result["per_ci_id"]
    assert "CI-21" in result["per_ci_id"]
