# Supporting Documents

This folder groups the auxiliary material created around the benchmark and paper workflow.

## Structure

- `presentation/`: editable slide deck source, generated `.pptx`, and rendering utilities
- `diagrams/`: Mermaid and PlantUML sources plus exported PNGs
- `docx/`: Word exports and document templates
- `pdf/`: exported PDF notes and presentation-support files
- `notes/`: Markdown speaker notes and related narrative material
- `scripts/`: helper scripts that generate the supporting artifacts

Paper-specific source files now live in the repository-level `publication/` folder.

## Recommended entry points

- Build the presentation:
  - `npm --prefix supporting-docs/presentation run build`
- Render presentation previews:
  - `bash scripts/render_presentation.sh`
- Export diagrams:
  - `bash scripts/export_diagrams.sh`
- Compile the paper:
  - `cd publication && ./build.sh`

The paper build also copies a title-named PDF to the repository root so it is easy to find and share.
