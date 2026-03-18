#!/usr/bin/env bash
set -euo pipefail

ENV_DIR="${1:-asmcm-env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[1/4] Creating virtual environment at ${ENV_DIR}..."
"${PYTHON_BIN}" -m venv "${ENV_DIR}"

echo "[2/4] Upgrading pip..."
"${ENV_DIR}/bin/python" -m pip install --upgrade pip

echo "[3/4] Installing project requirements..."
"${ENV_DIR}/bin/pip" install -r requirements.txt

echo "[4/4] Verifying key imports inside the environment..."
"${ENV_DIR}/bin/python" - <<'PY'
import ipykernel
import mido
import numpy
import openai
import pdf2image
import PIL
import pptx
print("Verified imports: ipykernel, mido, numpy, openai, pdf2image, PIL, pptx")
PY

echo ""
echo "Environment ready."
echo "Activate it with:"
echo "  source ${ENV_DIR}/bin/activate"
echo ""
echo "VS Code or Jupyter should detect the interpreter from the virtual environment once it is activated."
