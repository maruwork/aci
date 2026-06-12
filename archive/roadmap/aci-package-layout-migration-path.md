# ACI Package Layout Migration Path

Status: Complete

## Path

1. inventory the minimum layout changes required for package-safe imports
2. define the bounded migration model
3. add package metadata and package-safe loading rules
4. update reader routes and packaging docs
5. verify the reviewed migrated surface

## Stop When

- migration requires a destructive tree rewrite outside the bounded common shelf
- one migration step would break reviewed CLI/report/sample routes without a bounded replacement
- package-safe loading still depends on implicit repo-local behavior
