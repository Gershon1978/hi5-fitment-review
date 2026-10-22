# -*- coding: utf-8 -*-
"""Correlation study across all 1,519 bikes: what can be inferred from a neighbour part."""
import collections
import json
import re

BIKES = r"C:\Users\Gershon\Desktop\WORKSPACE\mcp\bike-research\data\bikes.json"
bikes = json.load(open(BIKES, encoding="utf-8"))

GROUPS = ["105", "ultegra", "dura-ace", "tiagra", "sora", "claris", "deore", "slx", "xt", "xtr",
          "eagle", "rival", "force", "red", "apex", "tourney", "altus", "acera", "alivio"]


def speeds_of(text):
    t = str(text or "")
    out = set()
    for m in re.finditer(r"(\d{1,2})\s*-?\s*(?:speed|скор)", t, re.I):
        v = int(m.group(1))
        if 5 <= v <= 14:
            out.add(v)
    return out


def features(b):
    dt = b.get("drivetrain") or {}
    blob = json.dumps(b, ensure_ascii=False).lower()
    speed = None
    s = speeds_of(dt.get("cassette")) or speeds_of(dt.get("groupset")) or speeds_of(blob)
    if s:
        speed = max(s)
    group = next((g for g in GROUPS if re.search(r"\b" + g + r"\b", blob)), None)
    bb = dt.get("bottom_bracket") or ""
    bb_std = ("pressfit" if re.search(r"press|pf30|bb86|bb92|t47", bb, re.I)
              else "bsa" if re.search(r"bsa|english|thread|1\.37", bb, re.I) else None)
    typ = (b.get("type") or "").lower()
    axle = "thru" if re.search(r"12\s*[x×]\s*1\d\d|15\s*[x×]\s*1\d\d|thru", blob) else (
        "qr" if re.search(r"\bqr\b|quick release|эксцентрик", blob) else None)
    return {"speed": speed, "group": group, "bb": bb_std, "type": typ, "axle": axle}


F = [features(b) for b in bikes]
print("bikes:", len(F))


def conditional(parent, child, minimum_support=25):
    groups = collections.defaultdict(collections.Counter)
    for f in F:
        if f[parent] and f[child]:
            groups[f[parent]][f[child]] += 1
    out = []
    for key, counts in groups.items():
        total = sum(counts.values())
        if total < minimum_support:
            continue
        value, n = counts.most_common(1)[0]
        out.append((key, value, n / total, total))
    return sorted(out, key=lambda x: -x[2])


for parent, child in [("group", "speed"), ("type", "bb"), ("type", "axle"), ("speed", "axle")]:
    print("\nP(%s | %s)" % (child, parent))
    for key, value, conf, support in conditional(parent, child)[:8]:
        print("   %-12s -> %-6s %.0f%% of %d" % (key, str(value), 100 * conf, support))
