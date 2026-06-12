# ACI Release Bootstrap Notes

Status: Draft

## Purpose

Give the owner a bounded checklist for the moment just before a standalone public repository is created.

## Bootstrap Notes

1. Copy the standalone shelf using the root shape in `REPO_EXPORT_GUIDE.md`.
2. Add the chosen `MIT` license file.
3. Carry `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` as the active repository community files.
4. Decide whether `Pier` remains the only public example domain pack or whether `domains/custom-template/` should be highlighted instead.
5. Define the public CI surface for smoke check and sample validation.

## Chosen Defaults For First Bootstrap

- repository target: `fumimaruwork/aci`
- initial visibility: `private`
- public contribution posture: issues open from day one, PRs accepted with maintainer review
- public security posture: GitHub private vulnerability reporting if enabled, best effort response
- CI posture: required at repository creation

## Must Not Be Skipped

- verify repo-relative commands still work after extraction
- verify sample JSON files still parse
- verify public docs do not require `common/refernce/` to be understood
