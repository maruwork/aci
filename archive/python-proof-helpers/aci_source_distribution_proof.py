#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helpers for bounded source-distribution proof of the ACI package."""
from __future__ import annotations

from pathlib import Path


def _normalized_distribution_name(project_name: str) -> str:
    return project_name.replace("-", "_")


def find_built_source_distribution(dist_dir: str | Path, project_name: str = "aci") -> dict[str, object]:
    directory = Path(dist_dir)
    normalized = _normalized_distribution_name(project_name)
    archives = sorted(directory.glob(f"{normalized}-*.tar.gz"))
    selected = archives[-1] if archives else None
    return {
        "dist_dir": str(directory),
        "project_name": project_name,
        "archive_count": len(archives),
        "archive_files": [item.name for item in archives],
        "selected_archive": str(selected) if selected is not None else None,
        "ok": selected is not None,
    }
