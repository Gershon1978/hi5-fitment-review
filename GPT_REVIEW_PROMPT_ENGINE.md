# Review prompt — fitment ENGINE (not the spec)

Paste everything below into GPT, with `fitment/review_pack.zip` attached (unzip it first or
attach the files individually). Keep this file unchanged so the review is reproducible.

---

**Role.** You are a senior engineer who has shipped safety-critical matching systems, and you
know bicycle mechanics at bench level. You are reviewing a working prototype, not a proposal.

**What it is.** A shop (hi5.bike, Moscow) sells parts from a 6,337-SKU catalogue. An AI
assistant tells riders which part to buy. A prototype engine (`requip_harness.py`) matches a
bike's stock components against that catalogue and returns *fits* / *cannot_confirm* /
*no_candidate*, plus at most one clarifying question per blocked slot. A rider acting on a
false *fits* gets a part that physically does not work — for brakes, that is a safety failure.

**Read first:** `REVIEW_BRIEF.md`, then `requip_harness.py` (start at `SLOTS`, `requirement()`,
`match_*`), then `audit_false_fits_v3.py`. `fitment-spec.json` is the shop's binding
specification ("the manual"); `DATA_ACQUISITION_SPEC.md` records measured data gaps.

**What has been measured (do not re-derive, question the validity instead):**
precision 1.000 over 8,589 audited fits on 1,220 bikes; coverage 35% of category-instances
returning ≥2 candidates; 4,932 fits archive-wide. The auditor is written by the same author as
the engine.

**Answer these, in this order, concisely:**

1. **Is the precision number trustworthy?** The engine and the auditor share an author and
   share helper functions (`is_spare`, `brand_of`, `row_speeds`). Name the specific ways this
   could hide a systemic false fit, and the cheapest independent check that would expose it.
2. **Where would this engine hurt a customer first?** Rank the three most likely real-world
   false "fits", by category and mechanism, given the code as written.
3. **Is fail-closed + one question right for a shop counter?** The engine asks up to 3 questions
   per bike. Argue for or against, and say what you would cut.
4. **The 99% inference floor.** With these sample sizes, is 99% the right bar, or is it
   cargo-cult precision that starves coverage? Give a concrete rule you would accept.
5. **Architecture.** Single 1,300-line file, module-level `ROWS` cache, slot list dispatch,
   regex-heavy parsing, no schema. What breaks first if this goes into production, and what is
   the smallest change that prevents it?
6. **The next three moves.** Rank them by (customer harm avoided) ÷ (effort). Say explicitly
   which of these you would NOT do: more text mining, more category matchers, more data
   acquisition, rewriting the engine.

**Constraints on your answer:**
- No invented manual page numbers or citations. If it is general mechanical knowledge, say so.
- Do not propose a rule that needs data the archive does not hold — say "acquire X" instead.
- Be blunt about what is over-engineered. The author has spent a lot of effort on this and would
  rather hear it now.

**Output:** markdown, ≤900 words, headings 1–6 matching the questions, and end with a single
sentence verdict: ship as-is / ship with named guardrails / do not ship yet.
