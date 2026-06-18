from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from urllib import error


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "shared" / "tools" / "aci_capture_owner_release_state.py"
SPEC = importlib.util.spec_from_file_location("aci_capture_owner_release_state_tool", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
owner_release_state = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = owner_release_state
SPEC.loader.exec_module(owner_release_state)


def test_normalize_remote_slug_supports_https_and_ssh() -> None:
    assert owner_release_state._normalize_remote_slug("https://github.com/maruwork/aci.git") == "maruwork/aci"
    assert owner_release_state._normalize_remote_slug("git@github.com:maruwork/aci.git") == "maruwork/aci"


def test_parse_httpish_output_extracts_status_and_error_message() -> None:
    parsed = owner_release_state._parse_httpish_output(
        "HTTP/2.0 403 Forbidden\nHeader: value\n\n"
        '{"message":"Code scanning is not enabled for this repository.","status":"403"}'
    )

    assert parsed.status_code == 403
    assert parsed.ok is False
    assert parsed.error_summary == "Code scanning is not enabled for this repository."


def test_release_blockers_include_pypi_conflict_and_missing_release() -> None:
    snapshot = {
        "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
        "pypi": {"exists": True, "latest_version": "1.3"},
        "github": {
            "latest_release": {"status_code": 404},
            "code_scanning": {"status_code": 403},
            "secret_scanning": {"status_code": 404},
        },
    }

    blockers = owner_release_state._release_blockers(snapshot)

    assert "PyPI package name 'ac-inspector' exists but latest version is '1.3', not the local release version '0.1.7'." in blockers
    assert "No GitHub latest release object exists yet." in blockers
    assert "GitHub code scanning is not enabled on the hosted repository." in blockers
    assert "GitHub secret scanning is disabled on the hosted repository." in blockers


def test_release_blockers_treat_matching_pypi_version_as_release_evidence() -> None:
    snapshot = {
        "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
        "pypi": {"exists": True, "latest_version": "0.1.7"},
        "github": {
            "latest_release": {"status_code": 200},
            "code_scanning": {"status_code": 200},
            "secret_scanning": {"status_code": 200},
        },
    }

    assert owner_release_state._release_blockers(snapshot) == []


def test_release_blockers_report_fixed_package_name_not_yet_published() -> None:
    snapshot = {
        "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
        "pypi": {"exists": False, "latest_version": None},
        "github": {
            "latest_release": {"status_code": 404},
            "code_scanning": {"status_code": 200},
            "secret_scanning": {"status_code": 200},
        },
    }

    blockers = owner_release_state._release_blockers(snapshot)

    assert "PyPI package name 'ac-inspector' is fixed but not published yet." in blockers
    assert "No GitHub latest release object exists yet." in blockers


def test_release_readiness_reports_item_statuses_for_current_blockers() -> None:
    snapshot = {
        "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
        "pypi": {"exists": False, "latest_version": None},
        "github": {
            "vulnerability_alerts": {"status_code": 204, "ok": True},
            "dependabot_alerts": {"status_code": 200, "ok": True},
            "latest_release": {"status_code": 404, "ok": False},
            "code_scanning": {"status_code": 403, "ok": False},
            "secret_scanning": {"status_code": 404, "ok": False},
        },
        "owner_evidence": {},
    }

    readiness = owner_release_state._release_readiness(snapshot)

    assert readiness["decision"] == "blocked"
    assert readiness["item_statuses"]["37_dependabot_alerts"]["state"] == "complete"
    assert readiness["item_statuses"]["36_hosted_code_and_secret_scanning"]["state"] == "incomplete"
    assert readiness["item_statuses"]["39_first_public_release"]["state"] == "incomplete"
    assert readiness["item_statuses"]["35_trusted_publisher_oidc"]["state"] == "incomplete"
    assert readiness["item_statuses"]["38_public_history_policy"]["state"] == "incomplete"


def test_release_readiness_passes_when_all_snapshot_verifiable_items_and_owner_decisions_are_complete() -> None:
    snapshot = {
        "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
        "pypi": {"exists": True, "latest_version": "0.1.7"},
        "github": {
            "vulnerability_alerts": {"status_code": 204, "ok": True},
            "dependabot_alerts": {"status_code": 200, "ok": True},
            "latest_release": {"status_code": 200, "ok": True},
            "code_scanning": {"status_code": 200, "ok": True},
            "secret_scanning": {"status_code": 200, "ok": True},
        },
        "owner_evidence": {
            "trusted_publisher_registered": True,
            "public_history_policy_decided": True,
        },
    }
    readiness = owner_release_state._release_readiness(snapshot)

    assert readiness["decision"] == "pass"
    assert readiness["blocking_items"] == []


def test_load_owner_evidence_requires_json_object(tmp_path: Path) -> None:
    evidence_path = tmp_path / "owner-evidence.json"
    evidence_path.write_text('{"trusted_publisher_registered": true}', encoding="utf-8")

    assert owner_release_state._load_owner_evidence(evidence_path) == {
        "trusted_publisher_registered": True,
    }


def test_build_markdown_summary_renders_key_statuses() -> None:
    markdown = owner_release_state.build_markdown_summary(
        {
            "captured_at": "2026-06-18T03:00:00Z",
            "repo_slug": "maruwork/aci",
            "project": {"distribution_name": "ac-inspector", "version": "0.1.7"},
            "git": {"tags": ["v0.1.7"]},
            "github": {
                "repository": {"visibility": "private", "default_branch": "main"},
                "vulnerability_alerts": {"status_code": 204, "ok": True},
                "dependabot_alerts": {"status_code": 200, "ok": True},
                "code_scanning": {"status_code": 403, "ok": False, "error_summary": "disabled"},
                "secret_scanning": {"status_code": 404, "ok": False, "error_summary": "disabled"},
                "branch_protection": {"status_code": 403, "ok": False, "error_summary": "upgrade required"},
                "latest_release": {"status_code": 404, "ok": False, "error_summary": "Not Found"},
            },
            "pypi": {
                "url": "https://pypi.org/pypi/ac-inspector/json",
                "exists": False,
                "latest_version": None,
            },
            "readiness": {
                "decision": "blocked",
                "blocking_items": [
                    "35_trusted_publisher_oidc",
                    "36_hosted_code_and_secret_scanning",
                    "38_public_history_policy",
                    "39_first_public_release",
                ],
            },
            "external_blockers": ["example blocker"],
        }
    )

    assert "# Owner-Gated Release Snapshot" in markdown
    assert "- Distribution name: `ac-inspector`" in markdown
    assert "- Code scanning: `403 (disabled)`" in markdown
    assert "- Exists: `False`" in markdown
    assert "- Matches local version: `False`" in markdown
    assert "- Decision: `blocked`" in markdown
    assert "35_trusted_publisher_oidc" in markdown
    assert "- example blocker" in markdown


def test_fetch_pypi_project_tolerates_network_unavailability(monkeypatch) -> None:
    def _raise_url_error(*args, **kwargs):
        raise error.URLError("blocked")

    monkeypatch.setattr(owner_release_state.request, "urlopen", _raise_url_error)

    result = owner_release_state._fetch_pypi_project("aci")

    assert result["exists"] is None
    assert result["error_summary"] == "blocked"
