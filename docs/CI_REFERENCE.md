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
value); **overlaps** = ruff already covers this (prefer ruff; ACI auto-dedupes
its native finding when the ruff lane runs; see README "Relationship to ruff").

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
| CI-14 | Security Neglect | `eval`/`exec`; `subprocess(shell=True)`; plaintext secret (AST); plain `http://` (docstrings/comments skipped); unsafe YAML / deserialization; bounded supply-chain drift checks (`requirements*.txt`, `pyproject.toml`, `package.json`, container base tags, GitHub Actions refs) | high (secret/http/supply-chain: medium) | partial (bandit S); ACI finds more |
| CI-18 | Data Clump | function with >= 6 **required** positional params (optional kwargs / framework signatures excluded) | medium | overlaps (PLR0913) |
| CI-19 | Feature Envy | domain side-program term on an authority line (domain-aware; needs a domain pack). `core-only` does not claim substantive CI-19 coverage. | medium | unique |
| CI-20 | Shotgun Surgery | value-shaped string literal (URI/connection string, filesystem/route path, or format template) repeated across 3+ files (cross-file; bare words, tags, header and symbol names excluded by a shape allowlist) | medium | **unique** (cross-file) |
| CI-21 | Error Handling Rot | `except Exception:` that does not re-raise (excl. module-level fallbacks); silent-sentinel return | medium | overlaps (BLE) |
| CI-22 | Resource Lifecycle Leak | opener (`open`/`Popen`/`*TemporaryFile`) whose handle is not returned / stored on an attribute / wrapped / exception-safely closed / used in `with` (dataflow; includes straight-line same-suite explicit close calls such as `handle.close()`, `close(handle)`, or `os.close(fd)`, same-suite close-alias calls such as `cleanup = handle.close; cleanup()`, `cleanup = close; cleanup(handle)`, or `cleanup = os.close; cleanup(fd)`, same-suite lambda close-alias executions such as `cleanup = lambda: handle.close(); cleanup()`, `cleanup = lambda managed=handle: managed.close(); cleanup()`, `cleanup = lambda managed=handle: close(managed); cleanup()`, `cleanup = lambda: close(handle); cleanup()`, `cleanup = lambda: os.close(fd); cleanup()`, `cleanup = lambda managed: managed.close(); cleanup(handle)`, or `cleanup = lambda raw_fd: os.close(raw_fd); cleanup(fd)`, `try/finally`, explicit `try/except/else` close paths, helper context-manager wrapping such as `closing(handle)`, managed `ExitStack` / `AsyncExitStack` registration via `enter_context(...)` or `enter_async_context(...)` including `enter_context(closing(handle))`, `enter_context(closing(open(path)))`, `await stack.enter_async_context(handle)`, `await stack.enter_async_context(open(path))`, local enter-context registrar aliases such as `register = stack.enter_context; register(handle)`, `register(closing(handle))`, `handle = register(open(path))`, or `handle = register(managed)`, async enter-context registrar aliases such as `register = stack.enter_async_context; await register(handle)` or `handle = await register(open(path))`, locally assigned `closing(handle)` or `closing(open(path))` wrappers, `push(handle)`, `push(closing(handle))`, `push(closing(open(path)))`, local push-registrar aliases such as `register = stack.push; register(handle)`, `register(closing(handle))`, `register(closing(open(path)))`, `handle = register(open(path))`, or `register(managed)`, locally assigned `closing(...)` wrappers pushed via `stack.push(managed)`, direct or lambda-wrapped close callbacks including local callback-registrar aliases such as `register = stack.callback; register(handle.close)`, `register(os.close, fd)`, `register(lambda: handle.close())`, `register(lambda managed=handle: managed.close())`, `register(cleanup)`, or callback-supplied-arg lambda forms such as `register(lambda managed: managed.close(), handle)` or `register(lambda raw_fd: os.close(raw_fd), fd)`, direct or locally assigned `functools.partial(...)` close wrappers such as `stack.callback(partial(handle.close))`, `stack.callback(partial(os.close, fd))`, `stack.callback(partial(close, handle))`, `stack.callback(partial(cleanup_fn, handle))` after `cleanup_fn = close`, `stack.callback(partial(cleanup_fn))` after `cleanup_fn = handle.close`, `stack.callback(partial(cleanup_fn))` after `def cleanup(): close(handle); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn))` after `def cleanup(): handle.close(); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn, fd))` after `cleanup_fn = os.close`, `stack.callback(partial(cleanup_fn, handle))` after `def cleanup(managed): managed.close(); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn, fd))` after `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn))` after `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn))` after `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup`, `stack.callback(partial(cleanup_fn))` after `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup`, `register = stack.callback; register(partial(handle.close))`, `register = stack.callback; register(partial(os.close, fd))`, `register = stack.callback; register(partial(cleanup_fn, handle))` after `cleanup_fn = close`, `register = stack.callback; register(partial(cleanup_fn))` after `cleanup_fn = handle.close`, `register = stack.callback; register(partial(cleanup_fn))` after `def cleanup(): close(handle); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn))` after `def cleanup(): handle.close(); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn, fd))` after `cleanup_fn = os.close`, `register = stack.callback; register(partial(cleanup_fn, handle))` after `def cleanup(managed): managed.close(); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn, fd))` after `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn))` after `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn))` after `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup`, `register = stack.callback; register(partial(cleanup_fn))` after `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup`, `cleanup = partial(handle.close); stack.callback(cleanup)`, `cleanup = partial(close, handle); stack.callback(cleanup)`, `cleanup = partial(os.close, fd); stack.callback(cleanup)`, `cleanup_fn = close; cleanup = partial(cleanup_fn, handle); stack.callback(cleanup)`, `cleanup_fn = handle.close; cleanup = partial(cleanup_fn); stack.callback(cleanup)`, `def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`, `def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`, `register = stack.callback; def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.callback; def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`, `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`, `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`, `register = stack.callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.callback; def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.callback; def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.callback; cleanup_fn = handle.close; cleanup = partial(cleanup_fn); register(cleanup)`, `register = stack.callback; cleanup_fn = close; cleanup = partial(cleanup_fn, handle); register(cleanup)`, `register = stack.callback; cleanup = partial(handle.close); register(cleanup)`, `register = stack.callback; cleanup = partial(os.close, fd); register(cleanup)`, `register = stack.callback; cleanup = partial(close, handle); register(cleanup)`, `stack.push_async_callback(partial(handle.close))`, `stack.push_async_callback(partial(os.close, fd))`, `stack.push_async_callback(partial(close, handle))`, `stack.push_async_callback(partial(cleanup_fn, handle))` after `cleanup_fn = close`, `stack.push_async_callback(partial(cleanup_fn))` after `cleanup_fn = handle.close`, `stack.push_async_callback(partial(cleanup_fn))` after `def cleanup(): close(handle); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn))` after `def cleanup(): handle.close(); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn, fd))` after `cleanup_fn = os.close`, `stack.push_async_callback(partial(cleanup_fn, handle))` after `def cleanup(managed): managed.close(); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn, fd))` after `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn))` after `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn))` after `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup`, `stack.push_async_callback(partial(cleanup_fn))` after `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup`, `cleanup = partial(handle.close); stack.push_async_callback(cleanup)`, `cleanup = partial(close, handle); stack.push_async_callback(cleanup)`, `cleanup = partial(os.close, fd); stack.push_async_callback(cleanup)`, `cleanup_fn = close; cleanup = partial(cleanup_fn, handle); stack.push_async_callback(cleanup)`, `cleanup_fn = handle.close; cleanup = partial(cleanup_fn); stack.push_async_callback(cleanup)`, `def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`, `def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`, `cleanup_fn = os.close; cleanup = partial(cleanup_fn, fd); stack.push_async_callback(cleanup)`, `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`, `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`, `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`, `register = stack.push_async_callback; register(partial(handle.close))`, `register = stack.push_async_callback; register(partial(os.close, fd))`, `register = stack.push_async_callback; register(partial(close, handle))`, `register = stack.push_async_callback; register(partial(cleanup_fn, handle))` after `cleanup_fn = close`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `cleanup_fn = handle.close`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `def cleanup(): close(handle); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `def cleanup(): handle.close(); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn, fd))` after `cleanup_fn = os.close`, `register = stack.push_async_callback; register(partial(cleanup_fn, handle))` after `def cleanup(managed): managed.close(); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn, fd))` after `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup`, `register = stack.push_async_callback; register(partial(cleanup_fn))` after `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup`, `register = stack.push_async_callback; cleanup = partial(handle.close); register(cleanup)`, `register = stack.push_async_callback; cleanup = partial(os.close, fd); register(cleanup)`, `register = stack.push_async_callback; cleanup_fn = close; cleanup = partial(cleanup_fn, handle); register(cleanup)`, `register = stack.push_async_callback; cleanup_fn = handle.close; cleanup = partial(cleanup_fn); register(cleanup)`, `register = stack.push_async_callback; def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.push_async_callback; def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.push_async_callback; def cleanup(managed=handle): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, `register = stack.push_async_callback; def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`, or `register = stack.push_async_callback; cleanup = partial(close, handle); register(cleanup)`, assigned bound-close aliases such as `cleanup = handle.close; stack.callback(cleanup)`, `register = stack.callback; cleanup = handle.close; register(cleanup)`, assigned `os.close` aliases such as `cleanup = os.close; stack.callback(cleanup, fd)`, assigned lambda aliases such as `cleanup = lambda: handle.close(); stack.callback(cleanup)`, callback-supplied-arg lambda aliases such as `cleanup = lambda managed: managed.close(); stack.callback(cleanup, handle)` or `cleanup = lambda raw_fd: os.close(raw_fd); stack.callback(cleanup, fd)`, default-bound aliases such as `lambda managed=handle: managed.close()`, async callback cleanup such as `stack.push_async_callback(handle.close)`, `stack.push_async_callback(os.close, fd)`, `stack.push_async_callback(lambda managed: managed.close(), handle)`, `stack.push_async_callback(lambda managed=handle: managed.close())`, `stack.push_async_callback(lambda raw_fd: os.close(raw_fd), fd)`, `cleanup = handle.close; stack.push_async_callback(cleanup)`, `register = stack.push_async_callback; register(handle.close)`, `register = stack.push_async_callback; cleanup = handle.close; register(cleanup)`, `register = stack.push_async_callback; register(os.close, fd)`, `register = stack.push_async_callback; register(lambda raw_fd: os.close(raw_fd), fd)`, `cleanup = os.close; stack.push_async_callback(cleanup, fd)`, `cleanup = lambda managed: managed.close(); stack.push_async_callback(cleanup, handle)`, `cleanup = lambda managed=handle: managed.close(); stack.push_async_callback(cleanup)`, `cleanup = lambda raw_fd: os.close(raw_fd); stack.push_async_callback(cleanup, fd)`, `register = stack.push_async_callback; cleanup = os.close; register(cleanup, fd)`, `register = stack.push_async_callback; cleanup = lambda managed: managed.close(); register(cleanup, handle)`, `register = stack.push_async_callback; cleanup = lambda managed=handle: managed.close(); register(cleanup)`, `register = stack.push_async_callback; cleanup = lambda raw_fd: os.close(raw_fd); register(cleanup, fd)`, `cleanup = lambda: handle.close(); stack.push_async_callback(cleanup)`, or `register = stack.push_async_callback; cleanup = lambda: handle.close(); register(cleanup)`, and local `stack = ExitStack(); with stack:` management). Recall limit: ownership transfers through helper calls and non-local lifecycle reasoning remain intentionally conservative. | medium | partial (SIM115); ACI dataflow-aware |
| CI-23 | Interface / Contract Drift | function hiding 2+ implicit fields behind `**kwargs` | low | **unique** |
| CI-25 | Nondeterminism / Environment Drift | naive `datetime.now()`/`today()` (no tz); `random.*` draw | datetime: medium; random: low | partial (DTZ/S311) |
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

## CI-22 Callback Helper Forms

The callback-helper examples below are representative bounded same-function
patterns, not a general callback or ownership-transfer proof.
`CI-22` recognizes only local, explainable helper registration forms where the
cleanup target and helper definition stay in the same function body.
Broader non-local helper ownership transfer and wider exception-path reasoning
remain intentionally conservative.

CI-22 also treats local callback helper forms as safe management when the
cleanup target is passed directly as a callback argument, including:

- `stack.callback(close, handle)`
- `register = stack.callback; register(close, handle)`
- `cleanup = close; stack.callback(cleanup, handle)`
- `register = stack.callback; cleanup = close; register(cleanup, handle)`
- `stack.push_async_callback(close, handle)`
- `register = stack.push_async_callback; register(close, handle)`
- `cleanup = close; stack.push_async_callback(cleanup, handle)`
- `register = stack.push_async_callback; cleanup = close; register(cleanup, handle)`

CI-22 also treats local helper-lambda callback forms as safe management,
including:

- `stack.callback(lambda managed: close(managed), handle)`
- `register = stack.callback; register(lambda managed: close(managed), handle)`
- `stack.callback(lambda managed=handle: close(managed))`
- `register = stack.callback; register(lambda managed=handle: close(managed))`
- `cleanup = lambda managed: close(managed); stack.callback(cleanup, handle)`
- `register = stack.callback; cleanup = lambda managed: close(managed); register(cleanup, handle)`
- `cleanup = lambda managed=handle: close(managed); stack.callback(cleanup)`
- `register = stack.callback; cleanup = lambda managed=handle: close(managed); register(cleanup)`
- `stack.push_async_callback(lambda managed: close(managed), handle)`
- `stack.push_async_callback(lambda managed=handle: close(managed))`
- `cleanup = lambda managed: close(managed); stack.push_async_callback(cleanup, handle)`
- `cleanup = lambda managed=handle: close(managed); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; register(lambda managed: close(managed), handle)`
- `register = stack.push_async_callback; register(lambda managed=handle: close(managed))`
- `register = stack.push_async_callback; cleanup = lambda managed: close(managed); register(cleanup, handle)`
- `register = stack.push_async_callback; cleanup = lambda managed=handle: close(managed); register(cleanup)`

CI-22 also treats zero-arg generic `close(handle)` helper-lambda callback forms
as safe management, including:

- `stack.callback(lambda: close(handle))`
- `register = stack.callback; register(lambda: close(handle))`
- `cleanup = lambda: close(handle); stack.callback(cleanup)`
- `register = stack.callback; cleanup = lambda: close(handle); register(cleanup)`
- `stack.push_async_callback(lambda: close(handle))`
- `register = stack.push_async_callback; register(lambda: close(handle))`
- `cleanup = lambda: close(handle); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; cleanup = lambda: close(handle); register(cleanup)`

CI-22 also treats local zero-arg helper-definition callback forms as safe
management, including:

- `def cleanup(): close(handle); stack.callback(cleanup)`
- `register = stack.callback; def cleanup(): close(handle); register(cleanup)`
- `def cleanup(): close(handle); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; def cleanup(): close(handle); register(cleanup)`
- `def cleanup(): handle.close(); stack.callback(cleanup)`
- `register = stack.callback; def cleanup(): handle.close(); register(cleanup)`
- `def cleanup(): handle.close(); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; def cleanup(): handle.close(); register(cleanup)`
- `def cleanup(managed=handle): close(managed); stack.callback(cleanup)`
- `register = stack.callback; def cleanup(managed=handle): close(managed); register(cleanup)`
- `def cleanup(managed=handle): close(managed); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); register(cleanup)`
- `def cleanup(managed=handle): managed.close(); stack.callback(cleanup)`
- `register = stack.callback; def cleanup(managed=handle): managed.close(); register(cleanup)`
- `def cleanup(managed=handle): managed.close(); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; def cleanup(managed=handle): managed.close(); register(cleanup)`
- `def cleanup(raw_fd=fd): os.close(raw_fd); stack.callback(cleanup)`
- `register = stack.callback; def cleanup(raw_fd=fd): os.close(raw_fd); register(cleanup)`
- `def cleanup(raw_fd=fd): os.close(raw_fd); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; def cleanup(raw_fd=fd): os.close(raw_fd); register(cleanup)`

CI-22 also treats local helper-definition callback-with-arg forms as safe
management, including:

- `def cleanup(managed): close(managed); stack.callback(cleanup, handle)`
- `register = stack.callback; def cleanup(managed): close(managed); register(cleanup, handle)`
- `def cleanup(managed): close(managed); stack.push_async_callback(cleanup, handle)`
- `register = stack.push_async_callback; def cleanup(managed): close(managed); register(cleanup, handle)`
- `def cleanup(managed): managed.close(); stack.callback(cleanup, handle)`
- `register = stack.callback; def cleanup(managed): managed.close(); register(cleanup, handle)`
- `def cleanup(managed): managed.close(); stack.push_async_callback(cleanup, handle)`
- `register = stack.push_async_callback; def cleanup(managed): managed.close(); register(cleanup, handle)`
- `def cleanup(raw_fd): os.close(raw_fd); stack.callback(cleanup, fd)`
- `register = stack.callback; def cleanup(raw_fd): os.close(raw_fd); register(cleanup, fd)`
- `def cleanup(raw_fd): os.close(raw_fd); stack.push_async_callback(cleanup, fd)`
- `register = stack.push_async_callback; def cleanup(raw_fd): os.close(raw_fd); register(cleanup, fd)`

CI-22 also treats `partial(...)` wrappers around local helper definitions as
safe management, including:

- `def cleanup(): close(handle); stack.callback(partial(cleanup))`
- `def cleanup(): close(handle); cleanup_cb = partial(cleanup); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(): close(handle); register(partial(cleanup))`
- `register = stack.callback; def cleanup(): close(handle); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `def cleanup(): close(handle); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn))`
- `def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(): close(handle); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.callback; def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(): close(handle); stack.push_async_callback(partial(cleanup))`
- `def cleanup(): close(handle); cleanup_cb = partial(cleanup); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(): close(handle); register(partial(cleanup))`
- `register = stack.push_async_callback; def cleanup(): close(handle); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `def cleanup(): close(handle); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn))`
- `def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(): close(handle); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.push_async_callback; def cleanup(): close(handle); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(): handle.close(); stack.callback(partial(cleanup))`
- `def cleanup(): handle.close(); cleanup_cb = partial(cleanup); stack.callback(cleanup_cb)`
- `def cleanup(): handle.close(); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn))`
- `def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(): handle.close(); register(partial(cleanup))`
- `register = stack.callback; def cleanup(): handle.close(); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `register = stack.callback; def cleanup(): handle.close(); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.callback; def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(): handle.close(); stack.push_async_callback(partial(cleanup))`
- `def cleanup(): handle.close(); cleanup_cb = partial(cleanup); stack.push_async_callback(cleanup_cb)`
- `def cleanup(): handle.close(); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn))`
- `def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(): handle.close(); register(partial(cleanup))`
- `register = stack.push_async_callback; def cleanup(): handle.close(); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(): handle.close(); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.push_async_callback; def cleanup(): handle.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(managed): close(managed); stack.callback(partial(cleanup, handle))`
- `def cleanup(managed): close(managed); cleanup_cb = partial(cleanup, handle); stack.callback(cleanup_cb)`
- `def cleanup(managed): close(managed); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn, handle))`
- `register = stack.callback; def cleanup(managed): close(managed); register(partial(cleanup, handle))`
- `register = stack.callback; def cleanup(managed): close(managed); cleanup_cb = partial(cleanup, handle); register(cleanup_cb)`
- `register = stack.callback; def cleanup(managed): close(managed); cleanup_fn = cleanup; register(partial(cleanup_fn, handle))`
- `def cleanup(managed): close(managed); stack.push_async_callback(partial(cleanup, handle))`
- `def cleanup(managed): close(managed); cleanup_cb = partial(cleanup, handle); stack.push_async_callback(cleanup_cb)`
- `def cleanup(managed): close(managed); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn, handle))`
- `register = stack.push_async_callback; def cleanup(managed): close(managed); register(partial(cleanup, handle))`
- `register = stack.push_async_callback; def cleanup(managed): close(managed); cleanup_cb = partial(cleanup, handle); register(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed): close(managed); cleanup_fn = cleanup; register(partial(cleanup_fn, handle))`
- `def cleanup(managed): managed.close(); stack.callback(partial(cleanup, handle))`
- `def cleanup(managed): managed.close(); cleanup_cb = partial(cleanup, handle); stack.callback(cleanup_cb)`
- `def cleanup(managed): managed.close(); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn, handle))`
- `def cleanup(managed): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, handle); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(managed): managed.close(); register(partial(cleanup, handle))`
- `register = stack.callback; def cleanup(managed): managed.close(); cleanup_cb = partial(cleanup, handle); register(cleanup_cb)`
- `register = stack.callback; def cleanup(managed): managed.close(); cleanup_fn = cleanup; register(partial(cleanup_fn, handle))`
- `register = stack.callback; def cleanup(managed): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, handle); register(cleanup_cb)`
- `def cleanup(managed): managed.close(); stack.push_async_callback(partial(cleanup, handle))`
- `def cleanup(managed): managed.close(); cleanup_cb = partial(cleanup, handle); stack.push_async_callback(cleanup_cb)`
- `def cleanup(managed): managed.close(); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn, handle))`
- `def cleanup(managed): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, handle); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed): managed.close(); register(partial(cleanup, handle))`
- `register = stack.push_async_callback; def cleanup(managed): managed.close(); cleanup_cb = partial(cleanup, handle); register(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed): managed.close(); cleanup_fn = cleanup; register(partial(cleanup_fn, handle))`
- `register = stack.push_async_callback; def cleanup(managed): managed.close(); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, handle); register(cleanup_cb)`
- `def cleanup(raw_fd): os.close(raw_fd); stack.callback(partial(cleanup, fd))`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_cb = partial(cleanup, fd); stack.callback(cleanup_cb)`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn, fd))`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, fd); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(raw_fd): os.close(raw_fd); register(partial(cleanup, fd))`
- `register = stack.callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_cb = partial(cleanup, fd); register(cleanup_cb)`
- `register = stack.callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; register(partial(cleanup_fn, fd))`
- `register = stack.callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, fd); register(cleanup_cb)`
- `def cleanup(raw_fd): os.close(raw_fd); stack.push_async_callback(partial(cleanup, fd))`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_cb = partial(cleanup, fd); stack.push_async_callback(cleanup_cb)`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn, fd))`
- `def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, fd); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(raw_fd): os.close(raw_fd); register(partial(cleanup, fd))`
- `register = stack.push_async_callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_cb = partial(cleanup, fd); register(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; register(partial(cleanup_fn, fd))`
- `register = stack.push_async_callback; def cleanup(raw_fd): os.close(raw_fd); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn, fd); register(cleanup_cb)`
- `def cleanup(managed=handle): close(managed); stack.callback(partial(cleanup))`
- `def cleanup(managed=handle): close(managed); cleanup_cb = partial(cleanup); stack.callback(cleanup_cb)`
- `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; stack.callback(partial(cleanup_fn))`
- `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(managed=handle): close(managed); register(partial(cleanup))`
- `register = stack.callback; def cleanup(managed=handle): close(managed); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `register = stack.callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(managed=handle): close(managed); stack.push_async_callback(partial(cleanup))`
- `def cleanup(managed=handle): close(managed); cleanup_cb = partial(cleanup); stack.push_async_callback(cleanup_cb)`
- `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; stack.push_async_callback(partial(cleanup_fn))`
- `def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); register(partial(cleanup))`
- `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; register(partial(cleanup_fn))`
- `register = stack.push_async_callback; def cleanup(managed=handle): close(managed); cleanup_fn = cleanup; cleanup_cb = partial(cleanup_fn); register(cleanup_cb)`
- `def cleanup(managed=handle): managed.close(); stack.callback(partial(cleanup))`
- `def cleanup(managed=handle): managed.close(); cleanup_cb = partial(cleanup); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(managed=handle): managed.close(); register(partial(cleanup))`
- `register = stack.callback; def cleanup(managed=handle): managed.close(); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `def cleanup(managed=handle): managed.close(); stack.push_async_callback(partial(cleanup))`
- `def cleanup(managed=handle): managed.close(); cleanup_cb = partial(cleanup); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(managed=handle): managed.close(); register(partial(cleanup))`
- `register = stack.push_async_callback; def cleanup(managed=handle): managed.close(); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `def cleanup(raw_fd=fd): os.close(raw_fd); stack.callback(partial(cleanup))`
- `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_cb = partial(cleanup); stack.callback(cleanup_cb)`
- `register = stack.callback; def cleanup(raw_fd=fd): os.close(raw_fd); register(partial(cleanup))`
- `register = stack.callback; def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_cb = partial(cleanup); register(cleanup_cb)`
- `def cleanup(raw_fd=fd): os.close(raw_fd); stack.push_async_callback(partial(cleanup))`
- `def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_cb = partial(cleanup); stack.push_async_callback(cleanup_cb)`
- `register = stack.push_async_callback; def cleanup(raw_fd=fd): os.close(raw_fd); register(partial(cleanup))`
- `register = stack.push_async_callback; def cleanup(raw_fd=fd): os.close(raw_fd); cleanup_cb = partial(cleanup); register(cleanup_cb)`

CI-22 also treats default-bound `os.close(...)` helper-lambda callback forms as
safe management, including:

- `stack.callback(lambda raw_fd=fd: os.close(raw_fd))`
- `register = stack.callback; register(lambda raw_fd=fd: os.close(raw_fd))`
- `cleanup = lambda raw_fd=fd: os.close(raw_fd); stack.callback(cleanup)`
- `register = stack.callback; cleanup = lambda raw_fd=fd: os.close(raw_fd); register(cleanup)`
- `stack.push_async_callback(lambda raw_fd=fd: os.close(raw_fd))`
- `register = stack.push_async_callback; register(lambda raw_fd=fd: os.close(raw_fd))`
- `cleanup = lambda raw_fd=fd: os.close(raw_fd); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; cleanup = lambda raw_fd=fd: os.close(raw_fd); register(cleanup)`

CI-22 also treats zero-arg `os.close(...)` helper-lambda callback forms as
safe management, including:

- `stack.callback(lambda: os.close(fd))`
- `register = stack.callback; register(lambda: os.close(fd))`
- `cleanup = lambda: os.close(fd); stack.callback(cleanup)`
- `register = stack.callback; cleanup = lambda: os.close(fd); register(cleanup)`
- `stack.push_async_callback(lambda: os.close(fd))`
- `register = stack.push_async_callback; register(lambda: os.close(fd))`
- `cleanup = lambda: os.close(fd); stack.push_async_callback(cleanup)`
- `register = stack.push_async_callback; cleanup = lambda: os.close(fd); register(cleanup)`
