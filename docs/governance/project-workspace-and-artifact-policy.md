# ACI Project Workspace And Artifact Policy

Status: Active

## 1. Purpose

Fix the handling of ACI scratch files, generated residue, and archives.

## 2. Active Workspace

- active workspace root:
  - `workspace/`
- allowed contents:
  - scratch notes
  - one-off review outputs
  - temporary verification artifacts
- prohibited uses:
  - placing canonical contracts or runtime files without explicit promotion

## 3. Generated Output Shelf

- machine-readable output:
  - `workspace/`
- human-readable report output:
  - `workspace/`
- retention:
  - keep only while the artifact is still referenced by active review work
- promotion rule:
  - generated artifact is not canonical until explicitly reviewed and promoted

## 4. Archive Shelf

- archive root:
  - `archive/`
- what belongs here:
  - retired mappings
  - obsolete exports
  - historical one-off artifacts
- archive note rule:
  - retain why the file left active topology

## 5. Legacy Compatibility Shelf

- legacy shelf:
  - `none`
- why it still exists:
  - `not applicable`
- rule:
  - `not applicable`

## 5a. Hidden Active Asset Rule

- hidden / ignored active shelf:
  - `none`
- rule:
  - hidden active asset must not stay unannounced

## 5b. Runtime / Agent Residue Rule

- residue shelf:
  - `.pytest_cache/`
  - `build/`
  - `aci.egg-info/`
- class:
  - `generated`
- cleanup trigger:
  - when packaging or verification work no longer needs the residue
- owner:
  - repository owner or the maintainer explicitly handling residue cleanup

## 6. Promotion Rule

1. decide the artifact role
2. choose the canonical shelf using taxonomy
3. confirm caller / reader impact
4. update governance docs if the artifact is promoted

## 7. Cleanup Rule

- residue cleanup must not silently remove canonical evidence
- cleanup must not write from generated shelves back into canonical shelves without review

## 8. Completion Rule

- active workspace is explicit
- generated residue shelves are explicit
- archive shelf is explicit
- hidden active assets are not assumed
