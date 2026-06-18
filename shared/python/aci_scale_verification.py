#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scale and platform verification helpers for the bounded ACI shelf."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import cast

try:
    from .aci_analyzer_execution import analyzer_availability
    from .aci_scan import scan_target
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_analyzer_execution import analyzer_availability  # type: ignore[no-redef]
    from aci_scan import scan_target  # type: ignore[no-redef]


@dataclass(frozen=True)
class ScaleScenario:
    scenario_id: str
    file_count: int
    budget_seconds: float


SCALE_SCENARIOS: tuple[ScaleScenario, ...] = (
    ScaleScenario("medium-python-repo", file_count=250, budget_seconds=8.0),
    ScaleScenario("large-python-repo", file_count=1000, budget_seconds=35.0),
)

ANALYZER_RUNTIME_BUDGETS_SECONDS: dict[str, float] = {
    "ruff": 10.0,
    "pyflakes": 10.0,
    "mypy": 45.0,
    "pytest": 60.0,
    "semgrep": 45.0,
    "eslint": 30.0,
    "tsc": 45.0,
    "shellcheck": 20.0,
    "sqlfluff": 20.0,
}


def _default_scratch_root(repo_root: Path) -> Path | None:
    workspace_root = repo_root / "workspace"
    if workspace_root.exists():
        return workspace_root / "scale-check"
    return None


def _variant_body(index: int) -> str:
    # 11 variants keep the synthetic repo readable while avoiding a single
    # repeated clone shape from dominating CI-05 in every file.
    variant = index % 11
    value = 1000 + index
    header = [
        f'"""Synthetic benchmark module {index}."""',
        "",
        f"VALUE = {value}",
        "",
        "def compute(input_value: int) -> int:",
    ]
    if variant == 0:
        body = ["    total = input_value + VALUE", "    return total"]
    elif variant == 1:
        body = ["    total = input_value - VALUE", "    return total"]
    elif variant == 2:
        body = ["    if input_value < 0:", "        return VALUE - input_value", "    return input_value + VALUE"]
    elif variant == 3:
        body = ["    if input_value % 2 == 0:", "        return input_value + VALUE", "    return input_value - VALUE"]
    elif variant == 4:
        body = ["    total = input_value", "    total += VALUE", "    return total"]
    elif variant == 5:
        body = ["    total = input_value", "    total -= VALUE", "    return total"]
    elif variant == 6:
        body = ["    total = VALUE", "    total += input_value", "    return total"]
    elif variant == 7:
        body = ["    total = VALUE", "    total -= input_value", "    return total"]
    elif variant == 8:
        body = ["    adjustment = VALUE // 2", "    return input_value + adjustment"]
    elif variant == 9:
        body = ["    adjustment = VALUE // 3", "    return input_value - adjustment"]
    else:
        body = ["    result = input_value * 2", "    result += VALUE", "    return result"]
    return "\n".join([*header, *body, ""])


def _build_synthetic_repo(root: Path, file_count: int) -> Path:
    src_root = root / "src"
    src_root.mkdir(parents=True, exist_ok=True)
    for index in range(file_count):
        path = src_root / f"module_{index:04d}.py"
        path.write_text(_variant_body(index), encoding="utf-8")
    return src_root


def _benchmark_scenario(root: Path, scenario: ScaleScenario) -> dict[str, object]:
    scenario_root = root / scenario.scenario_id
    _build_synthetic_repo(scenario_root, scenario.file_count)
    started = perf_counter()
    report = scan_target(
        scenario_root,
        "full",
        "core-only",
        include_external_analyzers=False,
        scope_mode="source-only",
    )
    elapsed = perf_counter() - started
    findings = cast("list[dict[str, object]]", report["findings"])
    skipped_targets = cast("list[dict[str, object]]", report["skipped_targets"])
    return {
        "scenario_id": scenario.scenario_id,
        "file_count": scenario.file_count,
        "budget_seconds": scenario.budget_seconds,
        "elapsed_seconds": round(elapsed, 3),
        "within_budget": elapsed <= scenario.budget_seconds,
        "finding_count": len(findings),
        "skipped_target_count": len(skipped_targets),
    }


def build_scale_check_result(repo_root: Path, scratch_root: Path | None = None) -> dict[str, object]:
    resolved_repo_root = repo_root.resolve()
    requested_scratch_root = scratch_root.resolve() if scratch_root is not None else _default_scratch_root(resolved_repo_root)
    analyzer_snapshot = [
        {
            "analyzer_id": item["analyzer_id"],
            "availability_state": item["availability_state"],
            "version_text": item["version_text"],
            "budget_seconds": ANALYZER_RUNTIME_BUDGETS_SECONDS.get(str(item["analyzer_id"]), None),
        }
        for item in analyzer_availability()
    ]

    def _result_for(root: Path) -> dict[str, object]:
        root.mkdir(parents=True, exist_ok=True)
        scenarios = [_benchmark_scenario(root, scenario) for scenario in SCALE_SCENARIOS]
        ok = all(bool(item["within_budget"]) for item in scenarios)
        return {
            "tool": "ACI",
            "command": "scale-check",
            "ok": ok,
            "repository_layout": "standalone",
            "scratch_root": root.as_posix(),
            "scan_runtime_budgets_seconds": {
                item.scenario_id: item.budget_seconds for item in SCALE_SCENARIOS
            },
            "analyzer_runtime_budgets_seconds": dict(ANALYZER_RUNTIME_BUDGETS_SECONDS),
            "scenarios": scenarios,
            "analyzer_availability_snapshot": analyzer_snapshot,
            "platform_support_matrix": {
                "continuous_ci": ["ubuntu-latest", "windows-latest", "macos-latest"],
                "python_versions": ["3.11", "3.12"],
            },
        }

    if requested_scratch_root is not None:
        return _result_for(requested_scratch_root)

    with TemporaryDirectory(prefix="aci-scale-check-") as temp_dir:
        return _result_for(Path(temp_dir))
