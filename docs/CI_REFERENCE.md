# ACI CI-ID Reference

What each active inspection ID detects, which lane produces it, and how much to
trust it. Active catalog = 22 IDs. The authoritative catalog is
`shared/core/aci-code-inspection-execution-spec.md`; this page is the
adoption-facing summary.

Lanes:
- **native-static**: ACI's own AST/text detector (Python).
- **external-analyzer**: produced by ruff / pyflakes / mypy / pytest / semgrep / eslint / tsc / shellcheck / sqlfluff (opt-in;
  only when installed and the profile enables them).
- **human-judgment**: surfaced for a human to decide; not auto-detected.

Confidence reflects how syntactic vs. heuristic the signal is. Treat `low` as a
discussion prompt, `high` as close to a confirmed defect.

## Native static detectors (Python)

`vs ruff`: **unique** = a cross-file/structural check ruff cannot do (ACI's core
value); **overlaps** = ruff can cover this *when configured for the matching
rule* (e.g. C901/PLR0915). ACI always runs its native detector and dedupes only
where the ruff lane actually reports the same finding — so enabling ruff never
silently drops a native signal ruff's active rules don't emit (see README
"Relationship to ruff").

| CI-ID | Name | Detects | Confidence | vs ruff |
|---|---|---|---|---|
| CI-02 | Spaghetti Code | nesting depth >= 5 **and** cyclomatic complexity >= 8; or a long function (>= 80 logical lines **and** complexity >= 15; long-but-flat builders are spared) | medium | overlaps (C901/PLR0915) |
| CI-03 | Patchwork Code | leftover `TODO` / `FIXME` / `HACK` markers | high | overlaps (TD/FIX) |
| CI-04 | God Class | large class (>= 15 methods) split into >= 2 substantial responsibility clusters (low LCOM cohesion) | medium | **unique** |
| CI-05 | Copy-Paste Programming | rename-invariant structural near-duplicate function bodies (>= 18 nodes) across 2+ files; one finding per file-set. Recall limit: the signature is structure-exact, so a clone with an inserted/removed/reordered statement is missed (favors precision over fuzzy matching). | medium | **unique** |
| CI-06 | Magic Number | numeric literal repeated across 3+ files (cross-file; excludes data-collection members, sub-byte ints, powers of two) | low | **unique** (cross-file) |
| CI-07 | Lava Flow (dead private symbol) | module-level private `_name` function/class referenced nowhere in the whole project (cross-file; excludes decorated, `__all__`, string-referenced). Blind spot: cannot see references from compiled extensions (`.pyd`/`.so`); a Rust/C callback target may look unused. | medium | **unique** (cross-file) |
| CI-12 | Poltergeist | tiny class that wraps one dependency and only delegates | medium | unique |
| CI-13 | Dependency Rot (circular import) | cross-file import cycles (strongly-connected import graph; stdlib-shadowing-safe, TYPE_CHECKING/deferred imports excluded) | high | **unique** (cross-file) |
| CI-14 | Security Neglect | `eval`/`exec`; `subprocess(shell=True)` (AST; nested-call args handled); plaintext secret (AST); plain `http://` (docstrings/comments skipped); unsafe YAML / deserialization. Subprocess, deserialization, and YAML resolve static import aliases (`import pickle as p`, `from pickle import loads`) to their canonical name; residual blind spot is variable/dynamic-import indirection (`KL-ACI-CI14-CI25-IMPORT-ALIAS`). Plus bounded supply-chain drift checks (`requirements*.txt`, `pyproject.toml`, `package.json`, container base tags, GitHub Actions refs), and a bounded **intra-procedural taint flow** check (`CI14_TAINTED_FLOW`): untrusted input (`input()`, `os.environ`/`os.getenv`, `sys.argv`, `request.*`) reaching a dangerous sink (`eval`/`exec`, `os.system`/`os.popen`, `subprocess(shell=True)`, `cursor.execute`) in the same function, propagated through assignments / f-strings / concatenation / string methods. Inter-procedural flow and container aliasing are out of scope (`KL-ACI-CI14-TAINT-INTRAPROCEDURAL`) | high (secret/http/supply-chain: medium) | partial (bandit S); ACI finds more |
| CI-18 | Data Clump | function with >= 6 **required** positional params (optional kwargs / framework signatures excluded) | medium | overlaps (PLR0913) |
| CI-19 | Feature Envy | domain side-program term on an authority line (domain-aware; needs a domain pack). `core-only` does not claim substantive CI-19 coverage. | medium | unique |
| CI-20 | Shotgun Surgery | value-shaped string literal (URI/connection string, filesystem/route path, or format template) repeated across 3+ files (cross-file; bare words, tags, header and symbol names excluded by a shape allowlist) | medium | **unique** (cross-file) |
| CI-21 | Error Handling Rot | `except Exception:` that does not re-raise (excl. module-level fallbacks); silent-sentinel return | medium | overlaps (BLE) |
| CI-22 | Resource Lifecycle Leak | opener (`open`/`Popen`/`*TemporaryFile`) whose handle is not managed: not returned, stored on an attribute, used in `with`/`closing(...)`, closed in the same suite, closed exception-safely (`try/finally` or `try/except/else`), or registered to an `ExitStack` (`enter_context`/`push`/`callback`/`push_async_callback`). Cleanup spellings (bound method, `os.close`, `close(handle)`, `functools.partial`, lambda, local helper, registrar aliases) are resolved by one recursive predicate rather than enumerated. Recall limit: non-local helper ownership transfer stays conservative (`KL-ACI-CI22-NONLOCAL-LIFECYCLE`). | medium | partial (SIM115); ACI dataflow-aware |
| CI-23 | Interface / Contract Drift | function hiding 2+ implicit fields behind `**kwargs` | low | **unique** |
| CI-25 | Nondeterminism / Environment Drift | naive `datetime.now()`/`today()` (no tz; static import aliases such as `import datetime as dt; dt.datetime.now()` resolved); `random.*` draw | datetime: medium; random: low | partial (DTZ/S311) |
| CI-26 | Concurrency / Race Hazard | function mutating module-level state via `global` | high | overlaps (PLW0603) |

## External-analyzer lane (opt-in, no native detector)

These have no native ACI detector; they appear only when the named tool is
installed and the profile enables the external lane.

| CI-ID | Name | Produced by |
|---|---|---|
| CI-02 | Spaghetti / style-quality proxy from external lint | eslint, shellcheck, sqlfluff |
| CI-07 | Lava Flow (single-file unused) | ruff, pyflakes; complements ACI's native cross-file dead-private-symbol detector above |
| CI-09 | Test Rot | pytest |
| CI-13 | Dependency Rot (unused/outdated imports) | ruff, pyflakes; complements ACI's native circular-import detector above |
| CI-14 | Security Neglect | semgrep baseline rules, eslint security-style rules |
| CI-15 | Documentation Rot | ruff, mypy |
| CI-21 | Error Handling Rot | shellcheck, ruff |
| CI-23 | Interface / Contract Drift | mypy, eslint, tsc |

## Human-judgment lane (not auto-detected by design)

Surfaced for human review; ACI does not attempt to detect these automatically
because a reliable, low-false-positive static rule does not exist.

This is a product boundary, not a temporary omission. See
`shared/core/aci-product-boundary-and-coverage-policy.md`.

| CI-ID | Name |
|---|---|
| CI-08 | Configuration Hell |
| CI-11 | Golden Hammer |
| CI-24 | Observability Gap |

## Retired IDs

`CI-01`, `CI-10`, `CI-16`, `CI-17`, `CI-27` are retired and will not be reassigned.

## Suppressing a finding

When a finding is a known, accepted case, route it through an operations file
instead of editing code (see `docs/QUICKSTART.md` section 6):

- **baseline**: accept all current occurrences; only new ones fail the gate.
- **waiver**: explicitly excuse a specific finding with an id and reason.
- **suppression**: drop a finding from output entirely.

For systematic false positives in a detector itself, open an issue with the
fixture; detector precision is tuned against a real-corpus baseline (see
`shared/tools/aci_corpus_harness.py`).

## Profile and signal scope

Profiles control which signals (and therefore which detectors) are active per run.

**Generic ACI (no domain pack)**: use `quick-gate` or `full`. These profiles activate
all native CI-xx detectors via the `native_hygiene_signals` group.

**Workflow profiles** (`startup`, `wrap-up`, `state-change`, `build-preflight`,
`build-review`) include structure signals (`RESPONSIBILITY_SPROUT`,
`OPERATOR_VIEW_GAP`, `STATE_DUPLICATION`, `SIDE_PROGRAM_LEAK`). These are domain-pack
vocabulary signals with no native detector in generic ACI core.
Running a workflow profile without a domain pack produces findings when:
- `startup` includes CI-04, CI-12, CI-02; structural quality detectors active without a domain pack
- `state-change` / `build-*` include additional native CI-xx signals (e.g. CI-21, CI-22)
- a domain pack with `side_program_terms` is loaded (enables the `SIDE_PROGRAM_LEAK` detector)

The human-judgment lane (`_HUMAN_JUDGMENT_SIGNALS = ()`) is intentionally empty:
CI-08, CI-11, and CI-24 are classified as human-judgment only; no reliable static
rule exists for them (see the human-judgment table above).

## Language scope

ACI is **Python-first**. The native structural detectors are Python-only, but the
scan surface also accepts supported non-Python text/code files so the text-scan
detectors and applicable external analyzers can run.

| File type | Coverage |
|---|---|
| `.py` | Full; native Python AST detectors, text scans, and Python external analyzers |
| `.js` / `.jsx` / `.ts` / `.tsx` | Text scans + semgrep + eslint (and `tsc` when `tsconfig.json` is present) |
| `.go` / `.rs` / `.java` / `.cs` / `.kt` / `.kts` / `Dockerfile` / `Containerfile` / `.tf` / `.hcl` | Text scans + semgrep baseline rules |
| `.sh` / `.bash` | Text scans + shellcheck |
| `.sql` | Text scans + sqlfluff |
| `.md` / `.txt` / `.toml` / `.yml` / `.yaml` / `.json` | Text scans only |

The external-analyzer lane inherits whatever language support those tools provide,
but ACI's own structural analysis remains Python-native.

If your codebase is primarily non-Python, the native lane will have no coverage;
use dedicated tools for other languages.

## CI-14 Supply-Chain Scope

The current common-shelf CI-14 supply-chain detector intentionally covers:

- `requirements*.txt`
- `pyproject.toml` dependency surfaces (`project.dependencies`, optional dependencies, dependency groups, Poetry dependency tables)
- `package.json`
- `Dockerfile` / `Containerfile`
- GitHub workflow `uses:` refs

It does not currently claim general manifest/lockfile coverage for surfaces
such as `poetry.lock`, `package-lock.json`, `pnpm-lock.yaml`,
`Cargo.lock`, or `go.mod`.

## CI-22 Managed-Lifecycle Forms

CI-22 treats a handle as managed when its lifecycle is guaranteed by any of:
`with` / `closing(...)`, return, attribute-store, a same-suite close, an
exception-safe close (`try/finally` or `try/except/else`), or registration to an
`ExitStack` via `enter_context` / `push` / `callback` / `push_async_callback`.

The cleanup target may be spelled as a bound `handle.close`, `os.close(fd)`,
`close(handle)`, a `functools.partial(...)` wrapper, a lambda, a local helper
`def`, or any name aliased to those (including registrar aliases such as
`register = stack.callback`). These are not enumerated case by case: one recursive
predicate resolves "does calling this expression close the handle?" through
assignments, partials, lambdas, defs, and aliases, so every combination is covered
by construction.

Recall limit: ownership transfer through non-local helper calls and broad
exception-path reasoning remain intentionally conservative
(`KL-ACI-CI22-NONLOCAL-LIFECYCLE`).
