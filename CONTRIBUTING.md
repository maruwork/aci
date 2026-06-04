# Contributing to ACI

Status: Active

This file is a pre-publication draft. It exists so the repository can be published later without inventing the contribution surface from memory.

## Current Intent

- keep `ACI core` domain-independent
- keep project-local runtime rules out of core
- add a domain pack only when the vocabulary is reusable beyond one runtime copy
- prefer bounded, reviewable additions over broad structural rewrites

## Expected Contribution Areas

- inspection catalog and contracts
- domain-pack loader support
- report contract improvements
- public examples and smoke verification
- documentation clarity

## Must Not Be Treated As Core Contributions

- project-local trigger wiring
- project-local DB writeback rules
- project-local operator workflows
- downstream current-state records

## Before Opening Public Contributions

Chosen defaults for the first repository bootstrap are:

- license: `MIT`
- repository: `fumimaruwork/aci`
- issue policy: issues open from day one
- pull request policy: PRs accepted from day one with maintainer review
- minimum public CI expectations: required at repository creation
