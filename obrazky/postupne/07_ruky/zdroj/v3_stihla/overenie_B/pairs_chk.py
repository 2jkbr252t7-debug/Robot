"""Independent verifier (R3/overenie_B): sliding clearances between joint parts that move against each other (own code).
Full revolution vs anything: exact 2-D (x, r) polygon distance (own segment-segment code).  Rib (arm sector) vs lug (static
sector): 3-D, rib swept over -45..+135 deg in 0.25 deg steps, fine samples (0.03).  Designed contacts are skipped and listed.
Also: clutch magnet pockets (count / web), and the stop contact angles.
usage: pairs_chk.py <option> -> pairs_<option>.json"""
import sys, os, math, json, itertools
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as PT  # noqa: E402
YA, ZA = 3.0, -17.0
oid = sys.argv[1]
opt = PT.options()[oid]


def seg_seg(a, b, c, d):
    """min distance between 2-D segments ab and cd"""
    def pt_seg(p, a, b):
        ab = b - a; t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-15), 0, 1)
        return np.linalg.norm(p - (a + t * ab))

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2, d3, d4 = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
    if (d1 * d2 < 0) and (d3 * d4 < 0):
        return 0.0
    return min(pt_seg(c, a, b), pt_seg(d, a, b), pt_seg(a, c, d), pt_seg(b, c, d))


def inpoly(p, P):
    return bool(PT._inpoly(np.atleast_2d(p), P)[0])


def poly_gap(P, Q):
    """>0 gap, <=0 touching/overlap (overlap -> -1 marker if a vertex is strictly inside)"""
    P, Q = np.asarray(P, float), np.asarray(Q, float)
    for p in P:
        if inpoly(p, Q):
            return -1.0
    for q in Q:
        if inpoly(q, P):
            return -1.0
    m = 1e9
    for i in range(len(P)):
        for j in range(len(Q)):
            m = min(m, seg_seg(P[i], P[(i + 1) % len(P)], Q[j], Q[(j + 1) % len(Q)]))
    return m


def prof(p):
    return p.outline_xr() if p.mag is not None else p.prof


contacts = set(tuple(sorted(c)) for c in opt["contacts"])
rigid = set(tuple(sorted(c)) for c in opt.get("rigid", []))
parts = [p for p in opt["parts"] if p.role != "torso"]
OUT = dict(option=oid, pairs={}, skipped_contacts=sorted(map(list, contacts)), rigid=sorted(map(list, rigid)))
for a, b in itertools.combinations(parts, 2):
    if a.role == b.role or (a.mag is not None and b.mag is not None):
        continue
    key = tuple(sorted((a.name, b.name)))
    if key in contacts or key in rigid:
        continue
    if a.mag is not None or b.mag is not None:
        # a magnet against a part of another role: the magnet ring (it turns with the drive hub)
        pass
    if a.az is not None and b.az is not None:
        arm_p, st_p = (a, b) if a.role == "arm" else (b, a)

        def sector_cloud(p, h=0.03):
            P = np.asarray(p.prof, float); x0, x1 = P[:, 0].min(), P[:, 0].max(); r0, r1 = P[:, 1].min(), P[:, 1].max()
            pts = []
            a0, a1 = p.az
            for x in np.arange(x0, x1 + 1e-9, h):
                for r in np.arange(r0, r1 + 1e-9, h):
                    if not (inpoly((x, r), P) or abs(x - x1) < 1e-9 or abs(r - r1) < 1e-9 or abs(x - x0) < 1e-9 or abs(r - r0) < 1e-9):
                        continue
                    # boundary of the solid only: faces + end caps
                    on_face = abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9 or abs(r - r0) < 1e-9 or abs(r - r1) < 1e-9
                    if on_face:
                        n = max(2, int(math.radians(a1 - a0) * r / h) + 1)
                        ph = np.radians(np.linspace(a0, a1, n))
                    else:
                        ph = np.radians(np.array([a0, a1]))
                    pts.append(np.c_[np.full(len(ph), x), np.full(len(ph), r), ph])
            return np.concatenate(pts)
        A = sector_cloud(arm_p); B = sector_cloud(st_p)
        Bx = np.c_[B[:, 0], YA + B[:, 1] * np.cos(B[:, 2]), ZA + B[:, 1] * np.sin(B[:, 2])]
        tr = cKDTree(Bx)
        best = (1e9, None)
        for s in np.r_[np.arange(-45.0, 135.001, 0.25)]:
            ph = A[:, 2] - math.radians(s)              # swing s rotates arm parts by -s in this azimuth convention
            Ax = np.c_[A[:, 0], YA + A[:, 1] * np.cos(ph), ZA + A[:, 1] * np.sin(ph)]
            d, _ = tr.query(Ax, distance_upper_bound=3.0)
            if d.min() < best[0]:
                best = (float(d.min()), float(s))
        OUT["pairs"][f"{a.name} | {b.name}"] = dict(gap=round(best[0], 3), at_swing=best[1], kind="3D sweep -45..135")
        # contact angles
        cont = {}
        for s in (-51.0, 140.5):
            ph = A[:, 2] - math.radians(s)
            Ax = np.c_[A[:, 0], YA + A[:, 1] * np.cos(ph), ZA + A[:, 1] * np.sin(ph)]
            cont[str(s)] = round(float(tr.query(Ax)[0].min()), 3)
        OUT["stop_contact_gap"] = cont
    else:
        g = poly_gap(prof(a), prof(b))
        OUT["pairs"][f"{a.name} | {b.name}"] = dict(gap=round(g, 3), kind="2D profile (exact for a full revolution)")
mins = sorted(OUT["pairs"].items(), key=lambda kv: kv[1]["gap"])
OUT["min_pair"] = dict(pair=mins[0][0], gap=mins[0][1]["gap"])
OUT["below_0p3"] = [k for k, v in OUT["pairs"].items() if v["gap"] < 0.3 - 1e-6]
# clutch magnets: count, pitch, web between pockets (pocket D = magnet D + 0.1)
mags = [p for p in opt["parts"] if p.mag is not None and p.role == "drive"]
if mags:
    m = mags[0].mag
    pitch = 2 * m["r"] * math.sin(math.pi / len(mags))
    OUT["magnets"] = dict(count=len(mags), r=m["r"], d=m["d"], x=[m["x0"], m["x1"]], chord_pitch=round(pitch, 3),
                          web_between_pockets=round(pitch - (m["d"] + 0.1), 3))
for k, v in mins[:10]:
    print(f"{k:44s} {v['gap']}  {v['kind']}")
print("below 0.3:", OUT["below_0p3"]); print("stop contact gaps:", OUT.get("stop_contact_gap")); print("magnets:", OUT.get("magnets"))
json.dump(OUT, open(os.path.join(HERE, f"pairs_{oid}.json"), "w"), indent=1)
