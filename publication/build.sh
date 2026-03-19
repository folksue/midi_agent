#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PROJECT_ROOT="$(cd .. && pwd)"
LOCAL_TECTONIC="$PROJECT_ROOT/.local/bin/tectonic"
MAIN_TEX="symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology.tex"

if [[ -x "$LOCAL_TECTONIC" ]]; then
  "$LOCAL_TECTONIC" "$MAIN_TEX"
else
  tectonic "$MAIN_TEX"
fi
