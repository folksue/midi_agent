#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-8787}"

if [[ -x "asmcm-env/bin/python" ]]; then
  PYTHON_BIN="asmcm-env/bin/python"
else
  PYTHON_BIN="python3"
fi

exec "${PYTHON_BIN}" benchmark_web.py --host "${HOST}" --port "${PORT}"
