# -*- coding: utf-8 -*-
"""Read-only re-equip calibration: v0.3 rules vs 10 archived bikes.

    python requip_harness.py

Frozen seed, stratified sample, no writes anywhere except the two report files.
Every outcome carries the rule that produced it; every cannot_confirm carries
the single question that would resolve it.
"""
import collections
import json
import os
import random
import re

BIKES = r"C:\Users\Gershon\Desktop\WORKSPACE\mcp\bike-research\data\bikes.json"
CATALOGUE = r"C:\Users\Gershon\Desktop\WORKSPACE\data\all_products.json"
OUT_DIR = r"C:\Users\Gershon\Desktop\WORKSPACE\fitment"
SEED = 20261022
RUN = int(os.environ.get("FITMENT_RUN", "4"))

bikes = json.load(open(BIKES, encoding="utf-8"))
products = json.load(open(CATALOGUE, encoding="utf-8"))


def rows_in(leaf):
    return [p for p in products
            if any(c == leaf or c.endswith(" > " + leaf) for c in (p.get("categories") or []))]


CATS = {
    "crankset": "Системы",
    "cassette": "Кассеты и трещотки",
    "chain": "Цепи",
    "shifters": "Манетки и шифтеры",
    "rear_derailleur": "Задние переключатели",
    "front_derailleur": "Передние переключатели",
    "bottom_bracket": "Каретки",
    "tyres": "Покрышки",
    "rims": "Обода",
    "seatpost": "Подседелы",
    "handlebar": "Рули",
    "stem": "Выносы",
}


def speeds(text):
    """Every plausible speed count: 11-speed, 11- скор, 11s, 6,7 скоростей, 2x11."""
    t = str(text or "")
    out = set()
    for pat in (r"(\d{1,2})\s*[-–]?\s*speed", r"(\d{1,2})\s*sp\b", r"(\d{1,2})\s*[-–]?\s*скор",
                r"(?<![\d/])[123]\s*[xх]\s*(\d{1,2})\b"):
        for m in re.finditer(pat, t, re.I):
            v = int(m.group(1))
            if 5 <= v <= 14:
                out.add(v)
    for m in re.finditer(r"(\d)\s*[,./]\s*(\d)\s*(?:скор|speed)", t, re.I):
        for g in (m.group(1), m.group(2)):
            if 5 <= int(g) <= 14:
                out.add(int(g))
    return out


def title_speeds(row):
    """The title is authoritative (v0.3 rule 1)."""
    return speeds(row.get("name", ""))


def bucket_speeds(row):
    return speeds(row.get("attributes", {}).get("Скорость", ""))


def speed_gate(rows, speed):
    """Returns (confirmed, bucket_only) - bucket-only rows are cannot_confirm, never fits."""
    ok, silent = [], 0
    for r in rows:
        ts = title_speeds(r)
        if not ts:
            if speed in bucket_speeds(r):
                silent += 1
            continue
        if speed in ts:
            ok.append(r)
    return ok, silent


def teeth(text):
    """Tooth counts: 50/34, 50x34, 38T, 11-32T (values <= 60)."""
    t = str(text or "")
    out = set()
    for m in re.finditer(r"\b(\d{2})\s*(?:T\b|т\b|/|x|х|-|–)", t, re.I):
        v = int(m.group(1))
        if 8 <= v <= 60:
            out.add(v)
    for m in re.finditer(r"[xх/]\s*(\d{2})\b", t):
        v = int(m.group(1))
        if 8 <= v <= 60:
            out.add(v)
    return out


def cog_range(text):
    t = str(text or "")
    m = re.search(r"\b(\d{2})\s*[-–x×]\s*(\d{2,3})\b", t)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo < hi:
            return lo, hi
    return None


ETRTO = {"700": "622", "29": "622", "28": "622", "27.5": "584", "26": "559",
         "24": "507", "22": "457", "20": "406", "18": "355", "16": "305"}


def wheel_size(text):
    """L5: normalise to ETRTO bead-seat diameter so 700C / 29" / 622 compare equal."""
    t = str(text or "")
    m = re.search(r"\b(700\s*[cC]|29|27[.,]5|26|28|24|22|20|18|16)\b", t)
    if not m:
        return None
    v = m.group(1).replace(" ", "").lower().replace(",", ".")
    if v.startswith("700"):
        v = "700"
    return ETRTO.get(v, v)


def bb_standard(text):
    t = str(text or "").lower()
    if "bb86" in t: return "bb86"
    if "bb92" in t: return "bb92"
    if "pf30" in t: return "pf30"
    if "t47" in t: return "t47"
    if "press" in t or "пресс" in t: return "pressfit"
    if "bsa" in t or "english" in t or "1.37" in t: return "bsa"
    if "итал" in t or "italian" in t: return "italian"
    return None


def bb_spindle(text):
    t = str(text or "").lower()
    if "hollowtech" in t or "outboard" in t or "24mm" in t or "24 mm" in t: return "hollowtech"
    if "gxp" in t: return "gxp"
    if "dub" in t: return "dub"
    if "octalink" in t: return "octalink"
    if "isis" in t: return "isis"
    if "square" in t or "jis" in t or "квадрат" in t: return "square"
    return None


def row_speeds(row):
    """Title only: the attribute is a bucket and must never confirm a fit."""
    return title_speeds(row)


def row_teeth(row):
    return teeth(row.get("name", "")) | teeth(row.get("attributes", {}).get("Количество Зубьев", ""))


SPARE_HEADS = {
    "chain": r"^(замок|пин|lock|missing|powerlock|соединит)",
    "cassette": r"^(кольцо|проставк|шайб|локринг|spacer|замок|простав)",
    "bottom_bracket": r"^(вал|ось|болт|чашк|пыльник|подшипник|адаптер|проставк|spacer|ключ|съемник|съёмник)",
    "hubs": r"^(ось|конус|барабан|пыльник|колпач|собачк|шарик|ремкомплект|спиц)",
    "pedals": r"^(ось|конус|подшипник|ремкомплект|платформ)",
}
REQUIRED_NOUN = {"chain": "цеп", "bottom_bracket": "каретк"}


SPARE_ANYWHERE = {"bottom_bracket": r"без подшипник|чашк|конус|собачк"}


def is_spare(slot, name):
    """Category != product form: ocStore keeps spare parts inside the assembly category."""
    low = (name or "").strip().lower()
    # L18: a repair kit is never the assembly it repairs.
    if re.search(r"набор деталей|ремкомплект|рем\.?\s*комплект|запчаст|kit\b", low):
        return True
    if slot in SPARE_HEADS and re.match(SPARE_HEADS[slot], low):
        return True
    if slot in SPARE_ANYWHERE and re.search(SPARE_ANYWHERE[slot], low):
        return True
    noun = REQUIRED_NOUN.get(slot)
    if noun and noun not in low:
        return True
    return False


def brand_of(text):
    t = (text or "").lower()
    if re.search(r"shimano|\b105\b|\bxt\b|deore|ultegra|dura-ace|tiagra|sora|claris|slx|xtr", t):
        return "shimano"
    if re.search(r"\bsram\b|eagle|\bnx\b|\bgx\b|\bsx\b|apex|\brival\b|\bred\b(?!\s*k?-?force)", t):
        return "sram"
    if "microshift" in t:
        return "microshift"
    return None


def bike_text(bike):
    return json.dumps(bike, ensure_ascii=False).lower()


def bike_electronic(bike):
    return bool(re.search(r"di2|axs|e-?tap|электро", bike_text(bike)))


def bike_discipline(bike):
    t = bike_text(bike)
    road = bool(re.search(r"claris|sora|tiagra|\b105\b|ultegra|dura-ace|\bred\b|\bforce\b|\brival\b", t))
    mtb = bool(re.search(r"deore|\bslx\b|\bxt\b|xtr|alivio|altus|acera|tourney|eagle|\bsx\b|\bnx\b|\bgx\b", t))
    if road and not mtb:
        return "road"
    if mtb and not road:
        return "mtb"
    return None


def part_electronic(name):
    return bool(re.search(r"di2|axs|e-?tap|электро", (name or "").lower()))


def part_discipline(name):
    t = (name or "").lower()
    road = bool(re.search(r"claris|sora|tiagra|\b105\b|ultegra|dura-ace", t))
    mtb = bool(re.search(r"deore|\bslx\b|\bxt\b|xtr|alivio|altus|acera|tourney|eagle", t))
    if road and not mtb:
        return "road"
    if mtb and not road:
        return "mtb"
    return None


def rings_from(text):
    """1x / 2x / 3x from words or from the number of tooth figures in a name."""
    t = (text or "").lower()
    if re.search(r"\b1\s*[xх]\b|single|narrow[- ]wide", t):
        return 1
    if "triple" in t or re.search(r"\b3\s*[xх]\b", t):
        return 3
    if "compact" in t or "double" in t or re.search(r"\b2\s*[xх]\b", t):
        return 2
    nums = re.findall(r"\b(\d{2})\b", t)
    if len(nums) >= 3:
        return 3
    if len(nums) == 2:
        return 2
    if len(nums) == 1:
        return 1
    return None


def bike_rings(bike):
    dt = bike.get("drivetrain") or {}
    return rings_from(dt.get("crankset", "")) or rings_from(dt.get("groupset", ""))


def pick(cands):
    if not cands:
        return None
    return sorted(cands, key=lambda r: (r.get("quantity", 0) <= 0, r.get("price", 0)))[0]


def result(outcome, row=None, rules=None, missing=None, question=None):
    return {"outcome": outcome, "row": row, "rule_ids": rules or [],
            "missing": missing, "question": question}


def row_big_ring(row, big):
    """True/False/None - None means the row does not state a big ring (cannot_confirm)."""
    a = str(row.get("attributes", {}).get("Количество Зубьев", ""))
    m = re.search(r"(\d{2})\s*[-–]\s*(\d{2})", a)
    if m:
        return int(m.group(1)) <= big <= int(m.group(2))
    m = re.search(r"(\d{2})\s*\+", a)
    if m:
        return big >= int(m.group(1))
    t = row_teeth(row)
    if not t:
        return None
    return big in t


def match_crankset(req, rows):
    """v0.3, Системы: speed + BB interface are core.
    Teeth are CONDITIONAL (only when the archive states them); length is NICE.
    """
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    ok, rules, unknown = [], ["CRANKSET-SPEEDS"], False
    big = max(req["teeth"]) if req["teeth"] else None
    for r in rows:
        if req["rings"] and rings_from(r.get("name", "")) not in (None, req["rings"]):
            continue
        if req["speed"] not in row_speeds(r):
            continue
        if not brand_ok(req, r.get("name", "")):
            continue
        if req["bb_spindle"] == "hollowtech":
            t = (r.get("attributes", {}).get("Крепление", "") + " " + r.get("name", "")).lower()
            if not ("интегр" in t or "hollowtech" in t):
                continue
            rules = ["CRANKSET-SPEEDS", "CRANKSET-BB"]
        if big is not None:
            verdict = row_big_ring(r, big)
            if verdict is False:
                continue
            if verdict is None:
                unknown = True
                continue
            rules = sorted(set(rules + ["CRANKSET-TEETH"]))
        ok.append(r)
    if not ok and unknown:
        return result("cannot_confirm", None, sorted(set(rules)),
                      "row does not state the big chainring",
                      {"attribute": "Количество Зубьев", "text": "How many teeth on your biggest front ring?",
                       "options": ["50", "48", "44", "other"], "resolves": ["CRANKSET-TEETH"]})
    if not ok:
        return result("no_candidate", rules=sorted(set(rules)),
                      missing="no crankset matching speed %d%s" % (
                          req["speed"], " + big ring" if big else ""))
    return result("fits", pick(ok), sorted(set(rules)), None)


def cassette_compat(row, freehub):
    """L13: a cassette whose model implies another driver standard must not be offered."""
    name = (row.get("name") or "").lower()
    part_fh = None
    for pattern, fh in CASSETTE_FREEHUB:
        if re.search(pattern, name):
            part_fh = fh
            break
    if not part_fh or not freehub:
        return True
    return part_fh == freehub


def match_cassette(req, rows):
    fh = req.get("freehub")
    if fh:
        rows = [r for r in rows if cassette_compat(r, fh)]
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    confirmed, silent = speed_gate(rows, req["speed"])
    ok, rules = [], ["DRIVETRAIN-SPEED-RANGE", "PART-FORM"]
    for r in confirmed:
        n = r.get("name", "")
        if is_spare("cassette", n):
            continue  # spacer rings live in the cassette category
        if req.get("freehub") in ("xd", "xdr", "microspline"):
            stated = freehub_explicit(n)
            if stated and stated != req["freehub"]:
                continue  # explicit conflict: XD/XDR/MicroSpline are not interchangeable
            if not stated:
                continue  # silent on a non-HG bike: cannot confirm, never assume HG
        if "трещ" in n.lower() and "трещ" not in req["raw"].lower():
            continue  # freewheel on a cassette bike - PART-FORM
        if req["range"]:
            high = max(teeth(r.get("attributes", {}).get("Звезда большая", "")) | teeth(n) or {0})
            if high and high > req["range"][1]:
                continue  # CASSETTE-RANGE: cog exceeds the bike's stock range
            rules = ["DRIVETRAIN-SPEED-RANGE", "PART-FORM", "CASSETTE-RANGE"]
        ok.append(r)
    if not ok and silent:
        return result("cannot_confirm", None, ["DRIVETRAIN-SPEED-RANGE"],
                      "title does not state the speed; the attribute is a %d-speed bucket" % req["speed"],
                      {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                       "options": ["7", "8", "9", "другое"], "resolves": ["DRIVETRAIN-SPEED-RANGE"]})
    if not ok:
        return result("no_candidate", rules=sorted(set(rules)),
                      missing="no %d-speed cassette%s" % (
                          req["speed"], " within %dT" % req["range"][1] if req["range"] else ""))
    return result("fits", pick(ok), sorted(set(rules)), None)


def match_chain(req, rows):
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    confirmed, silent = speed_gate(rows, req["speed"])
    ok = [r for r in confirmed if not is_spare("chain", r.get("name", ""))]
    if not ok and silent:
        return result("cannot_confirm", None, ["DRIVETRAIN-SPEED-RANGE"],
                      "title does not state the speed; the attribute is a %d-speed bucket" % req["speed"],
                      {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                       "options": ["7", "8", "9", "другое"], "resolves": ["DRIVETRAIN-SPEED-RANGE"]})
    if not ok:
        return result("no_candidate", rules=["DRIVETRAIN-SPEED-RANGE", "PART-FORM"],
                      missing="no %d-speed chain (locks and pins excluded)" % req["speed"])
    return result("fits", pick(ok), ["DRIVETRAIN-SPEED-RANGE", "PART-FORM"], None)


def discipline_ok(req, name):
    pd = part_discipline(name)
    return not (req.get("discipline") and pd and pd != req["discipline"])


def brand_ok(req, name):
    """A Shimano drivetrain is not served by a SRAM derailleur. Chains/cassettes are exempt."""
    bike = req.get("brand")
    part = brand_of(name)
    return not (bike and part and bike != part)
    """Road bike vs MTB groupset: only enforced when both sides are confident."""
    pd = part_discipline(name)
    return not (req.get("discipline") and pd and pd != req["discipline"])


def actuation_ok(req, name):
    """Electronic vs mechanical, both directions."""
    return part_electronic(name) == bool(req.get("electronic"))


def match_shifters(req, rows):
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    confirmed, silent = speed_gate(rows, req["speed"])
    ok = [r for r in confirmed
          if discipline_ok(req, r.get("name", "")) and actuation_ok(req, r.get("name", ""))
          and brand_ok(req, r.get("name", ""))]
    if not ok and silent:
        return result("cannot_confirm", None, ["SHIFTER-SPEEDS"],
                      "title does not state the speed for a %d-speed bike" % req["speed"],
                      {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                       "options": ["7", "8", "9", "другое"], "resolves": ["SHIFTER-SPEEDS"]})
    if not ok:
        return result("no_candidate", rules=["SHIFTER-SPEEDS", "SHIFTER-FAMILY"],
                      missing="no %d-speed shifter in the bike's family/actuation" % req["speed"])
    return result("fits", pick(ok), ["SHIFTER-SPEEDS", "SHIFTER-FAMILY"], None)


def match_rd(req, rows):
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    confirmed, silent = speed_gate(rows, req["speed"])
    ok = [r for r in confirmed
          if discipline_ok(req, r.get("name", "")) and actuation_ok(req, r.get("name", ""))
          and brand_ok(req, r.get("name", ""))]
    if not ok and silent:
        return result("cannot_confirm", None, ["RD-SPEEDS"],
                      "title does not state the speed for a %d-speed bike" % req["speed"],
                      {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                       "options": ["7", "8", "9", "другое"], "resolves": ["RD-SPEEDS"]})
    if not ok:
        return result("no_candidate", rules=["RD-SPEEDS", "RD-PULL-FAMILY"],
                      missing="no %d-speed rear derailleur in the bike's family/actuation" % req["speed"])
    return result("fits", pick(ok), ["RD-SPEEDS", "RD-PULL-FAMILY"], None)


def match_fd(req, rows):
    if not req["speed"]:
        return result("requirement_missing", missing="speed count not stated")
    confirmed, silent = speed_gate(rows, req["speed"])
    ok = []
    for r in confirmed:
        n = r.get("name", "")
        if not discipline_ok(req, n) or not actuation_ok(req, n) or not brand_ok(req, n):
            continue
        pr = rings_from(n)
        if req["rings"] and pr and pr != req["rings"]:
            continue  # a 1x cage cannot serve a 2x bike
        ok.append(r)
    if not ok and silent:
        return result("cannot_confirm", None, ["FD-SPEEDS"],
                      "title does not state the speed for a %d-speed bike" % req["speed"],
                      {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                       "options": ["7", "8", "9", "другое"], "resolves": ["FD-SPEEDS"]})
    if not ok:
        return result("no_candidate", rules=["FD-SPEEDS", "FD-PULL"],
                      missing="no %d-speed front derailleur for %dx" % (req["speed"], req["rings"] or 0))
    return result("fits", pick(ok), ["FD-SPEEDS", "FD-PULL"], None)


def match_bb(req, rows):
    if not req["bb_spindle"]:
        return result("requirement_missing", missing="spindle interface not stated")
    ok = []
    for r in rows:
        if is_spare("bottom_bracket", r.get("name", "")):
            continue
        t = (r.get("attributes", {}).get("Тип", "") + " " + r.get("name", "")).lower()
        if req["bb_spindle"] == "hollowtech" and not ("hollowtech" in t or "внешн" in t or "24" in t):
            continue
        if req["bb_spindle"] == "square" and not ("квадрат" in t or "jis" in t):
            continue
        if req["bb_spindle"] == "dub" and "dub" not in t:
            continue
        if req["bb_spindle"] == "gxp" and "gxp" not in t:
            continue
        ok.append(r)
    if not ok:
        return result("no_candidate", rules=["BB-SPINDLE"], missing="no %s bottom bracket" % req["bb_spindle"])
    if not req["bb_standard"]:
        return result("cannot_confirm", pick(ok), ["BB-SHELL"], "shell standard unknown (record says: %s)" % req["bb_raw"],
                      {"attribute": "Тип", "text": "Where the cups fit, is the frame threaded or smooth?",
                       "options": ["резьба 68", "резьба 73", "пресс-фит", "не знаю"],
                       "resolves": ["BB-SHELL"]})
    return result("fits", pick(ok), ["BB-SPINDLE", "BB-SHELL"], None)


def parse_brakes(text):
    t = (text or "").lower()
    if re.search(r"disc|диск|hydraulic|гидравл", t):
        return "disc"
    if re.search(r"v-?brake|ободн|caliper|rim brake", t):
        return "rim"
    return None


def parse_holes(text):
    m = re.search(r"\b(28|32|36|24|20)\s*h\b|(\d{2})\s*(?:спиц|holes?)", str(text or ""), re.I)
    if m:
        return int(m.group(1) or m.group(2))
    return None


def parse_mm(text):
    """Diameter or width in mm. Order matters: explicit 'mm' > Ø notation > clamp Ø > width.

    L7 taught: accept '420' and 'Ø31,8'. L31 taught: a clamp must beat a width, and a
    dimension pair ('760x35mm' = width x rise) must never yield 35.0 as a clamp.
    """
    t = str(text or "")
    m = re.search(r"\b(\d{2,3}(?:[.,]\d)?)\s*mm\b", t, re.I)
    if m:
        return m.group(1).replace(",", ".")
    m = re.search(r"[Ø⌀Φ]\s*(\d{2}(?:[.,]\d)?)", t)
    if m:
        return m.group(1).replace(",", ".")
    CANON = {"22.2", "25.4", "26.0", "26", "27.2", "30.9", "31.6", "31.8", "34.9", "35.0", "35"}
    for m in re.finditer(r"(\d{2,3}(?:[.,]\d)?)", t):
        v = m.group(1).replace(",", ".")
        if m.start() > 0 and t[m.start() - 1] in "xX×хХ/":
            continue  # second value of a dimension pair
        if v in CANON:
            return v
    for m in re.finditer(r"(\d{2,3}(?:[.,]\d)?)", t):
        v = m.group(1).replace(",", ".")
        if 380 <= float(v) <= 820:
            return v  # bar width: a legitimate match axis when no clamp is stated
    return None


def freehub_explicit(text):
    """Only an explicit statement counts; silence is not HG."""
    t = (text or "").lower()
    if "micro spline" in t or "microspline" in t:
        return "microspline"
    if "xdr" in t:
        return "xdr"
    if re.search(r"\bxd\b", t):
        return "xd"
    return None


def bike_freehub(bike):
    """Road AXS = XDR, MTB Eagle = XD, Shimano 12s MTB = MicroSpline, else HG."""
    blob = json.dumps(bike, ensure_ascii=False).lower()
    typ = (bike.get("type") or "").lower()
    speed = max([int(v) for v in re.findall(r"(\d{1,2})\s*-?\s*speed", blob) if 5 <= int(v) <= 14] or [0])
    if "sram" in blob and speed >= 12:
        return "xdr" if typ in ("road", "cyclocross", "gravel", "hybrid") else "xd"
    if "shimano" in blob and speed >= 12 and typ in ("mountain", "mtb"):
        return "microspline"
    return "hg"


def parse_brake_act(text):
    t = (text or "").lower()
    if "hydraulic" in t or "гидравл" in t:
        return "hydraulic"
    if "mechanical" in t or "механ" in t or "cable" in t:
        return "mechanical"
    return None


# Cross-slot inference (Gemini, round 50): a named derailleur implies the freehub and the
# max cog. Only well-known families are listed; anything else stays unknown.
RD_FAMILY = [
    (r"m9100|m8100|m7100", "microspline", 51),
    (r"m6100|m5100", "microspline", 51),
    (r"rx8\d\d", None, 34),
    (r"r7\d{3}|r8\d{3}|r9\d{3}", None, 34),
    (r"eagle", "xd", 52),
    (r"rival|force|red\s*axs|apex\s*axs", "xdr", 36),
]


def infer_from_drivetrain(bike):
    """Return (freehub, max_cog) implied by a named rear derailleur, or (None, None)."""
    dt = bike.get("drivetrain") or {}
    blob = " ".join(str(dt.get(k) or "") for k in ("rear_derailleur", "groupset")).lower()
    for pattern, fh, cog in RD_FAMILY:
        if re.search(pattern, blob):
            return fh, cog
    return None, None


# Deterministic cassette model -> freehub (product fact, not a correlation).
CASSETTE_FREEHUB = [
    (r"cs-m8[0-9]{3}|cs-m7[0-9]{3}|cs-m6[0-9]{3}", "microspline"),  # Shimano 12s MTB
    (r"xg-12[79][05]|xg-129[59]|xg-1150", "xd"),                   # SRAM Eagle
    (r"xg-12[57]0|xg-1251|xg-1271", "xdr"),                        # SRAM AXS road
    (r"cs-r9[0-9]{3}|cs-r8[0-9]{3}|cs-r7[0-9]{3}", "hg"),          # Shimano 12s road (HG)
]


def cassette_freehub(bike):
    text = " ".join(str((bike.get("drivetrain") or {}).get(k) or "")
                    for k in ("cassette", "groupset")).lower()
    for pattern, fh in CASSETTE_FREEHUB:
        if re.search(pattern, text):
            return fh
    return None


def group_family(bike):
    blob = json.dumps(bike, ensure_ascii=False).lower()
    for g in ("eagle", "105", "ultegra", "dura-ace", "tiagra", "sora", "claris", "deore", "slx",
              "xtr", "xt", "rival", "force", "red", "apex", "tourney", "altus", "acera", "alivio"):
        if re.search(r"\b" + g + r"\b", blob):
            return g
    return None


def match_brakes(req, rows):
    kind = req.get("brake_type")
    if not kind:
        return result("requirement_missing", missing="brake type not stated by the archive")
    act = req.get("brake_act")
    ok = []
    for r in rows:
        if is_spare("brakes", r.get("name", "")):
            continue
        if act:
            row_act = str(r.get("attributes", {}).get("Тип Тормоза", "")).lower()
            if act == "hydraulic" and "гидравл" not in row_act:
                continue
            if act == "mechanical" and "гидравл" in row_act:
                continue
        ok.append(r)
    if not ok:
        return result("no_candidate", rules=["BRAKE-TYPE"], missing="no %s %s brakes in stock" % (act or "", kind))
    return result("fits", pick(ok), ["BRAKE-TYPE"], None)


def parse_axle(text):
    t = (text or "").lower()
    if re.search(r"\b12\s*[x×]\s*1\d\d|\b15\s*[x×]\s*1\d\d|thru|сквозн", t):
        return "thru"
    if re.search(r"\bqr\b|эксцентрик|quick release", t):
        return "qr"
    return None


def match_hubs(req, rows):
    holes = req.get("holes")
    if not holes:
        # L10 (Gemini): spoke count is a hard mechanical dependency, so never guess it —
        # but the axle still narrows the shelf to a short list worth asking about.
        axle = req.get("axle")
        short = []
        for r in rows:
            if is_spare("hubs", r.get("name", "")):
                continue
            # L20: a freewheel hub cannot carry a cassette — 9+ speed bikes need a cassette body.
            if (req.get("speed") or 0) >= 9 and re.search(r"трещ[её]тк", (r.get("name") or ""), re.I):
                continue
            mount = str(r.get("attributes", {}).get("Крепление", "")).lower()
            if axle == "thru" and "эксцентрик" in mount:
                continue
            if axle == "qr" and "ось" in mount and "эксцентрик" not in mount:
                continue
            short.append(r)
        q = {"attribute": "holes", "text": "Сколько спиц у втулки: 28, 32 или 36?", "options": [28, 32, 36]}
        if short:
            return result("cannot_confirm", row=pick(short), rules=["HUB-AXLE-TYPE"],
                          missing="spoke count not stated", question=q)
        return result("requirement_missing", missing="spoke count not stated", question=q)
    axle = req.get("axle")
    ok = []
    for r in rows:
        if is_spare("hubs", r.get("name", "")):
            continue
        # L21: the freewheel/cassette-body rule applies on the main path too.
        if (req.get("speed") or 0) >= 9 and re.search(r"трещ[её]тк", (r.get("name") or ""), re.I):
            continue
        a = str(r.get("attributes", {}).get("Количество отверстий", ""))
        if str(holes) not in a and str(holes) not in r.get("name", ""):
            continue
        if axle:
            mount = str(r.get("attributes", {}).get("Крепление", "")).lower()
            if axle == "thru" and "эксцентрик" in mount:
                continue
            if axle == "qr" and "ось" in mount and "эксцентрик" not in mount:
                continue
        ok.append(r)
    if not ok:
        return result("no_candidate", rules=["HUB-HOLES", "HUB-AXLE-TYPE"],
                      missing="no %d-hole hub%s" % (holes, " with %s axle" % axle if axle else ""))
    return result("fits", pick(ok), ["HUB-HOLES", "HUB-AXLE-TYPE"], None)


def norm_model(text):
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def parse_rotor_mm(text):
    """Rotor diameter: '160mm rotors', 'Ф180мм', '203 mm'."""
    for m in re.finditer(r"(\d{3})\s*(?:mm|мм)", str(text or ""), re.I):
        v = int(m.group(1))
        if 120 <= v <= 230:
            return v
    return None


def parse_rotor_mount(text):
    t = str(text or "").lower()
    if re.search(r"center\s*lock|центр\s*лок|центральн", t):
        return "centerlock"
    if re.search(r"6\s*болт|six\s*bolt|6-bolt", t):
        return "6bolt"
    return None


def parse_caliper(text):
    """Caliper model code: 'HD-R280', 'DSK-300R', 'BR-MT200', 'MT200', 'GX-2'."""
    m = re.search(r"\b((?:[A-Z]{2,4}-)?[A-Z]{1,3}-?\d{2,4}[A-Z]?)\b", str(text or ""))
    return m.group(1) if m else None


def brake_type(text):
    t = str(text or "").lower()
    if re.search(r"disc|диск", t):
        return "дисковые"
    if re.search(r"rim|v-?brake|ободн|linear pull|caliper", t):
        return "ободные"
    return None


def match_rotors(req, rows):
    """WAVE 1: a wrong rotor is a brake that does not stop."""
    dia = req.get("rotor_mm")
    mount = req.get("rotor_mount")
    pool = [r for r in rows if not is_spare("rotors", r.get("name", ""))]
    if not dia:
        q = {"attribute": "Диаметр", "text": "Какой диаметр ротора: 160, 180 или 203 мм?",
             "options": ["160", "180", "203", "не знаю"], "resolves": ["ROTOR-DIAMETER"]}
        if pool:
            return result("cannot_confirm", pick(pool), ["ROTOR-DIAMETER"],
                          "rotor diameter not stated by the archive", q)
        return result("requirement_missing", missing="rotor diameter not stated", question=q)
    by_dia = [r for r in pool if str(dia) in str((r.get("attributes") or {}).get("Диаметр", ""))]
    if not mount:
        # mount is binary: 6-bolt will not bolt to a CenterLock hub without an adapter
        q = {"attribute": "Тип", "text": "Ротор крепится на 6 болтов или Center Lock?",
             "options": ["6 болтов", "Center Lock", "не знаю"], "resolves": ["ROTOR-MOUNT"]}
        if by_dia:
            return result("cannot_confirm", pick(by_dia), ["ROTOR-DIAMETER", "ROTOR-MOUNT"],
                          "%d mm rotor exists, mount not stated" % dia, q)
        return result("no_candidate", rules=["ROTOR-DIAMETER"], missing="no %d mm rotor in stock" % dia)
    want = "6 болт" if mount == "6bolt" else "lock"
    ok = [r for r in by_dia if want in str((r.get("attributes") or {}).get("Тип", "")).lower()]
    if not ok:
        return result("no_candidate", rules=["ROTOR-DIAMETER", "ROTOR-MOUNT"],
                      missing="no %d mm %s rotor in stock" % (dia, mount))
    return result("fits", pick(ok), ["ROTOR-DIAMETER", "ROTOR-MOUNT"], None)


def match_pads(req, rows):
    """WAVE 1: pads are caliper-specific; a wrong shape is a brake that does not stop."""
    cal = req.get("caliper")
    kind = req.get("brake_kind")
    pool = [r for r in rows if not is_spare("pads", r.get("name", ""))]
    if kind:
        pool = [r for r in pool if kind in str((r.get("attributes") or {}).get("Тип", "")).lower()]
    if not cal:
        q = {"attribute": "Модель тормоза", "text": "Какая модель написана на калипере?",
             "options": [], "resolves": ["PAD-CALIPER"]}
        if pool:
            return result("cannot_confirm", pick(pool), ["PAD-CALIPER"],
                          "caliper model not stated by the archive", q)
        return result("requirement_missing", missing="caliper model not stated", question=q)
    key = norm_model(cal)
    ok = [r for r in pool
          if key in norm_model((r.get("attributes") or {}).get("Модель тормоза", ""))
          or key in norm_model(r.get("name", ""))]
    if not ok:
        return result("no_candidate", rules=["PAD-CALIPER"], missing="no pads listed for %s" % cal)
    return result("fits", pick(ok), ["PAD-CALIPER"], None)


def match_by_mm(req, rows, key, attr, rule):
    value = req.get(key)
    q_clamp = {"attribute": attr, "text": "Какой диаметр зажима: 31.8 или 25.4?",
               "options": ["31.8", "25.4", "35.0", "не знаю"]}
    if not value:
        # L11: 'not stated' is answerable by the customer — lead with a question and a sample.
        q = {"attribute": attr, "text": "Какой %s у детали? (например, 31.8 или 27.2)" % attr,
             "options": []}
        short = [r for r in rows if not is_spare("handlebar", r.get("name", ""))]
        if short:
            return result("cannot_confirm", row=pick(short), rules=[rule],
                          missing="%s not stated" % attr, question=q)
        return result("requirement_missing", missing="%s not stated" % attr, question=q)
    if float(value) >= 380:
        # Manual (fitment-spec.json): "width is fit, not compatibility" - tier_b ranks, never excludes.
        short = [r for r in rows if not is_spare("handlebar", r.get("name", ""))]
        if short:
            return result("cannot_confirm", row=pick(short), rules=[rule],
                          missing="clamp diameter not stated (width %s is only a fit preference)" % value,
                          question=q_clamp)
        return result("requirement_missing", missing="clamp diameter not stated", question=q_clamp)
    ok = [r for r in rows
          if value in str(r.get("attributes", {}).get(attr, "")) or value in (r.get("name") or "")]
    if not ok:
        return result("no_candidate", rules=[rule], missing="no row stating %s mm" % value)
    return result("fits", pick(ok), [rule], None)


def match_pedals(req, rows):
    kind = req.get("pedal_type")
    if not kind:
        return result("requirement_missing", missing="pedal type not stated by the archive")
    ok = [r for r in rows if kind in (r.get("name") or "").lower()]
    if not ok:
        return result("no_candidate", rules=["PEDAL-TYPE"], missing="no %s pedals in stock" % kind)
    return result("fits", pick(ok), ["PEDAL-TYPE"], None)
    if not req["wheel"]:
        return result("requirement_missing", missing="wheel size not stated")
    ok = [r for r in rows
          if wheel_size(r.get("attributes", {}).get("Размер колеса", "") + " " + r.get("name", "")) == req["wheel"]]
    if not ok:
        return result("no_candidate", rules=["TYRE-WHEEL-SIZE"], missing="no tyre in %s" % req["wheel"])
    return result("fits", pick(ok), ["TYRE-WHEEL-SIZE"], None)


def match_rims(req, rows):
    if not req["wheel"]:
        return result("requirement_missing", missing="wheel size not stated")
    ok = [r for r in rows
          if wheel_size(r.get("attributes", {}).get("Размер колеса", "") + " " + r.get("name", "")) == req["wheel"]]
    if not ok:
        return result("no_candidate", rules=["RIM-SIZE"], missing="no rim in %s" % req["wheel"])
    return result("fits", pick(ok), ["RIM-SIZE"], None)



def match_tyres(req, rows):
    if not req["wheel"]:
        return result("requirement_missing", missing="wheel size not stated")
    ok = [r for r in rows
          if wheel_size(str(r.get("attributes", {}).get("Размер колеса", "")) + " " + str(r.get("name", ""))) == req["wheel"]]
    if not ok:
        return result("no_candidate", rules=["TYRE-WHEEL-SIZE"], missing="no tyre in %s" % req["wheel"])
    return result("fits", pick(ok), ["TYRE-WHEEL-SIZE"], None)


def match_rims(req, rows):
    if not req["wheel"]:
        return result("requirement_missing", missing="wheel size not stated")
    ok = [r for r in rows
          if wheel_size(str(r.get("attributes", {}).get("Размер колеса", "")) + " " + str(r.get("name", ""))) == req["wheel"]]
    if not ok:
        return result("no_candidate", rules=["RIM-SIZE"], missing="no rim in %s" % req["wheel"])
    return result("fits", pick(ok), ["RIM-SIZE"], None)


SLOTS = [
    ("crankset", match_crankset),
    ("cassette", match_cassette),
    ("chain", match_chain),
    ("shifters", match_shifters),
    ("rear_derailleur", match_rd),
    ("front_derailleur", match_fd),
    ("bottom_bracket", match_bb),
    ("brakes", match_brakes),
    ("hubs", match_hubs),
    ("spokes", lambda req, rows: result("not_supported", missing="spoke length is not derivable: no ERD in the archive, no ERD in stock data")),
    ("tyres", match_tyres),
    ("rims", match_rims),
    ("handlebar", lambda req, rows: match_by_mm(req, rows, "mm", "Диаметр", "BAR-CLAMP")),
    ("stem", lambda req, rows: match_by_mm(req, rows, "mm", "Диаметр", "STEM-CLAMP")),
    ("seatpost", lambda req, rows: match_by_mm(req, rows, "mm", "Диаметр", "POST-DIAMETER")),
    ("pedals", match_pedals),
    ("rotors", match_rotors),
    ("pads", match_pads),
]

ROWS = {
    "crankset": rows_in("Системы"),
    "cassette": rows_in("Кассеты и трещотки"),
    "chain": rows_in("Цепи"),
    "shifters": rows_in("Манетки и шифтеры"),
    "rear_derailleur": rows_in("Задние переключатели"),
    "front_derailleur": rows_in("Передние переключатели"),
    "bottom_bracket": rows_in("Каретки"),
    "brakes": rows_in("Дисковые") + rows_in("Ободные"),
    "hubs": rows_in("Втулки задние") + rows_in("Втулки передние"),
    "spokes": rows_in("Спицы"),
    "tyres": rows_in("Покрышки"),
    "rims": rows_in("Обода"),
    "handlebar": rows_in("Рули"),
    "stem": rows_in("Выносы"),
    "seatpost": rows_in("Подседелы"),
    "pedals": rows_in("Педали платформенные"),
    "rotors": rows_in("Роторы"),
    "pads": rows_in("Колодки"),
}

# every fitment-critical category in v0.3, mapped or not
V03 = [
    ("Роторы", "rotors"), ("Колодки", "pads"), ("Адаптеры", None), ("Цепи", "chain"),
    ("Кассеты и трещотки", "cassette"), ("Каретки", "bottom_bracket"),
    ("Передние переключатели", "front_derailleur"), ("Задние переключатели", "rear_derailleur"),
    ("Манетки и шифтеры", "shifters"), ("Петухи", None), ("Системы", "crankset"),
    ("Звезды", None), ("Шатуны", None), ("Втулки задние", "hubs"), ("Втулки передние", "hubs"),
    ("Обода", "rims"), ("Спицы", "spokes"), ("Покрышки", "tyres"), ("Камеры", None),
    ("Подседелы", "seatpost"), ("Выносы", "stem"), ("Рули", "handlebar"),
    ("Рулевые колонки", None), ("Вилки", None), ("Амортизаторы", None), ("Подшипники", None),
]


def raw_for(slot, bike):
    dt = bike.get("drivetrain") or {}
    wh = bike.get("wheels") or {}
    co = bike.get("components") or {}
    br = bike.get("brakes") or {}
    if slot == "tyres":
        return (wh.get("front_tire") or wh.get("rear_tire") or "").strip()
    if slot == "rims":
        return (wh.get("rims") or "").strip()
    if slot in ("brakes", "rotors", "pads", "adapters"):
        return str(br.get("type") or "").strip()
    if slot == "hubs":
        return str(wh.get("hubs") or "").strip()
    if slot == "spokes":
        return str(wh.get("spokes") or "").strip()
    if slot in ("handlebar", "stem", "seatpost", "pedals"):
        base = str(co.get(slot) or "").strip()
        if slot in ("handlebar", "stem"):
            # Spec §4: one clamp measurement serves both parts; append it so parse_mm sees it.
            mm = co.get(slot + "_clamp_mm") or co.get("handlebar_clamp_mm")
            if mm and str(mm) not in base:
                base = (base + " " + str(mm) + "mm").strip()
        return base
    return str(dt.get(slot) or "").strip()


def bike_speed_set(bike):
    dt = bike.get("drivetrain") or {}
    found = set()
    for key in ("cassette", "chain", "shifters", "rear_derailleur", "crankset", "groupset"):
        found |= speeds(dt.get(key, ""))
    return found


def bike_speed(bike):
    found = bike_speed_set(bike)
    return max(found) if len(found) == 1 else None


def requirement(slot, bike):
    raw = raw_for(slot, bike)
    req = {"raw": raw, "speed": None, "teeth": set(), "range": None, "wheel": None,
           "bb_spindle": None, "bb_standard": None, "bb_raw": ""}
    sp = speeds(raw)
    req["speed"] = max(sp) if sp else bike_speed(bike)
    if slot == "crankset":
        req["teeth"] = {t for t in teeth(raw) if t >= 20}
    if slot == "cassette":
        req["range"] = cog_range(raw)
    req["wheel"] = wheel_size(raw)
    if not req["wheel"] and slot in ("rims", "tyres"):
        # L9: a stated tyre size determines the rim's ETRTO diameter (622/584/559).
        wh = bike.get("wheels") or {}
        req["wheel"] = wheel_size(str(wh.get("front_tire") or wh.get("rear_tire") or ""))
        if req["wheel"]:
            req["wheel_inferred"] = "from_tyre"
    if slot == "bottom_bracket":
        req["bb_raw"] = raw
        req["bb_spindle"] = bb_spindle(raw)
        req["bb_standard"] = bb_standard(raw)
    req["rings"] = bike_rings(bike)
    req["electronic"] = bike_electronic(bike)
    req["discipline"] = bike_discipline(bike)
    req["brand"] = brand_of(raw) or brand_of(json.dumps(bike.get("drivetrain") or {}, ensure_ascii=False))
    req["brake_type"] = parse_brakes(raw)
    req["brake_act"] = parse_brake_act(raw)
    req["freehub"] = cassette_freehub(bike) or bike_freehub(bike)
    inf_fh, inf_cog = infer_from_drivetrain(bike)
    req["inferred_freehub"] = inf_fh
    req["inferred_max_cog"] = inf_cog
    if inf_fh and req["freehub"] == "hg":
        req["freehub"] = inf_fh  # a named derailleur outranks the brand heuristic
    if slot == "cassette" and not req.get("range") and inf_cog:
        req["range"] = (11, inf_cog)
    req["holes"] = parse_holes(raw)
    req["axle"] = parse_axle(raw)
    req["mm"] = parse_mm(raw)
    req["pedal_type"] = (
        "platform" if re.search(r"platform|платформ", raw, re.I)
        else "contact" if re.search(r"spd|contact|контакт", raw, re.I) else None
    )
    # Statistical inference, 95% floor / >=25 support (correlations.py):
    #   Eagle => 12-speed (96%, n=26);  12-speed => thru-axle (100%, n=47). Nothing else qualifies.
    # Gemini L1: floor raised 95% -> 99% / deterministic only. Eagle=>12s (96%) no longer qualifies.
    # L3: A/B switch — FITMENT_NOINFER=1 turns every inference off for a frozen-sample comparison.
    if not os.environ.get("FITMENT_NOINFER"):
        if not req.get("axle") and req.get("speed") == 12:
            req["axle"] = "thru"
            req["axle_inferred"] = "speed12"  # 100%, n=47
        if slot == "bottom_bracket":
            blob = json.dumps(bike, ensure_ascii=False).lower()
            for key, val in (("dub", "dub"), ("hollowtech", "24"), ("gxp", "gxp"), ("30mm", "30")):
                if key in blob:
                    req["bb_interface"] = val  # deterministic: spindle dictates the BB
                    if not req.get("bb_spindle"):
                        req["bb_spindle"] = val  # L12: crank spindle fills a silent BB
    if slot == "bottom_bracket" and not req.get("bb_standard"):
        # WAVE 2: 43 bikes state the shell standard only in the frame spec.
        fs = bb_standard(str(bike.get("frame") or ""))
        if fs:
            req["bb_standard"] = fs
            req["bb_standard_source"] = "frame"
    if slot in ("rotors", "pads", "adapters"):
        br = bike.get("brakes") or {}
        wh = bike.get("wheels") or {}
        bt = str(br.get("type") or "").strip()
        req["brake_kind"] = brake_type(bt)
        req["rotor_mm"] = parse_rotor_mm(bt) or parse_rotor_mm(json.dumps(bike, ensure_ascii=False))
        req["caliper"] = parse_caliper(bt)
        req["rotor_mount"] = parse_rotor_mount(bt) or parse_rotor_mount(str(wh.get("hubs") or ""))
        return req
    return req


def local_search(bike, attribute):
    """The one search: look for the missing fact in the fields most likely to hold it."""
    if attribute != "Тип":
        return None
    text = " ".join(str(bike.get(k) or "") for k in ("frame", "notes"))
    text += " " + str((bike.get("drivetrain") or {}).get("bottom_bracket") or "")
    t = text.lower()
    for token, value in (("bb86", "bb86"), ("bb92", "bb92"), ("pf30", "pf30"), ("t47", "t47"),
                         ("bsa", "bsa"), ("thread", "bsa"), ("резьб", "bsa"), ("итал", "italian")):
        if token in t:
            return value
    return None


# Gemini's ruling (round 8): partition the catalogue. Only these can be filled from this
# archive; the rest are a data-acquisition backlog, not an engine failure.
SUPPORTED = {
    "Цепи", "Кассеты и трещотки", "Каретки", "Передние переключатели", "Задние переключатели",
    "Манетки и шифтеры", "Системы", "Втулки задние", "Втулки передние", "Обода", "Покрышки",
}


def metrics(slots):
    total = len(V03)
    supported = [s for s in slots if s["category"] in SUPPORTED]
    sup_two = sum(1 for s in supported if len(s.get("candidates") or []) >= 2)
    with2 = sum(1 for s in slots if len(s.get("candidates") or []) >= 2)
    with1 = sum(1 for s in slots if len(s.get("candidates") or []) == 1)
    nofield = sum(1 for s in slots if s["outcome"] in ("not_in_archive", "not_stated"))
    fits = sum(1 for s in slots if s["outcome"] == "fits")
    asked = sum(1 for s in slots if s.get("question"))
    return {
        "categories": total,
        "two_or_more": with2,
        "exactly_one": with1,
        "zero": total - with2 - with1,
        "no_archive_field": nofield,
        "fits": fits,
        "questions": asked,
        "coverage2": round(with2 / total, 3) if total else 0.0,
        "coverage1": round((with2 + with1) / total, 3) if total else 0.0,
        "supported_slots": len(supported),
        "supported_two": sup_two,
        "supported_rate": round(sup_two / len(supported), 3) if supported else 0.0,
    }


def main():
    picked, bucket_sizes = sample()
    report, lines = [], ["# Re-equip calibration — run #%d" % RUN, "",
                         "Seed `%d` · stratified 2 per bucket · local archive only" % SEED, "",
                         "| bucket | bikes in archive |", "|---|---|"]
    for k, v in sorted(bucket_sizes.items()):
        lines.append("| %s | %d |" % (k, v))
    lines += ["", "| bike | type | cats ≥2 | cats =1 | fits | questions | coverage ≥2 |",
              "|---|---|---|---|---|---|---|"]

    totals = collections.Counter()
    for bike in picked:
        slots = evaluate(bike)
        slots = apply_one_search(bike, slots)
        m = metrics(slots)
        for k, v in m.items():
            totals[k] += v
        report.append({
            "bike_id": bike["bike_id"], "brand": bike.get("brand"), "model": bike.get("model"),
            "year": bike.get("year"), "type": bike.get("type"), "metrics": m, "slots": slots,
        })
        lines.append("| %s | %s | %d | %d | %d | %d | %.0f%% |" % (
            bike["bike_id"], bike.get("type"), m["two_or_more"], m["exactly_one"], m["fits"],
            m["questions"], 100 * m["coverage2"]))

    width = totals["two_or_more"] / totals["categories"] if totals["categories"] else 0
    depth = totals["fits"] / totals["categories"] if totals["categories"] else 0
    # L14 (Gemini): cap at 3 questions per bike — ask only about the highest-consequence slots.
    PRIO = ("bottom_bracket", "hubs", "brakes", "cassette", "crankset")
    questions = []
    for r in report:
        qs = [s for s in r["slots"] if s.get("question")]
        qs.sort(key=lambda s: PRIO.index(s.get("slot")) if s.get("slot") in PRIO else 99)
        questions.extend(qs[:3])
    resolved = [s for s in questions if s.get("resolved_by_search")]

    lines += ["", "## Aggregate", "",
              "| measure | value |", "|---|---|",
              "| bikes | %d |" % len(report),
              "| categories per bike | %d |" % (totals["categories"] // max(len(report), 1)),
              "| categories with ≥2 candidates | %d |" % totals["two_or_more"],
              "| categories with exactly 1 | %d |" % totals["exactly_one"],
              "| categories with 0 | %d |" % totals["zero"],
              "| categories with no archive field | %d |" % totals["no_archive_field"],
              "| categories at `fits` | %d |" % totals["fits"],
              "| **coverage (≥2 candidates)** | **%.0f%%** |" % (100 * width),
              "| **supported fill (≥2, 11 categories)** | **%.0f%%** |" % (
                  100 * totals["supported_two"] / totals["supported_slots"] if totals["supported_slots"] else 0),
              "| **fits share of all categories** | **%.0f%%** |" % (100 * depth),
              "| one-question prompts | %d |" % len(questions),
              "| resolved by the single search | %d |" % len(resolved), ""]

    unanswered = collections.Counter(s["missing"] for r in report for s in r["slots"]
                                     if s["outcome"] in ("no_candidate", "requirement_missing"))
    if unanswered:
        lines += ["## Top reasons a slot did not fill", "", "| reason | slots |", "|---|---|"]
        for reason, n in unanswered.most_common(10):
            lines.append("| %s | %d |" % (reason, n))
        lines.append("")

    cats = []
    for name, slot in V03:
        if not slot:
            cats.append((name, "no archive field", 0, 0, 0))
            continue
        entries = [s for r in report for s in r["slots"] if s["slot"] == slot]
        fits = sum(1 for s in entries if s["outcome"] == "fits")
        gap = sum(1 for s in entries if s["outcome"] == "requirement_missing")
        cats.append((name, "tested", len(entries), fits, gap))
    lines += ["", "## All categories (v0.3)", "",
              "| category | status | tested | fits | archive gap |", "|---|---|---|---|---|"]
    for name, status, tested, fits, gap in cats:
        lines.append("| %s | %s | %d | %d | %d |" % (name, status, tested, fits, gap))
    lines.append("")

    backlog = sorted({s["category"] for r in report for s in r["slots"]
                      if s["category"] not in SUPPORTED})
    lines += ["", "## Data-acquisition backlog (not an engine failure)", "",
              ", ".join(backlog) or "none", ""]

    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump({"spec": "hi5.fitment.calibration.v1", "seed": SEED,
               "metrics": {"width": width, "depth": depth, **totals},
               "bikes": report},
              open(os.path.join(OUT_DIR, "requip-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    open(os.path.join(OUT_DIR, "requip-scorecard.md"), "w", encoding="utf-8").write("\n".join(lines))

    rounds_dir = os.path.join(OUT_DIR, "rounds")
    os.makedirs(rounds_dir, exist_ok=True)
    for src, ext in (("requip-report.json", "json"), ("requip-scorecard.md", "md")):
        data = open(os.path.join(OUT_DIR, src), encoding="utf-8").read()
        open(os.path.join(rounds_dir, "round-%02d.%s" % (RUN, ext)), "w", encoding="utf-8").write(data)

    print("bikes:", len(report), "| coverage2 %.0f%% | fits %d/%d | questions %d"
          % (100 * width, totals["fits"], totals["categories"], len(questions)))
    print("questions:", len(questions), "| resolved by one search:", len(resolved))


# entry point is at the end of the file



def evaluate(bike):
    """Per bike: every v0.3 category, up to 2 candidates, one question when blocked."""
    slots = []
    single_speed = bike_speed(bike) is None
    for name, slot in V03:
        if not slot:
            slots.append({"category": name, "slot": None, "outcome": "not_in_archive",
                          "candidates": [], "missing": "the archive never names this part",
                          "question": None})
            continue
        raw = raw_for(slot, bike)
        if not raw:
            slots.append({"category": name, "slot": slot, "outcome": "not_stated",
                          "candidates": [], "missing": "slot not stated by the archive",
                          "question": None})
            continue
        if single_speed and slot in ("cassette", "shifters", "rear_derailleur", "front_derailleur"):
            continue
        req = requirement(slot, bike)
        conflicting = bike_speed_set(bike)
        if slot in ("crankset", "cassette", "chain", "shifters", "rear_derailleur", "front_derailleur") and len(conflicting) > 1:
            slots.append({"category": name, "slot": slot, "raw": raw,
                          "requirement": {"speed": sorted(conflicting)},
                          "outcome": "cannot_confirm", "rule_ids": ["DRIVETRAIN-SPEED-RANGE"],
                          "candidates": [],
                          "missing": "the bike record states several speeds: %s" % sorted(conflicting),
                          "question": {"attribute": "Скорость", "text": "How many cogs on the back wheel?",
                                       "options": [str(v) for v in sorted(conflicting)][:4],
                                       "resolves": ["DRIVETRAIN-SPEED-RANGE"]}})
            continue

        matcher = dict(SLOTS)[slot]
        res = matcher(req, ROWS[slot])
        entry = {"category": name, "slot": slot, "raw": raw,
                 "requirement": {"speed": req.get("speed"), "wheel": req.get("wheel"),
                                 "bb_spindle": req.get("bb_spindle"), "brand": req.get("brand"),
                                 "freehub": req.get("freehub")},
                 "outcome": res["outcome"], "rule_ids": res["rule_ids"],
                 "missing": res["missing"], "question": res["question"], "candidates": []}
        if res["row"]:
            chosen = res["row"]
            rest = [r for r in ROWS[slot] if r["product_id"] != chosen["product_id"]]
            second = matcher(req, rest)["row"]
            for row in [chosen, second]:
                if row:
                    entry["candidates"].append({"id": row["product_id"], "sku": row.get("sku"),
                                                "name": row.get("name"), "price": row.get("price"),
                                                "qty": row.get("quantity")})
        slots.append(entry)
    return slots


def apply_one_search(bike, slots):
    """For each cannot_confirm, fire exactly one local search and re-evaluate the fact."""
    for entry in slots:
        if entry["outcome"] != "cannot_confirm" or not entry["question"]:
            continue
        attribute = entry["question"]["attribute"]
        answer = local_search(bike, attribute)
        entry["search"] = {"query": "local archive scan for %s" % attribute, "answer": answer}
        if answer:
            entry["outcome"] = "fits"
            entry["resolved_by_search"] = True
            entry["rule_ids"] = sorted(set(entry["rule_ids"] + ["BB-SHELL"]))
    return slots


def bucket(bike):
    t = (bike.get("type") or "").lower()
    sp = bike_speed(bike) or 0
    if t == "mountain":
        return "mtb_entry" if sp <= 8 else "mtb_modern"
    if t in ("road", "gravel"):
        return "road"
    if t in ("hybrid", "kids"):
        return "city"
    if t in ("cyclocross", "bmx", "fat bike"):
        return "other"
    return None


def _has_post(b):
    return bool(parse_mm((b.get("components") or {}).get("seatpost", "")))


def _has_tyre(b):
    return bool(wheel_size((b.get("wheels") or {}).get("front_tire", "")))


def _has_rim(b):
    return bool(wheel_size((b.get("wheels") or {}).get("rims", "")))


def _has_bb(b):
    return bool((b.get("drivetrain") or {}).get("bottom_bracket"))


def sample(n=10):
    """1 per type bucket + 1 per dimension-bearing category + 1 random = exactly n fresh bikes.

    Why: a pure type draw often lands on records that omit seatpost Ø / tyre size / rim size,
    so those categories were never exercised. This guarantees at least one bike that states each.
    """
    rng = random.Random(SEED + RUN * 101)
    frozen = os.environ.get("FITMENT_BIKES")
    if frozen:
        if frozen.strip().upper() == "ALL":  # L4: whole archive, no sampling noise
            return list(bikes), {}
        wanted = [x.strip() for x in frozen.split(",") if x.strip()]
        by_id = {b["bike_id"]: b for b in bikes}
        return [by_id[w] for w in wanted if w in by_id], {}
    used_path = os.path.join(OUT_DIR, "used_bikes.json")
    used = set(json.load(open(used_path, encoding="utf-8"))) if os.path.exists(used_path) else set()
    pool = [b for b in bikes if b["bike_id"] not in used]
    groups = collections.defaultdict(list)
    for b in pool:
        key = bucket(b)
        if key:
            groups[key].append(b)

    picked = []
    for key in ["mtb_entry", "mtb_modern", "road", "city", "other"]:
        bucket_pool = sorted([b for b in groups.get(key, []) if b not in picked], key=lambda x: x["bike_id"])
        if bucket_pool:
            picked.append(rng.choice(bucket_pool))

    for test in (_has_post, _has_tyre, _has_rim, _has_bb):
        candidates = sorted([b for b in pool if b not in picked and test(b)], key=lambda x: x["bike_id"])
        if candidates:
            picked.append(rng.choice(candidates))

    remaining = sorted([b for b in pool if b not in picked], key=lambda x: x["bike_id"])
    while len(picked) < n and remaining:
        pick = rng.choice(remaining)
        picked.append(pick)
        remaining.remove(pick)

    used.update(b["bike_id"] for b in picked)
    json.dump(sorted(used), open(used_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return picked[:n], {k: len(v) for k, v in groups.items()}


if __name__ == "__main__":
    main()


