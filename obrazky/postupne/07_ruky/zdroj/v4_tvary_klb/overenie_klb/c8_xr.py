"""C8: exact pose-independent (x, r) distances of the axisymmetric rotating parts (visible collar / ring and the printed hub
part, stop-rib sector excluded) to every static mesh near the shoulder.  The rotating part's (x, r) boundary is taken from
its own STL surface samples (a solid of revolution maps every surface point onto its profile boundary); penetration is
tested with the klb profile (STL == profile, checked in C1) and with the merged print profile rebuilt like build_klb.merged."""
import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K, parts as PT
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"; M2B = "/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b"
TB = mio.sample(mio.crop(mio.load(os.path.join(MOD, "T_bok_L.stl")), rmax=20.0, xmin=40.0), 0.1)
TB = TB[(mio.xr(TB)[:, 1] < 20) & (TB[:, 0] > 40)]


def merged(pf):
    keep = dict(K.NEST); K.NEST.update(x_step=52.8, r_step=9.6, x_back=54.8, r_rim=12.2)
    try:
        return pf()
    finally:
        K.NEST.clear(); K.NEST.update(keep)


OUT = {}
for vid in ("K1", "K3", "K3v"):
    v = K.variant(vid); sh = K.arm_dx(vid) - K.DX0
    p = [q for q in v["parts"] if q["role"] == "rotating"][0]
    prof_v = [q for q in K.VARIANTS[vid]["parts"] if q["role"] == "rotating"][0]["profile"]
    stat = {"T_bok_L": TB}
    for q in v["parts"]:
        if q["role"] == "static":
            stat[q["id"]] = mio.sample(mio.crop(mio.load(q["stl"]), rmax=16.0, xmin=43.0), 0.08)
    for nm in ("PLG_kruzok", "PLG_cap", "PLG_doraz", "BRG_A2_MR74", "M4_DIN7984_M4x20", "BRG_MR128_vnut", "DRV_unasac"):
        Q = mio.sample(mio.load(os.path.join(M2B, nm + ".stl")), 0.08).copy(); Q[:, 0] += sh
        stat["M2b_" + nm] = Q
    res = {}
    for label, stl, poly in (("visible", p["stl"], prof_v()), ("print", p["print_stl"], merged(prof_v))):
        S = mio.sample(mio.load(stl), 0.06)
        a = mio.az(S); X = mio.xr(S)
        rib = (a > PT.RIB_AZ[0] - 1) & (a < PT.RIB_AZ[1] + 1) & (X[:, 1] < 9.75) & (X[:, 0] > 52.0 + sh)
        B = X[~rib]
        tr = cKDTree(B)
        for sk, Q in stat.items():
            Qx = mio.xr(Q)
            m = (Qx[:, 0] > B[:, 0].min() - 3) & (Qx[:, 0] < B[:, 0].max() + 3) & (Qx[:, 1] < B[:, 1].max() + 3)
            if not m.any():
                continue
            d, _ = tr.query(Qx[m])
            ins = mio.inpoly(Qx[m], poly)
            if label == "print":
                # the print part also contains the M2b hub: points inside the hub profile count as inside
                hub = np.array(PT.options()["M2b"]["parts"][[pp.name for pp in PT.options()["M2b"]["parts"]].index("ARM_naboj")].prof, float).copy()
                hub[:, 0] += sh
                ins |= mio.inpoly(Qx[m], hub)
            sd = np.where(ins, -d, d)
            k = int(np.argmin(sd))
            q3 = Q[m][k]
            res[f"{label} | {sk}"] = dict(min=round(float(sd[k]), 3), at_xr=Qx[m][k].round(2).tolist(),
                                          az=round(float(mio.az(q3[None])[0]), 1))
    OUT[vid] = res
    print(vid)
    for k_, r_ in sorted(res.items(), key=lambda kv: kv[1]["min"]):
        if r_["min"] < 2.5:
            print(f"   {k_:40s} {r_['min']:7.3f}  at xr {r_['at_xr']} az {r_['az']}")
json.dump(OUT, open(os.path.join(HERE, "c8_xr.json"), "w"), indent=1)
