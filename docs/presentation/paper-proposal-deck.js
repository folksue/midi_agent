const path = require("path");
const pptxgen = require("pptxgenjs");
const { warnIfSlideHasOverlaps, warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "ASMCM";
pptx.company = "UPF";
pptx.subject = "Symbolic music benchmark paper proposal";
pptx.title = "Symbolic Music Benchmark for Music Theory and Computational Musicology";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Georgia",
  bodyFontFace: "Verdana",
  lang: "en-US",
};

const COLORS = {
  navy: "123B66",
  teal: "1E7C86",
  gold: "C18A2D",
  green: "2A8E5E",
  rose: "B5535C",
  ink: "1F2A37",
  muted: "5C6775",
  bg: "F6F7FB",
  panel: "FFFFFF",
  line: "D7DEE8",
  paleTeal: "E9F5F6",
  paleGold: "FAF3E6",
  paleRose: "F9ECEE",
};
const EPS = 0.001;

function addBase(slide, section, title, subtitle = "") {
  slide.background = { color: COLORS.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.32,
    line: { color: COLORS.navy, transparency: 100 },
    fill: { color: COLORS.navy },
  });
  slide.addText(section.toUpperCase(), {
    x: 0.6,
    y: 0.48,
    w: 2.5,
    h: 0.2,
    fontFace: "Verdana",
    fontSize: 11,
    bold: true,
    color: COLORS.teal,
    tracking: 1,
  });
  slide.addText(title, {
    x: 0.6,
    y: 0.78,
    w: 9.8,
    h: 0.5,
    fontFace: "Georgia",
    fontSize: 24,
    bold: true,
    color: COLORS.ink,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6,
      y: 1.28,
      w: 10.9,
      h: 0.45,
      fontFace: "Verdana",
      fontSize: 11,
      color: COLORS.muted,
    });
  }
  slide.addShape(pptx.ShapeType.line, {
    x: 0.6,
    y: 1.82,
    w: 12.1,
    h: EPS,
    line: { color: COLORS.line, pt: 1.25 },
  });
}

function addFooter(slide, label) {
  slide.addText(label, {
    x: 0.6,
    y: 7.08,
    w: 6,
    h: 0.2,
    fontFace: "Verdana",
    fontSize: 8,
    color: COLORS.muted,
  });
}

function addBulletList(slide, items, x, y, w, opts = {}) {
  const fontSize = opts.fontSize || 13;
  const color = opts.color || COLORS.ink;
  const gap = opts.gap || 0.38;
  items.forEach((item, index) => {
    slide.addText(item, {
      x,
      y: y + index * gap,
      w,
      h: gap,
      fontFace: "Verdana",
      fontSize,
      color,
      breakLine: false,
      bullet: { indent: 14 },
      margin: 0,
    });
  });
}

function addCard(slide, x, y, w, h, title, body, fill, accent = COLORS.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: COLORS.line, pt: 1 },
    fill: { color: fill },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w: 0.12,
    h,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.22,
    y: y + 0.16,
    w: w - 0.34,
    h: 0.28,
    fontFace: "Georgia",
    fontSize: 15,
    bold: true,
    color: COLORS.ink,
  });
  slide.addText(body, {
    x: x + 0.22,
    y: y + 0.52,
    w: w - 0.34,
    h: h - 0.64,
    fontFace: "Verdana",
    fontSize: 10.5,
    color: COLORS.muted,
    valign: "top",
  });
}

function addFlowBox(slide, x, y, w, h, title, subtitle, fill = COLORS.panel) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: COLORS.line, pt: 1.1 },
    fill: { color: fill },
  });
  slide.addText(title, {
    x: x + 0.16,
    y: y + 0.18,
    w: w - 0.32,
    h: 0.25,
    fontFace: "Georgia",
    fontSize: 14,
    bold: true,
    color: COLORS.ink,
    align: "center",
  });
  slide.addText(subtitle, {
    x: x + 0.16,
    y: y + 0.52,
    w: w - 0.32,
    h: h - 0.64,
    fontFace: "Verdana",
    fontSize: 9.5,
    color: COLORS.muted,
    align: "center",
    valign: "mid",
  });
}

function addArrow(slide, x1, y1, x2, y2, color = COLORS.teal) {
  const w = Math.abs(x2 - x1) < EPS ? (x2 >= x1 ? EPS : -EPS) : (x2 - x1);
  const h = Math.abs(y2 - y1) < EPS ? (y2 >= y1 ? EPS : -EPS) : (y2 - y1);
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w,
    h,
    line: { color, pt: 1.6, endArrowType: "triangle" },
  });
}

function finalize(slide, footer) {
  addFooter(slide, footer);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

{
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 7.5,
    line: { color: COLORS.bg, transparency: 100 },
    fill: { color: COLORS.bg },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.72,
    y: 0.9,
    w: 0.18,
    h: 5.2,
    line: { color: COLORS.teal, transparency: 100 },
    fill: { color: COLORS.teal },
  });
  slide.addText("Symbolic Music Benchmark", {
    x: 1.1,
    y: 1.05,
    w: 7.2,
    h: 0.5,
    fontFace: "Verdana",
    fontSize: 14,
    bold: true,
    color: COLORS.teal,
    tracking: 1,
  });
  slide.addText("Music Theory and\nComputational Musicology", {
    x: 1.08,
    y: 1.55,
    w: 6.9,
    h: 1.5,
    fontFace: "Georgia",
    fontSize: 24,
    bold: true,
    color: COLORS.ink,
    breakLine: true,
  });
  slide.addText(
    "A benchmark with classification and transformation tasks, automatic formal evaluation, and an optional analytical explanation layer.",
    {
      x: 1.08,
      y: 3.35,
      w: 5.7,
      h: 1.1,
      fontFace: "Verdana",
      fontSize: 12,
      color: COLORS.muted,
      valign: "top",
    }
  );
  addCard(
    slide,
    8.45,
    1.2,
    3.95,
    1.55,
    "Standard benchmark mode",
    "Mandatory and easy to test. Outputs are prediction_label or prediction_notes, with clean automatic evaluation for non-expert users.",
    COLORS.panel,
    COLORS.teal
  );
  addCard(
    slide,
    8.45,
    3.0,
    3.95,
    1.55,
    "Explanatory mode",
    "Optional and paper-oriented. prediction_explanation is preserved for qualitative analysis without destabilizing the main benchmark.",
    COLORS.panel,
    COLORS.gold
  );
  addCard(
    slide,
    8.45,
    4.8,
    3.95,
    1.35,
    "Presentation use",
    "Editable .pptx deck designed to be imported into Google Slides for collaboration.",
    COLORS.panel,
    COLORS.rose
  );
  finalize(slide, "midi_agent | paper proposal deck");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Motivation",
    "Why a symbolic music-theory benchmark",
    "The project needs to be useful as software, but also legible as a scientific contribution."
  );
  addCard(
    slide,
    0.7,
    2.15,
    5.8,
    3.85,
    "Why symbolic benchmarking",
    "",
    COLORS.panel,
    COLORS.teal
  );
  addBulletList(
    slide,
    [
      "It operationalizes musical relationships that can be verified with rule-based logic.",
      "It avoids the ambiguity of audio-only evaluation in a first benchmark release.",
      "It lets us compare models on musically meaningful structure rather than surface text alone.",
      "It creates a reproducible benchmark that non-expert users can run end to end.",
    ],
    1.0,
    2.75,
    5.1,
    { fontSize: 11.5, gap: 0.62 }
  );
  addCard(
    slide,
    6.8,
    2.15,
    5.85,
    1.65,
    "Scientific value",
    "The benchmark can support a paper on symbolic musical reasoning, music-theory operationalization, and the gap between structural correctness and analytical explanation.",
    COLORS.paleGold,
    COLORS.gold
  );
  addCard(
    slide,
    6.8,
    4.0,
    5.85,
    2.0,
    "Project design principle",
    "Keep the standard benchmark simple, testable, and automatically evaluable. Add interpretation as a second layer instead of forcing every run to produce discursive prose.",
    COLORS.paleRose,
    COLORS.rose
  );
  finalize(slide, "Motivation | benchmark + paper framing");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Tasks",
    "Task families and benchmark outputs",
    "The benchmark covers eight tasks split into label classification and symbolic sequence transformation."
  );
  addCard(
    slide,
    0.7,
    2.15,
    5.8,
    3.1,
    "Label classification",
    "",
    COLORS.paleTeal,
    COLORS.teal
  );
  addBulletList(
    slide,
    [
      "Task 1: Interval Identification",
      "Task 2: Chord Identification",
      "Task 3: Harmonic Function",
      "Task 8: Voice-Leading Violation Detection",
      "Main output: prediction_label",
    ],
    1.0,
    2.7,
    5.0,
    { fontSize: 11.5, gap: 0.46 }
  );
  addCard(
    slide,
    6.8,
    2.15,
    5.85,
    3.1,
    "Sequence transformation",
    "",
    COLORS.paleGold,
    COLORS.gold
  );
  addBulletList(
    slide,
    [
      "Task 4: Transposition",
      "Task 5: Melodic Inversion",
      "Task 6: Retrograde",
      "Task 7: Rhythmic Augmentation or Diminution",
      "Main output: prediction_notes",
      "Optional output: prediction_structured",
    ],
    7.1,
    2.7,
    5.0,
    { fontSize: 11.2, gap: 0.4 }
  );
  addCard(
    slide,
    0.7,
    5.6,
    11.95,
    0.95,
    "Usage modes",
    "Standard mode is the default benchmark path. Explanatory mode is optional and preserves prediction_explanation for qualitative paper analysis.",
    COLORS.panel,
    COLORS.rose
  );
  finalize(slide, "Benchmark tasks | label and sequence outputs");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Scope",
    "Current V1 scope",
    "The benchmark should present these constraints as an intentional V1 boundary for reproducible evaluation."
  );
  addCard(slide, 0.7, 2.15, 3.0, 1.55, "Harmonic function", "Major mode only in V1, with three coarse labels: tonic, predominant, dominant.", COLORS.panel, COLORS.teal);
  addCard(slide, 3.95, 2.15, 3.0, 1.55, "Voice-leading", "Two-voice simplification in V1, with labels limited to parallel_fifths, voice_crossing, and none.", COLORS.panel, COLORS.gold);
  addCard(slide, 7.2, 2.15, 2.9, 1.55, "Harmony", "Reduced chord vocabulary focused on major, minor, diminished, augmented, and dominant7.", COLORS.panel, COLORS.rose);
  addCard(slide, 10.35, 2.15, 2.3, 1.55, "Representation", "Symbolic music only, not audio.", COLORS.panel, COLORS.green);
  addCard(
    slide,
    0.7,
    4.1,
    11.95,
    1.65,
    "Interpretation of scope",
    "These are not arbitrary simplifications. They define a current V1 benchmark slice that is narrow enough to be stable, testable, and easy to document, while still being broad enough to support a real discussion in music theory and computational musicology.",
    COLORS.paleTeal,
    COLORS.teal
  );
  finalize(slide, "Current V1 scope | constrained but defensible");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Scope",
    "Planned extensions and not yet final theoretical coverage",
    "The current benchmark is scientifically usable now, but it should not be framed as the final boundary of the paper."
  );
  addCard(
    slide,
    0.7,
    2.15,
    6.0,
    3.6,
    "Planned extensions",
    "",
    COLORS.panel,
    COLORS.gold
  );
  addBulletList(
    slide,
    [
      "Extend harmonic-function coverage beyond major mode.",
      "Extend voice-leading analysis beyond two voices.",
      "Expand the harmonic vocabulary and chord-template inventory.",
      "Study richer analytical explanations and explanation quality.",
      "Broaden the comparison between standard accuracy and interpretive capacity.",
    ],
    1.05,
    2.8,
    5.3,
    { fontSize: 11.2, gap: 0.56 }
  );
  addCard(
    slide,
    7.0,
    2.15,
    5.65,
    1.85,
    "Not yet final theoretical coverage",
    "The paper should describe the current benchmark as a V1 slice, not as exhaustive tonal or musicological coverage.",
    COLORS.paleRose,
    COLORS.rose
  );
  addCard(
    slide,
    7.0,
    4.25,
    5.65,
    1.5,
    "Recommended wording",
    "Current V1 scope. Planned extensions. Not yet final theoretical coverage.",
    COLORS.paleGold,
    COLORS.gold
  );
  finalize(slide, "Planned extensions | future-facing wording");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Architecture",
    "Benchmark pipeline architecture",
    "The benchmark is organized as a rule-based generation and evaluation pipeline around tokenizer views and model-ready cases."
  );
  const y = 3.0;
  const w = 2.1;
  addFlowBox(slide, 0.75, y, w, 1.25, "Theory rules", "rules.py\ntask_specs.py\nmusicology.py", COLORS.panel);
  addFlowBox(slide, 3.0, y, w, 1.25, "Raw benchmark", "gen_zero_shot.py\nraw note-level jsonl", COLORS.panel);
  addFlowBox(slide, 5.25, y, w, 1.25, "Views and cases", "export_views.py\nbuild_model_io_json.py", COLORS.panel);
  addFlowBox(slide, 7.5, y, w, 1.25, "Model runners", "run_api_model_list.py\nrun_ollama_model_list.py", COLORS.panel);
  addFlowBox(slide, 9.75, y, w, 1.25, "Evaluation", "eval_predictions.py\nannotate_model_outputs.py", COLORS.panel);
  addArrow(slide, 2.85, y + 0.62, 3.0, y + 0.62);
  addArrow(slide, 5.1, y + 0.62, 5.25, y + 0.62);
  addArrow(slide, 7.35, y + 0.62, 7.5, y + 0.62);
  addArrow(slide, 9.6, y + 0.62, 9.75, y + 0.62);
  addCard(
    slide,
    0.75,
    5.05,
    11.1,
    1.2,
    "Output products",
    "The standard path produces predictions.jsonl, overall.json, by_task.json, and by_tokenizer.json. The analysis path adds cases_with_outputs.json and summary.json.",
    COLORS.paleTeal,
    COLORS.teal
  );
  finalize(slide, "Architecture | benchmark pipeline");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Workflow",
    "Standard benchmark workflow for non-expert users",
    "The default path should be simple enough to document in a user guide and easy enough to run without deep repository knowledge."
  );
  const steps = [
    ["Generate", "gen_zero_shot.py"],
    ["Export", "export_views.py"],
    ["Validate", "validate_views.py"],
    ["Build", "build_model_io_json.py"],
    ["Run", "run_api_model_list.py or run_ollama_model_list.py"],
    ["Evaluate", "eval_predictions.py"],
    ["Review", "annotate_model_outputs.py"],
  ];
  steps.forEach((step, index) => {
    const x = 0.8 + index * 1.8;
    addFlowBox(slide, x, 3.0, 1.5, 1.2, step[0], step[1], index % 2 === 0 ? COLORS.panel : COLORS.paleGold);
    if (index < steps.length - 1) {
      addArrow(slide, x + 1.5, 3.6, x + 1.74, 3.6, COLORS.gold);
    }
  });
  addCard(
    slide,
    1.15,
    5.1,
    11.1,
    1.15,
    "Design principle",
    "The standard benchmark is mandatory, stable, and automatically evaluable. Users do not need to provide analytical explanations unless they explicitly want paper-oriented examples.",
    COLORS.paleRose,
    COLORS.rose
  );
  finalize(slide, "Workflow | standard benchmark mode");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Schema",
    "Canonical prediction schema",
    "The benchmark keeps backward compatibility with the legacy prediction field while defining task-aware canonical outputs."
  );
  addCard(slide, 0.7, 2.15, 5.8, 3.95, "Label-task prediction row", "", COLORS.panel, COLORS.teal);
  slide.addText(
    '{\n  "id": "task3_harmonic_function-000001",\n  "prediction_type": "label",\n  "prediction_label": "dominant",\n  "prediction_explanation": "optional",\n  "prediction": "dominant"\n}',
    {
      x: 1.0,
      y: 2.75,
      w: 5.1,
      h: 2.9,
      fontFace: "Courier New",
      fontSize: 10.5,
      color: COLORS.ink,
      fill: { color: "F8FAFD" },
      line: { color: COLORS.line, pt: 0.8 },
      margin: 0.16,
    }
  );
  addCard(slide, 6.8, 2.15, 5.85, 3.95, "Sequence-task prediction row", "", COLORS.panel, COLORS.gold);
  slide.addText(
    '{\n  "id": "task4_transposition-000001",\n  "prediction_type": "notes",\n  "prediction_notes": "tokenized melody",\n  "prediction_structured": [ ... ],\n  "prediction": "tokenized melody"\n}',
    {
      x: 7.1,
      y: 2.75,
      w: 5.1,
      h: 2.9,
      fontFace: "Courier New",
      fontSize: 10.1,
      color: COLORS.ink,
      fill: { color: "F8FAFD" },
      line: { color: COLORS.line, pt: 0.8 },
      margin: 0.16,
    }
  );
  finalize(slide, "Prediction schema | canonical fields with fallback");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Evaluation",
    "Automatic evaluation and result products",
    "The standard evaluator covers all eight tasks while still allowing task-specific sequence analysis when needed."
  );
  addCard(slide, 0.7, 2.15, 4.1, 3.9, "Core evaluator", "eval_predictions.py unifies Tasks 1-8 and produces overall, by-task, and by-tokenizer summaries.", COLORS.panel, COLORS.teal);
  addBulletList(
    slide,
    [
      "Tasks 1 and 2: exact match accuracy",
      "Task 3: accuracy and macro F1",
      "Task 4: exact match, pitch accuracy, interval preservation, rhythm preservation",
      "Task 5: exact match and pitch accuracy",
      "Task 6: exact match",
      "Task 7: exact match, duration accuracy, bar validity",
      "Task 8: accuracy and macro F1",
    ],
    1.0,
    3.0,
    3.45,
    { fontSize: 9.8, gap: 0.39 }
  );
  addCard(slide, 5.1, 2.15, 3.7, 1.85, "Primary outputs", "overall.json\nby_task.json\nby_tokenizer.json", COLORS.paleGold, COLORS.gold);
  addCard(slide, 5.1, 4.2, 3.7, 1.85, "Analysis outputs", "cases_with_outputs.json\nsummary.json", COLORS.paleRose, COLORS.rose);
  addCard(slide, 9.05, 2.15, 3.6, 3.9, "Why this matters", "The benchmark can be tested with short, stable outputs. This keeps the main evaluation reproducible while leaving room for a second explanatory layer in the paper.", COLORS.panel, COLORS.green);
  finalize(slide, "Evaluation | standard reporting and analysis outputs");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Musicology",
    "Standard mode vs explanatory mode",
    "The benchmark remains formally strict in standard mode and analytically richer in explanatory mode."
  );
  addCard(slide, 0.7, 2.15, 5.8, 3.65, "Standard benchmark mode", "", COLORS.paleTeal, COLORS.teal);
  addBulletList(
    slide,
    [
      "Mandatory and documented first.",
      "Aimed at non-expert users.",
      "Stable outputs: prediction_label or prediction_notes.",
      "Easy parsing and automatic scoring.",
      "Best path for demos, tests, and reproducible evaluation.",
    ],
    1.0,
    2.8,
    5.1,
    { fontSize: 11.2, gap: 0.53 }
  );
  addCard(slide, 6.8, 2.15, 5.85, 3.65, "Explanatory mode", "", COLORS.paleGold, COLORS.gold);
  addBulletList(
    slide,
    [
      "Optional and paper-oriented.",
      "Keeps the same main output as standard mode.",
      "May add prediction_explanation for label tasks.",
      "Supports qualitative comparison between correctness and explanation quality.",
      "Should not become a dependency of the core benchmark metric.",
    ],
    7.1,
    2.8,
    5.1,
    { fontSize: 11.1, gap: 0.5 }
  );
  slide.addText('prediction_label = "dominant"\nprediction_explanation = "In C major, G functions as V and creates tension toward the tonic."', {
    x: 1.1,
    y: 5.95,
    w: 11.0,
    h: 0.7,
    fontFace: "Courier New",
    fontSize: 10.5,
    color: COLORS.ink,
    fill: { color: "F8FAFD" },
    line: { color: COLORS.line, pt: 0.8 },
    margin: 0.16,
  });
  finalize(slide, "Musicology layer | standard and explanatory usage modes");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Diagrams",
    "Use-case view",
    "This view is useful when explaining who uses the benchmark and what each user type needs from it."
  );
  slide.addText("Actors", {
    x: 0.92, y: 2.2, w: 1.5, h: 0.25,
    fontFace: "Georgia", fontSize: 16, bold: true, color: COLORS.ink
  });
  addFlowBox(slide, 0.8, 2.7, 2.2, 0.95, "Non-expert user", "Runs and scores the standard benchmark", COLORS.panel);
  addFlowBox(slide, 0.8, 4.0, 2.2, 0.95, "Research user", "Collects qualitative paper examples", COLORS.panel);
  addFlowBox(slide, 0.8, 5.3, 2.2, 0.95, "Model developer", "Compares models and tokenizers", COLORS.panel);
  slide.addText("Use cases", {
    x: 3.75, y: 2.2, w: 1.7, h: 0.25,
    fontFace: "Georgia", fontSize: 16, bold: true, color: COLORS.ink
  });
  addFlowBox(slide, 3.6, 2.7, 3.0, 0.95, "Run the standard benchmark", "Generate, run, evaluate", COLORS.paleTeal);
  addFlowBox(slide, 3.6, 4.0, 3.0, 0.95, "Review annotated outputs", "Inspect hit_ground_truth and examples", COLORS.paleGold);
  addFlowBox(slide, 3.6, 5.3, 3.0, 0.95, "Compare tokenizers or models", "Benchmark engineering workflow", COLORS.paleRose);
  addFlowBox(slide, 7.2, 2.7, 5.0, 0.95, "Collect paper examples", "Use cases_with_outputs.json and summary.json", COLORS.panel);
  addFlowBox(slide, 7.2, 4.0, 5.0, 0.95, "Inspect analytical explanations", "Optional prediction_explanation for qualitative analysis", COLORS.panel);
  addArrow(slide, 3.0, 3.18, 3.56, 3.18);
  addArrow(slide, 3.0, 4.48, 3.56, 4.48);
  addArrow(slide, 3.0, 5.78, 3.56, 5.78);
  addArrow(slide, 6.6, 3.18, 7.16, 3.18);
  addArrow(slide, 6.6, 4.48, 7.16, 4.48, COLORS.gold);
  finalize(slide, "Use-case view | actors and benchmark goals");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Diagrams",
    "Sequence and component views",
    "These views are useful in the paper and in technical walkthroughs because they separate runtime order from logical organization."
  );
  slide.addText("Runtime sequence", {
    x: 0.85, y: 2.15, w: 2.2, h: 0.25,
    fontFace: "Georgia", fontSize: 16, bold: true, color: COLORS.ink
  });
  const actors = [
    ["User", 0.85],
    ["Generator", 2.35],
    ["Views", 3.85],
    ["Cases", 5.35],
    ["Runner", 6.85],
    ["Eval", 8.35],
    ["Review", 9.85],
  ];
  actors.forEach(([label, x]) => {
    addFlowBox(slide, x, 2.55, 1.15, 0.58, label, "", COLORS.panel);
    slide.addShape(pptx.ShapeType.line, {
      x: x + 0.58,
      y: 3.2,
      w: EPS,
      h: 2.15,
      line: { color: COLORS.line, pt: 1, dash: "dash" },
    });
  });
  addArrow(slide, 1.45, 3.55, 2.35, 3.55);
  addArrow(slide, 2.95, 3.9, 3.85, 3.9);
  addArrow(slide, 4.45, 4.25, 5.35, 4.25);
  addArrow(slide, 5.95, 4.6, 6.85, 4.6);
  addArrow(slide, 7.45, 4.95, 8.35, 4.95);
  addArrow(slide, 7.45, 5.3, 9.85, 5.3, COLORS.gold);
  slide.addText("generate", { x: 1.63, y: 3.42, w: 0.6, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });
  slide.addText("export", { x: 3.12, y: 3.77, w: 0.6, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });
  slide.addText("build", { x: 4.62, y: 4.12, w: 0.6, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });
  slide.addText("run", { x: 6.13, y: 4.47, w: 0.6, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });
  slide.addText("score", { x: 7.62, y: 4.82, w: 0.6, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });
  slide.addText("annotate", { x: 8.12, y: 5.17, w: 0.7, h: 0.16, fontFace: "Verdana", fontSize: 8, color: COLORS.muted });

  slide.addText("Component view", {
    x: 10.45, y: 1.98, w: 2.0, h: 0.25,
    fontFace: "Georgia", fontSize: 16, bold: true, color: COLORS.ink
  });
  addFlowBox(slide, 10.35, 3.15, 2.25, 0.62, "Theory logic", "rules.py\ntask_specs.py\nmusicology.py", COLORS.paleTeal);
  addFlowBox(slide, 10.35, 4.0, 2.25, 0.62, "Representation", "render.py\ntokenizers.py\npredictions.py", COLORS.paleGold);
  addFlowBox(slide, 10.35, 4.85, 2.25, 0.62, "Execution", "build_model_io_json.py\nmodel runners", COLORS.panel);
  addFlowBox(slide, 10.35, 5.7, 2.25, 0.62, "Analysis", "eval_predictions.py\nannotate_model_outputs.py", COLORS.paleRose);
  finalize(slide, "Sequence and component views | runtime and logical organization");
}

{
  const slide = pptx.addSlide();
  addBase(
    slide,
    "Paper",
    "Paper framing, contributions, and next steps",
    "The project can now be presented as both a usable benchmark and a paper-ready research artifact."
  );
  addCard(slide, 0.7, 2.15, 5.8, 3.95, "Paper framing", "", COLORS.panel, COLORS.teal);
  addBulletList(
    slide,
    [
      "A symbolic benchmark for music theory and computational musicology.",
      "A multi-task benchmark for symbolic musical reasoning.",
      "Automatic formal evaluation with stable outputs.",
      "Optional analytical explanation layer for qualitative analysis.",
      "Current V1 scope with planned extensions and not yet final theoretical coverage.",
    ],
    1.0,
    2.8,
    5.1,
    { fontSize: 11.1, gap: 0.5 }
  );
  addCard(slide, 6.8, 2.15, 5.85, 1.85, "Research claims", "Operationalization of music-theory concepts, benchmark design for symbolic reasoning, and comparison between structural accuracy and explanation quality.", COLORS.paleGold, COLORS.gold);
  addCard(slide, 6.8, 4.2, 5.85, 1.85, "Next steps", "Finish API integration, run benchmark experiments, collect explanatory examples, and refine paper and presentation together.", COLORS.paleRose, COLORS.rose);
  finalize(slide, "Paper framing | benchmark and scientific contribution");
}

async function main() {
  await pptx.writeFile({ fileName: path.join(__dirname, "paper-proposal-deck-raw.pptx") });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
