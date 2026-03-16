#!/usr/bin/env bash
set -euo pipefail

# Edit these two lists.
MODELS=(
  "qwen2.5:3b"
  # "qwen3:4b"
  "qwen2.5:7b"
  
)

BENCHES=(
  "benchmark/data/model_io/note_level/sequence_cases.json"
  "benchmark/data/model_io/midilike/sequence_cases.json"
  "benchmark/data/model_io/remilike/sequence_cases.json"
)

OUT_DIR="${1:-benchmark/results/ollama_suite}"
MAX_CASES="${MAX_CASES:-0}"
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
TEMP="${TEMP:-0}"

models_csv="$(IFS=,; echo "${MODELS[*]}")"
benches_csv="$(IFS=,; echo "${BENCHES[*]}")"

python -m benchmark.scripts.run_ollama_model_list \
  --cases-list "${benches_csv}" \
  --models "${models_csv}" \
  --out-dir "${OUT_DIR}" \
  --max-cases "${MAX_CASES}" \
  --timeout "${TIMEOUT_SEC}" \
  --temperature "${TEMP}"

echo "[done] out_dir=${OUT_DIR}"
