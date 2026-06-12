# ACI CI-27 Patchwork Structure Design

Status: Active

## Purpose

Define the generic ACI meaning of `CI-27 Patchwork Structure`.

## Why CI-03 Is Not Enough

`CI-03 Patchwork Code` already covers local residue such as:

- TODO / FIXME / HACK markers
- stitched local exceptions
- partial code migrations

It does not cover higher-level structure cases where the system keeps accumulating temporary bridge layers without ever closing the shelf or authority move.

## CI-27 Scope

`CI-27` is for structure-level stitching such as:

- concept shelves that exist only as temporary mirrors
- bridge-on-bridge documents that hide the real authority
- partial authority moves where both old and new surfaces keep acting live
- compatibility seams that were supposed to be temporary but now shape the architecture

## Expected Evidence

- duplicated mapping shelves
- conflicting authority language across shelves
- repeated "temporary" or "bridge" routing that never closes
- structure signals showing mixed authority or mixed shelf ownership

## Lane Rule

- primary lane: `human judgment`
- supporting lane: native structure evidence

## Tool Mapping

- `CI-27` is represented by the structure signal `PATCHWORK_GRAFT`
- report rows must carry both `ci_id=CI-27` and `signal=PATCHWORK_GRAFT` when this item is emitted
- normalized structure emission goes through `python/aci_findings.py`
