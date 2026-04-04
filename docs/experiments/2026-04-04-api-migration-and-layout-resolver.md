# 品質改善 実験ログ

## 1. 基本情報

- 日付: 2026-04-04
- ブランチ: `current-progress-20260404`
- PR: 未作成
- 担当: Codex / sora

## 2. 改善テーマ

- 何を改善したいか:
  - API hosted LLM への移行を安定化する
  - JSON から PDF / PPTX / HTML への見た目差を減らす
  - プレビュー UI をスライドらしい確認体験にする
- 対象レイヤ:
  - provider / parser / validator / renderer / export / UI / docs

## 3. 仮説

- provider の structured output 依存を緩めれば、OpenAI 互換 API でも失敗しにくくなる
- JSON のあとに Layout Resolver / RenderSpec を挟めば、HTML / Marp / PPTX の見た目判断を揃えられる
- preview を 16:9 の単一スライド表示にすれば、一覧カード表示より視認性が上がる
- 自然文入力から `objective` を補完できれば、生成前バリデーション停止を減らせる

## 4. 固定入力

- 入力ファイル:
  - [`samples/quality_input_manager_update.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_manager_update.json)
  - [`samples/quality_input_executive_briefing.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_executive_briefing.json)
- 入力概要:
  - 社内向けの進捗共有
  - 役員向けの簡易説明
  - 自然文入力からの補完確認

## 5. 変更内容

- 実装した変更:
  - API provider に structured output 非対応時の plain JSON fallback を追加
  - export API を安定化
  - `LayoutResolver` と `RenderSpec` を追加
  - HTML / Marp / PPTX を共通レイアウト判断に寄せた
  - preview を 16:9 の単一スライド + 左右ナビゲーションへ変更
  - 自然文入力からの `objective` 補完ロジックを強化
  - README / AGENTS / `.env.example` を現仕様に合わせて更新
- 非対象:
  - LLM の文章品質そのものの大幅改善
  - exporter の完全な画面一致
  - 認証や DB の再設計

## 6. 確認結果

### Before

- タイトル:
  - API 移行後の大枠は動くが、provider 差異に弱い
- bullets:
  - JSON は出るが、renderer ごとに見せ方の判断が分散していた
- JSON 妥当性:
  - 自然文入力によっては `objective is required` で停止
- プレビュー表示:
  - 一覧カード表示で幅が足りず、3カード系が崩れやすい
- 気になった点:
  - PDF / PPTX の見た目差が大きい
  - docs と実装に細かいズレがあった

### After

- タイトル:
  - API hosted LLM 前提の説明と実装が整合
- bullets:
  - 3項目は3カード、layout3 は2カラム、summary は action cards として共通判断
- JSON 妥当性:
  - 自然文入力の補完が強くなり、生成前停止が減った
- プレビュー表示:
  - 16:9 の単一スライド表示になり、左右移動で確認可能
- 良くなった点:
  - renderer 間の一貫性が上がった
  - docs / env / 実装のズレが減った
  - export API の安定性が上がった

## 7. 差分の要約

- 変化した点:
  - JSON のあとに `Layout Resolver / RenderSpec` を追加
  - provider fallback と自然文補完の強化
  - preview UI の単一スライド化
- まだ残る課題:
  - PDF と PPTX の完全一致にはまだ差が残る
  - prompt 品質改善は今後も継続余地がある
  - preview のアニメーションや操作性はさらに改善可能

## 8. リスク

- 想定される副作用:
  - 共通 resolver のルールが強すぎると、表現の柔軟性を落とす可能性がある
  - preview の単一表示は一覧性が下がる
- 影響を受けそうなケース:
  - 4 bullet の複雑な content slide
  - 2カラムが適切でないのに layout3 が選ばれるケース
  - かなり曖昧な自然文入力

## 9. 次に試すこと

- 次の候補 1:
  - `LayoutResolver` の pattern 判定を title / agenda / content role ごとにさらに細かくする
- 次の候補 2:
  - preview と export の theme tokens を共通化して、色や余白の一致度をさらに上げる
