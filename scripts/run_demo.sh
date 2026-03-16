#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Non-interactive smoke run for CLI loop. Uses stub LLM if OPENAI_API_KEY is unset.
export MIDI_AGENT_METRICS_PATH="${MIDI_AGENT_METRICS_PATH:-/tmp/midi_agent_metrics.jsonl}"
(
  printf '/play demo groove\n'
  sleep 4
  printf '/stop\n'
  printf '/quit\n'
) | python3 -m midi_agent

echo "[demo] done"
