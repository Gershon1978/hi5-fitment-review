# -*- coding: utf-8 -*-
"""Wave 2 probe: does the bike record already state a bottom-bracket shell standard?"""
import collections
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requip_harness as H

PATTERNS = [
    ("bsa", r"\bbsa\b|english thread|резьбов|1[.,]37"),
    ("bb86", r"bb86"),
    ("bb92", r"bb92"),
    ("pf30", r"pf30|pressfit\s*30"),
    ("t47", r"\bt47\b"),
    ("pressfit", r"press[-\s]?fit|пресс[-\s]?фит"),
]

hits = collections.Counter()
fields = collections.Counter()
none = 0
examples = []

for b in H.bikes:
    found = None
    where = None
    for key, val in b.items():
        if not isinstance(val, str):
            continue
        low = val.lower()
        for name, pat in PATTERNS:
            if re.search(pat, low):
                found, where = name, key
                break
        if found:
            break
    # also the drivetrain sub-dict
    if not found:
        dt = b.get("drivetrain") or {}
        for key, val in dt.items():
            low = str(val).lower()
            for name, pat in PATTERNS:
                if re.search(pat, low):
                    found, where = name, "drivetrain." + key
                    break
            if found:
                break
    if found:
        hits[found] += 1
        fields[where] += 1
        if len(examples) < 6:
            examples.append((b["bike_id"], where, found, str(b.get(where))[:70]))
    else:
        none += 1

print("bikes with a stated shell standard:", sum(hits.values()), "of", len(H.bikes))
print("by standard:", hits.most_common())
print("by field:", fields.most_common())
print("no statement anywhere:", none)
for e in examples:
    print("  ", e)
