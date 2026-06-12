"""Native detector registry.

Each entry: (required_signals, scan_function).
The orchestrator activates a detector when required_signals & active_signals is non-empty.
"""
from __future__ import annotations

from . import ci_02, ci_03, ci_04, ci_05, ci_06, ci_12, ci_14, ci_18, ci_20, ci_21, ci_22, ci_23, ci_25, ci_26

PER_FILE_REGISTRY: tuple[tuple[frozenset[str], object], ...] = (
    (ci_02.SIGNALS_SPAGHETTI, ci_02.scan_spaghetti),
    (ci_02.SIGNALS_LONG, ci_02.scan_long_functions),
    (ci_03.SIGNALS, ci_03.scan),
    (ci_04.SIGNALS, ci_04.scan),
    (ci_12.SIGNALS, ci_12.scan),
    (ci_14.SIGNALS_EVAL_EXEC, ci_14.scan_eval_exec),
    (ci_14.SIGNALS_SUBPROCESS, ci_14.scan_subprocess_shell_true),
    (ci_14.SIGNALS_SECRET, ci_14.scan_plaintext_secrets),
    (ci_14.SIGNALS_HTTP, ci_14.scan_insecure_http),
    (ci_21.SIGNALS_BROAD, ci_21.scan_broad),
    (ci_21.SIGNALS_SILENT, ci_21.scan_silent),
    (ci_22.SIGNALS, ci_22.scan),
    (ci_23.SIGNALS, ci_23.scan),
    (ci_25.SIGNALS, ci_25.scan),
    (ci_26.SIGNALS, ci_26.scan),
)

CROSS_FILE_REGISTRY: tuple[tuple[frozenset[str], object], ...] = (
    (ci_05.SIGNALS, ci_05.scan),
    (ci_06.SIGNALS, ci_06.scan),
    (ci_18.SIGNALS, ci_18.scan),
    (ci_20.SIGNALS, ci_20.scan),
)
