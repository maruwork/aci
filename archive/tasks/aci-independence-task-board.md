# ACI Independence Task Board

Status: Complete

## CP1 Tasks — Complete

- classify each current `epo root` file by responsibility
- extract Pier-only vocabulary and patterns
- identify mixed authority files

## CP2 Tasks — Complete

- define top-level shelf structure
- decide what stays in core
- decide what moves to domain packs
- decide what becomes runtime/report/persistence/integration surfaces

## CP3 Tasks — Complete

- define allowed dependency direction
- define normalized finding contract
- define runtime boundary
- define report boundary
- define persistence boundary
- define healthcheck integration boundary

## CP4 Tasks — Complete

- define `domains/pier`
- define minimum domain pack interface
- define project-local override role
- define future domain promotion rule

## CP5 Tasks — Complete

- create ACI five-layer roadmap documents
- create ACI independence basic design
- wire `README.md` to the new reading order

## CP6 Tasks — Complete

詳細タスクボード: `tasks/aci-pier-decoupling-task-board.md`

完了した作業（aci-pier-decoupling 波）:
- split mixed authority from `aci_signals.py` ← Step 6 完了
- place domain vocabulary under `domains/pier` ← コアから除去完了
- update imports, placeholders, and README guidance ← Steps 8, 9 完了
- run minimum verification ← Step 10 完了

後続波（2026-06-09）での確認作業:
- runtime/report/persistence/integrations 各 shelf の境界定義・契約文書の存在を確認
  - `runtime/`: README (Owns/Must Not Own) + 複数 contract.md ✓
  - `report/`: README (Owns/Must Not Own) + 複数 contract.md ✓
  - `persistence/`: README + PERSISTENCE_BRIDGE_INDEX.md ✓
  - `integrations/healthcheck/`: README (Owns/Must Not Own) + healthcheck_contract.md ✓
- `runtime/aci-ci-and-automation-contract.md` の pier 必須表記をオプション表記に修正

CP6 close: 2026-06-09。ACI independence workstream 完了。
