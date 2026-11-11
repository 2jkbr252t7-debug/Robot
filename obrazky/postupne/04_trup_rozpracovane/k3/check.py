"""K3 checks: extra-pose sweep, critical clearances, arm limit table, CoG/tipping.  Writes check_parts/*.json
(merged into check.json by merge_check.py).  Usage: python check.py extra|gaps|arms|cog"""
import sys, json, time, math, itertools, os
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

HERE = "/tmp/claude-0/gapwf/fin/T1/k3"
os.makedirs(f"{HERE}/check_parts", exist_ok=True)
L = T.Layout(f"{HERE}/layout.json")
G = {c["name"]: c["group"] for c in L.comps}

EXTRA = [  # own poses: pan +-85 at lift 0 / 12.5 / 20 with the tilt limits of the B table, arms, J1 extremes
    {"pan": 85, "tilt": 5}, {"pan": -85, "tilt": -10},
    {"pan": 85, "lift": 12.5, "tilt": 30}, {"pan": -85, "lift": 12.5, "tilt": -40},
    {"pan": 85, "lift": 20, "tilt": -40}, {"pan": -85, "lift": 20, "tilt": 40},
    {"pan": 45, "lift": 10, "tilt": 25}, {"pan": -30, "lift": 17.5, "tilt": 40},
    {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20},            # awake pose
    {"armR": -45, "armL": -45, "j1": 150}, {"armR": 0, "armL": 0, "j1": -150},
    {"armR": 100, "armL": 100}, {"armR": 100, "armL": 100, "lift": 20, "tilt": 40},
    {"armR": 180, "armL": 180, "pan": 85, "lift": 12.5, "tilt": -40},
    {"armR": 180, "armL": 180, "pan": -85, "lift": 20, "tilt": 40},
    {"j1": 150, "armR": 90, "armL": 90, "pan": -85, "lift": 20, "tilt": 40},
    {"j1": -150, "armR": 180, "armL": 180, "pan": 85, "lift": 20},
    {"j1": 150, "armR": -45, "armL": 0, "pan": 85, "lift": 20, "tilt": -40},
    {"armR": 135, "armL": 135, "pan": 85, "lift": 20},
]


def min_gap(pose, A, B, skip_allowed=True):
    SA = {n: L.shape(n, pose) for n in A}
    SB = {n: L.shape(n, pose) for n in B}
    BA = {n: s.bounding_box() for n, s in SA.items()}
    BBx = {n: s.bounding_box() for n, s in SB.items()}
    best = (1e9, None, None)
    cand = []
    for a in A:
        for b in B:
            if a == b or (skip_allowed and frozenset((a, b)) in L.allow) or (a.startswith("B_") and b.startswith("B_")):
                continue
            x, y = BA[a], BBx[b]
            dx = max(0, x.min.X - y.max.X, y.min.X - x.max.X)
            dy = max(0, x.min.Y - y.max.Y, y.min.Y - x.max.Y)
            dz = max(0, x.min.Z - y.max.Z, y.min.Z - x.max.Z)
            cand.append((math.sqrt(dx * dx + dy * dy + dz * dz), a, b))
    cand.sort()
    for lb, a, b in cand:
        if lb >= best[0]:
            break
        d = SA[a].distance_to(SB[b])
        if d < best[0]:
            best = (d, a, b)
    return round(best[0], 2), best[1], best[2]


def names(groups, excl=()):
    return [c["name"] for c in L.comps if c["group"] in groups and c["name"] not in excl]


mode = sys.argv[1]
t0 = time.time()
if mode == "extra":
    out = []
    for i, p in enumerate(EXTRA):
        cl = L.clashes(p, only_moving=True)
        out.append({"pose": p, "clashes": cl})
        print(i, p, cl, round(time.time() - t0), flush=True)
    json.dump(out, open(f"{HERE}/check_parts/extra.json", "w"), indent=1)

elif mode == "gaps":
    res = {}
    Pn = names(("P",)); Ln = names(("L",)); Tn = names(("T",)); Bn = names(("B",)); Hn = names(("H",))
    Tstatic_no_ring = [n for n in Tn if n != "B_golier_prstenec"]
    # (a) pan stage vs static torso
    for pan in (-85, -42.5, 0, 42.5, 85):
        for lift in (0, 20):
            p = {"pan": pan, "lift": lift}
            res[f"P+L vs T  pan {pan} lift {lift}"] = min_gap(p, Pn + Ln, Tstatic_no_ring)
            print(list(res.items())[-1], round(time.time() - t0), flush=True)
    res["collar disc vs ring (B frame seam, by design 0.25)"] = min_gap({"pan": 85}, ["B_golier_kotuc"], ["B_golier_prstenec"], False)
    # (b) lift: neck + tongue vs pan stage
    for lift in (0, 5, 10, 15, 20):
        res[f"L vs P  lift {lift}"] = min_gap({"lift": lift}, Ln, [n for n in Pn if n != "P_klika"])
        print(list(res.items())[-1], round(time.time() - t0), flush=True)
    res["L_jazyk vs P_klika (crank at rest; pin in slot by design)"] = min_gap({}, ["L_jazyk"], ["P_klika"], False)
    # (c) J1: torso vs base
    for j1 in (0, 75, 150, -150):
        res[f"T(+P,L,H) vs B  j1 {j1}"] = min_gap({"j1": j1}, Tn + Pn, Bn)
        print(list(res.items())[-1], round(time.time() - t0), flush=True)
    # (d) arms vs torso / base / each other
    AR = names(("AR",)); AL = names(("AL",))
    for a in (-45, 0, 45, 90, 135, 180):
        res[f"AR vs T  arm {a}"] = min_gap({"armR": a}, AR, Tn)
        res[f"AR vs B  arm {a}  j1 0/90"] = min(min_gap({"armR": a}, AR, Bn), min_gap({"armR": a, "j1": 90}, AR, Bn))
        print(list(res.items())[-2:], round(time.time() - t0), flush=True)
    res["AR vs AL  arms 180/180"] = min_gap({"armR": 180, "armL": 180}, AR, AL)
    # (e) head vs torso top over the tilt table
    for lift, tdn, tup in ((0, 5, -10), (10, 25, -35), (12.5, 30, -40), (15, 15, -20), (20, 40, -40)):
        for tilt in (tdn, tup):
            for pan in (0, 85):
                p = {"pan": pan, "lift": lift, "tilt": tilt}
                res[f"H vs T  lift {lift} tilt {tilt} pan {pan}"] = min_gap(p, Hn, ["T_shell", "B_golier_prstenec"])
        print(list(res.items())[-1], round(time.time() - t0), flush=True)
    json.dump(res, open(f"{HERE}/check_parts/gaps.json", "w"), indent=1)

elif mode == "arms":
    HEAD = ["B_hlava", "B_usi", "B_ram_tvar"]
    ARM = ["A_R_skrupina", "A_R_krytka"]
    states = []
    for lift, tdn, tup in ((0, 5, -10), (12.5, 30, -40), (20, 40, -40)):
        for pan in (-85, -60, -30, 0, 30, 60, 85):
            states.append((pan, lift, (tdn, 0, tup)))
    table = []

    def ok(pose):
        return min_gap(pose, ARM, HEAD, False)[0] >= 2.0

    for pan, lift, tilts in states:
        worst = 180.0
        for tilt in tilts:
            base = {"pan": pan, "lift": lift, "tilt": tilt}
            if ok(dict(base, armR=180)):
                lim = 180.0
            else:
                lo, hi = 90.0, 180.0
                if not ok(dict(base, armR=lo)):
                    lo = 60.0
                for _ in range(7):
                    mid = (lo + hi) / 2
                    if ok(dict(base, armR=mid)):
                        lo = mid
                    else:
                        hi = mid
                lim = math.floor(lo)
            worst = min(worst, lim)
        table.append({"pan": pan, "lift": lift, "tilt_range": [tilts[2], tilts[0]], "armR_max": worst,
                      "armL_max_at_pan": -pan})
        print(table[-1], round(time.time() - t0), flush=True)
    json.dump(table, open(f"{HERE}/check_parts/arms.json", "w"), indent=1)

elif mode == "cog":
    cands = {"rest": {}, "awake": {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20},
             "arms fwd, head down": {"armR": 90, "armL": 90, "lift": 20, "tilt": 40},
             "arms 100 fwd, lift 20 tilt 40": {"armR": 100, "armL": 100, "lift": 20, "tilt": 40},
             "arms back -45, head up": {"armR": -45, "armL": -45, "lift": 20, "tilt": -40},
             "j1 90 arms fwd": {"j1": 90, "armR": 90, "armL": 90, "lift": 20, "tilt": 40},
             "j1 45 arms fwd": {"j1": 45, "armR": 90, "armL": 90, "lift": 20, "tilt": 40},
             "arms up (pan 85)": {"armR": 180, "armL": 180, "pan": 85, "lift": 20}}
    res = {k: dict(T.Layout.tipping(L, p, accel_g=0.15), pose=p) for k, p in cands.items()}
    M, cog, rows = L.cog({})
    grp = {}
    for n, m in rows:
        grp.setdefault(G[n], 0.0)
        grp[G[n]] += m
    res["_mass_rows"] = rows
    res["_mass_by_group"] = {k: round(v, 1) for k, v in grp.items()}
    json.dump(res, open(f"{HERE}/check_parts/cog.json", "w"), indent=1)
    for k, v in res.items():
        if not k.startswith("_"):
            print(k, v)
    print(res["_mass_by_group"])
print("done", mode, round(time.time() - t0))
