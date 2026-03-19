# Publication

This folder contains the paper-oriented material for the project, centered on a draft package based on the official ISMIR 2026 LaTeX template.

Included files:

- `symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology.tex`: prefilled draft focused on the symbolic benchmark project
- `references.bib`: starter bibliography for the current draft
- `ismir.sty`, `IEEEtran.bst`, `cite.sty`: official template files
- `figures/`: local copies of benchmark diagrams used in the draft
- `reviewer-checklist.md`: review-facing checklist based on the criteria currently guiding the paper
- `ASMCM-scientific-paper-template.docx`: Word template aligned with the same paper direction
- `scripts/generate_asmcm_scientific_paper_template.py`: generator for the paper template DOCX

## Compile locally

With `tectonic`:

```bash
cd publication
./build.sh
```

This compiles the local draft and copies a title-named PDF to the repository root.

If you prefer a traditional LaTeX flow:

```bash
cd publication
pdflatex symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology.tex
bibtex symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology
pdflatex symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology.tex
pdflatex symbolicMusicBenchmarkForMusicTheoryReasoningAndComputationalMusicology.tex
```

## Notes

- The draft currently uses anonymized author metadata for a submission-style version.
- The related-work section is intentionally compact and should be expanded before submission.
- The results section is framed as preliminary validation plus expected outcomes, not as a final empirical paper.
- The current draft compiles to 3 pages total, which stays below the temporary 4-page target for this version.

## Current reference set

The current bibliography is intentionally small and focused:

- `peeters2025mir`
  - motivates MIR benchmarking culture and evaluation practice
- `huang2020pop`
  - covers event-based symbolic representation through Pop Music Transformer / REMI-style modeling
- `huang2021musicbert`
  - covers pretrained symbolic music understanding
- `liang2023holistic`
  - supports the benchmark-design and multi-metric evaluation framing

Before a real submission, add more references on symbolic music reasoning, theory-aware evaluation, and computational musicology where appropriate.
