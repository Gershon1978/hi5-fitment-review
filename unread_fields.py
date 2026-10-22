# -*- coding: utf-8 -*-
"""Audit archive fields the engine never reads: what mechanical facts are hiding there?

Zero acquisition risk: every hit is already stored on the bike record.
"""
import collections
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requip_harness as H

PATTERNS = {
    "axle_thru": r"\b(?:12|15|20)\s*[x×]\s*(?:100|110|142|148|150|157|197)\b",
    "axle_qr": r"\b(?:9|10)\s*[x×]\s*(?:100|135)\b|qr\b|quick[-\s]?release",
    "headset_std": r"\b(?:EC|ZS|IS)\s?\d{2}\b|integrated headset|tapered steerer",
    "rotor_mm": r"\b(?:140|160|180|203)\s*(?:mm|мм)\b|rotor",
    "freehub": r"micro\s?spline|xdr\b|\bxd\b",
    "bb_shell": r"\bbsa\b|bb86|bb92|pf30|\bt47\b|press[-\s]?fit",
}

# fields the engine already reads through raw_for()
USED = {"drivetrain", "components", "wheels.rims", "wheels.front_tire", "wheels.rear_tire",
        "wheels.hubs", "wheels.spokes", "brakes.type"}

hits = collections.Counter()
field_hits = collections.defaultdict(collections.Counter)
examples = collections.defaultdict(list)


def flat(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = prefix + k
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        elif isinstance(v, str) and v.strip():
            out[key] = v
    return out


for b in H.bikes:
    for field, text in flat(b).items():
        low = text.lower()
        for name, pat in PATTERNS.items():
            if re.search(pat, low):
                hits[name] += 1
                field_hits[name][field] += 1
                if len(examples[name]) < 3 and field not in USED:
                    examples[name].append((b["bike_id"], field, text[:60]))
                break

print("bikes with a hit, per fact:")
for name, n in hits.most_common():
    print("  %-12s %4d  fields: %s" % (name, n, field_hits[name].most_common(4)))

print("\nexamples from fields the engine does NOT read:")
for name in examples:
    for e in examples[name]:
        print("  %-12s %s" % (name, e))

unread = collections.Counter()
for name, fc in field_hits.items():
    for field, n in fc.items():
        if field not in USED:
            unread[field] += n
print("\nunread fields by total hits:", unread.most_common(10))
