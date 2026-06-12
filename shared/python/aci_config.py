#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded config loader for the common ACI shelf."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import tomllib

try:
    from .aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW


VALID_OUTPUT_FORMATS = {"json", "pretty-json"}
VALID_SEVERITY_THRESHOLDS = {SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL}


@dataclass(frozen=True)
class AciCliConfig:
    output_format: str = "pretty-json"
    severity_threshold: str = "high"
    fail_on_new_findings: bool = False
    fail_on_analyzer_errors: bool = False
    fail_on_unreviewed_review_required: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def config_schema() -> dict[str, object]:
    return {
        "format": "toml",
        "top_level_table": "aci",
        "fields": {
            "output_format": {
                "type": "string",
                "allowed": sorted(VALID_OUTPUT_FORMATS),
                "default": "pretty-json",
                "purpose": "default rendering format for CLI JSON output",
            },
            "severity_threshold": {
                "type": "string",
                "allowed": sorted(VALID_SEVERITY_THRESHOLDS),
                "default": "high",
                "purpose": "default scan gate threshold for blocking severities",
            },
            "fail_on_new_findings": {
                "type": "boolean",
                "default": False,
                "purpose": "whether scans should fail when any new finding remains after baseline handling",
            },
            "fail_on_analyzer_errors": {
                "type": "boolean",
                "default": False,
                "purpose": "whether scans should fail when configured analyzers are missing or runtime-failing",
            },
            "fail_on_unreviewed_review_required": {
                "type": "boolean",
                "default": False,
                "purpose": "whether scans should fail when any human-judgment-lane finding has not been explicitly waived or added to baseline",
            },
        },
    }


def load_cli_config(config_path: Path | None) -> AciCliConfig:
    if config_path is None:
        return AciCliConfig()
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    aci = data.get("aci", {})
    if not isinstance(aci, dict):
        raise ValueError("Config table [aci] must be a TOML table")

    output_format = aci.get("output_format", "pretty-json")
    severity_threshold = aci.get("severity_threshold", "high")
    fail_on_new_findings = aci.get("fail_on_new_findings", False)
    fail_on_analyzer_errors = aci.get("fail_on_analyzer_errors", False)
    fail_on_unreviewed_review_required = aci.get("fail_on_unreviewed_review_required", False)

    if output_format not in VALID_OUTPUT_FORMATS:
        raise ValueError(f"Invalid output_format: {output_format}")
    if severity_threshold not in VALID_SEVERITY_THRESHOLDS:
        raise ValueError(f"Invalid severity_threshold: {severity_threshold}")
    if not isinstance(fail_on_new_findings, bool):
        raise ValueError("fail_on_new_findings must be true or false")
    if not isinstance(fail_on_analyzer_errors, bool):
        raise ValueError("fail_on_analyzer_errors must be true or false")
    if not isinstance(fail_on_unreviewed_review_required, bool):
        raise ValueError("fail_on_unreviewed_review_required must be true or false")

    return AciCliConfig(
        output_format=output_format,
        severity_threshold=severity_threshold,
        fail_on_new_findings=fail_on_new_findings,
        fail_on_analyzer_errors=fail_on_analyzer_errors,
        fail_on_unreviewed_review_required=fail_on_unreviewed_review_required,
    )
