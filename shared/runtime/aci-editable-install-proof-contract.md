# ACI Editable Install Proof Contract

Status: Active

## Purpose

Define the bounded proof route for editable install of `ACI` from the local shelf.

## What This Contract Proves

- a temporary environment can install `ACI` from the local shelf with editable install
- the installed `aci` command can execute the reviewed `installed-package-check`
- the proof route does not depend on permanent host-environment changes

## What This Contract Does Not Prove

- registry publishing
- built wheel installation
- cross-platform installer parity
- downstream project rollout

## Required Proof Shape

1. create a temporary environment in a bounded writable location
2. install `ACI` from the current shelf through editable install
3. run `aci installed-package-check`
4. record the result
5. discard or leave the temporary environment as non-authority proof output

## Required Boundaries

- no permanent host Python environment mutation
- no external package registry dependency beyond standard local tooling already present
- no claim that editable install equals full distribution proof

## Reviewed Command Target

- local proof route:
  - `aci installed-package-check`
