#!/usr/bin/env bash
set -euo pipefail

# Auto-load project .env (if present), so API keys are available without manual source.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

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
  # "ollama:qwen2.5:7b"
  "openai:gpt-5-mini"
  # "gemini:gemini-2.5-flash"
  # "gemini:gemini-3.1-flash-preview"
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

LABEL_TASKS=(
  "task1_interval_identification"
  "task2_chord_identification"
  "task3_harmonic_function"
  "task4_voice_leading"
)

SEQUENCE_TASKS=(
  "task5_transposition"
  "task6_melodic_inversion"
  "task7_retrograde"
  "task8_rhythm_scale"
)

# ========= editable suite settings =========
# Data generation args (used only when regeneration happens).
SAMPLES_PER_TASK_DEFAULT=200
PROMPT_MODE_DEFAULT="agent_like"

# Regeneration mode:
# - auto: reuse existing *_cases.json; generate only if missing
# - always: always regenerate benchmark data
# - never: never regenerate; missing files cause failure
REGEN_MODE="always"

# Whether to run model inference after case files are ready.
RUN_MODELS=1

# Result directory (supports "{ts}" placeholder).
OUT_DIR_TEMPLATE="benchmark/results/suite_{ts}"

# Runtime knobs (shared by ollama + api runners).
# 最大测试用例数上限：控制基准套件本次最多执行多少个 case（这里设为 20）。
# 可用于缩短测试时间、限制资源消耗；当可用 case 多于该值时，只会运行前 MAX_CASES 个。
MAX_CASES=0
TIMEOUT_SEC=120
TEMP=0
SLEEP_SEC=0
SAVE_PARTIAL_ON_TIMEOUT=1

# Provider fallback when model string has no prefix.
DEFAULT_MODEL_PROVIDER="ollama"

usage() {
  cat <<'EOF'
Usage:
  bash benchmark/scripts/run_ollama_bench_suite.sh [samples_per_task] [prompt_mode] [generate_only]
  bash benchmark/scripts/run_ollama_bench_suite.sh [samples_per_task] [prompt_mode] [--generate-only|--run-models]

Args:
  samples_per_task  Optional. Default from SAMPLES_PER_TASK_DEFAULT.
  prompt_mode       Optional. light | agent_like. Default from PROMPT_MODE_DEFAULT.
  generate_only     Optional legacy positional. 1 => only generate benchmark data, do not run models.
                    0 => generate/reuse then run models.
                    If omitted, uses RUN_MODELS in script settings.

Flags:
  --generate-only   Named switch for generate_only=1.
  --run-models      Named switch for generate_only=0.
EOF
}

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

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SAMPLES_PER_TASK="${1:-${SAMPLES_PER_TASK_DEFAULT}}"
PROMPT_MODE="${2:-${PROMPT_MODE_DEFAULT}}"
GENERATE_ONLY_ARG="${3:-}"
if [[ -n "${GENERATE_ONLY_ARG}" ]]; then
  case "${GENERATE_ONLY_ARG}" in
    --generate-only|1|true|TRUE|yes|YES|y|Y)
      RUN_MODELS=0
      ;;
    --run-models|0|false|FALSE|no|NO|n|N)
      RUN_MODELS=1
      ;;
    *)
      echo "[fatal] invalid generate_only arg: ${GENERATE_ONLY_ARG} (use --generate-only/--run-models or 1/0)"
      usage
      exit 2
      ;;
  esac
fi
RUN_TS="$(date +%Y%m%d_%H%M%S)"

BENCHMARK_OUT_DIR="${OUT_DIR_TEMPLATE//\{ts\}/${RUN_TS}}"

declare -a TOKS=("${TOKENIZER_LIST_DEFAULT[@]}")

append_case_files_for_group() {
  local group="$1"
  for tok in "${TOKS[@]}"; do
    tok="$(trim "${tok}")"
    if [[ -z "${tok}" ]]; then
      continue
    fi
    CASE_FILES+=("benchmark/data/model_io/${tok}/${group}_cases.json")
  done
}

group_cases_ready() {
  local group="$1"
  local task_list=()
  case "${group}" in
    label) task_list=("${LABEL_TASKS[@]}") ;;
    sequence) task_list=("${SEQUENCE_TASKS[@]}") ;;
    *) return 1 ;;
  esac

  for tok in "${TOKS[@]}"; do
    tok="$(trim "${tok}")"
    if [[ -z "${tok}" ]]; then
      continue
    fi
    local out="benchmark/data/model_io/${tok}/${group}_cases.json"
    if [[ ! -f "${out}" ]]; then
      return 1
    fi
    for task in "${task_list[@]}"; do
      local by_task_fp="benchmark/data/model_io/${tok}/by_task/${task}.json"
      if [[ ! -f "${by_task_fp}" ]]; then
        return 1
      fi
    done
  done
  return 0
}

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
    python -m benchmark.scripts.build_model_io_json \
      --src "${src}" \
      --out "${out}" \
      --task-group "${group}" \
      --split-by-task \
      --out-dir "benchmark/data/model_io/${tok}/by_task" \
      --pretty
    CASE_FILES+=("${out}")
  done
}

declare -a CASE_FILES=()
for g in "${TASK_GROUP_LIST_DEFAULT[@]}"; do
  g="$(trim "${g}")"
  if [[ -z "${g}" ]]; then
    continue
  fi
  if [[ "${g}" != "label" && "${g}" != "sequence" ]]; then
    echo "[fatal] unsupported BENCHMARK_TASK_GROUPS entry: ${g} (use label/sequence)"
    exit 2
  fi
  case "${REGEN_MODE}" in
    always)
      echo "[suite] generating group=${g} (regen=always)"
      build_data_for_group "${g}"
      ;;
    auto)
      if group_cases_ready "${g}"; then
        echo "[suite] reusing existing group=${g} (regen=auto)"
        append_case_files_for_group "${g}"
      else
        echo "[suite] generating group=${g} (missing files, regen=auto)"
        build_data_for_group "${g}"
      fi
      ;;
    never)
      if group_cases_ready "${g}"; then
        echo "[suite] reusing existing group=${g} (regen=never)"
        append_case_files_for_group "${g}"
      else
        echo "[fatal] missing case files for group=${g} with REGEN_MODE=never"
        exit 2
      fi
      ;;
    *)
      echo "[fatal] unsupported REGEN_MODE=${REGEN_MODE} (use auto|always|never)"
      exit 2
      ;;
  esac
done

echo "[suite] generated case files:"
for c in "${CASE_FILES[@]}"; do
  echo "  - ${c}"
done

if [[ "${RUN_MODELS}" != "1" ]]; then
  echo "[done] generation only, RUN_MODELS=${RUN_MODELS}"
  exit 0
fi

declare -a OLLAMA_MODELS=()
declare -a API_MODELS=()
for m in "${MODEL_LIST[@]}"; do
  m="$(trim "${m}")"
  if [[ -z "${m}" ]]; then
    continue
  fi
  if [[ "${m}" == *:* ]]; then
    provider="${m%%:*}"
    rest="${m#*:}"
  else
    provider="${DEFAULT_MODEL_PROVIDER}"
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
      echo "[fatal] unsupported provider in MODEL_LIST: ${provider}"
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
    --max-cases "${MAX_CASES}"
    --timeout "${TIMEOUT_SEC}"
    --temperature "${TEMP}"
    --sleep "${SLEEP_SEC}"
  )
  if [[ "${SAVE_PARTIAL_ON_TIMEOUT}" != "1" ]]; then
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
    --out-dir "${BENCHMARK_OUT_DIR}/api" \
    --max-cases "${MAX_CASES}" \
    --timeout "${TIMEOUT_SEC}" \
    --temperature "${TEMP}" \
    --sleep "${SLEEP_SEC}"
fi

echo "[done] out_dir=${BENCHMARK_OUT_DIR}"
