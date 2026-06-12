# ACI Release Tag Discipline Goal

Status: Complete

## Goal

Define the bounded release-tag discipline that `ACI` must satisfy before any release tag creation is allowed.

## Complete When

- one bounded release-tag discipline contract exists
- release-prep reading order explains where tag preparation starts and stops
- tag prerequisites, evidence, and hold lines are explicit
- reader guidance explains what remains outside this shelf

## Out of Scope

- actual remote tag creation
- repository-host automation
- public release announcement
- downstream rollout

## Failure Conditions

- release tagging is implied without an explicit gate
- versioning, changelog, and tag readiness are blurred together
- tag readiness still depends on oral explanation
