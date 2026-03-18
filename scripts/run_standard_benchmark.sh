#!/usr/bin/env bash
set -euo pipefail

SAMPLES_PER_TASK="${1:-200}"
PROMPT_MODE="${2:-agent_like}"
BACKEND="${3:-none}"        # none | api | ollama
MODELS="${4:-}"

RAW_PATH="benchmark/data/raw_note_level/zero_shot.jsonl"
VIEWS_DIR="benchmark/data/views"
NOTE_CASES="benchmark/data/model_io/note_level/all_cases.json"
MIDILIKE_CASES="benchmark/data/model_io/midilike/all_cases.json"
REMILIKE_CASES="benchmark/data/model_io/remilike/all_cases.json"

echo "[1/6] Generating raw benchmark data..."
python3 -m benchmark.scripts.gen_zero_shot \
  --task-group all \
  --samples-per-task "${SAMPLES_PER_TASK}" \
  --prompt-mode "${PROMPT_MODE}" \
  --out "${RAW_PATH}"

echo "[2/6] Exporting tokenizer views..."
python3 -m benchmark.scripts.export_views \
  --src "${RAW_PATH}" \
  --prompt-mode "${PROMPT_MODE}"

echo "[3/6] Validating tokenizer consistency..."
python3 -m benchmark.scripts.validate_views

echo "[4/6] Building model-ready case files..."
python3 -m benchmark.scripts.build_model_io_json \
  --src "${VIEWS_DIR}/note_level/zero_shot.jsonl" \
  --out "${NOTE_CASES}" \
  --task-group all \
  --pretty

python3 -m benchmark.scripts.build_model_io_json \
  --src "${VIEWS_DIR}/midilike/zero_shot.jsonl" \
  --out "${MIDILIKE_CASES}" \
  --task-group all \
  --pretty

python3 -m benchmark.scripts.build_model_io_json \
  --src "${VIEWS_DIR}/remilike/zero_shot.jsonl" \
  --out "${REMILIKE_CASES}" \
  --task-group all \
  --pretty

echo "[5/6] Benchmark data is ready."
echo "note_level cases: ${NOTE_CASES}"
echo "This benchmark supports two usage modes:"
echo "- standard: prediction_label / prediction_notes"
echo "- explanatory: optional prediction_explanation for qualitative analysis"

sanitize_name() {
  printf "%s" "$1" | sed -E 's/[^A-Za-z0-9._-]+/_/g'
}

if [[ "${BACKEND}" == "none" ]]; then
  echo "[6/6] No model backend selected. Data preparation is complete."
  echo "Next steps:"
  echo "  API:    python3 -m benchmark.scripts.run_api_model_list --cases ${NOTE_CASES} --models gpt-4o-mini --out-dir benchmark/results/api"
  echo "  Ollama: python3 -m benchmark.scripts.run_ollama_model_list --cases ${NOTE_CASES} --models qwen2.5:7b --out-dir benchmark/results/ollama"
  echo "  Eval:   python3 -m benchmark.scripts.eval_predictions --gold ${VIEWS_DIR}/note_level/zero_shot.jsonl --pred <predictions.jsonl> --out benchmark/results/eval_predictions.json"
  exit 0
fi

if [[ -z "${MODELS}" ]]; then
  if [[ "${BACKEND}" == "api" ]]; then
    MODELS="gpt-4o-mini"
  elif [[ "${BACKEND}" == "ollama" ]]; then
    MODELS="qwen2.5:7b"
  fi
fi

if [[ "${BACKEND}" == "api" ]]; then
  OUT_DIR="benchmark/results/api"
  echo "[6/6] Running API backend with models=${MODELS}..."
  python3 -m benchmark.scripts.run_api_model_list \
    --cases "${NOTE_CASES}" \
    --models "${MODELS}" \
    --out-dir "${OUT_DIR}"

  OLDIFS="$IFS"
  IFS=','
  for model in ${MODELS}; do
    model="$(printf "%s" "${model}" | xargs)"
    [[ -z "${model}" ]] && continue
    safe_model="$(sanitize_name "${model}")"
    pred_path="${OUT_DIR}/pred_${safe_model}.jsonl"
    python3 -m benchmark.scripts.eval_predictions \
      --gold "${VIEWS_DIR}/note_level/zero_shot.jsonl" \
      --pred "${pred_path}" \
      --out "${OUT_DIR}/eval_${safe_model}.json" \
      --overall-out "${OUT_DIR}/overall_${safe_model}.json" \
      --by-task-out "${OUT_DIR}/by_task_${safe_model}.json" \
      --by-tokenizer-out "${OUT_DIR}/by_tokenizer_${safe_model}.json"
  done
  IFS="$OLDIFS"
  exit 0
fi

if [[ "${BACKEND}" == "ollama" ]]; then
  OUT_DIR="benchmark/results/ollama"
  BENCH_NAME="note_level_all_cases"
  echo "[6/6] Running Ollama backend with models=${MODELS}..."
  python3 -m benchmark.scripts.run_ollama_model_list \
    --cases "${NOTE_CASES}" \
    --models "${MODELS}" \
    --out-dir "${OUT_DIR}"

  OLDIFS="$IFS"
  IFS=','
  for model in ${MODELS}; do
    model="$(printf "%s" "${model}" | xargs)"
    [[ -z "${model}" ]] && continue
    safe_model="$(sanitize_name "${model}")"
    pred_path="${OUT_DIR}/${BENCH_NAME}/${safe_model}/pred_${safe_model}.jsonl"
    python3 -m benchmark.scripts.eval_predictions \
      --gold "${VIEWS_DIR}/note_level/zero_shot.jsonl" \
      --pred "${pred_path}" \
      --out "${OUT_DIR}/${BENCH_NAME}/${safe_model}/eval_${safe_model}.json" \
      --overall-out "${OUT_DIR}/${BENCH_NAME}/${safe_model}/overall_${safe_model}.json" \
      --by-task-out "${OUT_DIR}/${BENCH_NAME}/${safe_model}/by_task_${safe_model}.json" \
      --by-tokenizer-out "${OUT_DIR}/${BENCH_NAME}/${safe_model}/by_tokenizer_${safe_model}.json"
  done
  IFS="$OLDIFS"
  exit 0
fi

echo "Unknown backend: ${BACKEND}"
echo "Use one of: none, api, ollama"
exit 1
