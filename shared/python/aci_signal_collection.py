"""Shared helpers for benchmark/fixture signal collection."""
from __future__ import annotations

from pathlib import Path
from typing import cast

try:
    from .aci_scan import scan_target
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_scan import scan_target  # type: ignore[no-redef]


def scan_signals(target: Path) -> set[str]:
    report = scan_target(target, "full", "core-only", include_external_analyzers=False)
    findings = cast("list[dict[str, object]]", report["findings"])
    return {
        signal
        for item in findings
        for signal in [item.get("signal")]
        if isinstance(signal, str)
    }
