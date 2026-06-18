#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-readable known-limit metadata for the bounded ACI common shelf."""
from __future__ import annotations


_KNOWN_LIMITS: tuple[dict[str, object], ...] = (
    {
        "limit_id": "KL-ACI-CI05-STRUCTURE-EXACT",
        "ci_ids": ["CI-05"],
        "signal_ids": ["CI05_COPY_PASTE_CODE"],
        "kind": "recall-limit",
        "title": "Structure-exact clone matching",
        "summary": (
            "CI-05 matches rename-invariant structural clones, but intentionally "
            "misses variants with inserted, removed, or reordered statements."
        ),
        "operator_guidance": (
            "Treat near-duplicate misses with small structural edits as a known "
            "precision-over-recall tradeoff, not an unconditional runtime bug."
        ),
        "source_refs": [
            "docs/CI_REFERENCE.md",
            "shared/tools/aci_recall_probe.py",
        ],
    },
    {
        "limit_id": "KL-ACI-CI07-COMPILED-EXTENSIONS",
        "ci_ids": ["CI-07"],
        "signal_ids": ["CI07_UNUSED_PRIVATE_SYMBOL"],
        "kind": "blind-spot",
        "title": "Compiled-extension references are invisible",
        "summary": (
            "CI-07 cannot see calls or callbacks originating from compiled "
            "extensions such as .pyd or .so modules."
        ),
        "operator_guidance": (
            "Review dead-private-symbol findings carefully when Python code is "
            "called from Rust, C, C++, or other compiled integration layers."
        ),
        "source_refs": ["docs/CI_REFERENCE.md"],
    },
    {
        "limit_id": "KL-ACI-CI14-SUPPLY-CHAIN-SCOPE",
        "ci_ids": ["CI-14"],
        "signal_ids": ["CI14_SUPPLY_CHAIN_DRIFT"],
        "kind": "coverage-boundary",
        "title": "Supply-chain manifest coverage is intentionally narrow",
        "summary": (
            "The common-shelf CI-14 supply-chain detector currently covers only "
            "requirements*.txt, package.json, Dockerfile/Containerfile, and "
            "GitHub workflow uses: references."
        ),
        "operator_guidance": (
            "Use additional tooling or downstream extensions for lockfiles and "
            "ecosystem manifests outside the bounded common-shelf set."
        ),
        "source_refs": [
            "docs/CI_REFERENCE.md",
            "shared/core/aci-product-boundary-and-coverage-policy.md",
        ],
    },
    {
        "limit_id": "KL-ACI-CI22-NONLOCAL-LIFECYCLE",
        "ci_ids": ["CI-22"],
        "signal_ids": ["CI22_RESOURCE_CLEANUP_GAP", "CI22_FIRE_AND_FORGET_TASK"],
        "kind": "recall-limit",
        "title": "Non-local lifecycle reasoning stays conservative",
        "summary": (
            "CI-22 does not try to prove resource cleanup through helper calls, "
            "ownership transfers, or broad non-local control flow."
        ),
        "operator_guidance": (
            "Treat CI-22 as a conservative structural signal; confirm exception-path "
            "cleanup manually when ownership leaves the local function."
        ),
        "source_refs": [
            "docs/CI_REFERENCE.md",
            "shared/python/detectors/ci_22.py",
            "shared/tools/aci_recall_probe.py",
        ],
    },
)


def known_limits() -> list[dict[str, object]]:
    """Return a copy of the bounded machine-readable known-limit catalog."""
    return [dict(item) for item in _KNOWN_LIMITS]
