#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_PATH="/tmp/ollama-linux-amd64.tar.zst"
INSTALL_ROOT="${ROOT_DIR}/.local"

if [[ ! -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  echo ".venv が見つかりません。先に Python 仮想環境を作成してください。" >&2
  exit 1
fi

if ! "${ROOT_DIR}/.venv/bin/python" -c "import zstandard" >/dev/null 2>&1; then
  echo "zstandard が未導入です。.venv/bin/pip install zstandard を実行してください。" >&2
  exit 1
fi

mkdir -p "${INSTALL_ROOT}"

echo "Downloading Ollama archive..."
curl -L https://ollama.com/download/ollama-linux-amd64.tar.zst -o "${ARCHIVE_PATH}"

echo "Extracting Ollama into ${INSTALL_ROOT}..."
"ROOT_DIR=${ROOT_DIR}" "${ROOT_DIR}/.venv/bin/python" - <<'PY'
import os
import tarfile
from pathlib import Path

import zstandard

root = Path(os.environ["ROOT_DIR"])
src = Path("/tmp/ollama-linux-amd64.tar.zst")
dest = root / ".local"
dest.mkdir(parents=True, exist_ok=True)

with src.open("rb") as fh:
    dctx = zstandard.ZstdDecompressor()
    with dctx.stream_reader(fh) as reader:
        with tarfile.open(fileobj=reader, mode="r|") as tar:
            tar.extractall(dest)
PY

echo "Ollama local install complete: ${INSTALL_ROOT}/bin/ollama"
