"""overenie_C/own_fit_C.py - verifier's OWN fit check of the joint packaging options M1..M4 in shape variant C.
Independent of mech/fit.py: own arm surface (geomC: adaptive param cloud, spacing <= 0.04 / 0.03 mm), own part sampling
(only the (x, r) profile numbers and roles are read from mech/parts.py), own rules, own 2-D polygon distances, own stop
geometry.  Also: top dome above the hub, seam surface vs parts, black tip plane vs parts.
usage: /opt/venv/cad/bin/python own_fit_C.py [C|0] [M1,M2,...]"""
import sys, os, math, json, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import geomC as G
import parts as PT          # part DATA only (profiles, roles, kinds); sampling and rules are mine

YA, ZA = 3.0, -17.0
H = 0.06                    # part surface sampling
SLIDE, COVER = 0.3, 1.2
RHOLE = 7.0                 # arm hole radius for the plug ring (inner-shell rule waived inside r < RHOLE - 0.3)


def sample_part(p, h=H):
    """own surface sampling of a part in frame B"""
    if p.mag is not None:
        m = p.mag; a = math.radians(m["az"]); rr = m["d"] / 2
        cy, cz = YA + m["r"] * math.cos(a), ZA + m["r"] * math.sin(a)
        th = np.linspace(0, 2 * np.pi, max(24, int(2 * np.pi * rr / h)), endpoint=False)
        xs = np.linspace(m["x0"], m["x1"], max(2, int((m["x1"] - m["x0"]) / h) + 1))
        out = [np.c_[np.repeat(xs, len(th)), np.tile(cy + rr * np.cos(th), len(xs)), np.tile(cz + rr * np.sin(th), len(xs))]]
        for x in (m["x0"], m["x1"]):
            for rho in np.linspace(0, rr, max(2, int(rr / h) + 1)):
                n = max(1, int(2 * np.pi * rho / h))
                t = np.linspace(0, 2 * np.pi, n, endpoint=False)
                out.append(np.c_[np.full(n, x), cy + rho * np.cos(t), cz + rho * np.sin(t)])
        return np.concatenate(out)
    P = np.asarray(p.prof, float)
    E = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n = max(2, int(math.ceil(np.hypot(*(b - a)) / h)))
        t = np.linspace(0, 1, n, endpoint=False)
        E.append(a + t[:, None] * (b - a))
    E = np.concatenate(E)
    a0, a1 = (0.0, 360.0) if p.az is None else p.az
    out = []
    for x, r in E:
        n = max(1, int(math.radians(a1 - a0) * r / h) + 1) if r > 1e-9 else 1
        ph = np.radians(np.linspace(a0, a1, n, endpoint=p.az is not None))
        out.append(np.c_[np.full(n, x), YA + r * np.cos(ph), ZA + r * np.sin(ph)])
    if p.az is not None:
        x0, x1 = P[:, 0].min(), P[:, 0].max(); r0, r1 = P[:, 1].min(), P[:, 1].max()
        X, Rr = np.meshgrid(np.arange(x0, x1 + 1e-9, h), np.arange(r0, r1 + 1e-9, h), indexing="ij")
        Q = np.c_[X.ravel(), Rr.ravel()]
        Q = Q[PT._inpoly(Q, P)]
        for a in (a0, a1):
            out.append(np.c_[Q[:, 0], YA + Q[:, 1] * math.cos(math.radians(a)), ZA + Q[:, 1] * math.sin(math.radians(a))])
    return np.concatenate(out)


# ------------------------------------------------------------------------------------------- exact 2-D polygon distance
def seg_seg(p1, p2, q1, q2):
    """min distance between segments (vectorised over the first set: p1, p2 (n, 2); q1, q2 (2,))"""
    def pt_seg(P, A, B):
        AB = B - A; L2 = (AB ** 2).sum(-1)
        t = np.clip(((P - A) * AB).sum(-1) / np.maximum(L2, 1e-18), 0, 1)
        return np.linalg.norm(P - (A + t[..., None] * AB), axis=-1)
    d = np.minimum.reduce([pt_seg(p1, q1, q2), pt_seg(p2, q1, q2), pt_seg(np.broadcast_to(q1, p1.shape), p1, p2),
                           pt_seg(np.broadcast_to(q2, p1.shape), p1, p2)])
    # proper intersection -> 0
    def cross(o, a, b):
        return (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])
    d1 = cross(p1, p2, np.broadcast_to(q1, p1.shape)); d2 = cross(p1, p2, np.broadcast_to(q2, p1.shape))
    d3 = cross(np.broadcast_to(q1, p1.shape), np.broadcast_to(q2, p1.shape), p1)
    d4 = cross(np.broadcast_to(q1, p1.shape), np.broadcast_to(q2, p1.shape), p2)
    inter = (d1 * d2 < 0) & (d3 * d4 < 0)
    return np.where(inter, 0.0, d)


def poly_gap(A, B):
    """exact distance between two closed polygons; negative (-1) if one overlaps the other's interior"""
    A, B = np.asarray(A, float), np.asarray(B, float)
    a1, a2 = A, np.roll(A, -1, 0)
    d = min(float(seg_seg(a1, a2, B[j], B[(j + 1) % len(B)]).min()) for j in range(len(B)))
    # interior overlap: a vertex strictly inside the other polygon, or a tiny probe of the edge midpoints
    mA = 0.5 * (a1 + a2); b1, b2 = B, np.roll(B, -1, 0); mB = 0.5 * (b1 + b2)
    if d < 1e-9:
        # touching or overlapping: probe points slightly inside A near the contact
        cA = A.mean(0); cB = B.mean(0)
        pa = A + 1e-4 * (cA - A); pb = B + 1e-4 * (cB - B)
        if PT._inpoly(pa, B).any() or PT._inpoly(pb, A).any() or PT._inpoly(mA + 1e-4 * (cA - mA), B).any():
            return -1.0
    return d


def moving(r1, r2):
    return not ("torso" in (r1, r2) or r1 == r2)


# ------------------------------------------------------------------------------------------------- the check
def run(vid="C", oids=("M1", "M2", "M2b", "M3", "M4")):
    shp = G.SHAPE_C if vid == "C" else G.SHAPE_0
    t0 = time.time()
    sdf = G.SDF(shp, 0.0, 0.62, ds=0.04, dth=0.03)          # local z 0 .. -44.6 covers every part (|z+15.8| <= 15)
    print(f"arm cloud {sdf.n} pts ({time.time() - t0:.0f} s)", flush=True)
    from scipy.spatial import cKDTree
    Cd = sdf.C[(-sdf.C[:, 2] / G.L) < 0.12]
    Cd = Cd[::7]                                            # dome patch, about 0.1 mm spacing is enough for a report
    t_dome = cKDTree(Cd)
    tip_pt, tip_n = tip_plane(shp)
    res = {}
    for oid in oids:
        opt = PT.options()[oid]
        parts = opt["parts"]
        R = dict(option=oid, title=opt["title"], parts={}, pairs={}, stop=None)
        worst = (9e9, None)
        for p in parts:
            if p.role == "torso" or not p.pebble:
                continue
            Q = sample_part(p)
            Pl = G.to_local(Q)
            u = np.clip(-Pl[:, 2] / G.L, 0, 1)
            seam = shp.sec(u)[0]
            ds = Pl[:, 0] - seam                          # + = cover side of the seam surface
            w_out, ins = sdf.query(Pl, "out"); w_in, _ = sdf.query(Pl, "inn")
            d_out, d_in = np.abs(w_out), np.abs(w_in)
            near_out = d_out <= d_in
            dmin = np.minimum(d_out, d_in)
            w_all = np.where(ins, dmin, -dmin)          # + wall to the nearest surface, - depth outside
            rq = np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA)
            hole = rq < RHOLE - SLIDE
            printed_arm = p.role == "arm" and p.kind == "printed"
            steel_arm = p.role == "arm" and p.kind != "printed"
            if printed_arm:
                req = COVER
                # cover rule only for hub points on the cover side of the seam; inner-side points are A_vnut material
                cov = ds >= 0
                crit = np.where(cov | ((~ins) & near_out), w_all, 9.0)
                outside_bad = (~ins) & near_out                  # poking out through the OUTER surface
                outside_inner = (~ins) & ~near_out & ~hole       # poking out through the inner surface (would be trimmed)
            elif steel_arm:
                req = COVER
                crit = w_all
                outside_bad = ~ins; outside_inner = np.zeros(len(Q), bool)
            else:                                   # drive / static: 0.3 sliding + 1.2 wall
                req = SLIDE + COVER
                waive = hole & ~near_out                         # inside the arm's ring hole: no inner-shell rule
                crit = np.where(waive, np.where(ins, d_out, 9.0), w_all)
                outside_bad = (~ins) & ~waive; outside_inner = np.zeros(len(Q), bool)
            k = int(np.argmin(crit))
            m = float(crit[k] - req)
            top = Pl[:, 2] > np.percentile(Pl[:, 2], 80)
            dd, _ = t_dome.query(Pl[top], distance_upper_bound=12.0, workers=3)
            kd = int(np.argmin(dd))
            tipd = (Pl - tip_pt) @ tip_n
            q = Q[k]
            R["parts"][p.name] = dict(
                role=p.role, kind=p.kind, req=req, min_wall=round(float(crit[k]), 3), margin=round(m, 3),
                at=dict(x=round(float(q[0]), 2), r=round(float(rq[k]), 2),
                        az=round(math.degrees(math.atan2(q[2] - ZA, q[1] - YA)) % 360, 1), local=Pl[k].round(2).tolist()),
                n_outside_outer=int(outside_bad.sum()), n_outside_inner_trimmed=int(outside_inner.sum()),
                seam_rel=[round(float(ds.min()), 2), round(float(ds.max()), 2)],
                min_to_outer=round(float(w_out.min()), 3), min_to_inner=round(float(w_in.min()), 3),
                crosses_seam=bool(ds.min() < -0.25 and ds.max() > 0.25),
                dome_dist=round(float(dd[kd]), 2), tip_plane_min=round(float(-tipd.max()), 1),
                ok=bool(m >= -1e-3 and not outside_bad.any()))
            if m < worst[0]:
                worst = (m, p.name)
        # ---- pairwise sliding clearances (shape independent), exact 2-D where possible
        solid = [p for p in parts if p.role != "torso"]
        contacts = set(tuple(sorted(c)) for c in opt["contacts"]) | set(tuple(sorted(c)) for c in opt.get("rigid", []))
        for i, a in enumerate(solid):
            for b in solid[i + 1:]:
                key = tuple(sorted((a.name, b.name)))
                if not moving(a.role, b.role) or key in contacts:
                    continue
                if a.mag is not None or b.mag is not None:
                    continue        # magnets sit inside the drive-hub profile (containment checked below); the 0.25 skin
                                    # between a magnet and the friction washer is the designed friction face
                if a.az is not None and b.az is not None:
                    g = sector_gap(a, b)
                else:
                    g = poly_gap(a.outline_xr(), b.outline_xr())
                    if (a.mag is not None) or (b.mag is not None):
                        pass
                R["pairs"][f"{a.name} | {b.name}"] = round(g, 3)
        # magnets inside the drive hub
        hub = next((p for p in parts if p.name == "DRV_unasac"), None)
        if hub is not None:
            for p in parts:
                if p.mag is not None and p.role == "drive":
                    x0, x1, r0, r1 = p.xr_bounds()
                    corners = np.array([(x0 + 1e-3, r0 + 1e-3), (x1 - 1e-3, r0 + 1e-3), (x1 - 1e-3, r1 - 1e-3), (x0 + 1e-3, r1 - 1e-3)])
                    if not PT._inpoly(corners, hub.prof).all():
                        R["pairs"][f"{p.name} not inside DRV_unasac"] = -1.0
        pm = min(R["pairs"].items(), key=lambda kv: kv[1]) if R["pairs"] else (None, 9)
        R["min_pair"] = dict(pair=pm[0], gap=pm[1], ok=bool(pm[1] >= SLIDE - 1e-3))
        if opt.get("stop"):
            R["stop"] = stop_check(parts)
        R["fits"] = bool(all(v["ok"] for v in R["parts"].values()) and R["min_pair"]["ok"] and (R["stop"] is None or R["stop"]["ok"]))
        R["governing"] = dict(part=worst[1], margin=round(worst[0], 3), at=R["parts"][worst[1]]["at"])
        res[oid] = R
        print_opt(R)
    return res


def sector_gap(a, b):
    """stop rib (arm) vs lug (static), over the swing -45..+135: min 3-D distance from own dense clouds"""
    from scipy.spatial import cKDTree
    arm_p, st_p = (a, b) if a.role == "arm" else (b, a)
    ca = sample_part(arm_p, 0.05); cs = sample_part(st_p, 0.05)
    tr = cKDTree(cs)
    best = 9.0
    for s in np.r_[np.arange(-45.0, 135.0, 1.0), 135.0]:
        d, _ = tr.query(G.swing(ca, s), distance_upper_bound=6.0)
        best = min(best, float(d.min()))
    return best


def stop_check(parts):
    """analytic: rib sector and lug sector angular gaps at -45 / +135 and contact angles; arc gap at the smallest common r"""
    lug = next(p for p in parts if p.name == "PLG_doraz"); rib = next(p for p in parts if p.name == "ARM_rebro")
    l0, l1 = lug.az; r0, r1 = rib.az
    # axial / radial overlap of the two profiles
    lx0, lx1, lr0, lr1 = lug.xr_bounds(); rx0, rx1, rr0, rr1 = rib.xr_bounds()
    xo = (max(lx0, rx0), min(lx1, rx1)); ro = (max(lr0, rr0), min(lr1, rr1))
    # swing s turns arm parts by -s in azimuth (armgeo.swing: + = forward/up, tip to -Y)
    def gaps(s):
        lo, hi = r0 - s, r1 - s
        g_hi = ((l0 - hi) % 360.0)          # rib upper edge to lug start (backward swing contact)
        g_lo = ((lo - l1) % 360.0)          # lug end to rib lower edge (forward swing contact)
        return min(g_hi, g_lo)
    ang = {s: gaps(s) for s in (-51.0, -45.0, 135.0, 140.5)}
    rmin = ro[0]
    arc = {s: 2 * rmin * math.sin(math.radians(v) / 2) for s, v in ang.items()}
    # check numerically with own clouds at those angles
    from scipy.spatial import cKDTree
    ca = sample_part(rib, 0.04); cs = sample_part(lug, 0.04); tr = cKDTree(cs)
    num = {s: float(tr.query(G.swing(ca, s))[0].min()) for s in ang}
    ok = num[-45.0] >= SLIDE and num[135.0] >= SLIDE and num[-51.0] < 0.12 and num[140.5] < 0.12
    return dict(overlap_x=xo, overlap_r=ro, ang_gap_deg={str(k): round(v, 2) for k, v in ang.items()},
                arc_gap_analytic={str(k): round(v, 3) for k, v in arc.items()}, gap_numeric={str(k): round(v, 3) for k, v in num.items()},
                ok=bool(ok))


def tip_plane(shp):
    ut = shp.p["utip"]
    c = float(shp.sec(ut)[0])
    n = np.array([-0.50, -0.35, -0.79]); n /= np.linalg.norm(n)
    return np.array([c, 0.0, -G.L * ut]), n


def print_opt(R):
    print(f"\n=== {R['option']} {R['title']} : FITS {'YES' if R['fits'] else 'NO'}  governing {R['governing']}")
    print("%-22s %-6s %5s %8s %7s %5s %5s  %-16s %6s %6s" % ("part", "role", "req", "minwall", "margin", "outO", "outI", "seam rel x", "dome", "tip"))
    for k, v in R["parts"].items():
        print("%-22s %-6s %5.2f %8.2f %7.2f %5d %5d  %-16s %6.2f %6.1f %s" % (k, v["role"], v["req"], v["min_wall"], v["margin"],
              v["n_outside_outer"], v["n_outside_inner_trimmed"], str(v["seam_rel"]), v["dome_dist"], v["tip_plane_min"],
              "ok" if v["ok"] else "NO"))
    print("min sliding clearance:", R["min_pair"])
    if R["stop"]:
        print("stop:", R["stop"])


if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "C"
    oids = sys.argv[2].split(",") if len(sys.argv) > 2 else ["M1", "M2", "M2b", "M3", "M4"]
    res = run(vid, oids)
    json.dump(res, open(os.path.join(HERE, f"own_fit_{vid}.json"), "w"), indent=1)
