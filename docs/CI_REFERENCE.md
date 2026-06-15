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

`vs ruff`: **unique** = a cross-file/structural check ruff cannot do (ACI's core
value); **overlaps** = ruff already covers this (prefer ruff; ACI auto-dedupes
its native finding when the ruff lane runs — see README "Relationship to ruff").

| CI-ID | Name | Detects | Confidence | vs ruff |
|---|---|---|---|---|
| CI-02 | Spaghetti Code | nesting depth >= 5 **and** cyclomatic complexity >= 8; or a long function (>= 50 logical lines **and** complexity >= 10, or >= 120 lines regardless of complexity — a flat long `__init__`/config builder is spared) | medium | overlaps (C901/PLR0915) |
| CI-03 | Patchwork Code | leftover `TODO` / `FIXME` / `HACK` markers | high | overlaps (TD/FIX) |
| CI-04 | God Class | large class (>= 15 methods) split into >= 2 substantial responsibility clusters (low LCOM cohesion) | medium | **unique** |
| CI-05 | Copy-Paste Programming | rename-invariant structural near-duplicate function bodies (>= 18 nodes) across 2+ files; one finding per file-set. Recall limit: the signature is structure-exact, so a clone with an inserted/removed/reordered statement is missed (favors precision over fuzzy matching). | medium | **unique** |
| CI-06 | Magic Number | numeric literal repeated across 3+ files (cross-file; excludes data-collection members, sub-byte ints, powers of two) | low | **unique** (cross-file) |
| CI-07 | Lava Flow (dead private symbol) | module-level private `_name` function/class referenced nowhere in the whole project (cross-file; excludes decorated, `__all__`, string-referenced). Blind spot: cannot see references from compiled extensions (`.pyd`/`.so`) — a Rust/C callback target looks unused. | medium | **unique** (cross-file) |
| CI-12 | Poltergeist | tiny class that wraps one dependency and only delegates | medium | unique |
| CI-13 | Dependency Rot (circular import) | cross-file import cycles (strongly-connected import graph; stdlib-shadowing-safe, TYPE_CHECKING/deferred imports excluded) | high | **unique** (cross-file) |
| CI-14 | Security Neglect | `eval`/`exec`; `subprocess(shell=True)`; plaintext secret (AST); plain `http://` (docstrings/comments skipped) | high (secret/http: medium) | partial (bandit S); ACI finds more |
| CI-18 | Data Clump | function with >= 6 **required** positional params (optional kwargs / framework signatures excluded) | medium | overlaps (PLR0913) |
| CI-19 | Feature Envy | domain side-program term on an authority line (domain-aware; needs a domain pack) | medium | unique |
| CI-20 | Shotgun Surgery | value-shaped string literal (URI/connection string, filesystem/route path, or format template) repeated across 3+ files (cross-file; bare words, tags, header and symbol names excluded by a shape allowlist) | medium | **unique** (cross-file) |
| CI-21 | Error Handling Rot | `except Exception:` that does not re-raise (excl. module-level fallbacks); silent-sentinel return | medium | overlaps (BLE) |
| CI-22 | Resource Lifecycle Leak | opener (`open`/`Popen`/`*TemporaryFile`) whose handle is not returned / stored on an attribute / wrapped / deferred via a `lambda` factory / closed / used in `with` (dataflow). Recall limit: a handle closed only on the success path (a bare `.close()` with no `try/finally`) is treated as managed; exception-path leaks are not traced. | medium | partial (SIM115); ACI dataflow-aware |
| CI-23 | Interface / Contract Drift | function hiding 2+ implicit fields behind `**kwargs` | low | **unique** |
| CI-25 | Nondeterminism / Environment Drift | naive `datetime.now()`/`today()` (no tz); `random.*` draw | datetime: medium; random: low | partial (DTZ/S311) |
| CI-26 | Concurrency / Race Hazard | function mutating module-level state via `global` | high | overlaps (PLW0603) |

## External-analyzer lane (opt-in, no native detector)

These have no native ACI detector; they appear only when the named tool is
installed and the profile enables the external lane.

| CI-ID | Name | Produced by |
|---|---|---|
| CI-07 | Lava Flow (single-file unused) | ruff, pyflakes — complements ACI's native cross-file dead-private-symbol detector above |
| CI-09 | Test Rot | pytest |
| CI-13 | Dependency Rot (unused/outdated imports) | ruff, pyflakes — complements ACI's native circular-import detector above |
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

## Language scope

ACI is a **Python-only** tool. Every native-static detector checks `path.suffix == ".py"`
and returns early for all other file types.

| File type | Coverage |
|---|---|
| `.py` | Full — all active CI-IDs via Python AST |
| All other types | Not scanned by native-static lane |

The external-analyzer lane (ruff / pyflakes / mypy) inherits whatever language support
those tools provide, but ACI itself makes no attempt to scan non-Python files.

If your codebase is primarily non-Python, the native lane will have no coverage — use
dedicated tools for other languages.
