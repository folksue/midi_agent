# Diagrams

This folder contains Mermaid and PlantUML diagrams for understanding the benchmark and supporting paper or presentation work.

- `benchmark-usage-flow.md`: end-to-end user workflow
- `benchmark-architecture.md`: internal architecture and data flow
- `benchmark-sequence-diagram.md`: end-to-end runtime sequence from generation to reporting
- `benchmark-use-cases.md`: user-facing benchmark use cases
- `benchmark-components.md`: component-level benchmark organization
- `benchmark-usage-flow.mmd`: raw Mermaid source
- `benchmark-architecture.mmd`: raw Mermaid source
- `benchmark-sequence-diagram.mmd`: raw Mermaid source
- `benchmark-use-cases.mmd`: raw Mermaid source
- `benchmark-components.mmd`: raw Mermaid source
- `benchmark-usage-flow.puml`: PlantUML source
- `benchmark-architecture.puml`: PlantUML source
- `benchmark-sequence-diagram.puml`: PlantUML source
- `benchmark-use-cases.puml`: PlantUML source
- `benchmark-components.puml`: PlantUML source

## Viewing in Visual Studio Code

### Mermaid

If a Mermaid extension did not open the diagram directly, use one of these workflows:

1. Open the `.md` file that contains the Mermaid block.
2. Use `Markdown: Open Preview to the Side` in VS Code.
3. If Mermaid still does not render, install an extension that supports Mermaid in Markdown preview, such as `Markdown Preview Mermaid Support`.

If you prefer raw Mermaid files:

- open the `.mmd` file
- use a Mermaid preview extension that supports `.mmd`

### PlantUML

For PlantUML in VS Code:

1. Install the `PlantUML` extension.
2. Open the `.puml` file.
3. Run the PlantUML preview command from the command palette.

## Exporting PNG

### Mermaid

If Mermaid CLI is installed:

```bash
bash scripts/export_diagrams.sh
```

### PlantUML

If PlantUML CLI is installed:

```bash
bash scripts/export_diagrams.sh
```

### Convenience script

A helper script is available:

```bash
bash scripts/export_diagrams.sh
```

It exports all Mermaid and PlantUML diagrams in this folder to PNG when the required tools are available in `PATH`.
