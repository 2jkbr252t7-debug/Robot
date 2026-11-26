"""Verifier: arm-torso gap of variant A (left arm), rest and over the swing, with TWO torso models:
  'rec1' : approved analytic torso exterior t4_common.x_surface, socket cap edge r 14 about the shoulder axis, plug face
           r <= 13.5 recessed 1.0 (= the judge's armgap_top.py model)
  'stl'  : the real side-cover mesh T4/stl/T_bok_L.stl (triangles sampled at <= 0.15 mm) + the same recessed plug face
Arm = my own parametric surface (geomA, spacing 0.06) with the analytic inside sign; also variant 0 for reference.
Angles -45..+135 in 1 deg steps (0.5 deg from 125), plus 135..142 for the stop region."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomA as G  # noqa
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C  # noqa
import vlib  # noqa

t0 = time.time()
# ---------------------------------------------------------------- torso models
hs = 0.2
ys = np.arange(-34.0, 36.0, hs); zs = np.arange(-80.0, 3.9, hs)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)])
ok = np.isfinite(X) & (X > 38.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - 3.0, S0[:, 2] + 17.0)
th = np.linspace(0, 2 * np.pi, 900, endpoint=False)
rim = np.c_[np.zeros_like(th), 3.0 + 14.0 * np.cos(th), -17.0 + 14.0 * np.sin(th)]
rim[:, 0] = [C.x_surface(y, z) for y, z in rim[:, 1:]]
disc = S0[ra <= 13.5].copy(); disc[:, 0] -= 1.0
T_rec1 = np.r_[S0[ra >= 14.0], rim, disc]

T = vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_bok_L.stl")
keep = T[:, :, 0].max(1) > 41.0
T = T[keep]


def sample_tris(T, h=0.15):
    out = []
    for tri in T:
        a, b, c = tri
        lab, lac = np.linalg.norm(b - a), np.linalg.norm(c - a)
        n1 = max(1, int(math.ceil(max(lab, lac, np.linalg.norm(c - b)) / h)))
        i, j = np.meshgrid(np.arange(n1 + 1), np.arange(n1 + 1), indexing="ij")
        m = (i + j) <= n1
        s, t = i[m] / n1, j[m] / n1
        out.append(a + s[:, None] * (b - a) + t[:, None] * (c - a))
    return np.concatenate(out)


Sstl = sample_tris(T)
rs = np.hypot(Sstl[:, 1] - 3.0, Sstl[:, 2] + 17.0)
# the old T_klb socket / anything inside r 13.5 of the axis on the outside is replaced by the recessed plug face
Sstl = Sstl[rs >= 13.5]
Sstl = np.unique(np.round(Sstl, 2), axis=0)
T_stl = np.r_[Sstl, disc]
print("torso samples rec1", len(T_rec1), "stl", len(T_stl), f"{time.time() - t0:.0f}s", flush=True)

# ---------------------------------------------------------------- arms
ANG = np.r_[np.arange(-45.0, 125.0, 1.0), np.arange(125.0, 142.01, 0.5)]
res = {}
for vid, ko, kw in (("A", 0.62, 0.95), ("0", 1.0, 1.0)):
    P, H = G.surface(0.0, 1.0, 0.06, ko, kw)
    tree = cKDTree(P)
    # swing-invariant prefilter: (x, r) about the shoulder axis does not change with the swing, so a torso point whose
    # (x, r) lies farther than 6 mm from the arm's (x, r) set can never come within 6 mm of the arm
    Wa = G.to_world(P)
    xr_arm = np.c_[Wa[:, 0], np.hypot(Wa[:, 1] - 3.0, Wa[:, 2] + 17.0)]
    xr_tree = cKDTree(np.unique(np.round(xr_arm, 2), axis=0))
    for tname, TT0 in (("rec1", T_rec1), ("stl", T_stl)):
        dxr, _ = xr_tree.query(np.c_[TT0[:, 0], np.hypot(TT0[:, 1] - 3.0, TT0[:, 2] + 17.0)], distance_upper_bound=4.0)
        TT = TT0[np.isfinite(dxr)]
        print(vid, tname, "torso points kept", len(TT), "of", len(TT0), flush=True)
        per = []
        where = []
        for a in ANG:
            Q = G.to_local(G.swing(TT, -a))                # torso into the arm frame (arm swung by +a)
            # only torso points near the arm matter
            d, _ = tree.query(Q, distance_upper_bound=4.0, workers=2)
            ins = G.inside(Q, ko, kw)
            sd = np.where(ins, -np.minimum(d, 4.0), np.minimum(d, 4.0))
            k = int(np.argmin(sd)); per.append(float(sd[k])); where.append(TT[k].round(2).tolist())
        per = np.array(per)
        sel = (ANG >= -45) & (ANG <= 135)
        k = int(np.argmin(np.where(sel, per, 9e9)))
        r = dict(rest=round(float(per[ANG == 0][0]), 3), rest_at=where[int(np.nonzero(ANG == 0)[0][0])],
                 min_m45_135=round(float(per[k]), 3), min_angle=float(ANG[k]), min_at=where[k],
                 at_m45=round(float(per[ANG == -45][0]), 3), at_130=round(float(per[ANG == 130][0]), 3),
                 at_135=round(float(per[ANG == 135][0]), 3), at_140p5=round(float(per[ANG == 140.5][0]), 3),
                 per_10deg={str(int(a)): round(float(v), 2) for a, v in zip(ANG, per) if a % 10 == 0})
        res[f"{vid} {tname}"] = r
        json.dump(res, open(os.path.join(HERE, "gap_A.json"), "w"), indent=1)
        print(vid, tname, {kk: vv for kk, vv in r.items() if kk != "per_10deg"}, f"{time.time() - t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, "gap_A.json"), "w"), indent=1)
