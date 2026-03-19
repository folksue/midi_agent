#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PROJECT_ROOT="$(cd .. && pwd)"
LOCAL_TECTONIC="$PROJECT_ROOT/.local/bin/tectonic"

if [[ -x "$LOCAL_TECTONIC" ]]; then
  "$LOCAL_TECTONIC" main.tex
else
  tectonic main.tex
fi
