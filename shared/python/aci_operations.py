#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Operations-file handling for repeated ACI scans."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

try:
    from .aci_findings import AciFinding, build_legacy_location_key
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import AciFinding, build_legacy_location_key


@dataclass(frozen=True)
class BaselineEntry:
    fingerprint: str | None = None
    ci_id: str | None = None
    target_file: str | None = None
    line: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class SuppressionEntry:
    suppression_id: str
    match: str
    reason: str | None = None
    reviewer: str | None = None


@dataclass(frozen=True)
class WaiverEntry:
    waiver_id: str
    fingerprint: str | None = None
    ci_id: str | None = None
    target_file: str | None = None
    line: int | None = None
    owner: str | None = None
    reason: str | None = None
    review_condition: str | None = None


@dataclass(frozen=True)
class OperationsState:
    baseline_entries: tuple[BaselineEntry, ...] = ()
    suppression_entries: tuple[SuppressionEntry, ...] = ()
    waiver_entries: tuple[WaiverEntry, ...] = ()


def _opt_str(v: object) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError(f"expected str, got {type(v).__name__}: {v!r}")
    return v


def _opt_int(v: object) -> int | None:
    if v is None:
        return None
    if not isinstance(v, int):
        raise ValueError(f"expected int, got {type(v).__name__}: {v!r}")
    return v


def _table_entries(data: dict[str, object], key: str) -> list[dict[str, object]]:
    table = data.get(key, {})
    if table == {}:
        return []
    if not isinstance(table, dict):
        raise ValueError(f"[{key}] must be a TOML table")
    entries = table.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError(f"[{key}].entries must be an array")
    if not all(isinstance(item, dict) for item in entries):
        raise ValueError(f"[{key}].entries must contain only inline tables")
    return entries


def load_operations_state(operations_file: Path | None) -> OperationsState:
    if operations_file is None:
        return OperationsState()
    data = tomllib.loads(operations_file.read_text(encoding="utf-8"))
    baseline_entries = tuple(
        BaselineEntry(
            fingerprint=_opt_str(item.get("fingerprint")),
            ci_id=_opt_str(item.get("ci_id")),
            target_file=_opt_str(item.get("target_file")),
            line=_opt_int(item.get("line")),
            reason=_opt_str(item.get("reason")),
        )
        for item in _table_entries(data, "baseline")
    )
    suppression_entries = tuple(
        SuppressionEntry(
            suppression_id=str(item.get("suppression_id", "")),
            match=str(item.get("match", "")),
            reason=_opt_str(item.get("reason")),
            reviewer=_opt_str(item.get("reviewer")),
        )
        for item in _table_entries(data, "suppression")
    )
    waiver_entries = tuple(
        WaiverEntry(
            waiver_id=str(item.get("waiver_id", "")),
            fingerprint=_opt_str(item.get("fingerprint")),
            ci_id=_opt_str(item.get("ci_id")),
            target_file=_opt_str(item.get("target_file")),
            line=_opt_int(item.get("line")),
            owner=_opt_str(item.get("owner")),
            reason=_opt_str(item.get("reason")),
            review_condition=_opt_str(item.get("review_condition")),
        )
        for item in _table_entries(data, "waiver")
    )
    for entry in suppression_entries:
        if not entry.suppression_id or not entry.match:
            raise ValueError("suppression entries require suppression_id and match")
    for waiver_entry in waiver_entries:
        if not waiver_entry.waiver_id:
            raise ValueError("waiver entries require waiver_id")
    return OperationsState(
        baseline_entries=baseline_entries,
        suppression_entries=suppression_entries,
        waiver_entries=waiver_entries,
    )


def _matches_location(
    *,
    fingerprint: str | None,
    ci_id: str | None,
    target_file: str | None,
    line: int | None,
    finding: AciFinding,
) -> bool:
    legacy_key = build_legacy_location_key(
        ci_id=finding.ci_id,
        target_file=finding.target_file,
        line=finding.line,
    )
    if fingerprint and fingerprint in {finding.fingerprint, legacy_key}:
        return True
    if ci_id and ci_id != finding.ci_id:
        return False
    if target_file and target_file != finding.target_file:
        return False
    if line is not None and line != finding.line:
        return False
    return bool(ci_id or target_file or line is not None)


def is_existing_baseline(finding: AciFinding, operations: OperationsState) -> bool:
    return any(
        _matches_location(
            fingerprint=entry.fingerprint,
            ci_id=entry.ci_id,
            target_file=entry.target_file,
            line=entry.line,
            finding=finding,
        )
        for entry in operations.baseline_entries
    )


def find_active_waiver(finding: AciFinding, operations: OperationsState) -> WaiverEntry | None:
    for entry in operations.waiver_entries:
        if _matches_location(
            fingerprint=entry.fingerprint,
            ci_id=entry.ci_id,
            target_file=entry.target_file,
            line=entry.line,
            finding=finding,
        ):
            return entry
    return None


def find_resolved_baseline_entries(
    operations: OperationsState,
    detected_findings: list[AciFinding],
) -> list[dict[str, object]]:
    """Return baseline entries that have no matching finding in the current scan.

    A resolved entry means the finding was previously known but is no longer
    detected, making it a candidate for removal from the baseline.
    """
    resolved: list[dict[str, object]] = []
    for entry in operations.baseline_entries:
        matched = any(
            _matches_location(
                fingerprint=entry.fingerprint,
                ci_id=entry.ci_id,
                target_file=entry.target_file,
                line=entry.line,
                finding=finding,
            )
            for finding in detected_findings
        )
        if not matched:
            resolved.append(
                {
                    "fingerprint": entry.fingerprint,
                    "ci_id": entry.ci_id,
                    "target_file": entry.target_file,
                    "line": entry.line,
                    "lifecycle_state": "resolved",
                    "note": "baseline entry no longer detected; candidate for removal from operations file",
                }
            )
    return resolved


def find_matching_suppression(
    finding: AciFinding,
    operations: OperationsState,
) -> SuppressionEntry | None:
    haystacks = (
        finding.signal,
        finding.target_file,
        finding.excerpt,
        finding.reason,
    )
    for entry in operations.suppression_entries:
        if any(entry.match in value for value in haystacks):
            return entry
    return None
