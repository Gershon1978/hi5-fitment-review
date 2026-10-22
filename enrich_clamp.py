# -*- coding: utf-8 -*-
"""L31 merge tool: apply OEM-spec enrichment to the bike archive, with provenance.

Input: JSONL, one record per line:
  {"bike_id": "...", "field": "handlebar_clamp_mm", "value": 31.8,
   "source_url": "https://...", "retrieved_at": "2026-10-22", "method": "oem_spec"}

Rules enforced (DATA_ACQUISITION_SPEC.md §4, §6):
  - every record needs a source_url and a retrieved_at; no exceptions
  - additive only: never overwrite a value already stated on the bike record
  - value must be in the field's allowed domain
  - dry_run by default; a backup is written before any change
"""
import argparse
import json
import os
import shutil
import sys

BIKES = r"C:\Users\Gershon\Desktop\WORKSPACE\mcp\bike-research\data\bikes.json"
DOMAIN = {
    "handlebar_clamp_mm": {"22.2", "25.4", "26.0", "31.8", "35.0"},
    "stem_clamp_mm": {"22.2", "25.4", "26.0", "31.8", "35.0"},
    "stem_steerer": {"28.6", "31.8", "38.1"},
    "bb_shell": {"bsa68", "bsa73", "bb86", "bb92", "pf30", "t47"},
    "rim_internal_mm": None,  # any integer 13..45
}
TARGET_KEY = {"handlebar_clamp_mm": "components", "stem_clamp_mm": "components",
              "stem_steerer": "components", "bb_shell": "drivetrain",
              "rim_internal_mm": "wheels"}


def check(rec):
    for k in ("bike_id", "field", "value", "source_url", "retrieved_at", "method"):
        if not rec.get(k) and rec.get(k) != 0:
            return "missing %s" % k
    if rec["field"] not in DOMAIN:
        return "unknown field"
    if rec["method"] not in ("oem_spec", "retailer", "measured"):
        return "bad method"
    if not str(rec["source_url"]).startswith("http"):
        return "source_url is not a URL"
    dom = DOMAIN[rec["field"]]
    if dom is not None and str(rec["value"]) not in dom:
        return "value %s outside domain" % rec["value"]
    if rec["field"] == "rim_internal_mm" and not (13 <= float(rec["value"]) <= 45):
        return "rim width outside 13..45"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    bikes = json.load(open(BIKES, encoding="utf-8"))
    by_id = {b["bike_id"]: b for b in bikes}
    accepted, rejected, dupes = [], [], []

    for line in open(args.jsonl, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        err = check(rec)
        if err:
            rejected.append((rec.get("bike_id"), err))
            continue
        bike = by_id.get(rec["bike_id"])
        if bike is None:
            rejected.append((rec["bike_id"], "bike not in archive"))
            continue
        bucket = bike.setdefault(TARGET_KEY[rec["field"]], {})
        if bucket.get(rec["field"]) not in (None, ""):
            dupes.append((rec["bike_id"], rec["field"], bucket[rec["field"]]))
            continue
        bucket[rec["field"]] = rec["value"]
        bike.setdefault("enrichment", {})[rec["field"]] = {
            "value": rec["value"], "source_url": rec["source_url"],
            "retrieved_at": rec["retrieved_at"], "method": rec["method"]}
        accepted.append((rec["bike_id"], rec["field"], rec["value"]))

    print("accepted %d | rejected %d | already stated %d" % (len(accepted), len(rejected), len(dupes)))
    for r in rejected[:10]:
        print("  REJECT", r)
    for d in dupes[:5]:
        print("  KEEP-EXISTING", d)

    if not accepted:
        print("nothing to write")
        return 0
    if not args.apply:
        print("dry run — rerun with --apply to write")
        return 0
    shutil.copy(BIKES, BIKES + ".bak")
    json.dump(bikes, open(BIKES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written to %s (backup at .bak)" % BIKES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
