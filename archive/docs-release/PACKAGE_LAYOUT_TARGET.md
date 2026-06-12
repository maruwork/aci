# ACI Package Layout Target

Status: Active

## Purpose

Describe the bounded target state that packaging work should eventually satisfy.

## Target Expectations

- one explicit package metadata file
- one explicit CLI entrypoint
- package-safe imports for core Python helpers
- package-safe access to selected bundled assets
- domain-pack discovery that does not depend on unstated repo-local filesystem assumptions

## Must Stay Reachable As Packaged Assets

- sample report examples
- fixture contract assets
- selected release-prep and evaluation docs that the product surface points to directly

## Entry Point Target

The packaged CLI now exposes an `aci` entrypoint in `pyproject.toml` that maps to the current common CLI surface.

The reviewed repo-local supported entrypoint remains:

```bash
python python/aci_cli.py <command>
```

The reviewed packaged entrypoint target is:

```bash
aci <command>
```

## Not This Wave

- migrating the tree into a final package layout
- adding package registry publishing metadata
- proving cross-platform installer behavior
