"""R3/mech/fit.py - does an arm-side joint packaging option fit inside a given arm shape?

usage:  /opt/venv/cad/bin/python fit.py <variant_module.py> <variant_id> <option M1|M2|M3|M4|all> [--dx -1.0] [--json out.json] [--quiet]
        e.g.  fit.py standin.py kt070 M2

The variant module must expose (all in the arm LOCAL frame of that module: x = thickness direction, outer +):
    inside_local(vid, P, inset)   boolean point-in-arm test
    to_world(P, vid, dx)          local -> frame B (LEFT arm at rest)
    profile(vid, u)               (half width, half thickness) - only reported
Parts come from parts.py (frame B, left arm at rest).  Checks:
  1 wall from every part to the OUTER arm surface (local x >= 0 half = vonkajší kryt A_vonk) and to the INNER surface
    (local x < 0 half = A_vnut): true Euclidean distance to a dense surface cloud built from inside_local (ray bisection,
    spacing <= 0.12 mm, error < 0.01 mm), sign from inside_local.  Required: see parts.py (1.2 cover wall, +0.3 where the
    part moves against the arm).
  2 sliding clearance between parts that move against each other (arm/static over the swing, arm/drive at clutch slip,
    drive/static): exact 2-D (x, r) profile distance for axisymmetric pairs (and for a sector against a full revolution);
    3-D point clouds rotated over the swing -45..+135 deg for sector/sector pairs (stop rib vs lug); designed contacts are
    listed and skipped.  Required >= 0.3.
  3 stop: rib/lug gap at -45 and +135 (>= 0.3) and contact (< 0.1) at the stop angles -51 / +140.5.
Prints a table and returns/writes a JSON report with fits yes/no and the governing spot."""
import sys, os, math, json, time, argparse, importlib.util
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as PT  # noqa: E402

YA, ZA = PT.YA, PT.ZA
SLIDE = 0.3
DMAX = 3.5            # walls larger than this are reported as 3.5 (keeps the nearest-neighbour search local)
SWING = np.r_[np.arange(-45.0, 135.01, 3.0), 135.0]


def load_variant(path):
    spec = importlib.util.spec_from_file_location("variant_mod_" + os.path.basename(path).replace(".", "_"), path)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec.loader.exec_module(m)
    return m


def variant_thickness(mod, vid):
    """real max thickness of the variant: thickness(vid) or max_u thickness(vid, u) or from profile(vid, u)"""
    us = np.linspace(0.0, 1.0, 2001)
    try:
        return float(mod.thickness(vid))
    except TypeError:
        try:
            return float(np.max(mod.thickness(vid, us)))
        except Exception:
            pass
    pr = mod.profile(vid, us)
    if len(pr) >= 3:                       # (half width, half thick inner, half thick outer)
        return float(np.max(np.asarray(pr[1]) + np.asarray(pr[2])))
    return float(2 * np.max(np.asarray(pr[1])))


class Arm:
    """surface cloud + affine frame of one arm variant"""

    def __init__(self, mod, vid, dx=-1.0):
        self.mod, self.vid, self.dx = mod, vid, dx
        b = np.asarray(mod.to_world(np.zeros((1, 3)), vid, dx), float).reshape(3)
        Am = np.array([np.asarray(mod.to_world(np.eye(3)[i:i + 1], vid, dx), float).reshape(3) - b for i in range(3)])
        self.b, self.A = b, Am                         # world = local @ A + b
        self.Ai = np.linalg.inv(Am)
        self.rigid_err = float(np.abs(Am @ Am.T - np.eye(3)).max())

    def to_local(self, Q):
        return (np.asarray(Q, float) - self.b) @ self.Ai

    def to_world(self, P):
        return np.asarray(P, float) @ self.A + self.b

    def inside(self, P):
        return np.asarray(self.mod.inside_local(self.vid, np.atleast_2d(P), 0.0), bool)

    def build_cloud(self, zlo, zhi, h=0.12):
        """surface cloud in the local frame for local z in [zlo, zhi] (+ the top cap)"""
        ins = self.inside
        zs_axis = np.linspace(5.0, -120.0, 25001)
        cx = lambda z: float(self.seam(np.array([[0.0, 0.0, z]]))[0])      # ray centre on the seam line (inside the section)
        on = ins(np.c_[self.seam(np.c_[np.zeros_like(zs_axis), np.zeros_like(zs_axis), zs_axis]), np.zeros_like(zs_axis), zs_axis])
        if not on.any():
            raise RuntimeError("local z axis does not pierce the arm")
        ztop, zbot = zs_axis[on].max(), zs_axis[on].min()
        self.ztop, self.zbot = float(ztop), float(zbot)
        zhi = min(zhi, ztop - 1e-3); zlo = max(zlo, zbot + 1e-3)
        pts = []

        def bisect(C, D, rmax=45.0, it=24):
            lo = np.zeros(len(D)); hi = np.full(len(D), rmax)
            for _ in range(it):
                mid = 0.5 * (lo + hi)
                ok = ins(C + D * mid[:, None])
                lo = np.where(ok, mid, lo); hi = np.where(ok, hi, mid)
            return C + D * lo[:, None]
        # horizontal rows
        for z in np.arange(zhi, zlo - 1e-9, -h):
            # perimeter estimate from 64 rays, then the real ray count
            th = np.linspace(0, 2 * np.pi, 64, endpoint=False)
            C = np.array([cx(z), 0.0, z])
            D = np.c_[np.cos(th), np.sin(th), np.zeros_like(th)]
            P0 = bisect(np.broadcast_to(C, D.shape), D, it=16)
            per = np.sum(np.linalg.norm(np.diff(np.r_[P0, P0[:1]], axis=0), axis=1))
            n = max(64, int(per / h) + 1)
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            D = np.c_[np.cos(th), np.sin(th), np.zeros_like(th)]
            pts.append(bisect(np.broadcast_to(C, D.shape), D))
        # top cap: rays from an interior centre through the upper half space (covers the steep dome near u = 0)
        c = np.array([cx(ztop - 9.0), 0.0, ztop - 9.0])
        nd = int(4 * np.pi * 12.0 ** 2 / h ** 2 / 2)
        k = np.arange(nd) + 0.5
        cz = k / nd                                       # cos(polar) uniform in (0, 1] -> upper hemisphere
        ph = np.pi * (1 + 5 ** 0.5) * k
        sz = np.sqrt(1 - cz ** 2)
        D = np.c_[sz * np.cos(ph), sz * np.sin(ph), cz]
        cap = bisect(np.broadcast_to(c, D.shape), D)
        pts.append(cap[cap[:, 2] >= zhi - 1.0])
        S = np.concatenate(pts)
        S = np.unique(np.round(S, 3), axis=0)              # rows near the dome tip collapse onto a few points
        self.cloud = S
        side = S[:, 0] >= self.seam(S)
        self.t_out = cKDTree(S[side])
        self.t_in = cKDTree(S[~side])
        return S

    def seam(self, P):
        """local x of the seam (A_vonk / A_vnut parting line) at the points' u; 0 unless the module has seam_x(vid, u)"""
        P = np.atleast_2d(P)
        if hasattr(self.mod, "seam_x"):
            u = np.clip(-P[:, 2] / 72.0, 0.0, 1.0)
            return np.asarray(self.mod.seam_x(self.vid, u), float) * np.ones(len(P))
        return np.zeros(len(P))

    def walls(self, Q):
        """for world points Q: inside flag, distance to the outer half surface, distance to the inner half surface"""
        P = self.to_local(Q)
        dout, _ = self.t_out.query(P, distance_upper_bound=DMAX, workers=3)
        din, _ = self.t_in.query(P, distance_upper_bound=DMAX, workers=3)
        dout = np.minimum(dout, DMAX); din = np.minimum(din, DMAX)
        return self.inside(P), dout, din, P


# ------------------------------------------------------------------------------------------- 2-D profile distance
def _seg_dist(Pts, A, B):
    AB = B - A; L2 = (AB ** 2).sum()
    t = np.clip(((Pts - A) @ AB) / max(L2, 1e-12), 0, 1)
    return np.linalg.norm(Pts - (A + t[:, None] * AB), axis=1)


def poly_dist(P, Q, h=0.02):
    """signed distance between two closed (x, r) polygons: >0 gap, <0 overlap depth (approx.)"""
    def bnd(Pp):
        out = []
        for i in range(len(Pp)):
            a, b = Pp[i], Pp[(i + 1) % len(Pp)]
            n = max(2, int(np.hypot(*(b - a)) / h))
            t = np.linspace(0, 1, n, endpoint=False)
            out.append(a + t[:, None] * (b - a))
        return np.concatenate(out)

    def one(A, B):
        S = bnd(A)
        d = np.min([_seg_dist(S, B[i], B[(i + 1) % len(B)]) for i in range(len(B))], axis=0)
        ins = PT._inpoly(S, B)
        sd = np.where(ins, -d, d)
        k = int(np.argmin(sd))
        return float(sd[k]), S[k]
    a, pa = one(P, Q); b, pb = one(Q, P)
    return (a, pa) if a <= b else (b, pb)


def swing_pts(Q, deg):
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    Q = np.array(Q, float, copy=True)
    y, z = Q[:, 1] - YA, Q[:, 2] - ZA
    Q[:, 1] = c * y - s * z + YA; Q[:, 2] = s * y + c * z + ZA
    return Q


def rel_moving(r1, r2):
    if "torso" in (r1, r2) or r1 == r2:
        return False
    return True


# ------------------------------------------------------------------------------------------------------- the check
def check(mod, vid, oid, dx=-1.0, quiet=False, arm=None, h=0.2):
    t0 = time.time()
    opt = PT.options()[oid]
    parts = opt["parts"]
    arm = arm or Arm(mod, vid, dx)
    S = {p.name: p.surface(h) for p in parts if p.pebble and p.role != "torso"}
    if not hasattr(arm, "cloud"):
        allp = np.concatenate(list(S.values()))
        L = arm.to_local(allp)
        arm.build_cloud(L[:, 2].min() - 8.0, L[:, 2].max() + 8.0)
    rep = dict(variant=vid, option=oid, title=opt["title"], dx=dx, rigid_err=arm.rigid_err, thickness=None, parts={}, pairs={},
               stop={}, fits=True, governing=None)
    rep["thickness"] = variant_thickness(mod, vid)
    worst = (1e9, None)
    for p in parts:
        if p.name not in S:
            continue
        Q = S[p.name]
        ins, dout, din, P = arm.walls(Q)
        n_out = int((~ins).sum())
        wo = np.where(ins, dout, -np.minimum(dout, din))
        wi = np.where(ins, din, -np.minimum(dout, din))
        if p.role == "arm" and p.kind == "printed":
            # printed arm parts merge with the inner shell A_vnut: where they reach the INNER surface they are simply trimmed by
            # it; only the cover side matters (and points outside on the outer side still fail)
            inner_side = (~ins) & (din < dout)
            wo = np.where(inner_side, dout, wo)
            # the 1.2 cover rule applies on the cover side of the seam (local x >= 0); a printed hub point on the inner
            # side of the seam plane IS inner-shell material and only has to stay inside the arm
            wo = np.where(ins & (P[:, 0] < arm.seam(P)), DMAX, wo)
            wi = np.where(inner_side, 0.0, wi)
            n_out = int(((~ins) & ~inner_side).sum())
        if p.role in ("static", "drive"):
            # inside the arm's hole (r < rhole - 0.3) there is no inner shell: the inner-surface rule does not apply there
            rq = np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA)
            hole = rq < opt.get("rhole", 7.0) - SLIDE + 1e-6
            wi = np.where(hole & ins, DMAX, wi)
        ko, ki = int(np.argmin(wo)), int(np.argmin(wi))
        mo = float(wo[ko] - p.req_out); mi = float(wi[ki] - p.req_in)
        ok = (mo >= -1e-3) and (mi >= -1e-3) and n_out == 0
        q = Q[ko]; r = math.hypot(q[1] - YA, q[2] - ZA); az = math.degrees(math.atan2(q[2] - ZA, q[1] - YA)) % 360
        qi = Q[ki]
        rep["parts"][p.name] = dict(role=p.role, wall_out=round(float(wo[ko]), 3), req_out=p.req_out, margin_out=round(mo, 3),
                                    at_out=dict(x=round(float(q[0]), 2), r=round(r, 2), az=round(az, 1), local=P[ko].round(2).tolist()),
                                    wall_in=round(float(wi[ki]), 3), req_in=p.req_in, margin_in=round(mi, 3),
                                    at_in=dict(x=round(float(qi[0]), 2), r=round(math.hypot(qi[1] - YA, qi[2] - ZA), 2)),
                                    points_outside=n_out, ok=bool(ok))
        rep["fits"] &= bool(ok)
        for m, side in ((mo, "out"), (mi, "in")):
            if m < worst[0]:
                worst = (m, f"{p.name} wall_{side}")
    # ---- pairwise sliding clearances
    contacts = set(tuple(sorted(c)) for c in opt["contacts"])
    rigid = set(tuple(sorted(c)) for c in opt.get("rigid", []))
    solid = [p for p in parts if p.mag is None and p.role != "torso"]
    clouds = {}
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            key = tuple(sorted((a.name, b.name)))
            if not rel_moving(a.role, b.role) or key in contacts or key in rigid:
                continue
            if "PLG_kruzok" in key and "drive" in (a.role, b.role):
                pass
            if a.az is not None and b.az is not None:          # sector vs sector: rotate the arm one over the swing
                arm_p, st_p = (a, b) if a.role == "arm" else (b, a)
                for p in (arm_p, st_p):
                    if p.name not in clouds:
                        clouds[p.name] = p.surface(0.08)
                tr = cKDTree(clouds[st_p.name])
                best = (1e9, None)
                for s in SWING:
                    d, _ = tr.query(swing_pts(clouds[arm_p.name], s), distance_upper_bound=5.0)
                    if d.min() < best[0]:
                        best = (float(d.min()), float(s))
                g = best[0]
                rep["pairs"][f"{a.name} | {b.name}"] = dict(min=round(g, 3) if g < 5 else ">5", at_swing=best[1], kind="3D swing")
            else:
                g, where = poly_dist(a.outline_xr(), b.outline_xr())
                rep["pairs"][f"{a.name} | {b.name}"] = dict(min=round(g, 3), at_xr=np.round(where, 2).tolist(), kind="2D profile")
            if g < SLIDE - 1e-3:
                rep["fits"] = False
            if g - SLIDE < worst[0]:
                worst = (g - SLIDE, f"pair {a.name} | {b.name}")
    # magnets must sit inside their hub profile
    hub = next((p for p in parts if p.name == "DRV_unasac"), None)
    for p in parts:
        if p.mag is not None and p.role == "drive" and hub is not None:
            R = p.outline_xr()
            ok = bool(PT._inpoly(R + np.array([[1e-3, 1e-3], [-1e-3, 1e-3], [-1e-3, -1e-3], [1e-3, -1e-3]]), hub.prof).all())
            if not ok:
                rep["fits"] = False
                rep["pairs"][f"{p.name} inside DRV_unasac"] = dict(min=-1, kind="containment")
    # ---- stop
    if opt.get("stop"):
        lug = next(p for p in parts if p.name == "PLG_doraz"); rib = next(p for p in parts if p.name == "ARM_rebro")
        cl, cr = lug.surface(0.05), rib.surface(0.05)
        tr = cKDTree(cl)
        g = {}
        for s in (-51.0, -45.0, 135.0, 140.5):
            d, _ = tr.query(swing_pts(cr, s)); g[s] = round(float(d.min()), 3)
        rep["stop"] = dict(gap_at_m45=g[-45.0], gap_at_135=g[135.0], gap_at_stop_m51=g[-51.0], gap_at_stop_140p5=g[140.5],
                           ok=bool(g[-45.0] >= SLIDE and g[135.0] >= SLIDE and g[-51.0] < 0.12 and g[140.5] < 0.12))
        rep["fits"] &= rep["stop"]["ok"]
    rep["governing"] = dict(margin=round(worst[0], 3), where=worst[1])
    po = min(((v["margin_out"], k) for k, v in rep["parts"].items()), default=(9, None))
    pi = min(((v["margin_in"], k) for k, v in rep["parts"].items()), default=(9, None))
    pp = min(((v["min"] - SLIDE, k) for k, v in rep["pairs"].items() if isinstance(v["min"], float)), default=(9, None))
    rep["margin_outer"] = dict(margin=round(po[0], 3), part=po[1], at=rep["parts"][po[1]]["at_out"] if po[1] else None)
    rep["margin_inner"] = dict(margin=round(pi[0], 3), part=pi[1])
    rep["margin_pairs"] = dict(margin=round(pp[0], 3), pair=pp[1])
    rep["time_s"] = round(time.time() - t0, 1)
    if not quiet:
        print_report(rep)
    return rep


def print_report(rep):
    print(f"\n=== option {rep['option']} ({rep['title']}) in arm {rep['variant']} (max thickness {rep['thickness']:.2f}, dx {rep['dx']}) ===")
    print("%-24s %-6s %8s %5s %7s | %8s %5s %7s | %s" % ("part", "role", "wall_out", "req", "margin", "wall_in", "req", "margin", "ok / governing spot (x, r, az)"))
    for k, v in rep["parts"].items():
        a = v["at_out"]
        print("%-24s %-6s %8.2f %5.2f %7.2f | %8.2f %5.2f %7.2f | %s  (x %.2f r %.2f az %.0f)%s" % (
            k, v["role"], v["wall_out"], v["req_out"], v["margin_out"], v["wall_in"], v["req_in"], v["margin_in"],
            "ok" if v["ok"] else "NO", a["x"], a["r"], a["az"], "" if not v["points_outside"] else f"  {v['points_outside']} pts outside"))
    ps = sorted(rep["pairs"].items(), key=lambda kv: kv[1]["min"] if isinstance(kv[1]["min"], float) else 99)
    print("sliding clearances (min first, required >= 0.3):")
    for k, v in ps[:8]:
        print(f"   {k:44s} {v['min']}  ({v['kind']})")
    if rep["stop"]:
        print("stop:", rep["stop"])
    print(f"FITS: {'YES' if rep['fits'] else 'NO'}   governing: {rep['governing']}   ({rep['time_s']} s)")
    print(f"      outer-surface margin {rep['margin_outer']['margin']} ({rep['margin_outer']['part']} at {rep['margin_outer']['at']}), "
          f"inner {rep['margin_inner']['margin']} ({rep['margin_inner']['part']}), pairs {rep['margin_pairs']['margin']} ({rep['margin_pairs']['pair']})")


def envelope(oid, rs=None):
    """thickness-independent envelope: for each radius r from the shoulder axis the outermost x of the arm-side parts
    plus the required wall (cover 1.2, +0.3 where the part moves against the arm) -> the arm's OUTER surface must lie at
    or beyond this x along the line || X at radius r (any azimuth).  Also the innermost x minus the inner requirement."""
    rs = np.arange(0.0, 16.01, 0.25) if rs is None else rs
    opt = PT.options()[oid]
    out = []
    for r in rs:
        xo, who_o, xi, who_i = -1e9, None, 1e9, None
        for p in opt["parts"]:
            if not p.pebble or p.role == "torso":
                continue
            P = p.outline_xr()
            xs = []
            for i in range(len(P)):
                (x1, r1), (x2, r2) = P[i], P[(i + 1) % len(P)]
                if (r1 - r) * (r2 - r) <= 0 and r1 != r2:
                    xs.append(x1 + (r - r1) * (x2 - x1) / (r2 - r1))
                elif r1 == r2 == r:
                    xs += [x1, x2]
            if xs:
                if max(xs) + p.req_out > xo:
                    xo, who_o = max(xs) + p.req_out, p.name
                if p.req_in > 0 and min(xs) - p.req_in < xi:
                    xi, who_i = min(xs) - p.req_in, p.name
        out.append(dict(r=round(float(r), 2), x_outer_surface_min=None if who_o is None else round(xo, 3), by=who_o,
                        x_inner_surface_max=None if who_i is None else round(xi, 3), by_in=who_i))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("variant_module"); ap.add_argument("vid"); ap.add_argument("option")
    ap.add_argument("--dx", type=float, default=-1.0); ap.add_argument("--json"); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    mod = load_variant(a.variant_module)
    oids = list(PT.options()) if a.option == "all" else a.option.split(",")
    arm = Arm(mod, a.vid, a.dx)
    allS = np.concatenate([p.surface(0.5) for o in oids for p in PT.options()[o]["parts"] if p.pebble and p.role != "torso"])
    L = arm.to_local(allS)
    arm.build_cloud(L[:, 2].min() - 8.0, L[:, 2].max() + 8.0)
    reps = [check(mod, a.vid, o, a.dx, a.quiet, arm=arm) for o in oids]
    if a.json:
        json.dump(reps if len(reps) > 1 else reps[0], open(a.json, "w"), indent=1)
