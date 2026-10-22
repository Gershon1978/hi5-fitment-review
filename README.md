# hi5.bike — parts-fitment engine (external review pack)

Prototype engine that matches a bicycle's stock components against a 6,337-SKU parts catalogue
and returns `fits` / `cannot_confirm` / `no_candidate`, plus at most one clarifying question per
blocked slot. Fail-closed by design: a false *fits* is treated as a safety failure.

**Start here → [`REVIEW_BRIEF.md`](REVIEW_BRIEF.md)**, then the questions in
[`GPT_REVIEW_PROMPT_ENGINE.md`](GPT_REVIEW_PROMPT_ENGINE.md).

## Measured state

| metric | value |
|---|---|
| precision | **1.000** — 8,589 audited candidate fits, 1,220 of 1,519 bikes, 0 false |
| coverage | **35%** of category-instances return ≥2 candidates |
| fits archive-wide | 4,932 (3.25 parts per bike) |
| ground truth | the engine auditing itself — **not** a mechanic |

## Files

| file | role |
|---|---|
| `REVIEW_BRIEF.md` | situation, decisions, weaknesses, what to attack |
| `GPT_REVIEW_PROMPT_ENGINE.md` | the review questions |
| `requip_harness.py` | the engine (start at `SLOTS`, `requirement()`, `match_*`) |
| `audit_false_fits_v3.py` | independent auditor for every produced fit |
| `validate_slice.py` | resumable whole-archive precision walk |
| `full_archive.py` | whole-archive outcome census |
| `correlations.py` | conditional-probability study over all 1,519 bikes |
| `unread_fields.py` | audits archive fields the engine never reads |
| `wave1_probe.py`, `wave2_probe.py` | what catalogue/archive state for wave 1 and 2 |
| `enrich_clamp.py`, `plan_sweep.py` | enrichment tooling (dry-run, provenance-mandatory) |
| `fitment-spec.json` | the shop's binding spec ("the manual"): 25 categories, rules, waves |
| `DATA_ACQUISITION_SPEC.md` | measured data gaps, tiers, explicit refusals |
| `LOOP_30.md`, `GEMINI_LOOP.md` | 30-round improvement protocol and log |
| `precision_state.json`, `full_summary.json`, `rounds_log.txt`, `requip-scorecard.md` | results |

The bike archive (`bikes.json`, 1,519 models) and the catalogue snapshot are **not** included —
they are shop data. The engine reads them from local paths; schemas are described in the brief.

## Not included / not done

The engine is **not** wired into the production advisor. No UI, no latency work, no caching.
15 of 25 categories have no field in the bike archive at all.
