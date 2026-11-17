#!/opt/venv/cad/bin/python
"""Module checks of t4_ram.py REV. 2 (RAM builder's own checks, NOT the global K1-K13).  rev. 1: rev2_backup/t4_ram_checks.py.ram.bak

    /opt/venv/cad/bin/python t4_ram_checks.py [A B C D E F G H S P X]   -> ram_checks.json, ram_checks.log

  A  solids valid / single / volume > 0; STL watertight (export_abs statistics in parts_ram.json); deleted parts gone
  B  interference among the RAM parts (OCC common volume) against the list of declared fits
  C  zones: shell inset 2.2, white-lip outline - 0.5 (T_stred lowering), tub - 0.3, F1 boss keep-out, PAN_ENV2 swept over
     pan +-90 (with sectors), pivot interface (r <= 4.5, head <= -39.35), pinion vs drum shroud, stop pins vs lug
  D  seats / numbers measured on the solids
  E  walls (bisection), insert walls >= 1.6, roots (fillet probes), board air >= 1.5, deck trim
  F  tool channels D4.5 (F4 = D1.3 ball-end key <= 10 deg through the T_stred bore r 26.65)
  G  J1 sweep +-155 vs the dummy hub: (r, z) profiles + the stop lug / block contact angle
  H  carrier: USB-C plug envelope free, every connector reachable along +Y from the door opening (pan 0)
  S  strength rows (Z2: normal 8.5, sustained 4.3, abuse 12.9 MPa incl. Kt; epoxy 2.7) on the rev. 2 geometry + torque table
  P  K10 / K13 print table (orientation, build volume with 5 mm margin, supports, drains, resin rules)
  X  advisory real-mesh clearances vs the other modules' current STLs (ram2_work/cross_rev2.json from ram2_work/cross_rev2.py)
"""
from __future__ import annotations
import os, sys, json, math, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                      # noqa: E402
import t4_common as C                   # noqa: E402
import t4_ram as M                      # noqa: E402
import build123d as bd                  # noqa: E402
from build123d import Vector            # noqa: E402

R2, RV = C.R2, M.RAM2
OUT, FAIL = {}, []
LOGF = None
A_N, A_S, A_A, A_EP = 8.5, 4.3, 12.9, 2.7          # Z2 allowables (MPa): normal, sustained / notch, abuse, epoxy working


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    if LOGF:
        LOGF.write(s + "\n"); LOGF.flush()


def verdict(key, ok, info=""):
    OUT.setdefault("verdicts", {})[key] = dict(ok=bool(ok), info=info)
    if not ok:
        FAIL.append(key)
    log(f"   [{'PASS' if ok else 'FAIL'}] {key} {info}")


def inside(solid, p):
    return bool(solid.is_inside(Vector(*[float(v) for v in p]), 1e-6))


def boundary(solid, p0, d, tmax=30.0, step=0.05, tol=0.002):
    p0 = np.array(p0, float); d = np.array(d, float) / np.linalg.norm(d)
    s0 = inside(solid, p0); t = 0.0
    while t < tmax:
        t2 = t + step
        if inside(solid, p0 + d * t2) != s0:
            lo, hi = t, t2
            while hi - lo > tol:
                mid = 0.5 * (lo + hi)
                if inside(solid, p0 + d * mid) != s0:
                    hi = mid
                else:
                    lo = mid
            return 0.5 * (lo + hi)
        t = t2
    return None


def thickness(solid, p, d):
    if not inside(solid, p):
        return None
    a = boundary(solid, p, d); b = boundary(solid, p, -np.array(d, float))
    return None if a is None or b is None else a + b


def gap(solid, p, d):
    if inside(solid, p):
        return None
    a = boundary(solid, p, d); b = boundary(solid, p, -np.array(d, float))
    return None if a is None or b is None else a + b


def surf_points(shape, h=0.7, tol=0.03):
    V, T = C.mesh_of(shape, tol, 0.25)
    P = [V]
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    big = area > h * h / 2
    for A, B_, Cc, ar in zip(a[big], b[big], c[big], area[big]):
        n = int(min(40, max(1, math.ceil(math.sqrt(2 * ar) / h))))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1)); m = i + j <= n
        P.append(A + np.outer(i[m] / n, B_ - A) + np.outer(j[m] / n, Cc - A))
    return np.concatenate(P)


def common_volume(a, b):
    try:
        r = a & b
        return float(sum(s.volume for s in r.solids())) if r is not None else 0.0
    except Exception:        # noqa
        return float("nan")


def bbox(s):
    b = s.bounding_box()
    return np.array([b.min.X, b.min.Y, b.min.Z]), np.array([b.max.X, b.max.Y, b.max.Z])


PTS = {}


def pts(parts, n):
    if n not in PTS:
        PTS[n] = surf_points(parts[n]["shape"])
    return PTS[n]


# =====================================================================================================================
def check_A(parts):
    log("A. validity / watertight")
    doc = json.load(open(os.path.join(HERE, "parts_ram.json")))
    rec = {e["name"]: e for e in doc["parts"]}
    bad = []
    for n, p in parts.items():
        s = p["shape"]; ok = s.is_valid and len(s.solids()) == 1 and s.volume > 0
        wt = rec.get(n, {}).get("watertight")
        if not (ok and wt):
            bad.append((n, ok, wt))
    OUT["A"] = dict(n=len(parts), bad=bad, removed=doc.get("removed_parts"))
    verdict("A_valid_single_watertight", not bad, f"{len(parts) - len(bad)}/{len(parts)} valid single solids with watertight STL; bad {bad}")
    deleted = ["T_ram", "T_prichytka_fpc", "skr_fpc", "cap_pan", "skr_F5", "vl_F5", "skr_F6", "pena_J1"] + \
        [f"skr_F2_{i}" for i in range(1, 7)] + [f"vl_F2_{i}" for i in range(1, 7)]
    left = [n for n in deleted if n in parts or os.path.exists(os.path.join(HERE, "stl", n + ".stl"))]
    verdict("A_deleted_parts_gone", not left, f"deleted parts / exports still present: {left}")


# =====================================================================================================================
INTENDED = [   # thread / mesh contacts that overlap by design
    ("skr_F3a_", "vl_F3a_", "thread in the insert"), ("skr_F3b_", "vl_F3b_", "thread in the insert"),
    ("skr_F7_", "vl_F7_", "thread in the insert"), ("skr_F4_", "mat_F4_", "thread in the nut"),
    ("skr_F14_", "T_spodok", "thread-forming in the D1.7 pilot"), ("skr_F15", "T_most", "M3 thread in the D2.5 tap hole"),
    ("skr_F16_", "servo_J1", "thread in the servo case (modelled D1.6)"), ("pastorok_J1", "Z_koleso_J1", "gear mesh"),
    ("skr_F3b_", "T_most", "countersunk head in the countersink"),
]


def _intended(a, b):
    for pa, pb, why in INTENDED:
        if (a.startswith(pa) and b.startswith(pb)) or (b.startswith(pa) and a.startswith(pb)):
            return why
    return None


def check_B(parts):
    log("B. interference among RAM parts")
    names = list(parts)
    bb = {n: bbox(parts[n]["shape"]) for n in names}
    hits, declared, npairs = [], [], 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (la, ha), (lb, hb) = bb[a], bb[b]
            if np.any(la > hb + 0.01) or np.any(lb > ha + 0.01):
                continue
            npairs += 1
            v = common_volume(parts[a]["shape"], parts[b]["shape"])
            if v > 0.01 or v != v:
                why = _intended(a, b)
                (declared if why else hits).append((a, b, round(v, 3), why))
    for h in hits:
        log("   overlap", h)
    OUT["B"] = dict(pairs=npairs, unexpected=hits, declared=declared)
    verdict("B_no_unexpected_overlap", not hits, f"{npairs} bbox pairs, {len(hits)} unexpected, {len(declared)} declared fits")


# =====================================================================================================================
def lip_ylim():
    L = C.lip_outline(C.Z_WHITE, C.WALL, 720)
    m = L[:, 1] > 0; o = np.argsort(L[m, 0]); xs, ys = L[m, 0][o], L[m, 1][o]
    return lambda x: np.interp(np.abs(x), xs[xs >= 0], ys[xs >= 0], right=0.0)


def se_margin(P, a, b, n):
    return C.se_r(a, b, n, np.arctan2(P[:, 1], P[:, 0])) - np.hypot(P[:, 0], P[:, 1])


PIVOT_PARTS = ("T_cap", "ptfe_cap", "pd_F15", "skr_F15", "ptfe_podlozka")
LATE = {"pastorok_pan": "bonded on the STS3032 spline AFTER T_stred (in situ, through the bore, Loctite 638)"}


def env_rmax(z, azB):
    """max radius of the pan stage (PAN_ENV2 + sectors) at height z over pan -90..+90, seen at the B azimuth azB (deg)"""
    r = np.full(z.shape, -1.0)
    for z0, z1, rr in C.PAN_ENV2:
        z0 = max(z0, R2["GEAR_PAN"]["plane"][0])      # below the gear plane (-45.9, PTFE / deck below) only the lug sector reaches
        m = (z >= z0) & (z <= z1); r[m] = np.maximum(r[m], rr)
    for S in C.PAN_ENV2_SECTORS:
        if "lug" in S["what"]:
            continue                                  # annular sector r 27.6..31.6: see env_lug()
        lo, hi = S["az"][0] - 90.0, S["az"][1] + 90.0
        m = (z >= S["z"][0]) & (z <= S["z"][1]) & (((azB - lo) % 360.0) <= (hi - lo))
        r[m] = np.maximum(r[m], S["r"])
    return r


def env_lug(P):
    """clearance of points to the swept stop lug + bridge (annulus r 27.6..31.6, stage az 106.5..131.7 -> B az 16.5..221.7,
    z -47.2..-39.9; the block alone (z < -43.6) only from stage az 118.3 -> B az 28.3..221.7); +inf where not concerned"""
    St = R2["STOP"]; r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    r0, r1 = St["lug"]["r"]
    z = P[:, 2]
    a_lo = np.where(z < St["bridge"]["z"][0], St["lug"]["az"][0], St["bridge"]["az"][0]) - 90.0
    a_hi = St["lug"]["az"][1] + 90.0
    inaz = (az >= a_lo) & (az <= a_hi)
    inz = (z >= St["lug"]["z"][0]) & (z <= St["bridge"]["z"][1])
    radial = np.where(r < r0, r0 - r, np.where(r > r1, r - r1, -0.01))
    # angular distance to the swept sector ends for points beside it (radially inside the annulus)
    da = np.minimum((a_lo - az) % 360, (az - a_hi) % 360)
    ang = np.radians(da) * np.clip(r, r0, r1)
    vz = np.where(z < St["lug"]["z"][0], St["lug"]["z"][0] - z, np.where(z > St["bridge"]["z"][1], z - St["bridge"]["z"][1], 0.0))
    d = np.where(inaz & inz, radial, np.where(inz, np.where(radial > 0, np.hypot(radial, ang), ang), np.where(inaz, np.hypot(np.maximum(radial, 0), vz), 99.0)))
    return d


def check_C(parts):
    log("C. zones")
    res = {}
    T = [n for n, p in parts.items() if p["group"] == "T"]
    rows = {}
    for n in T:
        P = pts(parts, n); P = P[P[:, 2] > -78.0]
        if not len(P):
            continue
        cl = C.clearance_to_shell(P); i = int(np.argmin(cl))
        rows[n] = dict(min=round(float(cl[i]), 2), at=[round(float(v), 1) for v in P[i]])
    w = sorted(rows.items(), key=lambda kv: kv[1]["min"])[:6]
    for n, r in w:
        log(f"   shell clearance {n:16s} {r['min']:6.2f} at {r['at']}")
    res["shell"] = rows
    verdict("C1_inside_shell", all(r["min"] >= 0.45 for r in rows.values()), f"min {w[0][1]['min']} ({w[0][0]}) >= 0.45 (rev. 1 criterion)")
    yl = lip_ylim(); rel = C.LIP_RELIEF
    rows = {}
    for n in T:
        P = pts(parts, n); P = P[(np.abs(P[:, 0]) <= C.XS) & (P[:, 2] > -78.0)]
        if not len(P):
            continue
        lim = yl(P[:, 0])
        inr = (P[:, 0] >= rel["x"][0]) & (P[:, 0] <= rel["x"][1]) & (P[:, 1] < 0)
        lim = np.where(inr, np.maximum(lim, rel["y_min"]), lim)
        mg = lim - np.abs(P[:, 1]); i = int(np.argmin(mg))
        rows[n] = dict(min=round(float(mg[i]), 2), at=[round(float(v), 2) for v in P[i]])
    w = sorted(rows.items(), key=lambda kv: kv[1]["min"])[:8]
    for n, r in w:
        log(f"   lip margin {n:16s} {r['min']:6.2f} at {r['at']}")
    res["lip"] = rows
    bad = {n: r for n, r in rows.items() if r["min"] < C.TOWER_CLEAR - 0.005 and n not in LATE}
    verdict("C2_T_stred_can_be_lowered", not bad, f"min lip margin {min(r['min'] for n, r in rows.items() if n not in LATE)} (need 0.5); "
            f"bad {list(bad)}; mounted after T_stred: {[(n, rows[n]['min'], LATE[n]) for n in LATE if n in rows]}")
    rows = {}
    for n in T:
        if n == "T_spodok" or n.startswith(("skr_F1_", "pd_F1_")):       # F1 runs through the pad into the T_stred boss
            continue
        P = pts(parts, n); P = P[(P[:, 2] < -78.0) & (P[:, 2] > C.Z_FLOOR - 0.01)]
        if not len(P):
            continue
        mg = se_margin(P, *C.TUB_SE); i = int(np.argmin(mg))
        rows[n] = dict(min=round(float(mg[i]), 2), at=[round(float(v), 2) for v in P[i]])
    res["tub"] = rows
    verdict("C3_inside_tub", all(r["min"] >= 0.3 - 0.005 for r in rows.values()), f"min {min((r['min'], n) for n, r in rows.items())} (need 0.3)")
    hits = []
    Z = RV["F1"]["keepout"]
    for n in T:
        if n.startswith(("skr_F1_", "pd_F1_")):
            continue
        P = pts(parts, n)
        # integrator rev2: the real boss zone = the boss cylinder r 3.40 (+0.25) about (+-29, +-19) and the web band |y| >= 19.5
        # (measured on T_stred: toward the tower the footprint is the r 3.40 cylinder); the box was the conservative rev. 2 zone
        dbs = np.hypot(np.abs(P[:, 0]) - 29.0, np.abs(P[:, 1]) - 19.0)
        inz = (dbs < 3.40 + 0.25 - 0.02) | ((np.abs(P[:, 0]) > Z["x"][0] + 0.5 + 0.02) & (np.abs(P[:, 0]) < Z["x"][1] - 0.5 - 0.02)
                                           & (np.abs(P[:, 1]) > 19.5))
        m = inz & (P[:, 2] > C.Z_WHITE + 0.02) & (P[:, 2] < -75.0)
        if m.any():
            hits.append((n, int(m.sum())))
    res["f1_keepout"] = hits
    verdict("C4_F1_boss_zone", not hits, f"RAM parts inside the F1 boss zone (cylinder r 3.65 about (+-29, +-19) + web band |y| >= 19.5), z -81..-75: {hits} "
            "(tower kept 0.5 outside it)")
    rows = {}
    for n in T:
        if n in PIVOT_PARTS or n == "pastorok_pan" or n.startswith("kolik_dorazu"):
            continue
        P = pts(parts, n); P = P[(P[:, 2] >= -47.2) & (P[:, 2] <= 4.0)]
        if not len(P):
            continue
        r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
        rm = env_rmax(P[:, 2], az)
        cl = np.where(rm > 0, r - rm, 99.0)
        cl = np.minimum(cl, env_lug(P))
        i = int(np.argmin(cl))
        if cl[i] > 90:
            continue
        rows[n] = dict(min=round(float(cl[i]), 2), at=[round(float(v), 2) for v in P[i]])
    w = sorted(rows.items(), key=lambda kv: kv[1]["min"])[:8]
    for n, r in w:
        log(f"   PAN_ENV2 clearance {n:16s} {r['min']:6.2f} at {r['at']}")
    res["pan_env"] = rows
    verdict("C5_static_vs_PAN_ENV2", all(r["min"] >= 0.995 for r in rows.values()),
            f"min {w[0][1]['min']} ({w[0][0]}) >= 1.0 hard; below 1.3: {[(n, r['min']) for n, r in rows.items() if r['min'] < 1.3]}")
    piv = {}
    for n in PIVOT_PARTS:
        if n == "ptfe_podlozka":
            continue
        lo, hi = bbox(parts[n]["shape"])
        piv[n] = dict(r=round(max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])), 3), z_top=round(hi[2], 3))
    res["pivot"] = piv
    hub_r = R2["STACK"]["hub_disc_r"][0]
    verdict("C6_pivot_interface", all(v["r"] <= 4.501 and v["z_top"] <= -39.349 for v in piv.values()),
            f"{piv}; washer r 4.5 -> hub disc ring r {hub_r}: {hub_r - 4.5:.2f}; F15 head r 2.85 -> foot hole r 5.5: 2.65; head top -39.35 -> neck -36.5: 2.85")
    P = pts(parts, "pastorok_pan"); r = np.hypot(P[:, 0], P[:, 1]); m = (r >= 15.4) & (r <= 17.6)
    az = np.degrees(np.arctan2(P[m, 1], P[m, 0])) % 360
    D = R2["DRUM"]["az"]; lo, hi = D[0] - 90.0, D[1] + 90.0
    marg = np.minimum((az - hi) % 360, (lo - az) % 360)
    i = int(np.argmin(marg)); mm = float(np.radians(marg[i]) * r[m][i])
    res["pinion_vs_drum"] = dict(deg=round(float(marg[i]), 2), mm=round(mm, 2))
    verdict("C7_pinion_vs_drum_shroud", mm >= 1.0, f"min margin {marg[i]:.2f} deg = {mm:.2f} mm at r {r[m][i]:.2f} (architect 1.03 / 1.20)")
    St = R2["STOP"]; rowp = []
    for k, n in enumerate(("kolik_dorazu_1", "kolik_dorazu_2")):
        lo, hi = bbox(parts[n]["shape"]); c = (lo + hi) / 2
        rr = math.hypot(c[0], c[1]); a = math.degrees(math.atan2(c[1], c[0])) % 360
        half = math.degrees(math.asin(St["pin_d"] / 2 / rr))
        stop = (a + half) - St["lug"]["az"][0] if k == 0 else (a - half) - St["lug"]["az"][1]
        rowp.append(dict(name=n, r=round(rr, 3), az=round(a, 2), top=round(hi[2], 3), stop_at_pan=round(stop, 2)))
    res["stop_pins"] = rowp
    ok = all(abs(p["r"] - 30.0) < 0.02 and abs(p["top"] - St["pin_top"]) < 0.01 for p in rowp) and \
        abs(rowp[0]["stop_at_pan"] + 90) < 0.1 and abs(rowp[1]["stop_at_pan"] - 90) < 0.1
    verdict("C8_stop_pins", ok, f"{rowp} (lug faces stage az 118.3 / 131.7)")
    OUT["C"] = res


# =====================================================================================================================
def check_D(parts):
    log("D. seats / numbers on the solids")
    S = parts["T_spodok"]["shape"]; rows = []

    def row(name, val, nom, tol, note=""):
        ok = val is not None and abs(val - nom) <= tol
        rows.append(dict(name=name, value=None if val is None else round(float(val), 3), nominal=nom, tol=tol, ok=bool(ok), note=note))
        log(f"   {'ok ' if ok else 'BAD'} {name:50s} {val if val is None else round(float(val), 3)}  (nominal {nom} +-{tol}) {note}")
    for z in (-97.0, -94.5, -92.0):
        for az in (0, 90, 200, 300):
            u = (math.cos(math.radians(az)), math.sin(math.radians(az)), 0.0)
            row(f"6805 seat radius z {z} az {az}", boundary(S, (0, 0, z), u, tmax=25, step=0.2), RV["SEAT_R"], 0.01, "bearing r 18.5: slide + epoxy")
    row("cradle +Y wall inner face y", boundary(S, (-5, 0, -60), (0, 1, 0)), 12.55, 0.01, "STS3215 +0.2")
    row("cradle -Y wall inner face y", boundary(S, (-20, 0, -60), (0, -1, 0)), 12.55, 0.01)
    row("-X end wall inner face (x -29.7)", boundary(S, (-20, 0, -60), (-1, 0, 0)), 9.7, 0.01, "0.2 of PET shims")
    row("bumper face (x 16.7)", boundary(S, (10, 0, -75), (1, 0, 0)), 6.7, 0.01, "PORON 1.0")
    row("corner pad top (-X, +Y)", -80.0 - boundary(S, (-28.5, 11.5, -80), (0, 0, -1)), -83.3, 0.01)
    row("corner pad top (+X, -Y)", -80.0 - boundary(S, (14.5, -11.5, -80), (0, 0, -1)), -83.3, 0.01)
    row("air under the case over the plinth (-12.5, -12)", 0.7 + boundary(S, (-12.5, -12.0, -84.0), (0, 0, -1), tmax=5), 1.2, 0.05,
        "case bottom -83.3, plinth top -84.5")
    row("pan post +X top", -50.0 - boundary(S, (15.0, -23.5, -50.0), (0, 0, -1)), -56.5, 0.01)
    row("pan post +X inner face x", 11.0 + boundary(S, (11.0, -23.5, -61.0), (1, 0, 0)), 12.05, 0.01, "STS3032 x 11.75 + 0.3")
    row("stop post 1 top", -40.0 - boundary(S, (27.09 + 2.5, 12.89, -40.0), (0, 0, -1)), -48.2, 0.01)
    row("stop post 2 top", -40.0 - boundary(S, (-21.37 - 2.5, -21.06, -40.0), (0, 0, -1)), -48.2, 0.01)
    for k, (x, y) in enumerate(R2["STOP"]["pin_xy"], 1):
        row(f"pin hole {k} radius", boundary(S, (x, y, -52.0), (1, 0, 0), tmax=4), 1.525, 0.01, "pin r 1.5, slide + epoxy")
        row(f"pin hole {k} depth", boundary(S, (x, y, -48.3), (0, 0, -1), tmax=12) + 0.1, 8.7, 0.02, "bond 8.4 + 0.3")
    for nm, (x, y) in (("F3a", RV["F3A"][0]), ("F3b", RV["F3B"][0])):
        row(f"{nm} insert hole radius", boundary(S, (x, y, -49.0), (1, 0, 0), tmax=4), 1.8, 0.01, "insert OD 3.5 + 0.1")
    x, z = RV["CTRL"]["f7"][0]
    row("F7 standoff face y", 20.0 - boundary(S, (x + 2.0, 20.0, z), (0, -1, 0)), 16.5, 0.01, "carrier back face")
    row("F7 insert hole radius", boundary(S, (x, 15.5, z), (1, 0, 0), tmax=4), 1.65, 0.01, "insert OD 3.2 + 0.1")
    row("F8 insert hole radius (L, az 180)", boundary(S, (37.0, M.SHY - 7.5, M.SHZ), (0, 1, 0), tmax=4), 1.65, 0.01)
    row("capacitor trough radius", boundary(S, (9.0, RV["CAP"]["y"], RV["CAP"]["z"]), (0, 0, -1), tmax=8), 4.1, 0.01, "can r 4.0")
    yh, zh = M.AMP_HOLES[0]
    row("amp standoff face x", 36.0 + boundary(S, (36.0, yh + 1.8, zh), (1, 0, 0), tmax=6), 38.9, 0.01, "board 1.5 off the web")
    yh, zh = M.BUCK_HOLES[0]
    row("buck standoff face x", -36.0 - boundary(S, (-36.0, yh + 1.8, zh), (-1, 0, 0), tmax=6), -38.9, 0.01)
    row("column boss face x (L)", 45.0 - boundary(S, (45.0, M.SHY, M.SHZ + 9.5), (-1, 0, 0), tmax=12), C.X_COL_BOSS, 0.01)
    row("stop ring face x (L)", 45.0 - boundary(S, (45.0, M.SHY, M.SHZ - 12.2), (-1, 0, 0), tmax=12), C.X_COL_STOP, 0.01)
    Dk = parts["T_paluba"]["shape"]; Mo = parts["T_most"]["shape"]
    row("deck top z", -40.0 - boundary(Dk, (17.0, 10.0, -40.0), (0, 0, -1), tmax=10), -46.2, 0.005)
    row("deck thickness", thickness(Dk, (17.0, 10.0, -47.2), (0, 0, 1)), 2.0, 0.005)
    row("T_most thickness", thickness(Mo, (0.0, 8.0, -47.2), (0, 0, 1)), 2.0, 0.005)
    row("FFC wall top z", -40.0 - boundary(Dk, (0.0, 24.3, -40.0), (0, 0, -1), tmax=10), -43.0, 0.005)
    row("FFC wall thickness (az 90)", thickness(Dk, (0.0, 24.3, -44.0), (0, 1, 0)), 1.6, 0.005)
    row("C J1", float(np.hypot(*C.J1_AX)), 18.00, 1e-6)
    row("C pan (PAN_AX)", float(np.hypot(*M.PAX)), 21.600, 0.001)
    lo, hi = bbox(parts["pastorok_pan"]["shape"]); row("pan pinion plane bottom", lo[2], -45.9, 1e-3); row("pan pinion plane top", hi[2], -41.9, 1e-3)
    lo, hi = bbox(parts["pastorok_J1"]["shape"]); row("J1 pinion plane bottom", lo[2], -90.0, 1e-3); row("J1 pinion plane top", hi[2], -86.0, 1e-3)
    lo, hi = bbox(parts["ptfe_podlozka"]["shape"]); row("PTFE washer top", hi[2], -45.9, 1e-3)
    lo, hi = bbox(parts["T_cap"]["shape"]); row("T_cap top", hi[2], -41.8, 1e-3)
    lo, hi = bbox(parts["skr_F15"]["shape"]); row("F15 head top", hi[2], -39.35, 1e-3)
    lo, hi = bbox(parts["servo_pan"]["shape"]); row("pan servo top of the boss (= pinion bottom - 0.3)", -46.2 if hi[2] > -46.21 else None, -46.2, 1e-3)
    row("T_cap + tape diameter (gear bore 8.00)", 2 * (RV["CAP_BOSS"]["r"] + 0.13), 7.96, 1e-3, "radial 0.02")
    st = R2["STACK"]
    stack = (st["foot"][1] - st["foot"][0]) + st["rest_gap"] + (st["hub_disc"][1] - st["hub_disc"][0]) + (st["gear"][1] - st["gear"][0]) + \
        (st["ptfe"][1] - st["ptfe"][0]) + (M.ZD1 - M.ZD0) + (st["shim"][1] - st["shim"][0]) + 35.0 + 1.2
    row("stack neck bottom -> cap underside", stack, 48.0, 1e-6)
    OUT["D"] = rows
    verdict("D_seats", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} measurements within tolerance")


# =====================================================================================================================
WALLS = [   # name, part, point inside the wall, direction, nominal, minimum allowed
    ("cradle +Y wall", "T_spodok", (-15.0, 13.8, -65.0), (0, 1, 0), 2.5, 2.5),
    ("cradle -Y wall (outside the recess)", "T_spodok", (-22.0, -13.8, -65.0), (0, 1, 0), 2.5, 2.5),
    ("cradle -Y wall between the servos (declared 1.69)", "T_spodok", (0.0, -13.4, -60.0), (0, 1, 0), 1.693, 1.65),
    ("-X end wall", "T_spodok", (-31.0, 0.0, -65.0), (1, 0, 0), 2.5, 2.5),
    ("column web L", "T_spodok", (35.9, 0.0, -60.0), (1, 0, 0), 3.0, 3.0),
    ("column web P", "T_spodok", (-35.9, 0.0, -60.0), (1, 0, 0), 3.0, 3.0),
    ("column rib L", "T_spodok", (40.0, -7.75, -60.0), (0, 1, 0), 2.5, 2.0),
    ("column box closure L", "T_spodok", (41.0, 3.0, -42.0), (1, 0, 0), 2.0, 2.0),
    ("cap floor", "T_spodok", (20.0, 18.0, -83.4), (0, 0, 1), 2.2, 2.0),
    ("J1 corner pad", "T_spodok", (-27.0, 11.5, -84.0), (0, 0, 1), 1.2, 1.2),
    ("pan post +X nut-slot ceiling", "T_spodok", (16.0, -20.79, -57.2), (0, 0, 1), 1.5, 1.5),
    ("pan post +X wall in front of the nut slot", "T_spodok", (16.0, -24.5, -58.6), (0, 1, 0), 1.96, 1.5),
    ("pan post +X front leg", "T_spodok", (14.0, -25.8, -67.0), (0, 1, 0), 1.6, 1.5),
    ("stop post 1 wall beside the pin hole", "T_spodok", (27.09 + 2.5, 12.89, -52.0), (1, 0, 0), 1.975, 1.6),
    ("stop post 2 wall beside the pin hole", "T_spodok", (-21.37 - 2.5, -21.06, -52.0), (1, 0, 0), 1.975, 1.6),
    ("plinth skin outside the base-FFC slot (az 104)", "T_spodok", (23.2 * math.cos(math.radians(104)), 23.2 * math.sin(math.radians(104)), -88.0),
     (math.cos(math.radians(104)), math.sin(math.radians(104)), 0), 1.6, 1.2),
    ("plinth wall (r 17..24)", "T_spodok", (0.0, -20.5, -88.0), (0, 1, 0), 7.0, 2.0),
    ("F1 pad under the counterbore", "T_spodok", (29.0 + 2.3, 19.0, -82.0), (0, 0, 1), 1.6, 1.5),
    ("J1 stop lug (tangential)", "T_spodok", (0.0, 19.8, -100.0), (1, 0, 0), 5.0, 5.0),
    ("J1 stop lug (radial, r 18.65..21)", "T_spodok", (0.0, 19.8, -100.0), (0, 1, 0), 2.35, 2.3),
    ("deck plate", "T_paluba", (17.0, 10.0, -47.2), (0, 0, 1), 2.0, 2.0),
    ("FFC wall", "T_paluba", (0.0, 24.3, -44.5), (0, 1, 0), 1.6, 1.5),
    ("T_cap wall", "T_cap", (2.8, 0.0, -44.0), (1, 0, 0), 2.15, 2.0),
    ("T_most", "T_most", (0.0, 8.0, -47.2), (0, 0, 1), 2.0, 2.0),
]
INSERT_WALLS = [
    (f"F3a {tuple(RV['F3A'][0])}", (RV["F3A"][0][0], RV["F3A"][0][1], -50.0), "z", 1.8), ("F3a (31,5)", (31.0, 5.0, -50.0), "z", 1.8),
    ("F3b (6,15.95)", (6.0, 15.95, -50.0), "z", 1.8), ("F3b (18.5,-15.95)", (18.5, -15.95, -50.0), "z", 1.8),
    ("F7 x -25", (RV["CTRL"]["f7"][0][0], 15.5, -62.5), "y", 1.65), ("F7 x 25.8", (RV["CTRL"]["f7"][1][0], 15.5, -62.5), "y", 1.65),
    ("F8 L az 60", (37.0, M.SHY + 3.75, M.SHZ + 6.5), "x", 1.65), ("F8 L az 300", (37.0, M.SHY + 3.75, M.SHZ - 6.5), "x", 1.65),
    ("F8 P az 180", (-37.0, M.SHY - 7.5, M.SHZ), "x", 1.65),
]


def check_E(parts):
    log("E. walls, insert walls, roots, board air, deck trim")
    rows = []
    for name, part, p, d, nom, mn in WALLS:
        t = thickness(parts[part]["shape"], p, d)
        ok = t is not None and t >= mn - 0.01
        rows.append(dict(name=name, part=part, t=None if t is None else round(t, 3), nominal=nom, min=mn, ok=ok))
        log(f"   {'ok ' if ok else 'BAD'} {name:50s} {t if t is None else round(t, 3)} (nominal {nom}, min {mn})")
    Dk = parts["T_paluba"]["shape"]; (px, py) = R2["STOP"]["pin_xy"][0]; a = math.radians(25.43)
    tdir = np.array([math.sin(a), -math.cos(a), 0.0])
    t = thickness(Dk, np.array([px, py, -47.2]) + tdir * 1.85, tdir)
    rows.append(dict(name="deck C-ear behind pin 1 (CW side)", part="T_paluba", t=None if t is None else round(t, 3), nominal=2.0, min=1.5,
                     ok=t is not None and t >= 1.5))
    log(f"   deck C-ear behind pin 1: {t}")
    OUT["E_walls"] = rows
    verdict("E1_walls", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} designed walls >= their minimum "
            f"(declared thin: cradle front wall 1.69 between the two servos)")
    S = parts["T_spodok"]["shape"]; iw = []
    for name, c, ax, rh in INSERT_WALLS:
        k = "xyz".index(ax); dmin = 99.0
        o = [i for i in range(3) if i != k]
        for ang in range(0, 360, 30):
            u = np.zeros(3); u[o[0]] = math.cos(math.radians(ang)); u[o[1]] = math.sin(math.radians(ang))
            p = np.array(c, float) + u * (rh + 0.05)
            if not inside(S, p):
                continue
            b = boundary(S, p, u, tmax=8.0, step=0.1)
            if b is not None:
                dmin = min(dmin, b + 0.05)
        iw.append(dict(name=name, min_wall=round(dmin, 2), ok=dmin >= 1.6 - 0.01))
        log(f"   insert wall {name:22s} {dmin:.2f}")
    OUT["E_insert_walls"] = iw
    verdict("E2_insert_walls", all(r["ok"] for r in iw), f"min {min(r['min_wall'] for r in iw)} (need 1.6)")
    rr = []
    for r in M.ROOTS:
        s = parts[r["part"]]["shape"]
        ok = inside(s, np.array(r["p"]) + np.array(r["u"]) * 0.3 * r["R"])
        rr.append(dict(r, ok=ok))
        if not ok:
            log("   root NOT found:", r["part"], r["name"], r["p"])
    OUT["E_roots"] = rr
    verdict("E3_roots", all(r["ok"] for r in rr), f"{sum(r['ok'] for r in rr)}/{len(rr)} listed loaded roots carry their fillet "
            "(probe at 0.3 R on the bisector)")
    lo, hi = bbox(parts["menic"]["shape"]); lo2, hi2 = bbox(parts["zosilnovac"]["shape"])
    air_b = -RV["COL"]["web"][1] - hi[0]; air_a = lo2[0] - RV["COL"]["web"][1]
    verdict("E4_board_air", air_b >= 1.5 - 1e-6 and air_a >= 1.5 - 1e-6, f"buck {air_b:.2f}, amp {air_a:.2f} (need 1.5); D4 vents in the webs")
    bad = []
    for n in ("T_paluba", "T_most"):
        P = pts(parts, n); r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
        m = (r > 26.6 + 0.01) & (az > RV["DECK_TRIM"]["az"][0] + 0.05) & (az < RV["DECK_TRIM"]["az"][1] - 0.05)
        if m.any():
            bad.append((n, int(m.sum())))
    verdict("E5_deck_trim", not bad, f"deck / bridge points at r > 26.6 in B az 26.2..223.8: {bad}")


# =====================================================================================================================
def tool_cyl(p0, d, L, r=2.25):
    p0 = np.array(p0, float); d = np.array(d, float) / np.linalg.norm(d)
    z = Vector(0, 0, 1); v = Vector(*d); ax = z.cross(v)
    rot = bd.Location()
    if ax.length > 1e-9:
        ang = math.degrees(math.acos(max(-1.0, min(1.0, z.dot(v)))))
        rot = bd.Location((0, 0, 0), (ax.X, ax.Y, ax.Z), ang)
    return bd.Pos(*(p0 + d * L / 2)) * (rot * bd.Cylinder(r, L))


TOOLS = [  # screw prefix, tool direction (None: from the fastener record), length, situation
    ("skr_F1_", (0, 0, -1), 25.0, "torso off the base, from below"),
    ("skr_F3a_", (0, 0, 1), 40.0, "T3 before T_stred / service with T_stred off"),
    ("skr_F3b_", (0, 0, 1), 40.0, "T3 before T_stred / service with T_stred off"),
    ("skr_F7_", (0, 1, 0), 15.0, "through the door (+Y)"),
    ("skr_F14_", None, 25.0, "side caps off (+-X)"),
    ("skr_F15", (0, 0, 1), 45.0, "through the empty well (neck out)"),
    ("skr_F16_", (0, 0, -1), 25.0, "torso off the base, from below"),
]


def check_F(parts):
    log("F. tool channels")
    rows = []
    stat = [n for n, p in parts.items() if p["group"] == "T"]
    for pre, d0, L, note in TOOLS:
        for n in [k for k in parts if k.startswith(pre)]:
            rec = parts[n]["fastener"]; h = np.array(rec["head"], float)
            d = d0 if d0 is not None else ((-1, 0, 0) if rec["dir"] == "+X" else (1, 0, 0))
            dd = np.array(d, float)
            cyl = tool_cyl(h + dd * 1.7, dd, L)
            hits = []
            for m in stat:
                if m == n or m.startswith(("pd_F", "vl_F", "mat_F")):
                    continue
                v = common_volume(cyl, parts[m]["shape"])
                if v > 0.01:
                    hits.append((m, round(v, 2)))
            rows.append(dict(screw=n, dir=[float(v) for v in dd], hits=hits, note=note, ok=not hits))
            log(f"   {'ok ' if not hits else 'HIT'} {n:12s} {note:46s} {hits}")
    for n in ("skr_F4_1", "skr_F4_2"):
        h = np.array(parts[n]["fastener"]["head"], float)
        inward = -np.array([h[0], h[1], 0.0]) / math.hypot(h[0], h[1])
        best = None
        for tilt in (0.0, 5.0, 10.0):
            s_, c_ = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
            d = np.array([inward[0] * s_, inward[1] * s_, c_])
            zs = np.array([-10.5, -2.0]); t = (zs - h[2]) / d[2]; P = h[None, :] + t[:, None] * d[None, :]
            rb = float(np.max(np.hypot(P[:, 0], P[:, 1]))) + 0.65
            cyl = tool_cyl(h + d * 1.4, d, 50.0, r=0.65)
            hits = [m for m in stat if m != n and not m.startswith("mat_F4") and common_volume(cyl, parts[m]["shape"]) > 0.005]
            if rb <= 26.65 - 0.1 and not hits:
                best = dict(screw=n, tilt=tilt, r_at_bore=round(rb, 2), hits=hits, ok=True, note="D1.3 key, before the stage (T7)")
                break
        rows.append(best or dict(screw=n, ok=False, note="no path <= 10 deg"))
        log(f"   F4 {n}: {rows[-1]}")
    OUT["F"] = rows
    verdict("F_tool_channels", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} screws reachable "
            "(D4.5 channel; F4: D1.3 ball-end key through the bore r 26.65 before the stage goes in)")


# =====================================================================================================================
def check_G(parts):
    log("G. J1 sweep vs the dummy hub")
    L = RV["J1_LUG"]; half = M.DUMMY["stop"]["half"]
    th = 180.0 - half - math.degrees(math.atan2(L["w"] / 2, L["r"][0]))
    OUT["G_stop"] = dict(stop_at=round(th, 2), dummy_block=M.DUMMY["stop"], lug=L)
    verdict("G1_J1_stop_angle", 150.0 < th <= 155.5, f"lug face meets the block (az 270 +- {half}) at +-{th:.2f} deg (firmware 150, spec 155)")
    rot = ["T_spodok", "servo_J1", "skr_F16_1", "skr_F16_2", "pd_F16_1", "pd_F16_2", "pastorok_J1"]
    dum = ["Z_naboj_test", "Z_skrutka_M8", "Z_pruzina_1", "Z_pruzina_2"]

    def prof(names):
        out = []
        for n in names:
            P = pts(parts, n); P = P[P[:, 2] < -84.4]
            if len(P):
                out.append(np.stack([np.hypot(P[:, 0], P[:, 1]), P[:, 2]], 1))
        return np.concatenate(out)
    A = prof(rot); B = prof(dum)
    A = A[~((A[:, 1] < -97.9) & (A[:, 0] > 18.6) & (A[:, 0] < 21.05))]   # stop lug: angular check G1
    dmin, at = 99.0, None
    for z0 in np.arange(-114.0, -84.0, 0.5):
        a = A[(A[:, 1] >= z0) & (A[:, 1] < z0 + 0.5)]; b = B[(B[:, 1] >= z0 - 1.5) & (B[:, 1] < z0 + 2.0)]
        if len(a) and len(b):
            dd = np.hypot(a[:, None, 0] - b[None, :, 0], a[:, None, 1] - b[None, :, 1]); i = np.unravel_index(np.argmin(dd), dd.shape)
            if dd[i] < dmin:
                dmin, at = float(dd[i]), (a[i[0]].round(2).tolist(), b[i[1]].round(2).tolist())
    P = pts(parts, "pastorok_J1"); r = float(np.hypot(P[:, 0], P[:, 1]).max())
    OUT["G"] = dict(min_rz=round(dmin, 3), at=at, pinion_orbit_r=round(r, 3))
    verdict("G2_J1_sweep", dmin >= 0.29, f"rotating torso parts (lug excluded) vs dummy, swept (r, z): {dmin:.3f} at {at}; "
            f"pinion orbit r {r:.2f} (base opening r >= 29.0)")


# =====================================================================================================================
def check_H(parts):
    log("H. carrier: USB envelope, connector reach")
    E = R2["CTRL2"]["plug_env"]
    env = C.box(E["x"][0], E["x"][1], E["y"][0], E["y"][1], E["z"][0], E["z"][1])
    hits = [(n, round(v, 3)) for n, p in parts.items() if p["group"] == "T" for v in [common_volume(env, p["shape"])] if v > 0.001]
    verdict("H1_usb_plug_envelope_free", not hits, f"RAM parts in x {E['x']} y {E['y']} z {E['z']}: {hits}")
    rows = []
    for name, (x0, x1, y1, z0, z1) in M.CTRL_BLOCKS.items():
        if not name.startswith("J_"):
            continue
        xc, zc = 0.5 * (x0 + x1), 0.5 * (z0 + z1)
        yb = float(C.y_surface(xc, zc, side=1)) + 1.0
        line = C.cyl_y(0.5, y1 + 0.05, yb, xc, zc)
        hit = [n for n, p in parts.items() if p["group"] == "T" and n != "DPS_riadenie" and common_volume(line, p["shape"]) > 0.0005]
        ok = abs(xc) <= 28.25 - 1.0 and -72.25 + 1.0 <= zc <= -11.75 - 1.0 and not hit
        rows.append(dict(conn=name, x=round(xc, 2), z=round(zc, 2), y_door=round(yb, 2), hits=hit, ok=ok))
        log(f"   {'ok ' if ok else 'BAD'} {name:26s} x {xc:6.2f} z {zc:6.2f} -> door y {yb:.1f} {hit}")
    OUT["H_reach"] = rows
    verdict("H2_connectors_reachable_from_the_door", all(r["ok"] for r in rows),
            "straight +Y line from every connector face to the door opening (x +-28.25, z -72.25..-11.75); stage above z -41.9 at pan 0")


# =====================================================================================================================
def check_S(parts):
    log("S. strength rows (Z2 allowables) on the rev. 2 geometry")
    sys.path.insert(0, os.path.join(HERE, "overenie_pevnost"))
    import pv_lib as L
    L._CACHE.clear()
    rows = []

    def row(no, feat, case, section, sigma, allow, note="", kt=1.0, info=False):
        s = sigma * kt; ok = s <= allow + 1e-9
        rows.append(dict(no=no, feature=feat, case=case, section=section, stress=round(s, 2), kt=kt, allowable=allow,
                         margin=round(allow / s, 2) if s > 0 else 99.0, ok=bool(ok), note=note, info=info))
        log(f"   {'ok  ' if ok else ('info' if info else 'FAIL')} {no:5s} {feat:60s} {case:34s} {s:7.2f} / {allow} {note}")
    zs = {"box z -42": -42.0, "U below the box z -55": -55.0, "U z -70": -70.0, "foot z -79.5": -79.5}
    # integrator rev2: column HEAD + shoulder PLATE (z -38 .. -8): every section from the box top to above the shoulder axis
    for z in (-37.0, -35.0, -33.0, -31.0, -30.0, -29.0, -28.0, -26.0, -24.0, -21.0, -19.0, -17.0, -14.0, -11.0, -9.0):
        zs[f"head / plate z {z:.0f}"] = z
    secs = {}
    for k, z in zs.items():
        r = L.sec("T_spodok", "z", z, window=(20.0, 44.5, -24.0, 30.0) if z > -40.0 else (33.0, 44.5, -12.0, 18.0), h=0.03)
        zm = L.zmods(r)
        secs[k] = dict(A=round(r["A"], 1), Zx=round(min(zm["Zw_p"], zm["Zw_m"]), 1), Zy=round(min(zm["Zu_p"], zm["Zu_m"]), 1))
        log(f"   column section {k}: {secs[k]}")
    OUT["S_column_sections"] = secs
    for k, z in zs.items():
        Mx = 720.0 + 10.0 * max(0.0, -17.0 - z)
        row("42/44", f"column {k} (alone; cap shell share ignored)", "L5 10 N along X at the arm tip", f"Zx {secs[k]['Zx']}",
            Mx / secs[k]["Zx"], A_N, f"M {Mx:.0f} N.mm" + ("; decisive: connected section 42c" if z < -48 else ""), kt=1.3,
            info=z < -48)
        My = 720.0
        row("42y", f"column {k}", "L5 10 N along Y (arm down, 72 mm)", f"Zy {secs[k]['Zy']}", My / secs[k]["Zy"], A_N, "", kt=1.3)
        row("43", f"column {k}", "lifted by one arm 15 N", f"Zx {secs[k]['Zx']}", 15.0 * 13.6 / secs[k]["Zx"] + 15.0 / secs[k]["A"], A_N, "", kt=1.3)
    comp = {}
    for k, z in (("z -55", -55.0), ("z -70", -70.0), ("z -79.5", -79.5)):
        r = L.sec("T_spodok", "z", z, window=(20.0, 44.5, -16.0, 18.0), h=0.04)
        zm = L.zmods(r); comp[k] = dict(A=round(r["A"], 1), Zx=round(min(zm["Zw_p"], zm["Zw_m"]), 1))
        Mx = 720.0 + 10.0 * (-17.0 - z)
        row("42c", f"column + full-height bridge walls (connected section x 20..44.5) {k}", "L5 10 N along X at the arm tip",
            f"Zx {comp[k]['Zx']}", Mx / comp[k]["Zx"], A_N, f"M {Mx:.0f} N.mm; plane-section estimate, FE (K12) to confirm", kt=1.3)
    OUT["S_column_composite"] = comp
    Aen = (41.0 - 35.9) * (13.75 + 7.75); circ = 21.5 / 3.0 + 21.5 / 2.0 + 2 * 5.1 / 2.5
    J = 4 * Aen ** 2 / circ; tau = 10.0 * 18.3 / (2 * Aen * 2.0)
    row("45", f"column box torsion (closed, J {J:.0f} mm4)", "L5 10 N along Y at the hub", "Bredt t 2.0", tau / 0.6, A_N, "tau / 0.6")
    Pre = 0.05 / (0.2 * 0.002); ring = math.pi * (12.8 ** 2 - 11.6 ** 2)
    row("46", "stop ring 0.7 x 1.2 under the cap flange (3 x F8 preload)", "sustained, F8 0.05 N.m", f"A {ring:.0f}", 3 * Pre / ring, A_S,
        "K 0.2; 0.04 N.m -> 3.3")
    row("40", "F8 M2 bonded inserts in the column boss", "L5 (max bolt 29.8 N, p08)", "D3.2 x 3.0", 29.8 / (math.pi * 3.2 * 3.0), A_EP, "epoxy")
    rc = RV["J1_LUG"]["r"][0] + 1.2
    for case, Tq, allow in (("L4 clutch-limited 0.40 N.m", 0.40, A_N), ("L4 hand on the stop 0.6 N.m", 0.60, A_A)):
        F = Tq * 1000.0 / rc
        Lw = RV["J1_LUG"]; Zl = (Lw["r"][1] - Lw["r"][0]) * Lw["w"] ** 2 / 6.0
        row("49", f"J1 stop lug {Lw['r'][1] - Lw['r'][0]:.2f} x {Lw['w']} root at z -98 (R1)", case, f"Z {Zl:.1f}, lever 2.15",
            F * 2.65 / Zl, allow, f"F {F:.1f} N, block top -99.3 -> lever 2.65", kt=1.4)
    S = parts["T_spodok"]["shape"]; padA = []
    for (x0, x1) in RV["J1_PADS"]["x"]:
        for sy in (1, -1):
            n = sum(inside(S, (x, sy * y, -83.9)) for x in np.arange(x0 + 0.25, x1, 0.5) for y in np.arange(7.6, 12.5, 0.5))
            padA.append(round(n * 0.25, 1))
    Fp = 30.0 / 4 + 0.6
    row("50", "J1 corner pad 1.2 (case corner, two-edge supported, lever 1.5)", "L2 30 N / 4 + servo", f"pads {padA} mm2",
        6 * Fp * 1.5 / (5.0 * 1.2 ** 2) * 0.5, A_N, "plate estimate (half the one-edge cantilever)")
    row("50b", "J1 corner pads contact pressure", "L2", f"sum {sum(padA):.1f} mm2", (30.0 + 2.4) / max(1.0, sum(padA)), A_N)
    for case, Tq, allow in (("L4 clutch 0.40 N.m", 0.40, A_N), ("L8 locked clutch, 638 releases at 1.1 N.m", 1.1, A_A)):
        F = Tq * 1000.0 / 45.2
        row("48", "cradle long wall 2.5 (case-corner reaction, b_eff 15, lever 5)", case, "2.5 x 15", 6 * F * 5.0 / (15.0 * 2.5 ** 2), allow,
            f"F {F:.1f} N per wall (F16 x2 + end wall share ignored)", kt=1.3)
    row("51", "6805 shoulder r 17..18.5 (L2 + torso weight)", "L2", "183 mm2", 40.0 / (math.pi * (18.5 ** 2 - 17.0 ** 2)), A_N)
    row("51b", "6805 bond in the D37.15 seat", "L1 x 2", "816 mm2", 30.0 / (math.pi * 37.15 * 7.0), A_EP, "epoxy")
    Pf15 = 0.08 / (0.2 * 0.003); Acap = math.pi * (3.85 ** 2 - 1.7 ** 2); Zcap = math.pi * (7.7 ** 4 - 3.4 ** 4) / (32 * 7.7)
    row("S06", "T_cap compression under the F15 preload", "sustained, F15 0.08 N.m", f"A {Acap:.1f}", Pf15 / Acap, A_S, "0.12 N.m (spec) -> 5.3 MPa")
    row("S06b", "T_cap root: radial mesh 65 N x 2.3 + preload", "L8", f"Z {Zcap:.1f}", 65 * 2.3 / Zcap * 1.2 + Pf15 / Acap, A_N, "Kt 1.2 (R0.6)")
    row("S06c", "pivot journal on PTFE tape D7.96 x 4.0", "L8", "31.8 mm2", 65.0 / (7.96 * 4.0), 5.0, "Z3.8 sliding limit 5")
    row("S06d", "T_cap bond on T_most (radial 65 N)", "L8", "53 mm2", 65.0 / (math.pi * (4.45 ** 2 - 1.7 ** 2)), A_EP, "epoxy")
    P2SEC = {}
    A_, B_ = np.array(RV["F3B"][0]), np.array(RV["F3B"][1]); dv = B_ - A_
    dist = abs(dv[0] * (-A_[1]) - dv[1] * (-A_[0])) / np.linalg.norm(dv)
    lc = 4.8; Rc = 30.0 * dist / lc; Ft = (30.0 + Rc) / 2
    row("A7a", f"F3b bonded M2.5 inserts (pivot {dist:.1f} off the screw line)", "L1 x 2 (30 N)", "D3.5 x 4.0", Ft / (math.pi * 3.5 * 4.0), A_EP,
        f"{Ft:.0f} N per screw, wall-top reaction {Rc:.0f} N")
    row("A7b", "+Y wall top under T_most (2.5 x 6 contact)", "L1 x 2", "15 mm2", Rc / 15.0, A_N)
    row("A7c", f"T_most Al 2.0 bending (30 N x {dist:.1f}, b 25)", "L1 x 2", "Z 16.7", 30.0 * dist / 16.7, 80.0, "Al: yield 130 (5754-H22) / 1.6")
    row("A7d", "F15 M3 in T_most, 0.8 engaged (strip about 700 N): load as % of strip x 0.8", "0.08 N.m + L1", "-", (Pf15 + 30.0) / 700.0 * 80.0, 80.0)
    for case, F, allow in (("L3 hand 0.6 N.m (abuse)", 20.0, A_A), ("L8 servo stall 0.88 N.m at the stage", 29.0, A_N)):
        row("S05a", "pin 1 bearing in the deck C-ear (2.0 x D3)", case, "6 mm2", F / 6.0, allow)
        row("S05b", "deck C-ear ligaments (2 x 2.0 x 2.95)", case, "11.8 mm2", F / 11.8, allow)
        row("S05c", "pin 2 in its post (cantilever 2.3, bond 8.4)", case, "D3.05 x 8.4", 6 * F * 2.3 / (3.0 * 8.4 ** 2) + F / (3.0 * 8.4), allow)
        # integrator rev2: post 2 = block (x -24.7..-17.87) on a column to the floor merged with the -X pan post (+ front wall)
        a = math.radians(R2["STOP"]["pin_az"][1] + 90.0); fx, fy = F * math.cos(a), F * math.sin(a)
        for zc in (-60.0, -70.0, -80.0):
            if zc not in P2SEC:
                rr = L.sec("T_spodok", "z", zc, window=(-26.0, -11.0, -26.5, -12.4), h=0.03); zm = L.zmods(rr)
                P2SEC[zc] = (min(zm["Zw_p"], zm["Zw_m"]), min(zm["Zu_p"], zm["Zu_m"]), rr["A"])
            Zx_, Zy_, A_ = P2SEC[zc]
            lev = -45.9 - zc
            row("S05d", f"post-2 column + -X pan post + front wall at z {zc:.0f}", case, f"Zx {Zx_:.0f} Zy {Zy_:.0f}",
                abs(fx) * lev / Zx_ + abs(fy) * lev / Zy_, allow, f"F {F:.0f} N at z -45.9, lever {lev:.1f} (both components added)", kt=1.3)
        row("S05e", "steel pin D3 bending (lever 2.3)", case, "Z 2.65", F * 2.3 / 2.65, 400.0, "hardened dowel")
    row("S-pp", "pan-servo posts (radial 22 N, lever 25.8, 2 posts on the front wall)", "L8", "Z 86.7", 22.0 * 25.8 / 2 / 86.7, A_N, kt=1.3)
    TQ = dict(R2["TORQUE"]); TQ_SPEC = dict(R2["TORQUE"])
    TQ.update(TORQUE_RAM)                                 # recommended torques under the Z2 allowables (spec values fail)
    joints = [
        ("F1 M2.5 head + DIN 125 on the pad", 2.5, TQ["M25_insert"], math.pi * (3.0 ** 2 - 1.35 ** 2), A_S, "washer bearing on resin"),
        ("F3a M2.5 head + DIN 125 on the deck", 2.5, TQ["M25_insert"], math.pi * (3.0 ** 2 - 1.35 ** 2), A_S, "washer bearing on resin"),
        ("F3a / F3b M2.5 bonded insert", 2.5, TQ["M25_insert"], math.pi * 3.5 * 4.0, A_EP, "epoxy"),
        ("F4 DIN 562 nut on the slot ceiling", 2.0, TQ["M2_nut_on_resin"], 16.0 - math.pi, A_S, "nut bearing on resin"),
        ("F7 M2 bonded insert", 2.0, TQ["M2_insert"], math.pi * 3.2 * 3.0, A_EP, "epoxy"),
        ("F8 M2 bonded insert (screw: OBAL)", 2.0, TQ["M2_insert"], math.pi * 3.2 * 3.0, A_EP, "epoxy"),
        ("F16 M2 head + DIN 125 on the 1.2 pad", 2.0, TQ["J1_pads"], math.pi * (2.5 ** 2 - 1.1 ** 2), A_S, "washer bearing on resin"),
    ]
    tq = []
    spec_of = {"F1": "M25_insert", "F3a M2.5 head": "M25_insert", "F3a / F3b": "M25_insert", "F4": "M2_nut_on_resin", "F7": "M2_insert",
               "F8": "M2_insert", "F16": "J1_pads"}
    for nm, d, T_, A_l, allow, what in joints:
        Ts = next(TQ_SPEC[v] for k, v in spec_of.items() if nm.startswith(k))
        F = T_ / (0.2 * d * 1e-3); s = F / A_l; Tmax = allow * A_l * 0.2 * d * 1e-3; ss = Ts / (0.2 * d * 1e-3) / A_l
        tq.append(dict(joint=nm, torque_spec=Ts, stress_at_spec=round(ss, 2), spec_ok=bool(ss <= allow), torque_ram=T_, preload_N=round(F),
                       stress=round(s, 2), allow=allow, torque_max=round(Tmax, 3), what=what))
        row("L7", nm, f"{T_} N.m (RAM; spec {Ts}: {ss:.1f} MPa)", f"A {A_l:.1f}", s, allow, f"{what}; max {Tmax:.3f} N.m")
    OUT["S_torque_table"] = tq
    OUT["S"] = rows
    bad = [r for r in rows if not r["ok"] and not r["info"]]
    verdict("S_strength_rows", not bad, f"{len(rows) - len(bad)}/{len(rows)} rows within the Z2 allowable; FAIL: "
            f"{[(r['no'], r['feature'][:44], r['case'][:24], r['stress']) for r in bad]}")


# =====================================================================================================================
BUILD = (211.68, 118.37, 220.0)
TORQUE_RAM = dict(M25_insert=0.045, M2_nut_on_resin=0.02, M2_insert=0.03, J1_pads=0.025)   # N.m, K 0.2 (see S / STATUS)


def check_P(parts):
    log("P. print table (K10 / K13)")
    rows = []
    tilt = {"T_spodok": 15.0, "T_paluba": 70.0}
    for n, (fn, grp, mat, label) in M.PRINTED.items():
        lo, hi = bbox(parts[n]["shape"]); ext = hi - lo
        if n in tilt:
            a = math.radians(tilt[n])
            ext = np.array([ext[0], ext[1] * math.cos(a) + ext[2] * math.sin(a), ext[1] * math.sin(a) + ext[2] * math.cos(a)])
        fits = bool(all(np.sort(ext + 10.0) <= np.sort(np.array(BUILD))))
        rows.append(dict(part=n, mat=mat, extents_in_print=[round(float(v), 1) for v in ext], fits_with_5mm=fits, **M.PRINT[n]))
        log(f"   {n:14s} {mat:12s} {np.round(ext, 1)} fits {fits}")
    resin = all(parts[n]["mat"].startswith("resin") for n in M.PRINTED)
    k13 = dict(no_petg_pom=resin, insert_holes="M2.5 D3.6 (OD 3.5 + 0.1), M2 D3.3 (OD 3.2 + 0.1), all bonded",
               countersunk="only F3b DIN 7991 in the aluminium T_most", fits="pins D3.05/3.0, 6805 D37.15/37.0, T_cap 7.96 in 8.00 H7, "
               "pinions on metal splines (Loctite 638): slide fits", flex="no hook / clip / snap",
               thread_forming="F14 only (one-time, D1.7 pilot, 4.1 engaged >= 2d, boss D5)")
    OUT["P"] = dict(rows=rows, k13=k13)
    verdict("P_print_table", all(r["fits_with_5mm"] for r in rows) and resin, f"{[(r['part'], r['extents_in_print']) for r in rows]}")


def check_X(parts):
    log("X. advisory real-mesh clearances (ram2_work/cross_rev2.json)")
    f = os.path.join(HERE, "ram2_work", "cross_rev2.json")
    if not os.path.exists(f):
        verdict("X_cross_module_advisory", True, "not run")
        return
    d = json.load(open(f)); OUT["X"] = d
    intended = {("DPS_riadenie", "ffc_A_nosic"): "FFC end inside the J_PAN_A ZIF (intended)", ("DPS_riadenie", "ffc_B_nosic"): "FFC end inside the J_PAN_B ZIF (intended)"}
    for r in d["pairs"]:
        r["intended"] = intended.get((r["ram"], r["other"]))
    pen = [r for r in d["pairs"] if r["depth"] > 0.02]
    log(f"   {len(d['pairs'])} pairs; penetrating {len(pen)}")
    for r in pen[:20]:
        log("   ", r)
    OUT["X_summary"] = dict(n=len(d["pairs"]), penetrating=pen)
    verdict("X_cross_module_advisory", True, f"ADVISORY ({len(pen)} penetrating pairs vs the current OBAL / PAN STLs - see STATUS)")


def main(argv):
    global LOGF
    which = [a for a in argv if len(a) == 1] or list("ABCDEFGHSPX")
    LOGF = open(os.path.join(HERE, "ram_checks.log"), "w")
    t0 = time.time()
    parts = M.build()
    log(f"built {len(parts)} parts in {time.time() - t0:.1f} s")
    for k in which:
        t = time.time()
        globals()["check_" + k](parts)
        log(f"   ({k}: {time.time() - t:.1f} s)")
    OUT["fail"] = FAIL; OUT["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(OUT, open(os.path.join(HERE, "ram_checks.json"), "w"), indent=1, default=str)
    log("FAILED:", FAIL if FAIL else "none", f"| {time.time() - t0:.1f} s")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
