#!/usr/bin/env bash
set -euo pipefail

ENV_DIR="${1:-asmcm-env}"
DECK_PATH="${2:-docs/presentation/paper-proposal-deck.pptx}"
OUT_DIR="${3:-docs/presentation/rendered}"
SOFFICE_DIR="${SOFFICE_DIR:-/Applications/LibreOffice.app/Contents/MacOS}"
BREW_BIN="${BREW_BIN:-/opt/homebrew/bin}"
PY_BIN="${ENV_DIR}/bin/python"
RENDER_SCRIPT="docs/presentation/scripts/render_slides.py"
MONTAGE_SCRIPT="docs/presentation/scripts/create_montage.py"

if [[ ! -x "${PY_BIN}" ]]; then
  echo "Python interpreter not found: ${PY_BIN}"
  echo "Create the environment first with: bash scripts/setup_asmcm_env.sh"
  exit 1
fi

if [[ ! -f "${DECK_PATH}" ]]; then
  echo "Deck not found: ${DECK_PATH}"
  exit 1
fi

if [[ ! -f "${RENDER_SCRIPT}" ]]; then
  echo "Render helper not found: ${RENDER_SCRIPT}"
  exit 1
fi

PATH="${SOFFICE_DIR}:${BREW_BIN}:${PATH}" "${PY_BIN}" "${RENDER_SCRIPT}" "${DECK_PATH}" --output_dir "${OUT_DIR}"

if [[ -f "${MONTAGE_SCRIPT}" ]]; then
  PATH="${SOFFICE_DIR}:${BREW_BIN}:${PATH}" "${PY_BIN}" "${MONTAGE_SCRIPT}" \
    --input_dir "${OUT_DIR}" \
    --output_file "${OUT_DIR}/montage.png"
fi

echo "Rendered presentation assets are available in ${OUT_DIR}"
