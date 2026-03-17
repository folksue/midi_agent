#!/usr/bin/env bash
set -euo pipefail

# Unified suite:
# 1) generate benchmark cases (label + sequence)
# 2) run local models (ollama:*)
# 3) run API models (openai:* / gemini:*)
#
# Model list format:
#   BENCHMARK_MODELS=ollama:qwen2.5:7b,openai:gpt-4o-mini,gemini:gemini-2.5-flash

# ========= editable lists (explicit in this script) =========
# You can edit these directly without touching .env.
MODEL_LIST=(
  "ollama:qwen2.5:7b"
  "openai:gpt-4o-mini"
  # "gemini:gemini-2.5-flash"
)

TASK_GROUP_LIST_DEFAULT=(
  "label"
  "sequence"
)

TOKENIZER_LIST_DEFAULT=(
  "note_level"
  "midilike"
  "remilike"
)

trim() {
  local s="$1"
  # shellcheck disable=SC2001
  s="$(echo "${s}" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  echo "${s}"
}

join_csv() {
  local IFS=,
  echo "$*"
}

SAMPLES_PER_TASK="${1:-200}"
PROMPT_MODE="${2:-agent_like}"

BENCHMARK_TASK_GROUPS="${BENCHMARK_TASK_GROUPS:-$(join_csv "${TASK_GROUP_LIST_DEFAULT[@]}")}"
BENCHMARK_TOKENIZERS="${BENCHMARK_TOKENIZERS:-$(join_csv "${TOKENIZER_LIST_DEFAULT[@]}")}"
BENCHMARK_MODELS="${BENCHMARK_MODELS:-$(join_csv "${MODEL_LIST[@]}")}"
BENCHMARK_MODEL_DEFAULT_PROVIDER="${BENCHMARK_MODEL_DEFAULT_PROVIDER:-ollama}"
BENCHMARK_RUN_MODELS="${BENCHMARK_RUN_MODELS:-1}"
BENCHMARK_OUT_DIR="${BENCHMARK_OUT_DIR:-benchmark/results/suite}"

BENCHMARK_MAX_CASES="${BENCHMARK_MAX_CASES:-0}"
BENCHMARK_TIMEOUT_SEC="${BENCHMARK_TIMEOUT_SEC:-120}"
BENCHMARK_TEMP="${BENCHMARK_TEMP:-0}"
BENCHMARK_SLEEP_SEC="${BENCHMARK_SLEEP_SEC:-0}"
BENCHMARK_SAVE_PARTIAL_ON_TIMEOUT="${BENCHMARK_SAVE_PARTIAL_ON_TIMEOUT:-1}"

build_data_for_group() {
  local group="$1"
  local raw="benchmark/data/raw_note_level/zero_shot_${group}.jsonl"
  python -m benchmark.scripts.gen_zero_shot \
    --task-group "${group}" \
    --samples-per-task "${SAMPLES_PER_TASK}" \
    --prompt-mode "${PROMPT_MODE}" \
    --out "${raw}"

  python -m benchmark.scripts.export_views \
    --src "${raw}" \
    --prompt-mode "${PROMPT_MODE}"

  python -m benchmark.scripts.validate_views

  IFS=',' read -r -a TOKS <<< "${BENCHMARK_TOKENIZERS}" || true
  for tok in "${TOKS[@]}"; do
    tok="$(trim "${tok}")"
    if [[ -z "${tok}" ]]; then
      continue
    fi
    local src="benchmark/data/views/${tok}/zero_shot.jsonl"
    local out="benchmark/data/model_io/${tok}/${group}_cases.json"
    python -m benchmark.scripts.build_model_io_json \
      --src "${src}" \
      --out "${out}" \
      --task-group "${group}" \
      --pretty
    CASE_FILES+=("${out}")
  done
}

declare -a CASE_FILES=()
IFS=',' read -r -a TASK_GROUP_LIST <<< "${BENCHMARK_TASK_GROUPS}" || true
for g in "${TASK_GROUP_LIST[@]}"; do
  g="$(trim "${g}")"
  if [[ -z "${g}" ]]; then
    continue
  fi
  if [[ "${g}" != "label" && "${g}" != "sequence" ]]; then
    echo "[fatal] unsupported BENCHMARK_TASK_GROUPS entry: ${g} (use label/sequence)"
    exit 2
  fi
  echo "[suite] generating group=${g}"
  build_data_for_group "${g}"
done

echo "[suite] generated case files:"
for c in "${CASE_FILES[@]}"; do
  echo "  - ${c}"
done

if [[ "${BENCHMARK_RUN_MODELS}" != "1" ]]; then
  echo "[done] generation only, BENCHMARK_RUN_MODELS=${BENCHMARK_RUN_MODELS}"
  exit 0
fi

declare -a OLLAMA_MODELS=()
declare -a API_MODELS=()
IFS=',' read -r -a MODELS_RAW <<< "${BENCHMARK_MODELS}" || true
for m in "${MODELS_RAW[@]}"; do
  m="$(trim "${m}")"
  if [[ -z "${m}" ]]; then
    continue
  fi
  if [[ "${m}" == *:* ]]; then
    provider="${m%%:*}"
    rest="${m#*:}"
  else
    provider="${BENCHMARK_MODEL_DEFAULT_PROVIDER}"
    rest="${m}"
  fi
  provider="$(trim "${provider}")"
  rest="$(trim "${rest}")"
  case "${provider}" in
    ollama)
      OLLAMA_MODELS+=("${rest}")
      ;;
    openai|gemini)
      API_MODELS+=("${provider}:${rest}")
      ;;
    *)
      echo "[fatal] unsupported provider in BENCHMARK_MODELS: ${provider}"
      exit 2
      ;;
  esac
done

cases_csv="$(join_csv "${CASE_FILES[@]}")"
if [[ -n "${cases_csv}" && "${#OLLAMA_MODELS[@]}" -gt 0 ]]; then
  ollama_models_csv="$(join_csv "${OLLAMA_MODELS[@]}")"
  echo "[suite] running ollama models=${ollama_models_csv}"
  ollama_cmd=(
    python -m benchmark.scripts.run_ollama_model_list
    --cases-list "${cases_csv}"
    --models "${ollama_models_csv}"
    --out-dir "${BENCHMARK_OUT_DIR}/ollama"
    --max-cases "${BENCHMARK_MAX_CASES}"
    --timeout "${BENCHMARK_TIMEOUT_SEC}"
    --temperature "${BENCHMARK_TEMP}"
    --sleep "${BENCHMARK_SLEEP_SEC}"
  )
  if [[ "${BENCHMARK_SAVE_PARTIAL_ON_TIMEOUT}" != "1" ]]; then
    ollama_cmd+=(--no-save-partial-on-timeout)
  fi
  "${ollama_cmd[@]}"
fi

if [[ -n "${cases_csv}" && "${#API_MODELS[@]}" -gt 0 ]]; then
  api_models_csv="$(join_csv "${API_MODELS[@]}")"
  echo "[suite] running api models=${api_models_csv}"
  python -m benchmark.scripts.run_api_model_list \
    --cases-list "${cases_csv}" \
    --models "${api_models_csv}" \
    --default-provider "${BENCHMARK_MODEL_DEFAULT_PROVIDER}" \
    --out-dir "${BENCHMARK_OUT_DIR}/api" \
    --max-cases "${BENCHMARK_MAX_CASES}" \
    --timeout "${BENCHMARK_TIMEOUT_SEC}" \
    --temperature "${BENCHMARK_TEMP}" \
    --sleep "${BENCHMARK_SLEEP_SEC}"
fi

echo "[done] out_dir=${BENCHMARK_OUT_DIR}"
