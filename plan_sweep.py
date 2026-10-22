# -*- coding: utf-8 -*-
"""L31 option 2: build the targeted enrichment worklist (2015+ road/MTB, clamp unstated)."""
import collections
import json

import requip_harness as H

ROADISH = ("road", "mountain", "mtb", "gravel", "cyclocross", "fat bike", "e-bike", "e-mtb")

work = []
for b in H.bikes:
    typ = (b.get("type") or "").lower()
    year = b.get("year")
    try:
        year = int(year)
    except (TypeError, ValueError):
        continue
    if year < 2015 or not any(t in typ for t in ROADISH):
        continue
    co = b.get("components") or {}
    need = []
    for slot in ("handlebar", "stem"):
        raw = str(co.get(slot) or "").strip()
        if raw and not H.parse_mm(raw):
            need.append(slot)
    if need:
        work.append({"bike_id": b["bike_id"], "year": year, "type": typ,
                     "slots": need, "source": b.get("source") or "", "brand": b.get("brand") or ""})

with_url = sum(1 for w in work if str(w["source"]).startswith("http"))
print("targets: %d bikes | with a source URL: %d | without: %d" % (len(work), with_url, len(work) - with_url))
print("by year:", collections.Counter(w["year"] for w in work).most_common(5))
print("by type:", collections.Counter(w["type"] for w in work).most_common(5))
print("slots: bars only %d | stems only %d | both %d"
      % (sum(1 for w in work if w["slots"] == ["handlebar"]),
         sum(1 for w in work if w["slots"] == ["stem"]),
         sum(1 for w in work if len(w["slots"]) == 2)))
json.dump(work, open("sweep_worklist.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for w in work[:8]:
    print("  ", w["bike_id"], w["year"], w["type"], w["slots"], (w["source"] or "-")[:50])
