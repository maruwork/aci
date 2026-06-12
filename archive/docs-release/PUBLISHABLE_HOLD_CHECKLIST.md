# ACI Publishable Hold Checklist

Status: Active

## Purpose

Check whether the shelf is in a state where publication is blocked only by owner decisions and repo-hosting actions.

## Checklist

- `README.md` provides public-facing entry guidance
- smoke command is repo-relative
- public sample reports are repo-relative
- standalone repo extraction guidance exists
- pre-publication draft assets exist
- owner decisions are gathered in `docs/governance/OWNER_DECISION_PACKET.md`
- registry publishing discipline is explicit in `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
- no remaining common-shelf restructuring is required for first publication
- remaining work is limited to license, host, contribution/security policy, and public CI decisions

## Fail-Close Rule

If any unchecked item still requires shelf restructuring, do not call the shelf "publishable hold".
