"""Independent verifier (R3/overenie_B): seam and cover-attachment checks that fit.py does not do.
 1 which part of every joint part lies on the cover side (A_vonk) / inner side (A_vnut) of the seam surface x_local = c(u)
 2 distance of every joint part (full revolution) to the SEAM LINE on the skin (where the 0.5 seam groove / lip sits)
 3 the approved cover attachment (v1/v2: 4 magnets D3x2 in printed posts r 2.2 x 2.4 on each side of the seam, at u 0.16 and
   0.66, 3.5 inside the outline; parts_v1.py) moved onto this variant's seam and width, against the joint parts
usage: seam_chk.py <vid> <option>  -> seam_<vid>_<option>.json"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armsurf as AS  # noqa: E402
VA = AS.VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as PT  # noqa: E402
YA, ZA = 3.0, -17.0
vid = sys.argv[1]; oid = sys.argv[2]
dx = -1.0


def revolve(prof, h=0.06, az=None):
    P = np.asarray(prof, float)
    E = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n = max(1, int(math.ceil(np.hypot(*(b - a)) / h)))
        t = np.linspace(0, 1, n, endpoint=False)
        E.append(a + t[:, None] * (b - a))
    E = np.concatenate(E)
    a0, a1 = (0.0, 360.0) if az is None else az
    out = []
    for x, r in E:
        n = max(1, int(math.radians(a1 - a0) * r / h) + 1) if r > 1e-6 else 1
        ph = np.radians(np.linspace(a0, a1, n, endpoint=az is not None))
        out.append(np.c_[np.full(n, x), YA + r * np.cos(ph), ZA + r * np.sin(ph)])
    return np.concatenate(out)


def xr_az(Q):
    return Q[:, 0], np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA), np.degrees(np.arctan2(Q[:, 2] - ZA, Q[:, 1] - YA)) % 360


# seam line on the skin (both edges), local -> world
us = np.linspace(0.0005, 0.9995, 40001)
c, ti, to, w, _, _ = VA.section(vid, us)
SL = np.concatenate([np.c_[c, w, -VA.L * us], np.c_[c, -w, -VA.L * us]])
SW = VA.to_world(SL, vid, dx)
st = cKDTree(SW)
x_, r_, a_ = xr_az(SW)
near = r_ < 16
REP = dict(variant=vid, option=oid, seam_line_near_axis=dict(
    note="seam line points within r 16 of the shoulder axis: world x range and azimuths",
    x_range=[round(float(x_[near].min()), 2), round(float(x_[near].max()), 2)] if near.any() else None))
# seam surface world x on the shoulder-axis line and on circles r 13 (az 0 / 90 / 180 / 270)
xs = np.linspace(45, 75, 30001)
for r in (0.0, 6.0, 10.0, 13.0):
    row = {}
    for az in ((0,) if r == 0 else (0, 45, 90, 135, 180, 225, 270, 315)):
        Q = np.c_[xs, np.full_like(xs, YA + r * math.cos(math.radians(az))), np.full_like(xs, ZA + r * math.sin(math.radians(az)))]
        Pl = VA.to_local(Q, vid, dx)
        f = Pl[:, 0] - VA.seam_x(vid, np.clip(-Pl[:, 2] / VA.L, 0, 1))
        k = np.nonzero(np.diff(np.sign(f)))[0]
        row[str(az)] = round(float(xs[k[0]]), 2) if len(k) else None
    REP[f"seam_surface_world_x_at_r{r:g}"] = row
print(json.dumps({k: v for k, v in REP.items() if k.startswith("seam")}, indent=0))

opt = PT.options()[oid]
REP["parts"] = {}
for p in opt["parts"]:
    if not p.pebble or p.role == "torso":
        continue
    prof = p.outline_xr() if p.mag is not None else p.prof
    az = None if (p.mag is not None or p.role in ("static", "drive")) else p.az
    Q = revolve(prof, 0.06, az)
    Pl = VA.to_local(Q, vid, dx)
    sd = Pl[:, 0] - VA.seam_x(vid, np.clip(-Pl[:, 2] / VA.L, 0, 1))
    d, k = st.query(Q)
    j = int(np.argmin(d))
    x, r, a = xr_az(Q[j:j + 1])
    REP["parts"][p.name] = dict(role=p.role, frac_cover_side=round(float((sd > 0).mean()), 3),
                                seam_dx=[round(float(sd.min()), 2), round(float(sd.max()), 2)],
                                dist_to_seam_line=round(float(d[j]), 3), at=dict(x=round(float(x[0]), 2), r=round(float(r[0]), 2), az=round(float(a[0]), 1)))
    print(f"{p.name:22s} {p.role:6s} cover-side frac {REP['parts'][p.name]['frac_cover_side']:.3f}  seam_dx {REP['parts'][p.name]['seam_dx']}  "
          f"to seam line {d[j]:.3f} at x {x[0]:.2f} r {r[0]:.2f} az {a[0]:.0f}")

# cover magnet posts (parts_v1.py: Solid.make_cylinder(2.2, 2.4) along local +-x from the seam +-0.25, magnet D3x2 inside)
posts = []
for u, sg in ((0.16, -1), (0.16, 1), (0.66, -1), (0.66, 1)):
    cc, _, _, ww, _, _ = VA.section(vid, u)
    for side in (1, -1):
        base = np.array([float(cc) + side * VA.SEAM, sg * (float(ww) - 3.5), -VA.L * u])
        th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        pts = []
        for s in np.linspace(0, 2.4, 25):
            for rr in (2.2,):
                pts.append(np.c_[np.full(72, base[0] + side * s), base[1] + rr * np.cos(th), base[2] + rr * np.sin(th)])
        for s in (0.0, 2.4):
            for rr in np.linspace(0, 2.2, 12):
                pts.append(np.c_[np.full(72, base[0] + side * s), base[1] + rr * np.cos(th), base[2] + rr * np.sin(th)])
        Pp = np.concatenate(pts)
        posts.append(dict(u=u, y_sign=sg, half="vonk" if side > 0 else "vnut", P=VA.to_world(Pp, vid, dx)))
REP["cover_magnet_posts"] = []
moving = [p for p in opt["parts"] if p.pebble and p.role in ("drive", "static")]
for po in posts:
    x, r, a = xr_az(po["P"])
    best = (1e9, None)
    for p in moving:
        prof = p.outline_xr() if p.mag is not None else p.prof
        # exact 2-D (x, r) distance of the post's points to the part's revolved profile (full revolution: any clutch angle)
        X = np.c_[x, r]
        ins = PT._inpoly(X, np.asarray(prof, float))
        P_ = np.asarray(prof, float)
        dmin = np.full(len(X), 1e9)
        for i in range(len(P_)):
            A, B = P_[i], P_[(i + 1) % len(P_)]
            AB = B - A; t = np.clip(((X - A) @ AB) / max(AB @ AB, 1e-12), 0, 1)
            dmin = np.minimum(dmin, np.linalg.norm(X - (A + t[:, None] * AB), axis=1))
        sdist = np.where(ins, -dmin, dmin)
        m = float(sdist.min())
        if m < best[0]:
            best = (m, p.name)
    e = dict(u=po["u"], y_sign=po["y_sign"], half=po["half"], x_range=[round(float(x.min()), 2), round(float(x.max()), 2)],
             r_range=[round(float(r.min()), 2), round(float(r.max()), 2)], min_dist_to_moving_part=round(best[0], 3), part=best[1],
             needs=0.3)
    REP["cover_magnet_posts"].append(e)
    print("post", e)
json.dump(REP, open(os.path.join(HERE, f"seam_{vid}_{oid}.json"), "w"), indent=1)
