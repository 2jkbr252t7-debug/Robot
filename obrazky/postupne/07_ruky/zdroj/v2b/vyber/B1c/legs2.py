"""JUDGE: per-z-band clearance of the sketched column legs (left) to the kept static T4 parts (exact surface samples),
to the T_stred lowering path (exact rays, T5 group withdrawn +Z) and to the side-cap removal path (+X rays)."""
import sys, os, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3"); import vlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo as G
T4 = "/tmp/claude-0/gapwf/fin/T4"
PJ = json.load(open(f"{T4}/parts.json"))
sys.path.insert(0, T4); cwd = os.getcwd(); os.chdir(T4); import t4_assembly as A; os.chdir(cwd)
T5 = [s for s in A.STEPS if s["id"] == "T5"][0]["move"]
REM = {"T_klb_L", "T_klb_P", "zosilnovac", "menic"}
REMP = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14", "skr_F3a_2", "pd_F3a_2", "vl_F3a_2")
SP, ST = [], []
for p in PJ["parts"]:
    n = p["name"]
    if p["group"] != "T" or n in REM or n.startswith(REMP) or p["bbox"][3] < 18: continue
    S = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{n}.stl"), 0.15)
    if n == "T_spodok":
        X, Y, Z = S.T
        pin = (np.hypot(X - 27.09, Y - 12.89) <= 4.0)
        tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
        S = S[~((Z >= -82.3) & ((Z >= -78.0) | tub) & (X >= 26.0) & ~pin)]
    if n == "T_paluba": S = S[S[:, 0] <= 31.0]
    S = S[S[:, 0] > 20]; SP.append(S); ST += [n] * len(S)
SP = np.concatenate(SP); ST = np.array(ST); tree = cKDTree(SP)
S5 = np.concatenate([vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{nm}.stl"), 0.15) for nm in T5]); S5 = S5[S5[:, 0] > 20]
SB = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/T_bok_L.stl"), 0.15)
def ray(Q, S, ax, R=1.0):
    o = [i for i in range(3) if i != ax]; t = cKDTree(S[:, o]); best = R
    for i, li in enumerate(t.query_ball_point(Q[:, o], R)):
        if not li: continue
        li = np.asarray(li); dp = np.hypot(*(S[li][:, o] - Q[i, o]).T); ah = Q[i, ax] - S[li, ax]
        best = min(best, float(np.where(ah >= 0, dp, np.hypot(dp, ah)).min()))
    return best
legs = {"back": (13.8, 19.5, 34.4, 43.5, 31.5), "front": (-24.0, -19.2, 34.4, 43.0, 33.0)}
for nm, (y0, y1, xa, xb, xlow) in legs.items():
    print(nm)
    for z0 in np.arange(-80.0, -28.0, 2.0):
        x0 = xlow if z0 + 2 <= -48 else xa
        Q = G.box(x0, xb, y0, y1, z0, z0 + 2, 0.25)
        d, j = tree.query(Q)
        k = d.argmin()
        print("  z %6.1f..%6.1f  static %.2f (%s at %s)  lower %.2f  cap %.2f" % (z0, z0 + 2, d[k], ST[j[k]], Q[k].round(1), ray(Q[::3], S5, 2), ray(Q[::3], SB, 0)))
