# ACI Pre-Public Readiness Snapshot 2026-06-06

Status: Active

## Purpose

Capture the current `ACI` state as of `2026-06-06` while the repository remains private and is being held just before public release.

## Confirmed Ready

- hosted repository exists at `https://github.com/fumimaruwork/aci`
- repository visibility remains `private`
- `README.md` explains what `ACI` is and is not
- smoke command remains repo-relative
- sample reports remain repo-relative
- `LICENSE`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, issue template, and pull request template exist
- Community Profile is `100%`
- `vulnerability alerts` are enabled
- `Dependabot security updates` are enabled
- `dependabot.yml` exists for `pip` and `github-actions`
- hosted Actions permissions are enabled
- `python python/aci_public_smoke.py` passes in the private repository candidate
- report example JSON files parse successfully
- `__pycache__` directories were removed from the private repository candidate after verification

## Remaining Non-Public Hold Items

- keep repository visibility `private`
- do not run the public release step sequence yet
- hosted `code scanning` default setup is not enabled in the current private-repository state
- hosted `secret scanning` and `secret scanning` push protection are not enabled in the current private-repository state
- `private vulnerability reporting` is not available while the repository remains private

## Current Interpretation

`ACI` is now in a publishable-hold state where remaining work is limited to host-side public-release actions and feature toggles whose availability depends on the repository becoming public or gaining different hosted security eligibility.

## Next Release-Moment Checks

1. Reconfirm owner posture in `docs/governance/OWNER_DECISION_PACKET.md`.
2. Re-run smoke, JSON parse, and no-`__pycache__` checks in the standalone repository.
3. Change visibility only when the owner explicitly chooses to publish.
4. Immediately after public release, re-check `private vulnerability reporting`, `secret scanning`, push protection, and `code scanning`.
