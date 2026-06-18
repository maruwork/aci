from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from aci.aci_cli import _handle_catalog_command
from aci.aci_config import AciCliConfig
import aci.aci_installed_package_verification as verify


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_catalog_handler_skips_output_format_for_non_catalog_commands() -> None:
    args = SimpleNamespace(command="installed-package-check")

    assert _handle_catalog_command(args, AciCliConfig()) is None


def test_editable_install_checks_cover_report_helper_and_analyzer_asset() -> None:
    checks = {item["check"]: item for item in verify._editable_install_checks(REPO_ROOT)}

    assert checks["editable_import.aci_github_summary"]["ok"] is True
    assert checks["editable_import.analyzer_asset"]["ok"] is True


def test_built_contract_checks_cover_analyzer_rule_and_report_helper_module() -> None:
    checks = {item["check"]: item for item in verify._built_artifact_contract_checks(REPO_ROOT)}

    assert checks["built_contract.analyzer_asset_rule"]["ok"] is True
    assert checks["built_contract.report_helper_module"]["ok"] is True


def test_built_contract_checks_installed_distribution_branch_covers_assets_and_helper(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured_distribution_names: list[str] = []
    fake_dist = SimpleNamespace(
        entry_points=[
            SimpleNamespace(group="console_scripts", name="aci", value="aci.aci_cli:main"),
        ],
        files=[
            "aci/aci_github_summary.py",
            "aci/package_assets/analyzers/aci-semgrep-rules.yml",
            "aci/package_assets/fixtures/expected_smoke_contract.json",
            "aci/package_assets/report/examples/aci-core-sample-report.json",
            "aci/package_assets/report/examples/aci-core-sample-report.md",
        ],
    )
    monkeypatch.setattr(
        verify.importlib.metadata,
        "packages_distributions",
        lambda: {"aci": ["ac-inspector"]},
    )
    monkeypatch.setattr(
        verify.importlib.metadata,
        "distribution",
        lambda name: captured_distribution_names.append(name) or fake_dist,
    )

    checks = {item["check"]: item for item in verify._built_artifact_contract_checks(tmp_path)}

    assert captured_distribution_names == ["ac-inspector"]
    assert checks["built_contract.cli_entrypoint"]["ok"] is True
    assert checks["built_contract.fixture_asset_rule"]["ok"] is True
    assert checks["built_contract.report_asset_rule"]["ok"] is True
    assert checks["built_contract.analyzer_asset_rule"]["ok"] is True
    assert checks["built_contract.report_helper_module"]["ok"] is True


def test_release_gate_checks_fall_back_to_installed_metadata(monkeypatch, tmp_path: Path) -> None:
    fake_package_module = SimpleNamespace(__version__="0.1.7")
    fake_scan_module = SimpleNamespace(ACI_TOOL_VERSION="0.1.7")
    real_import_module = verify.importlib.import_module
    version_calls: list[str] = []

    def _fake_import_module(name: str):
        if name == "aci":
            return fake_package_module
        if name == "aci.aci_scan":
            return fake_scan_module
        return real_import_module(name)

    monkeypatch.setattr(verify.importlib, "import_module", _fake_import_module)
    monkeypatch.setattr(
        verify.importlib.metadata,
        "packages_distributions",
        lambda: {"aci": ["ac-inspector"]},
    )
    monkeypatch.setattr(
        verify.importlib.metadata,
        "version",
        lambda name: version_calls.append(name) or "0.1.7",
    )

    check = verify._release_version_consistency_check(tmp_path)

    assert version_calls == ["ac-inspector"]
    assert check["ok"] is True
