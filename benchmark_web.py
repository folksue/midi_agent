#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parent
PYTHON_BIN = sys.executable

BENCHMARK_DIR = REPO_ROOT / "benchmark"
DATA_DIR = BENCHMARK_DIR / "data"
RESULTS_DIR = BENCHMARK_DIR / "results"
WEBUI_DIR = RESULTS_DIR / "webui"
TOKENIZERS = ("note_level", "midilike", "remilike")
PROMPT_MODES = ("light", "agent_like")


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Symbolic Music Benchmark UI</title>
  <style>
    :root {
      --bg: #f6f9fb;
      --panel: #ffffff;
      --ink: #1f2a37;
      --muted: #5b6877;
      --accent: #0f766e;
      --accent-soft: #dff3f1;
      --line: #d6e3ea;
      --warn: #9a3412;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Aptos", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 30%),
        linear-gradient(180deg, #f9fcfd 0%, var(--bg) 100%);
    }
    .wrap {
      width: min(1200px, calc(100vw - 32px));
      margin: 24px auto 40px;
    }
    .hero, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }
    .hero {
      padding: 28px;
      margin-bottom: 18px;
    }
    .hero h1 {
      margin: 0 0 10px;
      font-size: 2rem;
      line-height: 1.1;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      max-width: 760px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }
    .panel {
      padding: 20px;
    }
    .panel h2 {
      margin: 0 0 10px;
      font-size: 1.1rem;
    }
    .muted {
      color: var(--muted);
      font-size: 0.95rem;
    }
    .small {
      font-size: 0.88rem;
      color: var(--muted);
    }
    .pill {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.82rem;
      margin-bottom: 10px;
    }
    label {
      display: block;
      font-weight: 600;
      margin: 12px 0 6px;
    }
    input, select, textarea, button {
      width: 100%;
      font: inherit;
    }
    input, select, textarea {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: #fff;
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    button {
      margin-top: 14px;
      border: 0;
      border-radius: 12px;
      background: var(--accent);
      color: white;
      padding: 11px 14px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary {
      background: #334155;
    }
    button.ghost {
      background: #eef6f5;
      color: var(--accent);
      border: 1px solid #c8e3df;
    }
    .outputs {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: #fbfdff;
    }
    .card strong {
      display: block;
      font-size: 1.2rem;
      margin-top: 6px;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #dbeafe;
      padding: 16px;
      border-radius: 14px;
      min-height: 180px;
      overflow: auto;
      border: 1px solid #1e293b;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.93rem;
    }
    th, td {
      padding: 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 0.84rem; text-transform: uppercase; letter-spacing: 0.03em; }
    .section-title {
      margin: 20px 0 10px;
      font-size: 1rem;
    }
    .path {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.82rem;
      color: #155e75;
      word-break: break-all;
    }
    .status-ok { color: #166534; }
    .status-missing { color: var(--warn); }
    @media (max-width: 760px) {
      .row { grid-template-columns: 1fr; }
      .wrap { width: min(100vw - 18px, 1200px); }
      .hero, .panel { border-radius: 16px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="pill">Local benchmark UI</div>
      <h1>Symbolic Music Benchmark Playground</h1>
      <p>
        This small web app lets you generate the benchmark, run an oracle demo without an external model,
        evaluate your own prediction files, and inspect the main output artifacts.
      </p>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>1. Generate Benchmark</h2>
        <p class="muted">This runs the standard data-preparation flow: generate raw data, export tokenizer views, validate them, and build model-ready cases.</p>
        <div class="row">
          <div>
            <label for="samples">Samples per task</label>
            <input id="samples" type="number" min="1" value="8">
          </div>
          <div>
            <label for="promptMode">Prompt mode</label>
            <select id="promptMode">
              <option value="agent_like">agent_like</option>
              <option value="light">light</option>
            </select>
          </div>
        </div>
        <button id="generateBtn">Generate benchmark data</button>
        <p class="small">Tip: start with 8 or 16 samples per task for a fast demo run.</p>
      </section>

      <section class="panel">
        <h2>2. Run Oracle Demo</h2>
        <p class="muted">This creates perfect reference predictions from the benchmark ground truth, then evaluates and annotates them so you can inspect the full pipeline without API keys.</p>
        <div class="row">
          <div>
            <label for="oracleTokenizer">Tokenizer</label>
            <select id="oracleTokenizer">
              <option value="note_level">note_level</option>
              <option value="midilike">midilike</option>
              <option value="remilike">remilike</option>
            </select>
          </div>
          <div>
            <label for="oracleExplain">Explanation layer</label>
            <select id="oracleExplain">
              <option value="yes">Include target explanations</option>
              <option value="no">No explanations</option>
            </select>
          </div>
        </div>
        <button id="oracleBtn">Run oracle demo</button>
      </section>

      <section class="panel">
        <h2>3. Evaluate Your Prediction File</h2>
        <p class="muted">Paste a relative path inside the repo, for example <code>benchmark/results/api/pred_gpt-4o-mini.jsonl</code>.</p>
        <label for="predPath">Prediction file path</label>
        <input id="predPath" type="text" placeholder="benchmark/results/api/pred_model.jsonl">
        <div class="row">
          <div>
            <label for="customTokenizer">Tokenizer</label>
            <select id="customTokenizer">
              <option value="note_level">note_level</option>
              <option value="midilike">midilike</option>
              <option value="remilike">remilike</option>
            </select>
          </div>
          <div>
            <label for="customModel">Run label</label>
            <input id="customModel" type="text" placeholder="gpt-4o-mini or custom">
          </div>
        </div>
        <button id="evaluateBtn" class="secondary">Evaluate prediction file</button>
      </section>

      <section class="panel">
        <h2>4. Run Full Local Demo</h2>
        <p class="muted">This executes the full local benchmark workflow: generate data, run oracle predictions for all tokenizers, and refresh the visual demo assets with comparison-ready charts.</p>
        <label for="fullExplain">Explanation layer in oracle runs</label>
        <select id="fullExplain">
          <option value="yes">Include target explanations</option>
          <option value="no">No explanations</option>
        </select>
        <button id="fullDemoBtn">Run full local demo</button>
        <p class="small">This is the fastest way to refresh the local dashboard and the static <code>visual-demo/</code> site together.</p>
      </section>
    </div>

    <section class="panel" style="margin-bottom: 18px;">
      <div class="row">
        <div>
          <h2>Benchmark Outputs</h2>
          <p class="muted">These are the main outputs the repo produces and that this UI helps you inspect.</p>
          <div class="outputs" id="outputCards"></div>
        </div>
        <div>
          <h2>Quick Commands</h2>
          <p class="muted">If you prefer the terminal, these are the most useful direct entry points.</p>
          <pre id="quickCommands"></pre>
        </div>
      </div>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>Current Data Status</h2>
        <div id="statusSummary" class="muted">Loading status…</div>
        <div class="section-title">Sample cases</div>
        <div id="sampleCases">No cases loaded yet.</div>
      </section>

      <section class="panel">
        <h2>Latest Results</h2>
        <div class="small">Oracle run</div>
        <div id="oracleResults" class="muted">No oracle results yet.</div>
        <div class="section-title">Custom evaluation</div>
        <div id="customResults" class="muted">No custom evaluation yet.</div>
      </section>
    </div>

    <section class="panel" style="margin-top: 18px;">
      <h2>Logs</h2>
      <pre id="logs">Ready.</pre>
      <button id="refreshBtn" class="ghost">Refresh status</button>
    </section>
  </div>

  <script>
    const logs = document.getElementById('logs');
    const outputCards = document.getElementById('outputCards');
    const quickCommands = document.getElementById('quickCommands');
    const statusSummary = document.getElementById('statusSummary');
    const sampleCases = document.getElementById('sampleCases');
    const oracleResults = document.getElementById('oracleResults');
    const customResults = document.getElementById('customResults');

    function setLogs(text) {
      logs.textContent = text || 'Done.';
    }

    function appendLogs(text) {
      logs.textContent = (logs.textContent || '') + '\\n' + text;
    }

    function fmtBool(v) {
      return v ? '<span class="status-ok">available</span>' : '<span class="status-missing">missing</span>';
    }

    function fmtNum(v) {
      return typeof v === 'number' ? v.toString() : '0';
    }

    function renderOutputCards(status) {
      const cards = [
        ['Raw benchmark rows', status.outputs.raw.count, status.outputs.raw.path],
        ['note_level view rows', status.outputs.views.note_level.count, status.outputs.views.note_level.path],
        ['midilike view rows', status.outputs.views.midilike.count, status.outputs.views.midilike.path],
        ['remilike view rows', status.outputs.views.remilike.count, status.outputs.views.remilike.path],
        ['note_level cases', status.outputs.cases.note_level.count, status.outputs.cases.note_level.path],
        ['Latest oracle accuracy', status.runs.oracle.latest_accuracy_text, status.runs.oracle.path || 'Run the oracle demo to populate this.'],
        ['Latest custom accuracy', status.runs.custom.latest_accuracy_text, status.runs.custom.path || 'Evaluate a prediction file to populate this.'],
      ];
      outputCards.innerHTML = cards.map(([label, value, path]) => `
        <div class="card">
          <div class="small">${label}</div>
          <strong>${value}</strong>
          <div class="path">${path}</div>
        </div>
      `).join('');
    }

    function renderQuickCommands(status) {
      quickCommands.textContent = [
        'Generate benchmark:',
        'python3 benchmark_web.py --smoke-test',
        '',
        'Serve the UI:',
        'python3 benchmark_web.py',
        '',
        'Manual benchmark flow:',
        'bash scripts/run_standard_benchmark.sh 8 agent_like none',
        '',
        'Oracle predictions:',
        'python3 -m benchmark.scripts.make_oracle_predictions --cases benchmark/data/model_io/note_level/all_cases.json --out benchmark/results/webui/oracle/note_level/predictions.jsonl --include-explanations',
        '',
        'Unified evaluation:',
        'python3 -m benchmark.scripts.eval_predictions --gold benchmark/data/views/note_level/zero_shot.jsonl --pred benchmark/results/webui/oracle/note_level/predictions.jsonl --out benchmark/results/webui/oracle/note_level/eval_predictions.json',
        '',
        'Refresh the visual demo:',
        'bash scripts/run_visual_demo_workflow.sh 8 agent_like yes'
      ].join('\\n');
    }

    function renderStatus(status) {
      const views = status.outputs.views;
      const cases = status.outputs.cases;
      statusSummary.innerHTML = `
        <p><strong>Raw benchmark</strong>: ${fmtBool(status.outputs.raw.exists)} · ${fmtNum(status.outputs.raw.count)} rows</p>
        <p><strong>Views</strong>: note_level ${fmtNum(views.note_level.count)}, midilike ${fmtNum(views.midilike.count)}, remilike ${fmtNum(views.remilike.count)}</p>
        <p><strong>Cases</strong>: note_level ${fmtNum(cases.note_level.count)}, midilike ${fmtNum(cases.midilike.count)}, remilike ${fmtNum(cases.remilike.count)}</p>
        <p><strong>Last updated</strong>: ${status.generated_at}</p>
      `;

      if (!status.sample_cases.length) {
        sampleCases.innerHTML = '<div class="muted">Generate the benchmark first to preview sample cases.</div>';
      } else {
        sampleCases.innerHTML = `
          <table>
            <thead>
              <tr><th>Case</th><th>Task</th><th>Input</th><th>Ground truth</th></tr>
            </thead>
            <tbody>
              ${status.sample_cases.map(row => `
                <tr>
                  <td>${row.case_id}</td>
                  <td>${row.task}</td>
                  <td>${row.input_preview}</td>
                  <td>${row.ground_truth}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }

      renderRunPanel(oracleResults, status.runs.oracle, 'No oracle results yet. Run the oracle demo after generating the benchmark.');
      renderRunPanel(customResults, status.runs.custom, 'No custom evaluation yet. Evaluate a prediction file after generating cases.');
      renderOutputCards(status);
      renderQuickCommands(status);
    }

    function renderRunPanel(node, run, emptyText) {
      if (!run.available) {
        node.innerHTML = `<div class="muted">${emptyText}</div>`;
        return;
      }
      const overall = run.overall || {};
      const byTask = run.by_task || {};
      const taskRows = Object.entries(byTask).map(([task, stats]) => `
        <tr>
          <td>${task}</td>
          <td>${(stats.accuracy ?? 0).toFixed(3)}</td>
          <td>${stats.n ?? stats.cases ?? '-'}</td>
        </tr>
      `).join('');
      node.innerHTML = `
        <p><strong>Tokenizer</strong>: ${run.tokenizer}</p>
        <p><strong>Accuracy</strong>: ${(overall.accuracy ?? 0).toFixed(3)} · <strong>Cases</strong>: ${overall.cases ?? 0}</p>
        <p class="path">${run.path}</p>
        <table>
          <thead>
            <tr><th>Task</th><th>Accuracy</th><th>N</th></tr>
          </thead>
          <tbody>${taskRows}</tbody>
        </table>
      `;
    }

    async function apiGet(url) {
      const response = await fetch(url);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `GET ${url} failed`);
      }
      return response.json();
    }

    async function apiPost(url, payload) {
      const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload || {}),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `POST ${url} failed`);
      }
      return response.json();
    }

    async function refreshStatus() {
      const status = await apiGet('/api/status');
      renderStatus(status);
    }

    async function withAction(name, fn) {
      setLogs(`${name}...`);
      try {
        const data = await fn();
        setLogs(data.log || `${name} completed.`);
        await refreshStatus();
      } catch (error) {
        setLogs(`${name} failed.\\n\\n${error.message}`);
      }
    }

    document.getElementById('generateBtn').addEventListener('click', () => withAction('Benchmark generation', async () => {
      const samplesPerTask = parseInt(document.getElementById('samples').value || '8', 10);
      const promptMode = document.getElementById('promptMode').value;
      return apiPost('/api/generate', {samples_per_task: samplesPerTask, prompt_mode: promptMode});
    }));

    document.getElementById('oracleBtn').addEventListener('click', () => withAction('Oracle demo', async () => {
      const tokenizer = document.getElementById('oracleTokenizer').value;
      const includeExplanations = document.getElementById('oracleExplain').value === 'yes';
      return apiPost('/api/oracle', {tokenizer, include_explanations: includeExplanations});
    }));

    document.getElementById('evaluateBtn').addEventListener('click', () => withAction('Custom evaluation', async () => {
      const tokenizer = document.getElementById('customTokenizer').value;
      const predictionsPath = document.getElementById('predPath').value.trim();
      const modelName = document.getElementById('customModel').value.trim();
      return apiPost('/api/evaluate', {tokenizer, predictions_path: predictionsPath, model_name: modelName});
    }));

    document.getElementById('fullDemoBtn').addEventListener('click', () => withAction('Full local demo', async () => {
      const samplesPerTask = parseInt(document.getElementById('samples').value || '8', 10);
      const promptMode = document.getElementById('promptMode').value;
      const includeExplanations = document.getElementById('fullExplain').value === 'yes';
      return apiPost('/api/full-demo', {samples_per_task: samplesPerTask, prompt_mode: promptMode, include_explanations: includeExplanations});
    }));

    document.getElementById('refreshBtn').addEventListener('click', () => withAction('Status refresh', async () => {
      const status = await apiGet('/api/status');
      renderStatus(status);
      return {log: 'Status refreshed.'};
    }));

    refreshStatus().catch(error => setLogs(`Failed to load status.\\n\\n${error.message}`));
  </script>
</body>
</html>
"""


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _html_response(handler: BaseHTTPRequestHandler, payload: str, status: int = 200) -> None:
    data = payload.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _error_response(handler: BaseHTTPRequestHandler, message: str, status: int = 400) -> None:
    _json_response(handler, {"error": message}, status=status)


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _count_json_array(path: Path) -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data) if isinstance(data, list) else 0


def _mtime_text(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def _run_subprocess(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )
    combined = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
    return proc.returncode, combined.strip()


def _run_step(title: str, args: list[str]) -> str:
    code, output = _run_subprocess(args)
    block = [f"[{title}]", " ".join(args)]
    if output:
      block.append(output)
    if code != 0:
      raise RuntimeError("\n".join(block))
    return "\n".join(block)


def _raw_path() -> Path:
    return DATA_DIR / "raw_note_level" / "zero_shot.jsonl"


def _view_path(tokenizer: str) -> Path:
    return DATA_DIR / "views" / tokenizer / "zero_shot.jsonl"


def _cases_path(tokenizer: str) -> Path:
    return DATA_DIR / "model_io" / tokenizer / "all_cases.json"


def _oracle_run_dir(tokenizer: str) -> Path:
    return WEBUI_DIR / "oracle" / tokenizer


def _custom_run_dir(tokenizer: str) -> Path:
    return WEBUI_DIR / "custom" / tokenizer


def generate_benchmark(samples_per_task: int, prompt_mode: str) -> str:
    if prompt_mode not in PROMPT_MODES:
        raise ValueError(f"prompt_mode must be one of {PROMPT_MODES}")
    if samples_per_task <= 0:
        raise ValueError("samples_per_task must be positive")

    logs: list[str] = []
    raw_path = _raw_path()

    logs.append(
        _run_step(
            "Generate raw benchmark",
            [
                PYTHON_BIN,
                "-m",
                "benchmark.scripts.gen_zero_shot",
                "--task-group",
                "all",
                "--samples-per-task",
                str(samples_per_task),
                "--prompt-mode",
                prompt_mode,
                "--out",
                str(raw_path),
            ],
        )
    )
    logs.append(
        _run_step(
            "Export tokenizer views",
            [
                PYTHON_BIN,
                "-m",
                "benchmark.scripts.export_views",
                "--src",
                str(raw_path),
                "--prompt-mode",
                prompt_mode,
            ],
        )
    )
    logs.append(
        _run_step(
            "Validate views",
            [PYTHON_BIN, "-m", "benchmark.scripts.validate_views"],
        )
    )
    for tokenizer in TOKENIZERS:
        logs.append(
            _run_step(
                f"Build cases for {tokenizer}",
                [
                    PYTHON_BIN,
                    "-m",
                    "benchmark.scripts.build_model_io_json",
                    "--src",
                    str(_view_path(tokenizer)),
                    "--out",
                    str(_cases_path(tokenizer)),
                    "--task-group",
                    "all",
                    "--pretty",
                ],
            )
        )
    return "\n\n".join(logs)


def run_oracle_demo(tokenizer: str, include_explanations: bool) -> str:
    if tokenizer not in TOKENIZERS:
        raise ValueError(f"tokenizer must be one of {TOKENIZERS}")

    cases_path = _cases_path(tokenizer)
    gold_path = _view_path(tokenizer)
    if not cases_path.exists():
        raise FileNotFoundError(f"Missing cases file: {cases_path}")
    if not gold_path.exists():
        raise FileNotFoundError(f"Missing gold view file: {gold_path}")

    run_dir = _oracle_run_dir(tokenizer)
    run_dir.mkdir(parents=True, exist_ok=True)
    pred_path = run_dir / "predictions.jsonl"
    eval_path = run_dir / "eval_predictions.json"
    overall_path = run_dir / "overall.json"
    by_task_path = run_dir / "by_task.json"
    by_tokenizer_path = run_dir / "by_tokenizer.json"
    annotated_path = run_dir / "cases_with_outputs.json"
    summary_path = run_dir / "summary.json"

    logs: list[str] = []
    make_args = [
        PYTHON_BIN,
        "-m",
        "benchmark.scripts.make_oracle_predictions",
        "--cases",
        str(cases_path),
        "--out",
        str(pred_path),
    ]
    if include_explanations:
        make_args.append("--include-explanations")
    logs.append(_run_step("Create oracle predictions", make_args))
    logs.append(
        _run_step(
            "Evaluate oracle predictions",
            [
                PYTHON_BIN,
                "-m",
                "benchmark.scripts.eval_predictions",
                "--gold",
                str(gold_path),
                "--pred",
                str(pred_path),
                "--out",
                str(eval_path),
                "--overall-out",
                str(overall_path),
                "--by-task-out",
                str(by_task_path),
                "--by-tokenizer-out",
                str(by_tokenizer_path),
            ],
        )
    )
    logs.append(
        _run_step(
            "Annotate oracle outputs",
            [
                PYTHON_BIN,
                "-m",
                "benchmark.scripts.annotate_model_outputs",
                "--cases",
                str(cases_path),
                "--pred",
                str(pred_path),
                "--out",
                str(annotated_path),
                "--summary-out",
                str(summary_path),
                "--model-name",
                f"oracle-{tokenizer}",
                "--pretty",
            ],
        )
    )
    return "\n\n".join(logs)


def evaluate_predictions_file(tokenizer: str, predictions_path: str, model_name: str) -> str:
    if tokenizer not in TOKENIZERS:
        raise ValueError(f"tokenizer must be one of {TOKENIZERS}")
    if not predictions_path.strip():
        raise ValueError("predictions_path is required")

    pred_path = Path(predictions_path)
    if not pred_path.is_absolute():
        pred_path = (REPO_ROOT / pred_path).resolve()
    if not pred_path.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_path}")

    cases_path = _cases_path(tokenizer)
    gold_path = _view_path(tokenizer)
    if not cases_path.exists() or not gold_path.exists():
        raise FileNotFoundError("Generate benchmark data before evaluating a prediction file.")

    run_dir = _custom_run_dir(tokenizer)
    run_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in (model_name or pred_path.stem)).strip("_")
    if not safe_name:
        safe_name = "custom"
    eval_path = run_dir / f"eval_{safe_name}.json"
    overall_path = run_dir / f"overall_{safe_name}.json"
    by_task_path = run_dir / f"by_task_{safe_name}.json"
    by_tokenizer_path = run_dir / f"by_tokenizer_{safe_name}.json"
    annotated_path = run_dir / f"cases_with_outputs_{safe_name}.json"
    summary_path = run_dir / f"summary_{safe_name}.json"
    latest_meta = run_dir / "latest.json"

    logs: list[str] = []
    logs.append(
        _run_step(
            "Evaluate predictions",
            [
                PYTHON_BIN,
                "-m",
                "benchmark.scripts.eval_predictions",
                "--gold",
                str(gold_path),
                "--pred",
                str(pred_path),
                "--out",
                str(eval_path),
                "--overall-out",
                str(overall_path),
                "--by-task-out",
                str(by_task_path),
                "--by-tokenizer-out",
                str(by_tokenizer_path),
            ],
        )
    )
    annotate_args = [
        PYTHON_BIN,
        "-m",
        "benchmark.scripts.annotate_model_outputs",
        "--cases",
        str(cases_path),
        "--pred",
        str(pred_path),
        "--out",
        str(annotated_path),
        "--summary-out",
        str(summary_path),
        "--pretty",
    ]
    if model_name.strip():
        annotate_args.extend(["--model-name", model_name.strip()])
    logs.append(_run_step("Annotate evaluated predictions", annotate_args))

    latest_meta.write_text(
        json.dumps(
            {
                "pred_path": str(pred_path),
                "eval_path": str(eval_path),
                "overall_path": str(overall_path),
                "by_task_path": str(by_task_path),
                "by_tokenizer_path": str(by_tokenizer_path),
                "annotated_path": str(annotated_path),
                "summary_path": str(summary_path),
                "tokenizer": tokenizer,
                "model_name": model_name.strip() or pred_path.stem,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return "\n\n".join(logs)


def build_visual_demo_snapshot() -> str:
    return _run_step(
        "Build visual demo snapshot",
        [PYTHON_BIN, "scripts/build_visual_demo_site.py"],
    )


def run_full_local_demo(samples_per_task: int, prompt_mode: str, include_explanations: bool) -> str:
    logs = [generate_benchmark(samples_per_task=samples_per_task, prompt_mode=prompt_mode)]
    for tokenizer in TOKENIZERS:
        logs.append(run_oracle_demo(tokenizer=tokenizer, include_explanations=include_explanations))
    logs.append(build_visual_demo_snapshot())
    return "\n\n".join(logs)


def _trim_text(value: object, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _sample_cases(tokenizer: str = "note_level", limit: int = 5) -> list[dict]:
    path = _cases_path(tokenizer)
    if not path.exists():
        return []
    data = _read_json(path, [])
    if not isinstance(data, list):
        return []
    out = []
    for row in data[:limit]:
        out.append(
            {
                "case_id": str(row.get("case_id", "")),
                "task": str(row.get("task", "")),
                "input_preview": _trim_text(row.get("input_tokenized", row.get("input_label_context", ""))),
                "ground_truth": _trim_text(row.get("ground_truth", "")),
            }
        )
    return out


def _load_run_bundle(run_dir: Path, tokenizer: str, run_kind: str) -> dict:
    if run_kind == "oracle":
        overall_path = run_dir / "overall.json"
        by_task_path = run_dir / "by_task.json"
        path_label = run_dir / "eval_predictions.json"
        available = overall_path.exists()
    else:
        latest_meta = _read_json(run_dir / "latest.json", {})
        if not isinstance(latest_meta, dict) or not latest_meta:
            return {
                "available": False,
                "tokenizer": tokenizer,
                "path": "",
                "latest_accuracy_text": "not run",
            }
        overall_path = Path(str(latest_meta.get("overall_path", "")))
        by_task_path = Path(str(latest_meta.get("by_task_path", "")))
        path_label = Path(str(latest_meta.get("eval_path", "")))
        available = overall_path.exists()

    overall = _read_json(overall_path, {}) if available else {}
    by_task = _read_json(by_task_path, {}) if available else {}
    accuracy = overall.get("accuracy")
    return {
        "available": bool(available),
        "tokenizer": tokenizer,
        "path": str(path_label) if available else "",
        "overall": overall if isinstance(overall, dict) else {},
        "by_task": by_task if isinstance(by_task, dict) else {},
        "latest_accuracy_text": f"{accuracy:.3f}" if isinstance(accuracy, (int, float)) else "not run",
        "updated_at": _mtime_text(path_label) if available else "",
    }


def get_status_payload() -> dict:
    raw_path = _raw_path()
    views = {tokenizer: _view_path(tokenizer) for tokenizer in TOKENIZERS}
    cases = {tokenizer: _cases_path(tokenizer) for tokenizer in TOKENIZERS}

    oracle_latest = None
    for tokenizer in TOKENIZERS:
        run_dir = _oracle_run_dir(tokenizer)
        if (run_dir / "overall.json").exists():
            current = _load_run_bundle(run_dir, tokenizer, "oracle")
            if oracle_latest is None or current["updated_at"] > oracle_latest["updated_at"]:
                oracle_latest = current
    custom_latest = None
    for tokenizer in TOKENIZERS:
        run_dir = _custom_run_dir(tokenizer)
        current = _load_run_bundle(run_dir, tokenizer, "custom")
        if current["available"] and (custom_latest is None or current["updated_at"] > custom_latest["updated_at"]):
            custom_latest = current

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "outputs": {
            "raw": {
                "exists": raw_path.exists(),
                "count": _count_jsonl_rows(raw_path),
                "path": str(raw_path),
            },
            "views": {
                tokenizer: {
                    "exists": path.exists(),
                    "count": _count_jsonl_rows(path),
                    "path": str(path),
                }
                for tokenizer, path in views.items()
            },
            "cases": {
                tokenizer: {
                    "exists": path.exists(),
                    "count": _count_json_array(path),
                    "path": str(path),
                }
                for tokenizer, path in cases.items()
            },
        },
        "sample_cases": _sample_cases("note_level", limit=5),
        "runs": {
            "oracle": oracle_latest
            or {"available": False, "tokenizer": "note_level", "path": "", "latest_accuracy_text": "not run"},
            "custom": custom_latest
            or {"available": False, "tokenizer": "note_level", "path": "", "latest_accuracy_text": "not run"},
        },
    }


class BenchmarkWebHandler(BaseHTTPRequestHandler):
    server_version = "BenchmarkWeb/1.0"

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            _html_response(self, INDEX_HTML)
            return
        if parsed.path == "/api/status":
            _json_response(self, get_status_payload())
            return
        _error_response(self, f"Unknown route: {html.escape(parsed.path)}", status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            _error_response(self, "Request body must be valid JSON.", status=400)
            return

        try:
            if parsed.path == "/api/generate":
                log = generate_benchmark(
                    samples_per_task=int(payload.get("samples_per_task", 8)),
                    prompt_mode=str(payload.get("prompt_mode", "agent_like")),
                )
                _json_response(self, {"ok": True, "log": log, "status": get_status_payload()})
                return

            if parsed.path == "/api/oracle":
                tokenizer = str(payload.get("tokenizer", "note_level"))
                include_explanations = bool(payload.get("include_explanations", True))
                log = run_oracle_demo(tokenizer=tokenizer, include_explanations=include_explanations)
                _json_response(self, {"ok": True, "log": log, "status": get_status_payload()})
                return

            if parsed.path == "/api/evaluate":
                tokenizer = str(payload.get("tokenizer", "note_level"))
                predictions_path = str(payload.get("predictions_path", "")).strip()
                model_name = str(payload.get("model_name", "")).strip()
                log = evaluate_predictions_file(
                    tokenizer=tokenizer,
                    predictions_path=predictions_path,
                    model_name=model_name,
                )
                _json_response(self, {"ok": True, "log": log, "status": get_status_payload()})
                return

            if parsed.path == "/api/full-demo":
                log = run_full_local_demo(
                    samples_per_task=int(payload.get("samples_per_task", 8)),
                    prompt_mode=str(payload.get("prompt_mode", "agent_like")),
                    include_explanations=bool(payload.get("include_explanations", True)),
                )
                _json_response(self, {"ok": True, "log": log, "status": get_status_payload()})
                return

            _error_response(self, f"Unknown route: {html.escape(parsed.path)}", status=404)
        except Exception as exc:
            _error_response(self, str(exc), status=500)


def run_smoke_test() -> int:
    print("Running benchmark web smoke test...")
    print(run_full_local_demo(samples_per_task=2, prompt_mode="agent_like", include_explanations=True))
    status = get_status_payload()
    print(json.dumps(status["runs"]["oracle"], ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a small local web UI for the symbolic benchmark.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--smoke-test", action="store_true", help="Run a small generation + oracle-eval smoke test and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.smoke_test:
        return run_smoke_test()

    WEBUI_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), BenchmarkWebHandler)
    print(f"Benchmark UI running at http://{args.host}:{args.port}")
    print(f"Repo root: {REPO_ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
