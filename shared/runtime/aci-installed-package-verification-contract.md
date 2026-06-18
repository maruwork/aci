# ACI Installed Package Verification Contract

Status: Active

## Purpose

Define the bounded proof surface for installed-package verification after package layout migration.

## What This Contract Proves

- the package metadata names one reviewed CLI entrypoint
- the current package root can be imported through a package-style route
- reviewed package assets are reachable through the package asset helper
- reviewed helper modules remain importable through the packaged route
- reviewed domain-pack loading works through the package-safe import route
- version consistency can be proved either from repo-local release metadata or
  from installed package metadata when the source checkout is absent

## What This Contract Does Not Prove

- registry publishing
- wheel upload
- end-to-end installer behavior on every environment
- downstream project rollout

## Proof Lanes

### Editable-Install Proof

This lane proves:

- package-style import of `aci`
- package-style import of reviewed helper modules such as `aci_github_summary`
- package-style access to reviewed assets, including sample reports, fixtures,
  and the bundled Semgrep baseline rules

This lane does not claim:

- that an editable install command was run
- that external packaging tools behaved correctly

### Built-Artifact Contract Proof

This lane proves:

- `pyproject.toml` declares the reviewed CLI entrypoint
- reviewed package-data rules exist for sample reports, fixture assets, and
  bundled analyzer assets
- package metadata remains aligned with the reviewed common shelf

This lane does not claim:

- that a wheel was built and installed
- that registry publishing is complete

## Reviewed Commands

- repo-local:
  - `python shared/python/aci_cli.py installed-package-check`
- packaged target:
  - `aci installed-package-check`

## Reading Rule

Read this contract together with:

1. `pyproject.toml`
