# ACI Packaging Blockers

Status: Active

## Purpose

State what packaging blockers were resolved by the layout migration and what remains outside this bounded wave.

## Resolved By Package Layout Migration

1. Package metadata now exists.
   - `pyproject.toml` defines package name, version, and CLI entrypoint

2. A package-safe import route now exists.
   - `python/__init__.py` defines the installable package root
   - domain packs live in `domains/<domain>/python/` and are discovered by `aci_domain_loader.py` without bundling domain-specific code into the `aci` package

3. Domain loading no longer depends on one unstated filesystem route.
   - `python/aci_domain_loader.py` prefers package import
   - repo-local file loading remains the reviewed compatibility fallback

4. Reviewed bundled assets now have package-data rules.
   - `python/package_assets/fixtures/`
   - `python/package_assets/report/examples/`
   are declared in `pyproject.toml`

## Remaining Limits

1. Current reviewed verification proves the local package routes that this shelf owns, but not every distribution shape.
   - repo-local execution, installed-package checks, editable install, built wheel install, and source-distribution install are now proved
   - signed artifacts and registry delivery remain outside this shelf

2. The physical tree is not yet the final long-term package layout.
   - `python/` remains the current reviewed home of the package root
   - release packaging and final tree simplification remain later work

3. Registry publishing is still out of scope.
   - packaging metadata exists
   - publishing workflow and installer discipline remain separate work

## Safe Conclusion

`ACI` now has a bounded package-safe layout, one reviewed CLI entrypoint, and executed editable-install, built-wheel, and source-distribution proof, but it is not yet claiming full distribution-grade release proof.
