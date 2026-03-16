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
N="${1:-8}"
TARGET_RUN_ID="${2:-latest}"

printf "=== Log Paths ===\n"
printf "terminal: %s\n" "$TERM_PATH"
printf "raw llm : %s\n" "$RAW_PATH"
printf "metrics : %s\n\n" "$METRICS_PATH"
printf "view mode: run-centric (target=%s)\n\n" "$TARGET_RUN_ID"

# Arrow-key run selection via fzf (if installed).
if [[ "$TARGET_RUN_ID" == "latest" ]] && [[ -t 0 ]] && command -v fzf >/dev/null 2>&1; then
  pick="$(
    python3 - "$RAW_PATH" "$METRICS_PATH" "$TERM_PATH" <<'PY' \
      | fzf --ansi --height 70% --reverse --prompt="Select run> " --header="↑/↓ choose, Enter confirm"
import json
import re
import sys
from collections import Counter
from pathlib import Path

raw_path, metrics_path, term_path = sys.argv[1:]

def read_jsonl(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows

raw_rows = read_jsonl(raw_path)
metric_rows = read_jsonl(metrics_path)
term_lines = Path(term_path).read_text(encoding="utf-8", errors="replace").splitlines() if Path(term_path).exists() else []

run_ids = []
for r in raw_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for r in metric_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for ln in term_lines:
    m = re.search(r"\[run_id=([^\]]+)\]", ln)
    if m:
        run_ids.append(m.group(1))

seen = set()
ordered = []
for rid in run_ids:
    if rid not in seen:
        seen.add(rid)
        ordered.append(rid)

def run_ts(rid: str) -> int:
    m = re.match(r"^run-(\d+)$", rid or "")
    return int(m.group(1)) if m else -1

ordered = sorted(ordered, key=run_ts)

for rid in reversed(ordered[-50:]):
    rr = [x for x in raw_rows if x.get("run_id") == rid]
    mr = [x for x in metric_rows if x.get("run_id") == rid]
    chunk_rr = [x for x in rr if x.get("kind") == "chunk"]
    parse_ok = sum(1 for x in mr if x.get("parse_ok"))
    parse_fail = len(mr) - parse_ok
    bars = [x.get("meta", {}).get("bar") for x in chunk_rr if x.get("meta", {}).get("bar") is not None]
    retry_bars = sum(1 for c in Counter(bars).values() if c > 1)
    print(
        f"{rid}\traw={len(rr)} chunk={len(chunk_rr)} metrics={len(mr)} "
        f"ok={parse_ok} fail={parse_fail} retry_bars={retry_bars}"
    )
PY
  )"
  if [[ -n "${pick:-}" ]]; then
    TARGET_RUN_ID="${pick%%$'\t'*}"
  fi
fi

# Fallback selector when fzf is unavailable: simple numeric prompt.
if [[ "$TARGET_RUN_ID" == "latest" ]] && [[ -t 0 ]] && ! command -v fzf >/dev/null 2>&1; then
  mapfile -t RUN_CANDIDATES < <(
    python3 - "$RAW_PATH" "$METRICS_PATH" "$TERM_PATH" <<'PY'
import json
import re
import sys
from pathlib import Path

raw_path, metrics_path, term_path = sys.argv[1:]

def read_jsonl(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows

raw_rows = read_jsonl(raw_path)
metric_rows = read_jsonl(metrics_path)
term_lines = Path(term_path).read_text(encoding="utf-8", errors="replace").splitlines() if Path(term_path).exists() else []

run_ids = []
for r in raw_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for r in metric_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for ln in term_lines:
    m = re.search(r"\[run_id=([^\]]+)\]", ln)
    if m:
        run_ids.append(m.group(1))

seen = set()
ordered = []
for rid in run_ids:
    if rid not in seen:
        seen.add(rid)
        ordered.append(rid)

def run_ts(rid: str) -> int:
    m = re.match(r"^run-(\d+)$", rid or "")
    return int(m.group(1)) if m else -1

ordered = sorted(ordered, key=run_ts)

for rid in ordered[-20:]:
    print(rid)
PY
  )
  if [[ "${#RUN_CANDIDATES[@]}" -gt 0 ]]; then
    echo "Select run (number, Enter=latest):"
    for i in "${!RUN_CANDIDATES[@]}"; do
      idx=$((i + 1))
      mark=""
      if [[ "$idx" -eq "${#RUN_CANDIDATES[@]}" ]]; then
        mark=" (latest)"
      fi
      echo "  $idx. ${RUN_CANDIDATES[$i]}$mark"
    done
    read -r -p "Run number: " PICK_NUM || true
    if [[ -n "${PICK_NUM:-}" ]] && [[ "$PICK_NUM" =~ ^[0-9]+$ ]] \
      && [[ "$PICK_NUM" -ge 1 ]] && [[ "$PICK_NUM" -le "${#RUN_CANDIDATES[@]}" ]]; then
      TARGET_RUN_ID="${RUN_CANDIDATES[$((PICK_NUM - 1))]}"
    fi
  fi
fi

python3 - "$RAW_PATH" "$METRICS_PATH" "$TERM_PATH" "$N" "$TARGET_RUN_ID" <<'PY'
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

raw_path, metrics_path, term_path, n_s, target = sys.argv[1:]
n = int(n_s)


def read_jsonl(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows


raw_rows = read_jsonl(raw_path)
metric_rows = read_jsonl(metrics_path)
term_lines = []
p_term = Path(term_path)
if p_term.exists():
    term_lines = p_term.read_text(encoding="utf-8", errors="replace").splitlines()

run_ids = []
for r in raw_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for r in metric_rows:
    rid = r.get("run_id")
    if rid:
        run_ids.append(rid)
for ln in term_lines:
    m = re.search(r"\[run_id=([^\]]+)\]", ln)
    if m:
        run_ids.append(m.group(1))

if not run_ids:
    print("No run_id records found yet. Run the agent once, then retry.")
    raise SystemExit(0)

# Preserve order of first appearance.
seen = set()
ordered_run_ids = []
for rid in run_ids:
    if rid not in seen:
        seen.add(rid)
        ordered_run_ids.append(rid)

def run_ts(rid: str) -> int:
    m = re.match(r"^run-(\d+)$", rid or "")
    return int(m.group(1)) if m else -1

ordered_run_ids = sorted(ordered_run_ids, key=run_ts)

latest_run = ordered_run_ids[-1]
target_run = latest_run

if target == "latest":
    target_run = latest_run
else:
    target_run = target

print("=== Runs Overview ===")
for rid in ordered_run_ids[-10:]:
    rr = [x for x in raw_rows if x.get("run_id") == rid]
    mr = [x for x in metric_rows if x.get("run_id") == rid]
    tr = [x for x in term_lines if f"[run_id={rid}]" in x]

    chunk_rr = [x for x in rr if x.get("kind") == "chunk"]
    err_rr = sum(1 for x in rr if x.get("error"))
    parse_ok = sum(1 for x in mr if x.get("parse_ok"))
    parse_fail = len(mr) - parse_ok
    regen_total = sum(int(x.get("chunk_regen_count", 0) or 0) for x in mr)

    bars = [x.get("meta", {}).get("bar") for x in chunk_rr]
    bar_counts = Counter(b for b in bars if b is not None)
    retry_bars = sum(1 for c in bar_counts.values() if c > 1)

    print(
        f"- {rid}: raw={len(rr)} chunk={len(chunk_rr)} raw_err={err_rr} "
        f"metrics={len(mr)} parse_ok={parse_ok} parse_fail={parse_fail} "
        f"regen_total={regen_total} retry_bars={retry_bars} term_lines={len(tr)}"
    )

if target_run not in ordered_run_ids:
    print(f"\nTarget run_id not found: {target_run}")
    print(f"Tip: use one of above run_id values. Latest is {latest_run}")
    raise SystemExit(1)

print(f"\n=== Selected Run: {target_run} ===")
rr = [x for x in raw_rows if x.get("run_id") == target_run]
mr = [x for x in metric_rows if x.get("run_id") == target_run]
tr = [x for x in term_lines if f"[run_id={target_run}]" in x]

print(f"raw_records={len(rr)} metrics_records={len(mr)} terminal_lines={len(tr)}")

print("\n--- Terminal (selected run, last lines) ---")
for ln in tr[-n:]:
    print(ln)

print("\n--- Chunk Attempts by Bar ---")
chunk_rr = [x for x in rr if x.get("kind") == "chunk"]
by_bar = defaultdict(list)
for x in chunk_rr:
    bar = x.get("meta", {}).get("bar")
    by_bar[bar].append(x)

for bar in sorted(k for k in by_bar.keys() if k is not None):
    items = sorted(by_bar[bar], key=lambda x: int(x.get("seq") or 0))
    attempts = [str(i.get("meta", {}).get("attempt")) for i in items]
    errs = sum(1 for i in items if i.get("error"))
    print(f"bar={bar}: tries={len(items)} attempts=[{', '.join(attempts)}] errors={errs}")

print("\n--- Raw LLM (selected run, last records) ---")
for x in rr[-n:]:
    out = (x.get("output_text") or "").replace("\n", " ")
    if len(out) > 140:
        out = out[:137] + "..."
    print("---")
    print(
        f"seq={x.get('seq')} kind={x.get('kind')} bar={x.get('meta',{}).get('bar')} "
        f"attempt={x.get('meta',{}).get('attempt')} error={x.get('error')}"
    )
    print(f"out={out}")

print("\n--- Metrics (selected run, last records) ---")
for x in mr[-n:]:
    print("---")
    print(
        f"ts={x.get('timestamp')} parse_ok={x.get('parse_ok')} fatal={x.get('fatal_error_count')} "
        f"regen={x.get('chunk_regen_count')} repair={x.get('repair_applied')} "
        f"late={x.get('scheduler_late_count')} events={x.get('event_count')}"
    )
PY
