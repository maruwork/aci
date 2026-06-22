#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub-friendly markdown summary emitter for ACI reports."""
from __future__ import annotations

from typing import Callable

try:
    from .aci_report_helpers import report_map as _report_map
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_report_helpers import report_map as _report_map  # type: ignore[no-redef]


def _append_list_section(
    lines: list[str],
    items: object,
    header: str,
    row: Callable[[dict[str, object]], str],
) -> None:
    if not isinstance(items, list) or not items:
        return
    lines.append(f"### {header}")
    lines.append("")
    for item in items:
        if isinstance(item, dict):
            lines.append(row(item))
    lines.append("")


def build_github_summary_markdown(report: dict[str, object]) -> str:
    gate = _report_map(report.get("gate"))
    summary = _report_map(report.get("summary"))
    review_brief = _report_map(report.get("review_brief"))
    report_view = _report_map(report.get("report_view"))
    scope_policy = _report_map(summary.get("by_scope_policy"))
    lines = [
        "## ACI Review Summary",
        "",
        f"- Gate: `{gate.get('decision', 'fail')}`",
        f"- Findings: `{summary.get('total_findings', 0)}`",
        f"- Blockers: `{summary.get('blocker_count', 0)}`",
        f"- Scope mode: `{review_brief.get('scope_mode', 'unknown')}`",
        "",
        str(review_brief.get("blocker_headline", "No review headline available.")),
        "",
    ]
    if report_view:
        lines.insert(
            5,
            f"- Visible view: `{report_view.get('visible_total_findings', summary.get('total_findings', 0))}`"
            f" of `{report_view.get('source_total_findings', summary.get('total_findings', 0))}` finding(s)",
        )
    if scope_policy:
        lines.append(
            f"Advisory-only findings outside the gate: `{scope_policy.get('advisory', 0)}`"
        )
        lines.append("")
    advisory_headline = review_brief.get("advisory_headline")
    if advisory_headline:
        lines.append(str(advisory_headline))
        lines.append("")
    _append_list_section(
        lines, review_brief.get("top_files"), "Hottest Files",
        lambda i: f"- `{i.get('name', '')}`: {i.get('count', 0)} finding(s)",
    )
    _append_list_section(
        lines, review_brief.get("top_signals"), "Top Signals",
        lambda i: f"- `{i.get('name', '')}`: {i.get('count', 0)}",
    )
    _append_list_section(
        lines, review_brief.get("advisory_scope_classes"), "Advisory Scope Classes",
        lambda i: f"- `{i.get('name', '')}`: {i.get('count', 0)}",
    )
    _append_list_section(
        lines, review_brief.get("analyzer_failures"), "Analyzer Failures",
        lambda i: f"- `{i.get('analyzer_id', '')}`: `{i.get('runtime_state', '')}`",
    )
    _append_list_section(
        lines, review_brief.get("analyzer_availability_notes"), "Analyzer Availability Notes",
        lambda i: f"- `{i.get('analyzer_id', '')}`: `{i.get('runtime_state', '')}`",
    )
    # The non-exhaustiveness disclosure must travel with the human-facing summary,
    # not just the JSON report: this PR summary is where a reviewer forms the
    # judgement "ACI passed, the code is clean." A pass with zero findings is
    # exactly where that false confidence is highest, so the bound is stated here,
    # at the point of use, sourced from the same disclosure the report carries.
    disclosure = report.get("detection_disclosure")
    if isinstance(disclosure, str) and disclosure:
        lines.append("---")
        lines.append("")
        lines.append(f"> **Scope note:** {disclosure}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
