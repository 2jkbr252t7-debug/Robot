"""Q5: pebble swept about the shoulder axis (-45 .. +135 deg) against T_bok_L, T_stred, T_klb_L, base top, desk."""
import json, time
from armgeo import *
from scipy.spatial import cKDTree
t0 = time.time()
ANG = list(range(-45, 136, 5))


def unswing(Q, deg):
    return swing(Q, -deg)


res = {}
# ---- torso meshes: surface samples (only x > 42: the pebble never comes below x 49.5, rotation about X keeps x)
for nm in ("T_bok_L", "T_stred", "T_klb_L"):
    T = load(nm)
    P = vlib.sample_surface(T, 0.3)
    print(nm, "max x of the part %.3f" % T[..., 0].max(), flush=True)
    P = P[P[:, 0] > 42.0]
    if not len(P):
        res[nm] = dict(n=0, min=round(49.498 - T[..., 0].max(), 3), note="part lies entirely at x < 42: lower bound = pebble min x - part max x")
        print(nm, "no samples beyond x 42 -> clearance >= %.2f" % (49.498 - T[..., 0].max()), flush=True); continue
    if nm == "T_klb_L":
        r = np.hypot(P[:, 1] - SH_Y, P[:, 2] - ZS)
        P = P[(P[:, 0] <= 51.3) & (r >= 11.2)]          # shoulder ring + body (the journal is meant to be inside the arm hub)
    per = []
    for a in ANG:
        sd = sdf_world(unswing(P, a))
        k = sd.argmin()
        per.append((a, float(sd[k]), P[k].round(2).tolist()))
    w = min(per, key=lambda t: t[1])
    res[nm] = dict(n=len(P), per_angle={a: round(d, 3) for a, d, _ in per}, min=round(w[1], 3), at_angle=w[0], at_point=w[2])
    print("%-8s n %6d  min signed clearance %.3f at arm %+d deg, torso point %s   (%.0f s)" % (nm, len(P), w[1], w[0], w[2], time.time() - t0))
    print("    by angle:", " ".join("%d:%.2f" % (a, d) for a, d, _ in per))
# refine T_bok_L / T_stred around their minimum with 1 deg steps
for nm in ("T_bok_L",):
    T = load(nm); P = vlib.sample_surface(T, 0.12); P = P[P[:, 0] > 42.0]
    P = P[np.linalg.norm(P - np.array(res[nm]["at_point"]), axis=1) < 12.0]
    a0 = res[nm]["at_angle"]
    best = (9e9, None, None)
    for a in np.arange(max(-45, a0 - 10), min(135, a0 + 5) + 0.01, 1.0):
        sd = sdf_world(unswing(P, a)); k = sd.argmin()
        if sd[k] < best[0]: best = (float(sd[k]), float(a), P[k].round(2).tolist())
        print("   fine %s arm %+.0f deg: %.3f at %s" % (nm, a, sd[k], P[k].round(2)), flush=True)
    res[nm]["fine"] = dict(min=round(best[0], 3), angle=best[1], point=best[2])
    print("   fine", nm, best)
# ---- base, desk, reach
C = pebble_cloud(0.3); W0 = to_world(C)
be, bz = S.base_stations(0.25)
BP = np.concatenate([np.column_stack([S.base_section(e, 2400), np.full(2400, Z_BASE_TOP - z)]) for e, z in zip(be, bz) if z < 20])
btree = cKDTree(BP)
low = []
for a in ANG + [-3, -2, -1]:
    Wa = swing(W0, a)
    zmin = Wa[:, 2].min(); k = Wa[:, 2].argmin()
    d, _ = btree.query(Wa[Wa[:, 2] < -60] if (Wa[:, 2] < -60).any() else Wa[:1])
    rxy = np.hypot(Wa[:, 0], Wa[:, 1]).max()
    low.append((a, float(zmin), float(d.min()), float(rxy), Wa[k].round(2).tolist()))
low.sort()
wl = min(low, key=lambda t: t[1]); wb = min(low, key=lambda t: t[2])
res["base"] = dict(z_lowest=round(wl[1], 3), at_angle=wl[0], at=wl[4], above_flat_base_top=round(wl[1] - Z_BASE_TOP, 3),
                   true_dist_real_base_J1_0=round(wb[2], 3), at_angle_true=wb[0], above_desk=round(wl[1] - Z_DESK, 3),
                   per_angle={a: dict(zmin=round(z, 2), d_base=round(d, 2), rxy=round(r, 2)) for a, z, d, r, _ in low})
print("lowest pebble point over the sweep: z %.3f at arm %+d deg %s -> above base top (flat, any J1) %.3f, above desk %.3f; true distance to the real base (J1 0) min %.3f at %+d deg" %
      (wl[1], wl[0], wl[4], wl[1] - Z_BASE_TOP, wl[1] - Z_DESK, wb[2], wb[0]))
print("per angle (z_min, d_base, max r_xy):", [(a, round(z, 1), round(d, 1), round(r, 1)) for a, z, d, r, _ in low])
tipW = to_world(np.array([0, 0, -L]))
res["reach"] = dict(max_x=round(float(W0[:, 0].max()), 3), tip_x=round(float(tipW[0]), 3), max_rxy=round(max(t[3] for t in low), 3),
                    max_rxy_angle=max(low, key=lambda t: t[3])[0])
print("lateral reach: max x of the pebble %.3f (constant over the sweep), bottom tip x %.3f; max radius from the J1 axis %.3f at arm %+d deg" %
      (W0[:, 0].max(), tipW[0], res["reach"]["max_rxy"], res["reach"]["max_rxy_angle"]))
tip_path = {a: swing(tipW, a).round(2).tolist() for a in (-45, 0, 45, 90, 135)}
print("bottom tip positions:", tip_path)
res["tip_path"] = tip_path
json.dump(res, open("q5_out.json", "w"), indent=1)
print("done %.0f s" % (time.time() - t0))
