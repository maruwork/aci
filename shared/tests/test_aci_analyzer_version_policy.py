from __future__ import annotations

from pathlib import Path

from aci.aci_analyzer_execution import analyzer_version_policy


REPO_ROOT = Path(__file__).resolve().parents[2]


def _requirements_specs(path: Path) -> dict[str, str]:
    specs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, version = line.partition("==")
        specs[name] = version
    return specs


def test_pinned_python_analyzer_requirements_match_version_policy() -> None:
    policy = analyzer_version_policy()
    specs = _requirements_specs(REPO_ROOT / "requirements-dev-analyzers.txt")

    assert specs == {
        "pytest": "9.0.3",
        "ruff": "0.4.8",
        "pyflakes": "3.2.0",
        "mypy": "1.10.0",
    }
    assert policy["pytest"]["install_spec"] == "pytest==9.0.3"
    assert policy["ruff"]["install_spec"] == "ruff==0.4.8"
    assert policy["pyflakes"]["install_spec"] == "pyflakes==3.2.0"
    assert policy["mypy"]["install_spec"] == "mypy==1.10.0"


def test_ci_workflow_uses_pinned_python_analyzer_requirements() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pip install -r requirements-dev-analyzers.txt" in workflow
