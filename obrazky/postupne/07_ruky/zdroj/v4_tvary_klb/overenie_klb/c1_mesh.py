"""C1: mesh integrity of every new STL + agreement of the axisymmetric STLs with the klb.py profiles"""
import sys, os, json, glob
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
import mio, klb as K
OUT = {}
for f in sorted(glob.glob("/tmp/claude-0/gapwf/fin/R4/klb/stl/*/*.stl")):
    T = mio.load(f)
    n, bad, vol = mio.manifold(T)
    P = T.reshape(-1, 3)
    key = os.path.relpath(f, "/tmp/claude-0/gapwf/fin/R4/klb/stl")
    OUT[key] = dict(tris=n, bad_edges=bad, volume=round(vol, 1), bbox=[round(v, 2) for v in np.r_[P.min(0), P.max(0)]])
    print(f"{key:40s} tris {n:7d} bad_edges {bad:5d} vol {vol:9.1f} bbox {np.round(P.min(0),2)} {np.round(P.max(0),2)}")
# profile agreement (vertices of the visible rotating parts vs their klb profile)
for vid in ("K1", "K3", "K3v"):
    p = [q for q in K.VARIANTS[vid]["parts"] if q["role"] == "rotating"][0]
    prof = p["profile"]()
    T = mio.load(K.stl(vid, p["id"]))
    Q = mio.xr(T.reshape(-1, 3))
    d = mio.seg_dist(Q, prof)
    OUT[f"{vid}/{p['id']}_vs_profile"] = dict(max_dev=round(float(d.max()), 4))
    print(vid, p["id"], "max vertex deviation from klb profile", round(float(d.max()), 4))
for vid in ("K2", "K3", "K3v"):
    sh = K.SHIFT_K3V if vid == "K3v" else 0.0
    prof = K.cover_profile(sh)
    T = mio.load(K.stl(vid, f"PLG_zatka_{vid}"))
    Q = mio.xr(T.reshape(-1, 3))
    m = (Q[:, 0] > 44.6) & (Q[:, 1] > 6.6)
    # exclude the screw access bores (r 2.3 around the 3 screws at r 9)
    P = T.reshape(-1, 3)
    import g2 as G
    keep = m.copy()
    for h in (12, 4, 8):
        y, z = G.clock_pt(h, 9.0)
        keep &= np.hypot(P[:, 1] - y, P[:, 2] - z) > 2.35
    d = mio.seg_dist(Q[keep], prof)
    OUT[f"{vid}/cover_vs_profile"] = dict(max_dev=round(float(d.max()), 4), n=int(keep.sum()))
    print(vid, "cover vertices (x>44.6, r>6.6, off bores) max deviation from cover profile", round(float(d.max()), 4), keep.sum())
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "c1_mesh.json"), "w"), indent=1)
