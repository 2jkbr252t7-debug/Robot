"""C2b (lean): swing sweep -51..+142.5 deg, 1 deg steps (+140.5): rotating clouds vs static clouds near the shoulder.
Rotating: white inner half A_vnut with the variant's opening (mesh, r < 30 around the axis), visible collar / ring, printed
hub part.  Static: T_bok_L, variant plug, plug screws.  Coarse h 0.2/0.25, then local fine refinement (h 0.04) at the key
angles and the 3 coarse minima.   usage: c2b_sweep.py K0,K2,...  -> c2b_<vid>.json"""
import sys, os, json, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K
t0 = time.time()
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"
ANG = np.unique(np.r_[np.arange(-51.0, 142.51, 1.0), 140.5, -45.0, 135.0])
KEY = (0.0, -45.0, 135.0, 140.5, -51.0)
TBm = mio.crop(mio.load(os.path.join(MOD, "T_bok_L.stl")), rmax=32.0, xmin=40.0)


def run(vid):
    v = K.variant(vid)
    stat = {"T_bok_L": TBm}
    for p in v["parts"]:
        if p["role"] == "static":
            stat[p["id"]] = mio.crop(mio.load(p["stl"]), rmax=16.0, xmin=43.0)
    rot = {"A_vnut": mio.crop(mio.load(v.get("arm_inner_half_stl") or K.stl("K0", "A_vnut_otvor_K0")), rmax=30.0, xmax=60.0)}
    for p in ([] if os.environ.get("AVNUT_ONLY") else v["parts"]):
        if p["role"] == "rotating":
            rot[p["id"]] = mio.load(p["stl"])
            rot[p["id"].replace("ARM_", "PRINT_")] = mio.load(p["print_stl"])
    statC = {k: mio.sample(T, 0.25) for k, T in stat.items()}
    res = {}
    for rk, RT in rot.items():
        RC = mio.sample(RT, 0.2)
        tr = cKDTree(RC)
        lo, hi = RC[:, 0].min() - 3, RC[:, 0].max() + 3
        rr = mio.xr(RC)[:, 1].max() + 3
        for sk, S in statC.items():
            Sx = mio.xr(S)
            S = S[(S[:, 0] > lo) & (S[:, 0] < hi) & (Sx[:, 1] < rr)]
            if len(S) == 0:
                continue
            per = {}
            for a in ANG:
                d, _ = tr.query(mio.swing(S, -a), distance_upper_bound=5.0, workers=1)
                k = int(np.argmin(d)); per[float(a)] = (float(min(d[k], 5.0)), S[k])
            dd = np.array([per[float(a)][0] for a in ANG])
            if dd.min() >= 4.99:
                continue
            cand = set(KEY) | set(float(a) for a in ANG[np.argsort(dd)[:3]])
            for a in sorted(cand):
                c = per[a][1]
                SF = mio.sample(mio.crop(stat[sk], center=c, radius=3.0), 0.04, seed=3)
                cr = mio.swing(c[None], -a)[0]
                RF = mio.sample(mio.crop(RT, center=cr, radius=per[a][0] + 3.5), 0.04, seed=5)
                if len(SF) == 0 or len(RF) == 0:
                    continue
                d, _ = cKDTree(RF).query(mio.swing(SF, -a), distance_upper_bound=5.0, workers=1)
                k = int(np.argmin(d))
                if d[k] < per[a][0]:
                    per[a] = (float(d[k]), SF[k])
            dd = np.array([per[float(a)][0] for a in ANG])
            rng = (ANG >= -45) & (ANG <= 135)
            k0 = int(np.argmin(dd)); kr = int(np.argmin(np.where(rng, dd, 99)))
            q = per[float(ANG[k0])][1]
            res[f"{rk} | {sk}"] = dict(min_all=round(float(dd[k0]), 3), at_deg=float(ANG[k0]),
                                       at_xr=mio.xr(q[None])[0].round(2).tolist(), at_az=round(float(mio.az(q[None])[0]), 1),
                                       min_m45_135=round(float(dd[kr]), 3), at_deg_m45_135=float(ANG[kr]),
                                       rest=round(per[0.0][0], 3), at_135=round(per[135.0][0], 3), at_140_5=round(per[140.5][0], 3),
                                       at_m51=round(per[-51.0][0], 3), refined=sorted(cand))
        print(vid, rk, f"{time.time()-t0:.0f}s", flush=True)
    json.dump(dict(dx=K.arm_dx(vid), pairs=res), open(os.path.join(HERE, f"c2b_{vid}.json"), "w"), indent=1)
    for k_, q in sorted(res.items(), key=lambda kv: kv[1]["min_all"]):
        print(f"  {k_:40s} min {q['min_all']:6.3f} @{q['at_deg']:6.1f} xr {q['at_xr']} az {q['at_az']:5.1f} | rest {q['rest']:6.3f}"
              f"  m45..135 {q['min_m45_135']:6.3f}@{q['at_deg_m45_135']:5.1f}  135 {q['at_135']:6.3f}  140.5 {q['at_140_5']:6.3f}  -51 {q['at_m51']:6.3f}", flush=True)


for vid in (sys.argv[1].split(",") if len(sys.argv) > 1 else K.VIDS):
    run(vid)
print("done", f"{time.time()-t0:.0f}s")
