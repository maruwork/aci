# ACI Public Surface Polish Goal

Status: Complete

## Goal

`ACI` の公開向け入口、sample、smoke、説明文から内部整理の温度を外し、初見の第三者が「利用者向けの完成ツール」として読める状態へ持っていく。

## Completion State

- `README.md` が利用者向け入口として薄く明快である
- internal wave / legacy / temporary の温度が public-facing surface から過度に見えない
- sample report が内部整理文脈ではなく中立な利用例になっている
- smoke check の出力と説明が一致している
- 開発者向け履歴面と利用者向け面の読順が分かれている

## Out Of Scope

- domain rule の新規実装
- report contract 自体の schema 拡張
- GitHub 公開操作

## Failure Conditions

- public-facing 文書に internal migration の温度が残る
- sample が内部事情の説明に寄る
- smoke 説明と実際の挙動がずれる
