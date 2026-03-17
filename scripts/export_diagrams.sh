#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-docs/diagrams/png}"
mkdir -p "${OUT_DIR}"
shopt -s nullglob

MERMAID_FILES=(docs/diagrams/*.mmd)
PLANTUML_FILES=(docs/diagrams/*.puml)
MMDC_BIN=""
PLANTUML_BIN=""
MERMAID_PUPPETEER_CONFIG="docs/presentation/mermaid-puppeteer-config.json"

if command -v mmdc >/dev/null 2>&1; then
  MMDC_BIN="$(command -v mmdc)"
elif [[ -x "docs/presentation/node_modules/.bin/mmdc" ]]; then
  MMDC_BIN="docs/presentation/node_modules/.bin/mmdc"
fi

if command -v plantuml >/dev/null 2>&1; then
  PLANTUML_BIN="$(command -v plantuml)"
elif [[ -x "/opt/homebrew/bin/plantuml" ]]; then
  PLANTUML_BIN="/opt/homebrew/bin/plantuml"
fi

if [[ -n "${MMDC_BIN}" ]]; then
  echo "[mermaid] exporting PNG files..."
  for src in "${MERMAID_FILES[@]}"; do
    base="$(basename "${src}" .mmd)"
    if [[ -f "${MERMAID_PUPPETEER_CONFIG}" ]]; then
      "${MMDC_BIN}" -p "${MERMAID_PUPPETEER_CONFIG}" -i "${src}" -o "${OUT_DIR}/${base}-mermaid.png"
    else
      "${MMDC_BIN}" -i "${src}" -o "${OUT_DIR}/${base}-mermaid.png"
    fi
  done
else
  echo "[mermaid] skip: Mermaid CLI was not found"
  echo "Install Mermaid CLI or run npm install in docs/presentation and rerun this script."
fi

if [[ -n "${PLANTUML_BIN}" ]]; then
  echo "[plantuml] exporting PNG files..."
  if ((${#PLANTUML_FILES[@]} > 0)); then
    "${PLANTUML_BIN}" -tpng "${PLANTUML_FILES[@]}"
  fi
  find docs/diagrams -maxdepth 1 -name '*.png' -exec mv {} "${OUT_DIR}/" \;
else
  echo "[plantuml] skip: PlantUML was not found"
  echo "Install PlantUML CLI and rerun this script."
fi

echo "Done. PNG files, when available, are in ${OUT_DIR}"
