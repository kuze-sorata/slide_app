# Slide Draft Generator MVP

Gemini などの API ホスト型 LLM を使って、日本語の社内資料向けスライド草案を構造化 JSON として生成する FastAPI アプリです。

このリファクタの目的は、ローカル LLM 依存を main inference path から外しつつ、既存の JSON 中心アーキテクチャを維持することです。

## 方針

- JSON を single source of truth にする
- 推論層だけを provider abstraction の背後へ移す
- HTML プレビューと Marp/PDF 出力は極力維持する
- 生成直後に export を自動実行しない
- provider を後から差し替えやすくする

## 現在のアーキテクチャ

```text
User Input
-> Preprocess
-> Prompt Builder
-> LLM Provider
-> Response Parser / Validator / Repair
-> Structured Slide JSON
-> Layout Resolver / RenderSpec
-> Preview Rendering
-> Optional Export
```

## JSON 契約

生成結果の canonical output は次です。

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
- bullets は 1〜4
- title は 30 文字以内
- bullet は 40 文字以内
- 出力は日本語
- 先頭は `title`
- 最後は `summary`
- `content` を最低 1 枚含める

## 実装範囲

- FastAPI
- Pydantic v2 schema
- provider abstraction
- API-backed provider
- Ollama / LM Studio は任意 provider として残す
- `POST /api/generate`
- `POST /api/render/html`
- `POST /api/update`
- `POST /api/export/marp`
- `POST /api/export/pdf`
- `POST /api/export/pptx`
- 入力フォーム `/`
- プレビュー画面 `/preview`
- JSON からのプレビュー編集
- 16:9 の単一スライドプレビューと左右ナビゲーション
- Marp markdown 出力
- PDF 出力
- PPTX 出力
- 最低限の pytest

## 入力方針

- 主入力は自然文の `資料リクエスト`
- `テーマ / 資料の目的 / 想定読者` は詳細設定で任意上書き
- preprocess で自然文から `theme / objective / audience / required_points` を補完
- 補助入力は自然文の解像度を上げるために使う

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 環境変数

`.env` かシェル環境で設定してください。最短では [`.env.example`](/home/sora/dev/llm-apps/slide_app/.env.example) を `.env` として使い、選んだ provider に応じた API key を埋めてください。

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai

LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_MS=60000
LLM_MAX_RETRIES=2

MOCK_GENERATION=false
GENERATION_TIMEOUT_SECONDS=120

MARP_CLI_PATH=marp
MARP_THEME=default
CHROME_PATH=/path/to/chrome-headless-shell
MARP_TIMEOUT_SECONDS=60

# optional local providers
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=phi3:mini
LMSTUDIO_BASE_URL=http://localhost:1234
LMSTUDIO_MODEL=local-model
```

主な項目:

- `LLM_PROVIDER`
  - `gemini` / `api` / `openai_compatible` / `ollama` / `lmstudio` を切り替える
- `LLM_API_KEY`
  - API provider の認証キー
- `LLM_MODEL`
  - 利用モデル名
- `LLM_BASE_URL`
  - `chat/completions` 互換 API の base URL
- `LLM_TIMEOUT_MS`
  - provider request timeout
- `LLM_MAX_RETRIES`
  - transport / rate limit / temporary failure 時の retry 回数
- structured output 非対応の chat/completions 互換 API では、自動で plain JSON mode へフォールバックします

## 起動方法

通常:

```bash
.venv/bin/uvicorn app.main:app --reload
```

補助スクリプト:

```bash
bash scripts/start_server.sh
```

`start_server.sh` は `LLM_PROVIDER=api` を既定にし、`LLM_PROVIDER=ollama` の時だけ Ollama 起動処理を行います。

## Provider 切り替え

Gemini:

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_gemini_api_key
export GEMINI_MODEL=gemini-2.5-flash
```

OpenAI compatible API:

```bash
export LLM_PROVIDER=api
export LLM_API_KEY=your_api_key
export LLM_MODEL=gpt-4.1-mini
export LLM_BASE_URL=https://api.openai.com/v1
```

Ollama:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=phi3:mini
```

LM Studio:

```bash
export LLM_PROVIDER=lmstudio
export LMSTUDIO_BASE_URL=http://localhost:1234
export LMSTUDIO_MODEL=local-model
```

モック:

```bash
export MOCK_GENERATION=true
```

## API

### `POST /api/generate`

入力:

```json
{
  "user_request": "営業部長向けに、営業進捗の振り返りを5枚で共有したい。現状の進捗、課題、次の打ち手を簡潔に整理したい。数字は仮置きでよい。",
  "slide_count": 5,
  "tone": "簡潔で落ち着いた説明",
  "extra_notes": "数字は仮置きでよい",
  "required_points": ["進捗", "課題", "次の打ち手"],
  "forbidden_expressions": ["気合いで", "なんとなく"],
  "debug_mode": false
}
```

`theme / objective / audience` は省略可能です。省略時は `user_request` から補完します。

出力は `deck_title` / `slides[]` を持つ slide JSON です。

### `POST /api/render/html`

slide JSON から HTML preview fragment を返します。

### `POST /api/update`

編集済み slide JSON を再検証して返します。

### `POST /api/export/marp`

slide JSON を Marp markdown に変換します。

### `POST /api/export/pdf`

slide JSON を PDF に変換します。実行はユーザーが明示的に trigger した時だけです。

### `POST /api/export/pptx`

slide JSON を PPTX に変換します。これも手動 export の時だけ実行します。

### `GET /api/debug/provider-health`

現在の provider の設定状態を返します。

### `GET /api/export/debug/config`

Marp / Chrome の解決結果を返します。

## 安定化方針

- prompt は `app/llm/prompts.py` に集約
- prompt では slide role を固定して 1枚1メッセージを強制する
- route handler に prompt を inline しない
- provider は raw text 取得だけに責務を寄せる
- response parser / validator は `GenerationService` と正規化層で処理
- 正規化層で bullet の重複除去、layout 補正、summary の action 化を行う
- `LayoutResolver` が JSON から共通の RenderSpec を作り、HTML / Marp / PPTX で共有する
- malformed response や invalid JSON は repair / retry を試す
- timeout, rate limit, temporary API failure を防御的に扱う
- ログには provider 名、prompt 長、応答時間、失敗理由を出す

## エクスポート

- Preview は JSON から描画する
- Preview UI は 16:9 の単一スライド表示で、左右の矢印またはキーボード左右キーで切り替える
- Marp/PDF も同じ JSON から生成する
- export は手動操作時のみ実行する
- PPTX は JSON から PowerPoint 用スライドへ変換して出力します

## サンプル

- 入力例: [`samples/sample_input.json`](/home/sora/dev/llm-apps/slide_app/samples/sample_input.json)
- 出力例: [`samples/sample_output.json`](/home/sora/dev/llm-apps/slide_app/samples/sample_output.json)
- 品質比較用入力:
  - [`samples/quality_input_manager_update.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_manager_update.json)
  - [`samples/quality_input_executive_briefing.json`](/home/sora/dev/llm-apps/slide_app/samples/quality_input_executive_briefing.json)
- 実験ログ:
  - [`docs/experiments/2026-04-04-prompt-structure-tightening.md`](/home/sora/dev/llm-apps/slide_app/docs/experiments/2026-04-04-prompt-structure-tightening.md)
- デザイン参考:
  - [`references/design/README.md`](/home/sora/dev/llm-apps/slide_app/references/design/README.md)
  - [`docs/design_guidelines.md`](/home/sora/dev/llm-apps/slide_app/docs/design_guidelines.md)
  - [`docs/slide_patterns.md`](/home/sora/dev/llm-apps/slide_app/docs/slide_patterns.md)

## 開発運用

スライド品質の改善は、小さな差分を branch / PR 単位で積み上げる運用を推奨します。

- Git / GitHub 運用ルール: [`docs/GIT_WORKFLOW.md`](/home/sora/dev/llm-apps/slide_app/docs/GIT_WORKFLOW.md)
- 実験ログテンプレート: [`docs/EXPERIMENT_LOG_TEMPLATE.md`](/home/sora/dev/llm-apps/slide_app/docs/EXPERIMENT_LOG_TEMPLATE.md)
- PR テンプレート: [`.github/pull_request_template.md`](/home/sora/dev/llm-apps/slide_app/.github/pull_request_template.md)

基本方針:

- `main` は常に動く状態を維持する
- 改善テーマごとに branch を切る
- fixed input で Before / After を比べる
- PR に仮説、確認方法、リスクを書く

## テスト

```bash
./.venv/bin/pytest
```

固定入力でローカル生成を確認する場合:

```bash
.venv/bin/python scripts/run_generation_fixture.py samples/quality_input_manager_update.json
```

## 制限事項

- 品質目標は draft-quality です
- wording より speed と stability を優先しています
- provider 側の structured output 互換性には差があります
- `debug_mode=true` は軽量 prompt を使いますが、通常生成より品質が落ちます
- PPTX export はテキスト中心のシンプルなレイアウトに限定しています
