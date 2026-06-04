#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-boundary constants for project-local ACI execution.

These constants are not domain vocabulary, but they are also not part of the
smallest domain-independent signal core. They describe runtime/operator-facing
surfaces and exclusions that belong with runtime binding.
"""
from __future__ import annotations

from pathlib import Path

OPERATOR_SURFACES = (
    Path("{project_operator_start}"),
    Path("{project_operator_report}"),
    Path("{project_operator_close}"),
    Path("{project_operator_interface}"),
    Path("{project_state_query}"),
)

RESPONSIBILITY_CLUSTERS: dict[str, tuple[str, ...]] = {
    "startup": ("session_start", "startup summary", "session start"),
    "healthcheck": ("healthcheck", "quick check", "governance check"),
    "reporting": ("report", "wrap_up", "operator view"),
    "trial_lifecycle": ("start_tool_trial", "close_tool_trial", "trial lifecycle"),
    "register_sync": ("current-task-register", "pending_tasks", "execution"),
}

CRITICAL_RESPONSIBILITY_FILES = {
    "{project_operator_start}",
    "{project_healthcheck}",
    "{project_operator_report}",
    "{project_operator_close}",
    "{project_operator_interface}",
}

RESPONSIBILITY_SPROUT_EXCLUDED_PREFIXES = (
    "{project_test_shelf}/",
)

RESPONSIBILITY_SPROUT_EXCLUDED_FILES = {
    "{project_aci_core}",
    "{project_index_generator}",
    "{project_tools_classifier}",
}

SHELF_RISK_SURFACES = {
    "{project_entry_readme}",
    "{project_workflow_doc}",
    "{project_docs_index}",
    "{project_current_task_register}",
    "{project_execution_order_file}",
}
