# ACI Built Wheel Install Proof Contract

Status: Active

## Purpose

Define the bounded proof route for local wheel build and wheel install of `ACI` from the current shelf.

## What This Contract Proves

- a local wheel can be built from the current shelf without registry publishing
- a bounded temporary environment can install that built wheel
- the installed `aci` command can execute the reviewed `installed-package-check`
- the proof route does not depend on permanent host-environment changes

## What This Contract Does Not Prove

- registry publishing
- wheel signing
- cross-platform installer parity
- downstream project rollout

## Required Proof Shape

1. create a temporary environment in a bounded writable location
2. build a local wheel from the current shelf into a bounded writable location
3. install that built wheel into the temporary environment
4. run `aci installed-package-check`
5. run `aci smoke`
6. record the result
7. discard or leave the temporary environment as non-authority proof output

## Required Boundaries

- no permanent host Python environment mutation
- no external package registry dependency beyond standard local tooling already present
- no claim that built wheel proof equals registry or release completion

## Reviewed Command Targets

- repo-local proof route:
  - `python shared/python/aci_cli.py installed-package-check`
- wheel-installed target:
  - `aci installed-package-check`
  - `aci smoke`
