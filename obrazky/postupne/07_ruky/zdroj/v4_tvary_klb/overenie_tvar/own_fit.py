"""(walls >= 3.0 are reported as 3.0)  own wall check of the M2b joint envelope inside R4 arm variants: every M2b part (frame B, from R3/mech/parts.py
profiles, own surface sampling h 0.04) against the own dense arm surface (armsurf_own, h 0.05), sign from the analytic
inside test.  Reports for each part the min distance to the whole arm skin, to the outer cover half and to the inner half."""
import sys, json, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech"); import parts as PT
YA, ZA = 3.0, -17.0


def part_surface(p, h):
    if p.mag is not None:
        return p.surface(h)
    P = p.prof; E = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n = max(2, int(math.ceil(np.hypot(*(b - a)) / h)))
        t = np.linspace(0, 1, n, endpoint=False); E.append(a + t[:, None] * (b - a))
    E = np.concatenate(E)
    a0, a1 = (0.0, 360.0) if p.az is None else p.az
    out = []
    for x, r in E:
        n = max(1, int(math.radians(a1 - a0) * r / h) + 1) if r > 1e-6 else 1
        ph = np.radians(np.linspace(a0, a1, n, endpoint=p.az is not None))
        out.append(np.c_[np.full(n, x), YA + r * np.cos(ph), ZA + r * np.sin(ph)])
    return np.concatenate(out)


res = {}
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else ["B0", "B1", "B2", "B3"]
parts = [p for p in PT.options()["M2b"]["parts"] if p.pebble and p.role != "torso"]
PS = {p.name: part_surface(p, 0.06) for p in parts}
for vid in vids:
    S, lab, U = AS.cloud(vid, 0.05, 0.0, 0.55)
    tr = {k: cKDTree(S[m]) for k, m in (("all", np.ones(len(S), bool)), ("out", lab >= 1), ("in", lab != 1))}
    Sc, labc, Uc = AS.cloud(vid, 0.4, 0.0, 0.55)
    trc = cKDTree(Sc)
    R = {}
    for p in parts:
        Q = VB.to_local(PS[p.name], vid)
        ins = VB.inside_local(vid, Q)
        dc = trc.query(Q, workers=2)[0]
        near_ = dc < 3.3                      # coarse cloud (h 0.4) overestimates by <= 0.3: every point with a true wall < 3.0 is kept
        d = {}
        for k_, t in tr.items():
            dd = np.full(len(Q), 3.0)
            if near_.any():
                q_ = t.query(Q[near_], distance_upper_bound=3.6, workers=2)[0]
                dd[near_] = np.minimum(q_, 3.6)
            d[k_] = dd
        da = np.where(ins, d["all"], -d["all"])
        k = int(np.argmin(da)); q = PS[p.name][k]
        side = "out" if d["out"][k] <= d["in"][k] else "in"
        # wall measured on the cover side only (points whose nearest skin is the outer cover), as fit.py wall_out
        R[p.name] = dict(role=p.role, kind=p.kind, req_out=p.req_out, req_in=p.req_in, wall_min=round(float(da[k]), 3), nearest_half=side,
                         at=dict(x=round(float(q[0]), 2), r=round(math.hypot(q[1] - YA, q[2] - ZA), 2),
                                 az=round(math.degrees(math.atan2(q[2] - ZA, q[1] - YA)) % 360, 1), local=Q[k].round(2).tolist(),
                                 u=round(float(-Q[k, 2] / 72), 3)),
                         wall_to_cover=round(float(np.where(ins, d["out"], -d["out"]).min()), 3),
                         wall_to_inner=round(float(np.where(ins, d["in"], -d["in"]).min()), 3), n_outside=int((~ins).sum()))
    res[vid] = R
    d = R["DRV_unasac"]
    print(vid, "DRV wall_min", d["wall_min"], d["nearest_half"], d["at"], "to cover", d["wall_to_cover"], "to inner", d["wall_to_inner"], flush=True)
    for n, v in R.items():
        if n != "DRV_unasac" and (v["wall_to_cover"] < 3.0 or v["wall_to_inner"] < 3.0):
            print("    %-20s %-6s cover %.3f (req %.1f) inner %.3f (req %.1f) out %d" % (n, v["role"], v["wall_to_cover"], v["req_out"], v["wall_to_inner"], v["req_in"], v["n_outside"]))
json.dump(res, open("out/own_fit_%s.json" % "_".join(vids), "w"), indent=1)
