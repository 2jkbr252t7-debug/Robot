"""Passive arm (approved T3 pebble placed by armgeo.to_world with dx) vs the approved torso exterior (analytic outer surface
of t4_common = every white torso part).  Coarse pass: arm inner-half cloud 0.6 mm, angles every 5 deg, KD query capped at
8 mm; fine pass: arm cloud 0.2 mm around the closest region, 0.5 deg steps.  dx moves the arm rigidly along X
(dx < 0 = toward the torso).  Writes armgap.json"""
import sys, json, os, time
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); import armgeo as G
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); os.chdir("/tmp/claude-0/gapwf/fin/T4"); import t4_common as C
t0 = time.time()
_, TREE = C.outer_cloud(0.16)
def dist(Q):
    d, _ = TREE.query(Q, distance_upper_bound=8.0); d = np.minimum(d, 8.0)
    return np.where(C.inside_outer(Q), -d, d)
Pc = G.pebble_cloud(0.6); Pc = Pc[Pc[:, 0] < 2.0]
Pf = G.pebble_cloud(0.2); Pf = Pf[Pf[:, 0] < 2.0]
print("arm pts coarse / fine", len(Pc), len(Pf), f"{time.time()-t0:.0f}s", flush=True)
angs = np.arange(-45.0, 135.01, 5.0)
W0 = G.to_world(Pc, dx=0.0)
coarse = {}
for a in angs:
    d = dist(G.swing(W0, a)); coarse[a] = d
print("coarse dx0 done", f"{time.time()-t0:.0f}s", flush=True)
out = {}
for dx in (0.0, -0.5, -1.0, -1.5, -2.0, -3.0):
    g = {}
    for a in angs:
        near = coarse[a] < 6.0 - dx                      # candidates (dx < 0 brings points closer by <= |dx|)
        if not near.any(): g[a] = 8.0; continue
        Q = G.swing(G.to_world(Pc[near], dx=dx), a); g[a] = float(dist(Q).min())
    a_min = min(g, key=g.get)
    # fine pass around a_min with the 0.2 cloud restricted to the closest region
    Qc = G.swing(G.to_world(Pc, dx=dx), a_min); dc = dist(Qc); loc = Pc[dc < dc.min() + 3.0]
    lo_, hi_ = loc.min(0) - 2.0, loc.max(0) + 2.0
    Pfl = Pf[np.all((Pf >= lo_) & (Pf <= hi_), axis=1)]
    best = (9.0, None, None)
    for a in np.arange(max(-45.0, a_min - 5.0), min(135.0, a_min + 5.0) + 1e-9, 0.5):
        Q = G.swing(G.to_world(Pfl, dx=dx), a); d = dist(Q); j = int(np.argmin(d))
        if d[j] < best[0]: best = (float(d[j]), float(a), Q[j].round(2).tolist())
    rest = G.swing(G.to_world(Pf, dx=dx), 0.0); dr = float(dist(rest).min())
    xs = np.linspace(46.0, 56.0, 4001); Qax = np.stack([xs, np.full_like(xs, 3.0), np.full_like(xs, -17.0)], 1)
    ins = G.sdf_world(Qax, dx=dx, dmax=12.0) < 0
    out[str(dx)] = dict(gap_rest=round(dr, 2), min_gap=round(best[0], 2), at_deg=best[1], arm_point_world=best[2],
                        arm_skin_x_on_axis=round(float(xs[np.argmax(ins)]), 2) if ins.any() else None,
                        gap_by_angle_coarse={f"{a:+.0f}": round(v, 2) for a, v in g.items()})
    print(dx, {k: v for k, v in out[str(dx)].items() if k != "gap_by_angle_coarse"}, f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/armgap.json", "w"), indent=1)
