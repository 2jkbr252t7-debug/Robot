"""C2: full swing sweep -51..+142.5 deg (1 deg steps + 140.5, -45, 135) of every rotating part against every static part near
the left shoulder.  Coarse pass (static h 0.3, rotating h 0.15) at every angle, then a fine pass (static h 0.05 within 3 mm of
the coarse spot, rotating h 0.05) at the key angles (0, -45, 135, 140.5, -51) and at the 3 coarse-minimum angles.
Rotating: visible collar/ring, printed hub part, white inner half A_vnut with the variant's opening (mesh), outer cover
A_vonk (analytic, arm B at the variant dx).  Static: T_bok_L (v2 mod), variant plug, plug screws, M2b static parts
(ring / seat cap / stop lug; +1.5 for K3v).   usage: c2_sweep.py K0,K1,...   -> c2_<vid>.json"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K, variants as VA
t0 = time.time()
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"
M2B = "/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b"
ANG = np.unique(np.r_[np.arange(-51.0, 142.51, 1.0), 140.5, -45.0, 135.0])
KEY = (0.0, -45.0, 135.0, 140.5, -51.0)


def near(P, rmax=40.0, xmin=34.0):
    r = np.hypot(P[:, 1] - 3.0, P[:, 2] + 17.0)
    return P[(r < rmax) & (P[:, 0] > xmin)]


MESH = {"T_bok_L": mio.load(os.path.join(MOD, "T_bok_L.stl"))}


def outer_cover(dx, nu, nth):
    rows, c0, c1 = VA.half_rows("B", "vonk", nu=nu, nth=nth)
    return VA.to_world(rows.reshape(-1, 3), "B", dx)


def run(vid):
    v = K.variant(vid)
    dx = K.arm_dx(vid); sh = dx - K.DX0
    meshes = dict(MESH)
    for p in v["parts"]:
        if p["role"] == "static":
            meshes[p["id"]] = mio.load(p["stl"])
    for nm in ("PLG_kruzok", "PLG_cap", "PLG_doraz"):
        T = mio.load(os.path.join(M2B, nm + ".stl")).copy(); T[..., 0] += sh
        meshes["M2b_" + nm] = T
    meshes = {k: mio.crop(T, rmax=40.0, xmin=34.0) for k, T in meshes.items()}
    statC = {k: near(mio.sample(T, 0.3 if k == "T_bok_L" else 0.15)) for k, T in meshes.items()}
    rotm = {}
    for p in v["parts"]:
        if p["role"] == "rotating":
            rotm[p["id"]] = mio.load(p["stl"])
            rotm[p["id"].replace("ARM_", "PRINT_")] = mio.load(p["print_stl"])
    rotm["A_vnut"] = mio.load(v.get("arm_inner_half_stl") or K.stl("K0", "A_vnut_otvor_K0"))
    rotm["A_vnut"] = mio.crop(rotm["A_vnut"], rmax=45.0, xmax=60.0)       # the part of the inner half that can reach the torso
    rotC = {k: mio.sample(T, 0.15) for k, T in rotm.items()}
    rotC["A_vonk"] = outer_cover(dx, 300, 200)
    AVF = outer_cover(dx, 900, 600)
    res = {}
    for rk in rotC:
        trC = cKDTree(rotC[rk])
        lo = rotC[rk].min(0) - 3.0; hi = rotC[rk].max(0) + 3.0; rr = mio.xr(rotC[rk])[:, 1].max() + 3.0
        for sk, S in statC.items():
            Sx = mio.xr(S)
            m = (S[:, 0] >= lo[0]) & (S[:, 0] <= hi[0]) & (Sx[:, 1] <= rr)
            if not m.any():
                continue
            Sm = S[m]
            per = {}
            for a in ANG:
                d, _ = trC.query(mio.swing(Sm, -a), distance_upper_bound=6.0, workers=3)
                k = int(np.argmin(d)); per[float(a)] = (float(min(d[k], 6.0)), Sm[k])
            dd = np.array([per[a][0] for a in ANG])
            if dd.min() >= 5.9:
                continue
            # fine pass
            cand = set(KEY) | set(float(a) for a in ANG[np.argsort(dd)[:3]])
            fine = {}
            for a in sorted(cand):
                c = per[a][1]
                if per[a][0] >= 5.9:
                    fine[a] = per[a][0]; continue
                SF = mio.sample(mio.crop(meshes[sk], center=c, radius=3.5), 0.04, seed=3)
                cr = mio.swing(c[None], -a)[0]
                if rk == "A_vonk":
                    RF = AVF[np.linalg.norm(AVF - cr, axis=1) < per[a][0] + 4.0]
                else:
                    RF = mio.sample(mio.crop(rotm[rk], center=cr, radius=per[a][0] + 4.0), 0.04, seed=5)
                if len(SF) == 0 or len(RF) == 0:
                    fine[a] = per[a][0]; continue
                trF = cKDTree(RF)
                d, _ = trF.query(mio.swing(SF, -a), distance_upper_bound=6.0, workers=3)
                mm = np.ones(len(SF), bool)
                k = int(np.argmin(d)); fine[a] = float(min(d[k], per[a][0]))
                if fine[a] < per[a][0] - 1e-9:
                    per[a] = (fine[a], SF[mm][k])
            dd2 = np.array([per[a][0] for a in ANG])
            rng = (ANG >= -45) & (ANG <= 135)
            k0 = int(np.argmin(dd2)); kr = int(np.argmin(np.where(rng, dd2, 99)))
            q = per[float(ANG[k0])][1]
            res[f"{rk} | {sk}"] = dict(min_all=round(float(dd2[k0]), 3), at_deg=float(ANG[k0]), at_xyz=q.round(2).tolist(),
                                       at_xr=mio.xr(q[None])[0].round(2).tolist(), at_az=round(float(mio.az(q[None])[0]), 1),
                                       min_m45_135=round(float(dd2[kr]), 3), at_deg_m45_135=float(ANG[kr]),
                                       rest=round(per[0.0][0], 3), at_135=round(per[135.0][0], 3), at_140_5=round(per[140.5][0], 3),
                                       at_m51=round(per[-51.0][0], 3), coarse_spread=round(float(dd.max() - dd.min()), 3),
                                       fine_refined=sorted(cand))
        print(vid, rk, f"{time.time()-t0:.0f}s", flush=True)
    json.dump(dict(dx=dx, pairs=res), open(os.path.join(HERE, f"c2_{vid}.json"), "w"), indent=1)
    for k, q in sorted(res.items(), key=lambda kv: kv[1]["min_all"]):
        if q["min_all"] < 4.0:
            print(f"  {k:42s} min {q['min_all']:6.3f} @{q['at_deg']:6.1f} xr {q['at_xr']} az {q['at_az']:5.1f} | rest {q['rest']:6.3f}"
                  f"  m45..135 {q['min_m45_135']:6.3f}@{q['at_deg_m45_135']:5.1f}  135 {q['at_135']:6.3f}  140.5 {q['at_140_5']:6.3f}", flush=True)


for vid in (sys.argv[1].split(",") if len(sys.argv) > 1 else K.VIDS):
    run(vid)
print("done", f"{time.time()-t0:.0f}s")
