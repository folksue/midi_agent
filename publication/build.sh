#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${SCRIPT_DIR}"
tectonic main.tex

TITLE="$(python3 - <<'PY'
from pathlib import Path
import re
text = Path("main.tex").read_text(encoding="utf-8")
m = re.search(r"\\title\{([^}]*)\}", text)
title = m.group(1).strip() if m else "paper"
print(title)
PY
)"

OUTPUT_PATH="${REPO_ROOT}/${TITLE}.pdf"
cp main.pdf "${OUTPUT_PATH}"
echo "Paper PDF written to ${OUTPUT_PATH}"
