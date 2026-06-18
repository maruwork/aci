from __future__ import annotations

from pathlib import Path
from typing import cast

from aci.aci_profiles import PROFILE_SELF_AUDIT
from aci.aci_scan import scan_target, SCOPE_MODE_SELF_AUDIT
from aci.aci_self_audit_verification import (
    _tracked_expected_classifications,
    run_self_audit_check,
)
from shared.tests._aci_test_helpers import write_fixture as _write


REPO_ROOT = Path(__file__).resolve().parents[2]


def _snapshot_targets(report: dict[str, object]) -> dict[str, object]:
    findings_rows = cast("list[dict[str, object]]", report["findings"])
    scope_rules = cast("dict[str, object]", report["scope_rules"])
    summary = cast("dict[str, object]", report["summary"])
    findings = sorted(
        (item["target_file"], item["scope_class"])
        for item in findings_rows
        if isinstance(item, dict)
    )
    return {
        "scope_mode": scope_rules["scope_mode"],
        "include_paths": scope_rules["include_paths"],
        "exclude_paths": scope_rules["exclude_paths"],
        "targets": findings,
        "by_scope_class": summary["by_scope_class"],
    }


def test_self_audit_scope_mode_snapshots_are_stable(tmp_path: Path) -> None:
    _write(tmp_path / ".aciignore", "archive\ncommon\nworkspace\n")
    _write(tmp_path / "shared" / "python" / "runtime.py", "# TODO: runtime\n")
    _write(tmp_path / "shared" / "tests" / "test_runtime.py", "# TODO: test\n")
    _write(tmp_path / "shared" / "tools" / "aci_recall_probe.py", 'URL = "http://api.acme-corp.com/v1"\n')
    _write(tmp_path / "docs" / "roadmap" / "evidence.md", "See http://api.acme-corp.com/v1\n")
    _write(tmp_path / "docs" / "guide.md", "Guide URL: http://api.acme-corp.com/v1/docs\n")
    _write(tmp_path / "examples" / "fixture.py", "# TODO: fixture\n")
    _write(tmp_path / "archive" / "old.py", "# TODO: archive\n")
    _write(tmp_path / "common" / "template.py", "# TODO: common\n")
    _write(tmp_path / "workspace" / "scratch.py", "# TODO: workspace\n")

    snapshots = {
        "source-only": _snapshot_targets(
            scan_target(
                tmp_path,
                "full",
                "core-only",
                include_external_analyzers=False,
                scope_mode="source-only",
            )
        ),
        "dogfood": _snapshot_targets(
            scan_target(
                tmp_path,
                "full",
                "core-only",
                include_external_analyzers=False,
                scope_mode="dogfood",
            )
        ),
        "full-repo": _snapshot_targets(
            scan_target(
                tmp_path,
                "full",
                "core-only",
                include_external_analyzers=False,
                scope_mode="full-repo",
            )
        ),
        "self-audit": _snapshot_targets(
            scan_target(
                tmp_path,
                PROFILE_SELF_AUDIT,
                "core-only",
                include_external_analyzers=False,
                scope_mode=SCOPE_MODE_SELF_AUDIT,
            )
        ),
    }

    assert snapshots == {
        "source-only": {
            "scope_mode": "source-only",
            "include_paths": [],
            "exclude_paths": [
                "archive",
                "common",
                "docs",
                "examples",
                "shared/tests",
                "shared/tools",
                "workspace",
            ],
            "targets": [("shared/python/runtime.py", "runtime-source")],
            "by_scope_class": {"runtime-source": 1},
        },
        "dogfood": {
            "scope_mode": "dogfood",
            "include_paths": ["shared/python", "shared/tests"],
            "exclude_paths": ["archive", "common", "docs", "examples", "workspace"],
            "targets": [
                ("shared/python/runtime.py", "runtime-source"),
                ("shared/tests/test_runtime.py", "tests"),
            ],
            "by_scope_class": {"runtime-source": 1, "tests": 1},
        },
        "full-repo": {
            "scope_mode": "full-repo",
            "include_paths": [],
            "exclude_paths": [],
            "targets": [
                ("examples/fixture.py", "fixtures"),
                ("shared/python/runtime.py", "runtime-source"),
                ("shared/tests/test_runtime.py", "tests"),
            ],
            "by_scope_class": {
                "fixtures": 1,
                "runtime-source": 1,
                "tests": 1,
            },
        },
        "self-audit": {
            "scope_mode": "self-audit",
            "include_paths": ["shared/python", "shared/tests", "shared/tools", "docs/roadmap"],
            "exclude_paths": [],
            "targets": [
                ("shared/python/runtime.py", "runtime-source"),
                ("shared/tests/test_runtime.py", "tests"),
            ],
            "by_scope_class": {
                "runtime-source": 1,
                "tests": 1,
            },
        },
    }


def test_self_audit_check_passes_for_repo() -> None:
    result = run_self_audit_check(REPO_ROOT)
    checks = {
        cast("str", item["check"]): item
        for item in cast("list[dict[str, object]]", result["checks"])
    }

    assert result["ok"] is True
    assert result["command"] == "self-audit-check"
    assert checks["self_audit.profile_registered"]["ok"] is True
    assert checks["self_audit.required_ignore_patterns"]["ok"] is True
    assert checks["classification.shared/tools/aci_recall_probe.py"]["actual"] == "maintainer-probes"

    for relative_path, expected_scope_class in _tracked_expected_classifications(REPO_ROOT):
        assert checks[f"classification.{relative_path}"]["actual"] == expected_scope_class
