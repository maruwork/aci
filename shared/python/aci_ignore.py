#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ignore-file loading for ACI scan scope."""
from __future__ import annotations

from pathlib import Path


DEFAULT_IGNORE_FILE_NAME = ".aciignore"


def load_ignore_patterns(target_root: Path, ignore_file: Path | None = None) -> tuple[str, ...]:
    path = ignore_file or (target_root / DEFAULT_IGNORE_FILE_NAME)
    if not path.exists():
        return ()
    patterns: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip().replace("\\", "/").strip("/")
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return tuple(patterns)
