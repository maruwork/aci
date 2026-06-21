#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Common CLI entry for the ACI shelf."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .aci_config import AciCliConfig, config_schema, load_cli_config
    from .aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from .aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from .aci_github_summary import build_github_summary_markdown
    from .aci_report_view import (
        apply_report_view,
        SUPPORTED_REPORT_OWNER_LANES,
        SUPPORTED_REPORT_SCOPE_CLASSES,
    )
    from .aci_profiles import PROFILE_QUICK_GATE, default_scope_mode
    from .aci_scan import (
        scan_target,
        ACI_TOOL_VERSION,
        SUPPORTED_SCOPE_MODES,
        SCOPE_MODE_SOURCE_ONLY,
    )
    from .aci_annotations import build_github_annotations
    from .aci_baseline import build_baseline_operations
    from .aci_sarif import build_sarif_report
    from .aci_sarif import validate_sarif_report
    from .aci_package_assets import read_text_asset
    from .aci_installed_package_verification import run_installed_package_check
    from .aci_analyzer_execution import (
        analyzer_availability,
        analyzer_execution_support_levels,
        profile_execution_plan,
    )
    from .aci_analyzers import analyzer_catalog, analyzer_support_levels
    from .aci_automation import validate_report_payload, validate_sample_reports
    from .aci_fixture_check import run_fixture_check
    from .aci_profile_catalog import profile_catalog, profile_support_levels
    from .aci_public_smoke import build_public_smoke_result, detect_repo_root
    from .aci_ratchet import check_ratchet
    from .aci_scale_verification import build_scale_check_result
    from .aci_self_audit_verification import run_self_audit_check
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_config import AciCliConfig, config_schema, load_cli_config
    from aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from aci_github_summary import build_github_summary_markdown
    from aci_report_view import (  # type: ignore[no-redef]
        apply_report_view,
        SUPPORTED_REPORT_OWNER_LANES,
        SUPPORTED_REPORT_SCOPE_CLASSES,
    )
    from aci_profiles import PROFILE_QUICK_GATE, default_scope_mode
    from aci_scan import (
        scan_target,
        ACI_TOOL_VERSION,
        SUPPORTED_SCOPE_MODES,
        SCOPE_MODE_SOURCE_ONLY,
    )
    from aci_annotations import build_github_annotations
    from aci_baseline import build_baseline_operations  # type: ignore[no-redef]
    from aci_sarif import build_sarif_report
    from aci_sarif import validate_sarif_report
    from aci_package_assets import read_text_asset
    from aci_installed_package_verification import run_installed_package_check
    from aci_analyzer_execution import (
        analyzer_availability,
        analyzer_execution_support_levels,
        profile_execution_plan,
    )
    from aci_analyzers import analyzer_catalog, analyzer_support_levels
    from aci_automation import validate_report_payload, validate_sample_reports
    from aci_fixture_check import run_fixture_check
    from aci_profile_catalog import profile_catalog, profile_support_levels
    from aci_public_smoke import build_public_smoke_result, detect_repo_root
    from aci_ratchet import check_ratchet
    from aci_scale_verification import build_scale_check_result
    from aci_self_audit_verification import run_self_audit_check


EXIT_OK = 0
EXIT_FINDINGS_PRESENT = 1
EXIT_USAGE_OR_CONFIG_ERROR = 2
EXIT_RUNTIME_FAILURE = 3
EXIT_INTERNAL_CONTRACT_ERROR = 4
EXIT_AUTOMATION_VERIFICATION_FAILURE = 5


def _resolve_repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "shared/python/aci_cli.py").exists() and (cwd / "README.md").exists():
        return cwd
    return detect_repo_root(Path(__file__))


def _print_json(data: object, output_format: str) -> None:
    indent = 2 if output_format == "pretty-json" else None
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def _write_report_file(data: dict, path: Path, output_format: str) -> None:
    """Write the report JSON to `path` (creating parent dirs) and print a
    one-line summary to stdout, so the report lives at a known location instead
    of being mixed into piped stdout."""
    indent = 2 if output_format == "pretty-json" else None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")
    summary = data.get("summary") if isinstance(data, dict) else None
    gate = data.get("gate") if isinstance(data, dict) else None
    total = summary.get("total_findings", "?") if isinstance(summary, dict) else "?"
    decision = gate.get("decision", "?") if isinstance(gate, dict) else "?"
    print(f"ACI report written to {path} ({total} findings, gate: {decision})")


def _read_json_file(path: Path) -> object:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Report file is not valid JSON: {path}")


def _sample_asset_relative_path(output_format: str) -> str:
    suffix = "json" if output_format in {"json", "pretty-json"} else "md"
    return f"report/examples/aci-core-sample-report.{suffix}"


def _add_report_view_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--report-scope-class",
        action="append",
        default=[],
        choices=list(SUPPORTED_REPORT_SCOPE_CLASSES),
        help="Filter the report view to specific scope_class values; may be repeated.",
    )
    parser.add_argument(
        "--report-owner-lane",
        action="append",
        default=[],
        choices=list(SUPPORTED_REPORT_OWNER_LANES),
        help="Filter the report view to specific owner_lane values; may be repeated.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aci", description="Common CLI for the ACI shelf")
    parser.add_argument("--version", action="version", version=f"aci {ACI_TOOL_VERSION}")
    parser.add_argument("--config", type=Path, help="Path to a bounded ACI TOML config file")
    sub = parser.add_subparsers(dest="command", required=True)

    smoke = sub.add_parser("smoke", help="Run the bounded common-shelf smoke check")
    smoke.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )

    sub.add_parser(
        "automation-smoke",
        help="Run the bounded automation-facing verification surface and emit compact JSON",
    )
    sub.add_parser(
        "fixture-check",
        help="Run the bounded common-shelf fixture suite and emit compact JSON",
    )
    sub.add_parser(
        "installed-package-check",
        help="Run the bounded installed-package verification surface and emit compact JSON",
    )
    sub.add_parser(
        "self-audit-check",
        help="Run the dedicated self-audit verification surface and emit compact JSON",
    )
    scale = sub.add_parser(
        "scale-check",
        help="Run the bounded scale/platform verification surface and emit compact JSON",
    )
    scale.add_argument(
        "--scratch-root",
        type=Path,
        help=(
            "Optional writable scratch root for synthetic benchmark files. "
            "When omitted, ACI prefers ./workspace/scale-check when available."
        ),
    )

    sample = sub.add_parser("show-sample-report", help="Print a built-in sample report")
    sample.add_argument(
        "--format",
        choices=["markdown", "json", "pretty-json"],
        default="markdown",
        help="Output format for the sample report",
    )

    sub.add_parser("show-config-schema", help="Print the bounded config schema")
    validate_report = sub.add_parser(
        "validate-report",
        help="Validate a machine-readable report JSON file against the bounded contract",
    )
    validate_report.add_argument("--report", type=Path, required=True, help="Report JSON file to validate")
    sarif = sub.add_parser(
        "emit-sarif",
        help="Convert an ACI machine-readable report JSON file into SARIF 2.1.0",
    )
    sarif.add_argument("--report", type=Path, required=True, help="ACI report JSON file to convert")
    _add_report_view_args(sarif)
    validate_sarif = sub.add_parser(
        "validate-sarif",
        help="Validate a SARIF 2.1.0 JSON file against the bounded hosted-ingestion-ready contract",
    )
    validate_sarif.add_argument("--report", type=Path, required=True, help="SARIF JSON file to validate")
    annotations_cmd = sub.add_parser(
        "emit-annotations",
        help="Convert an ACI machine-readable report JSON file into GitHub Actions workflow command annotations",
    )
    annotations_cmd.add_argument(
        "--report", type=Path, required=True, help="ACI report JSON file to convert"
    )
    _add_report_view_args(annotations_cmd)
    github_summary_cmd = sub.add_parser(
        "emit-github-summary",
        help="Convert an ACI machine-readable report JSON file into a GitHub-friendly markdown summary",
    )
    github_summary_cmd.add_argument("--report", type=Path, required=True, help="ACI report JSON file to summarize")
    _add_report_view_args(github_summary_cmd)

    baseline_cmd = sub.add_parser(
        "emit-baseline",
        help="Generate an operations-file baseline (TOML) from a report JSON, accepting today's findings as pre-existing",
    )
    baseline_cmd.add_argument("--report", type=Path, required=True, help="ACI report JSON file to baseline")
    baseline_cmd.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the baseline TOML to this path instead of stdout",
    )
    _add_report_view_args(baseline_cmd)

    catalog = sub.add_parser(
        "show-analyzer-catalog",
        help="Print the bounded external-analyzer catalog known to the common shelf",
    )
    catalog.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )

    profile_catalog_cmd = sub.add_parser(
        "show-profile-catalog",
        help="Print the bounded profile execution catalog known to the common shelf",
    )
    profile_catalog_cmd.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )

    availability = sub.add_parser(
        "show-analyzer-availability",
        help="Print bounded analyzer availability checks from the current shell",
    )
    availability.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )

    execution_plan = sub.add_parser(
        "show-profile-execution-plan",
        help="Print the bounded analyzer execution plan for supported profiles",
    )
    execution_plan.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )

    scan = sub.add_parser(
        "scan",
        help="Run a bounded real-target scan against a directory",
    )
    scan.add_argument("--target", type=Path, required=True, help="Target directory to scan")
    scan.add_argument(
        "--operations-file",
        type=Path,
        help="Optional operations TOML with baseline, suppression, and waiver entries",
    )
    scan.add_argument(
        "--include-path",
        action="append",
        default=[],
        help="Relative path under target root to include; may be repeated",
    )
    scan.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        help="Relative path under target root to exclude; may be repeated",
    )
    scan.add_argument(
        "--scope-mode",
        choices=list(SUPPORTED_SCOPE_MODES),
        default=None,
        help=(
            "Scope preset: source-only excludes common non-runtime shelves; "
            "dogfood focuses on common source/test shelves; "
            "self-audit adds maintainer probes and roadmap evidence; "
            "full-repo scans the full tree."
        ),
    )
    scan.add_argument(
        "--ignore-file",
        type=Path,
        help="Optional ignore file; defaults to .aciignore under the target root when present",
    )
    scan.add_argument(
        "--severity-threshold",
        choices=[SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL],
        default=None,
        help="Lowest severity that should block the gate when not waived",
    )
    scan.add_argument(
        "--fail-on-new-findings",
        action="store_true",
        help="Fail the gate when any new finding remains after baseline handling",
    )
    scan.add_argument(
        "--fail-on-unreviewed-review-required",
        action="store_true",
        help="Fail the gate when any human-judgment-lane finding has not been explicitly waived or baselined",
    )
    scan.add_argument(
        "--no-external-analyzers",
        action="store_true",
        help="Skip external analyzer execution even when the selected profile normally uses it",
    )
    scan.add_argument(
        "--fail-on-analyzer-errors",
        action="store_true",
        help="Fail the gate when a configured external analyzer is missing or runtime-failing",
    )
    scan.add_argument(
        "--profile",
        default=PROFILE_QUICK_GATE,
        help="Profile label recorded for this scan surface",
    )
    scan.add_argument(
        "--domain",
        default=CORE_ONLY_DOMAIN_ID,
        help="Optional domain-pack context for this scan (any registered domain id)",
    )
    scan.add_argument(
        "--domain-file",
        type=Path,
        help="Path to a domain rules Python file; used when the domain pack is not installed",
    )
    scan.add_argument(
        "--output-format",
        choices=["json", "pretty-json"],
        help="Override output format for this invocation",
    )
    scan.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Write the report to PATH instead of stdout (parent dirs are created). "
            "Overrides the [aci] report_output config default. When set, stdout gets a "
            "one-line summary so the JSON does not mix with logs."
        ),
    )
    scan.add_argument(
        "--ratchet",
        action="store_true",
        help=(
            "Enable ratchet gate: fail if any CI-ID finding count increases since "
            "the last passing run. On first run, writes a baseline state file."
        ),
    )
    scan.add_argument(
        "--ratchet-file",
        type=Path,
        default=None,
        help="Path to ratchet state file (default: .aci-ratchet under --target)",
    )
    scan.add_argument(
        "--diff-from",
        default=None,
        metavar="REF",
        help=(
            "Limit scan to files changed since git ref REF (e.g. origin/main, HEAD~1). "
            "Requires git to be available on PATH and the target to be inside a git repository."
        ),
    )
    _add_report_view_args(scan)
    return parser


def _project_report_view_from_args(
    data: dict[str, object],
    args: argparse.Namespace,
) -> dict[str, object]:
    return apply_report_view(
        data,
        scope_classes=getattr(args, "report_scope_class", ()),
        owner_lanes=getattr(args, "report_owner_lane", ()),
    )


def _handle_report_command(args: argparse.Namespace) -> int | None:
    if args.command == "show-config-schema":
        _print_json(config_schema(), "pretty-json")
        return EXIT_OK
    if args.command == "validate-report":
        data = _read_json_file(args.report)
        result = validate_report_payload(args.report.name, data)
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "emit-sarif":
        data = _read_json_file(args.report)
        if not isinstance(data, dict):
            raise ValueError(f"Report file is not a JSON object: {args.report}")
        _print_json(build_sarif_report(_project_report_view_from_args(data, args)), "pretty-json")
        return EXIT_OK
    if args.command == "validate-sarif":
        data = _read_json_file(args.report)
        result = validate_sarif_report(data)
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "emit-annotations":
        data = _read_json_file(args.report)
        if not isinstance(data, dict):
            raise ValueError(f"Report file is not a JSON object: {args.report}")
        for annotation_line in build_github_annotations(_project_report_view_from_args(data, args)):
            print(annotation_line)
        return EXIT_OK
    if args.command == "emit-github-summary":
        data = _read_json_file(args.report)
        if not isinstance(data, dict):
            raise ValueError(f"Report file is not a JSON object: {args.report}")
        print(build_github_summary_markdown(_project_report_view_from_args(data, args)), end="")
        return EXIT_OK
    if args.command == "emit-baseline":
        data = _read_json_file(args.report)
        if not isinstance(data, dict):
            raise ValueError(f"Report file is not a JSON object: {args.report}")
        toml_text = build_baseline_operations(_project_report_view_from_args(data, args))
        output_path = getattr(args, "output", None)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(toml_text, encoding="utf-8")
            entry_count = toml_text.count("{ ")
            print(f"ACI baseline written to {output_path} ({entry_count} entr{'y' if entry_count == 1 else 'ies'})")
        else:
            print(toml_text, end="")
        return EXIT_OK
    return None


def _handle_catalog_command(args: argparse.Namespace, cfg: AciCliConfig) -> int | None:
    if args.command == "show-analyzer-catalog":
        output_format = getattr(args, "output_format", None) or cfg.output_format
        _print_json(
            {
                "tool": "ACI",
                "catalog_kind": "external-analyzer",
                "support_levels": analyzer_support_levels(),
                "entries": analyzer_catalog(),
            },
            output_format,
        )
        return EXIT_OK
    if args.command == "show-profile-catalog":
        output_format = getattr(args, "output_format", None) or cfg.output_format
        _print_json(
            {
                "tool": "ACI",
                "catalog_kind": "profile-execution",
                "support_levels": profile_support_levels(),
                "entries": profile_catalog(),
            },
            output_format,
        )
        return EXIT_OK
    if args.command == "show-analyzer-availability":
        output_format = getattr(args, "output_format", None) or cfg.output_format
        _print_json(
            {
                "tool": "ACI",
                "catalog_kind": "analyzer-availability",
                "support_levels": analyzer_execution_support_levels(),
                "entries": analyzer_availability(),
            },
            output_format,
        )
        return EXIT_OK
    if args.command == "show-profile-execution-plan":
        output_format = getattr(args, "output_format", None) or cfg.output_format
        _print_json(
            {
                "tool": "ACI",
                "catalog_kind": "profile-execution-plan",
                "support_levels": analyzer_execution_support_levels(),
                "entries": profile_execution_plan(),
            },
            output_format,
        )
        return EXIT_OK
    return None


def _handle_verification_command(args: argparse.Namespace, cfg: AciCliConfig) -> int | None:
    if args.command == "automation-smoke":
        result = build_public_smoke_result(_resolve_repo_root())
        sample_validation = validate_sample_reports()
        smoke_ok = bool(result.get("ok", False))
        _print_json(
            {
                "tool": "ACI",
                "command": "automation-smoke",
                "verification": {
                    "smoke_ok": smoke_ok,
                    "sample_reports_ok": sample_validation["ok"],
                },
                "mode_checks": result["mode_checks"],
                "finding_sample": result["finding_sample"],
                "layout_note": result.get("layout_note"),
                "sample_report_checks": sample_validation["checks"],
            },
            "json",
        )
        return EXIT_OK if smoke_ok and sample_validation["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "fixture-check":
        result = run_fixture_check(_resolve_repo_root())
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "installed-package-check":
        result = run_installed_package_check(_resolve_repo_root())
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "self-audit-check":
        result = run_self_audit_check(_resolve_repo_root())
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "scale-check":
        result = build_scale_check_result(_resolve_repo_root(), args.scratch_root)
        _print_json(result, "json")
        return EXIT_OK if result["ok"] else EXIT_AUTOMATION_VERIFICATION_FAILURE
    if args.command == "show-sample-report":
        fallback_root = Path(__file__).resolve().parent / "package_assets"
        sample_text = read_text_asset(_sample_asset_relative_path(args.format), fallback_root)
        if args.format == "markdown":
            print(sample_text)
        else:
            _print_json(json.loads(sample_text), args.format)
        return EXIT_OK
    if args.command == "smoke":
        _print_json(build_public_smoke_result(_resolve_repo_root()), args.output_format or cfg.output_format)
        return EXIT_OK
    return None


def _handle_scan_command(args: argparse.Namespace, cfg: AciCliConfig) -> int | None:
    if args.command != "scan":
        return None
    output_format = args.output_format or cfg.output_format
    scope_mode = args.scope_mode or default_scope_mode(args.profile) or SCOPE_MODE_SOURCE_ONLY
    result = scan_target(
        args.target,
        args.profile,
        args.domain,
        args.operations_file,
        tuple(args.include_path),
        tuple(args.exclude_path),
        args.severity_threshold or cfg.severity_threshold,
        args.fail_on_new_findings or cfg.fail_on_new_findings,
        not args.no_external_analyzers,
        args.fail_on_analyzer_errors or cfg.fail_on_analyzer_errors,
        args.ignore_file,
        args.domain_file,
        args.fail_on_unreviewed_review_required or cfg.fail_on_unreviewed_review_required,
        diff_from=args.diff_from,
        scope_mode=scope_mode,
    )
    ratchet_result: dict[str, object] | None = None
    if args.ratchet:
        ratchet_path = args.ratchet_file or (args.target / ".aci-ratchet")
        findings: list[dict[str, object]] = result.get("findings", [])  # type: ignore[assignment]
        ratchet_result = check_ratchet(findings, state_path=ratchet_path)
        result["ratchet"] = ratchet_result
    projected_result = _project_report_view_from_args(result, args)

    report_output = args.output or (Path(cfg.report_output) if cfg.report_output else None)
    if report_output is not None:
        _write_report_file(projected_result, report_output, output_format)
    else:
        _print_json(projected_result, output_format)
    gate = result.get("gate")
    summary = result.get("summary")
    if not isinstance(gate, dict) or not isinstance(summary, dict):
        raise RuntimeError("scan_target returned unexpected result structure")
    ratchet_failed = ratchet_result is not None and ratchet_result.get("decision") == "fail"
    if gate.get("decision") == "fail" or summary.get("total_findings", 0) > 0 or ratchet_failed:
        return EXIT_FINDINGS_PRESENT
    return EXIT_OK


def _dispatch_command(args: argparse.Namespace, cfg: AciCliConfig) -> int:
    for handler in (
        _handle_report_command,
        lambda ns: _handle_catalog_command(ns, cfg),
        lambda ns: _handle_verification_command(ns, cfg),
        lambda ns: _handle_scan_command(ns, cfg),
    ):
        result = handler(args)
        if result is not None:
            return result
    return EXIT_USAGE_OR_CONFIG_ERROR


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        cfg = load_cli_config(args.config)
    except Exception as exc:
        print(f"ACI config error: {exc}")
        return EXIT_USAGE_OR_CONFIG_ERROR

    try:
        return _dispatch_command(args, cfg)
    except FileNotFoundError as exc:
        print(f"ACI runtime failure: {exc}")
        return EXIT_RUNTIME_FAILURE
    except ValueError as exc:
        print(f"ACI contract error: {exc}")
        return EXIT_INTERNAL_CONTRACT_ERROR
    except Exception as exc:  # pragma: no cover - bounded unexpected failure
        print(f"ACI runtime failure: {exc}")
        return EXIT_RUNTIME_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
