# -*- coding: utf-8 -*-
"""Evaluate the whole archive at once and dump one compact JSON (no sampling noise)."""
import collections
import json
import os

import requip_harness as H

NOINFER = bool(os.environ.get("FITMENT_NOINFER"))
STATE = "full_state.json"
state = (json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE)
         else {"done": 0, "per_category": {}, "fits_total": 0, "fits_by_bike": {}})
per_cat = collections.defaultdict(collections.Counter)
for k, v in state["per_category"].items():
    per_cat[k].update(v)

start = state["done"]
CHUNK = int(os.environ.get("FITMENT_CHUNK", "250"))
for bike in H.bikes[start:start + CHUNK]:
    slots = H.evaluate(bike)
    n_fit = 0
    for res in slots:
        slot = str(res.get("slot")) if isinstance(res, dict) else "None"
        outcome = res.get("outcome") if isinstance(res, dict) else str(res)
        per_cat[slot][outcome] += 1
        if outcome == "fits":
            n_fit += 1
    state["fits_total"] += n_fit
    state["fits_by_bike"][bike["bike_id"]] = n_fit
    state["done"] += 1

state["per_category"] = {k: dict(v) for k, v in per_cat.items()}
state["noinfer"] = NOINFER
json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
done = state["done"]
print("progress %d/%d bikes | fits %d" % (done, len(H.bikes), state["fits_total"]))

cov = [v for v in state["fits_by_bike"].values()]
summary = {
    "bikes": done,
    "noinfer": NOINFER,
    "fits_total": state["fits_total"],
    "fits_per_bike": round(state["fits_total"] / done, 2) if done else 0,
    "bikes_with_ge2": sum(1 for c in cov if c >= 2),
    "per_category": {k: dict(v) for k, v in per_cat.items()},
}
json.dump(summary, open("full_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
