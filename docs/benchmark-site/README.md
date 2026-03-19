# Benchmark Pages

This folder contains a static dashboard intended for GitHub Pages.

What it is for:

- publish a browser-friendly snapshot of the benchmark outputs
- show oracle-demo metrics and sample cases
- document how to run the real benchmark locally

What it does not do:

- it does not execute Python on GitHub Pages
- it does not replace the local `benchmark_web.py` app

To refresh the static assets locally:

```bash
python3 benchmark_web.py --smoke-test
python3 scripts/build_benchmark_pages_site.py
```

The generated JSON files live in:

- `docs/benchmark-site/assets/`

The local executable app remains:

- `benchmark_web.py`
