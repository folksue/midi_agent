# Presentation Workspace

This folder contains an editable slide deck for the benchmark and paper proposal.

## What is here

- `paper-proposal-deck.js`: source file that generates the presentation
- `paper-proposal-deck.pptx`: PowerPoint-compatible editable output after LibreOffice normalization
- `presentation-outline.md`: slide-by-slide outline for collaborative editing

## Why PowerPoint first

The recommended collaboration path is:

1. build the `.pptx` locally
2. upload it to Google Drive
3. open it with Google Slides for shared editing

This keeps the source deck versionable in the repository while still allowing collaborative work in Google Slides.

## Build

```bash
npm --prefix supporting-docs/presentation run build
```

This build now does two steps:

1. generate a raw `.pptx` from PptxGenJS
2. normalize it through LibreOffice into `paper-proposal-deck.pptx`

The raw and round-trip intermediate files are build artifacts and are not meant to be shared. Upload or share the normalized `paper-proposal-deck.pptx`.

## Render to PNG

```bash
bash scripts/render_presentation.sh
```

This renders the `.pptx` to slide PNGs in `supporting-docs/presentation/rendered/` and also creates a montage image when the required tools are available.

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

The repository now supports Mermaid export through the local `supporting-docs/presentation/node_modules/.bin/mmdc` installation, and PlantUML export through the installed CLI.

## Import into Google Slides

1. Upload `supporting-docs/presentation/paper-proposal-deck.pptx` to Google Drive.
2. Open the uploaded file with Google Slides.
3. Save a Slides-native copy if you want shared online editing.

## Related source diagrams

The deck is aligned with the versioned diagram sources in:

- `supporting-docs/diagrams/benchmark-usage-flow.mmd`
- `supporting-docs/diagrams/benchmark-architecture.mmd`
- `supporting-docs/diagrams/benchmark-sequence-diagram.mmd`
- `supporting-docs/diagrams/benchmark-use-cases.mmd`
- `supporting-docs/diagrams/benchmark-components.mmd`

## Validation note

The deck source is generated programmatically, and the repository now supports local raster-based validation through LibreOffice, Poppler, and the Python rendering dependencies installed into `asmcm-env`.
