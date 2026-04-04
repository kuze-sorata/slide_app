#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OLLAMA_BIN="${ROOT_DIR}/.local/bin/ollama"
UVICORN_BIN="${ROOT_DIR}/.venv/bin/uvicorn"
LLM_PROVIDER_VALUE="${LLM_PROVIDER:-api}"
OLLAMA_HOST_VALUE="${OLLAMA_HOST:-127.0.0.1:11434}"
OLLAMA_BASE_URL_VALUE="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL_VALUE="${OLLAMA_MODEL:-phi3:mini}"
MOCK_GENERATION_VALUE="${MOCK_GENERATION:-false}"
OLLAMA_DATA_DIR="${ROOT_DIR}/.ollama"
OLLAMA_LOG_DIR="${ROOT_DIR}/.logs"
OLLAMA_PID=""

mkdir -p "${OLLAMA_DATA_DIR}/models" "${OLLAMA_LOG_DIR}"

if [[ ! -x "${UVICORN_BIN}" ]]; then
  echo "uvicorn が見つかりません。.venv に依存関係をインストールしてください。" >&2
  exit 1
fi

export LLM_PROVIDER="${LLM_PROVIDER_VALUE}"
export MOCK_GENERATION="${MOCK_GENERATION_VALUE}"

cleanup() {
  if [[ -n "${OLLAMA_PID}" ]] && kill -0 "${OLLAMA_PID}" >/dev/null 2>&1; then
    kill "${OLLAMA_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

wait_for_ollama() {
  for _ in $(seq 1 30); do
    if curl -sf "${OLLAMA_BASE_URL}/api/tags" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if [[ "${LLM_PROVIDER}" == "ollama" ]]; then
  if [[ ! -x "${OLLAMA_BIN}" ]]; then
    echo "Ollama がローカル配置されていません。scripts/install_ollama_local.sh を先に実行してください。" >&2
    exit 1
  fi

  export PATH="${ROOT_DIR}/.local/bin:${PATH}"
  export OLLAMA_HOST="${OLLAMA_HOST_VALUE}"
  export OLLAMA_BASE_URL="${OLLAMA_BASE_URL_VALUE}"
  export OLLAMA_MODEL="${OLLAMA_MODEL_VALUE}"
  export OLLAMA_MODELS="${OLLAMA_DATA_DIR}/models"

  if ! curl -sf "${OLLAMA_BASE_URL}/api/tags" >/dev/null; then
    echo "Starting local Ollama..."
    "${OLLAMA_BIN}" serve >"${OLLAMA_LOG_DIR}/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    if ! wait_for_ollama; then
      echo "Ollama の起動確認に失敗しました。${OLLAMA_LOG_DIR}/ollama.log を確認してください。" >&2
      exit 1
    fi
  else
    echo "Ollama is already running at ${OLLAMA_BASE_URL}"
  fi

  if ! "${OLLAMA_BIN}" list | awk 'NR>1 {print $1}' | grep -Fx "${OLLAMA_MODEL}" >/dev/null 2>&1; then
    echo "Pulling model ${OLLAMA_MODEL} ..."
    "${OLLAMA_BIN}" pull "${OLLAMA_MODEL}"
  fi
fi

echo "Starting FastAPI on http://127.0.0.1:8000"
echo "LLM_PROVIDER=${LLM_PROVIDER}"
echo "MOCK_GENERATION=${MOCK_GENERATION}"
"${UVICORN_BIN}" app.main:app --reload --host 127.0.0.1 --port 8000
