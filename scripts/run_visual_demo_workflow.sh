#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SAMPLES_PER_TASK="${1:-8}"
PROMPT_MODE="${2:-agent_like}"
INCLUDE_EXPLANATIONS="${3:-yes}"

cd "${REPO_ROOT}"

echo "[Full local demo]"
echo "samples_per_task=${SAMPLES_PER_TASK}"
echo "prompt_mode=${PROMPT_MODE}"
echo "include_explanations=${INCLUDE_EXPLANATIONS}"
echo

INCLUDE_FLAG="True"
if [[ "${INCLUDE_EXPLANATIONS}" == "no" ]]; then
  INCLUDE_FLAG="False"
fi

"${PYTHON_BIN}" - <<PY
import benchmark_web

samples_per_task = int("${SAMPLES_PER_TASK}")
prompt_mode = "${PROMPT_MODE}"
include_explanations = ${INCLUDE_FLAG}

print(
    benchmark_web.run_full_local_demo(
        samples_per_task=samples_per_task,
        prompt_mode=prompt_mode,
        include_explanations=include_explanations,
    )
)
PY

echo
echo "Visual demo refreshed at:"
echo "${REPO_ROOT}/visual-demo/index.html"
