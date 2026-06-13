# ACI CI-ID Reference

What each active inspection ID detects, which lane produces it, and how much to
trust it. Active catalog = 22 IDs. The authoritative catalog is
`shared/core/aci-code-inspection-execution-spec.md`; this page is the
adoption-facing summary.

Lanes:
- **native-static** — ACI's own AST/text detector (Python).
- **external-analyzer** — produced by ruff / pyflakes / mypy / pytest (opt-in;
  only when installed and the profile enables them).
- **human-judgment** — surfaced for a human to decide; not auto-detected.

Confidence reflects how syntactic vs. heuristic the signal is. Treat `low` as a
discussion prompt, `high` as close to a confirmed defect.

## Native static detectors (Python)

| CI-ID | Name | Detects | Signal(s) | Confidence |
|---|---|---|---|---|
| CI-02 | Spaghetti Code | control-flow nesting depth >= 5; functions with >= 50 logical (code) lines | `CI02_SPAGHETTI_CODE`, `CI02_LONG_FUNCTION` | medium |
| CI-03 | Patchwork Code | leftover `TODO` / `FIXME` / `HACK` markers in comments | `CI03_TODO_HACK` | high |
| CI-04 | God Class | class with >= 20 non-dunder methods or >= 15 instance attributes | `CI04_GOD_CLASS` | medium |
| CI-05 | Copy-Paste Programming | identical function bodies (>= 4 statements) duplicated across 2+ files | `CI05_COPY_PASTE_CODE` | medium |
| CI-06 | Magic Number | numeric literal repeated across 3+ files (excludes small ints <= 16 and powers of two) | `CI06_MAGIC_NUMBER` | low |
| CI-12 | Poltergeist | tiny class that wraps one dependency and only delegates | `CI12_POLTERGEIST` | medium |
| CI-14 | Security Neglect | `eval`/`exec`; `subprocess(..., shell=True)`; plaintext secret literal; plain `http://` URL (comment/doctest lines skipped) | `CI14_DYNAMIC_CODE_EXECUTION`, `CI14_SUBPROCESS_SHELL_TRUE`, `CI14_PLAINTEXT_SECRET`, `CI14_INSECURE_HTTP` | high (secret, http: medium) |
| CI-18 | Data Clump | function/constructor with >= 6 positional parameters | `CI18_PARAMETER_CLUSTER` | medium |
| CI-19 | Feature Envy | domain side-program term used on an authority line (domain-aware; needs a domain pack) | `SIDE_PROGRAM_LEAK` | medium |
| CI-20 | Shotgun Surgery | string constant repeated across 3+ files (excludes `__all__` export names) | `CI20_SCATTERED_CONSTANT` | medium |
| CI-21 | Error Handling Rot | `except Exception:` that does not re-raise; handler that returns a silent sentinel | `CI21_BROAD_EXCEPTION_SWALLOW`, `CI21_SILENT_EXCEPTION_RETURN` | medium |
| CI-22 | Resource Lifecycle Leak | `open`/`Popen`/`*TemporaryFile` not wrapped in a `with` | `CI22_RESOURCE_CLEANUP_GAP` | low |
| CI-23 | Interface / Contract Drift | function hiding 2+ implicit fields behind `**kwargs` | `CI23_CONTRACT_FIELD_DRIFT` | low |
| CI-25 | Nondeterminism / Environment Drift | `datetime.now()`/`today()` without tz; `random.*` calls | `CI25_ENVIRONMENT_DRIFT` | high |
| CI-26 | Concurrency / Race Hazard | function mutating module-level state via `global` | `CI26_RACE_HAZARD` | high |

## External-analyzer lane (opt-in, no native detector)

These have no native ACI detector; they appear only when the named tool is
installed and the profile enables the external lane.

| CI-ID | Name | Produced by |
|---|---|---|
| CI-07 | Lava Flow (dead/unreachable code) | ruff, pyflakes |
| CI-09 | Test Rot | pytest |
| CI-13 | Dependency Rot | ruff, pyflakes |
| CI-15 | Documentation Rot | ruff, mypy |

## Human-judgment lane (not auto-detected by design)

Surfaced for human review; ACI does not attempt to detect these automatically
because a reliable, low-false-positive static rule does not exist.

| CI-ID | Name |
|---|---|
| CI-08 | Configuration Hell |
| CI-11 | Golden Hammer |
| CI-24 | Observability Gap |

## Retired IDs

`CI-01`, `CI-10`, `CI-16`, `CI-17`, `CI-27` are retired and will not be reassigned.

## Suppressing a finding

When a finding is a known, accepted case, route it through an operations file
instead of editing code (see `docs/QUICKSTART.md` §6):

- **baseline** — accept all current occurrences; only new ones fail the gate.
- **waiver** — explicitly excuse a specific finding with an id and reason.
- **suppression** — drop a finding from output entirely.

For systematic false positives in a detector itself, open an issue with the
fixture — detector precision is tuned against a real-corpus baseline (see
`shared/tools/aci_corpus_harness.py`).
