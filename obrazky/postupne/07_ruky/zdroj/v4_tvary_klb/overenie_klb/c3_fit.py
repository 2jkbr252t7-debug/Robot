"""C3: printed black hub part (collar / ring + M2b hub + rib) inside arm B: wall to the OUTER arm surface (cover side of the
seam, req 1.2), stays inside the arm, relation to the seam; plus 2-D clearances to the M2b drive / static parts and to the
steel arm parts (from the print STL (x, r) outline, not from klb profiles)."""
import sys, os, json, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K, variants as VA, parts as PT, fit as FT
OUT = {}
for vid in ("K1", "K3", "K3v"):
    v = K.variant(vid); dx = K.arm_dx(vid); sh = dx - K.DX0
    arm = FT.Arm(VA, "B", dx)
    p = [q for q in v["parts"] if q["role"] == "rotating"][0]
    S = mio.sample(mio.load(p["print_stl"]), 0.1)
    L = arm.to_local(S)
    arm.build_cloud(L[:, 2].min() - 8.0, L[:, 2].max() + 8.0)
    ins, dout, din, P = arm.walls(S)
    seam = arm.seam(P)
    cover_side = P[:, 0] >= seam
    # printed arm part: on the inner side of the seam it is inner-shell material; it must stay inside the arm except where it
    # leaves through the inner face (visible collar / ring outside the arm, towards the torso)
    outside = ~ins
    outside_inner_side = outside & (din < dout)
    outside_outer_side = outside & ~(din < dout)
    wo = np.where(cover_side & ins, dout, 9.0)
    k = int(np.argmin(np.where(ins, dout, 9.0)))
    q = S[k]
    # distance of every point (inside the arm) to the seam plane along local x (negative = on the cover side)
    dseam = seam - P[:, 0]
    kk = int(np.argmin(np.where(ins, dseam, 99)))
    r = dict(n=len(S), pts_cover_side=int(cover_side.sum()), pts_outside_through_outer=int(outside_outer_side.sum()),
             min_dist_to_outer_surface=round(float(dout[ins].min()), 3),
             at=dict(xyz=q.round(2).tolist(), xr=mio.xr(q[None])[0].round(2).tolist(), az=round(float(mio.az(q[None])[0]), 1)),
             min_local_x_to_seam=round(float(dseam[ins].min()), 3),
             at_seam=dict(xyz=S[kk].round(2).tolist(), xr=mio.xr(S[kk][None])[0].round(2).tolist(), az=round(float(mio.az(S[kk][None])[0]), 1)))
    # 2-D: print outline from the STL itself: (x, r) of all samples -> compare against M2b parts by point-in-polygon + distance
    Q = mio.xr(S)
    rows = []
    for mp in PT.options()["M2b"]["parts"]:
        if mp.name in ("ARM_naboj", "ARM_rebro"):
            continue
        Pm = np.array(mp.outline_xr(), float).copy(); Pm[:, 0] += sh
        if mp.az is not None or mp.mag is not None:
            # sector / magnet: (x, r) test is conservative for full-revolution print part
            pass
        d = mio.seg_dist(Q, Pm); inside = mio.inpoly(Q, Pm)
        dm = float(np.where(inside, -d, d).min())
        need = 0.3 if mp.role in ("static", "drive") else 0.0
        rows.append(dict(part=mp.name, role=mp.role, dist=round(dm, 3), need=need, ok=bool(dm >= need - 1e-3)))
    r["vs_M2b"] = rows
    OUT[vid] = r
    print(vid, json.dumps({k: r[k] for k in r if k != "vs_M2b"}))
    print("   ", [(x["part"], x["dist"], x["ok"]) for x in rows if x["dist"] < 1.5])
json.dump(OUT, open(os.path.join(HERE, "c3_fit.json"), "w"), indent=1)
