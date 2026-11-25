import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3"); sys.path.insert(0, ".")
import vlib, v1geo as V
T4 = "/tmp/claude-0/gapwf/fin/T4/stl/"
ST = "stl/"
M = {n: vlib.Mesh(vlib.load_stl(T4 + n + ".stl")) for n in ("T_klb_L", "T_bok_L", "T_spodok")}
new = ["o_kruzok", "kryt_surovy"]
for n in new:
    tr = vlib.load_stl(ST + n + ".stl")
    P = vlib.sample_surface(tr, 0.15)
    out = []
    for m, mesh in M.items():
        ins = mesh.inside(P)
        out.append(f"{m}: inside {ins.sum():5d}  min dist {np.min(mesh.dist(P, dmax=6.0)[0]):.3f}")
    print(f"{n:14s} pts {len(P):6d} | " + " | ".join(out))
