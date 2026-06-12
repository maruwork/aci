#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helpers for bounded package-safe asset loading."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

_PACKAGE_ASSET_ROOT = "package_assets"


def _package_root_name() -> str | None:
    package_name = __package__ or ""
    if not package_name:
        return None
    return package_name.split(".")[0]


def read_text_asset(relative_path: str, fallback_root: Path) -> str:
    package_root = _package_root_name()
    if package_root:
        try:
            asset = resources.files(package_root).joinpath(
                _PACKAGE_ASSET_ROOT,
                *relative_path.split("/"),
            )
            return asset.read_text(encoding="utf-8")
        except (FileNotFoundError, ModuleNotFoundError, OSError):
            pass
    return (fallback_root / relative_path).read_text(encoding="utf-8")


def read_bytes_asset(relative_path: str, fallback_root: Path) -> bytes:
    package_root = _package_root_name()
    if package_root:
        try:
            asset = resources.files(package_root).joinpath(
                _PACKAGE_ASSET_ROOT,
                *relative_path.split("/"),
            )
            return asset.read_bytes()
        except (FileNotFoundError, ModuleNotFoundError, OSError):
            pass
    return (fallback_root / relative_path).read_bytes()
