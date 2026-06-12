# ACI Package Layout Migration Goal

Status: Complete

## Goal

Migrate `ACI` toward a package-safe layout without breaking the reviewed common-shelf product surface.

## Complete When

- `ACI` has an explicit package metadata file
- the common Python surface can be addressed through a package-safe import route
- bundled assets needed by the reviewed product surface have a package-safe loading rule
- the reviewed CLI surface remains understandable after the layout migration

## Out of Scope

- publishing to a package registry
- final public release
- provider-specific install scripts
- downstream project migration work

## Failure Conditions

- layout migration breaks the current reviewed CLI surface
- package-safe imports are incomplete or inconsistent
- bundled asset handling still depends on unstated repo-local assumptions
