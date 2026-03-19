#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCAL_TECTONIC="${REPO_ROOT}/.local/bin/tectonic"
PAPER_BASENAME="symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology"
PAPER_TEX="${PAPER_BASENAME}.tex"
PAPER_PDF="${PAPER_BASENAME}.pdf"

cd "${SCRIPT_DIR}"

if [[ -x "${LOCAL_TECTONIC}" ]]; then
  "${LOCAL_TECTONIC}" "${PAPER_TEX}"
else
  tectonic "${PAPER_TEX}"
fi

OUTPUT_PATH="${REPO_ROOT}/${PAPER_PDF}"
cp "${PAPER_PDF}" "${OUTPUT_PATH}"
echo "Paper PDF written to ${OUTPUT_PATH}"
