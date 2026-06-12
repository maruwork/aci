# ACI Compatibility Surface Goal

Status: Complete

## Goal

`ACI` の compatibility surface を、canonical shelf と legacy shelf を誤読しにくい状態へ持っていく。

## Completion State

- `templates/` が legacy compatibility shelf であることが入口で分かる
- canonical 読順が `runtime/` `report/` `persistence/` 側へ寄る
- legacy templates を新規正本と誤読しにくい
