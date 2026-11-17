"""m04 - inventory of the T4 torso from parts.json + the module part files: printed parts, fastener kinds, inserts,
pins, magnets, tapes, FPC; counts per group; merged T_ram + T_spodok envelope and print-volume check; masses.
Run: /opt/venv/cad/bin/python m04_inventory.py"""
import json, re
from collections import Counter, defaultdict
from zj_lib import T4, dump, say

d = json.load(open(T4 + "/parts.json"))
P = d["parts"]
fast = {}
for f in ("parts_ram.json", "parts_pan.json", "parts_obal.json"):
    m = json.load(open(T4 + "/" + f))
    L = m["parts"] if isinstance(m, dict) and "parts" in m else m
    if isinstance(L, dict):
        L = list(L.values())
    for p in L:
        if p.get("fastener"):
            fast[p["name"]] = p["fastener"]

cat = defaultdict(list)
for p in P:
    n = p["name"]
    if p.get("printed"):
        cat["printed"].append(n)
    elif n.startswith(("skr", "skrutka", "Z_skrutka")):
        cat["screws"].append(n)
    elif n.startswith(("vl_", "vlozka")):
        cat["inserts"].append(n)
    elif n.startswith(("kolik", "cap_")):
        cat["pins"].append(n)
    elif n.startswith("magnet"):
        cat["magnets"].append(n)
    elif n.startswith(("ptfe", "pena", "tesnenie")):
        cat["tapes_foams"].append(n)
    elif n.startswith(("pruzina", "Z_pruzina")):
        cat["springs"].append(n)
    else:
        cat["bought_other"].append(n)
res = {"n_parts": len(P), "counts": {k: len(v) for k, v in cat.items()}, "lists": cat}

# screw kinds (size strings) from the fastener records + spec for those without records
kinds = Counter()
for n in cat["screws"]:
    f = fast.get(n, {})
    s = f.get("size")
    if s is None:
        s = {"skrutka_klb": "M2x10 socket (F8)", "skrutka_led": "M2x6 thread-forming (F13)",
             "skrutka_repro": "M2x6 thread-forming (F13)", "Z_skrutka_M8": "M8x25 (dummy stand)"}.get(
            re.sub(r"_[LP]?\d$", "", n), "?")
    kinds[s] += 1
res["screw_kinds"] = dict(kinds)
res["n_screw_kinds"] = len(kinds)
say("screw kinds", len(kinds), dict(kinds))

# merged T_ram + T_spodok
bb = {p["name"]: p["bbox"] for p in P}
mass = {p["name"]: p.get("mass_g") for p in P}
a, b = bb["T_ram"], bb["T_spodok"]
# parts.json bbox order is [x0, x1, y0, y1, z0, z1]
mb = [min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]), min(a[4], b[4]), max(a[5], b[5])]
size = sorted([mb[1] - mb[0], mb[3] - mb[2], mb[5] - mb[4]])
vol = (211.68, 118.37, 220.0)          # Saturn 4 Ultra 16K (the smaller of the two, T4_zivica Z0)
fits = size[0] <= sorted(vol)[0] and size[1] <= sorted(vol)[1] and size[2] <= sorted(vol)[2]
# T_ram was PETG (1.27 g/cm3) in parts.json -> resin 1.15
m_ram_resin = mass["T_ram"] / 1.27 * 1.15
res["merge_T_ram_T_spodok"] = dict(bbox=[round(v, 2) for v in mb], size_sorted=[round(v, 1) for v in size],
                                   build_volume=vol, fits=fits,
                                   mass_g=round(mass["T_spodok"] + m_ram_resin, 1),
                                   removes=["6 x F2 M2.5 countersunk", "6 x M2.5 inserts (walls 1.1..1.4, M03)",
                                            "6 countersinks over a 0.77 floor (M05)", "assembly step 3"])
say("merge", res["merge_T_ram_T_spodok"])
res["printed_masses_g"] = {n: mass[n] for n in cat["printed"]}
dump("m04_inventory.json", res)
