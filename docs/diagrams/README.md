# Diagrams

This folder contains Mermaid diagrams for understanding the benchmark.

- `benchmark-usage-flow.md`: end-to-end user workflow
- `benchmark-architecture.md`: internal architecture and data flow
- `benchmark-usage-flow.mmd`: raw Mermaid source
- `benchmark-architecture.mmd`: raw Mermaid source
- `benchmark-usage-flow.puml`: PlantUML source
- `benchmark-architecture.puml`: PlantUML source

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
mmdc -i docs/diagrams/benchmark-usage-flow.mmd -o docs/diagrams/png/benchmark-usage-flow-mermaid.png
mmdc -i docs/diagrams/benchmark-architecture.mmd -o docs/diagrams/png/benchmark-architecture-mermaid.png
```

### PlantUML

If PlantUML CLI is installed:

```bash
plantuml -tpng docs/diagrams/benchmark-usage-flow.puml docs/diagrams/benchmark-architecture.puml
```

### Convenience script

A helper script is available:

```bash
bash scripts/export_diagrams.sh
```

It exports Mermaid and PlantUML diagrams to PNG when the required tools are available in `PATH`.
