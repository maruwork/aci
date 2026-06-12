# ACI Pre-Publication Decisions

Status: Complete

## Purpose

Record the decisions that must be made before `ACI` is published, without pretending they are already resolved.

## Resolved Decisions

### 1. License

Status: chosen

- chosen license: `MIT`

### 2. Repository Host And Owner

Status: chosen

- GitHub owner/org: `fumimaruwork`
- repository name: `aci`
- initial visibility: `private`

### 3. Public Issue And PR Policy

Status: chosen

- issue policy: issues open from day one
- pull request policy: PRs accepted from day one with maintainer review
- public community contributions from day one: `yes`

### 4. Public Security Intake

Status: chosen

- security-report intake posture: GitHub private vulnerability reporting if enabled
- private disclosure from day one: `yes`
- response posture: best effort, no fixed SLA

### 5. CI/CD Scope

Status: chosen

- minimum public verification surface: public release checklist command set
- CI at repository creation: required

## Already Settled Inside The Shelf

- public-facing commands are repo-relative
- public-facing file paths are repo-relative
- standalone root shape is documented
- `aci core only` and `aci + pier domain` can be demonstrated locally
