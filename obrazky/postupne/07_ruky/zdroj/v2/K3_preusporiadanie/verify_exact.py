"""exact (point-cloud, 0.2-0.25 mm) clearances of the K3 parts:  usage verify_exact.py L|R
 (a) vs the pan/lift sweep: my points rotated by -phi (phi = -90.3..+90.3, 0.5 deg) against movcloud (stage frame, lift 0..20)
 (b) vs the kept static T4 parts (removed: T_klb, amp/buck, F14, F8, column zone of T_spodok, deck edge |x|>=31)
 (c) mutual clearances of the new parts (pairs that touch by design are skipped)
writes verify_<side>.json"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import k3_parts as KP
import movcloud
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as V
side = sys.argv[1] if len(sys.argv) > 1 else "L"
sg = 1.0 if side == "L" else -1.0
t0 = time.time()
PARTS = KP.parts()
if sg < 0:
    PARTS = {k: v * np.array([-1.0, 1.0, 1.0]) for k, v in PARTS.items()}
# ---------------------------------------------------------------- (a) pan / lift sweep
MP, tags = movcloud.get()
tree = cKDTree(MP)
res = {"side": side, "sweep": {}, "static": {}, "mutual": {}}
for name, P in PARTS.items():
    r = np.hypot(P[:, 0], P[:, 1]); Q = P[r < 38.0]
    if not len(Q):
        res["sweep"][name] = dict(min=None, note="all points r >= 38 (>= 4.6 from any moving part)"); continue
    best = (1e9, None, None)
    for phi in np.arange(-90.3, 90.31, 0.5):
        a = math.radians(-phi); c, s = math.cos(a), math.sin(a)
        R = np.c_[c * Q[:, 0] - s * Q[:, 1], s * Q[:, 0] + c * Q[:, 1], Q[:, 2]]
        d, j = tree.query(R, distance_upper_bound=4.0)
        k = int(np.argmin(d))
        if d[k] < best[0]: best = (float(d[k]), float(phi), (Q[k].round(2).tolist(), str(tags[j[k]])))
    res["sweep"][name] = dict(min=round(best[0], 2) if best[0] < 1e8 else ">4", pan=best[1], at=best[2])
    print("sweep  %-14s %s" % (name, res["sweep"][name]), f"{time.time()-t0:.0f}s", flush=True)
# ---------------------------------------------------------------- (b) kept static parts
sys.path.insert(0, V.T4); cwd = os.getcwd(); os.chdir(V.T4)
PJ = json.load(open("parts.json")); os.chdir(cwd)
REM = {"T_klb_L", "T_klb_P", "zosilnovac", "menic"}
REMP = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14")
stat_pts, stat_tag = [], []
for p in PJ["parts"]:
    n = p["name"]
    if p["group"] != "T" or n in REM or n.startswith(REMP):
        continue
    try:
        tr = V.load(n)
    except Exception:
        continue
    bb = tr.reshape(-1, 3)
    if sg * bb[:, 0].max() < 20.0:
        continue
    S = V.vlib.sample_surface(tr, 0.2)
    if n == "T_spodok":
        X, Y, Z = S[:, 0], S[:, 1], S[:, 2]
        pin = ((np.hypot(X - 27.09, Y - 12.89) <= 4.0) | (np.hypot(X + 21.37, Y + 21.06) <= 4.0)) & (Z >= -62.0)
        tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
        col = (Z >= -82.3) & ((Z >= -78.0) | tub) & ((X >= 26.0) | (X <= -32.4)) & ~pin
        S = S[~col]
    if n == "T_paluba":
        S = S[np.abs(S[:, 0]) < 31.0]
    if n.startswith(("skr_F3a", "pd_F3a", "vl_F3a")) and np.abs(S[:, 0]).mean() > 26.0:
        continue
    S = S[sg * S[:, 0] > 20.0]
    stat_pts.append(S); stat_tag += [n] * len(S)
SP = np.concatenate(stat_pts); stag = np.array(stat_tag)
for extra in ("golier_prstenec",):
    E = V.vlib.sample_surface(V.load(extra, V.BST), 0.2); E = E[sg * E[:, 0] > 20.0]
    SP = np.concatenate([SP, E]); stag = np.concatenate([stag, [extra] * len(E)])
st = cKDTree(SP)
need = {"SERVO": 0.3, "STAT:boss": 0.3, "STAT:tongue": 0.3}
for name, P in PARTS.items():
    d, j = st.query(P, distance_upper_bound=6.0)
    order = np.argsort(d)[:1]
    k = int(order[0])
    near = {}
    for kk in np.argsort(d)[:4000]:
        if d[kk] > 6: break
        t = str(stag[j[kk]]); near[t] = min(near.get(t, 99), float(d[kk]))
    res["static"][name] = dict(min=round(float(d[k]), 2) if d[k] < 6 else ">6", at=P[k].round(2).tolist(),
                               nearest=dict(sorted(((a, round(b, 2)) for a, b in near.items()), key=lambda kv: kv[1])[:5]))
    print("static %-14s %s" % (name, res["static"][name]), flush=True)
# ---------------------------------------------------------------- (c) mutual
skip = {("ROT_V:pinion", "ROT_A:gear"), ("ROT_V:shaft_v", "ROT_V:pinion"), ("ROT_V:coupler", "ROT_V:shaft_v"),
        ("ROT_A:gear", "ROT_A:shaft_a"), ("ROT_V:shaft_v", "BRG:B1"), ("ROT_A:shaft_a", "BRG:A1"), ("ROT_A:shaft_a", "BRG:A2"),
        ("BRG:B1", "STAT:tongue"), ("SERVO", "ROT_V:coupler"), ("STAT:boss", "STAT:tongue")}
names = list(PARTS)
trees = {k: cKDTree(v) for k, v in PARTS.items()}
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if (a, b) in skip or (b, a) in skip: continue
        d, _ = trees[b].query(PARTS[a], distance_upper_bound=5.0)
        m = float(d.min())
        if m < 5.0: res["mutual"][f"{a} | {b}"] = round(m, 2)
print("mutual", json.dumps(res["mutual"], indent=0))
json.dump(res, open(os.path.join(HERE, f"verify_{side}.json"), "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
