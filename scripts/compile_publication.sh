#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER_BASENAME="symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology"
PDF_FILE="${REPO_ROOT}/${PAPER_BASENAME}.pdf"

echo "[compile] building publication via publication/build.sh"
"${REPO_ROOT}/publication/build.sh"

echo "[ok] built: ${PDF_FILE}"
ls -lh "${PDF_FILE}"
stat -f '%Sm %N' "${PDF_FILE}"
