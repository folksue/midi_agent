#!/usr/bin/env bash
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ID="${1:-latest}"
OUT_PATH="${2:-}"
BASE_DIR="${MIDI_AGENT_SUCCESS_MIDI_DIR:-$PKG_DIR/logs/success_midi}"
CONDA_BIN="$PKG_DIR/.local/miniconda3/bin/conda"

cmd=(python3 "$PKG_DIR/scripts/merge_run_midis.py" --run-id "$RUN_ID" --base-dir "$BASE_DIR")
if [[ -n "$OUT_PATH" ]]; then
  cmd+=(--out "$OUT_PATH")
fi

if [[ -x "$CONDA_BIN" ]]; then
  "$CONDA_BIN" run -n midi-agent "${cmd[@]}"
else
  "${cmd[@]}"
fi
