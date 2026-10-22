# -*- coding: utf-8 -*-
"""Independent Wave-1 auditor: rotors and pads.

Written deliberately WITHOUT the harness's parsers: facts are re-extracted here from
bikes.json with separate regexes, so a shared blind spot cannot hide a false fit.
Checks only the safety-critical claims the general auditor does not cover.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPORT = "requip-report.json"
BIKES = r"C:\Users\Gershon\Desktop\WORKSPACE\mcp\bike-research\data\bikes.json"

report = json.load(open(REPORT, encoding="utf-8"))
bikes = {b["bike_id"]: b for b in json.load(open(BIKES, encoding="utf-8"))}

DIA = re.compile(r"\b(1[4-9]\d|20\d)\s*(?:mm|мм)\b", re.I)


def bike_rotor_mm(bike):
    """Diameter only from the brake line - never from fork/frame text."""
    bt = str((bike.get("brakes") or {}).get("type") or "")
    if not re.search(r"rotor|диск|disc", bt, re.I):
        return None
    m = DIA.search(bt)
    return int(m.group(1)) if m else None


def bike_mount(bike):
    txt = " ".join(str((bike.get(k) or {}).get("type") or "") for k in ("brakes",)) + " " + \
          str((bike.get("wheels") or {}).get("hubs") or "")
    low = txt.lower()
    if re.search(r"center\s*lock|центр\s*лок", low):
        return "centerlock"
    if re.search(r"6\s*болт|6-bolt|six bolt", low):
        return "6bolt"
    return None


def bike_brake_kind(bike):
    bt = str((bike.get("brakes") or {}).get("type") or "").lower()
    if re.search(r"disc|диск", bt):
        return "диск"
    if re.search(r"rim|v-brake|ободн|linear pull|caliper", bt):
        return "ободн"
    return None


def caliper_model(bike):
    bt = str((bike.get("brakes") or {}).get("type") or "")
    m = re.search(r"\b((?:[A-Z]{2,4}-)?[A-Z]{1,3}-?\d{2,4}[A-Z]?)\b", bt)
    return m.group(1) if m else None


checked = bad = unverified = 0
examples = []
by_slot = {"rotors": 0, "pads": 0}

for entry in report["bikes"]:
    bike = bikes.get(entry.get("bike_id") or entry.get("bike", {}).get("bike_id", ""))
    if not bike:
        continue
    for slot in entry.get("slots", []):
        name_slot = slot.get("slot")
        if name_slot not in ("rotors", "pads") or slot.get("outcome") != "fits":
            continue
        for part in slot.get("candidates") or []:
            checked += 1
            by_slot[name_slot] += 1
            attrs = part.get("attributes") or {}
            pname = (part.get("name") or "").lower()
            why = None

            if name_slot == "rotors":
                want = bike_rotor_mm(bike)
                got_m = re.search(r"(1[4-9]\d|20\d)", str(attrs.get("Диаметр", "")))
                got = int(got_m.group(1)) if got_m else None
                if want is None or got is None:
                    unverified += 1
                elif want != got:
                    why = "rotor %s mm on a %s mm bike" % (got, want)
                mount = bike_mount(bike)
                ptype = str(attrs.get("Тип", "")).lower()
                if not why and mount == "6bolt" and "lock" in ptype:
                    why = "CenterLock rotor on a 6-bolt bike"
                if not why and mount == "centerlock" and "болт" in ptype:
                    why = "6-bolt rotor on a CenterLock bike"

            else:  # pads
                kind = bike_brake_kind(bike)
                ptype = str(attrs.get("Тип", "")).lower()
                if kind is None:
                    unverified += 1
                elif kind == "диск" and "ободн" in ptype:
                    why = "rim pad on a disc brake"
                elif kind == "ободн" and "диск" in ptype:
                    why = "disc pad on a rim brake"
                if not why:
                    cal = caliper_model(bike)
                    listed = str(attrs.get("Модель тормоза", "")).lower()
                    if cal and listed and cal.lower() not in listed:
                        why = "caliper %s not in pad listing" % cal

            if why:
                bad += 1
                if len(examples) < 8:
                    examples.append((entry.get("bike_id"), name_slot, part.get("name", "")[:60], why))

print("WAVE-1 AUDIT: checked %d rotor/pad fits (rotors %d, pads %d)" % (checked, by_slot["rotors"], by_slot["pads"]))
print("false: %d | unverifiable (missing bike fact): %d" % (bad, unverified))
for e in examples:
    print("  -", e)
