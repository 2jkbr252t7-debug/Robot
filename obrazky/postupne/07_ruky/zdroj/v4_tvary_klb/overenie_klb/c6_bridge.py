"""C6: white band of the inner half around the opening: per azimuth the outermost radius of the arm's inner half
(x < seam - 0.25, any x) minus the hole radius; and the same from the A_vnut_otvor mesh (vertices)."""
import sys, os, json, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
import variants as VA, klb as K, mio
YA, ZA = 3.0, -17.0
OUT = {}
rs = np.arange(5.0, 80.0, 0.02)
xs = np.arange(47.0, 64.0, 0.1)
X, Rr = np.meshgrid(xs, rs, indexing="ij")
dx = K.DX0
rmax = {}
for az in range(0, 360, 5):
    t = math.radians(az)
    W = np.c_[X.ravel(), YA + Rr.ravel() * math.cos(t), ZA + Rr.ravel() * math.sin(t)]
    L = VA.to_local(W, "B", dx)
    ins = VA.inside_local("B", L)
    u = np.clip(-L[:, 2] / VA.L, 0, 1)
    inner = ins & (L[:, 0] < VA.seam_x("B", u) - VA.SEAM)
    # the arm material connected to the shoulder region: radius of the first exit from the arm going outward at each x;
    # take the max over x of the first-run end (for az where the arm continues far down, report 'long')
    I = inner.reshape(X.shape)
    best = 0.0
    for i in range(len(xs)):
        col = I[i]
        if not col.any():
            continue
        j0 = np.argmax(col)
        if rs[j0] > 14.0:
            continue
        # end of the first run
        rest = col[j0:]
        j1 = j0 + (np.argmin(rest) if (~rest).any() else len(rest)) - 1
        best = max(best, rs[j1])
    rmax[az] = best
for vid, hole in (("K0", 7.0), ("K1", 11.1), ("K3", 13.2)):
    OUT[vid] = {str(a): round(rmax[a] - hole, 2) for a in rmax if rmax[a] < 40}
print("outermost radius of the inner half per az (arm continues > 40 -> omitted):")
print({a: round(r, 2) for a, r in rmax.items() if r < 40})
for vid in OUT:
    v = OUT[vid]
    print(vid, "min white band above the hole:", min(v.values()), "at az", min(v, key=v.get), v)
# A_vnut mesh: radial gap between the hole edge and the outer silhouette near the top (vertices of the mesh)
for vid in ("K0", "K1", "K3"):
    P = mio.load(K.stl(vid, f"A_vnut_otvor_{vid}")).reshape(-1, 3)
    a = mio.az(P); r = mio.xr(P)[:, 1]
    m = (a > 60) & (a < 120)
    print(vid, "A_vnut mesh: top sector (az 60..120): min r", round(float(r[m].min()), 2), " max r", round(float(r[m].max()), 2))
json.dump(OUT, open(os.path.join(HERE, "c6_bridge.json"), "w"), indent=1)
