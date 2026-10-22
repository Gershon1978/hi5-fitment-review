# REVIEW BRIEF — hi5.bike parts-fitment engine (for external review)

Reviewer: read this first, then the code. Everything here is measured, not estimated; where a
number is uncertain it says so.

## 1. The situation

hi5.bike is a Moscow bike shop. It does **not** sell bikes — it sells parts from a
**6,337-SKU catalogue** and has an AI assistant ("Andrey") that tells a rider which part to buy.

The shop also holds an **archive of 1,519 bike models** with their stock components
(`bikes.json`, not in this pack: ~8 MB). The archive is free text, e.g.

```
drivetrain.cassette : "Shimano HG31, 11-34, 8 speed"
brakes.type         : "Promax DSK-300R mechanical disc, 160mm rotors"
components.handlebar: "Cannondale C3 riser, Alloy, 4 degree upsweep, 9 degree backsweep, 760x15mm"
frame               : "Al-13 Butted, Hydroformed aluminum, BSA Threaded Bottom Bracket"
```

The task: given a bike, propose parts from stock that **will fit**. The governing fear is a
**false "fits"** — a wrong rotor is a brake that does not stop. A false "no" merely loses a sale.

## 2. What governs the design (the "manual")

`fitment-spec.json` is the shop's own specification, built by an earlier review pass. Key rules:

- 25 fitment-critical categories; each has `must_have` rules (mismatch **excludes**; missing →
  `cannot_confirm`) and `nice_to_have` (ranking only, **never excludes**).
- `scope_waves`: **1** rotors/pads/adapters → **2** drivetrain → **3** hubs/rims/tyres →
  **4** seatposts/stems/bars/headsets/forks/shocks.
- Category notes are binding, e.g. bars: *"width is fit; clamp diameter is compatibility"*;
  stems: *"length is fit, not compatibility"*.
- 15 of the 25 categories have **no field at all** in the bike archive.

## 3. What was built

`requip_harness.py` (single file, ~1,300 lines) — a matching harness that, for one bike,
evaluates every category and returns one of: `fits` / `cannot_confirm` / `no_candidate` /
`requirement_missing` / `not_stated` / `not_supported`, plus at most one **question** per
blocked slot with ≤4 stock-derived options.

Supporting scripts in the pack:

| file | role |
|---|---|
| `requip_harness.py` | the engine |
| `audit_false_fits_v3.py` | independent auditor: re-checks every produced fit |
| `validate_slice.py` | resumable whole-archive precision walk |
| `full_archive.py` | whole-archive outcome census |
| `correlations.py` | conditional-probability study over all 1,519 bikes |
| `unread_fields.py` | audits archive fields the engine never reads |
| `wave1_probe.py`, `wave2_probe.py` | what the catalogue/archive state for wave 1 and 2 |
| `precision_state.json` | cumulative walk result |
| `DATA_ACQUISITION_SPEC.md` | what data work remains, with measured scope |
| `LOOP_30.md`, `GEMINI_LOOP.md` | the 30-round improvement protocol and log |

## 4. Measured results (these are the numbers to attack)

- **Precision 1.000** — 8,589 audited candidate fits across **1,220 of 1,519 bikes**, 0 false
  fits, after the auditor itself was corrected. Latest round: 182 candidates, 0 false.
- **Coverage 35%** — share of category-instances returning ≥2 candidates on a 10-bike sample.
- **4,932 fits** in the last whole-archive census (3.25 parts per bike).
- Ground truth is **the engine auditing itself**, not a mechanic — that is the weakest point of
  the whole exercise and the brief says so deliberately.

## 5. Decisions already taken (challenge them, but know the reasoning)

1. **No probabilistic inference below 99% confidence / ≥25 supporting bikes.** Measured
   correlations: 12-speed ⇒ thru-axle 100% (n=47) — allowed; Eagle ⇒ 12-speed 96% — rejected;
   "modern adult bike ⇒ 31.8 mm bar clamp" ~95% — rejected; mountain ⇒ BSA 66% — rejected.
2. **Fail-closed.** A missing attribute is always `cannot_confirm`, never a guess.
3. **Ask one question, never a form.** Questions are capped at 3 per bike, ordered by
   consequence (BB → hubs → brakes → cassette → crankset).
4. **Follow the manual's waves**, even when a different category looks more lucrative.
   Consequence: bar/stem clamp enrichment (1,675 slots) was **withdrawn** — it is wave 4,
   standard-fit, and retires only one question.
5. **Title is authoritative, attributes are buckets.** The catalogue's `Скорость` field holds
   `"11 sp, 12 sp"`; only the product title is exact.
6. **Never mine a field whose units are ambiguous.** `fork: "Fox Float 36 … 180mm"` is travel,
   not a 180 mm rotor; `crankset: "175мм"` is crank length.

## 6. Known weaknesses — please weigh these

- Precision is self-audited. A mechanic has not signed off the 8,589 fits.
- 15 categories (rotors were until recently, plus hangers, chainrings, crank arms, tubes,
  headsets, forks, shocks, bearings, rotors, pads…) have no archive field; some now work only
  because the catalogue side is rich.
- Rotor fits are rare in practice: diameter is parseable, but **mount (6-bolt vs CenterLock)**
  almost never is → they degrade to a question. Hub mount is wave 3 data that does not exist.
- Adaptors are unimplemented. The engine cannot yet express "you need an adapter".
- The engine is not wired into the advisor; there is no UI, no latency work, no caching.
- The 10-bike round metric swings ±5 points on sampling alone (proved by an A/B run where
  inference ON and OFF produced byte-identical output). Treat single-round deltas with suspicion.

## 7. File map for the reviewer

```
REVIEW_BRIEF.md            this file
GPT_REVIEW_PROMPT_ENGINE.md  the questions I want answered
requip_harness.py          the engine (start at SLOTS, requirement(), match_*)
audit_false_fits_v3.py     how precision is measured
validate_slice.py          the resumable walk
fitment-spec.json          the manual: categories, rules, waves
DATA_ACQUISITION_SPEC.md   measured data gaps, tiers, refusals
LOOP_30.md, GEMINI_LOOP.md process + 30-round log
precision_state.json       cumulative precision/counts
```
