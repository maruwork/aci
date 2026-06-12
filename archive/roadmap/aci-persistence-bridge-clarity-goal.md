# ACI Persistence Bridge Clarity Goal

Status: Complete

## Goal

`ACI` の `persistence/` 棚で、generic authority と domain-specific bridge をさらに誤読しにくくする。

## Completion State

- `persistence/` の入口で generic authority と domain bridge の差が明確
- `Pier` persistence bridge の読順が分かる
- future domain bridge が増えても同じ型で読める

## Out Of Scope

- persistence schema の変更
- downstream project の validation register 更新
- file rename / move
