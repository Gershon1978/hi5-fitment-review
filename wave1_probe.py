# -*- coding: utf-8 -*-
"""Wave 1 reconnaissance: what the catalogue states about rotors/pads/adapters,
and what the bike record states about brakes."""
import collections
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requip_harness as H

for cat in ("Роторы", "Колодки", "Адаптеры"):
    try:
        rows = H.rows_in(cat)
    except Exception as e:
        print(cat, "ERROR", e)
        continue
    attrs = collections.Counter()
    for r in rows:
        for k in (r.get("attributes") or {}):
            attrs[k] += 1
    print("\n== %s: %d rows ==" % (cat, len(rows)))
    print("  attribute coverage:", attrs.most_common(8))
    for r in rows[:3]:
        print("   -", (r.get("name") or "")[:80])
        print("     ", json.dumps(r.get("attributes") or {}, ensure_ascii=False)[:220])

print("\n== bike brake records ==")
seen = 0
for b in H.bikes:
    br = b.get("brakes") or {}
    if br:
        print(" ", b["bike_id"], "|", json.dumps(br, ensure_ascii=False)[:140])
        seen += 1
        if seen >= 6:
            break
print("bikes with any brakes data:", sum(1 for b in H.bikes if b.get("brakes")))
