# -*- coding: utf-8 -*-
"""Fix the stale contract in fitment-spec.json and add the question/lead policy.

The v0.1 decision "No questions to the rider at matching time" predates the question-based
design and contradicts the engine and the shop's intent. Replace it with the current contract,
and state explicitly that a cannot_confirm candidate is a lead, never a recommendation.
"""
import io
import json

PATH = "fitment-spec.json"
spec = json.load(open(PATH, encoding="utf-8"))

STALE = ("No questions to the rider at matching time; only the category attributes are used.")

decisions = spec.get("decisions_already_made") or []
new_decisions = []
for d in decisions:
    if d.strip().startswith("No questions to the rider"):
        continue
    new_decisions.append(d)
new_decisions.append(
    "Questions to the rider ARE allowed (supersedes the v0.1 'no questions' decision): at most "
    "three per bike, ordered by consequence, options drawn from stock, never a form. A question "
    "must resolve one named missing attribute.")
new_decisions.append(
    "A candidate shown alongside cannot_confirm is a LEAD, never a recommendation: the advisor "
    "must not render it as a confirmed fit until the missing attribute is supplied.")
spec["decisions_already_made"] = new_decisions

spec["question_policy"] = {
    "allowed": True,
    "max_per_bike": 3,
    "priority": ["bottom_bracket", "hubs", "brakes", "cassette", "crankset"],
    "options_source": "stock distribution",
    "never_ask": ["a standard the customer cannot read off the part"],
    "lead_semantics": "candidate + cannot_confirm = lead, not a recommendation",
}

# Wave-1 gating: brakes stay unconfirmed until mechanic fixtures exist (external review 2026-10-22).
spec["shipping_gate"] = {
    "rule": "a product may be 'fits' only when every applicable mandatory attribute is verified",
    "brakes": "cannot_confirm until mechanic-reviewed positive AND negative fixtures exist",
    "unaudited_classes_note": "precision 1.000 covers form/brand/speed/range/freehub only; "
                              "rotors and pads were unaudited until audit_wave1.py",
}

io.open(PATH, "w", encoding="utf-8").write(
    json.dumps(spec, ensure_ascii=False, indent=2) + "\n")

print("decisions now:", len(new_decisions))
print("stale line removed:", not any(d.strip().startswith("No questions") for d in new_decisions))
print("added keys: question_policy, shipping_gate")
