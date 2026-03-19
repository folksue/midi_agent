# Visual Demo

This folder contains the static visual demo intended for GitHub Pages.

What it is for:

- publish a browser-friendly visual snapshot of the benchmark outputs
- show oracle-demo metrics, run comparisons, and sample cases
- document how to run the real benchmark locally

What it does not do:

- it does not execute Python on GitHub Pages
- it does not replace the local `benchmark_web.py` app

To refresh the static assets locally:

```bash
bash scripts/run_visual_demo_workflow.sh 8 agent_like yes
python3 scripts/build_visual_demo_site.py
```

The generated JSON files live in:

- `visual-demo/assets/`

The local executable app remains:

- `benchmark_web.py`

The local one-command workflow remains:

- `bash scripts/run_visual_demo_workflow.sh 8 agent_like yes`

To open the static dashboard in a browser, serve it over HTTP instead of opening `index.html` directly:

```bash
bash scripts/run_visual_demo_server.sh
```

Then open:

```text
http://127.0.0.1:8899
```
