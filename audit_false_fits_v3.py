# -*- coding: utf-8 -*-
"""Audit every candidate in every round: form, brand, speed, range, freehub."""


def speeds_in(text):
    """L31: read '2/3 x8/9 скор' as {8, 9} but never read a tooth range as a speed.

    '11-34, 8 speed' means 8 speeds; the 11 is a cog, not a gear count.
    """
    t = str(text or "").lower()
    out = set()
    for m in re.finditer(r"speed|скор", t):
        head = t[max(0, m.start() - 14):m.start()]
        # Drop tooth ranges like "11-34" but keep real speed ranges like "9-11".
        head = re.sub(r"(\d{1,2})\s*[-\u2013]\s*(\d{2,3})",
                      lambda mm: " " if int(mm.group(2)) >= 15 else mm.group(0), head)
        nums = [int(x) for x in re.findall(r"\d{1,2}", head)]
        for n in nums[-3:]:
            if 5 <= n <= 14:
                out.add(n)
    return sorted(out)
import json
import re

REPORT = r"C:\Users\Gershon\Desktop\WORKSPACE\fitment\requip-report.json"
BIKES = r"C:\Users\Gershon\Desktop\WORKSPACE\mcp\bike-research\data\bikes.json"

d = json.load(open(REPORT, encoding="utf-8"))
bikes = {b["bike_id"]: b for b in json.load(open(BIKES, encoding="utf-8"))}
DRIVETRAIN = {"crankset", "cassette", "chain", "shifters", "rear_derailleur", "front_derailleur"}


def brand(text):
    t = (text or "").lower()
    if re.search(r"shimano|\b105\b|\bxt\b|deore|ultegra|dura-ace|tiagra|sora|claris|slx|xtr", t):
        return "shimano"
    if re.search(r"\bsram\b|eagle|\bnx\b|\bgx\b|\bsx\b|apex|\brival\b|\bred\b(?!\s*k?-?force)", t):
        return "sram"
    if "microshift" in t:
        return "microshift"
    return None


def freehub_of(text):
    t = (text or "").lower()
    if "micro spline" in t or "microspline" in t:
        return "microspline"
    if "xdr" in t:
        return "xdr"
    if re.search(r"\bxd\b", t):
        return "xd"
    return "hg"


def bike_freehub(bike):
    blob = json.dumps(bike, ensure_ascii=False).lower()
    typ = (bike.get("type") or "").lower()
    speed = max([int(v) for v in re.findall(r"(\d{1,2})\s*-?\s*speed", blob) if 5 <= int(v) <= 14] or [0])
    if "sram" in blob and speed >= 12:
        return "xdr" if typ in ("road", "cyclocross", "gravel", "hybrid") else "xd"
    if "shimano" in blob and speed >= 12 and typ in ("mountain", "mtb"):
        return "microspline"
    return "hg"


false_fits, checked = [], 0
for bike in d["bikes"]:
    src = bikes.get(bike["bike_id"], {})
    bike_brand = brand(json.dumps(src, ensure_ascii=False))
    bike_fh = bike_freehub(src)
    stock = json.dumps(src.get("drivetrain") or {}, ensure_ascii=False)
    rng = re.search(r"(\d{2})\s*[x×]\s*(\d{2,3})|(\d{2})\s*[-–]\s*(\d{2,3})", stock)
    stock_high = int(rng.group(2) or rng.group(4)) if rng else None
    bs = speeds_in(stock)
    bike_speed = max(bs) if bs else None

    for slot in bike["slots"]:
        if slot["outcome"] not in ("fits", "cannot_confirm"):
            continue
        for part in (slot.get("candidates") or []):
            checked += 1
            name = part.get("name") or ""
            low = name.lower()
            reasons = []
            if slot["slot"] == "chain" and re.match(r"^(замок|пин|lock|powerlock)", low):
                reasons.append("PART-FORM: lock/pin is not a chain")
            if slot["slot"] == "cassette" and re.match(r"^(кольцо|проставк|шайб|spacer)", low):
                reasons.append("PART-FORM: spacer ring is not a cassette")
            if slot["slot"] == "bottom_bracket" and re.search(r"^(вал|ось)|без подшипник|чашк", low):
                reasons.append("BB: spindle/cup-set is not a bottom bracket")
            if slot["slot"] in DRIVETRAIN and bike_brand and brand(name) and brand(name) != bike_brand:
                reasons.append("family: %s part on a %s bike" % (brand(name), bike_brand))
            ps = speeds_in(low)
            if bike_speed and ps and bike_speed not in ps:
                if not (slot["slot"] == "chain" and set(ps) <= {6, 7, 8} and bike_speed <= 8):
                    reasons.append("SPEED: %d-speed part on a %d-speed bike" % (max(ps), bike_speed))
            if slot["slot"] == "cassette" and stock_high:
                highs = [int(v) for v in re.findall(r"\b(\d{2,3})\b", name) if 20 <= int(v) <= 60]
                if highs and max(highs) > stock_high:
                    reasons.append("RANGE: %dT exceeds %dT" % (max(highs), stock_high))
            if slot["slot"] == "cassette" and freehub_of(name) != bike_fh:
                reasons.append("FREEHUB: %s part on an %s bike" % (freehub_of(name), bike_fh))
            if reasons:
                false_fits.append((bike["bike_id"], slot["category"], name[:60], "; ".join(reasons)))

print("candidates checked:", checked, "| false fits:", len(false_fits))
for b, cat, part, why in false_fits[:12]:
    print("  -", b, "|", cat, "|", part, "|", why)
print("precision:", round((checked - len(false_fits)) / checked, 3) if checked else 0)
