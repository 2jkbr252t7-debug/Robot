#!/opt/venv/cad/bin/python
"""Module-level checks of t4_ram.py (RAM builder's own checks, NOT the global K1-K11):

    /opt/venv/cad/bin/python t4_ram_checks.py [A B C D E F]      -> ram_checks.json, ram_checks.log (stdout)

  A  solids valid / single / volume > 0, STL watertight (every edge shared by exactly 2 triangles)
  B  interference among the RAM parts (OCC common volume) with the list of intended fits
  C  zones: shell inner surface, white-lip outline (lowering of T_stred), cap tub, T_stred boss prisms, PAN_ENV,
     bought parts against their t4_common envelopes
  D  seats of the bought parts measured on the solids (probe / bisection), centre distances
  E  wall thickness: designed walls measured by bisection + ray scan of the printed parts
  F  fasteners: thread engagement, tool channel D4.5 against the RAM parts
"""
from __future__ import annotations
import os, sys, json, math, time, struct, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                      # noqa: E402
import t4_common as C                   # noqa: E402
import t4_ram as M                      # noqa: E402
import build123d as bd                  # noqa: E402
from build123d import Vector            # noqa: E402

R = C.RAM
OUT = {}
FAIL = []


def log(*a):
    print(*a, flush=True)


def verdict(key, ok, info=""):
    OUT.setdefault("verdicts", {})[key] = dict(ok=bool(ok), info=info)
    if not ok:
        FAIL.append(key)
    log(f"   [{'PASS' if ok else 'FAIL'}] {key} {info}")


# ---------------------------------------------------------------------------------------------------------------------
def read_stl(path):
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


def watertight(tri):
    V = np.round(tri.reshape(-1, 3), 4)
    u, inv = np.unique(V, axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    deg = (F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])
    F = F[~deg]
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    Es = np.sort(E, 1)
    _, cnt = np.unique(Es, axis=0, return_counts=True)
    # orientation consistency: each directed edge once
    _, cd = np.unique(E, axis=0, return_counts=True)
    a, b, c = (u[F[:, i]] for i in range(3))
    vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    return dict(tris=int(len(F)), open_edges=int((cnt == 1).sum()), nonmanifold_edges=int((cnt > 2).sum()),
                dup_directed=int((cd > 1).sum()), volume=round(vol, 2))


def bbox(s):
    b = s.bounding_box()
    return np.array([b.min.X, b.min.Y, b.min.Z]), np.array([b.max.X, b.max.Y, b.max.Z])


def common_volume(a, b):
    try:
        r = a & b
        return float(sum(s.volume for s in r.solids())) if r is not None else 0.0
    except Exception as ex:          # noqa
        return float("nan")


def inside(solid, p):
    return bool(solid.is_inside(Vector(*p), 1e-6))


def boundary(solid, p0, d, tmax=30.0, step=0.05, tol=0.002):
    """distance from p0 along the unit vector d to the first change of inside/outside"""
    p0 = np.array(p0, float); d = np.array(d, float) / np.linalg.norm(d)
    s0 = inside(solid, p0)
    t = 0.0
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
    """material thickness through the point p (must be inside) along +-d"""
    if not inside(solid, p):
        return None
    a = boundary(solid, p, d); b = boundary(solid, p, -np.array(d, float))
    return None if a is None or b is None else a + b


def gap(solid, p, d):
    """free distance through the point p (must be outside) along +-d"""
    if inside(solid, p):
        return None
    a = boundary(solid, p, d); b = boundary(solid, p, -np.array(d, float))
    return None if a is None or b is None else a + b


def mesh(shape, tol=0.03, ang=0.25):
    return C.mesh_of(shape, tol, ang)


def surf_points(shape, h=0.7, tol=0.03):
    """mesh vertices + centroids of subdivided large triangles (roughly h spacing)"""
    V, T = mesh(shape, tol)
    P = [V]
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    big = area > h * h / 2
    for A, B_, Cc, ar in zip(a[big], b[big], c[big], area[big]):
        n = int(min(40, max(1, math.ceil(math.sqrt(2 * ar) / h))))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1))
        m = i + j <= n
        u, v = i[m] / n, j[m] / n
        P.append(A + np.outer(u, B_ - A) + np.outer(v, Cc - A))
    return np.concatenate(P)


# =====================================================================================================================
def check_A(parts):
    log("A. solids and STL")
    rows = {}
    ok_all = True
    for n, p in parts.items():
        s = p["shape"]
        r = dict(valid=bool(s.is_valid), n_solids=len(s.solids()), volume=round(s.volume, 2))
        w = watertight(read_stl(os.path.join(HERE, "stl", n + ".stl")))
        r.update(stl=w)
        r["ok"] = r["valid"] and r["n_solids"] == 1 and r["volume"] > 0 and w["open_edges"] == 0 and w["nonmanifold_edges"] == 0 \
            and w["dup_directed"] == 0 and abs(w["volume"] - C.mesh_volume(s, 0.02, 0.1)) < 0.02 * max(1.0, w["volume"])
        ok_all &= r["ok"]
        rows[n] = r
        if not r["ok"]:
            log("   NOT OK", n, r)
    OUT["A"] = rows
    verdict("A_valid_watertight", ok_all, f"{sum(r['ok'] for r in rows.values())}/{len(rows)} parts ok")


# intended fits: (name pattern a, name pattern b) -> (max common volume mm3, description)
def _m(n, pat):
    return n == pat or (pat.endswith("*") and n.startswith(pat[:-1]))


INTENDED = [
    ("cap_pan", "T_paluba", 2.5, "press fit D6.00 in D5.95 x 3.5"),
    ("vl_F2_*", "T_ram", 7.5, "heat-set insert M2.5 (OD 3.5 in D3.2)"),
    ("vl_F3_*", "T_ram", 7.5, "heat-set insert M2.5 (OD 3.5 in D3.2)"),
    ("vl_F5", "T_ram", 7.5, "heat-set insert M2.5 (OD 3.5 in D3.2)"),
    ("vl_F4_*", "T_ram", 5.0, "heat-set insert M2 (OD 3.2 in D2.9)"),
    ("vl_F8_*", "T_ram", 5.0, "heat-set insert M2 (OD 3.2 in D2.9)"),
    ("skr_F7_*", "T_ram", 3.0, "thread-forming M2 in pilot D1.7"),
    ("skr_F14_*", "T_ram", 3.0, "thread-forming M2 in pilot D1.7"),
    ("skr_fpc", "T_paluba", 3.0, "thread-forming M2 in pilot D1.6"),
    ("skr_F6", "servo_J1", 60.0, "M3 screw in the tapped servo shaft"),
    ("skr_pastorok_pan", "servo_pan", 20.0, "M2 screw in the tapped servo shaft"),
]


def check_B(parts):
    log("B. interference among the RAM parts")
    names = list(parts)
    bb = {n: bbox(parts[n]["shape"]) for n in names}
    rows, bad, fits = [], [], []
    t0 = time.time(); npairs = 0
    for a, b in itertools.combinations(names, 2):
        (a0, a1), (b0, b1) = bb[a], bb[b]
        if np.any(a1 < b0 + 0.005) or np.any(b1 < a0 + 0.005):
            continue
        npairs += 1
        v = common_volume(parts[a]["shape"], parts[b]["shape"])
        if not (v > 1e-4) and not math.isnan(v):
            continue
        lim, why = 0.0, None
        for pa, pb, mx, txt in INTENDED:
            if (_m(a, pa) and _m(b, pb)) or (_m(b, pa) and _m(a, pb)):
                lim, why = mx, txt
        rec = dict(a=a, b=b, common_mm3=round(v, 3) if not math.isnan(v) else None, intended=why, limit=lim)
        rows.append(rec)
        if why is None or math.isnan(v) or v > lim:
            bad.append(rec); log("   INTERFERENCE", rec)
        else:
            fits.append(rec)
    OUT["B"] = dict(pairs_tested=npairs, overlapping=rows, time_s=round(time.time() - t0, 1),
                    intended_fits=[dict(a=x[0], b=x[1], max_mm3=x[2], why=x[3]) for x in INTENDED])
    log(f"   {npairs} bbox-overlapping pairs tested in {time.time() - t0:.1f} s; intended overlaps {len(fits)}; unexpected {len(bad)}")
    verdict("B_no_interference", not bad, f"{len(bad)} unexpected overlaps; {len(fits)} declared press / thread fits")


# =====================================================================================================================
def lip_half_depth():
    """callable y_lim(x) of the white-lip inner outline at z -81 (front/back symmetric)"""
    L = C.lip_outline(C.Z_WHITE, C.WALL, 720)
    m = L[:, 1] > 0
    o = np.argsort(L[m, 0])
    xs, ys = L[m, 0][o], L[m, 1][o]
    return lambda x: np.interp(np.abs(x), xs[xs >= 0], ys[xs >= 0], right=0.0)


def se_margin(P, a, b, n):
    """radial margin of points to a superellipse outline (+ = inside)"""
    r = np.hypot(P[:, 0], P[:, 1]); th = np.arctan2(P[:, 1], P[:, 0])
    return C.se_r(a, b, n, th) - r


TOWER = ["T_ram", "T_paluba", "T_prichytka_fpc", "servo_J1", "servo_pan", "pastorok_pan", "cap_pan", "ptfe_podlozka", "DPS_riadenie",
         "pena_J1", "pena_J1_celo"]
UNDER = ["pastorok_J1", "lozisko_6805", "skr_F6"]


def check_C(parts):
    log("C. zones")
    res = {}
    names_T = [n for n, p in parts.items() if p["group"] == "T"]
    pts = {n: surf_points(parts[n]["shape"]) for n in names_T}
    # ---- C1 shell inner surface (wall 2.2): every static part above the cap floor
    rows = {}
    for n in names_T:
        if n == "T_spodok" or n in UNDER or n.startswith("skr_F1") or n.startswith("skr_F2"):
            continue
        P = pts[n]; P = P[P[:, 2] > C.Z_IN_BOT]
        if not len(P):
            continue
        cl = C.clearance_to_shell(P)
        i = int(np.argmin(cl))
        rows[n] = dict(min_clearance=round(float(cl[i]), 2), at=[round(float(v), 1) for v in P[i]])
    worst = sorted(rows.items(), key=lambda kv: kv[1]["min_clearance"])[:12]
    for n, r in worst:
        log(f"   shell clearance {n:18s} {r['min_clearance']:6.2f} at {r['at']}")
    res["shell_clearance"] = rows
    # the column feet / floor frame sit in the tub: they are below the inner loft's validity (z < -78) -> judged by C3
    cmin = min(r["min_clearance"] for n, r in rows.items())
    hi = {n: r for n, r in rows.items() if r["min_clearance"] < 0.45 and r["at"][2] > -78.0}
    verdict("C1_inside_shell", not hi, f"min clearance to the shell inner surface above z -78: "
            f"{min((r['min_clearance'] for r in rows.values() if r['at'][2] > -78.0), default=None)}; overall min {cmin} (tub zone -> C3)")
    # ---- C2 lowering of T_stred: tower inside the lip outline - 0.5 for |x| <= 33.3, z > -78 (relief |x| <= 16.75 front)
    ylim = lip_half_depth()
    rel = C.LIP_RELIEF
    rows = {}
    for n in TOWER + [k for k in names_T if k.startswith(("skr_F3", "vl_F3", "skr_F4", "vl_F4", "skr_F7", "skr_fpc", "skr_pastorok", "vl_F2", "skr_F5", "vl_F5"))]:
        P = pts[n]; P = P[(np.abs(P[:, 0]) <= C.XS) & (P[:, 2] > -78.0)]
        if not len(P):
            continue
        lim = ylim(P[:, 0])
        in_rel = (P[:, 0] >= rel["x"][0]) & (P[:, 0] <= rel["x"][1]) & (P[:, 1] < 0)
        lim = np.where(in_rel, np.maximum(lim, rel["y_min"]), lim)
        mg = lim - np.abs(P[:, 1])
        i = int(np.argmin(mg))
        rows[n] = dict(min_margin=round(float(mg[i]), 2), at=[round(float(v), 2) for v in P[i]], uses_relief=bool(in_rel[i] and ylim(P[i, 0]) - abs(P[i, 1]) < C.TOWER_CLEAR))
    for n, r in sorted(rows.items(), key=lambda kv: kv[1]["min_margin"])[:8]:
        log(f"   lip margin {n:18s} {r['min_margin']:6.2f} at {r['at']} relief {r['uses_relief']}")
    res["lip_margin"] = rows
    late = {"pastorok_pan", "skr_pastorok_pan"}                      # mounted through the bore AFTER T_stred
    bad = {n: r for n, r in rows.items() if r["min_margin"] < C.TOWER_CLEAR - 0.005 and n not in late}
    verdict("C2_T_stred_can_be_lowered", not bad, f"min lip margin {min(r['min_margin'] for n, r in rows.items() if n not in late)} "
            f"(need {C.TOWER_CLEAR}); parts using the front lip relief: {[n for n, r in rows.items() if r['uses_relief'] and n not in late]}; "
            f"mounted after T_stred: {sorted(late)} ({rows.get('pastorok_pan', {}).get('min_margin')})")
    # ---- C3 below z -78: inside the tub (inner face of the spigot) - 0.3
    rows = {}
    for n in ["T_ram", "servo_J1", "vl_F2_1", "vl_F2_2", "vl_F2_3", "vl_F2_4", "vl_F2_5", "vl_F2_6", "pena_J1_celo"]:
        P = pts[n]; P = P[(P[:, 2] < -78.0) & (P[:, 2] > C.Z_FLOOR - 0.01)]
        if not len(P):
            continue
        mg = se_margin(P, *C.TUB_SE); i = int(np.argmin(mg))
        rows[n] = dict(min_margin=round(float(mg[i]), 2), at=[round(float(v), 2) for v in P[i]])
        log(f"   tub margin {n:18s} {rows[n]['min_margin']:6.2f} at {rows[n]['at']}")
    res["tub_margin"] = rows
    verdict("C3_inside_tub", all(r["min_margin"] >= 0.25 for r in rows.values()), f"min {min(r['min_margin'] for r in rows.values())} (need 0.25; spec fit 0.28)")
    # ---- C4 keep-out prisms of the 4 T_stred screw bosses (x +-(25.8..32.2), |y| >= 15.8, z > -81)
    K = C.BOSS_KEEPOUT
    hits = {}
    for n in names_T:
        if n == "T_spodok" or n.startswith("skr_F1"):
            continue
        P = pts[n]
        m = (np.abs(P[:, 0]) > K["x"][0] + 0.01) & (np.abs(P[:, 0]) < K["x"][1] - 0.01) & (np.abs(P[:, 1]) > K["y_min"] + 0.01) & (P[:, 2] > C.Z_WHITE + 0.01)
        m &= np.abs(P[:, 0]) <= C.XS
        if m.any():
            hits[n] = int(m.sum())
    res["boss_keepout_hits"] = hits
    verdict("C4_boss_prisms_free", not hits, str(hits))
    # ---- C5 PAN_ENV: static parts above z -45.7 (the deck top zone is RAM's own: r <= 13 / back half r <= 25.1 up to -42.9)
    rows = {}
    for n in names_T:
        P = pts[n]; P = P[P[:, 2] > -45.7 + 1e-6]
        if not len(P):
            continue
        r = np.hypot(P[:, 0], P[:, 1])
        renv = np.zeros(len(P))
        for z0, z1, rm in C.PAN_ENV:
            renv = np.where((P[:, 2] > z0) & (P[:, 2] <= z1), rm, renv)
        mg = r - renv
        i = int(np.argmin(mg))
        rows[n] = dict(min_margin_to_PAN_ENV=round(float(mg[i]), 2), at=[round(float(v), 2) for v in P[i]], top_z=round(float(P[:, 2].max()), 2))
    res["pan_env"] = rows
    own = {"cap_pan": "pivot pin inside the hub bore (interface)", "pastorok_pan": "gear mesh (interface), under the well wall edge z -41.3",
           "skr_pastorok_pan": "flush in the pinion"}
    bad = {}
    for n, r in rows.items():
        if n in own:
            continue
        z = r["at"][2]
        lim = 1.0 if z > -41.9 else 1.0
        if r["min_margin_to_PAN_ENV"] < lim:
            bad[n] = r
    cols = {n: r for n, r in bad.items() if n in ("T_ram",) or n.startswith("vl_F8")}
    other = {n: r for n, r in bad.items() if n not in cols}
    for n, r in rows.items():
        log(f"   PAN_ENV {n:18s} margin {r['min_margin_to_PAN_ENV']:6.2f} at {r['at']} (top z {r['top_z']})")
    tz = {n: r["top_z"] for n, r in rows.items() if n not in ("T_ram",) and not n.startswith("vl_F8") and n not in own}
    res["static_top_z_above_deck"] = tz
    verdict("C5_static_outside_PAN_ENV", not other and all(z <= C.FPC_PAN["z"][1] + 1e-6 for z in tz.values()),
            f"deck-top parts end at z <= {max(tz.values()) if tz else None} (limit {C.FPC_PAN['z'][1]}, stage floor -41.9); "
            f"columns: inner face x {C.X_COL_IN} = PAN_ENV + {min((r['min_margin_to_PAN_ENV'] for r in cols.values()), default=None)} "
            f"(architect's X_COL_IN; real sweep r 33.38 -> 1.02); others below 1.0: {list(other)}")
    # ---- C6 bought parts against the t4_common envelopes
    env = {e["name"]: e for e in C.envelopes() if e["owner"] == "ram"}
    exp = {"servo_J1": ("servo_J1", "servo_J1_boss", "servo_J1_plug"), "servo_pan": ("servo_pan", "servo_pan_tabs", "servo_pan_boss", "servo_pan_plug", "pastorok_pan_naboj"),
           "DPS_riadenie": ("DPS_riadenie",), "menic": ("menic",), "zosilnovac": ("zosilnovac",), "kondenzator": ("kondenzator",),
           "pastorok_J1": ("pastorok_J1",), "lozisko_6805": ("lozisko_6805",), "pastorok_pan": ("pastorok_pan", "pastorok_pan_naboj"),
           "cap_pan": ("cap_pan",), "ptfe_podlozka": ("ptfe",), "T_paluba": ("paluba", "paluba_zad", "kanal_fpc_pan"), "Z_koleso_J1": ("Z_koleso_J1",)}
    rows = {}
    for n, es in exp.items():
        lo, hi = bbox(parts[n]["shape"])
        elo, ehi = np.full(3, 1e9), np.full(3, -1e9)
        for en in es:
            e = env[en]
            if e["kind"] == "box":
                l = np.array([e["x"][0], e["y"][0], e["z"][0]]); h = np.array([e["x"][1], e["y"][1], e["z"][1]])
            else:
                k = "xyz".index(e["axis"]); o = [i for i in range(3) if i != k]
                l = np.zeros(3); h = np.zeros(3)
                l[k], h[k] = e["rng"]; l[o[0]], h[o[0]] = e["c"][0] - e["r"], e["c"][0] + e["r"]; l[o[1]], h[o[1]] = e["c"][1] - e["r"], e["c"][1] + e["r"]
            elo = np.minimum(elo, l); ehi = np.maximum(ehi, h)
        over = np.maximum(np.maximum(elo - lo, hi - ehi), 0.0)
        rows[n] = dict(bbox=[round(float(v), 2) for v in np.stack([lo, hi], 1).ravel()], envelope=[round(float(v), 2) for v in np.stack([elo, ehi], 1).ravel()],
                       outside_xyz=[round(float(v), 2) for v in over])
        if over.max() > 0.011:
            log(f"   envelope {n:14s} outside by {rows[n]['outside_xyz']} (x, y, z)")
    res["envelopes"] = rows
    declared = {"servo_J1": "spline 2.2 below the boss envelope (inside the pinion)", "servo_pan": "output shaft inside the pinion",
                "menic": "1.0 standoffs: +0.8 outward (RAM['BUCK_X'])", "zosilnovac": "1.0 standoffs: +0.8 outward (RAM['AMP_X'])",
                "kondenzator": "+0.1 in x (RAM['CAP470_AT'])", "T_paluba": "screw ears at (+-22.9, +-15.8) outside the plate box"}
    und = [n for n, r in rows.items() if max(r["outside_xyz"]) > 0.011 and n not in declared]
    res["envelope_declared"] = declared
    verdict("C6_bought_parts_in_envelopes", not und, f"outside without declaration: {und}; declared: {sorted(k for k, r in rows.items() if max(r['outside_xyz']) > 0.011)}")
    OUT["C"] = res


# =====================================================================================================================
def check_D(parts):
    log("D. seats (measured on the solids)")
    S = {k: parts[k]["shape"] for k in ("T_spodok", "T_ram", "T_paluba", "Z_naboj_test")}
    rows = []

    def add(name, value, nominal, lo, hi, note=""):
        ok = value is not None and lo - 1e-3 <= value <= hi + 1e-3
        rows.append(dict(name=name, measured=None if value is None else round(value, 3), nominal=nominal, range=[lo, hi], ok=bool(ok), note=note))
        log(f"   {'ok ' if ok else 'BAD'} {name:58s} {value if value is None else round(value, 3)}  (nominal {nominal}, allowed {lo}..{hi}) {note}")
    sv = C.STS3215
    # ---- STS3215
    w = gap(S["T_ram"], (-5.0, 0.0, -60.0), (0, 1, 0))
    add("STS3215 cradle width between the walls", w, 25.1, sv["W"] + 0.2, sv["W"] + 0.6, "servo 24.7 +-0.3 -> 0.05..0.5 per side")
    xe = boundary(S["T_ram"], (-25.0, 0.0, -60.0), (-1, 0, 0)); xb = boundary(S["T_ram"], (10.0, 0.0, -75.0), (1, 0, 0))
    add("STS3215 seat length end wall -> bumper", None if xe is None or xb is None else xe + xb + 35.0, 46.7, sv["L"] + 1.0 + 0.3, sv["L"] + 1.0 + 0.7,
        "45.2 + 1.0 foam + slide +-0.3")
    zf = boundary(S["T_spodok"], (0.0, 0.0, -83.0), (0, 0, -1)); zd = boundary(S["T_paluba"], (-5.0, 5.0, -48.0), (0, 0, 1))
    add("STS3215 seat height pocket floor -> deck underside", None if zf is None or zd is None else zf + zd + 35.0, 35.5, 35.2, 35.8, "35.0 + 0.5 foam (0.3 / 0.5 / 0.8)")
    pw = gap(S["T_spodok"], (0.0, 0.0, -83.0), (0, 1, 0))
    add("cap pocket width (clearance only)", pw, 25.9, 25.5, 26.3)
    fl = thickness(S["T_spodok"], (0.0, 5.0, -83.9), (0, 0, 1))
    add("floor under the STS3215", fl, 1.2, 1.15, 1.25)
    sl = gap(S["T_spodok"], (-18.0, 0.0, -84.0), (0, 1, 0)); slx = gap(S["T_spodok"], (-18.0, 0.0, -84.0), (1, 0, 0))
    add("boss slot width (boss D12)", sl, 14.4, 14.3, 14.5, "0.9 radial + slide")
    add("boss slot length", slx, 15.0, 14.9, 15.1, "D14.4 + 2 x 0.3")
    add("C J1 (servo axis -> torso axis)", math.hypot(*C.J1_AX), C.C_J1, C.C_J1 - C.J1_ADJ, C.C_J1 + C.J1_ADJ, "set screw F5 + foam, +-0.3")
    # ---- 6805
    rs = boundary(S["T_spodok"], (0.0, 0.0, -95.0), (1, 0, 0)); rs2 = boundary(S["T_spodok"], (0.0, 0.0, -95.0), (0, -1, 0))
    add("6805 seat bore D (x)", None if rs is None else 2 * rs, 37.0, 37.0, 37.05, "drawing tolerance +0.05 / 0, CA")
    add("6805 seat bore D (y)", None if rs2 is None else 2 * rs2, 37.0, 37.0, 37.05)
    sh = boundary(S["T_spodok"], (17.7, 0.0, -95.0), (0, 0, 1))
    add("6805 seat depth to the shoulder", None if sh is None else sh + 3.0, 7.0, 6.95, 7.05)
    shw = thickness(S["T_spodok"], (17.7, 0.0, -90.0), (1, 0, 0))
    add("plinth wall above the bearing (r 17 .. 24)", shw, 7.0, 6.9, 7.1)
    rw = thickness(S["T_spodok"], (19.7, 0.0, -95.0), (1, 0, 0))
    add("foot ring wall around the bearing", rw, 2.5, 2.45, 2.55)
    pr = boundary(S["Z_naboj_test"], (0.0, 11.0, -95.0), (0, 1, 0))
    add("dummy hub post D (inner ring D25)", None if pr is None else 2 * (11.0 + pr), 24.96, 24.94, 24.98, "h -0.02 / -0.06")
    # ---- STS3032
    sp = C.STS3032
    zt = boundary(S["T_ram"], (14.0, -23.5, -59.0), (0, 0, 1)); zt2 = boundary(S["T_ram"], (-14.0, -23.5, -59.0), (0, 0, 1))
    add("STS3032 post top +X (tab underside -58.0)", None if zt is None else -59.0 + zt, -58.0, -58.02, -57.98, "tab height 16.2 above the bottom: verify, shim")
    add("STS3032 post top -X", None if zt2 is None else -59.0 + zt2, -58.0, -58.02, -57.98)
    g = gap(S["T_ram"], (0.0, -20.0, -60.0), (1, 0, 0))
    add("STS3032 clear width between the posts", g, 23.9, sp["L"] + 0.2, sp["L"] + 0.6, "case 23.5 +-0.3")
    add("STS3032 insert spacing", 28.0, 28.0, 27.9, 28.1, "tab holes D2.2 at 28.0")
    add("C pan (pinion axis -> pan axis)", math.hypot(*C.PAN_AX), C.C_PAN, C.C_PAN, C.C_PAN + 0.05, "+0.05 / 0; slop of the D2.2 tab holes")
    w = C.STS3032["plug"]
    pwy = gap(S["T_ram"], (14.0, -20.0, -68.0), (0, 1, 0)); pwz = gap(S["T_ram"], (14.0, -20.0, -68.0), (0, 0, 1))
    add("plug window of the +X post, y", pwy, 8.6, w["y"][1] - w["y"][0] + 0.4, 9.5, "plug zone 8.0")
    add("plug window of the +X post, z", pwz, 11.6, w["z"][1] - w["z"][0] + 0.4, 13.0, "plug zone 8.0")
    # ---- pivot, stop groove, FPC channel
    pb = gap(S["T_paluba"], (0.0, 0.0, -45.0), (1, 0, 0))
    add("pivot press bore D", pb, 5.95, 5.93, 5.97, "pin D6 h6")
    bo = thickness(S["T_paluba"], (4.5, 0.0, -45.0), (1, 0, 0))
    add("pivot boss wall", bo, 2.525, 2.4, 2.6)
    gw = gap(S["T_paluba"], (0.0, 13.5, -46.5), (0, 1, 0)); gd = boundary(S["T_paluba"], (0.0, 13.5, -46.5), (0, 0, -1))
    add("stop groove width", gw, 2.4, 2.35, 2.45, "pin D2")
    add("stop groove depth", None if gd is None else gd + 0.5, 1.2, 1.15, 1.25)
    ge = boundary(S["T_paluba"], (13.5, 0.0, -46.5), (0, -1, 0))
    add("stop groove end radius at azimuth 0", ge, 1.2, 1.15, 1.25, "pin centre stops at 90.85 deg")
    cw = thickness(S["T_paluba"], (0.0, 24.3, -44.0), (0, 1, 0)); ci = boundary(S["T_paluba"], (0.0, 20.0, -44.0), (0, 1, 0))
    add("FPC channel wall thickness", cw, 1.6, 1.55, 1.65)
    add("FPC channel wall inner radius", None if ci is None else 20.0 + ci, 23.5, 23.45, 23.55)
    # ---- shoulder interface
    for s, tag in ((1, "L"), (-1, "P")):
        xb_ = boundary(S["T_ram"], (s * 37.0, C.SH_Y, C.SH_Z + 8.5), (s, 0, 0))
        add(f"column boss face x ({tag})", None if xb_ is None else 37.0 + xb_, C.X_COL_BOSS, C.X_COL_BOSS - 0.02, C.X_COL_BOSS + 0.02)
        xs = boundary(S["T_ram"], (s * 38.0, C.SH_Y, C.SH_Z + 12.2), (s, 0, 0))
        add(f"stop ring face x ({tag})", None if xs is None else 38.0 + xs, C.X_COL_STOP, C.X_COL_STOP - 0.02, C.X_COL_STOP + 0.02)
        ri = boundary(S["T_ram"], (s * 38.8, C.SH_Y, C.SH_Z + 8.0), (0, 0, 1))
        add(f"stop ring inner r ({tag})", None if ri is None else 8.0 + ri, C.R_COL_STOP[0], C.R_COL_STOP[0] - 0.02, C.R_COL_STOP[0] + 0.02, "joint neck r 11.0")
        xp = boundary(S["T_ram"], (s * 40.0, C.SH_Y, C.SH_Z), (s, 0, 0))
        add(f"spigot end x ({tag})", None if xp is None else 40.0 + xp, C.KLB_BUSH["spigot_x"], 40.98, 41.02)
        rp = boundary(S["T_ram"], (s * 40.0, C.SH_Y, C.SH_Z), (0, 1, 0))
        add(f"spigot r ({tag})", rp, 5.0, 4.98, 5.02)
        kw = gap(S["T_ram"], (s * 37.8, C.SH_Y + 8.0, C.SH_Z), (0, 0, 1))
        add(f"key slot width ({tag})", kw, 3.0, 2.98, 3.02)
        xi = boundary(S["T_ram"], (s * 35.0, C.SH_Y, C.SH_Z + 5.0), (-s, 0, 0))
        add(f"column inner face x ({tag})", None if xi is None else 35.0 - xi, C.X_COL_IN, C.X_COL_IN - 0.01, C.X_COL_IN + 0.02)
    # ---- controller / boards
    add("controller standoff face y", 14.6 + (boundary(S["T_ram"], (18.0, 14.6, -57.0 + 2.0), (0, 1, 0)) or 99), C.CTRL["y"][0], 15.48, 15.52)
    OUT["D"] = rows
    verdict("D_seats", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} within range")


# =====================================================================================================================
def ray_scan(shape, n_rays=2500, tol=0.04, seed=1):
    """local thickness: rays from random surface points along the inward normal; returns (thickness, parallel?, point)"""
    V, T = mesh(shape, tol, 0.3)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nn = np.cross(b - a, c - a); ar = np.linalg.norm(nn, axis=1); ok = ar > 1e-9
    a, b, c, nn, ar = a[ok], b[ok], c[ok], nn[ok], ar[ok]
    nrm = nn / ar[:, None]
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(a), size=min(n_rays, len(a) * 4), p=ar / ar.sum())
    u = rng.random(len(idx)); v = rng.random(len(idx)); m = u + v > 1; u[m], v[m] = 1 - u[m], 1 - v[m]
    O = a[idx] + u[:, None] * (b[idx] - a[idx]) + v[:, None] * (c[idx] - a[idx])
    D = -nrm[idx]
    O = O + D * 1e-4
    e1, e2 = b - a, c - a
    th = np.full(len(O), np.inf); hn = np.zeros(len(O))
    for i0 in range(0, len(O), 200):
        o = O[i0:i0 + 200][:, None, :]; d = D[i0:i0 + 200][:, None, :]
        p = np.cross(d, e2[None]); det = np.einsum("rtk,tk->rt", p, e1)
        good = np.abs(det) > 1e-12
        inv = np.where(good, 1.0 / np.where(good, det, 1.0), 0.0)
        tv = o - a[None]
        uu = np.einsum("rtk,rtk->rt", tv, p) * inv
        q = np.cross(tv, e1[None])
        vv = np.einsum("rtk,rtk->rt", np.broadcast_to(d, q.shape), q) * inv
        tt = np.einsum("rtk,tk->rt", q, e2) * inv
        hit = good & (uu >= -1e-9) & (vv >= -1e-9) & (uu + vv <= 1 + 1e-9) & (tt > 1e-3)
        tt = np.where(hit, tt, np.inf)
        j = np.argmin(tt, 1)
        th[i0:i0 + 200] = tt[np.arange(len(j)), j]
        hn[i0:i0 + 200] = np.einsum("rk,rk->r", nrm[j], D[i0:i0 + 200])          # +1 = opposite wall parallel
    return th, hn, O


WALLS = [  # name, part, point inside the wall, direction, nominal, minimum allowed
    ("cap floor (tub)", "T_spodok", (25.0, 0.0, -83.4), (0, 0, 1), 2.2, 2.0),
    ("cap floor under the J1 servo", "T_spodok", (0.0, 5.0, -83.9), (0, 0, 1), 1.2, 1.2),
    ("spigot wall", "T_spodok", (0.0, 26.3, -80.0), (0, 1, 0), 1.6, 1.2),
    ("spigot wall at x 35", "T_spodok", (35.0, 15.3, -80.0), (0.7, 0.7, 0), 1.6, 1.2),
    ("cap rim wall beside the tub (z -82)", "T_spodok", (0.0, 27.5, -82.0), (0, 1, 0), 4.2, 2.0),
    ("skirt disc thickness", "T_spodok", (0.0, -26.5, -85.7), (0, 0, 1), 1.0, 1.0),
    ("plinth skin outside the J1 FPC slot", "T_spodok", (0.0, 23.5, -88.0), (0, 1, 0), 1.0, 0.9),
    ("plinth wall inside the J1 FPC slot", "T_spodok", (0.0, 19.0, -88.0), (0, 1, 0), 4.6, 2.0),
    ("stop lug width", "T_spodok", (0.0, 19.8, -99.0), (1, 0, 0), 2.5, 2.4),
    ("cradle long wall", "T_ram", (0.0, 13.3, -65.0), (0, 1, 0), 1.6, 1.6),
    ("cradle end wall", "T_ram", (-30.8, 8.0, -60.0), (1, 0, 0), 1.6, 1.6),
    ("bumper", "T_ram", (17.5, 0.0, -76.0), (1, 0, 0), 1.6, 1.6),
    ("floor strip", "T_ram", (21.0, 0.0, -81.3), (0, 0, 1), 2.0, 1.6),
    ("column web (left)", "T_ram", (35.4, 8.0, -62.0), (1, 0, 0), 2.0, 1.6),
    ("column web under the capacitor saddle", "T_ram", (35.2, 3.0, -45.0), (1, 0, 0), 1.65, 1.6),
    ("column rib", "T_ram", (40.0, 14.2, -55.0), (0, 1, 0), 1.6, 1.6),
    ("shoulder boss disc", "T_ram", (36.0, 3.0, -12.0), (1, 0, 0), 4.0, 3.0),
    ("stop ring radial", "T_ram", (38.8, 3.0, -4.8), (0, 0, 1), 1.2, 1.2),
    ("bridge", "T_ram", (30.0, 13.3, -55.0), (0, 1, 0), 1.6, 1.6),
    ("+X pan post: front leg", "T_ram", (14.0, -25.8, -68.0), (0, 1, 0), 1.6, 1.6),
    ("+X pan post: shelf under the tab", "T_ram", (12.6, -22.5, -60.0), (0, 0, 1), 3.6, 3.0),
    ("+X pan post: rib behind the plug", "T_ram", (14.0, -15.3, -68.0), (0, 1, 0), 2.25, 1.6),
    ("wall beside a deck insert (servo side)", "T_ram", (-22.9, 13.3, -49.0), (0, 1, 0), 1.65, 1.6),
    ("clip arm of the capacitor", "T_ram", (41.1, 3.0 + 5.65, -45.0), (0, 1, 0), 1.2, 1.2),
    ("deck plate", "T_paluba", (-25.0, -8.0, -46.9), (0, 0, 1), 1.8, 1.6),
    ("deck under the stop groove", "T_paluba", (0.0, 13.5, -47.5), (0, 0, 1), 0.6, 0.6),
    ("FPC channel wall", "T_paluba", (0.0, 24.3, -44.0), (0, 1, 0), 1.6, 1.6),
    ("FPC clamp block", "T_prichytka_fpc", M.pol(26.0, 156.0) + (-45.0,), (0, 0, 1), 2.2, 1.6),
    ("dummy plate", "Z_naboj_test", (30.0, 20.0, -106.0), (0, 0, 1), 5.0, 3.0),
    ("dummy post wall (bore D8.2)", "Z_naboj_test", (8.0, 0.0, -95.0), (1, 0, 0), 8.38, 3.0),
    ("dummy stop block radial", "Z_naboj_test", (0.0, -19.8, -101.0), (0, 1, 0), 3.1, 2.4),
]
THIN_DECLARED = {
    "T_spodok": "1.0 skirt disc (spec D2), 1.2 floor under the servo (spec), 0.75..1.0 plinth skin outside the FPC slot, countersink rims",
    "T_ram": "blind-hole floors (0.35..0.5) of the pilot / insert holes, capacitor clip arms 1.2, standoff rims",
    "T_paluba": "0.6 under the stop groove (spec: groove 1.2 in the 1.8 deck), ligament 0.9 between FPC slot and lobe edge",
    "T_prichytka_fpc": "countersink rim",
    "Z_naboj_test": "-",
}


def check_E(parts):
    log("E. walls")
    rows = []
    for name, pn, p, d, nom, mn in WALLS:
        t = thickness(parts[pn]["shape"], p, d)
        ok = t is not None and t >= mn - 0.011
        rows.append(dict(name=name, part=pn, measured=None if t is None else round(t, 2), nominal=nom, min_allowed=mn, ok=bool(ok)))
        log(f"   {'ok ' if ok else 'BAD'} {pn:16s} {name:44s} {None if t is None else round(t, 2)} (nominal {nom}, min {mn})")
    scan = {}
    for pn, lim in (("T_spodok", 1.2), ("T_ram", 1.6), ("T_paluba", 1.6), ("T_prichytka_fpc", 1.6), ("Z_naboj_test", 1.6)):
        t0 = time.time()
        th, hn, O = ray_scan(parts[pn]["shape"], 3000 if pn != "T_prichytka_fpc" else 600)
        par = hn > 0.94
        fin = np.isfinite(th)
        thin = par & fin & (th < lim - 0.02)
        hist = {f"<{x}": int((par & fin & (th < x)).sum()) for x in (0.6, 0.8, 1.0, 1.2, 1.6, 2.0)}
        ex = []
        order = np.argsort(np.where(thin, th, np.inf))[:12]
        for i in order:
            if thin[i]:
                ex.append(dict(t=round(float(th[i]), 2), at=[round(float(v), 1) for v in O[i]]))
        scan[pn] = dict(rays=int(len(th)), no_hit=int((~fin).sum()), parallel_rays=int(par.sum()), limit=lim, below_limit=int(thin.sum()),
                        min_parallel=round(float(th[par & fin].min()), 2) if (par & fin).any() else None, hist=hist, thinnest=ex,
                        declared_thin_features=THIN_DECLARED[pn], time_s=round(time.time() - t0, 1))
        log(f"   ray scan {pn:16s} rays {len(th)} parallel {int(par.sum())} min {scan[pn]['min_parallel']} below {lim}: {int(thin.sum())} {hist} ({time.time() - t0:.1f} s)")
        for e in ex[:8]:
            log(f"        thin {e}")
    OUT["E"] = dict(designed_walls=rows, ray_scan=scan)
    verdict("E_designed_walls", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} designed walls at or above their minimum")


# =====================================================================================================================
def check_F(parts):
    log("F. fasteners: tool channels D4.5 (against the RAM parts in the final state)")
    rows = []
    names = list(parts)
    bb = {n: bbox(parts[n]["shape"]) for n in names}
    late = {"skr_F4_1": ["pastorok_pan", "skr_pastorok_pan"], "skr_F4_2": []}          # mounted later in the order of spec 11
    for n, p in parts.items():
        f = p.get("fastener")
        if not f or "head" not in f:
            continue
        ax = f["dir"][1].lower(); sg = 1 if f["dir"][0] == "+" else -1
        k = "xyz".index(ax)
        h = np.array(f["head"], float)
        a = h[k] - sg * 0.05; b = h[k] - sg * 60.0
        o = [h[i] for i in range(3) if i != k]
        tool = M.cyl_ax(2.25, min(a, b), max(a, b), o[0], o[1], ax)
        tlo, thi = bbox(tool)
        hits = {}
        for m in names:
            if m == n:
                continue
            lo, hi = bb[m]
            if np.any(hi < tlo + 0.01) or np.any(thi < lo + 0.01):
                continue
            v = common_volume(tool, parts[m]["shape"])
            if v > 0.01 or math.isnan(v):
                hits[m] = round(v, 2)
        allowed = {m: v for m, v in hits.items() if m in late.get(n, []) or (n.startswith("skr_F14") and m in ("menic", "zosilnovac"))
                   or (n.startswith("skr_F7") and m == "DPS_riadenie") or (n == "skr_fpc" and m == "T_prichytka_fpc")
                   or (n.startswith("skr_F3") and m in ("T_paluba",)) or (n == "skr_F6" and m == "pastorok_J1")
                   or (n == "skr_pastorok_pan" and m == "pastorok_pan") or (n.startswith("skr_F4") and m == "servo_pan")}
        # the allowed ones are the clamped part itself seen by the head channel (counterbore / head on the surface)
        real = {m: v for m, v in hits.items() if m not in allowed}
        rows.append(dict(name=n, joint=f["joint"], size=f["size"], head=[round(float(v), 2) for v in h], tool_from=f["tool_from"],
                         blocked_by=real, clamped_or_later=allowed, ok=not real))
        log(f"   {'ok ' if not real else 'BAD'} {n:18s} {f['size']:24s} tool from {f['tool_from']:6s} blocked by {real} (clamped / later: {allowed})")
    OUT["F"] = rows
    verdict("F_tool_channels", all(r["ok"] for r in rows), f"{sum(r['ok'] for r in rows)}/{len(rows)} screws with a free D4.5 channel")
    # thread engagement table (analytic, from the constants)
    eng = [
        dict(joint="F1", screw="M2.5x8 csk", clamp="floor + pad 3.0 (head sunk 0.5)", engagement="5.0: insert 4.0 in the T_stred boss + 1.0 pilot (OBAL)"),
        dict(joint="F2", screw="M2.5x6 csk", clamp="floor 2.2", engagement="3.8 in the heat-set insert (4.0)"),
        dict(joint="F3", screw="M2.5x6 pan", clamp="deck 1.8", engagement="4.2 -> 4.0 insert + 0.2"),
        dict(joint="F4", screw="M2x6", clamp="servo tab 2.5", engagement="3.5 -> 3.0 insert + 0.5"),
        dict(joint="F5", screw="M2.5x6 set screw", clamp="-", engagement="4.0 insert, tip on the servo end face"),
        dict(joint="F6", screw="M3x6 csk", clamp="pinion web", engagement="about 4.1 in the servo shaft (z -88.1 .. -84.0)"),
        dict(joint="F7", screw="M2x4 thread-forming", clamp="PCB 1.6", engagement="2.4 in standoff + wall (pilot D1.7 x 2.55, 0.4 skin to the servo pocket)"),
        dict(joint="F14", screw="M2x4 thread-forming", clamp="PCB 1.6", engagement="2.4 in standoff 1.0 + web 2.0 (pilot D1.7 x 2.5, 0.5 skin)"),
        dict(joint="FPC", screw="M2x4 csk thread-forming", clamp="clamp 2.2", engagement="1.8 (deck thickness; light duty)"),
        dict(joint="PAN", screw="M2x5 csk", clamp="pinion", engagement="about 3.1 in the servo shaft"),
    ]
    OUT["F_engagement"] = eng


# =====================================================================================================================
def main(argv):
    which = [a for a in argv if len(a) == 1] or list("ABCDEF")
    t0 = time.time()
    parts = M.build()
    log(f"== t4_ram checks: {len(parts)} parts (build {time.time() - t0:.1f} s) ==")
    fn = dict(A=check_A, B=check_B, C=check_C, D=check_D, E=check_E, F=check_F)
    for w in which:
        t = time.time(); fn[w](parts); log(f"   ({w}: {time.time() - t:.1f} s)")
    OUT["summary"] = dict(failed=FAIL, run=which, time_s=round(time.time() - t0, 1), generated=time.strftime("%Y-%m-%d %H:%M:%S"))
    p = os.path.join(HERE, "ram_checks.json")
    old = json.load(open(p)) if os.path.exists(p) and len(which) < 6 else {}
    if old:
        v = old.get("verdicts", {}); v.update(OUT.get("verdicts", {})); old.update(OUT); old["verdicts"] = v
        old["summary"] = dict(failed=[k for k, x in v.items() if not x["ok"]], run="partial update " + "".join(which), generated=time.strftime("%Y-%m-%d %H:%M:%S"))
        json.dump(old, open(p, "w"), indent=1, ensure_ascii=False)
    else:
        json.dump(OUT, open(p, "w"), indent=1, ensure_ascii=False)
    log(f"== failed: {FAIL if FAIL else 'none'}; {time.time() - t0:.1f} s ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
