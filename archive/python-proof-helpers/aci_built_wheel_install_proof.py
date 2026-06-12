#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helpers for bounded built-wheel proof of the ACI package."""
from __future__ import annotations

from pathlib import Path


def _normalized_distribution_name(project_name: str) -> str:
    return project_name.replace("-", "_")


def find_built_wheel(dist_dir: str | Path, project_name: str = "aci") -> dict[str, object]:
    directory = Path(dist_dir)
    normalized = _normalized_distribution_name(project_name)
    wheels = sorted(directory.glob(f"{normalized}-*.whl"))
    selected = wheels[-1] if wheels else None
    return {
        "dist_dir": str(directory),
        "project_name": project_name,
        "wheel_count": len(wheels),
        "wheel_files": [item.name for item in wheels],
        "selected_wheel": str(selected) if selected is not None else None,
        "ok": selected is not None,
    }
