#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture owner-gated hosted/publication evidence for ACI release readiness."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
from pathlib import Path
import subprocess
import tomllib
from typing import Any
from urllib import error, request


def _detect_repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "README.md").exists():
            return candidate
    raise RuntimeError("Could not detect repository root")


def _read_project_metadata(repo_root: Path) -> dict[str, str]:
    data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    return {
        "distribution_name": str(project.get("name") or "aci"),
        "version": str(project.get("version") or "0.0.0"),
    }


def _run_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _normalize_remote_slug(remote_url: str) -> str | None:
    cleaned = remote_url.strip()
    for pattern in (
        r"github\.com[:/](?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$",
        r"^https://github\.com/(?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$",
    ):
        match = re.search(pattern, cleaned)
        if match:
            return str(match.group("slug"))
    return None


def _detect_origin_slug(repo_root: Path) -> str:
    completed = _run_command(["git", "remote", "get-url", "origin"], repo_root)
    if completed.returncode != 0:
        raise RuntimeError(f"git remote get-url origin failed: {completed.stderr.strip() or completed.stdout.strip()}")
    slug = _normalize_remote_slug(completed.stdout)
    if not slug:
        raise RuntimeError(f"Could not parse GitHub slug from origin URL: {completed.stdout.strip()}")
    return slug


def _git_tags(repo_root: Path) -> list[str]:
    completed = _run_command(["git", "tag"], repo_root)
    if completed.returncode != 0:
        raise RuntimeError(f"git tag failed: {completed.stderr.strip() or completed.stdout.strip()}")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


@dataclass(frozen=True)
class HttpLikeResult:
    status_code: int | None
    ok: bool
    body: str
    json_body: dict[str, Any] | list[Any] | None
    error_summary: str | None


def _try_json_loads(text: str) -> dict[str, Any] | list[Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if isinstance(value, (dict, list)):
        return value
    return None


def _parse_httpish_output(output: str) -> HttpLikeResult:
    lines = output.splitlines()
    status_code: int | None = None
    body_lines: list[str] = []
    body_started = False

    for line in lines:
        if status_code is None:
            match = re.match(r"HTTP/\S+\s+(\d{3})", line.strip())
            if match:
                status_code = int(match.group(1))
                continue
        if status_code is not None and not body_started and line.strip() == "":
            body_started = True
            continue
        if body_started:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    json_body = _try_json_loads(body)
    ok = status_code is not None and 200 <= status_code < 300
    error_summary: str | None = None
    if not ok:
        if isinstance(json_body, dict) and isinstance(json_body.get("message"), str):
            error_summary = str(json_body["message"])
        elif body:
            error_summary = body.splitlines()[0]
    return HttpLikeResult(
        status_code=status_code,
        ok=ok,
        body=body,
        json_body=json_body,
        error_summary=error_summary,
    )


def _gh_api(repo_root: Path, endpoint: str, *, include_headers: bool = False) -> HttpLikeResult:
    args = ["gh", "api", endpoint]
    if include_headers:
        args.append("-i")
    completed = _run_command(args, repo_root)
    output = completed.stdout if completed.stdout.strip() else completed.stderr
    if include_headers:
        return _parse_httpish_output(output)
    json_body = _try_json_loads(output)
    if completed.returncode != 0:
        error_summary = completed.stderr.strip() or completed.stdout.strip()
        return HttpLikeResult(None, False, output.strip(), json_body, error_summary or None)
    return HttpLikeResult(200, True, output.strip(), json_body, None)


def _fetch_pypi_project(package_name: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = request.Request(url, headers={"User-Agent": "aci-owner-release-state/1.0"})
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {
                "url": url,
                "status_code": response.status,
                "exists": True,
                "project_name": str(payload.get("info", {}).get("name") or package_name),
                "latest_version": str(payload.get("info", {}).get("version") or ""),
            }
    except error.HTTPError as exc:
        if exc.code == 404:
            return {
                "url": url,
                "status_code": 404,
                "exists": False,
                "project_name": package_name,
                "latest_version": None,
            }
        raise
    except error.URLError as exc:
        return {
            "url": url,
            "status_code": None,
            "exists": None,
            "project_name": package_name,
            "latest_version": None,
            "error_summary": str(exc.reason),
        }


def _release_blockers(snapshot: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    pypi_state = snapshot["pypi"]
    project = snapshot["project"]
    pypi_latest_version = pypi_state.get("latest_version")
    project_version = project.get("version")
    if pypi_state.get("exists") is False:
        blockers.append(
            f"PyPI package name '{project['distribution_name']}' is fixed but not published yet."
        )
    elif pypi_state.get("exists") and pypi_latest_version != project_version:
        blockers.append(
            f"PyPI package name '{project['distribution_name']}' exists but latest version is "
            f"'{pypi_latest_version}', not the local release version '{project_version}'."
        )
    release = snapshot["github"]["latest_release"]
    if release.get("status_code") == 404:
        blockers.append("No GitHub latest release object exists yet.")
    dependabot_open_alert_count = int(snapshot["github"]["dependabot_alerts"].get("open_alert_count") or 0)
    if dependabot_open_alert_count > 0:
        blockers.append(
            f"GitHub Dependabot still reports {dependabot_open_alert_count} open alert(s) on the hosted repository."
        )
    if snapshot["github"]["code_scanning"].get("status_code") == 403:
        blockers.append("GitHub code scanning is not enabled on the hosted repository.")
    if snapshot["github"]["secret_scanning"].get("status_code") == 404:
        blockers.append("GitHub secret scanning is disabled on the hosted repository.")
    return blockers


def _complete_when(condition: bool, *, complete: str, incomplete: str) -> dict[str, str]:
    return {
        "state": "complete" if condition else "incomplete",
        "reason": complete if condition else incomplete,
    }


def _owner_action(reason: str) -> dict[str, str]:
    return {
        "state": "owner-action-required",
        "reason": reason,
    }


def _dependabot_alert_counts(entry: dict[str, Any]) -> dict[str, int]:
    json_body = entry.get("json_body")
    if not isinstance(json_body, list):
        return {}
    counts: dict[str, int] = {}
    for alert in json_body:
        if not isinstance(alert, dict):
            continue
        state = alert.get("state")
        if not isinstance(state, str) or not state:
            continue
        counts[state] = counts.get(state, 0) + 1
    return counts


def _load_owner_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Owner evidence file must be a JSON object: {path}")
    return data


def _release_readiness(snapshot: dict[str, Any]) -> dict[str, Any]:
    github = snapshot["github"]
    pypi = snapshot["pypi"]
    project = snapshot["project"]
    owner_evidence = snapshot.get("owner_evidence", {})
    if not isinstance(owner_evidence, dict):
        owner_evidence = {}
    pypi_matches_local = pypi.get("exists") is True and pypi.get("latest_version") == project.get("version")
    trusted_publisher_registered = owner_evidence.get("trusted_publisher_registered") is True
    public_history_policy_decided = owner_evidence.get("public_history_policy_decided") is True
    dependabot_reachable = (
        github["vulnerability_alerts"].get("status_code") == 204
        and bool(github["dependabot_alerts"].get("ok"))
    )
    dependabot_open_alert_count = int(github["dependabot_alerts"].get("open_alert_count") or 0)
    item_statuses = {
        "35_trusted_publisher_oidc": _complete_when(
            trusted_publisher_registered,
            complete="Owner evidence records PyPI Trusted Publisher registration for the chosen package target.",
            incomplete="Repository-side OIDC publish workflow is wired, but PyPI Trusted Publisher registration still requires owner evidence.",
        ),
        "36_hosted_code_and_secret_scanning": _complete_when(
            bool(github["code_scanning"].get("ok")) and bool(github["secret_scanning"].get("ok")),
            complete="GitHub code scanning and secret scanning endpoints are both reachable.",
            incomplete="GitHub code scanning and/or secret scanning are not enabled on the hosted repository.",
        ),
        "37_dependabot_alerts": _complete_when(
            dependabot_reachable and dependabot_open_alert_count == 0,
            complete="Vulnerability alerts are enabled, Dependabot alerts are reachable, and no open Dependabot alerts remain.",
            incomplete=(
                "Vulnerability alerts or Dependabot alerts are not proven reachable."
                if not dependabot_reachable
                else f"Dependabot alerts remain open on the hosted repository ({dependabot_open_alert_count} open)."
            ),
        ),
        "38_public_history_policy": _complete_when(
            public_history_policy_decided,
            complete="Owner evidence records the public-history acceptance or cleanup decision.",
            incomplete="Current git history acceptance or cleanup remains an explicit owner decision.",
        ),
        "39_first_public_release": _complete_when(
            bool(github["latest_release"].get("ok")) and pypi_matches_local,
            complete="GitHub latest release exists and PyPI latest version matches the local release version.",
            incomplete="GitHub latest release is absent or PyPI latest version does not match the local release version.",
        ),
    }
    blocking_items = [
        item_id
        for item_id, item in item_statuses.items()
        if item["state"] != "complete"
    ]
    return {
        "decision": "pass" if not blocking_items else "blocked",
        "blocking_items": blocking_items,
        "item_statuses": item_statuses,
    }


def capture_owner_release_state(
    repo_root: Path,
    *,
    repo_slug: str | None = None,
    include_pypi: bool = True,
    owner_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_slug = repo_slug or _detect_origin_slug(repo_root)
    project = _read_project_metadata(repo_root)
    repo_response = _gh_api(repo_root, f"repos/{repo_slug}")
    if not isinstance(repo_response.json_body, dict):
        raise RuntimeError(f"GitHub repository lookup failed for {repo_slug}: {repo_response.error_summary or repo_response.body}")
    default_branch = str(repo_response.json_body.get("default_branch") or "main")

    dependabot_alerts = _gh_api(repo_root, f"repos/{repo_slug}/dependabot/alerts?per_page=100", include_headers=True).__dict__
    dependabot_counts = _dependabot_alert_counts(dependabot_alerts)
    dependabot_alerts["alert_counts"] = dependabot_counts
    dependabot_alerts["open_alert_count"] = dependabot_counts.get("open", 0)
    dependabot_alerts["fixed_alert_count"] = dependabot_counts.get("fixed", 0)

    snapshot: dict[str, Any] = {
        "captured_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_slug": repo_slug,
        "project": project,
        "github": {
            "repository": {
                "visibility": repo_response.json_body.get("visibility"),
                "private": repo_response.json_body.get("private"),
                "default_branch": default_branch,
                "html_url": repo_response.json_body.get("html_url"),
            },
            "vulnerability_alerts": _gh_api(repo_root, f"repos/{repo_slug}/vulnerability-alerts", include_headers=True).__dict__,
            "dependabot_alerts": dependabot_alerts,
            "code_scanning": _gh_api(repo_root, f"repos/{repo_slug}/code-scanning/alerts?per_page=1", include_headers=True).__dict__,
            "secret_scanning": _gh_api(repo_root, f"repos/{repo_slug}/secret-scanning/alerts?per_page=1", include_headers=True).__dict__,
            "branch_protection": _gh_api(repo_root, f"repos/{repo_slug}/branches/{default_branch}/protection", include_headers=True).__dict__,
            "latest_release": _gh_api(repo_root, f"repos/{repo_slug}/releases/latest", include_headers=True).__dict__,
        },
        "git": {
            "tags": _git_tags(repo_root),
        },
        "owner_evidence": owner_evidence or {},
    }
    snapshot["pypi"] = _fetch_pypi_project(project["distribution_name"]) if include_pypi else {
        "url": f"https://pypi.org/pypi/{project['distribution_name']}/json",
        "status_code": None,
        "exists": None,
        "project_name": project["distribution_name"],
        "latest_version": None,
        "skipped": True,
    }
    snapshot["external_blockers"] = _release_blockers(snapshot)
    snapshot["readiness"] = _release_readiness(snapshot)
    return snapshot


def _status_summary(entry: dict[str, Any]) -> str:
    status_code = entry.get("status_code")
    if status_code is None:
        return "unknown"
    if entry.get("ok"):
        return str(status_code)
    error_summary = entry.get("error_summary")
    return f"{status_code} ({error_summary})" if error_summary else str(status_code)


def build_markdown_summary(snapshot: dict[str, Any]) -> str:
    repository = snapshot["github"]["repository"]
    pypi_state = snapshot["pypi"]
    blockers = snapshot.get("external_blockers", [])
    owner_evidence = snapshot.get("owner_evidence", {})
    dependabot_open = snapshot["github"]["dependabot_alerts"].get("open_alert_count")
    dependabot_fixed = snapshot["github"]["dependabot_alerts"].get("fixed_alert_count")
    dependabot_suffix = ""
    if dependabot_open is not None or dependabot_fixed is not None:
        dependabot_suffix = f" (open={dependabot_open or 0}, fixed={dependabot_fixed or 0})"
    lines = [
        "# Owner-Gated Release Snapshot",
        "",
        f"- Captured at: `{snapshot['captured_at']}`",
        f"- Repository: `{snapshot['repo_slug']}`",
        f"- Distribution name: `{snapshot['project']['distribution_name']}`",
        f"- Version: `{snapshot['project']['version']}`",
        f"- Visibility: `{repository['visibility']}`",
        f"- Default branch: `{repository['default_branch']}`",
        f"- Git tags: `{', '.join(snapshot['git']['tags']) if snapshot['git']['tags'] else '(none)'}`",
        "",
        "## Hosted State",
        "",
        f"- Vulnerability alerts: `{_status_summary(snapshot['github']['vulnerability_alerts'])}`",
        f"- Dependabot alerts: `{_status_summary(snapshot['github']['dependabot_alerts'])}{dependabot_suffix}`",
        f"- Code scanning: `{_status_summary(snapshot['github']['code_scanning'])}`",
        f"- Secret scanning: `{_status_summary(snapshot['github']['secret_scanning'])}`",
        f"- Branch protection: `{_status_summary(snapshot['github']['branch_protection'])}`",
        f"- Latest release endpoint: `{_status_summary(snapshot['github']['latest_release'])}`",
        "",
        "## PyPI State",
        "",
        f"- Project URL: `{pypi_state['url']}`",
        f"- Exists: `{pypi_state.get('exists')}`",
        f"- Latest version: `{pypi_state.get('latest_version')}`",
        f"- Matches local version: `{pypi_state.get('latest_version') == snapshot['project']['version']}`",
        "",
        "## Owner Evidence",
        "",
        f"- Trusted Publisher registered: `{owner_evidence.get('trusted_publisher_registered') is True if isinstance(owner_evidence, dict) else False}`",
        f"- Public history policy decided: `{owner_evidence.get('public_history_policy_decided') is True if isinstance(owner_evidence, dict) else False}`",
        "",
        "## G8 Readiness",
        "",
        f"- Decision: `{snapshot['readiness']['decision']}`",
        f"- Blocking items: `{', '.join(snapshot['readiness']['blocking_items']) if snapshot['readiness']['blocking_items'] else '(none)'}`",
        "",
        "## External Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- none detected from the captured surfaces")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture owner-gated hosted/publication evidence for ACI.")
    parser.add_argument("--repo-slug", help="Override GitHub repo slug; defaults to origin remote parsing.")
    parser.add_argument("--skip-pypi", action="store_true", help="Skip the live PyPI project lookup.")
    parser.add_argument(
        "--owner-evidence",
        type=Path,
        help=(
            "Optional JSON object with owner-only evidence, e.g. "
            "trusted_publisher_registered and public_history_policy_decided."
        ),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("workspace") / "owner-release-state" / "owner-release-state.json",
        help="Write the captured machine-readable snapshot here.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("workspace") / "owner-release-state" / "owner-release-state.md",
        help="Write the rendered markdown summary here.",
    )
    args = parser.parse_args()

    repo_root = _detect_repo_root()
    snapshot = capture_owner_release_state(
        repo_root,
        repo_slug=args.repo_slug,
        include_pypi=not args.skip_pypi,
        owner_evidence=_load_owner_evidence(args.owner_evidence),
    )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.write_text(build_markdown_summary(snapshot), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "json_out": args.json_out.as_posix(),
        "markdown_out": args.markdown_out.as_posix(),
        "external_blockers": snapshot["external_blockers"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
