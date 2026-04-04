# Git / GitHub 運用ルール

このプロジェクトでは、スライド生成品質の改善を小さく分けて管理します。

## 基本方針

- `main` は常に動く状態を維持する
- 1つの改善テーマごとに 1 ブランチを切る
- 1 PR で扱う論点は 1 つに絞る
- 生成品質の改善は、コード変更と評価メモをセットで残す
- 大きな redesign は避け、差分を小さくする

## ブランチの切り方

推奨形式:

```text
feat/<topic>
fix/<topic>
chore/<topic>
docs/<topic>
experiment/<topic>
```

例:

- `feat/prompt-structure-tightening`
- `feat/japanese-bullet-shortening`
- `feat/json-repair-retry-tuning`
- `fix/preview-layout-overlap`
- `docs/quality-workflow`
- `experiment/executive-summary-tone`

## どの粒度で分けるか

良い例:

- プロンプトを短文化する
- JSON repair の再試行条件を変える
- summary スライドの安定性を上げる
- UI の編集導線を改善する

避けたい例:

- prompt 修正、provider 切替、UI 改修、README 更新を 1 PR にまとめる

## 日々の進め方

1. `main` を最新化する
2. 改善テーマごとにブランチを切る
3. まず固定入力で再現ケースを用意する
4. 実装する
5. 同じ入力で Before / After を比べる
6. 結果を PR と実験ログに残す
7. レビュー後に `main` へマージする

## 推奨コマンド

```bash
git switch main
git pull origin main
git switch -c feat/prompt-structure-tightening
```

変更後:

```bash
git add app/ tests/ samples/ README.md docs/
git commit -m "feat: tighten prompt structure for stable slide JSON"
git push -u origin feat/prompt-structure-tightening
```

## コミットメッセージ

推奨形式:

```text
<type>: <summary>
```

例:

- `feat: shorten bullet phrasing in prompt`
- `fix: prevent preview JSON panel overlap`
- `test: add generation regression fixtures`
- `docs: add quality improvement workflow`

## PR の作り方

PR は「何を直したか」だけでなく、「なぜ良くなるか」「どう確認したか」を必ず残します。

最低限書く項目:

- 目的
- 仮説
- 変更内容
- 確認方法
- Before / After
- リスク

`.github/pull_request_template.md` をそのまま使ってください。

## 品質改善で必ず残すもの

- 固定入力
- 出力 JSON の差分
- プレビュー上の見た目確認
- 壊れたケースがあればその例

生成品質は主観だけで進めると後で戻れないので、`samples/` と `docs/EXPERIMENT_LOG_TEMPLATE.md` を使って比較可能な形で残します。

## merge の判断基準

マージしてよい状態:

- JSON 契約を壊していない
- 既存プレビュー導線を壊していない
- 手動 export 導線を壊していない
- 改善内容が PR で説明できる
- 再現用の入力と確認結果が残っている

マージを止めるべき状態:

- 品質が上がったか説明できない
- 別の機能改修が混ざっている
- 失敗ケースが増えたのに記録がない
- 変更が大きすぎてロールバックしにくい
