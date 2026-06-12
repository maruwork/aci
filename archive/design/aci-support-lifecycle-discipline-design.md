# ACI Support Lifecycle Discipline Design

Status: Complete

## SLD-T1 Contract Fixed

### Start Conditions

- release and post-release discipline waves are already complete
- `SUPPORT.md` exists but does not yet define explicit support windows

### Read

- `SUPPORT.md`
- `VERSIONING_POLICY.md`
- `docs/release/RELEASE_PREP_INDEX.md`

### Write

- `docs/release/SUPPORT_LIFECYCLE_CONTRACT.md`

### Do

- define supported scope
- define unsupported scope
- define support windows
- define required intake fields
- define a fail-close rule

### Accept

- a reader can tell what generic `ACI` support covers without reading chat history

## SLD-T2 Entry Docs Aligned

### Read

- `docs/release/SUPPORT_LIFECYCLE_CONTRACT.md`
- `SUPPORT.md`

### Write

- `SUPPORT.md`

### Do

- route users from `SUPPORT.md` into the lifecycle contract
- align intake wording to the fixed contract

### Accept

- `SUPPORT.md` no longer acts as an incomplete standalone support rule

## SLD-T3 Release And Version Routes Aligned

### Read

- `docs/release/SUPPORT_LIFECYCLE_CONTRACT.md`
- `VERSIONING_POLICY.md`
- `docs/release/RELEASE_PREP_INDEX.md`
- `README.md`

### Write

- `VERSIONING_POLICY.md`
- `docs/release/RELEASE_PREP_INDEX.md`
- `README.md`

### Do

- ensure support lifecycle wording does not conflict with version bump wording
- add one clear reading route from release-prep and root entry docs

### Accept

- support and versioning surfaces read as one coherent policy set

## SLD-T4 Maintainer Surface Aligned

### Read

- `docs/release/MAINTAINER_HISTORY_INDEX.md`
- `python/aci_working_mirror_sync.py`

### Write

- `docs/release/MAINTAINER_HISTORY_INDEX.md`
- `python/aci_working_mirror_sync.py`

### Do

- add the wave to maintainer history
- add the 5 official/mirror pairs

### Accept

- maintainers can trace the wave from the index
- mirror sync reports the wave as covered

## SLD-T5 Verification And Summary

### Read

- all edited files

### Write

- `common/refernce/aci-support-lifecycle-discipline-summary.md`

### Do

- run smoke
- run compile
- remove `__pycache__`
- record the closed scope and result

### Accept

- reviewed surface has no new inconsistency
