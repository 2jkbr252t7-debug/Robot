"""C9: axial assembly path.  The arm assembly (glued black hub part, rib sector excluded = M2b procedure) is slid along -x
from 30 mm outboard to its seat; at every 0.1 mm step the min (x, r) distance of its profile boundary to the static parts
(variant plug + screws + T_bok_L + M2b ring / seat / lug) and penetration (static point inside the merged profile)."""
import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K, parts as PT
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"; M2B = "/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b"


def merged(pf):
    keep = dict(K.NEST); K.NEST.update(x_step=52.8, r_step=9.6, x_back=54.8, r_rim=12.2)
    try:
        return pf()
    finally:
        K.NEST.clear(); K.NEST.update(keep)


hub = np.array([p for p in PT.options()["M2b"]["parts"] if p.name == "ARM_naboj"][0].prof, float)
OUT = {}
for vid in ("K1", "K3", "K3v"):
    sh = K.arm_dx(vid) - K.DX0
    pf = [q for q in K.VARIANTS[vid]["parts"] if q["role"] == "rotating"][0]["profile"]
    polys = [merged(pf), hub + np.array([sh, 0.0])]
    stat = [mio.xr(mio.sample(mio.crop(mio.load(K.stl(vid, f"PLG_zatka_{vid}")), rmax=16, xmin=43), 0.1)),
            mio.xr(mio.sample(mio.load(K.stl(vid, "PLG_skrutky")), 0.1)),
            mio.xr(mio.sample(mio.crop(mio.load(os.path.join(MOD, "T_bok_L.stl")), rmax=18, xmin=40), 0.1))]
    for nm in ("PLG_kruzok", "PLG_cap"):
        Q = mio.xr(mio.sample(mio.load(os.path.join(M2B, nm + ".stl")), 0.08)); Q[:, 0] += sh; stat.append(Q)
    # lug: only matters if the ring bore passes it (full revolution part vs sector -> conservative)
    Q = mio.xr(mio.sample(mio.load(os.path.join(M2B, "PLG_doraz.stl")), 0.08)); Q[:, 0] += sh; stat.append(Q)
    S = np.concatenate(stat)
    S = np.unique(np.round(S, 3), axis=0)
    worst = (9.0, None)
    for s in np.arange(0.0, 30.0, 0.1):
        dmin = 9.0
        for P in polys:
            Pp = P + np.array([s, 0.0])
            m = (S[:, 0] > Pp[:, 0].min() - 1) & (S[:, 0] < Pp[:, 0].max() + 1) & (S[:, 1] < Pp[:, 1].max() + 1)
            if not m.any():
                continue
            d = mio.seg_dist(S[m], Pp); ins = mio.inpoly(S[m], Pp)
            sd = np.where(ins, -d, d)
            dmin = min(dmin, float(sd.min()))
        if dmin < worst[0]:
            worst = (dmin, round(float(s), 2))
    OUT[vid] = dict(min_clearance_along_path=round(worst[0], 3), at_offset=worst[1])
    print(vid, OUT[vid], flush=True)
json.dump(OUT, open(os.path.join(HERE, "c9_assembly.json"), "w"), indent=1)
