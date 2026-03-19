# Task Diagram Prompts (Image Generation)

This file provides ready-to-use prompts for generating per-task benchmark diagrams.
Task order follows the new numbering:
- Label tasks: `task1` to `task4`
- Sequence tasks: `task5` to `task8`

## Global Style Prefix

Use this prefix before each task-specific prompt:

```text
clean academic infographic, white background, vector style, black and blue color palette, minimal layout, high readability, 16:9, title + input panel + operation panel + output panel, music-theory symbols, no 3D, no photorealism, no watermark, no logo, no decorative clutter
```

## Label Classification (Task 1-4)

### Task 1: Interval Identification (`task1_interval_identification`)

```text
Interval Identification. Show two single notes as piano-roll blocks at the same start time (example: C4 and E4). Draw a vertical pitch-distance arrow and annotate semitone distance. Output panel shows one label token: major_third. Emphasize mapping from two-note input to one interval label.
```

### Task 2: Chord Identification (`task2_chord_identification`)

```text
Chord Identification. Show a simultaneity of notes stacked vertically (example: C4 E4 G4). Input is one chord-note set. Operation panel: infer root and quality. Output panel shows one label token: C_major. Emphasize set-to-label classification.
```

### Task 3: Harmonic Function Classification (`task3_harmonic_function`)

```text
Harmonic Function Classification. Show chord-note stack with explicit key context box: Key = C major. Operation panel: classify functional role. Output panel shows one label token from tonic / predominant / dominant. Emphasize context-dependent harmonic function.
```

### Task 4: Voice-Leading Violation Detection (`task4_voice_leading`)

```text
Voice-Leading Violation Detection. Show two voices across two time states t0 and t1, each voice with directional arrows. Include examples of parallel fifths and voice crossing patterns. Output panel shows one label token from parallel_fifths / voice_crossing / none. Emphasize rule-based violation detection.
```

## Note Sequence Transformation (Task 5-8)

### Task 5: Transposition (`task5_transposition`)

```text
Transposition. Input panel shows a short melody in piano-roll form and control params source_key -> target_key. Operation panel: shift all pitches by constant semitone offset. Output panel shows transformed melody with same note count, same order, same durations. Emphasize pitch shift only.
```

### Task 6: Melodic Inversion (`task6_melodic_inversion`)

```text
Melodic Inversion. Input panel shows melody and pivot pitch line. Operation panel displays formula p' = 2*pivot - p and mirror arrows for each note. Output panel shows inverted melody preserving timing and note order. Emphasize geometric pitch reflection.
```

### Task 7: Retrograde (`task7_retrograde`)

```text
Retrograde. Input panel shows melody left-to-right with numbered note order. Operation panel: reverse note order only. Output panel shows reversed sequence while preserving each note's pitch-duration pair. Emphasize temporal reversal.
```

### Task 8: Rhythm Scale (`task8_rhythm_scale`)

```text
Rhythm Scale. Input panel shows melody with explicit durations. Operation panel: duration x factor (example x2 or x0.5), keep pitch sequence unchanged. Output panel shows scaled durations and unchanged pitch order. Emphasize duration transformation only.
```

## Optional Negative Prompt

Use when your tool supports negative prompts:

```text
blurry, low resolution, cluttered layout, handwritten text, realistic photo, dark background, neon glow, fantasy style, extra symbols, illegible labels, watermark, logo
```

