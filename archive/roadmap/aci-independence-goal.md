# ACI Independence Goal

Status: Complete

## Goal

Make `epo root` stand as an independent ACI tool authority built from:

- `ACI core`
- selectable domain packs such as `Pier`
- project-local runtime binding
- separated report, persistence, and integration surfaces

## Completion State

ACI independence is complete when all are true:

- `ACI core` has no Pier-only investigation vocabulary
- `Pier` is selectable as a domain pack instead of being embedded in core
- future domains such as `adop` can be added with the same pack shape
- runtime, report, persistence, and healthcheck integration have explicit owner boundaries
- ACI has its own goal, path, checkpoints, tasks, and design documents inside `epo root`

## Current Judgment

- CP1–CP6 全完了（2026-06-09）
- CP6（コード結合除去 + docs 配置確認）完了
  - ACI core に Pier 固有 hardcoding なし（Steps 1–18 で除去）
  - domain-pack 動的 discovery 実装済み
  - runtime/report/persistence/integrations 各 shelf に明示的な境界定義と契約文書あり
  - ACI 独自の workstream 文書群（goal/path/checkpoints/tasks/design）が epo root 内に確立
- ACI independence workstream 完了（2026-06-09）

## Scope In

- `epo root` shelf structure
- `ACI core`
- `Pier option`
- runtime/report/persistence/healthcheck integration boundary definition
- ACI-side documentation needed to close the workstream

## Scope Out

- Pier completion workstream
- final Pier integration ownership
- adop domain implementation
- project-local runtime rollout in downstream repos

## Not Complete If

- Pier vocabulary remains in core
- domain-pack loading model is unclear
- runtime/report/persistence/healthcheck boundaries are still mixed
- ACI's own workstream documents are missing

## Reporting Subject

The completion subject is `ACI independence`, not `Pier completion`.
