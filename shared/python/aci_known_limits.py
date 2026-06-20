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
            "The common-shelf CI-14 supply-chain detector currently covers "
            "requirements*.txt, pyproject.toml dependency surfaces, package.json, "
            "Dockerfile/Containerfile, and GitHub workflow uses: references."
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
            "CI-22 accepts local safe-management patterns such as explicit close "
            "paths, helper context managers, and managed ExitStack registration "
            "or close callbacks, but still does not try to prove helper-call "
            "ownership transfers or broad non-local control flow."
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
    {
        "limit_id": "KL-ACI-CI14-CI25-IMPORT-ALIAS",
        "ci_ids": ["CI-14", "CI-25"],
        "signal_ids": [
            "CI14_UNSAFE_DESERIALIZATION",
            "CI14_SUBPROCESS_SHELL_TRUE",
            "CI25_ENVIRONMENT_DRIFT",
        ],
        "kind": "blind-spot",
        "title": "Variable-aliased and dynamic import forms stay unresolved",
        "summary": (
            "CI-14/CI-25 now run an import/name-resolution pass, so static "
            "`import x as y`, `from x import y`, attribute-module, and "
            "nested-call argument forms are resolved to their canonical name and "
            "detected. The residual blind spot is non-import indirection: "
            "variable aliasing (`m = pickle; m.loads()`), dynamic "
            "`importlib.import_module` lookups, and relative imports, which are "
            "intentionally not tracked to avoid speculative dataflow."
        ),
        "operator_guidance": (
            "Static import aliasing is covered. Do not rely on CI-14/CI-25 for "
            "values reached through an intermediate variable or a dynamic import; "
            "use dedicated SAST tooling for those indirection forms."
        ),
        "source_refs": [
            "docs/AUDIT_2026-06-19_GENERAL_PURPOSE_READINESS.md",
            "shared/python/detectors/ci_14.py",
            "shared/python/detectors/ci_25.py",
        ],
    },
    {
        "limit_id": "KL-ACI-CI14-TAINT-INTRAPROCEDURAL",
        "ci_ids": ["CI-14"],
        "signal_ids": ["CI14_TAINTED_FLOW"],
        "kind": "coverage-boundary",
        "title": "Native taint flow is intra-procedural only (orchestrated lane covers the rest)",
        "summary": (
            "The native CI14_TAINTED_FLOW detector tracks untrusted input to a "
            "dangerous sink within a single Python function, through assignments, "
            "f-strings, concatenation, and string methods. It does not itself "
            "follow taint across function calls, through container elements, or "
            "through object attributes. Inter-procedural and multi-language "
            "source→sink taint is instead delivered by the orchestrated "
            "external-analyzer lane: the bundled semgrep taint-mode rules "
            "(JavaScript, Python, and Go source→sink, run by default, "
            "precision-gated by shared/tools/aci_taint_eval.py at full recall "
            "and zero false positives on a curated control corpus) and the "
            "execution-ready codeql data-flow adapter (multi-language, opt-in "
            "because the per-language database build is heavy)."
        ),
        "operator_guidance": (
            "A clean native CI14_TAINTED_FLOW result does not by itself rule out "
            "injection that flows through helper functions or data structures. "
            "For that depth, enable the orchestrated taint lane (semgrep is on by "
            "default; codeql is opt-in) rather than reaching outside ACI; both "
            "normalize their source→sink findings into CI-14."
        ),
        "source_refs": [
            "docs/CI_REFERENCE.md",
            "shared/python/detectors/ci_14_taint.py",
            "shared/python/package_assets/analyzers/aci-semgrep-rules.yml",
            "shared/tests/fixtures/taint_multilang/README.md",
            "shared/tools/aci_taint_eval.py",
        ],
    },
)


def known_limits() -> list[dict[str, object]]:
    """Return a copy of the bounded machine-readable known-limit catalog."""
    return [dict(item) for item in _KNOWN_LIMITS]
