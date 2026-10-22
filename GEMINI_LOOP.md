# Calibration loop — Cline × Gemini

One round = run the harness on the frozen sample, audit it, send results + change plan to Gemini,
apply what it confirms or improves, then start the next round. 30 rounds.

## Rules of the loop

1. **Frozen sample.** Seed `20261022`, 10 stratified bikes. Never change the sample mid-loop — a score
   is only comparable against the same bikes.
2. **Two numbers, always.** Harness depth is meaningless without the audit. Report
   `width / harness depth / false fits / true depth`.
3. **No silent fits.** A missing fact is `cannot_confirm`. Never a "lead with a warning" — Gemini's
   ruling: that pollutes precision and the false-fit metric.
4. **One question per unresolved slot, ≤4 options.** If unanswered → leave blank.
5. **Signal to scale.** Only after **3 consecutive rounds with 0 false fits** across the full physical
   matrix (freehub + pull ratio + shell + ring count) may the sample grow to 30 bikes.
6. **Every fix carries its audit class.** A gate without an audit check is untested.

## Round log

| # | width | harness depth | false fits | true depth | dominant finding |
|---|---|---|---|---|---|
| 1 | 100% | 97% | 8 | 75% | chain locks/pins sold as chains (6), cotter spindle as BB, DI2 on a cable bike |
| 2 | 88% | 97% | 10 | 64% | audit widened: speed buckets (6), brand family (2), range (1), cup-set (1) |
| 3 | 83% | 97% | 1 | 97.3% | all categories wired; title-authoritative speed removed the bucket class |

## Round 3 → Gemini's rulings (applied to round 4)

- **Order is wrong.** Gemini: E (audit classes) → A (freehub) → D (ring count) → C (archive fields)
  → F (scale) → B (question engine). Audit first, because a fix without a detector is a regression
  waiting to happen.
- **"SRAM 12s AXS ⇒ XD" is wrong and dangerous.** Road AXS = **XDR**, MTB Eagle AXS = **XD**. An XDR
  cassette will not seat on an XD driver. The freehub gate must be Road/MTB-aware, not brand-aware.
- **Silent false-fit risk #1:** XD vs XDR. **#2:** road vs MTB pull-ratio inside the same speed count
  (Tiagra 4700 10-speed uses the 11-speed road ratio; Dynasys MTB 10-speed does not match road 10).
- **Blank-on-unanswered is correct** for the harness. Do not soften it into a lead.
- **Do not touch** the question engine or scale the sample until three clean rounds.

## Round 4 backlog (ordered by Gemini)

| # | Item | Done when |
|---|---|---|
| 1 | Audit classes: (a) XD vs XDR vs HG vs MicroSpline, (b) road/MTB pull ratio, (c) dimension contradiction | each class fires on a seeded counter-example and stays quiet on the 10-bike baseline |
| 2 | Freehub gate: HG / XD / XDR / MicroSpline / Campy N3W, split road vs MTB | the DURA-ACE-on-SRAM-AXS false fit disappears; SRAM NX (HG) cassettes stay allowed |
| 3 | Ring count 1×/2×/3× from OEM words on cranksets and FDs | a 1× crank cannot match a 2× bike |
| 4 | Archive fields: wheel size, BB shell | width recovers ≥10 of the 29 lost slots |
| 5 | Scale to 30 bikes | only after 3 consecutive 0-false-fit rounds |
| 6 | Question engine | last; UX, not calibration |
