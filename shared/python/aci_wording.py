#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI wording and remediation metadata."""
from __future__ import annotations

try:
    from .aci_signals import (
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_signals import (
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )

DEFAULT_PATCH_CLASSES = {
    SIGNAL_RESPONSIBILITY_SPROUT: "helper-reroute",
    SIGNAL_SIDE_PROGRAM_LEAK: "authority-read-reroute",
    SIGNAL_OPERATOR_VIEW_GAP: "projection-pullthrough",
    SIGNAL_STATE_DUPLICATION: "state-consolidation",
}

PRIMARY_CATEGORIES = {
    SIGNAL_RESPONSIBILITY_SPROUT: "responsibility-boundary",
    SIGNAL_SIDE_PROGRAM_LEAK: "authority-boundary",
    SIGNAL_OPERATOR_VIEW_GAP: "operator-surface",
    SIGNAL_STATE_DUPLICATION: "state-boundary",
}

SECONDARY_CATEGORIES = {
    SIGNAL_RESPONSIBILITY_SPROUT: ["operator-control", "surface-mixing"],
    SIGNAL_SIDE_PROGRAM_LEAK: ["authority", "governance"],
    SIGNAL_OPERATOR_VIEW_GAP: ["operator-surface", "state-plane"],
    SIGNAL_STATE_DUPLICATION: ["state-plane", "scattered-ownership"],
}

SUGGESTED_ACTIONS = {
    SIGNAL_RESPONSIBILITY_SPROUT: "Split distinct responsibilities into separate modules; each module should own one concern.",
    SIGNAL_SIDE_PROGRAM_LEAK: "Isolate the secondary concern behind an explicit boundary; keep it out of the primary authority surface.",
    SIGNAL_OPERATOR_VIEW_GAP: "Add a clear state anchor or readback surface to the operator-facing boundary.",
    SIGNAL_STATE_DUPLICATION: "Identify the canonical owner for this state and remove the duplicate definition; all consumers should read from the single source.",
}
