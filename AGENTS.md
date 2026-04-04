あなたは優秀なソフトウェアエンジニアです。
以下の要件に従って、APIホスト型LLMを使った「日本語の社内資料向けスライド生成アプリ」への移行を実装してください。

# 目的
自然言語入力から、日本語の社内資料向けスライド草案を生成するアプリを維持しつつ、
推論バックエンドをローカルLLMからAPIホスト型LLMへ置き換えたいです。

この変更はプロダクトの全面刷新ではなく、インフラ変更です。
既存アーキテクチャ、既存のレンダリングパイプライン、既存のJSON中心設計をできるだけ維持してください。

品質目標:
- 生成品質は 60 / 100 程度でよい
- 速度と安定性を優先する
- 日本語で短いスライド向け表現を返す

想定資料枚数:
- 3〜10枚

# 最重要原則
1. JSON を single source of truth にする
2. 推論バックエンドを差し替え可能にする
3. 既存レンダリングとエクスポートの影響範囲を最小化する
4. PPTX はユーザーが明示的にエクスポート操作をした時だけ生成する

# 全体アーキテクチャ
[Input]
  ↓
[Preprocess]
  ↓
[Prompt Builder]
  ↓
[LLM Provider]
  ↓
[Raw Response]
  ↓
[Response Parser / Validator / Repair]
  ↓
[構造化データ(JSON)]
  ↓
[Rendering Layer (HTML / Marp / Preview)]
  ↓
[Optional Export (PPTX / PDF / HTML)]

今回は Python を採用してください。
理由:
- FastAPI との相性がよい
- pydantic による JSON バリデーションがしやすい
- httpx で API 接続を抽象化しやすい
- Jinja2 / Markdown / Marp / python-pptx に広げやすい

# 移行ゴール
ローカルLLM依存のメイン推論経路を、APIホスト型LLMプロバイダに差し替えてください。

重要:
- 現在のアーキテクチャはなるべく維持する
- 大規模な再設計は避ける
- 既存インターフェースは可能な限り維持する
- レンダリングパイプラインは維持する
- JSON 契約は維持する
- バックエンドはスワップ可能にする

# 開発方針
- これは infrastructure change であり product redesign ではない
- JSON を正本にする
- HTML プレビューは JSON のプレビュー兼編集UIのままにする
- PPTX export は自動実行しない
- exporter はユーザーが明示操作した時だけ動かす
- prompt builder / provider / parser / domain model / renderer / exporter を分離する
- 必要最小限の差分で移行する

# 対象ユーザー
- 社内資料作成者
- 主な用途:
  - 会議資料
  - 課題整理資料
  - 上司向け説明資料
  - 役員向け簡易提案資料

# 想定入力
ユーザーは自然言語で資料要件を入力する想定です。
既存の structured form がある場合は、できるだけ維持してください。

# MVPで維持したい機能
1. ユーザー入力
2. APIホスト型LLMへプロンプト送信
3. 構造化JSONの生成
4. JSONの検証 / 修復 / 再試行
5. JSONからHTMLプレビューを描画
6. JSONからスライドプレビューを描画
7. JSONを編集して再描画
8. ユーザー明示操作によるPPTX export
9. エラー時に理由がわかる表示

# 非目標
- 画像生成
- 高度なチャート生成
- 大規模なUI再設計
- 認証基盤の再設計
- DB再設計
- マルチエージェント化
- スキーマの大規模変更

# 技術スタック
- Python 3.11+
- FastAPI
- Jinja2
- Pydantic v2
- httpx
- uvicorn
- Marp CLI
- python-pptx または既存PPTX exporter
- 必要ならサーバーサイドHTML + 最小限のJavaScript

# JSON 契約
生成されるスライドJSONは以下の shape を守ってください。

```json
{
  "deck_title": "string",
  "slides": [
    {
      "id": "string",
      "type": "title | agenda | content | summary",
      "title": "string",
      "bullets": ["string"],
      "layout": "layout1 | layout2 | layout3 | layout4"
    }
  ]
}
```

制約:
- スライド数は 3〜10
- 1スライドの bullets は 1〜4
- title は 30文字前後まで
- bullet は 40文字前後まで
- 出力言語は日本語
- 最初のスライドは title
- 最後のスライドは summary
- content slide を最低1枚含める

# 推論品質要件
- draft-quality でよい
- 品質目標は 60 / 100
- 完璧な文面よりも、短くて壊れにくいJSONを優先する
- 1スライド1メッセージを維持する

# レイヤ分離
責務は次の単位で分けてください。

1. prompt builder
2. LLM provider
3. response parser / validator / repair
4. slide JSON domain model
5. renderer
6. PPTX exporter

これらを混在させないでください。

# Provider abstraction 要件
推論は provider interface 経由で扱ってください。

例:

generate_slides(input_data) -> SlideDeck
health_check() -> bool
is_configured() -> bool

provider layer の責務:
- prompt input を受ける
- request payload を組み立てる
- API model を呼ぶ
- raw text または structured response を返す
- timeout / retry / predictable error handling を提供する

provider layer の非責務:
- HTML を描画しない
- PPTX を生成しない
- UI ロジックを持たない

rest of app は特定ベンダーAPIに直接依存しないでください。

# API migration 要件
設定は環境変数で切り替え可能にしてください。

例:
- LLM_PROVIDER
- LLM_API_KEY
- LLM_MODEL
- LLM_BASE_URL
- LLM_TIMEOUT_MS

禁止:
- secret のハードコード
- API key のコミット

# 信頼性要件
防御的に扱うこと:
- timeout
- malformed response
- rate limit
- temporary API failure
- invalid JSON output

対応方針:
- retry は少数回に限定する
- useful error context をログに残す
- fail gracefully にする
- 既存の repair logic があれば流用する
- repair できなければ 1〜2 回だけ retry する

# Prompt 要件
プロンプトは専用 module に置いてください。
route handler や UI component に大きな prompt を inline しないでください。

プロンプトで強く指示すること:
- strict JSON only
- no markdown
- no explanations
- Japanese output
- short slide-like phrases
- fixed slide types
- fixed layout selection rules

# 現在の flow で維持したいもの
現在のパイプライン概念は維持してください。

User Input
-> Preprocess
-> LLM inference
-> JSON validation / repair
-> Preview rendering
-> Optional PPTX export

不要な redesign は避けてください。

# レンダリング要件
- HTML preview は JSON から描画する
- slide preview rendering も JSON から描画する
- HTML や PPTX をモデルの primary output にしない
- current renderer には最小変更で済むようにする

# PPTX export 要件
- PPTX export path は維持してよい
- ただし PPTX 生成はユーザーが明示的に export を実行した時だけ行う
- 自動生成や推論直後の export は行わない
- JSON から PPTX を生成する構造は維持する

# API / 画面要件
最低限維持したい flow:
1. ユーザーが自然言語または既存フォームで入力
2. Generate を押す
3. JSON が生成される
4. JSON から preview が表示される
5. 必要なら手動で PPTX export する

この移行では、UI/UX を完璧にするより、推論の安定化と JSON 維持を優先してください。

# ディレクトリ構成
既存構造を尊重しつつ、少なくとも責務は以下のように保ってください。

app/
  main.py
  routes/
  templates/
  static/
  llm/ or providers/
    base.py
    api_provider.py
    prompts.py
  models/
    schema.py
  services/
    generation_service.py
    render_service.py
    export_service.py
    pptx_service.py
  utils/
    json_extract.py
    config.py

ファイル名は既存資産を活かしてよいですが、責務は崩さないでください。

# 設定
環境変数で切り替えられるようにしてください。

例:
- LLM_PROVIDER=openai_compatible
- LLM_API_KEY=...
- LLM_MODEL=gpt-4.1-mini
- LLM_BASE_URL=https://api.example.com/v1
- LLM_TIMEOUT_MS=30000
- MARP_CLI_PATH=marp

# 実装時の重要条件
- 型を丁寧に付ける
- 関数ごとに責務を分離する
- コメントは最小限で意図が分かるようにする
- 例外処理を入れる
- README を最新要件に更新する
- requirements.txt を必要に応じて更新する
- サンプル入力とサンプル出力 JSON を用意する
- 可能なら pytest で最低限のテストを追加する

# READMEに含める内容
- セットアップ手順
- API provider の設定方法
- 環境変数一覧
- アプリ起動方法
- JSON 契約
- provider 切り替え方
- PPTX export の実行方法
- ディレクトリ構成
- 今回の制限事項

# 優先順位
1. 現在のアーキテクチャ維持
2. JSON 契約維持
3. preview flow 維持
4. 推論の速度と安定性
5. 実装の単純さ
6. 品質最適化は後回し

# 期待する成果物
- provider abstraction for inference
- API-backed provider implementation
- updated configuration via environment variables
- preserved slide JSON contract
- minimal changes to renderer and PPTX export path
- README
- requirements.txt
- 最低限のテスト

# 実装ルール
- 不明な点は合理的に補完する
- 過剰実装しない
- migration task として差分を抑える
- 将来の provider swapping をしやすくする
- business logic と rendering / export を混ぜない

この要件に基づいて実装してください。

追加の引き継ぎ事項がある場合は `NEXT_STEPS.md` を参照してください。
