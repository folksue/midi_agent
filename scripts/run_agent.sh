#!/usr/bin/env bash
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(cd "$PKG_DIR/.." && pwd)"
ENV_FILE="${MIDI_AGENT_ENV_FILE:-$PKG_DIR/.env}"
TERM_LOG_PATH="${MIDI_AGENT_TERM_LOG_PATH:-/tmp/midi_agent_terminal.log}"
RUN_ID="${MIDI_AGENT_RUN_ID:-run-$(date +%s)}"
export MIDI_AGENT_RUN_ID="$RUN_ID"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "[run_agent] loaded env from $ENV_FILE"
else
  echo "[run_agent] no .env file at $ENV_FILE (continuing with current environment)"
fi

cd "$WORK_DIR"
echo "[run_agent] terminal log path: $TERM_LOG_PATH"
echo "[run_agent] run id: $RUN_ID"
if [[ -n "${LLM_RAW_LOG_PATH:-}" ]]; then
  echo "[run_agent] llm raw log path: ${LLM_RAW_LOG_PATH}"
else
  echo "[run_agent] llm raw log path: (disabled)"
fi
echo "[run_agent] ready: enter commands like '/play ...', '/stop', '/quit'"

set +e
PYTHONUNBUFFERED=1 python3 -m midi_agent "$@" 2>&1 \
  | awk -v rid="$RUN_ID" '{ print strftime("[%Y-%m-%d %H:%M:%S]"), "[run_id=" rid "]", $0; fflush(); }' \
  | tee -a "$TERM_LOG_PATH"
status=${PIPESTATUS[0]}
set -e
exit "$status"
