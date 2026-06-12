# ACI Installed Package Verification Goal

Status: Complete

## Goal

Verify `ACI` through an installed-package route, not only through repo-local script execution.

## Complete When

- a bounded installed-package verification route is explicit
- editable-install and built-artifact verification expectations are separated
- reviewed CLI commands are mapped to installed-package verification steps
- reader guidance explains what is and is not proven by this verification wave

## Out of Scope

- public package publishing
- package registry automation
- downstream project rollout

## Failure Conditions

- installed-package verification is claimed without an explicit proof path
- repo-local checks and installed-package checks are blurred together
- verification depends on oral explanation
