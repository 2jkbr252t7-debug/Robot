import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np
import mio, klb as K, variants as VA, parts as PT
OUT = {}
for vid in ("K1", "K3", "K3v"):
    v = K.variant(vid); dx = K.arm_dx(vid); sh = dx - K.DX0
    p = [q for q in v["parts"] if q["role"] == "rotating"][0]
    S = mio.sample(mio.load(p["print_stl"]), 0.06)
    a = mio.az(S); Q = mio.xr(S)
    rib = (a > PT.RIB_AZ[0] - 1) & (a < PT.RIB_AZ[1] + 1) & (Q[:, 1] < 9.75) & (Q[:, 0] > 52.0 + sh)
    Qn = Q[~rib]
    rows = {}
    for mp in PT.options()["M2b"]["parts"]:
        if mp.name in ("ARM_naboj", "ARM_rebro"):
            continue
        Pm = np.array(mp.outline_xr(), float).copy(); Pm[:, 0] += sh
        d = mio.seg_dist(Qn, Pm); ins = mio.inpoly(Qn, Pm)
        sd = np.where(ins, -d, d); k = int(np.argmin(sd))
        rows[mp.name] = dict(role=mp.role, dist=round(float(sd[k]), 3), at_xr=Qn[k].round(2).tolist())
    # stop-rib vs lug in 3-D at the stop angles and inside the range (from the print STL rib points)
    Sr = S[rib]
    lug = mio.sample(mio.load("/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b/PLG_doraz.stl"), 0.05); lug[:, 0] += sh
    from scipy.spatial import cKDTree
    tr = cKDTree(lug)
    st = {}
    for ang in (-51.0, -45.0, 0.0, 135.0, 140.5):
        d, _ = tr.query(mio.swing(Sr, ang)); st[str(ang)] = round(float(d.min()), 3)
    OUT[vid] = dict(vs_M2b_without_rib=rows, rib_vs_lug=st)
    print(vid, {k: (v_["dist"], v_["at_xr"]) for k, v_ in rows.items() if v_["dist"] < 1.2})
    print("   rib vs lug:", st)
json.dump(OUT, open(os.path.join(HERE, "c3b_fit.json"), "w"), indent=1)
