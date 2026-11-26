"""JUDGE: exact assembly-path clearances (3-D distance from a point to the swept ray of the other set).
  cap      : side cap T_bok removed along +sg X; new parts (except plug cartridge parts) must clear its sweep
  servo_in : servo (+ cable stub, coupler) slid out along +sg X with the cap off; kept static parts must clear its sweep
  lower    : T5 group (T_stred + front stack + inserts + frame magnets) withdrawn along +Z; new parts must clear
usage: paths.py <variant> <L|R>  -> paths_<variant>_<side>.json"""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo as G, variants
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib  # noqa
T4 = "/tmp/claude-0/gapwf/fin/T4"
var, side = sys.argv[1], sys.argv[2]
sg = 1.0 if side == "L" else -1.0
if var.startswith("B2"):
    import geo_b2 as GB  # noqa
    import intern_boss as IB  # noqa
    P0, _ = GB.parts()
    P0["STAT_boss"] = IB.boss_b2()
    if var == "B2col":
        import os as _o
        P0["STAT_colfill"] = np.load(_o.path.join(HERE, "colfill_%s.npz" % side))["P"].astype(float) * np.array([1.0 if side == "L" else -1.0, 1, 1])
else:
    _prm, _ex = variants.get(var)
    P0, _ = G.parts(_prm)
    if _ex: P0.update(_ex(_prm))
PARTS = P0 if sg > 0 else G.mirror(P0)
sys.path.insert(0, T4); os.chdir(T4)
import t4_assembly as A  # noqa
T5 = [s for s in A.STEPS if s["id"] == "T5"][0]["move"]
PJ = json.load(open("parts.json"))


def _reduce(P, ax, sense, cell=0.05, keep="min"):
    """one point per cell of the plane normal to ax: the extreme one along sense (keep='min': smallest sense*coord)"""
    o = [i for i in range(3) if i != ax]
    I = np.floor(P[:, o] / cell).astype(np.int64)
    I -= I.min(0)
    key = I[:, 0] * (I[:, 1].max() + 1) + I[:, 1]
    v = sense * P[:, ax] * (1 if keep == "min" else -1)
    order = np.lexsort((v, key))
    k2 = key[order]; first = np.r_[True, k2[1:] != k2[:-1]]
    return P[order][first]


def ray_min(Q, S, ax, sense, R=0.8):
    """min over q in Q of the distance to the union of rays {s + t*sense*e_ax, t >= 0}, s in S (>= R reported as R)"""
    o = [i for i in range(3) if i != ax]
    S = _reduce(S, ax, sense, keep="min")          # the most 'behind' ray origin per cell dominates
    Q = _reduce(Q, ax, sense, keep="max")          # the most 'ahead' query point per cell dominates
    tr = cKDTree(S[:, o])
    best = (R, None)
    for c0 in range(0, len(Q), 4000):
        Qc = Q[c0:c0 + 4000]
        lists = tr.query_ball_point(Qc[:, o], R)
        for i, li in enumerate(lists):
            if not li: continue
            li = np.asarray(li)
            dp = np.hypot(*(S[li][:, o] - Qc[i, o]).T)
            ahead = sense * (Qc[i, ax] - S[li, ax])
            d = np.where(ahead >= 0, dp, np.hypot(dp, ahead))
            k = int(d.argmin())
            if d[k] < best[0]: best = (float(d[k]), Qc[i].round(2).tolist())
    return best


res = {}
bok = "T_bok_L" if sg > 0 else "T_bok_P"
SB = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{bok}.stl"), 0.12)
res["cap"] = {}
for n, P in PARTS.items():
    if n.startswith(("ROT_A", "BRG_A", "STAT_keeper", "STAT_post")): continue
    Q = P[np.abs(P[:, 0]) > 30]
    b = ray_min(Q, SB, 0, sg)
    res["cap"][n] = dict(min=round(b[0], 2), at=b[1])
    print("cap", n, res["cap"][n], flush=True)
# servo insertion: static kept parts vs the servo's outward sweep
REM = {"T_klb_L", "T_klb_P", "zosilnovac", "menic", bok}
REMP = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14", "skr_F3a_2", "pd_F3a_2", "vl_F3a_2")
SS = []
for p in PJ["parts"]:
    nm = p["name"]
    if p["group"] != "T" or nm in REM or nm.startswith(REMP): continue
    bb = p["bbox"]
    if (bb[3] if sg > 0 else -bb[0]) < 18: continue
    S = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{nm}.stl"), 0.15)
    if nm == "T_spodok":
        X, Y, Z = S[:, 0], S[:, 1], S[:, 2]
        pin = (np.hypot(X - 27.09, Y - 12.89) <= 4.0) | (np.hypot(X + 21.37, Y + 21.06) <= 4.0)
        tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
        col = (Z >= -82.3) & ((Z >= -78.0) | tub) & ((X >= 26.0) | (X <= -32.4)) & ~pin
        S = S[~col]
    if nm == "T_paluba":
        S = S[np.abs(S[:, 0]) <= 31.0]
    SS.append(S)
SS = np.concatenate(SS + [v for k, v in PARTS.items() if k.startswith(("STAT_leg", "STAT_shelf", "STAT_strut", "STAT_web"))])
res["servo_in"] = {}
SLIDE = ("SERVO", "SERVO_cable") if var.startswith("B2") else ("SERVO", "SERVO_cable", "ROT_V_coupler")
for n in SLIDE:
    P = PARTS[n]
    lo, hi = P.min(0) - 2, P.max(0) + 2
    m = (SS[:, 1] > lo[1]) & (SS[:, 1] < hi[1]) & (SS[:, 2] > lo[2]) & (SS[:, 2] < hi[2])
    b = ray_min(SS[m], P, 0, sg)        # static point p ahead of a servo point along the outward slide direction
    res["servo_in"][n] = dict(min=round(b[0], 2), at=b[1])
    print("servo_in", n, res["servo_in"][n], flush=True)
# B2: the one-piece printed pinion-shaft is inserted along -sg X LIFTED by B2['lift'] (servo already in, cap off, plug out,
# U-insert / keeper / post not yet there); static = kept T4 parts (cap off) + column + tongue + boss + the servo in place
if var.startswith("B2"):
    lift = GB.B2["lift"]
    SS2 = np.concatenate([SS] + [v for k, v in PARTS.items() if k in ("STAT_tongue", "STAT_boss", "SERVO", "SERVO_cable",
                                                                     "STAT_strut", "STAT_leg_back_ext")])
    res["pinion_shaft_in"] = {}
    for n in ("ROT_V_coupler", "ROT_V_shaft", "ROT_V_collar", "ROT_V_pinion"):
        P = GB.lifted(PARTS[n], lift)
        lo, hi = P.min(0) - 2, P.max(0) + 2
        m = (SS2[:, 1] > lo[1]) & (SS2[:, 1] < hi[1]) & (SS2[:, 2] > lo[2]) & (SS2[:, 2] < hi[2])
        if not m.any():
            res["pinion_shaft_in"][n] = dict(min=">2 (no static part near the path)", at=None)
            print("pinion_shaft_in", n, res["pinion_shaft_in"][n], flush=True)
            continue
        b = ray_min(SS2[m], P, 0, sg)
        res["pinion_shaft_in"][n] = dict(min=round(b[0], 2), at=b[1])
        print("pinion_shaft_in", n, res["pinion_shaft_in"][n], flush=True)
        # vertical lift itself (+Z by lift) from the final place: static points above the part
        b2 = ray_min(SS2[m], PARTS[n], 2, +1, R=lift + 0.8)
        res["pinion_shaft_in"][n + "_vertical"] = dict(min=round(b2[0], 2), at=b2[1])
        print("pinion_shaft_lift", n, res["pinion_shaft_in"][n + "_vertical"], flush=True)
# T_stred lowering: T5 parts withdrawn +Z
S5 = np.concatenate([vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{nm}.stl"), 0.15) for nm in T5])
S5 = S5[sg * S5[:, 0] > 15]
res["lower"] = {}
for n, P in PARTS.items():
    b = ray_min(P[::2], S5, 2, +1)
    res["lower"][n] = dict(min=round(b[0], 2), at=b[1])
    print("lower", n, res["lower"][n], flush=True)
json.dump(res, open(os.path.join(HERE, f"paths_{var}_{side}.json"), "w"), indent=1)
print("done")
