"""f2 Kapsula - fit + sweep checks of the real exterior shells against the final packaging (T1/pack/layout.json).
Run: /opt/venv/cad/bin/python check_fit.py [static|sweep|arms|head|all]   -> check.json (merged per section)
  static : every internal part (rest pose) vs every f2 exterior part: intersection volume, containment in the outer
           solid, min distance (clearance); expected contacts listed with a reason.
  sweep  : t1lib sweep(STD_POSES + pack extra poses) with the f2 shells as custom components (moving pairs only)
  arms   : arm <-> torso gap over the arm range (-45..135), arm <-> base gap over J1 +-150, arm <-> arm, jewel ring /
           torso <-> base over J1; arm-head limit table (t1lib head envelopes, as pack/arm_limits.py)
  head   : real B head STL point cloud over the B tilt-vs-lift table x pan -85..85 vs the f2 torso top (analytic)"""
import sys, os, json, time, math
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t1lib as T
import exterior as E
from build123d import Shape as _Shape, Compound as _Compound

_and0 = _Shape.__and__


def _and_safe(self, other):
    """build123d 0.13 returns None for an empty intersection of imported solids -> t1lib reported it as a clash"""
    r = _and0(self, other)
    return r if r is not None else _Compound([])


_Shape.__and__ = _and_safe
import shape as S

OUT = os.path.dirname(os.path.abspath(__file__))
PACK = "/tmp/claude-0/gapwf/fin/T1/pack/layout.json"
REPLACED = {"T_shell", "Z_shell", "A_R_ruka", "A_L_ruka", "A_R_kryt", "A_L_kryt", "T_J1_sukna"}

# expected contacts: (internal part, f2 part) -> reason
BONDED = {
    ("T_svetlo", "T_svetlovod"): "LED strip lies on the back of the PMMA light guide",
    ("T_svetlo", "T_trup_predny"): "LED strip carrier clipped into the front panel behind the slot",
    ("A_L_servo", "A_L_vonkajsia"): "servo case bonded to the outer wall (pack)",
    ("A_R_servo", "A_R_vonkajsia"): "servo case bonded to the outer wall (pack)",
    ("A_L_servo", "A_L_vnutorna"): "servo flush in the inner-skin window",
    ("A_R_servo", "A_R_vnutorna"): "servo flush in the inner-skin window",
    ("Z_USB_C", "Z_skrupina"): "receptacle in the back-wall opening",
    ("Z_vypinac", "Z_skrupina"): "switch in the back-wall opening",
    ("Z_ToF", "Z_okno_ToF"): "sensor behind its window",
    ("Z_ToF", "Z_skrupina"): "sensor bracket on the front wall",
    ("Z_svetlo", "Z_svetlovod"): "LED strip behind the base light guide",
    ("Z_svetlo", "Z_skrupina"): "LED strip carrier on the front wall",
    ("T_J1_noha", "T_sokel"): "jewel ring is bonded on the rotating J1 foot ring (same group T)",
    ("T_reproduktor", "T_trup_predny"): "speaker screwed to the front panel behind the grille (pack: shell-mounted)",
    ("T_reproduktor", "T_mriezka"): "speaker behind its grille",
    ("A_L_servo", "A_L_kryt"): "cap glued on the servo face / spline boss through the cap",
    ("A_R_servo", "A_R_kryt"): "cap glued on the servo face / spline boss through the cap",
    ("T_STS3215", "T_trup_predny"): "servo cradle stands on the torso floor (0.5 mm shim)",
    ("T_STS3215", "T_trup_zadny"): "servo cradle stands on the torso floor (0.5 mm shim)",
    ("T_J1_noha", "T_trup_predny"): "rotating J1 foot ring is screwed to the torso floor",
    ("T_J1_noha", "T_trup_zadny"): "rotating J1 foot ring is screwed to the torso floor",
    ("T_stlpik_L", "T_trup_zadny"): "side column screwed to the shell (pack: shell-mounted)",
    ("T_stlpik_R", "T_trup_zadny"): "side column screwed to the shell (pack: shell-mounted)",
    ("T_stlpik_L", "T_trup_predny"): "side column touches the front panel at the parting line",
    ("T_stlpik_R", "T_trup_predny"): "side column touches the front panel at the parting line",
    ("Z_J1_kanal", "Z_skrupina"): "J1 cable channel hangs from the base top skin (pack: skin = channel lid)",
    ("Z_kolieska_P", "Z_kryt_bat_P"): "ball caster screwed into its battery-bay cover (pack)",
    ("Z_kolieska_Z", "Z_kryt_bat_Z"): "ball caster screwed into its battery-bay cover (pack)",
    ("T_horny_kruh", "T_trup_zadny"): "journal ring attached to the shell (pack: shell-mounted)",
    ("T_horny_kruh", "T_trup_predny"): "journal ring attached to the shell (pack: shell-mounted)",
}


def fdist(a, b):
    """boundary-to-boundary distance (solid.distance_to can return 0 when OCC's classifier misjudges a point on a
    coplanar loft region); overlap is detected separately by boolean volume"""
    from build123d import Compound
    return Compound(a.faces()).distance_to(Compound(b.faces()))


def gaps(L, pose, A_, B_):
    best = (1e9, None, None)
    for a in A_:
        sa = L.shape(a, pose)
        for b in B_:
            sb = L.shape(b, pose)
            ba, bb = sa.bounding_box(), sb.bounding_box()
            if (ba.min.X > bb.max.X + best[0] or bb.min.X > ba.max.X + best[0] or ba.min.Y > bb.max.Y + best[0] or
                    bb.min.Y > ba.max.Y + best[0] or ba.min.Z > bb.max.Z + best[0] or bb.min.Z > ba.max.Z + best[0]):
                continue
            d = fdist(sa, sb)
            if (sa & sb).volume > 0.01:
                d = -1.0
            if d < best[0]:
                best = (d, a, b)
    return best


def walls():
    """wall thickness of the raw shells: outer-surface samples -> distance to the inner skin faces"""
    from build123d import Compound
    res = {}
    for nm, o, i in (("torso", E.torso_outer(), E.torso_inner()), ("base", E.base_outer(), E.base_inner_eff()),
                     ("arm", E.arm_outer_L(), E.arm_inner_L())):
        ci = Compound(i.faces())
        ds = []
        for f in o.faces():
            if "BSPLINE" not in str(f.geom_type):
                continue
            for u in [k / 24 for k in range(25)]:
                for v in [k / 80 for k in range(81)]:
                    p = f.position_at(u, v)
                    ds.append((ci.distance_to(p), [round(p.X, 1), round(p.Y, 1), round(p.Z, 1)]))
        ds.sort(key=lambda q: q[0])
        res[nm] = {"min_mm": round(ds[0][0], 3), "at": ds[0][1], "p1_mm": round(ds[len(ds) // 100][0], 3),
                   "median_mm": round(ds[len(ds) // 2][0], 3), "max_mm": round(ds[-1][0], 3), "n": len(ds),
                   "lowest5": [[round(d, 3), p] for d, p in ds[:5]]}
        print(nm, res[nm], flush=True)
    return res


def f2_parts():
    meta = json.load(open(f"{OUT}/parts.json"))
    from build123d import import_step
    P = {}
    for p in meta["parts"]:
        P[p["name"]] = (E.one(import_step(p["step"])), p["group"], p["color"])
    return P


def layout(P):
    d = json.load(open(PACK))
    d["comps"] = [c for c in d["comps"] if c["name"] not in REPLACED]
    for c in d["comps"]:                                   # f2 packaging shifts (<= 3 mm, see forma.md)
        if c["name"] in E.SHIFT:
            c["at"] = [c["at"][k] + E.SHIFT[c["name"]][k] for k in range(3)]
    d["allow"] = [a for a in d["allow"] if not (set(a) & REPLACED)]
    for n, (s, g, col) in P.items():
        d["comps"].append({"name": n, "kind": "box", "size": [1, 1, 1], "group": g, "mat": "resin" if col == "white"
                           else "petg", "color": col, "label": n})
    for a, b in BONDED:
        d["allow"].append([a, b])
    d["allow"].append(["T_lem_goliera", "B_golier_prstenec"])
    d["allow"].append(["T_lem_goliera", "B_golier_kotuc"])         # disc runs inside the static ring (B seam 0.25)
    L = T.Layout(d)
    for n, (s, g, col) in P.items():
        L._raw[n] = s
    return L


def static(P, L):
    from build123d import Compound
    outer = {"T": E.torso_outer(), "B": E.base_outer(), "AL": E.arm_outer_L(), "AR": E.mirror_x(E.arm_outer_L())}
    rows, worst = [], {}
    by_group = {}
    for n, (s, g, c) in P.items():
        by_group.setdefault(g, []).append(n)
    internal = [c for c in L.comps if c["name"] not in P and not c["name"].startswith("B_")]
    for c in internal:
        nm, g = c["name"], c["group"]
        g2 = {"P": "T", "L": "T"}.get(g, g)
        sh = L.raw(nm)
        r = {"part": nm, "group": g}
        hits, mind = [], (1e9, None)
        for fn in by_group.get(g2, []):
            fs = P[fn][0]
            bb1, bb2 = sh.bounding_box(), fs.bounding_box()
            near = not (bb1.min.X > bb2.max.X + 4 or bb2.min.X > bb1.max.X + 4 or bb1.min.Y > bb2.max.Y + 4 or
                        bb2.min.Y > bb1.max.Y + 4 or bb1.min.Z > bb2.max.Z + 4 or bb2.min.Z > bb1.max.Z + 4)
            if not near:
                continue
            v = (sh & fs).volume
            if v > 0.01:
                hits.append([fn, round(v, 3), BONDED.get((nm, fn), "")])
            if (nm, fn) not in BONDED:
                d = fdist(sh, fs) if v <= 0.01 else -1.0
                if d < mind[0]:
                    mind = (d, fn)
        r["intersections"] = hits
        r["min_clearance_mm"] = round(mind[0], 2) if mind[1] else None
        r["closest_f2_part"] = mind[1]
        if g2 in outer:
            out_v = (sh - outer[g2]).volume
            r["outside_outer_mm3"] = round(out_v, 2)
        rows.append(r)
        print(nm, r.get("min_clearance_mm"), hits, r.get("outside_outer_mm3"), flush=True)
    return rows


def sweep(L):
    import importlib.util
    spec = importlib.util.spec_from_file_location("rs", "/tmp/claude-0/gapwf/fin/T1/pack/run_sweep.py")
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    out = {}
    for tag, poses in (("std", T.STD_POSES), ("extra", rs.EXTRA)):
        res = {}
        t0 = time.time()
        for i, p in enumerate(poses):
            cl = L.clashes(p, 0.5, only_moving=True)
            res[i] = {"pose": p, "clashes": cl}
            print(tag, i, p, cl, round(time.time() - t0), flush=True)
        out[tag] = res
    return out


def arms(P, L):
    res = {}
    TORSO = ["T_trup_predny", "T_trup_zadny", "T_lem_goliera", "T_sokel"]
    BASE = ["Z_skrupina", "Z_spodok", "Z_svetlovod", "Z_okno_ToF"]
    AL = ["A_L_vnutorna", "A_L_vonkajsia", "A_L_kryt"]
    AR = ["A_R_vnutorna", "A_R_vonkajsia", "A_R_kryt"]
    rows = []
    for a in range(-45, 136, 15):
        d, x, y = gaps(L, {"armL": a, "armR": a}, AL, TORSO)
        rows.append([a, round(d, 2), x, y])
        print("arm-torso", a, round(d, 2), x, y, flush=True)
    res["arm_L_vs_torso_by_angle"] = rows
    res["arm_L_vs_torso_min_mm"] = min(r[1] for r in rows)
    rows = []
    for j in (-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150):
        d, x, y = gaps(L, {"j1": j}, AL + AR, BASE)
        rows.append([j, round(d, 2), x, y])
        print("arm-base", j, round(d, 2), x, y, flush=True)
    res["arms_vs_base_by_j1"] = rows
    res["arms_vs_base_min_mm"] = min(r[1] for r in rows)
    rows = []
    for j in (-150, -90, -30, 0, 45, 120, 150):
        d, x, y = gaps(L, {"j1": j}, ["T_sokel", "T_trup_predny", "T_trup_zadny"], BASE + ["Z_J1_kanal", "Z_J1_hub"])
        rows.append([j, round(d, 2), x, y])
        print("torso-base", j, round(d, 2), x, y, flush=True)
    res["torso_vs_base_by_j1"] = rows
    res["torso_vs_base_min_mm"] = min(r[1] for r in rows)
    d = gaps(L, {"armL": 135, "armR": 135}, AL, AR)[0]
    res["arm_vs_arm_at_135_mm"] = round(d, 2)
    return res


def arm_limits(L):
    HEAD = ["B_hlava", "B_usi", "B_ram_tvar", "B_uska"]
    ARM = ["A_R_vnutorna", "A_R_vonkajsia", "A_R_kryt"]

    def hits(p):
        return bool(L.clashes(p, 0.05, only_moving=True, names=HEAD + ARM))

    def gap(p):
        return gaps(L, p, ARM, HEAD)[0]

    def limit(base):
        if not hits(dict(base, armR=180)) and gap(dict(base, armR=180)) >= 2.0:
            return 180.0
        lo, hi = 60.0, 180.0
        while hi - lo > 1.0:
            m = (lo + hi) / 2
            if hits(dict(base, armR=m)):
                hi = m
            else:
                lo = m
        a = lo
        while a > 60 and gap(dict(base, armR=a)) < 2.0:
            a -= 1.0
        return a
    out = {}
    t0 = time.time()
    for lift, tilt in [(0, 0), (12.5, 30), (12.5, -40), (20, 0), (20, 40), (20, -40)]:
        row = {}
        for pan in (-85, -60, -30, 0, 30, 60, 85):
            row[pan] = limit({"pan": pan, "lift": lift, "tilt": tilt})
        out[f"lift{lift}_tilt{tilt}"] = row
        print(lift, tilt, row, round(time.time() - t0), flush=True)
    return out


def head():
    """real head point cloud vs the f2 torso top: white top from the analytic sections (dimple ignored = it only
    lowers the surface), black trim ring plateau r <= 29.8 @ 133 + R1 round to (30.8, 132)"""
    import numpy as np
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1/pack")
    from head_keepout import read_stl, poses, AX_REST, DZ, Z_TT
    from head_real_check import pose_pts
    STL = "/tmp/claude-0/gapwf/fin/B/stl"
    H = np.vstack([read_stl(f"{STL}/{p}.stl") for p in ("hlava_skrupina", "ram_displeja", "usi", "displej")])
    H = H[H[:, 2] < 25.0]
    # white top height map on a 0.1 mm grid: z_top(x,y) = max z in [110, z_t] with (x,y) inside section(z)
    GS = 0.1
    GX = np.arange(-47, 47 + GS, GS)
    GY = np.arange(-43, 43 + GS, GS)
    X, Y = np.meshgrid(GX, GY, indexing="ij")
    ZW = np.full(X.shape, -1e9)
    for z in np.linspace(S.T["z_t"], 110.0, 1101):
        a, b, n = S.torso_ab(float(z))
        m = (ZW < -1e8) & ((np.abs(X) / a) ** n + (np.abs(Y) / b) ** n <= 1.0)
        ZW[m] = z

    def z_white(x, y):
        i = np.clip(np.round((x - GX[0]) / GS).astype(int), 0, len(GX) - 1)
        j = np.clip(np.round((y - GY[0]) / GS).astype(int), 0, len(GY) - 1)
        return ZW[i, j]

    def z_ring(r):
        z = np.full(r.shape, -1e9)
        z[(r >= 28.35) & (r <= 29.8)] = 133.0
        m = (r > 29.8) & (r <= 30.8)
        z[m] = 132.0 + np.sqrt(np.clip(1 - (r[m] - 29.8) ** 2, 0, None))
        return z
    best = (1e9, None)
    best_white = (1e9, None)
    for lift, tilt in poses():
        for pan in range(-85, 86, 5):
            x, y, z = pose_pts(H, lift, tilt, pan)
            m = z < Z_TT + 5.0
            if not m.any():
                continue
            x, y, z = x[m], y[m], z[m]
            r = np.hypot(x, y)
            zw = np.where(r >= E.TORSO_HOLE_R, z_white(x, y), -1e9)
            zr = z_ring(r)
            cl_w = z - zw
            cl_r = z - zr
            k = int(np.argmin(cl_w))
            if cl_w[k] < best_white[0]:
                best_white = (float(cl_w[k]), {"lift": lift, "tilt": tilt, "pan": pan,
                                               "point": [round(float(x[k]), 1), round(float(y[k]), 1),
                                                         round(float(z[k]), 2)]})
            k = int(np.argmin(cl_r))
            if cl_r[k] < best[0]:
                best = (float(cl_r[k]), {"lift": lift, "tilt": tilt, "pan": pan,
                                         "point": [round(float(x[k]), 1), round(float(y[k]), 1),
                                                   round(float(z[k]), 2)]})
    return {"head_vs_white_torso_top_min_mm": round(best_white[0], 2), "worst_white": best_white[1],
            "head_vs_black_trim_plateau_min_mm": round(best[0], 2), "worst_plateau": best[1],
            "criteria": "white top >= 1.0 (moving parts); plateau >= 0.25 (B-verified criterion, K2/pack had 0.45)",
            "poses": "B tilt-vs-lift table (all rows, limits + 5 deg steps) x pan -85..85 step 5"}


def merge(key, val):
    fn = f"{OUT}/check.json"
    d = json.load(open(fn)) if os.path.exists(fn) else {}
    d[key] = val
    json.dump(d, open(fn, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("walls", "all"):
        merge("wall_thickness", walls())
    if what == "walls":
        sys.exit(0)
    if what in ("head", "all"):
        r = head()
        print(json.dumps(r, indent=1))
        merge("head_real_vs_torso_top", r)
    if what == "head":
        sys.exit(0)
    P = f2_parts()
    L = layout(P)
    if what in ("static", "all"):
        merge("static_clashes_t1lib", L.clashes({}))
        merge("static_fit", static(P, L))
    if what in ("arms", "all"):
        merge("moving_gaps", arms(P, L))
    if what in ("limits", "all"):
        merge("arm_limit_table_deg", arm_limits(L))
    if what in ("sweep", "all"):
        merge("sweep", sweep(L))
    if what in ("mass", "all"):
        res = {}
        for nm, p in (("rest", {}), ("awake", {"lift": 12.5, "tilt": 8, "armR": 14, "armL": 14}),
                      ("worst", {"armR": 100, "armL": 100, "lift": 20, "tilt": 40})):
            res[nm] = L.tipping(p, accel_g=0.15)
        M, c, rows = L.cog({})
        res["f2_exterior_parts_g"] = {r[0]: r[1] for r in rows if r[0] in P}
        merge("mass_cog_tipping", res)
        print(json.dumps(res, indent=1))
