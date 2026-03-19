#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOST="${1:-127.0.0.1}"
PORT="${2:-8899}"

cd "${REPO_ROOT}"

echo "Serving visual-demo at http://${HOST}:${PORT}"
exec python3 -m http.server "${PORT}" --bind "${HOST}" --directory visual-demo
