#!/usr/bin/env bash
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(cd "$PKG_DIR/.." && pwd)"
RUNNER="$PKG_DIR/scripts/run_agent.sh"
ENV_FILE="${MIDI_AGENT_ENV_FILE:-$PKG_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

PLAY_SECS="${PLAY_SECS:-10}"
MAX_WAIT_SECS="${MAX_WAIT_SECS:-45}"
AUTO_QUIT="${AUTO_QUIT:-true}"
PROMPT="${PROMPT:-请播放C minor版本的小星星}"
METRICS_PATH="${MIDI_AGENT_METRICS_PATH:-/tmp/midi_agent_metrics_twinkle.jsonl}"
LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"

if [[ ! -x "$RUNNER" ]]; then
  echo "[test] runner not found or not executable: $RUNNER" >&2
  exit 1
fi

rm -f "$METRICS_PATH"
export MIDI_AGENT_METRICS_PATH="$METRICS_PATH"
export LLM_PROVIDER
export OLLAMA_BASE_URL
export OLLAMA_MODEL

cd "$WORK_DIR"

echo "[test] start auto-play prompt: $PROMPT"
echo "[test] play seconds: $PLAY_SECS"
echo "[test] max wait seconds: $MAX_WAIT_SECS"
echo "[test] auto quit: $AUTO_QUIT"
echo "[test] metrics: $METRICS_PATH"
echo "[test] provider: $LLM_PROVIDER"

if [[ "$LLM_PROVIDER" == "ollama" ]]; then
  echo "[test] checking ollama model: $OLLAMA_MODEL"
  python3 - <<'PY'
import json
import os
import sys
import urllib.request

base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
model = os.environ["OLLAMA_MODEL"].strip()
url = f"{base}/api/tags"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    names = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
except Exception as exc:
    print(f"[test] FAIL: cannot connect to ollama at {url}: {exc}", file=sys.stderr)
    sys.exit(10)

if model not in names:
    listed = ", ".join(names[:20]) if names else "<none>"
    print(f"[test] FAIL: model not found: {model}", file=sys.stderr)
    print(f"[test] available models: {listed}", file=sys.stderr)
    print(f"[test] hint: ollama pull {model}", file=sys.stderr)
    sys.exit(11)
PY
fi

(
  printf '/play %s\n' "$PROMPT"
  # Wait for first chunk metrics to appear, with timeout fallback.
  start_ts="$(date +%s)"
  while true; do
    if [[ -f "$METRICS_PATH" ]] && [[ "$(wc -l < "$METRICS_PATH" | tr -d ' ')" -ge 1 ]]; then
      break
    fi
    now_ts="$(date +%s)"
    elapsed="$((now_ts - start_ts))"
    if [[ "$elapsed" -ge "$MAX_WAIT_SECS" ]]; then
      break
    fi
    sleep 0.2
  done
  # Keep playing for configured window after first metric appears.
  sleep "$PLAY_SECS"
  printf '/stop\n'
  if [[ "${AUTO_QUIT,,}" == "true" ]]; then
    printf '/quit\n'
  fi
) | "$RUNNER"

for _ in 1 2 3 4 5; do
  [[ -f "$METRICS_PATH" ]] && break
  sleep 0.2
done

if [[ ! -f "$METRICS_PATH" ]]; then
  echo "[test] FAIL: metrics file not created: $METRICS_PATH" >&2
  exit 2
fi

line_count="$(wc -l < "$METRICS_PATH" | tr -d ' ')"
if [[ "$line_count" -lt 1 ]]; then
  echo "[test] FAIL: no chunk metrics produced" >&2
  exit 3
fi

echo "[test] chunk metrics lines: $line_count"
echo "[test] tail metrics:"
tail -n 5 "$METRICS_PATH"

echo "[test] PASS"
