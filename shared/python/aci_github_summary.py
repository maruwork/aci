#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub-friendly markdown summary emitter for ACI reports."""
from __future__ import annotations

from typing import cast


def _report_map(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


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
    top_files = review_brief.get("top_files", [])
    if isinstance(top_files, list) and top_files:
        lines.append("### Hottest Files")
        lines.append("")
        for item in top_files:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('name', '')}`: {item.get('count', 0)} finding(s)")
        lines.append("")
    top_signals = review_brief.get("top_signals", [])
    if isinstance(top_signals, list) and top_signals:
        lines.append("### Top Signals")
        lines.append("")
        for item in top_signals:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('name', '')}`: {item.get('count', 0)}")
        lines.append("")
    advisory_scope_classes = review_brief.get("advisory_scope_classes", [])
    if isinstance(advisory_scope_classes, list) and advisory_scope_classes:
        lines.append("### Advisory Scope Classes")
        lines.append("")
        for item in advisory_scope_classes:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('name', '')}`: {item.get('count', 0)}")
        lines.append("")
    analyzer_failures = review_brief.get("analyzer_failures", [])
    if isinstance(analyzer_failures, list) and analyzer_failures:
        lines.append("### Analyzer Failures")
        lines.append("")
        for item in analyzer_failures:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('analyzer_id', '')}`: `{item.get('runtime_state', '')}`")
        lines.append("")
    analyzer_availability_notes = review_brief.get("analyzer_availability_notes", [])
    if isinstance(analyzer_availability_notes, list) and analyzer_availability_notes:
        lines.append("### Analyzer Availability Notes")
        lines.append("")
        for item in analyzer_availability_notes:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('analyzer_id', '')}`: `{item.get('runtime_state', '')}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
