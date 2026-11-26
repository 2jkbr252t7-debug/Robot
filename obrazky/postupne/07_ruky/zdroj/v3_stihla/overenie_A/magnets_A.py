"""Verifier: cover magnets (Ø3x2 in bosses r 2.2 x 2.4 each side of the seam, v1geo concept spots u 0.16 / 0.66,
3.5 inside the outline) vs the joint parts; pre-existing check on the current arm with B1+ (M1) and search for spots
that work in variant A with M2b.  Requirement used: boss >= 0.3 from drive/static parts (they move against the arm),
>= 0.2 from steel arm parts (washer, bearing ring: no overlap + glue gap), magnet pocket back wall >= 1.2."""
import sys, os, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/overenie_A")
import geomA as G
import own_fit as OF
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as PT
O = PT.options()


def boss_points(m, h=0.1):
    pts = []
    for side in (1, -1):
        for x in np.arange(0.25, 2.65 + 1e-9, h):
            n = int(2 * np.pi * 2.2 / h)
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            pts.append(np.c_[np.full(n, side * x), m[1] + 2.2 * np.cos(th), m[2] + 2.2 * np.sin(th)])
        for rho in np.arange(0, 2.2 + 1e-9, h):
            n = max(1, int(2 * np.pi * rho / h))
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            pts.append(np.c_[np.full(n, side * 2.65), m[1] + rho * np.cos(th), m[2] + rho * np.sin(th)])
    return np.concatenate(pts)


def outer_x_at(y, z, ko, kw):
    u = -z / G.L
    hw, ht = G.prof(u)
    a = np.clip(np.abs(y) / (kw * hw), 0, 1)
    return ko * ht * (1 - a ** 2.3) ** (1 / 2.3)


def boss_vs_parts(m, oid):
    W = G.to_world(boss_points(m))
    res = {}
    for p in O[oid]["parts"]:
        if p.role == "torso" or not p.pebble:
            continue
        res[p.name] = float(OF.dist_part(W, p).min())
    return res


def back_wall(m, ko, kw, inset):
    th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    return float(outer_x_at(m[1] + 1.55 * np.cos(th), m[2] + 1.55 * np.sin(th), ko, kw).min()) - 2.30


out = {}
for vid, ko, kw, oid in (("0", 1.0, 1.0, "M1"), ("0", 1.0, 1.0, "M2b"), ("A", 0.62, 0.95, "M2b"), ("A", 0.62, 0.95, "M3")):
    rows = []
    for u, sgn in ((0.16, -1), (0.16, 1), (0.66, -1), (0.66, 1)):
        hw, ht = G.prof(u)
        m = np.array([0.0, sgn * (kw * float(hw) - 3.5), -G.L * u])
        r = boss_vs_parts(m, oid)
        worst = sorted(r.items(), key=lambda kv: kv[1])[:3]
        rows.append(dict(u=u, y=round(float(m[1]), 2), worst=[(k, round(v, 2)) for k, v in worst], back_wall=round(back_wall(m, ko, kw, 3.5), 2)))
    out[f"{vid}+{oid}"] = rows
    for r_ in rows:
        print(vid, oid, r_)

# search: upper magnet pair for A + M2b (u 0.02..0.45, inset 3.5..5.0 from the outline), lower pair back wall
cands = []
for u in np.arange(0.03, 0.46, 0.01):
    hw, ht = G.prof(u)
    for ins in (3.5, 4.0, 4.5, 5.0):
        ok_all = True; worst = 9.0; bw = 9.0
        for sgn in (-1, 1):
            m = np.array([0.0, sgn * (0.95 * float(hw) - ins), -G.L * u])
            r = boss_vs_parts(m, "M2b")
            for k, v in r.items():
                p = next(q for q in O["M2b"]["parts"] if q.name == k)
                req = 0.3 if p.role in ("drive", "static") else 0.2
                worst = min(worst, v - req)
            bw = min(bw, back_wall(m, 0.62, 0.95, ins))
        cands.append(dict(u=round(float(u), 2), inset=ins, clash_margin=round(worst, 2), back_wall=round(bw, 2),
                          ok=bool(worst >= 0 and bw >= 1.2)))
ok = [c for c in cands if c["ok"]]
print("upper-pair spots that work (A + M2b):", [(c["u"], c["inset"], c["clash_margin"], c["back_wall"]) for c in ok][:40])
low = []
for u in (0.60, 0.62, 0.64, 0.66):
    hw, ht = G.prof(u)
    for ins in (3.5, 4.0, 4.5, 5.0):
        m = np.array([0.0, (0.95 * float(hw) - ins), -G.L * u])
        low.append((u, ins, round(back_wall(m, 0.62, 0.95, ins), 2)))
print("lower pair back wall (u, inset, wall):", low)
out["search_upper"] = cands; out["lower_back_wall"] = low
json.dump(out, open("/tmp/claude-0/gapwf/fin/R3/overenie_A/magnets_A.json", "w"), indent=1)
