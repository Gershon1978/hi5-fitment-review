# 30-round loop — protocol and backlog

One round = **improve → new bikes → run → audit → suggest → Gemini → apply → next round**.
No round may reuse bikes (the `used_bikes.json` ledger enforces it).

## Per-round mechanics

1. Pick one item from the backlog below.
2. Implement it in `requip_harness.py` (one change, one commit).
3. Run: `FITMENT_RUN=<n> python requip_harness.py` → 10 fresh bikes, 26 categories, ≤2 candidates each.
4. Audit: `python audit_false_fits_v3.py` → precision.
5. Send the round digest + the next 3 backlog candidates to Gemini; ask which to take and why.
6. Apply Gemini's answer as the next round's item. Repeat.

## Current state (carried in)

| | |
|---|---|
| precision | **0.999** (2 false fits in 2,909 candidates over 40 archived rounds) |
| coverage (≥2 per category) | 9–21%, mean ~14% |
| supported categories | 11 (partitioned); 15 are data-acquisition backlog |
| statistical inference live | Eagle ⇒ 12-speed (96%, n=26) · 12-speed ⇒ thru-axle (100%, n=47) |
| rejected by the 95% floor | mountain ⇒ BSA 66% · road ⇒ press-fit 60% · 105 ⇒ 11-speed 41% |

## Backlog for rounds L2–L30 (ordered by expected value)

| # | Item | Why |
|---|---|---|
| 1 | Extend cross-slot inference to crankset ⇒ BB interface | 44% of records state a BB; cranks give the interface for the rest |
| 2 | Hub freehub inference from cassette speed (12s HG vs MicroSpline) | unblocks cassette/hub matching without a stated freehub |
| 3 | Fork ⇒ headset standard (EC/ZS/IS) | headsets are currently not_in_archive for all bikes |
| 4 | Rim ERD estimation from size+width+profile | unlocks spoke length |
| 5 | Tyre width → rim internal width check | rim/tyre compatibility with 52%/32% coverage |
| 6 | BB shell width from frame type (68 road / 73 MTB) at 95% floor only | needs support ≥25 per class |
| 7 | Seatpost diameter prior from frame material/type (25.4/27.2/31.6) | 32% of records state it; the rest could be inferred if confidence holds |
| 8 | Brake rotor diameter from wheel size + brake type | rotors are 0% covered |
| 9 | Pad family from caliper when only the brake model is stated | pads are 0% covered |
| 10 | Hanger match from frame brand+model+year | 168 products, no dimension |
| 11 | Crankset ring count from groupset family (1×/2×/3×) | improves FD/crank gates |
| 12 | Chain min-length inference from cassette + chainstay | length rule currently nice-to-have |
| 13 | Derailleur capacity from model table (extend RD_FAMILY) | RD-CAPACITY unresolved for most rows |
| 14 | Shifter family from derailleur family (one-directional) | SHIFTER-FAMILY is conditional today |
| 15 | Tyre ETRTO normalisation (622/584/559) | unifies 700C/29er/27.5 naming |
| 16 | Rim brake track detection from name | RIM-BRAKE is conditional |
| 17 | Axle diameter (not just QR/thru) from speed+type | 15x100 vs 15x110 unresolved |
| 18 | Stem/bar diameter default from type (drop bar 31.8) | 18–19% coverage today |
| 19 | Pedal thread prior (9/16 adult, 1/2 kids/BMX) | pedals have no thread attribute |
| 20 | Saddle rail standard (7mm round vs 7x9 carbon) | tier_b today |
| 21 | Front derailleur pull from frame routing text | FD-PULL is conditional |
| 22 | Cassette range from RD max cog when both stated inconsistently | range class is the last false-fit source |
| 23 | Contradiction resolver: prefer the more specific field | e.g. cassette beats groupset |
| 24 | Confidence-weighted candidate ranking (spec_depth × inference confidence) | ranking quality, not exclusion |
| 25 | Two-candidate diversity rule (never two identical specs) | product goal: two real options |
| 26 | Audit: slash-form speed parsing (`7/8 скор`) | removes the remaining audit artefacts |
| 27 | Audit: compare brand against the slot's OEM string | same |
| 28 | Hold-out validation of every inference rule (70/30 split) | proves inference accuracy, not just coverage |
| 29 | Freeze-sample A/B for each change (same 10 bikes, on/off) | separates real gains from sample noise |

## Round log

| round | change | coverage ≥2 | fits | precision |
|---|---|---|---|---|
| L1 | statistical inference (Eagle ⇒ 12s, 12s ⇒ thru) | 17% | 46/260 | 0.989 (1 audit artefact) |
