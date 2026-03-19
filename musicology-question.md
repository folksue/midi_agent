# Musicology Question Notes

This document summarizes how to connect the benchmark to a real musicological question rather than only to a technical prediction task.

## Conceptual core

These tasks can already be read as categories of musical analysis:

- intervals, chords, and harmonic function as analytical categories
- transposition, inversion, and retrograde as transformational operations
- voice-leading as a normative judgment from common-practice music

## What the benchmark already does

The benchmark already turns music-theory concepts into measurable symbolic tasks:

- Task 1 evaluates interval recognition
- Task 2 evaluates harmonic sonority identification
- Task 3 evaluates tonal harmonic function
- Tasks 4-7 evaluate structural musical transformations
- Task 8 evaluates a normative notion of voice-leading

This already supports a computational musicology reading:

- the system is not only predicting tokens
- it is being evaluated on whether it recognizes or transforms musically meaningful relationships

## What is missing for it to sound genuinely musicological

It needs an analytical explanation layer.

The main output can remain short and evaluable:

- `prediction_label`
- `prediction_notes`

But it is useful to add an optional interpretive output:

- `prediction_explanation`

## Example

```text
prediction_label = dominant
prediction_explanation = "In C major, G functions as V and creates tension toward the tonic."
```

## Proposed framing for the paper

The project narrative can be framed like this:

- the benchmark operationalizes core concepts from music theory and musicology
- evaluation does not measure only textual matching, but structurally musical correctness
- the system can judge, classify, or transform symbolic material with analytical relevance

## Benchmark framing

The benchmark should be framed as:

- a symbolic benchmark for music theory and computational musicology
- a multi-task benchmark for symbolic musical reasoning
- a benchmark with automatic formal evaluation
- a benchmark with an optional analytical explanation layer

This framing supports the following paper-level claims:

- operationalization of music-theory concepts into reproducible tasks
- multi-task benchmark design for symbolic musical reasoning
- comparison between structural accuracy and explanatory capacity
- analysis of model limits in basic musicological categories

## Possible musicological question

One possible formulation is:

"To what extent can a generative or language model recognize, transform, and explain basic musical relationships in a way that is coherent with analytical categories from tonal musicology?"

Another possible formulation is:

"Can a symbolic system respond to music-theory tasks in a way that is not only formally correct, but also interpretable in musicological terms?"

## Practical translation into the project

To support that musicological dimension, it is useful to:

- keep a structured and evaluable output
- add an optional analytical explanation
- clearly document the benchmark's theoretical simplifications
- use qualitative examples in the paper alongside quantitative metrics

## Standard and explanatory modes

The project should clearly separate two benchmark usage modes.

### Standard benchmark mode

This mode should be:

- mandatory
- simple
- aimed at non-expert users
- documented first

Its goal is:

- stable outputs
- easy testing
- easy parsing
- easy automatic evaluation

Its main outputs are:

- `prediction_label`
- `prediction_notes`
- optional `prediction_structured`

### Explanatory mode

This mode should be:

- optional
- aimed at paper writing and qualitative analysis
- built around `prediction_explanation`

Its goal is:

- analytical interpretation
- qualitative examples
- comparison between correctness and explanation quality

The key rule is:

- the main benchmark remains driven by the standard output
- explanation is supplementary rather than required for the core metric

## Limitations that should be made explicit

- harmonic function only in major mode in this version
- voice-leading simplified to two voices
- reduced harmonic vocabulary
- focus on symbolic music, not audio

## Current V1 scope

The benchmark should present these simplifications as the current operational scope of V1.

- V1 prioritizes reproducibility, clean automatic evaluation, and easy handoff to non-expert users
- V1 therefore uses a constrained symbolic-theory slice rather than full tonal coverage
- these constraints are implementation decisions for a first benchmark release, not a claim that the underlying musicological space is exhausted

In other words, the current benchmark is intentionally narrow enough to be testable, but broad enough to support a real music-theory and musicology discussion.

## Planned extensions

The documentation and the paper can already signal the benchmark's next expansion path.

- extend harmonic-function coverage beyond major mode
- extend voice-leading analysis beyond two-voice examples
- expand the harmonic vocabulary and chord-template inventory
- explore richer analytical explanation prompts and evaluation protocols
- compare standard benchmark accuracy against explanation quality in a larger qualitative study

## Not yet final theoretical coverage

The current implementation should not be framed as the final theoretical boundary of the paper.

- it is a V1 benchmark slice
- it captures a defensible and reproducible subset of symbolic tonal reasoning
- it leaves room for broader modal, harmonic, contrapuntal, and interpretive coverage in later iterations

That wording makes the benchmark scientifically usable now, while keeping the paper open to future extensions.

## Operational conclusion

The benchmark already has an implicit musicological basis.

What is still missing for that basis to become explicit in the paper is:

- better explanation of the analytical meaning of each task
- an added explanation layer
- presenting the results as evidence of musical reasoning, not only of correct formatting
