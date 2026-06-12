#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helpers for bounded editable-install proof reporting."""
from __future__ import annotations

from pathlib import Path


def editable_install_proof_payload(
    environment_root: Path,
    install_command: str,
    verification_command: str,
    verification_stdout: str,
) -> dict[str, object]:
    return {
        "tool": "ACI",
        "command": "editable-install-proof",
        "ok": True,
        "environment_root": str(environment_root),
        "install_command": install_command,
        "verification_command": verification_command,
        "verification_stdout": verification_stdout,
        "proof_boundary": {
            "permanent_environment_changed": False,
            "registry_publish_proved": False,
            "built_wheel_proved": False,
        },
    }
