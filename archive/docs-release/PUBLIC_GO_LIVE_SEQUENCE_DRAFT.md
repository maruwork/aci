# ACI Public Go-Live Sequence (Draft)

Status: Draft

## Purpose

Show the order of actions for the eventual public release, without performing them now.

## Sequence

1. confirm owner decisions in `docs/governance/OWNER_DECISION_PACKET.md`
2. confirm registry publish gates in `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
3. confirm release tag gates in `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
4. follow `REGISTRY_UPLOAD_RUNBOOK.md`
5. create the standalone repository in the chosen host location
6. copy the shelf using `REPO_EXPORT_GUIDE.md`
7. add the chosen license file
8. confirm `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` still match the chosen public posture
9. wire the public CI scope chosen by the owner
10. run smoke and sample validation in the standalone repository
11. publish

## Not This Wave

- repository creation
- remote configuration
- visibility change
- live issue or security intake
