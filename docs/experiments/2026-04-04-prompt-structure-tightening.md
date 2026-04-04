# 品質改善 実験ログ

## 1. 基本情報

- 日付: 2026-04-04
- ブランチ: `current-progress-20260404`
- PR:
- 担当:

## 2. 改善テーマ

- 何を改善したいか:
  - スライドが単純な箇条書き列にならず、社内資料として使いやすい構成と表現になるよう改善する
- 対象レイヤ:
  - prompt builder
  - parser / validator
  - renderer

## 3. 仮説

- slide type ごとの役割を prompt に明示すると、モデルが「表紙 / agenda / 課題 / 打ち手 / まとめ」を意識しやすくなる
- 後段で bullet の重複除去、summary の action 化、layout の再判定を行うと、業務資料らしい短文へ安定化できる
- preview 上で `agenda` と `summary` の見せ方を分けると、同じ JSON 契約でも実務向けの見え方に近づく

## 4. 固定入力

- 入力ファイル:
  - [`samples/quality_input_manager_update.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_manager_update.json)
  - [`samples/quality_input_executive_briefing.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_executive_briefing.json)
- 入力概要:
  - 管理職向けの営業進捗共有
  - 役員向けの提案方針共有

入力例:

```json
{
  "theme": "営業進捗の振り返り",
  "objective": "上司に現状と打ち手を簡潔に共有し、優先対応をそろえる",
  "audience": "営業部長",
  "slide_count": 5,
  "tone": "簡潔で落ち着いた説明",
  "extra_notes": "数字は仮置きでよい。会議でそのまま読み上げやすい表現にする",
  "required_points": ["進捗", "課題", "次の打ち手"],
  "forbidden_expressions": ["気合いで", "なんとなく"]
}
```

## 5. 変更内容

- 実装した変更:
  - prompt に slide plan と content role を追加
  - normalizer に bullet の重複除去、曖昧語除去、summary の action 化、layout 再判定を追加
  - preview に `agenda / summary / layout3` の見せ方差分を追加
- 非対象:
  - provider 切替
  - JSON schema の必須項目追加
  - export API の新設

## 6. 確認結果

### Before

- タイトル:
  - `共有項目`
  - `対応方針をそろえる`
- bullets:
  - `背景`
  - `課題`
  - `打ち手`
  - `現状を短く整理`
- JSON 妥当性:
  - 通る
- プレビュー表示:
  - すべて同じカード表示
- 気になった点:
  - agenda が抽象的で、会議資料のトピックとして弱い
  - content が「整理する」中心で、何を判断するかが伝わりにくい
  - summary が次アクションより説明寄りになりやすい

### After

- タイトル:
  - `重点案件の停滞が課題`
  - `優先案件へ工数を再配分する`
  - `優先案件の再整理が必要`
- bullets:
  - `進捗の要点`
  - `課題の整理`
  - `次の打ち手`
  - `重点案件へ営業工数を寄せる`
  - `週次レビューを固定化する`
- JSON 妥当性:
  - 関連テスト 15 件が通過
- プレビュー表示:
  - `agenda` は番号リスト
  - `summary` は専用ラベル表示
  - `layout3` は 2 カラム表示
- 良くなった点:
  - 1 枚 1 メッセージが出やすくなった
  - summary が action-oriented になった
  - agenda と summary が視覚的にも区別しやすくなった
  - 根拠のない具体的な数値を prompt で抑制する方針を追加した
  - 要因列挙のような slide では layout3 を使いすぎないよう調整した

## 7. 差分の要約

- 変化した点:
  - 生成の指示が「JSONを返す」中心から「社内資料の役割を持つ slide を返す」中心へ変わった
  - validator 後に bullet と layout を補正する層が強化された
  - preview が slide type を反映するようになった
- まだ残る課題:
  - 実データや数値の説得力は provider と入力品質に依存する
  - 課題 slide と原因 slide の違いはまだ曖昧なことがある
  - 役員向けの結論先行トーンは追加の微調整余地がある
  - summary の action 生成は content bullet の質にまだ強く依存する

## 8. リスク

- 想定される副作用:
  - normalizer が補正しすぎると、モデル出力のニュアンスを削る可能性がある
  - layout3 判定が広すぎると、2 カラム表示が増えすぎる可能性がある
- 影響を受けそうなケース:
  - bullet が 1 個だけの content slide
  - ラフなメモ入力から短い資料を作るケース

## 9. 次に試すこと

- 次の候補 1:
  - 役員向け入力では title をより結論先行に寄せるルールを追加する
- 次の候補 2:
  - `docs/experiments/` に local 実行結果 JSON を残す自動化を追加する

## 10. ローカル確認手順

ローカルで Gemini を使って固定入力を再現する場合:

```bash
.venv/bin/python scripts/run_generation_fixture.py \
  samples/quality_input_manager_update.json \
  --output-json docs/experiments/artifacts/manager-update-after.json
```

```bash
.venv/bin/python scripts/run_generation_fixture.py \
  samples/quality_input_executive_briefing.json \
  --output-json docs/experiments/artifacts/executive-briefing-after.json
```
