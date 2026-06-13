# Contributing

Thank you for considering a contribution to ACI.

## Before You Start

- read `README.md`
- read `docs/NON_GOALS.md` and `docs/DOMAIN_PACK_EXTENSION_GUIDE.md`
- read `SECURITY.md` if the change may involve credentials, local files, vulnerability behavior, or report evidence
- check whether the issue already exists

## Preferred Contribution Flow

1. open or confirm an issue when the change is non-trivial
2. keep generic core, optional domain-pack, and downstream-local boundaries explicit
3. keep the change small enough to review
4. update repo-relative docs when behavior, commands, or boundaries change
5. run the documented verification commands before opening a pull request

## Pull Request Expectations

- explain what changed
- explain why it changed
- list the checks you ran
- mention any remaining limitations or follow-up work
- call out any boundary decisions that affect generic core versus optional domain packs

## Verification

Run the same gates CI runs, from the repository root, before opening a PR:

```bash
pip install -e .
pip install pytest ruff mypy

pytest shared/tests/          # test suite (gating)
ruff check shared/python/     # lint (gating)
mypy shared/python/           # type check (gating; config in pyproject.toml)
aci automation-smoke          # bounded smoke surface
```

Optional deeper checks:

```bash
aci installed-package-check   # packaging/install proof
python shared/tools/aci_corpus_harness.py <real-project-dir>   # per-CI-ID precision triage
```

A quick pre-push hook that runs the four gates keeps lint and types green between
CI runs; wire it into your local `.git/hooks/pre-push` or a pre-commit tool.

## Review Notes

Maintainers may ask contributors to narrow scope, add evidence, or split follow-up work before merge.
