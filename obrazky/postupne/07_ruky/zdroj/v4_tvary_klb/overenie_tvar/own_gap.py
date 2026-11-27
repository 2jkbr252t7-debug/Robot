"""own arm - torso gap for the R4 arm variants (CAD venv).
torso 'mesh' : the REAL meshes the v2/v3 scene uses on the left side: R1/img_v2/work/stl_mod/T_bok_L.stl (side cover with the
               r 14 socket), R1/img_v2/work/stl/zatka.stl (static plug, face recessed 1.0), stl_mod/T_spodok.stl and every
               other non-removed T4 part with points near the arm; points with r < 7.0 about the shoulder axis are dropped
               (plug ring / centre pass through the arm's D14 hole by design: checked as sliding pairs by fit.py)
torso 'ana'  : approved analytic exterior t4_common.x_surface (own grid h 0.15) + socket rim r 14 + plug face r <= 13.5
               recessed 1.0 (same physical model as rec1)
arm          : own parametric skin (armsurf_own, h 0.1, whole arm) + analytic inside test for the sign
swing        : -51, -45 .. +135 (1 deg, 0.5 deg from 128), 140.5, 142
usage: own_gap.py B0,B1,...  -> out/gap_<vids>.json"""
import sys, os, json, time, math, glob
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS; import stlio
VB = AS.VB
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); import t4_common as C
t0 = time.time()
YA, ZA = 3.0, -17.0
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else ["B0", "B1", "B2", "B3"]
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"; T4S = "/tmp/claude-0/gapwf/fin/T4/stl"
REMOVED = {"T_klb_L", "T_klb_P", "zosilnovac"}
REMOVED_PRE = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14")


def near(P):
    r = np.hypot(P[:, 1] - YA, P[:, 2] - ZA)
    return (P[:, 0] > 38.0) & (r < 80.0) & (r >= 7.0)


mesh_pts = []; used = []
for f in sorted(glob.glob(T4S + "/*.stl")):
    n = os.path.basename(f)[:-4]
    if n in REMOVED or n.startswith(REMOVED_PRE) or n.endswith("_P") or n == "T_bok_P":
        continue
    p = os.path.join(MOD, n + ".stl") if os.path.exists(os.path.join(MOD, n + ".stl")) else f
    T = stlio.load_stl(p)
    V = T.reshape(-1, 3)
    if not near(V).any():
        continue
    keep = near(T.reshape(-1, 3)).reshape(-1, 3).any(1)
    S = stlio.sample(T[keep], 0.12)
    S = S[near(S)]
    mesh_pts.append(S); used.append((n, p, len(S)))
T = stlio.load_stl("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl/zatka.stl")
S = stlio.sample(T, 0.12); S = S[near(S)]
mesh_pts.append(S); used.append(("zatka", "R1/img_v2/work/stl/zatka.stl", len(S)))
TOR = {"mesh": np.concatenate(mesh_pts)}
print("mesh parts", [(u[0], u[2]) for u in used], f"{time.time() - t0:.0f}s", flush=True)
h = 0.15
ys = np.arange(-36.0, 40.0, h); zs = np.arange(-86.0, 4.0, h)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)], float)
ok = np.isfinite(X) & (X > 36.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - YA, S0[:, 2] - ZA)
th = np.linspace(0, 2 * np.pi, 1200, endpoint=False)
rim = np.c_[np.zeros_like(th), YA + 14.0 * np.cos(th), ZA + 14.0 * np.sin(th)]
rim[:, 0] = [C.x_surface(y, z) for y, z in rim[:, 1:]]
disc = S0[(ra <= 13.5) & (ra >= 7.0)].copy(); disc[:, 0] -= 1.0
TOR["ana"] = np.r_[S0[ra >= 14.0], rim, disc]
# how far is the real side-cover mesh from the analytic exterior near the arm (outer skin only)?
M = TOR["mesh"]; mm = (np.hypot(M[:, 1] - YA, M[:, 2] - ZA) > 14.5) & (M[:, 2] > -80) & (M[:, 2] < 2) & (np.abs(M[:, 1]) < 33)
xa = np.array([C.x_surface(y, z) for y, z in M[mm][:, 1:]])
dv = M[mm][:, 0] - xa; sk = np.abs(dv) < 0.6
print("mesh - analytic skin: max %.3f min %.3f (n %d)" % (dv[sk].max(), dv[sk].min(), sk.sum()), flush=True)
ANG = np.unique(np.r_[-51.0, np.arange(-45.0, 128.0, 1.0), np.arange(128.0, 135.01, 0.5), 140.5, 142.0])
OUT = dict(parts=[u[:2] for u in used], mesh_minus_analytic=[round(float(dv[sk].min()), 3), round(float(dv[sk].max()), 3)])
for vid in vids:
    A, lab, U = AS.cloud(vid, 0.08)
    tree = cKDTree(A)
    Ac, _, _ = AS.cloud(vid, 0.5)
    ctree = cKDTree(Ac)          # coarse (h 0.5): distance error <= ~0.36 -> only points within min + 0.8 are refined
    lo_b, hi_b = A.min(0) - 6.0, A.max(0) + 6.0
    for tk, TQ in TOR.items():
        per = []
        for a in ANG:
            Ql = VB.to_local(VB.swing(TQ, -a), vid)
            m = np.all((Ql >= lo_b) & (Ql <= hi_b), axis=1)
            Pq = Ql[m]
            ins = VB.inside_local(vid, Pq)
            dc = ctree.query(Pq, workers=2)[0]
            sdc = np.where(ins, -dc, dc)
            cand = sdc <= sdc.min() + 0.8
            d, k = tree.query(Pq[cand], workers=2)
            sd_c = np.where(ins[cand], -d, d)
            jc = int(np.argmin(sd_c))
            j = int(np.nonzero(cand)[0][jc]); kk = int(k[jc])
            sd = np.full(len(Pq), 9.0); sd[cand] = sd_c
            per.append((float(a), float(sd[j]), dict(torso=TQ[m][j].round(2).tolist(), arm_u=round(float(U[kk]), 3),
                                                     arm_half=["inner", "cover", "step"][int(lab[kk])], n_inside=int(ins.sum()))))
        aa = np.array([p[0] for p in per]); gg = np.array([p[1] for p in per])
        rng = (aa >= -45) & (aa <= 135)
        k2 = int(np.argmin(np.where(rng, gg, 1e9)))
        r = dict(rest=round(float(gg[aa == 0][0]), 3), rest_at=per[int(np.nonzero(aa == 0)[0][0])][2],
                 min_m45_135=round(float(gg[k2]), 3), min_angle=float(aa[k2]), min_at=per[k2][2],
                 at_m45=round(float(gg[aa == -45][0]), 3), at_135=round(float(gg[aa == 135][0]), 3),
                 at_m51=round(float(gg[aa == -51][0]), 3), at_140p5=round(float(gg[aa == 140.5][0]), 3), at_142=round(float(gg[aa == 142][0]), 3),
                 per_15deg={str(int(x)): round(float(v), 3) for x, v in zip(aa, gg) if abs(x % 15) < 1e-9})
        OUT[f"{vid} {tk}"] = r
        print(vid, tk, json.dumps({kk_: vv for kk_, vv in r.items() if kk_ != "per_15deg"}), f"{time.time() - t0:.0f}s", flush=True)
json.dump(OUT, open("out/gap_%s.json" % "_".join(vids), "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")
