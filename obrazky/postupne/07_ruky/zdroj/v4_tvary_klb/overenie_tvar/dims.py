"""thickness / width from the analytic inside test only (ray bisection, independent of section() bookkeeping) + inner face
vs B0 along the arm + how far each variant's inner half reaches beyond B0 towards the torso (world x)"""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB


def bis(vid, C, D, rmax=30.0, it=50):
    lo = np.zeros(len(C)); hi = np.full(len(C), rmax)
    for _ in range(it):
        m = 0.5 * (lo + hi)
        ok = VB.inside_local(vid, C + D * m[:, None])
        lo = np.where(ok, m, lo); hi = np.where(ok, hi, m)
    return lo


OUT = {}
us = np.linspace(0.002, 0.998, 4981)
for vid in ["B0", "B1", "B2", "B3"]:
    c = AS.secf(vid, us)[0]
    C = np.c_[c, np.zeros_like(us), -72 * us]
    xo = bis(vid, C, np.tile([1.0, 0, 0], (len(us), 1))); xi = bis(vid, C, np.tile([-1.0, 0, 0], (len(us), 1)))
    # width: scan x across the section, max y extent
    wmax = np.zeros_like(us)
    for dxs in np.linspace(-0.6, 0.6, 25):
        Cy = C + np.array([dxs, 0, 0]) * 1
        Cy[:, 0] = c + dxs * 1.0
        wmax = np.maximum(wmax, bis(vid, Cy, np.tile([0, 1.0, 0], (len(us), 1))))
    T = xo + xi
    k22 = int(np.argmin(np.abs(us - 0.22)))
    OUT[vid] = dict(T_max=round(float(T.max()), 2), T_max_u=round(float(us[T.argmax()]), 3), T_joint=round(float(T[k22]), 2),
                    cover_joint=round(float(xo[k22]), 2), inner_joint=round(float(xi[k22]), 2), W_max=round(float(2 * wmax.max()), 2),
                    W_max_u=round(float(us[wmax.argmax()]), 3), W_joint=round(float(2 * wmax[k22]), 2), inner_face=(c - xi))
for vid in ["B1", "B2", "B3"]:
    d = OUT[vid]["inner_face"] - OUT["B0"]["inner_face"]           # + = further from the torso than B0
    for lo, hi in ((0.0, 0.12), (0.12, 0.42), (0.42, 0.50), (0.5, 0.9), (0.9, 1.0)):
        m = (us >= lo) & (us < hi)
        OUT[vid][f"inner_face_vs_B0_u{lo}-{hi}"] = [round(float(d[m].min()), 3), round(float(d[m].max()), 3)]
for vid in OUT:
    OUT[vid].pop("inner_face")
# max world-x innermost (towards the torso) of each variant per u band vs B0 (rows of the own skin)
for vid in ["B0", "B1", "B2", "B3"]:
    S, lab, U = AS.cloud(vid, 0.1)
    W = VB.to_world(S, vid)
    OUT[vid]["innermost_world_x"] = round(float(W[:, 0].min()), 3)
    OUT[vid]["outermost_world_x"] = round(float(W[:, 0].max()), 3)
    OUT[vid]["robot_width_over_arms"] = round(float(2 * W[:, 0].max()), 2)
print(json.dumps(OUT, indent=1))
json.dump(OUT, open("out/dims.json", "w"), indent=1)
