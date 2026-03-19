#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PAPER_BASENAME="symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology"
PAPER_TEX="${PAPER_BASENAME}.tex"
PAPER_PDF="${PAPER_BASENAME}.pdf"

cd "${SCRIPT_DIR}"
tectonic "${PAPER_TEX}"

OUTPUT_PATH="${REPO_ROOT}/${PAPER_PDF}"
cp "${PAPER_PDF}" "${OUTPUT_PATH}"
echo "Paper PDF written to ${OUTPUT_PATH}"
