"""Verifier: independent fit check of the joint options M1..M4 inside arm variant A (left arm, rest; the joint parts are
coaxial with the shoulder axis, so the result is swing-independent except for the stop).
Method (different from fit.py):
  * arm surface = parametric (u, arc length) samples of my own re-implementation geomA (spacing 0.05 mm), no ray bisection;
  * full-revolution part vs arm: EXACT meridian distance - every arm surface point is mapped to (x, r) about the shoulder
    axis and its 2-D distance to the part's (x, r) polygon is computed (segment distance, sign by point-in-polygon);
  * sector parts: meridian distance inside the azimuth range, else exact distance to the nearer planar end face;
  * magnets (cylinders || X): exact cylinder distance;
  * pairs: exact 2-D polygon distance written here; stop: analytic angular gap r_min * sin(d_az).
Part geometry = parts.py (the design input), cross-checked against the option texts in the brief (see report)."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomA as G  # noqa
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as PT  # noqa

YA, ZA = G.YA, G.ZA
RHOLE = 7.0
KOV = [G.KO, G.KW]


def pip(Pxy, Poly):
    x, y = Pxy[:, 0], Pxy[:, 1]
    ins = np.zeros(len(Pxy), bool)
    n = len(Poly)
    for i in range(n):
        x1, y1 = Poly[i]; x2, y2 = Poly[(i + 1) % n]
        c = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        ins ^= c & (x < xi)
    return ins


def seg_d(Pxy, A, B):
    AB = B - A; L2 = float(AB @ AB)
    t = np.clip(((Pxy - A) @ AB) / max(L2, 1e-12), 0, 1)
    return np.linalg.norm(Pxy - (A + t[:, None] * AB), axis=1)


def poly_d(Pxy, Poly):
    """signed 2-D distance of points to a closed polygon (negative inside)"""
    d = np.min([seg_d(Pxy, Poly[i], Poly[(i + 1) % len(Poly)]) for i in range(len(Poly))], axis=0)
    return np.where(pip(Pxy, Poly), -d, d)


def seg_seg(a, b, c, d):
    """min distance between 2-D segments ab and cd"""
    def ccw(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if (ccw(a, b, c) * ccw(a, b, d) < 0) and (ccw(c, d, a) * ccw(c, d, b) < 0):
        return 0.0
    return float(min(seg_d(np.array([c, d]), a, b).min(), seg_d(np.array([a, b]), c, d).min()))


def poly_poly(P, Q):
    """signed min distance between two polygons: >0 gap, <=0 touching / overlapping (overlap -> -1 flag)"""
    m = min(seg_seg(P[i], P[(i + 1) % len(P)], Q[j], Q[(j + 1) % len(Q)]) for i in range(len(P)) for j in range(len(Q)))
    # overlap: a vertex of one strictly inside the other (shrunk test)
    cP = P.mean(0); cQ = Q.mean(0)
    Ps = cP + (P - cP) * 0.999; Qs = cQ + (Q - cQ) * 0.999
    if pip(Ps, Q).any() or pip(Qs, P).any():
        return -1.0 if m > 0 else -1.0
    return m


def xr_az(W):
    y, z = W[:, 1] - YA, W[:, 2] - ZA
    return W[:, 0], np.hypot(y, z), np.degrees(np.arctan2(z, y)) % 360.0


def dist_part(W, p):
    """signed distance of world points W to part p (negative = point inside the part)"""
    x, r, az = xr_az(W)
    if p.mag is not None:
        m = p.mag
        a = math.radians(m["az"])
        cy, cz = YA + m["r"] * math.cos(a), ZA + m["r"] * math.sin(a)
        rho = np.hypot(W[:, 1] - cy, W[:, 2] - cz)
        dr = rho - m["d"] / 2
        dxx = np.maximum(m["x0"] - x, x - m["x1"])
        out = np.hypot(np.maximum(dr, 0), np.maximum(dxx, 0))
        ins = (dr < 0) & (dxx < 0)
        return np.where(ins, np.maximum(dr, dxx), out)
    Pg = p.prof
    if p.az is None:
        return poly_d(np.c_[x, r], Pg)
    a0, a1 = p.az
    rel = (az - a0) % 360.0
    inr = rel <= (a1 - a0)
    res = np.empty(len(W))
    res[inr] = poly_d(np.c_[x[inr], r[inr]], Pg)
    o = ~inr
    d0 = np.minimum(rel[o], 360 - rel[o])                       # to a0
    d1 = np.minimum(np.abs(rel[o] - (a1 - a0)), 360 - np.abs(rel[o] - (a1 - a0)))   # to a1
    best = np.full(o.sum(), np.inf)
    for dd in (d0, d1):
        t = np.radians(dd)
        q = np.c_[x[o], r[o] * np.cos(t)]
        dpl = np.maximum(poly_d(q, Pg), 0.0)
        best = np.minimum(best, np.hypot(dpl, r[o] * np.sin(t)))
    res[o] = best
    return res


def clip_r(Pg, rc):
    """Sutherland-Hodgman clip of an (x, r) polygon to r >= rc (None if empty)"""
    out = []
    n = len(Pg)
    for i in range(n):
        a, b = Pg[i], Pg[(i + 1) % n]
        ia, ib = a[1] >= rc, b[1] >= rc
        if ia:
            out.append(a)
        if ia != ib:
            t = (rc - a[1]) / (b[1] - a[1])
            out.append(a + t * (b - a))
    return np.array(out) if len(out) >= 3 else None


def part_points(p, h=0.1):
    """sample points (world) of a part (surface) - only used for inside / seam tests"""
    return p.surface(h)


def check_option(oid, SW, SH, verbose=True):
    opt = PT.options()[oid]
    parts = [p for p in opt["parts"] if p.pebble and p.role != "torso"]
    xS, rS, azS = xr_az(SW)
    # inner-half points excluding the arm's hole (no material at r < 7.0 in the inner face)
    in_half = ~SH
    hole = in_half & (rS < RHOLE)
    rep = dict(option=oid, title=opt["title"], parts={}, pairs={}, stop=None)
    ok_all = True
    worst = []
    for p in parts:
        d = dist_part(SW, p)
        # surface points inside the part = the part pierces the skin
        do = d[SH]; di_all = d[in_half]; di = d[in_half & ~hole]
        if p.role in ("drive", "static") and p.mag is None:
            # inside the arm's hole (r < 7.0 - 0.3) the part faces the open hole, no inner shell: clip it to r >= 6.7
            import copy as _c
            pc = _c.copy(p); pc.prof = clip_r(p.prof, RHOLE - 0.3 + 0.01)
            di = dist_part(SW[in_half], pc) if pc.prof is not None else np.array([9.0])
        wall_out = float(do.min()); wall_in = float(di.min()) if len(di) else 9.0
        wall_in_hole = float(di_all.min())
        k = int(np.argmin(np.where(SH, d, np.inf)))
        Pp = part_points(p, 0.1)
        Lp = G.to_local(Pp)
        ins = G.inside(Lp, KOV[0], KOV[1])
        frac_out = float((~ins).mean())
        lx_max = float(Lp[:, 0].max()); lx_min = float(Lp[:, 0].min())
        slide = p.role in ("drive", "static")
        steel = p.kind in ("steel", "magnet")
        req_o = 1.5 if slide else 1.2
        if p.role == "arm" and p.kind == "printed":
            req_i = 0.0                                    # merges with A_vnut
        else:
            req_i = 1.5 if slide else (1.2 if steel else 0.0)
        # rule for printed arm parts (part of A_vnut): must stay on the inner side of the seam (local x <= -0.25)
        seam_ok = True
        if p.role == "arm" and p.kind == "printed":
            # part of A_vnut: it may protrude past the seam plane into the hollow of A_vonk (internal boss), then the
            # cover wall rule applies to it (static relative to the cover); report whether it protrudes
            seam_ok = lx_max <= -0.25 + 1e-6
            mo = 9.0 if seam_ok else wall_out - req_o
        else:
            mo = wall_out - req_o
        wi_used = wall_in if slide else wall_in_hole
        mi = wi_used - req_i if req_i > 0 else 9.0
        if p.role == "arm" and p.kind == "printed":
            okp = (mo >= -1e-3)                                  # may be trimmed by the INNER surface only
            # points outside on the outer side?
            outside_outer = int(((~ins) & (Lp[:, 0] >= 0)).sum())
            okp = okp and outside_outer == 0
        else:
            okp = (mo >= -1e-3) and (mi >= -1e-3) and frac_out == 0
        ok_all &= bool(okp)
        W0 = SW[k]
        rep["parts"][p.name] = dict(role=p.role, kind=p.kind, wall_outer_skin=round(wall_out, 3), req_outer=req_o,
                                    margin_outer=round(mo, 3) if mo < 9 else None,
                                    wall_inner_skin=round(wi_used, 3), req_inner=req_i, margin_inner=round(mi, 3) if mi < 9 else None,
                                    at_outer=dict(x=round(float(W0[0]), 2), r=round(float(rS[k]), 2), az=round(float(azS[k]), 1)),
                                    frac_points_outside_arm=round(frac_out, 4), local_x_range=[round(lx_min, 2), round(lx_max, 2)],
                                    crosses_seam=bool(lx_min < 0.25 and lx_max > -0.25), seam_ok=bool(seam_ok), ok=bool(okp))
        worst.append((min(mo, mi), p.name))
    # pairs (2-D exact, for relatively moving parts, skipping designed contacts / rigid pairs)
    contacts = set(tuple(sorted(c)) for c in opt["contacts"]) | set(tuple(sorted(c)) for c in opt.get("rigid", []))
    solid = [p for p in opt["parts"] if p.mag is None and p.role != "torso"]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if a.role == b.role or "torso" in (a.role, b.role):
                continue
            key = tuple(sorted((a.name, b.name)))
            if key in contacts:
                continue
            if a.az is not None and b.az is not None:
                continue                                   # rib vs lug: angular, below
            g = poly_poly(a.prof, b.prof)
            # sector vs full revolution: 2-D distance is exact (the full part exists at every azimuth)
            rep["pairs"][f"{a.name}|{b.name}"] = round(g, 3)
            if g < 0.3 - 1e-6:
                ok_all = False
    # magnets inside the drive hub profile
    hub = next((p for p in opt["parts"] if p.name == "DRV_unasac"), None)
    if hub is not None:
        for p in opt["parts"]:
            if p.mag is not None and p.role == "drive":
                x0, x1, r0, r1 = p.xr_bounds()
                box = np.array([(x0, r0), (x1, r0), (x1, r1), (x0, r1)])
                inside_hub = bool(pip(box + np.array([[1e-4, 1e-4], [-1e-4, 1e-4], [-1e-4, -1e-4], [1e-4, -1e-4]]), hub.prof).all())
                if not inside_hub:
                    ok_all = False
                    rep["pairs"][p.name + " in hub"] = "NOT INSIDE"
        # magnet pocket web (same radius pockets D5.1)
        mags = [p for p in opt["parts"] if p.mag is not None and p.role == "drive"]
        if mags:
            n = len(mags); r = mags[0].mag["r"]
            rep["magnet_pockets"] = dict(n=n, r=r, web_D5p1=round(2 * r * math.sin(math.pi / n) - 5.1, 2))
    # stop (analytic): rib and lug end faces are radial half-planes; gap = r_min_overlap * sin(d_az)
    if opt.get("stop"):
        lug = next(p for p in opt["parts"] if p.name == "PLG_doraz"); rib = next(p for p in opt["parts"] if p.name == "ARM_rebro")
        lx0, lx1, lr0, lr1 = lug.xr_bounds(); rx0, rx1, rr0, rr1 = rib.xr_bounds()
        r_ov0, r_ov1 = max(lr0, rr0), min(lr1, rr1)
        x_ov = min(lx1, rx1) - max(lx0, rx0)
        res = {}
        for s in (-51.0, -45.0, 135.0, 140.5):
            ra0, ra1 = rib.az[0] - s, rib.az[1] - s            # swing s rotates arm parts by -s (fit.py convention)
            la0, la1 = lug.az
            # angular gap between the arcs [ra0, ra1] and [la0, la1] (mod 360)
            gaps = []
            for (p0, p1, q0, q1) in ((ra0, ra1, la0, la1), (la0, la1, ra0, ra1)):
                gaps.append((q0 - p1) % 360.0)
            dang = min(gaps)
            if dang > 180:
                dang = 0.0
            res[s] = round(r_ov0 * math.sin(math.radians(dang)), 3) if dang < 90 else round(r_ov0, 3)
        rep["stop"] = dict(gap_m45=res[-45.0], gap_135=res[135.0], gap_at_m51=res[-51.0], gap_at_140p5=res[140.5],
                           contact_face_mm2=round(max(0, r_ov1 - r_ov0) * max(0, x_ov), 2))
        ok_all &= res[-45.0] >= 0.3 and res[135.0] >= 0.3 and res[-51.0] < 0.1 and res[140.5] < 0.1
    rep["fits"] = bool(ok_all)
    w = min(worst)
    rep["governing_part_margin"] = dict(margin=round(w[0], 3), part=w[1])
    pp = [v for v in rep["pairs"].values() if isinstance(v, float)]
    rep["min_pair_clearance"] = round(min(pp), 3) if pp else None
    if verbose:
        print(f"\n=== {oid} {opt['title']} : FITS {'YES' if ok_all else 'NO'}  governing {rep['governing_part_margin']}  min pair {rep['min_pair_clearance']}")
        for k, v in rep["parts"].items():
            print(f"  {k:22s} {v['role']:6s} out {v['wall_outer_skin']:7.3f} (req {v['req_outer']}) in {v['wall_inner_skin']:7.3f} (req {v['req_inner']})"
                  f"  outside {v['frac_points_outside_arm']:.3f} lx {v['local_x_range']} seam_ok {v['seam_ok']} {'ok' if v['ok'] else 'NO'}  @ {v['at_outer']}")
        bad = {k: v for k, v in rep["pairs"].items() if not isinstance(v, float) or v < 0.5}
        print("  pairs < 0.5:", bad)
        print("  stop:", rep["stop"], " magnets:", rep.get("magnet_pockets"))
    return rep


def arm_surface(ds=0.05, ko=G.KO, kw=G.KW):
    P, H = G.surface(0.0, 0.62, ds, ko, kw)
    W = G.to_world(P)
    x, r, _ = xr_az(W)
    keep = (r < 24.0) & (x > 44) & (x < 80)
    return W[keep], H[keep], P[keep]


if __name__ == "__main__":
    t0 = time.time()
    ko = float(sys.argv[1]) if len(sys.argv) > 1 else G.KO
    kw = float(sys.argv[2]) if len(sys.argv) > 2 else G.KW
    oids = sys.argv[3].split(",") if len(sys.argv) > 3 else list(PT.options())
    SW, SH, SL = arm_surface(0.05, ko, kw)
    print("arm surface points", len(SW), f"(ko {ko}, kw {kw})", f"{time.time() - t0:.1f}s")
    KOV[:] = [ko, kw]
    out = {oid: check_option(oid, SW, SH) for oid in oids}
    tag = f"ko{ko:g}_kw{kw:g}"
    json.dump(out, open(os.path.join(HERE, f"own_fit_{tag}.json"), "w"), indent=1)
    print(f"done {time.time() - t0:.0f}s")
