# Presentation Workspace

This folder contains an editable slide deck for the benchmark and paper proposal.

## What is here

- `paper-proposal-deck.js`: source file that generates the presentation
- `paper-proposal-deck.pptx`: editable PowerPoint output
- `presentation-outline.md`: slide-by-slide outline for collaborative editing

## Why PowerPoint first

The recommended collaboration path is:

1. build the `.pptx` locally
2. upload it to Google Drive
3. open it with Google Slides for shared editing

This keeps the source deck versionable in the repository while still allowing collaborative work in Google Slides.

## Build

```bash
npm --prefix docs/presentation run build
```

## Render to PNG

```bash
bash scripts/render_presentation.sh
```

This renders the `.pptx` to slide PNGs in `docs/presentation/rendered/` and also creates a montage image when the required tools are available.

## Validate the deck

```bash
bash scripts/validate_presentation.sh
```

This runs:

- overflow detection on the `.pptx`
- font inspection with JSON output saved next to the rendered assets

## Export diagrams to PNG

```bash
bash scripts/export_diagrams.sh
```

The repository now supports Mermaid export through the local `docs/presentation/node_modules/.bin/mmdc` installation, and PlantUML export through the installed CLI.

## Import into Google Slides

1. Upload `docs/presentation/paper-proposal-deck.pptx` to Google Drive.
2. Open the uploaded file with Google Slides.
3. Save a Slides-native copy if you want shared online editing.

## Related source diagrams

The deck is aligned with the versioned diagram sources in:

- `docs/diagrams/benchmark-usage-flow.mmd`
- `docs/diagrams/benchmark-architecture.mmd`
- `docs/diagrams/benchmark-sequence-diagram.mmd`
- `docs/diagrams/benchmark-use-cases.mmd`
- `docs/diagrams/benchmark-components.mmd`

## Validation note

The deck source is generated programmatically, and the repository now supports local raster-based validation through LibreOffice, Poppler, and the Python rendering dependencies installed into `asmcm-env`.
