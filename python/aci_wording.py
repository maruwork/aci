#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI wording and remediation metadata."""
from __future__ import annotations

DEFAULT_PATCH_CLASSES = {
    "RESPONSIBILITY_SPROUT": "helper-reroute",
    "SIDE_PROGRAM_LEAK": "authority-read-reroute",
    "SHELF_BOUNDARY_BREAK": "narrow-placement-reroute",
    "OPERATOR_VIEW_GAP": "projection-pullthrough",
    "PATCHWORK_GRAFT": "authority-closeout-reroute",
}

PRIMARY_CATEGORIES = {
    "RESPONSIBILITY_SPROUT": "responsibility-boundary",
    "SIDE_PROGRAM_LEAK": "authority-boundary",
    "SHELF_BOUNDARY_BREAK": "shelf-boundary",
    "OPERATOR_VIEW_GAP": "operator-surface",
    "PATCHWORK_GRAFT": "patchwork-structure",
}

SECONDARY_CATEGORIES = {
    "RESPONSIBILITY_SPROUT": ["operator-control", "surface-mixing"],
    "SIDE_PROGRAM_LEAK": ["authority", "governance"],
    "SHELF_BOUNDARY_BREAK": ["static-structure", "current-surface"],
    "OPERATOR_VIEW_GAP": ["operator-surface", "state-plane"],
    "PATCHWORK_GRAFT": ["bridge-layer", "authority-seam"],
}

SUGGESTED_ACTIONS = {
    "RESPONSIBILITY_SPROUT": "operator、control、reporting、startup の責務を 1 つの面に混載しない。",
    "SIDE_PROGRAM_LEAK": "side program を authority、mainline、current canonical から切り離す。",
    "SHELF_BOUNDARY_BREAK": "workspace、archive、scratch を current-facing authority から離す。",
    "OPERATOR_VIEW_GAP": "operator surface に state-plane anchor を戻す。",
    "PATCHWORK_GRAFT": "bridge、暫定 mapping、二重 authority を閉じて、正本面を 1 つに戻す。",
}
