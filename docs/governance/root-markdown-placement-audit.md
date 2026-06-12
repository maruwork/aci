# ACI Root Markdown Placement Audit

Status: Executed (2026-06-09)

## 1. Purpose

Safely classify root-level Markdown documents according to `common/` and local governance rules; fix the basis for future organization decisions.

Actions completed under owner direction on 2026-06-09:
- Owner Review group (31 files) → `docs/release/`
- OWNER_DECISION_PACKET.md → `docs/governance/`
- Support Candidate group (3 files) → `docs/`
- Root Keep (14 files) + CHANGELOG.md = 15 files remain at root

## 2. Success Subject

- Can distinguish `root keep`, `support candidate`, and `owner review` among root-level Markdown files
- Does not accidentally move runtime-sensitive shelves or root public contracts
- Locks in classification decisions without modifying existing files

## 3. Scope

In scope:

- `*.md` directly under repo root
- `docs/governance/project-template-adoption-packet.md`
- `docs/governance/project-file-taxonomy.md`
- `docs/governance/project-boundary-register.md`

Out of scope:

- anything under `archive/`
- `.pytest_cache/`, `build/`, `aci.egg-info/`
- rename / move of `shared/`, `shared/runtime/`, `domains/`
- immediate move of root public contracts

## 4. Working Rules

- prefer Git Bash for reads to avoid encoding issues
- make edits with minimum diff
- reclassification or movement of root public docs is an owner-only decision
- this audit result means "basis for what to raise to owner review next", not "safe to move now"

## 5. Classification Legend

| class | meaning |
|---|---|
| `root keep` | naturally belongs at root under current rules — public surface or thin entry |
| `support candidate` | does not need to be at root; worth considering for a future support shelf |
| `owner review` | movement decision could affect public contracts, release flow, or external callers; owner judgment required first |

## 6. Current Inventory

50 Markdown files directly under root.

### 6.1 Root Keep

| file | reason |
|---|---|
| `README.md` | human entry and front current surface |
| `AGENTS.md` | delegated AI entry |
| `CLAUDE.md` | thin route for delegated AI entry |
| `SUPPORT.md` | repository community file |
| `CODE_OF_CONDUCT.md` | repository community file |
| `CONTRIBUTING.md` | repository community file |
| `SECURITY.md` | repository community file |
| `CHANGELOG.md` | public release surface (GitHub convention) |

### 6.1.1 Moved to `docs/` (2026-06-10)

Moved from root to `docs/` per owner instruction. All references updated.

| file | new path |
|---|---|
| `USER_EVALUATION_INDEX.md` | `docs/USER_EVALUATION_INDEX.md` |
| `ACI_DOWNSTREAM_ADOPTION_PACKET.md` | `docs/ACI_DOWNSTREAM_ADOPTION_PACKET.md` |
| `ACI_SHELF_CLASSIFICATION.md` | `docs/ACI_SHELF_CLASSIFICATION.md` |
| `DOMAIN_PACK_EXTENSION_GUIDE.md` | `docs/DOMAIN_PACK_EXTENSION_GUIDE.md` |
| `NON_GOALS.md` | `docs/NON_GOALS.md` |
| `PUBLIC_RUNTIME_ASSUMPTIONS.md` | `docs/PUBLIC_RUNTIME_ASSUMPTIONS.md` |
| `VERSIONING_POLICY.md` | `docs/VERSIONING_POLICY.md` |

### 6.2 Owner Review

| file | reason |
|---|---|
| `CHANGELOG.md` | public release surface; whether to keep at root requires owner judgment |
| `CHANGELOG_DISCIPLINE.md` | tied to release discipline |
| `MAINTAINER_HISTORY_INDEX.md` | public support surface at root; candidate for support shelf |
| `OWNER_DECISION_PACKET.md` | owner-facing; reason for keeping at root needs confirmation |
| `PACKAGE_LAYOUT_TARGET.md` | close to packaging public contract |
| `PACKAGING_BLOCKERS.md` | affects release / packaging readiness |
| `PACKAGING_READINESS_CONTRACT.md` | packaging contract |
| `POST_RELEASE_MAINTENANCE_CADENCE.md` | release lifecycle contract |
| `POST_RELEASE_REVIEW_PACKET.md` | release governance artifact |
| `PRE_PUBLICATION_DECISIONS.md` | connected to publication go/no-go judgment |
| `PRIVATE_HOST_BOOTSTRAP_RUNBOOK.md` | possibly an external operator surface |
| `PRIVATE_RELEASE_HOLD_LINE.md` | tied to release gate |
| `PUBLIC_RELEASE_CHECKLIST.md` | publication surface |
| `PUBLISHABLE_HOLD_CHECKLIST.md` | release gate surface |
| `REGISTRY_ARTIFACT_CHECKLIST.md` | publication / packaging surface |
| `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md` | registry publication contract |
| `REGISTRY_UPLOAD_DRY_RUN_PROOF.md` | release evidence surface |
| `REGISTRY_UPLOAD_RUNBOOK.md` | operator-facing publication runbook |
| `RELEASE_CANDIDATE_PACKET.md` | release decision surface |
| `RELEASE_DISCIPLINE_CONTRACT.md` | release contract |
| `RELEASE_DISCIPLINE_PACKET.md` | release governance packet |
| `RELEASE_EVIDENCE_SNAPSHOT.md` | release evidence surface |
| `RELEASE_EXECUTION_HANDOFF_PACKET.md` | release handoff surface |
| `RELEASE_NOTES_DISCIPLINE_CONTRACT.md` | release notes contract |
| `RELEASE_PREP_INDEX.md` | explicitly listed as publication consequence in the adoption packet |
| `RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md` | rollback contract |
| `RELEASE_TAG_DISCIPLINE_CONTRACT.md` | release tag contract |
| `REPO_EXPORT_CHECKLIST.md` | repo export / publication support; relationship to root entry route needs verification |
| `REPO_EXPORT_GUIDE.md` | public surface for standalone export |
| `STANDALONE_CANDIDATE_NOTE.md` | related to standalone positioning |
| `SUPPORT_LIFECYCLE_CONTRACT.md` | support lifecycle contract |

### 6.3 Support Candidate

Completed (2026-06-09):
- `CONTRIBUTING_DRAFT.md`, `SECURITY_DRAFT.md` → moved directly under `archive/`
- `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`, `RELEASE_BOOTSTRAP_NOTES.md` → moved to `docs/release/`
- `PRE_PUBLIC_READINESS_SNAPSHOT_20260606.md` → moved to `archive/docs-release/` (date-suffixed historical snapshot)

## 7. Immediate Safe Actions

Safe to proceed without owner approval up to the following:

1. Update this audit document to improve classification accuracy
2. Identify shelf candidates for the `support candidate` group
3. Write root-keep reasons or movement impact for the `owner review` group
4. Add a "root audit in progress" note to the taxonomy / boundary register

## 8. Stop Conditions

Stop and raise to owner review before proceeding when:

1. Actually moving or renaming root public contracts
2. Formally reclassifying a root file to `support`
3. Changing the entry point for release / publication / packaging flow
4. A change could affect paths referenced by external users

## 9. Next Checkpoint

Next checkpoint: separate the `owner review` group into truly root-required files and files that can be moved to a support shelf, with written rationale for each.
