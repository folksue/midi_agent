#!/usr/bin/env bash
set -euo pipefail

ENV_DIR="${1:-asmcm-env}"
DECK_PATH="${2:-docs/presentation/paper-proposal-deck.pptx}"
OUT_DIR="${3:-docs/presentation/rendered}"
SOFFICE_DIR="${SOFFICE_DIR:-/Applications/LibreOffice.app/Contents/MacOS}"
BREW_BIN="${BREW_BIN:-/opt/homebrew/bin}"
PY_BIN="${ENV_DIR}/bin/python"
SLIDES_TEST_SCRIPT="docs/presentation/scripts/slides_test.py"
DETECT_FONT_SCRIPT="docs/presentation/scripts/detect_font.py"

mkdir -p "${OUT_DIR}"

if [[ ! -x "${PY_BIN}" ]]; then
  echo "Python interpreter not found: ${PY_BIN}"
  echo "Create the environment first with: bash scripts/setup_asmcm_env.sh"
  exit 1
fi

if [[ ! -f "${DECK_PATH}" ]]; then
  echo "Deck not found: ${DECK_PATH}"
  exit 1
fi

PATH="${SOFFICE_DIR}:${BREW_BIN}:${PATH}" "${PY_BIN}" "${SLIDES_TEST_SCRIPT}" "${DECK_PATH}"
PATH="${SOFFICE_DIR}:${BREW_BIN}:${PATH}" "${PY_BIN}" "${DETECT_FONT_SCRIPT}" "${DECK_PATH}" --json > "${OUT_DIR}/font-report.json"

echo "Validation finished. Font report: ${OUT_DIR}/font-report.json"
