# -*- coding: utf-8 -*-
"""Rounds L16-L30: walk the whole archive 100 bikes at a time and audit every fit.

Resumable: state lives in precision_state.json, so a killed process loses at most one chunk.
"""
import collections
import json
import os

import requip_harness as H

STATE = "precision_state.json"
CHUNK = int(os.environ.get("VAL_CHUNK", "100"))

st = (json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE)
      else {"done": 0, "bikes": 0, "fits": 0, "false": 0, "classes": {}, "examples": []})
classes = collections.Counter(st["classes"])

start = st["done"]
batch = H.bikes[start:start + CHUNK]

for bike in batch:
    st["bikes"] += 1
    slots = H.evaluate(bike)
    bike_speeds = H.bike_speed_set(bike)
    bike_brand = H.brand_of(H.bike_text(bike))
    # L26: outcomes per slot, so over-rejection (no_candidate) is visible, not just false fits.
    oc = st.setdefault("outcomes", {})
    for res in slots:
        if isinstance(res, dict):
            k = "%s|%s" % (res.get("slot"), res.get("outcome"))
            oc[k] = oc.get(k, 0) + 1
    for res in slots:
        if not isinstance(res, dict) or res.get("outcome") != "fits":
            continue
        for row in (res.get("candidates") or []):
            slot = res.get("slot")
            name = row.get("name") or ""
            st["fits"] += 1
            why = None
            if H.is_spare(slot, name):
                why = "form"
            else:
                ps = set(H.row_speeds(row))
                if bike_speeds and ps and not (bike_speeds & ps):
                    why = "speed"
                elif (bike_brand and slot != "bottom_bracket"
                      and H.brand_of(name) and H.brand_of(name) != bike_brand):
                    # only a difference from the slot's OWN OEM brand is a defect (mixed-brand bikes exist)
                    raw_brand = H.brand_of(str(H.raw_for(slot, bike) or ""))
                    if raw_brand and raw_brand != H.brand_of(name):
                        why = "brand"
                elif slot == "cassette":
                    fh = H.cassette_freehub(bike) or H.bike_freehub(bike)
                    if not H.cassette_compat(row, fh):
                        why = "freehub"
            if why:
                st["false"] += 1
                classes[why] += 1
                if len(st["examples"]) < 40:
                    st["examples"].append({"bike": bike["bike_id"], "slot": slot,
                                           "part": name[:70], "class": why})

st["done"] = start + len(batch)
st["classes"] = dict(classes)
json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

prec = (st["fits"] - st["false"]) / st["fits"] if st["fits"] else 1.0
print("chunk %d/%d | bikes %d/%d | fits %d | false %d | precision %.3f"
      % (st["done"], len(H.bikes), st["bikes"], len(H.bikes), st["fits"], st["false"], prec))
print("classes:", dict(classes))
