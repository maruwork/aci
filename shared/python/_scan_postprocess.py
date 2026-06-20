"""Finding post-processing: native/external dedup, scope-noise filtering, and
baseline/waiver/suppression application.

A distinct concern from report assembly: these transform the raw finding list
before it is summarized. Pure over a finding list plus the operations state.
"""
from __future__ import annotations

from dataclasses import replace

try:
    from .aci_findings import AciFinding, LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER
    from .aci_operations import (
        OperationsState, find_active_waiver, find_matching_suppression, is_existing_baseline,
    )
    from ._scan_scope import _SUPPORT_ONLY_HTTP_SCOPE_CLASSES, _classify_relative_path
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import AciFinding, LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER  # type: ignore[no-redef]
    from aci_operations import (  # type: ignore[no-redef]
        OperationsState, find_active_waiver, find_matching_suppression, is_existing_baseline,
    )
    from _scan_scope import _SUPPORT_ONLY_HTTP_SCOPE_CLASSES, _classify_relative_path  # type: ignore[no-redef]


def _deduplicate_findings(findings: list[AciFinding]) -> list[AciFinding]:
    # 1. exact fingerprint dedup
    deduplicated: dict[str, AciFinding] = {}
    for finding in findings:
        deduplicated.setdefault(finding.fingerprint, finding)
    unique = list(deduplicated.values())

    # 2. cross-lane dedup: when the external-analyzer lane (ruff/etc.) already
    #    reports a CI-ID at a location, drop the native-static finding for the
    #    same (ci_id, file, line). ACI complements the external linter rather than
    #    re-reporting what it already covers. Native findings are kept untouched
    #    when no external finding overlaps (e.g. the external lane is disabled).
    external_locs = {
        (f.ci_id, f.target_file, f.line)
        for f in unique
        if f.owner_lane == LANE_EXTERNAL_ANALYZER and f.line is not None
    }
    if not external_locs:
        return unique
    result: list[AciFinding] = []
    for finding in unique:
        if (
            finding.owner_lane == LANE_NATIVE_STATIC
            and finding.line is not None
            and any((finding.ci_id, finding.target_file, finding.line + dl) in external_locs for dl in (0, -1, 1))
        ):
            continue
        result.append(finding)
    return result


def _filter_scope_noise(findings: list[AciFinding]) -> list[AciFinding]:
    filtered: list[AciFinding] = []
    for finding in findings:
        scope_class = _classify_relative_path(finding.target_file)
        if finding.signal == "CI14_INSECURE_HTTP" and scope_class in _SUPPORT_ONLY_HTTP_SCOPE_CLASSES:
            continue
        filtered.append(finding)
    return filtered


def _apply_operations(
    findings: list[AciFinding],
    operations: OperationsState,
) -> tuple[list[AciFinding], int]:
    visible_findings: list[AciFinding] = []
    suppressed_count = 0
    for finding in findings:
        suppression = find_matching_suppression(finding, operations)
        if suppression is not None:
            suppressed_count += 1
            continue
        baseline_status = "existing-baseline" if is_existing_baseline(finding, operations) else "new"
        waiver = find_active_waiver(finding, operations)
        visible_findings.append(
            replace(
                finding,
                baseline_status=baseline_status,
                waiver_status="active-waiver" if waiver is not None else "none",
                lifecycle_state="accepted" if waiver is not None else finding.lifecycle_state,
                triage_state="accepted-residual" if waiver is not None else finding.triage_state,
            )
        )
    return visible_findings, suppressed_count
