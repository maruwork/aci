# ACI Pre-Public Polish Design

Status: Complete

## APPP-T1

- Start Conditions: `ACI` private bootstrap is already closed.
- Read: `README.md`, `docs/release/REPO_EXPORT_GUIDE.md`
- Write: `.github/`, `SUPPORT.md`
- Do: add issue templates, pull request template, `CODEOWNERS`, and support guidance.
- Acceptance: a third party can see where to report bugs, ask questions, and open reviewable pull requests.

## APPP-T2

- Start Conditions: `APPP-T1` is complete.
- Read: `common/refernce/prepare_private_repo_candidates.sh`
- Write: `README.md`, `docs/release/REPO_EXPORT_GUIDE.md`, candidate-generation script
- Do: make export and candidate flow carry the new repository-facing files.
- Acceptance: candidate regeneration does not require ad hoc copy steps.

## APPP-T3

- Start Conditions: `APPP-T2` is complete.
- Read: candidate-generation script, private candidate directory
- Write: `common/refernce/aci-private-repo-candidate-20260605`
- Do: regenerate candidate and run smoke/compile verification.
- Acceptance: candidate contains the new files and existing verification still passes.

## APPP-T4

- Start Conditions: `APPP-T3` is complete.
- Read: candidate directory, GitHub repository state
- Write: `fumimaruwork/aci` private repository contents and metadata
- Do: commit/push the polished candidate and set description/topics while keeping the repository private.
- Acceptance: repository metadata and files match the prepared candidate.

## APPP-T5

- Start Conditions: `APPP-T4` is complete.
- Read: common shelf and summary notes
- Write: summary note in `common/refernce`
- Do: remove generated cache directories, record the latest result, and stop before public release.
- Acceptance: no generated cache directories remain in `epo root`, and the summary explains what changed.
