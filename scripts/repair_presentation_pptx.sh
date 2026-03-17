#!/usr/bin/env bash
set -euo pipefail

RAW_DECK="${1:-docs/presentation/paper-proposal-deck-raw.pptx}"
FINAL_DECK="${2:-docs/presentation/paper-proposal-deck.pptx}"
ROUNDTRIP_DIR="${3:-docs/presentation/roundtrip}"
SOFFICE_BIN="${SOFFICE_BIN:-/Applications/LibreOffice.app/Contents/MacOS/soffice}"
RAW_BASE="$(basename "${RAW_DECK%.*}")"
ODP_PATH="${ROUNDTRIP_DIR}/${RAW_BASE}.odp"
ROUNDTRIP_PPTX_PATH="${ROUNDTRIP_DIR}/${RAW_BASE}.pptx"

if [[ ! -x "${SOFFICE_BIN}" ]]; then
  echo "LibreOffice soffice binary not found: ${SOFFICE_BIN}"
  exit 1
fi

if [[ ! -f "${RAW_DECK}" ]]; then
  echo "Raw presentation not found: ${RAW_DECK}"
  exit 1
fi

mkdir -p "${ROUNDTRIP_DIR}"
rm -f "${ODP_PATH}" "${ROUNDTRIP_PPTX_PATH}"

"${SOFFICE_BIN}" --headless --convert-to odp --outdir "${ROUNDTRIP_DIR}" "${RAW_DECK}"
"${SOFFICE_BIN}" --headless --convert-to pptx --outdir "${ROUNDTRIP_DIR}" "${ODP_PATH}"

cp "${ROUNDTRIP_PPTX_PATH}" "${FINAL_DECK}"
echo "PowerPoint-compatible presentation written to ${FINAL_DECK}"
