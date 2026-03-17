#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-docs/diagrams/png}"
mkdir -p "${OUT_DIR}"

if command -v mmdc >/dev/null 2>&1; then
  echo "[mermaid] exporting PNG files..."
  mmdc -i docs/diagrams/benchmark-usage-flow.mmd -o "${OUT_DIR}/benchmark-usage-flow-mermaid.png"
  mmdc -i docs/diagrams/benchmark-architecture.mmd -o "${OUT_DIR}/benchmark-architecture-mermaid.png"
else
  echo "[mermaid] skip: 'mmdc' was not found in PATH"
  echo "Install Mermaid CLI and rerun this script."
fi

if command -v plantuml >/dev/null 2>&1; then
  echo "[plantuml] exporting PNG files..."
  plantuml -tpng docs/diagrams/benchmark-usage-flow.puml docs/diagrams/benchmark-architecture.puml
  find docs/diagrams -maxdepth 1 -name '*.png' -exec mv {} "${OUT_DIR}/" \;
else
  echo "[plantuml] skip: 'plantuml' was not found in PATH"
  echo "Install PlantUML CLI and rerun this script."
fi

echo "Done. PNG files, when available, are in ${OUT_DIR}"
