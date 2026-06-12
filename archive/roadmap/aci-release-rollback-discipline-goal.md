# ACI Release Rollback Discipline Goal

Status: Complete

## Goal

Define one bounded rollback discipline that lets a maintainer respond to a bad `ACI` release without relying on oral explanation.

## Complete When

- one rollback discipline contract exists
- release-prep reading order points to that contract
- the contract defines minimum rollback fields and rules
- the rollback surface is positioned as post-release governance, not pre-release execution

## Out of Scope

- remote registry deletion
- hosted release-page editing
- downstream repository fixes

## Failure Conditions

- rollback handling still depends on chat memory
- the contract disagrees with release notes or versioning discipline
- the rollback surface does not define the minimum facts and next action
