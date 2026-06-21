#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an operations-file baseline from a scan report.

Adopting ACI on an existing codebase means accepting today's findings as
pre-existing so that future scans surface only NEW ones. That baseline used to
be hand-authored TOML; this module derives it from a report instead, turning the
central adoption step into one command (`aci emit-baseline`).

The emitted TOML round-trips through aci_operations.load_operations_state. Each
entry's identity is the fingerprint (stable across unrelated line shifts), so no
line number is written -- encoding identity by line was the root of three earlier
defects. Output is sorted for a stable, reviewable diff when the baseline is
regenerated.
"""
from __future__ import annotations

from typing import cast

# TOML basic-string escapes (TOML v1.0.0 §String). Everything else, including
# printable non-ASCII, is emitted as-is in UTF-8.
_TOML_SIMPLE_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _toml_escape(value: str) -> str:
    out: list[str] = []
    for ch in value:
        simple = _TOML_SIMPLE_ESCAPES.get(ch)
        if simple is not None:
            out.append(simple)
        elif ch < "\x20" or ch == "\x7f":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return "".join(out)


def _entry_fields(finding: dict[str, object]) -> list[tuple[str, str]]:
    """The stable-identity fields for one baseline entry, in emit order.

    fingerprint anchors the match; ci_id and target_file keep the TOML readable
    and let resolved-baseline detection bound itself to scanned files. line is
    deliberately omitted.
    """
    fields: list[tuple[str, str]] = []
    for key in ("fingerprint", "ci_id", "target_file"):
        raw = finding.get(key)
        if isinstance(raw, str) and raw:
            fields.append((key, raw))
    return fields


def build_baseline_operations(report: dict[str, object]) -> str:
    """Return operations TOML whose [baseline] accepts every finding in *report*."""
    raw_findings = report.get("findings")
    findings = raw_findings if isinstance(raw_findings, list) else []
    entries: list[list[tuple[str, str]]] = []
    skipped = 0
    for finding in findings:
        if not isinstance(finding, dict):
            skipped += 1
            continue
        fields = _entry_fields(cast(dict[str, object], finding))
        if not fields:
            skipped += 1
            continue
        entries.append(fields)

    # Deterministic order: by target_file, then ci_id, then fingerprint, so a
    # regenerated baseline diffs cleanly against the previous one.
    def _sort_key(fields: list[tuple[str, str]]) -> tuple[str, str, str]:
        as_map = dict(fields)
        return (as_map.get("target_file", ""), as_map.get("ci_id", ""), as_map.get("fingerprint", ""))

    entries.sort(key=_sort_key)

    lines = [
        "# ACI baseline -- generated from a scan report by `aci emit-baseline`.",
        "# Each entry accepts a finding as pre-existing; future scans report only",
        "# NEW findings. Identity is the fingerprint (stable across line shifts), so",
        "# no line numbers are stored here. Remove an entry once its finding is",
        "# fixed -- ACI then reports it as resolved on the next scan.",
        "[baseline]",
    ]
    if not entries:
        lines.append("entries = []")
        return "\n".join(lines) + "\n"

    lines.append("entries = [")
    rendered = [
        "  { " + ", ".join(f'{key} = "{_toml_escape(value)}"' for key, value in fields) + " },"
        for fields in entries
    ]
    lines.extend(rendered)
    lines.append("]")
    if skipped:
        lines.append(f"# note: {skipped} finding(s) had no usable identity and were not baselined.")
    return "\n".join(lines) + "\n"
