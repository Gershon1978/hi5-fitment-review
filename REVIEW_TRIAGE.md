# External review triage — GPT, 2026-10-22

Verdict received: **do not ship yet**. Below: what I verified in the code, what I fixed
immediately, what I accept and defer, and what I reject with reasons. No claim is accepted on
the reviewer's authority alone.

## 1. Accepted and fixed in this commit

| finding | evidence in code | fix |
|---|---|---|
| Rotor diameter could be taken from **anywhere** in the bike record | `req["rotor_mm"] = parse_rotor_mm(bt) or parse_rotor_mm(json.dumps(bike))` — a fork's 160 mm *travel* could become a 160 mm rotor requirement | fallback removed; diameter only from `brakes.type` |
| Pads could be matched when the brake type was unknown | `if kind:` filtered the pool but never refused | brake type now mandatory → `cannot_confirm` + one question |
| 12-speed ⇒ thru-axle asserted from a correlation | `req["axle"] = "thru"` on `speed == 12` (100%, n=47) | removed: a correlation is not a versioned compatibility rule |
| Auditor never checked rotors or pads | auditor reasons were form / family / speed / range / freehub only | new **`audit_wave1.py`**, deliberately written without the harness's parsers |

## 2. Accepted, measured, not yet fixed

**The independent Wave-1 audit result is the most important number in this document:**

```
WAVE-1 AUDIT: checked 2 rotor/pad fits (rotors 2, pads 0)
false: 0 | unverifiable (missing bike fact): 2
```

So the reviewer's conclusion is correct and now quantified: on the real archive the Wave-1
safety-critical fits are **almost entirely unverifiable**, because the bike record does not
state the fact the claim depends on. "Precision 1.000" never covered rotors and pads, and now
we can say how much that mattered.

Still open, accepted:

- `match_pads` matches on the caliper token only; it does not enforce the `Совместимость`
  attribute. Substring identity is not pad geometry.
- `match_hubs` merges front and rear stock and has no reliable position check.
- `match_tyres` checks bead-seat diameter only; no width or clearance.
- Result vocabulary (`fits` / `cannot_confirm` …) does not match the spec's
  (`fits` / `fits_with_caveat` / `cannot_confirm` / `excluded`).
- `ROWS` is built at import time; tests and refreshes are awkward.
- `requirement()` mixes parsing, inference and source precedence.

## 3. Rejected, with reasons

**"The spec says no questions to the rider; the harness violates the product contract."**
Half right. That sentence is decision #1 of the **v0.1** spec, written before the question-based
design existed. The current product intent is the opposite — one question per unresolved slot,
capped at 3, which is what the shop asked for. The defect is in the *document*, not the engine:
`fitment-spec.json` still carries the stale no-question line. Fix the spec text.

**"A candidate row next to `cannot_confirm` risks being read as a recommendation."**
It is a lead, deliberately: "here is what we would show you if you answer this". The risk is
real but it lives in the UI contract, not the matcher. Recorded as a requirement: the advisor
must never render a `cannot_confirm` candidate as a fit.

## 4. What this changes about the shipping position

Before: "precision 1.000, coverage 35%, ship an honest assistant".
After: **that claim was too strong.** It holds for drivetrain, wheels and cockpit categories
that the general auditor covers; it does **not** extend to rotors and pads, which are exactly
the safety-critical ones. The honest statement is:

> Precision 1.000 on 8,589 audited fits **in the five audited classes**. Rotors and pads are
> unaudited in practice and unverifiable in this archive; they must stay `cannot_confirm` until
> a mechanic signs off a fixture set.

## 5. Next three, accepted as written

1. Mechanic-reviewed fixtures for brakes / BB / hubs, positive **and** negative cases.
2. Enforce mandatory rules at the recommendation boundary: a product may be `fits` only when
   every applicable mandatory attribute is verified.
3. Acquire caliper compatibility, rotor mount and BB interfaces — but only for named
   requirements the engine cannot verify, not as general enrichment.
