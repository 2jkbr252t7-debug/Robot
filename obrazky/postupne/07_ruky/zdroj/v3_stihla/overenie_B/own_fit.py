"""Independent verifier (R3/overenie_B): do the arm-side joint parts of M1..M4 fit inside shape variant B?
Own computation, not fit.py:
  * arm surface = own analytic sampling of variants.section() (spacing 0.04) + exact Nelder-Mead refinement at the worst spots
  * part surfaces = own revolve sampler of the (x, r) profiles in mech/parts.py (design data only); FULL revolutions are used
    for every part that turns against the arm (static parts over the swing, drive parts while the clutch slips), so the
    result holds at any relative angle; sectors (rib) are sampled with their end caps at the rest angle
  * rules (user): cover wall 1.2; +0.3 sliding clearance -> 1.5 for parts that move against the arm; steel arm parts need
    1.2 printed backing to every skin; printed arm parts (hub, rib) merge with A_vnut -> only the cover side counts
  * extra: seam side of every part, distance of rotating parts to the seam line on the skin, the v1/v2 cover magnet posts
    (4x D3x2 in posts r 2.2 x 2.4 on the seam rim at u 0.16 / 0.66) against the joint parts
usage: own_fit.py [vid] [options]  -> own_fit_<vid>.json"""
import sys, os, math, json, time
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
vid = sys.argv[1] if len(sys.argv) > 1 else "B"
oids = sys.argv[2].split(",") if len(sys.argv) > 2 else ["M1", "M2", "M2b", "M3", "M4"]
t0 = time.time()
ARM = AS.ArmSurf(vid, 0.0, 0.55, 0.04)
print("arm samples", len(ARM.P), f"{time.time() - t0:.0f}s", flush=True)


def to_local(Q):
    return VA.to_local(Q, vid, -1.0)


def revolve(prof, h=0.08, az=None, caps=True):
    """surface samples (world) of a solid of revolution about the shoulder axis; returns pts, (x, r, az) per point"""
    P = np.asarray(prof, float)
    E = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n = max(1, int(math.ceil(np.hypot(*(b - a)) / h)))
        t = np.linspace(0, 1, n, endpoint=False)
        E.append(a + t[:, None] * (b - a))
    E = np.concatenate(E)
    a0, a1 = (0.0, 360.0) if az is None else az
    out, meta = [], []
    for x, r in E:
        n = max(1, int(math.radians(a1 - a0) * r / h) + 1) if r > 1e-6 else 1
        ph = np.linspace(a0, a1, n, endpoint=az is not None)
        out.append(np.c_[np.full(n, x), YA + r * np.cos(np.radians(ph)), ZA + r * np.sin(np.radians(ph))])
        meta.append(np.c_[np.full(n, x), np.full(n, r), ph])
    if az is not None and caps:
        x0, x1 = P[:, 0].min(), P[:, 0].max(); r0, r1 = P[:, 1].min(), P[:, 1].max()
        X, R = np.meshgrid(np.arange(x0, x1 + 1e-9, h), np.arange(r0, r1 + 1e-9, h), indexing="ij")
        Q = np.c_[X.ravel(), R.ravel()]
        Q = Q[PT._inpoly(Q, P) | np.isclose(Q[:, 0], x1) | np.isclose(Q[:, 1], r1)]
        for a in (a0, a1):
            out.append(np.c_[Q[:, 0], YA + Q[:, 1] * math.cos(math.radians(a)), ZA + Q[:, 1] * math.sin(math.radians(a))])
            meta.append(np.c_[Q[:, 0], Q[:, 1], np.full(len(Q), a)])
    return np.concatenate(out), np.concatenate(meta)


def part_prof(p):
    if p.mag is not None:          # magnets: revolved ring (they turn with the drive hub against the arm when the clutch slips)
        return p.outline_xr(), None
    if p.az is not None and p.role in ("static", "drive"):
        return p.prof, None        # the stop lug turns against the arm over the swing -> full revolution
    return p.prof, p.az


def rules(p):
    slide = p.role in ("drive", "static")
    steel = p.kind in ("steel", "magnet")
    printed_arm = p.role == "arm" and not steel
    return dict(cover=1.5 if slide else 1.2, inner=(1.5 if slide else (1.2 if steel else None)), printed_arm=printed_arm)


def seam_dx(Pl):
    u = np.clip(-Pl[:, 2] / VA.L, 0, 1)
    return Pl[:, 0] - VA.seam_x(vid, u)


REP = {}
for oid in oids:
    opt = PT.options()[oid]
    R = dict(title=opt["title"], parts={}, fits=True)
    rhole = opt.get("rhole", 7.0)
    seen = {}
    for p in opt["parts"]:
        if not p.pebble or p.role == "torso":
            continue
        prof, az = part_prof(p)
        key = (p.role, p.kind, str(np.round(np.asarray(prof, float), 4).tolist()), str(az))
        if key in seen:                      # identical revolved ring (clutch magnets): same result
            R["parts"][p.name] = dict(R["parts"][seen[key]], same_as=seen[key])
            continue
        seen[key] = p.name
        Q, meta = revolve(prof, 0.08, az)
        Pl = to_local(Q)
        ins = ARM.inside(Pl)
        dc, kc = ARM.dist(Pl, "cover")
        di, ki = ARM.dist(Pl, "inner")
        rl = rules(p)
        sd = seam_dx(Pl)
        # cover-side wall
        wc = np.where(ins, dc, -np.minimum(dc, di))
        if rl["printed_arm"]:
            wc = np.where(ins & (sd < 0), 4.0, wc)       # inner-shell material: no cover rule
            outside_bad = (~ins) & (dc <= di)             # outside through the cover side = real failure
            outside_ok = (~ins) & (dc > di)               # trimmed by the inner skin: merges with A_vnut
            wc = np.where(outside_ok, 4.0, wc)
        else:
            outside_bad = ~ins
        wi = np.where(ins, di, -np.minimum(dc, di))
        if p.role in ("static", "drive"):
            hole = meta[:, 1] < rhole - 0.3 + 1e-6
            wi = np.where(hole & ins, 4.0, wi)
        res = dict(role=p.role, kind=p.kind, n=len(Q), outside=int(outside_bad.sum()),
                   seam_side=("cover" if sd.min() > 0 else "inner" if sd.max() < 0 else "both"),
                   seam_dx_range=[round(float(sd.min()), 2), round(float(sd.max()), 2)])
        ok = res["outside"] == 0
        for side, w, req, kk in (("cover", wc, rl["cover"], kc), ("inner", wi, rl["inner"], ki)):
            if req is None:
                res[side] = dict(req=0.0, note="printed arm part, merges with A_vnut")
                continue
            j = int(np.argmin(w))
            wj = float(w[j])
            # exact refinement at the 25 worst points (positive walls only; negative = outside, keep sampled value)
            if wj > 0 and wj < 3.9:
                cand = np.argsort(w)[:8]
                best = (1e9, None)
                for c in cand:
                    if w[c] <= 0 or w[c] > 3.9:
                        continue
                    d_ex, ut, sp = ARM.refine(Pl[c], side, kk[c])
                    if d_ex < best[0]:
                        best = (d_ex, c, ut)
                if best[1] is not None:
                    j = best[1]; wj = best[0]
            x, r, a = meta[j]
            res[side] = dict(req=req, wall=round(wj, 3), margin=round(wj - req, 3),
                             at=dict(x=round(float(x), 2), r=round(float(r), 2), az=round(float(a), 1),
                                     local=Pl[j].round(2).tolist(), u=round(float(-Pl[j, 2] / VA.L), 3)))
            ok &= wj - req >= -1e-3
        res["ok"] = bool(ok)
        R["parts"][p.name] = res
        R["fits"] &= bool(ok)
        print(oid, f"{p.name:22s}", res["seam_side"], "out", res["outside"],
              "cover", res["cover"].get("margin"), "inner", res["inner"].get("margin"), "ok" if ok else "NO", flush=True)
    # governing
    ms = [(v[s]["margin"], k, s) for k, v in R["parts"].items() for s in ("cover", "inner") if "margin" in v[s]]
    R["governing"] = dict(zip(("margin", "part", "side"), min(ms)))
    REP[oid] = R
    print(oid, "FITS" if R["fits"] else "DOES NOT FIT", R["governing"], f"{time.time() - t0:.0f}s", flush=True)

json.dump(REP, open(os.path.join(HERE, f"own_fit_{vid}.json"), "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")
