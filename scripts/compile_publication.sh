#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ROOT="/media/Windows/midi_agent/.local/miniconda3"
CONDA_ENV="midi-agent"
TEX_FILE="${REPO_ROOT}/publication/main.tex"
PDF_FILE="${REPO_ROOT}/publication/main.pdf"

if [[ ! -x "${CONDA_ROOT}/bin/conda" ]]; then
  echo "[fatal] conda not found at ${CONDA_ROOT}/bin/conda"
  exit 2
fi

# shellcheck disable=SC1091
source "${CONDA_ROOT}/bin/activate" "${CONDA_ENV}"

if ! command -v tectonic >/dev/null 2>&1; then
  echo "[setup] tectonic not found in env=${CONDA_ENV}, installing via conda-forge..."
  conda install -y -n "${CONDA_ENV}" -c conda-forge tectonic
fi

echo "[compile] using $(command -v tectonic)"
cd "${REPO_ROOT}/publication"
tectonic -X compile "${TEX_FILE}"

echo "[ok] built: ${PDF_FILE}"
ls -lh "${PDF_FILE}"
stat -c '%y %n' "${PDF_FILE}"

