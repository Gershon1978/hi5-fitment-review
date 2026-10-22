# Data-Acquisition & Archive Enrichment Spec — v1.0 (2026-10-22)

Status: draft for review by Andrey. Supersedes the backlog in `LOOP_30.md` §Backlog.

## 0. Why this exists before wiring

The engine is not the bottleneck any more. Rounds L16–L30 walked 1,220 bikes and audited
**8,589 candidate fits with 0 false fits (precision 1.000)**; over-rejection is negligible
(`no_candidate` ≤ 11 per slot across 720 bikes). What limits the product is that the archive
does not state the attributes the gates need.

Wiring a 22%-coverage engine into the counter today means telling the shop "мы не знаем"
four times out of five. That is a worse first impression than not shipping, and it burns the
trust that 1.000 precision just earned.

## 1. The rule that governs every field in this document

**No field may be populated by inference below 99% confidence with ≥25 supporting bikes**
(the L1 ruling). Consequences that must not be softened:

| proposal | confidence | verdict |
|---|---|---|
| 12-speed ⇒ thru-axle | 100% (n=47) | allowed — live |
| Eagle ⇒ 12-speed | 96% (n=26) | **rejected** (was live, removed at L2) |
| "modern adult MTB/Road ⇒ 31.8 mm bar clamp" | ~95% | **rejected** — scrape it, do not infer it |
| mountain ⇒ BSA | 66% | rejected |
| 105 ⇒ 11-speed | 41% | rejected (spans three generations) |

A 95% rule is not "good enough for a shop". It is 5 customers in 100 leaving with the wrong
part. Where a value is only ~95% predictable, the field is a **scrape target**, and if it
cannot be scraped it stays `null` and becomes a counter question.

## 2. Three tiers

**Tier A — derivable from data already in the archive (no acquisition).**
Already live: rim ETRTO from stated tyre (L9), cassette model ⇒ freehub (L4), crank spindle ⇒
BB interface (L12), ETRTO normalisation 700C ≡ 29" ≡ 622 (L5).
Remaining: rim internal width as a *compatibility band* from the stock tyre width.

**Tier B — requires enrichment from an external authoritative source.**
Bar clamp diameter, stem steerer + clamp, BB shell standard, seatpost diameter.
These are stated on OEM spec sheets or frame geometry PDFs, and almost never in the archive.

**Tier C — cannot be enriched; ask at the counter.**
Hub spoke count (28/32/36) — not on OEM sheets for stock wheels, varies by build.
Already handled by the L10 question path; this spec asks for no data work.

## 3. Ranked backlog

Slot counts are the L4 full-archive baseline (1,519 bikes); they drift slightly as gates
change, so re-measure after each pass rather than trusting the number.

| # | Field | Slots blocked | Tier | Method | Acceptance |
|---|---|---|---|---|---|
| 1 | `hub_holes` front+rear | 1,702 | C | counter question (already live) | question fires, ≤3/bike (L14 cap) |
| 2 | `handlebar_clamp_mm` | 872 | B | OEM spec / retailer listing | ≥99% spot-check on 20 records |
| 3 | `stem_steerer` + `stem_clamp_mm` | 803 | B | **same scrape as #2** | idem |
| 4 | `rim_internal_mm` | 634 | A | band derived from tyre width | band must not exclude a valid rim |
| 5 | `bb_shell` | 517 | B | frame geometry PDF (BSA vs BB86/92/PF30/T47) | ≥99% spot-check |

**The double unlock.** #2 and #3 are the same physical measurement — the clamp at the centre
of the bar. One field, `handlebar_clamp_mm`, unlocks **1,675 slots** (872 bars + 803 stems).
That is ~98% of the spoke-count prize, and unlike spoke count it *is* on spec sheets.
This is the single highest-return hour of work in the whole project.

## 4. Schema (exact field names — the engine already looks here)

```jsonc
bike.components.handlebar_clamp_mm  // 25.4 | 26.0 | 31.8 | 35.0 | null
bike.components.stem_clamp_mm       // same domain (usually == handlebar clamp)
bike.components.stem_steerer        // "28.6" (1-1/8") | "31.8" (1.25") | "38.1" (1.5") | null
bike.wheels.rim_internal_mm         // integer mm | null
bike.wheels.hub_holes_front         // 28 | 32 | 36 | null
bike.wheels.hub_holes_rear          // 28 | 32 | 36 | null
bike.drivetrain.bb_shell            // "bsa68" | "bsa73" | "bb86" | "bb92" | "pf30" | "t47" | null
```

**Provenance is mandatory** for every enriched field — parallel object, never inline:

```jsonc
bike.enrichment.<field> = {
  "value": 31.8,
  "source_url": "https://...",
  "retrieved_at": "2026-10-22",
  "method": "oem_spec" | "retailer" | "measured"
}
```

`null` is always allowed and always preferred over a guess. A missing value costs a question;
a wrong value costs a customer.

## 5. Tier A derivation: rim internal width band

Given stock tyre nominal width `w` (mm), the rim must fall inside a compatibility band.
**These ranges are a starting proposal and must be confirmed by Andrey before they gate any
fit** — they are shop-practice numbers, not a standard I can cite:

| tyre width | rim internal band (mm) |
|---|---|
| 23–28 | 15–21 |
| 32–40 | 19–25 |
| 47–53 | 23–30 |
| 54–62 | 25–35 |
| 66–75 | 30–45 |

The band is used to *exclude* only rims outside it; anything inside stays a candidate. A rim
with no stated internal width is never excluded by this rule.

## 6. Acquisition rules

1. Source priority: OEM spec sheet / frame geometry PDF → manufacturer site → retailer
   listing → physical measurement. Never "the same model last year".
2. Never copy a value from a sibling trim. A 2021 Marlin 5 and a Marlin 7 can differ.
3. One record = one URL. No bulk rows without a source.
4. Spot-check 20 random records per field by hand. Field is rejected below 99% agreement.
5. Enrichment is additive: `null → value` only. Never overwrite a stated value.

## 7. Definition of done

- `handlebar_clamp_mm` populated on ≥90% of 2015+ road/MTB records → expect ~1,500 slots.
- Acceptance test after each pass, no exceptions:
  ```
  python validate_slice.py        # precision must stay 1.000
  ```
  Coverage (categories with ≥2 candidates) must rise from the current **22–26%** toward
  **≥45%** with precision still 1.000. If precision drops, the enrichment is wrong — revert
  the field, not the gate.

## 8. Engine integration — what code each field touches

| field | read by | code change needed |
|---|---|---|
| `handlebar_clamp_mm` | `raw_for("handlebar")` → `parse_mm` | **3 lines**: `raw_for` returns `components.handlebar` as one string, so the enriched field must be appended to it |
| `stem_clamp_mm` | `raw_for("stem")` → `parse_mm` | same 3 lines |
| `rim_internal_mm` | `match_rims` | small: band filter |
| `bb_shell` | `requirement("bottom_bracket")` | small: map to `bb_standard` |
| `hub_holes_*` | `requirement("hubs")` | none (already reads `wheels.hubs`) |

Correction to an earlier draft of this section: enrichment does **not** flow in for free. The
gates need no change — that part holds — but `raw_for()` returns each component as a single
string, so a new sibling field is invisible until it is appended there. Budget ~6 lines, and
do it **before** the first enrichment pass so the data lands on a path that is already wired.

## 9. What this spec explicitly refuses

- Probabilistic inference at 95% to "fill" bar clamp or BB shell.
- Filling `bb_shell` from bike type (mountain ⇒ BSA is 66% — wrong one time in three).
- Any bulk import without per-record provenance.
## 12. Unread-field audit (Wave 2) — where the traps are

Scanned every archive text field for mechanical facts (`unread_fields.py`). Result: the
archive holds more than the engine reads, but **most unread fields are false-positive traps**.

| fact | bikes with a hit | where | safe? |
|---|---|---|---|
| rotor diameter | 408 | `brakes.type` 299 · crankset 38 · fork 21 · frame 21 | **only `brakes.type`** |
| bb_shell | 144 | `drivetrain.bottom_bracket` 105 · `frame` 35 | **yes** — implemented |
| axle QR | 134 | `wheels.hubs` 75 · fork 23 · frame 13 · seatpost 18 | hubs yes, fork/frame **no** |
| axle thru | 61 | `wheels.hubs` 27 · frame 19 · fork 15 | hubs yes, fork/frame **no** |
| headset standard | 51 | `fork` 44 · frame 7 | wave 4 — not now |
| freehub | 23 | `wheels.hubs` 14 · cassette 5 | partial |

**Traps confirmed by inspecting the strings:**

- `fork`: `"Fox Float 36 … 180mm"` — that 180 is **travel**, not a 180 mm rotor. A naive
  rotor rule would fit a downhill rotor to a trail bike.
- `drivetrain.crankset`: `"… 175мм …"` — **crank length**. Same trap, different category.
- `components.seatpost`: `"Telescoping system w/quick-release collars"` — a QR **collar**, not
  a QR axle.
- `drivetrain.chain`: `"Alex XD-Lite"` — a rim model containing "XD", not an XD driver.
- `fork` axle (`15x110`) is the **front** axle; `match_hubs` covers front and rear in one slot,
  so applying a fork axle to the rear hub would be wrong.

**Conclusion:** the unread-field seam is now largely exhausted — 35 bb_shells were real and are
implemented; the rest need a domain guard per field before they can be trusted, and several
(fork travel, crank length) must never be mined at all. Coverage work from here needs either
category matchers (wave 4) or real acquisition (wave 3 hub mount), not more text mining.


Consulting `fitment-spec.json` (the manual) overrides my §3 ranking:

- `scope_waves`: **4 = seatposts, stems, bars, headsets, forks, shocks** — the last wave.
  I had ranked clamp enrichment #2 and #3, ahead of wave 1 (rotors/pads/adapters) and all of
  wave 2 (drivetrain). That was wrong on the manual's own terms.
- `Рули` note: **"width is fit; clamp diameter is compatibility"**; `Выносы`: **"length is fit,
  not compatibility"**. Both `nice_to_have` entries are tier_b: *ranking only, never excludes*.
  My matcher was **excluding** bars by width — a rule the manual forbids.
- `on_missing: cannot_confirm` for both BAR-CLAMP and STEM-STEERER — i.e. the manual's own
  answer to a missing clamp is **ask**, not acquire.

**Product consequence (Andrey's framing):** he does not need every clamp — he needs a few that
fit. A bar/stem is a standard-fit part; a customer who knows their clamp can be served today,
and a customer who does not gets one question. Enriching 232 bike records with a datum that
retires a single question is a poor use of nine cycles.

**Decision:** `handlebar_clamp_mm` / `stem_clamp_mm` are **removed from the acquisition
backlog** (Rank 2 and 3 of §3 are withdrawn). They remain supported by the question path.

**Code consequence (implemented):** `match_by_mm` now refuses to gate on a width. A parsed
value ≥ 380 is treated as a *fit preference* and returns `cannot_confirm` with the clamp
question instead of a fit. Verified: 24% coverage, 40/260 fits, 22 questions, **precision 1.000**.

**Re-ranked backlog, following the manual's waves:**

| # | Field / category | Slots | Wave | Status |
|---|---|---|---|---|
| 1 | **rotors** — `Диаметр` + `Тип` (mount) | 98 rows | 1 | **LIVE** — diameter from bike, mount asked (6-bolt vs CenterLock is binary) |
| 1 | **pads** — `Модель тормоза` (caliper) | 237 rows | 1 | **LIVE** — caliper model parsed from `brakes.type`, matched on normalised model, filtered disc vs rim |
| 1 | **adapters** — `Переход` | 45 rows | 1 | pending: derive only when rotor mount ≠ hub mount |
| 2 | `bb_shell` (BSA 68/73 vs PF) | 517 | 2 | next |
| 3 | hub spoke count | 1,702 | 3 | counter question only — live |
| — | ~~bar clamp~~ | ~~872~~ | 4 | withdrawn: standard fit, one question suffices |
| — | ~~stem clamp/steerer~~ | ~~803~~ | 4 | withdrawn: same measurement, same reasoning |


**Scope, option 2 (2015+ road/MTB-class with a blocked clamp slot): 232 bikes.**
Bars only 33, stems only 87, both 112 → **456 slot-unlocks** from 232 records. One cycle, not nine.

Parser recovery before the sweep: `parse_mm` now prefers a canonical clamp over a bar width and
skips the second value of a dimension pair, recovering **12 records** (3 bars, 9 stems).
Blocked records fell 1,504 → 1,492. Precision unchanged at 1.000.
Of the 1,492, only 232 are in the option-2 scope; the rest are older or non-road/MTB.

**Blocker found by testing, not assumed:**

1. The archive's `source` field is **not a spec sheet**. All 232 point at
   `bicyclebluebook.com/value-guide/<type>/…` category pages — they carry no component data.
2. **OEM pages are JS-rendered.** `fetch_web_content` against a Trek product URL returned 316 KB
   of boilerplate and zero component lines — and the URL itself resolved to a different model
   (Domane frameset), which is exactly the sibling-misattribution risk §6 forbids.
3. An aggregator attempt (99spokes search) loaded but scripted link extraction returned nothing
   (console errors, client-side rendering). A naive scraper does not work.

**Consequence:** no value may be written until a source that actually exposes component text is
chosen, and it must be read as rendered text, not raw HTML. Candidate sources, in the §6
priority order: manufacturer spec PDF (BMC/Trek/Specialized publish these), manufacturer product
page read through the browser, then the shop's own knowledge (Andrey).

**Revised cadence:** 20–30 bikes per cycle with a human-checkable source, not 232 in one pass.
At 25/cycle that is ~9 cycles for the full 232. The worklist is generated by `plan_sweep.py`
into `sweep_worklist.json`, so each cycle starts where the last stopped.

  crank arms, tubes, headsets, forks, shocks, bearings) before Tiers A–C are done. Those
  categories have no archive field at all and no acquisition plan yet.

