#!/usr/bin/env bash
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${MIDI_AGENT_ENV_FILE:-$PKG_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

METRICS_PATH="${MIDI_AGENT_METRICS_PATH:-/tmp/midi_agent_metrics.jsonl}"
RAW_PATH="${LLM_RAW_LOG_PATH:-/tmp/midi_agent_llm_raw.jsonl}"
TERM_PATH="${MIDI_AGENT_TERM_LOG_PATH:-/tmp/midi_agent_terminal.log}"

for p in "$TERM_PATH" "$RAW_PATH" "$METRICS_PATH"; do
  dir="$(dirname "$p")"
  mkdir -p "$dir"
  : > "$p"
  echo "[clear_logs] cleared: $p"
done

echo "[clear_logs] done"
