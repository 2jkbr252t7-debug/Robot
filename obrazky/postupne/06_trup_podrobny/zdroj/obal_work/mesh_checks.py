"""mesh-side checks of the OBAL module (Blender python: bmesh + BVH).  Reads stl/<name>.stl of parts_obal.json.
  M1 watertight / manifold STL of every part
  M2 wall thickness of the white shells: rays from the analytic exterior inward, first hit = exterior, second hit = inner
     face; "through-wall" exits (inner offset surface, add-ons) are separated from "edge" exits (cut faces of seams, openings)
  M3 exterior fidelity: deviation of the white parts + plugs from the analytic T4 exterior on a 0.45 mm grid,
     classification of uncovered points (seams, door seam, sockets, plug gaps), protrusion test of every part
  O2 interference among the OBAL parts: BVH triangle overlap of every bbox-overlapping pair, common volume by parity
     sampling around the intersecting triangles, containment test, intended fits listed
  X1 (information for the integrator) the same test of the OBAL parts against the STLs of the RAM module
  S1 seam backing: rays through the seam gaps (x = +-33.3, door seam, socket ring) must hit a part within 9 mm
Usage: /opt/venv/bl/bin/python mesh_checks.py [M1,M2,M3,O2,X1,S1]   -> obal_work/mesh_checks.json (sections are merged)"""
import sys, os, json, math, time, itertools
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

T4 = "/tmp/claude-0/gapwf/fin/T4"
sys.path.insert(0, T4)
import t4_common as C
import t4_obal as O

T0 = time.time()
argv = [a for a in sys.argv[1:] if not a.startswith("-") and not a.endswith(".py")]
WANT = set(argv[-1].split(",")) if argv and all(k[:1] in "MOXSF" for k in argv[-1].split(",")) else {"M1", "M2", "M3", "O2", "X1", "S1", "F1"}
recs = json.load(open(os.path.join(T4, "parts_obal.json")))
recs = recs["parts"] if isinstance(recs, dict) else recs
NAMES = [r["name"] for r in recs]
REC = {r["name"]: r for r in recs}
OUTF = os.path.join(T4, "obal_work", "mesh_checks.json")
OUT = json.load(open(OUTF)) if os.path.exists(OUTF) else {}
for k in list(OUT):
    if k.split("_")[0] in WANT:
        del OUT[k]


def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(T4, "stl", name + ".stl"))
    o = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.normal_update()
    bpy.data.objects.remove(o)
    return bm


BM, TREE, VERTS = {}, {}, {}


def get(name):
    if name not in BM:
        BM[name] = load(name)
        TREE[name] = BVHTree.FromBMesh(BM[name], epsilon=0.0)
        VERTS[name] = np.array([tuple(v.co) for v in BM[name].verts])
    return BM[name]


for n in NAMES:
    get(n)
print("loaded", len(NAMES), round(time.time() - T0, 1), flush=True)
DIRS = [Vector((0.5377, 0.3181, 0.7808)).normalized(), Vector((-0.2113, 0.8712, 0.4431)).normalized(),
        Vector((0.7312, -0.6017, 0.3217)).normalized()]


def inside(tree, p, d=DIRS[0]):
    """ray parity test of point p against a closed mesh (BVH is float32: restart 2e-4 behind every hit and never count
    the same triangle twice in a row)"""
    cnt = 0
    o = Vector(p)
    last = -1
    for _ in range(400):
        hit = tree.ray_cast(o, d, 1e4)
        if hit[0] is None:
            break
        if hit[2] == last and hit[3] < 1e-3:
            o = o + d * 1e-3
            continue
        cnt += 1
        last = hit[2]
        o = hit[0] + d * 2e-4
    return cnt % 2 == 1


def inside3(tree, p):
    v = sum(1 for d in DIRS if inside(tree, p, d))
    return v >= 2


# ---------------------------------------------------------------------------------------------------- M1 watertight
if "M1" in WANT:
    m1 = {}
    for r in recs:
        bm = BM[r["name"]]
        nonman = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        vol = bm.calc_volume(signed=True)
        m1[r["name"]] = dict(verts=len(bm.verts), tris=len(bm.faces), non_manifold_edges=nonman, volume=round(vol, 2),
                             ok=bool(nonman == 0 and vol > 0 and abs(vol - r["volume_mesh"]) <= max(0.3, 0.002 * r["volume_mesh"])))
    OUT["M1_watertight"] = dict(parts=m1, all_ok=all(v["ok"] for v in m1.values()))
    print("M1", OUT["M1_watertight"]["all_ok"], [k for k, v in m1.items() if not v["ok"]], round(time.time() - T0, 1), flush=True)

# ---------------------------------------------------------------------------------------------------- exterior grid
WHITE = ["T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka"]
if WANT & {"M2", "M3", "S1"}:
    big = bmesh.new()
    owner = []
    for nme in WHITE:
        me = bpy.data.meshes.new("tmp"); BM[nme].to_mesh(me); big.from_mesh(me); bpy.data.meshes.remove(me)
        owner += [nme] * len(BM[nme].faces)
    big.faces.ensure_lookup_table()
    wtree = BVHTree.FromBMesh(big, epsilon=0.0)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(C.PD), np.maximum(np.abs(np.diff(C.PA)), np.abs(np.diff(C.PB)))))])
    kmax = np.searchsorted(C.PD, C.DROP_WHITE - 0.02)
    t = np.arange(0.15, arc[kmax], 0.45)
    dd = np.interp(t, arc, C.PD)
    P = []
    for d in dd:
        a, b, n = C.prof(d)
        per = 2 * math.pi * math.sqrt((a * a + b * b) / 2)
        th = C.azimuths(max(24, int(per / 0.45)))
        rr = C.se_r(a, b, n, th)
        P.append(np.stack([rr * np.cos(th), rr * np.sin(th), np.full(len(th), C.TOP - d)], 1))
    P = np.concatenate(P)
    N = O.normal(P)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    dw, dh, dr = C.DOOR
    zc = C.Z_DOOR
    zb = C.Z_DOOR - C.DOOR[1] / 2

    def rrect_dist(xx, zz, w, h, r):
        qx = np.abs(xx) - (w / 2 - r); qz = np.abs(zz - zc) - (h / 2 - r)
        return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - r

    def pill_dist(xx, zz, w, h, z0):
        r = h / 2
        qx = np.maximum(np.abs(xx) - (w / 2 - r), 0)
        return np.hypot(qx, zz - z0) - r

    dd_door = rrect_dist(x, z, dw + C.SEAM / 2, dh + C.SEAM / 2, dr + C.SEAM / 4)      # mid line of the door seam
    r_sock = np.hypot(y - C.SH_Y, z - C.SH_Z)
    START = 4.0
    dev = np.full(len(P), np.nan); thick = np.full(len(P), np.nan); exit_kind = np.zeros(len(P), int)
    EXIT = ["none", "wall", "seam plane x", "lower edge z", "door edge", "socket bore", "front opening", "oblique face", "collar bore"]

    def classify_exit(q, fn, d):
        """where the inward ray leaves the material: 1 = a real wall face, 2.. = a cut face of a seam / opening"""
        ax = abs(q.x)
        if abs(ax - C.X_BAND) < 0.02 or abs(ax - C.X_CAP) < 0.02:
            return 2
        if abs(q.z - C.Z_WHITE) < 0.02:
            return 3
        if q.y > 5:
            dq = [abs(float(rrect_dist(np.array([q.x]), np.array([q.z]), dw + 2 * g, dh + 2 * g, dr + g)[0])) for g in (0.0, C.SEAM / 2)]
            if min(dq) < 0.02:
                return 4
        if ax > C.X_SEAT - 0.05 and abs(math.hypot(q.y - C.SH_Y, q.z - C.SH_Z) - C.R_SOCKET) < 0.03:
            return 5
        if q.y < 0 and (abs(float(pill_dist(np.array([q.x]), np.array([q.z]), C.BAR[0], C.BAR[1], C.Z_BAR)[0])) < 0.02 or
                        abs(float(pill_dist(np.array([q.x]), np.array([q.z]), C.SLOT[0], C.SLOT[1], C.Z_SLOT)[0])) < 0.02):
            return 6
        if q.z > C.Z_BORE_BOT and abs(math.hypot(q.x, q.y) - C.R_BORE) < 0.03:
            return 8
        return 1 if d.dot(fn) > 0.3 else 7
    through = None
    hit_owner = np.full(len(P), -1)
    for i in range(len(P)):
        p = Vector(P[i]); n = Vector(N[i])
        hit = wtree.ray_cast(p + n * START, -n, START + 1.5)
        if hit[0] is None:
            continue
        dev[i] = START - hit[3]                 # + = part surface outside the analytic surface
        hit_owner[i] = WHITE.index(owner[hit[2]])
        h2 = wtree.ray_cast(hit[0] - n * 1e-4, -n, 40.0)
        if h2[0] is not None:
            thick[i] = h2[3] + 1e-4
            exit_kind[i] = classify_exit(h2[0], h2[1], -n)
    cov = ~np.isnan(dev)
    through = exit_kind == 1

# ---------------------------------------------------------------------------------------------------- M2 wall thickness
if "M2" in WANT:
    edge_d = np.minimum.reduce([np.abs(np.abs(x) - C.X_BAND), np.abs(np.abs(x) - C.X_CAP),
                                np.where(y > 5, np.abs(rrect_dist(x, z, dw + C.SEAM, dh + C.SEAM, dr + C.SEAM / 2)), 99.0),
                                np.where(y > 5, np.abs(rrect_dist(x, z, dw, dh, dr)), 99.0),
                                np.where(np.abs(x) > 40, np.abs(r_sock - C.R_SOCKET), 99.0),
                                np.where(y < 0, np.abs(pill_dist(x, z, C.BAR[0], C.BAR[1], C.Z_BAR)), 99.0),
                                np.where(y < 0, np.abs(pill_dist(x, z, C.SLOT[0], C.SLOT[1], C.Z_SLOT)), 99.0),
                                np.abs(z - C.Z_WHITE)])
    shell = np.isin(hit_owner, [0, 1, 2, 3])                      # T_stred, caps, door (plugs are not walls)
    on_skin = cov & (np.abs(dev) < 0.06)                          # first hit is the exterior itself (not a gap wall)
    ok_t = on_skin & shell & through & ~np.isnan(thick)
    tw = thick[ok_t]
    DECL = {
        "LED boss pilots D1.7 (skin >= 1.2 behind the pilot)": (y < 0) & (np.hypot(np.abs(x) - C.LED_BOSS[0][0], z - C.LED_BOSS[0][1]) <= 1.6),
        "speaker boss pilots D1.7": (y < 0) & (np.minimum.reduce([np.hypot(x - bx_, z - bz_) for bx_, bz_ in O.spk_boss_xz()]) <= 1.6),
        "door_notch (finger notch, 0.85 deep)": (y > 5) & (np.abs(x) <= O.NOTCH["w"] / 2 + 0.6) & (z <= zb + O.NOTCH["h"] + 0.6),
        "front lip relief (pan-servo tabs)": (y < 0) & (np.abs(x) <= C.LIP_RELIEF["x"][1] + 0.5) & (z <= -79.3),
    }
    decl = np.zeros(len(P), bool)
    for mk in DECL.values():
        decl |= mk
    thin2 = ok_t & (thick < C.WALL_MIN - 0.02) & ~decl
    thin12 = ok_t & (thick < C.WALL_LOCAL)
    wedge = on_skin & shell & (exit_kind == 5) & ~np.isnan(thick)          # rim of the shoulder socket: exterior meets the bore
    wedge_far = wedge & (np.abs(r_sock - C.R_SOCKET) > 0.6)
    spots = []
    for i in np.argsort(np.where(thin2, thick, 9e9))[:4000]:
        if not thin2[i]:
            break
        if all(np.linalg.norm(P[i] - np.array(s["at"])) > 3.0 for s in spots):
            spots.append(dict(t=round(float(thick[i]), 3), at=[round(float(v), 2) for v in P[i]], part=WHITE[hit_owner[i]]))
        if len(spots) >= 25:
            break
    m2 = dict(method="inward ray from the analytic exterior (0.45 mm grid): distance exterior hit -> next face; exits are classified: "
                     "real wall faces (statistics below) / cut faces of seams, lower edge, door, front openings (skipped) / socket bore "
                     "(rim wedge, reported separately)",
              exits={EXIT[k]: int((on_skin & shell & (exit_kind == k)).sum()) for k in range(1, 9)},
              top_rim=dict(note="flat white rim around the collar bore: width R_RIM - R_BORE = 1.25 by construction (brief: >= 1.2); "
                                "ray thickness from the rim / shelf to the bore face",
                           min=round(float(thick[on_skin & shell & (exit_kind == 8)].min()), 3) if (on_skin & shell & (exit_kind == 8)).any() else None),
              socket_rim_wedge=dict(points=int(wedge.sum()), note="exterior meets the socket bore r 14 at a shallow angle on TOP of the shoulder "
                                    "(approved T3 look): thickness between exterior and bore, points further than 0.6 mm (radially) from the rim",
                                    min_beyond_0p6=round(float(thick[wedge_far].min()), 3) if wedge_far.any() else None,
                                    n_below_1p2_beyond_0p6=int((wedge_far & (thick < 1.2)).sum()),
                                    worst=[[round(float(v), 2) for v in P[i]] + [round(float(thick[i]), 3)]
                                           for i in np.argsort(np.where(wedge_far, thick, 9e9))[:4]]),
              points=int(ok_t.sum()), min=round(float(tw.min()), 3), p001=round(float(np.percentile(tw, 0.1)), 3),
              p01=round(float(np.percentile(tw, 1)), 3), median=round(float(np.median(tw)), 3),
              frac_below_2p0=round(float((tw < C.WALL_MIN - 0.02).mean()), 5),
              declared_thin={k: dict(points=int((ok_t & mk).sum()), min=round(float(thick[ok_t & mk].min()), 3) if (ok_t & mk).any() else None)
                             for k, mk in DECL.items()},
              n_below_2p0_not_declared=int(thin2.sum()), n_below_1p2=int(thin12.sum()), thin_spots=spots,
              ok=bool(thin12.sum() == 0))
    # per printed part: plain inward-ray statistics from every triangle (information; acute edges read as thin)
    info = {}
    for r in recs:
        if not r["printed"]:
            continue
        bm = BM[r["name"]]; tree = TREE[r["name"]]
        th_, ar_ = [], []
        for f in bm.faces:
            a = f.calc_area()
            if a < 1e-4:
                continue
            c = f.calc_center_median(); nn = f.normal
            hit = tree.ray_cast(c - nn * 1e-3, -nn, 60.0)
            if hit[0] is None or (-nn).dot(hit[1]) < 0.5:
                continue
            th_.append(hit[3] + 1e-3); ar_.append(a)
        th_ = np.array(th_); ar_ = np.array(ar_)
        info[r["name"]] = dict(min=round(float(th_.min()), 3), p01=round(float(np.percentile(th_, 1)), 3), median=round(float(np.median(th_)), 3),
                               area_frac_below_0p6=round(float(ar_[th_ < 0.6].sum() / ar_.sum()), 5),
                               area_frac_below_1p2=round(float(ar_[th_ < 1.2].sum() / ar_.sum()), 5))
    m2["per_part_opposite_face_rays"] = info
    OUT["M2_wall"] = m2
    print("M2", m2["ok"], "min", m2["min"], "p01", m2["p01"], "median", m2["median"], "<2.0 not declared:", m2["n_below_2p0_not_declared"],
          "<1.2:", m2["n_below_1p2"], round(time.time() - T0, 1), flush=True)
    for s in spots[:25]:
        print("     thin", s, flush=True)
    for k, v in info.items():
        print("     info", k, v, flush=True)

# ---------------------------------------------------------------------------------------------------- M3 exterior
if "M3" in WANT:
    zones = {
        "seam_x": (np.abs(np.abs(x) - C.XS) <= C.SEAM / 2 + 0.12),
        "door_seam": (y > 5) & (np.abs(dd_door) <= C.SEAM / 4 + 0.12),
        "door_notch": (y > 5) & (np.abs(x) <= O.NOTCH["w"] / 2 + 0.1) & (z <= zb + O.NOTCH["h"] + 0.1) & (z >= zb - 0.4),
        "socket": (r_sock <= C.R_SOCKET + 0.12) & (np.abs(x) > 40),
        "bar_gap": (y < 0) & (np.abs(pill_dist(x, z, C.BAR[0] - 0.2, C.BAR[1] - 0.2, C.Z_BAR)) <= 0.1 + 0.12),
        "grille_gap": (y < 0) & (np.abs(pill_dist(x, z, C.SLOT[0] - 0.2, C.SLOT[1] - 0.2, C.Z_SLOT)) <= 0.1 + 0.12),
        "grille_slots": (y < 0) & (pill_dist(x, z, C.GRILLE["plug"][0], C.GRILLE["plug"][1], C.Z_SLOT) <= 0.0),
    }
    declared = np.zeros(len(P), bool)
    for mk in zones.values():
        declared |= mk
    bad_dev = cov & ~declared & (np.abs(dev) > 0.05)
    unexpl = ~cov & ~declared
    m3 = dict(grid_points=int(len(P)), covered=int(cov.sum()), spacing=0.45, stl_deflection=REC["T_stred"].get("stl", {}).get("deflection_mm"),
              dev_min=round(float(np.nanmin(dev[~declared])), 4), dev_max=round(float(np.nanmax(dev[~declared])), 4),
              dev_abs_p999=round(float(np.nanpercentile(np.abs(dev[cov & ~declared]), 99.9)), 4),
              n_dev_over_0p05_outside_declared=int(bad_dev.sum()),
              uncovered_total=int((~cov).sum()), uncovered_in_declared={k: int((~cov & mk).sum()) for k, mk in zones.items()},
              uncovered_unexplained=int(unexpl.sum()),
              unexplained_samples=[[round(float(v), 2) for v in P[i]] for i in np.where(unexpl)[0][:12]],
              bad_dev_samples=[[round(float(v), 2) for v in P[i]] + [round(float(dev[i]), 3)] for i in np.where(bad_dev)[0][:12]])
    # measured seam widths: scan across the seam, a point is "skin" when the ray along its own normal meets a part within 0.06
    def skin(pt):
        nn = Vector(O.normal(np.array([pt]))[0])
        h = wtree.ray_cast(Vector(pt) + nn * 2.0, -nn, 2.06)
        return h[0] is not None and abs(2.0 - h[3]) < 0.06

    def gap_scan(fpt, c, half=1.0):
        """fpt(s) -> point on the exterior; uncovered run around s = c"""
        if skin(fpt(c)):
            return 0.0
        w = 0.0
        for sg in (1, -1):
            lo, hi = 0.0, half
            if not skin(fpt(c + sg * hi)):
                return float("nan")
            for _ in range(20):
                mid = 0.5 * (lo + hi)
                if skin(fpt(c + sg * mid)):
                    hi = mid
                else:
                    lo = mid
            w += 0.5 * (lo + hi)
        return w
    sw = {}
    ws = []
    for sx in (1, -1):
        for zz in (-70.0, -50.0, -30.0, -10.0):
            for side in (-1, 1):
                ws.append(gap_scan(lambda q: np.array([sx * q, C.y_surface(q, zz, side), zz]), C.XS))
    sw["seam_x, width along x (16 stations)"] = [round(float(np.nanmin(ws)), 3), round(float(np.nanmax(ws)), 3)]
    ws = []
    for zz in (-60.0, -42.0, -24.0):
        for sx in (1, -1):
            ws.append(gap_scan(lambda q: np.array([sx * q, C.y_surface(q, zz, 1), zz]), dw / 2 + C.SEAM / 4))
    sw["door seam sides, width along x (6 stations)"] = [round(float(np.nanmin(ws)), 3), round(float(np.nanmax(ws)), 3)]
    ws = []
    for xx in (-15.0, 0.0, 15.0):
        for ze in (zc + dh / 2 + C.SEAM / 4, zc - dh / 2 - C.SEAM / 4):
            if abs(xx) < 7 and ze < zc:
                continue                                              # finger notch
            ws.append(gap_scan(lambda q: np.array([xx, C.y_surface(xx, q, 1), q]), ze))
    sw["door seam top / bottom, width along z (5 stations)"] = [round(float(np.nanmin(ws)), 3), round(float(np.nanmax(ws)), 3)]
    m3["seam_widths_measured"] = sw
    prot = {}
    ALLOW = ("T_klb_", "T_puzdro_", "skrutka_klb_", "magnet_klb_", "pruzina_klb_")
    for r in recs:
        V = VERTS[r["name"]]
        zz_ = np.clip(V[:, 2], C.Z_BOT, C.TOP)
        a = np.interp(C.TOP - zz_, C.PD, C.PA); b = np.interp(C.TOP - zz_, C.PD, C.PB); n = np.interp(C.TOP - zz_, C.PD, C.PN)
        f = (np.abs(V[:, 0]) / a) ** n + (np.abs(V[:, 1]) / b) ** n
        rad = np.hypot(V[:, 0], V[:, 1]) * (1 - f ** (-1 / n))            # radial excess (+ outside)
        rad = np.where(V[:, 2] > C.TOP + 1e-6, np.maximum(rad, V[:, 2] - C.TOP), rad)
        prot[r["name"]] = round(float(rad.max()), 4)
    m3["max_radial_protrusion"] = prot
    m3["protruding_not_declared"] = {k: v for k, v in prot.items() if v > 0.03 and not k.startswith(ALLOW)}
    m3["ok"] = bool(m3["n_dev_over_0p05_outside_declared"] == 0 and m3["uncovered_unexplained"] == 0 and not m3["protruding_not_declared"])
    OUT["M3_exterior"] = m3
    print("M3", m3["ok"], "dev", m3["dev_min"], m3["dev_max"], "p99.9", m3["dev_abs_p999"], "bad", m3["n_dev_over_0p05_outside_declared"],
          "uncovered", m3["uncovered_total"], m3["uncovered_in_declared"], "unexplained", m3["uncovered_unexplained"],
          "seams", sw, round(time.time() - T0, 1), flush=True)
    print("     bad dev samples", m3["bad_dev_samples"][:6], "unexplained", m3["unexplained_samples"][:6], flush=True)

# ---------------------------------------------------------------------------------------------------- S1 seam backing
if "S1" in WANT:
    EXTRA_S1 = []
    for xn in ("T_spodok", "T_ram"):
        if os.path.exists(os.path.join(T4, "stl", xn + ".stl")):
            bpy.ops.wm.stl_import(filepath=os.path.join(T4, "stl", xn + ".stl"))
            o = bpy.context.selected_objects[0]
            bmx = bmesh.new(); bmx.from_mesh(o.data); bpy.data.objects.remove(o)
            TREE["S1_" + xn] = BVHTree.FromBMesh(bmx, epsilon=0.0); EXTRA_S1.append("S1_" + xn)
    S1_OWN = list(NAMES); S1_ALL = NAMES + EXTRA_S1

    def first_hit(p0, d, depth, trees):
        best = None
        for nme in trees:
            h = TREE[nme].ray_cast(Vector(p0) - d * 3.0, d, 3.0 + depth)
            if h[0] is not None and (best is None or h[3] < best):
                best = h[3]
        return best

    def backed(p0, n0, g, depth=9.0, fan=(0.0, 20.0, -20.0, 40.0, -40.0)):
        """lines of sight THROUGH a gap: the gap walls are parallel to the plane normal to g (seam plane x = const: g = X;
        door top / bottom edge: g = Z; ...), so only directions inside that plane can pass.  d0 = inward normal projected
        into the plane, then a fan about g.  Returns [(blocked by OBAL, blocked by OBAL + RAM)] per direction."""
        g = Vector(g).normalized()
        d0 = -Vector(n0); d0 = (d0 - g * d0.dot(g)).normalized()
        t = g.cross(d0)
        res = []
        for ang in fan:
            d = (d0 * math.cos(math.radians(ang)) + t * math.sin(math.radians(ang))).normalized()
            b_all = first_hit(p0, d, depth, S1_ALL) is not None
            thru = (not b_all) and first_hit(p0, d, 160.0, S1_ALL) is None            # leaves the torso again = real see-through
            res.append((first_hit(p0, d, depth, S1_OWN) is not None, b_all, float(d.z), thru))
        return res

    def tally(store, kind, p0, rr_):
        b = store.setdefault(kind, dict(rays=0, open_obal_only=0, open=0, see_through=0, open_samples=[], open_min_dz=None))
        b["see_through"] += sum(1 for q in rr_ if q[3])
        b["rays"] += len(rr_); b["open_obal_only"] += sum(1 for q in rr_ if not q[0]); b["open"] += sum(1 for q in rr_ if not q[1])
        for q in rr_:
            if not q[1]:
                b["open_min_dz"] = round(q[2], 3) if b["open_min_dz"] is None else round(min(b["open_min_dz"], q[2]), 3)
        if any(not q[1] for q in rr_) and len(b["open_samples"]) < 10:
            b["open_samples"].append([round(float(v), 2) for v in p0])
    s1 = {}
    # seams x = +-XS: stations along the seam (front, top, back), every 0.5 mm of height
    st = {}
    for sx in (1, -1):
        for side in (-1, 1):
            for zz in np.arange(-80.75, 1.0, 0.5):
                p0 = np.array([sx * C.XS, C.y_surface(C.XS, zz, side), zz])
                tally(st, "seam_x" if zz > O.LIP["z_bot"] + 0.2 else "seam_x_lower_end (below the lip, z < -77.5)", p0,
                      backed(p0, O.normal(np.array([p0]))[0], (1, 0, 0)))
        for yy in np.arange(-18.0, 18.01, 0.5):                     # across the top
            zt = C.TOP - float(np.interp(C.XS, C.PA[:np.argmax(C.PA)], C.PD[:np.argmax(C.PA)])) if False else None
            # top of the seam: highest z with the seam plane still inside the exterior at this y
            lo, hi = -20.0, C.TOP
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                a_, b_, n_ = C.prof(C.TOP - mid)
                if (C.XS / a_) ** n_ + (abs(yy) / b_) ** n_ < 1.0:
                    lo = mid
                else:
                    hi = mid
            p0 = np.array([sx * C.XS, yy, lo])
            tally(st, "seam_x_top", p0, backed(p0, O.normal(np.array([p0]))[0], (1, 0, 0)))
    s1.update(st)
    # door seam: mid line of the 0.25 gap; walls are parallel to Y
    mid_w, mid_h, mid_r = dw + C.SEAM / 2, dh + C.SEAM / 2, dr + C.SEAM / 4
    st = {}
    for xx in np.arange(-(mid_w / 2 - mid_r), mid_w / 2 - mid_r + 1e-6, 0.5):
        for ze, kind in ((zc + mid_h / 2, "door_top"), (zc - mid_h / 2, "door_bottom")):
            p0 = np.array([xx, C.y_surface(xx, ze, 1), ze])
            k2 = kind + ("_centre (no ledge, |x| < 20.6)" if (kind == "door_top" and abs(xx) < O.TOP_GAP_X) else "")
            tally(st, k2, p0, backed(p0, O.normal(np.array([p0]))[0], (0, 0, 1)))
    for zz in np.arange(zc - (mid_h / 2 - mid_r), zc + mid_h / 2 - mid_r + 1e-6, 0.5):
        for xe in (mid_w / 2, -mid_w / 2):
            p0 = np.array([xe, C.y_surface(xe, zz, 1), zz])
            tally(st, "door_sides", p0, backed(p0, O.normal(np.array([p0]))[0], (1, 0, 0)))
    for a in np.arange(2.5, 90, 5.0):
        for sx in (1, -1):
            for sz in (1, -1):
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                xx = sx * (mid_w / 2 - mid_r + mid_r * ca); zz = zc + sz * (mid_h / 2 - mid_r + mid_r * sa)
                p0 = np.array([xx, C.y_surface(xx, zz, 1), zz])
                kc = "door_top_centre (no ledge, |x| < 20.6)" if (sz > 0 and abs(xx) < O.TOP_GAP_X + 1.0) else "door_corners"
                tally(st, kc, p0, backed(p0, O.normal(np.array([p0]))[0], (sx * ca, 0, sz * sa), fan=(0.0, 8.0, -8.0)))
    s1.update(st)
    # socket ring: gap r 13.5 .. 14.0, walls parallel to X
    st = {}; opens = set()
    for sx in (1, -1):
        for a in np.arange(0, 360, 5.0):
            rm = (C.R_SOCKET + 13.5) / 2
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            yy = C.SH_Y + rm * ca; zz = C.SH_Z + rm * sa
            p0 = np.array([sx * C.x_surface(yy, zz), yy, zz])
            rr_ = backed(p0, (sx, 0, 0), (0, ca, sa), depth=14.0, fan=(0.0, 6.0, -6.0))
            tally(st, "socket_ring", p0, rr_)
            if any(not q[0] for q in rr_):
                opens.add(float(a))
    s1.update(st)
    s1["socket_ring"]["open_obal_only_azimuths"] = sorted(opens)
    s1["note"] = ("lines of sight through the seam gaps: directions inside the gap plane (inward normal projected into it, fan +-20 / +-40 deg; "
                  "+-8 at the door corners, +-6 in the socket ring).  open_obal_only = meets no OBAL part within 9 mm (14 mm in the socket); "
                  "open = meets neither an OBAL part nor " + (" / ".join(q[3:] for q in EXTRA_S1) if EXTRA_S1 else "(RAM STLs not found)") +
                  " within that depth; see_through = meets nothing at all within 160 mm (the line leaves the torso again)")
    DECL_S1 = {"door_top_centre (no ledge, |x| < 20.6)": "ledge omitted for the pan sweep (spec 4.3): the 0.25 seam along the top edge of the door is "
                                                         "open to the dark interior between the hook tabs",
               "seam_x_lower_end (below the lip, z < -77.5)": "the seam lip ends at z -77.7, the cap spigot top is at -78.0: horizontal lines of "
                                                            "sight through that 0.3 mm slit and lines rising from below the lower edge pass into "
                                                            "the shell; they end on the frame / inside of the shell (no see-through)"}
    s1["declared_open"] = {k: dict(open=s1[k]["open"], rays=s1[k]["rays"], open_min_dz=s1[k]["open_min_dz"], reason=r) for k, r in DECL_S1.items() if k in s1}
    s1["see_through_total"] = int(sum(v["see_through"] for v in s1.values() if isinstance(v, dict) and "rays" in v))
    s1["ok"] = bool(all(v["open"] == 0 for k, v in s1.items() if isinstance(v, dict) and "rays" in v and k not in DECL_S1) and
                    s1["see_through_total"] == 0)
    OUT["S1_seam_backing"] = s1
    for k, v in s1.items():
        if isinstance(v, dict) and "rays" in v:
            print("   S1", k, {q: v[q] for q in ("rays", "open_obal_only", "open", "see_through", "open_min_dz")}, v["open_samples"][:3], flush=True)
    print("S1 ok", s1["ok"], "declared open:", {k: (v["open"], v["rays"]) for k, v in s1["declared_open"].items()}, round(time.time() - T0, 1), flush=True)


# ---------------------------------------------------------------------------------------------------- O2 / X1 interference
def bbox_of(V):
    return np.concatenate([V.min(0), V.max(0)])


def pair_test(na, nb, max_pts=160000):
    """(n overlapping triangle pairs, common volume estimate, centre, half-depth, containment)"""
    ta, tb = TREE[na], TREE[nb]
    ov = ta.overlap(tb)
    bma, bmb = BMF[na], BMF[nb]
    if not ov:
        # containment: one vertex of each inside the other?
        ca = inside3(tb, Vector(VERTS[na][0])); cb = inside3(ta, Vector(VERTS[nb][0]))
        return dict(tri_pairs=0, contained=bool(ca or cb), common_mm3=None if (ca or cb) else 0.0)
    ia = sorted({i for i, _ in ov}); ib = sorted({j for _, j in ov})
    pts = np.array([tuple(v.co) for i in ia for v in bma[i].verts] + [tuple(v.co) for j in ib for v in bmb[j].verts])
    # clusters of intersection locations (6 mm cells) -> one sampling box each
    cell = np.floor(pts / 6.0).astype(int)
    keys = {tuple(k) for k in cell}
    clusters = []
    seen = set()
    for k in keys:
        if k in seen:
            continue
        stack = [k]; grp = []
        while stack:
            q = stack.pop()
            if q in seen or q not in keys:
                continue
            seen.add(q); grp.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        stack.append((q[0] + dx, q[1] + dy, q[2] + dz))
        g = np.array(grp)
        m = np.zeros(len(pts), bool)
        for q in grp:
            m |= (cell == np.array(q)).all(1)
        clusters.append(pts[m])
    tot = 0.0; worst = (0.0, None); cl_out = []
    budget = max(8000, max_pts // max(1, len(clusters)))
    for cp in clusters:
        lo = cp.min(0) - 0.25; hi = cp.max(0) + 0.25
        vol_box = float(np.prod(hi - lo))
        h = max(0.04, (vol_box / budget) ** (1 / 3))
        gx, gy, gz = (np.arange(lo[k] + h / 2, hi[k], h) for k in range(3))
        cnt = 0; cen = np.zeros(3); deep = 0.0
        for xx in gx:
            for yy in gy:
                # march along z with parity from both meshes: test each point (cheap enough for the budget)
                for zz in gz:
                    p = Vector((xx, yy, zz))
                    if inside(ta, p) and inside(tb, p) and inside3(ta, p) and inside3(tb, p):
                        cnt += 1; cen += (xx, yy, zz)
                        da = ta.find_nearest(p)[3]; db = tb.find_nearest(p)[3]
                        deep = max(deep, min(da, db))
        v = cnt * h ** 3
        tot += v
        if cnt:
            cl_out.append(dict(common_mm3=round(v, 3), centre=[round(float(q), 2) for q in cen / cnt], half_depth=round(deep, 3), grid=round(h, 3)))
    cl_out.sort(key=lambda q: -q["common_mm3"])
    return dict(tri_pairs=len(ov), contained=False, common_mm3=round(tot, 3), clusters=cl_out[:12],
                max_half_depth=max([c["half_depth"] for c in cl_out], default=0.0))


INTENDED = [   # (prefix a, prefix b, what) - designed overlaps / contacts
    ("skrutka_led", "T_stred", "thread-forming M2 x 6 in the pilot D1.7 of the LED boss (thread engagement)"),
    ("skrutka_repro", "T_stred", "thread-forming M2 x 6 in the pilot D1.7 of the speaker boss (thread engagement)"),
    ("skrutka_klb", "vl_F8", "F8 screw in the brass insert of the column boss"),
    ("skrutka_klb", "T_ram", "F8 screw tip in the pilot behind the insert"),
    ("vlozka_stred", "skr_F1", "F1 screw in the brass insert of T_stred"),
    ("T_stred", "skr_F1", "F1 screw tip in the pilot above the insert"),
]


def intended(a, b):
    for pa, pb, what in INTENDED:
        if (a.startswith(pa) and b.startswith(pb)) or (b.startswith(pa) and a.startswith(pb)):
            return what
    return None


BMF = {}
if WANT & {"O2", "X1"}:
    for n in NAMES:
        BM[n].faces.ensure_lookup_table(); BMF[n] = BM[n].faces
    BB = {n: bbox_of(VERTS[n]) for n in NAMES}

    def bb_overlap(A, B, pad=0.0):
        return all(A[k] < B[k + 3] + pad and B[k] < A[k + 3] + pad for k in range(3))

if "O2" in WANT:
    res = []
    pairs = [(a, b) for a, b in itertools.combinations(NAMES, 2) if bb_overlap(BB[a], BB[b])]
    for a, b in pairs:
        t = time.time()
        r = pair_test(a, b)
        r.update(a=a, b=b, intended=intended(a, b), time_s=round(time.time() - t, 1))
        res.append(r)
        v = r["common_mm3"]
        if r["tri_pairs"] or r["contained"]:
            flag = "" if ((v is not None and (v < 0.02 or r.get("max_half_depth", 0) <= 0.02)) or r["intended"]) else "   <-- INTERFERENCE"
            print(f"   {a:18s} x {b:18s} tri pairs {r['tri_pairs']:5d} common {v} mm3 half-depth {r.get('max_half_depth')} "
                  f"({r['time_s']} s) {r['intended'] or ''}{flag}", flush=True)
            for c in r.get("clusters", [])[:4]:
                if c["common_mm3"] >= 0.02:
                    print("        ", c, flush=True)
    def is_bad(r):
        return (r["contained"] or ((r["common_mm3"] or 0) >= 0.02 and r.get("max_half_depth", 0) > 0.02)) and not r["intended"]
    bad = [r for r in res if is_bad(r)]
    OUT["O2_interference"] = dict(method="BVH triangle overlap of every bbox-overlapping pair of STL meshes (deflection 0.01); common volume by "
                                         "ray-parity sampling (3 directions) around the intersecting triangles; interference = common volume "
                                         ">= 0.02 mm3 with a penetration half-depth > 0.02 mm (coincident glued / seated faces give thin "
                                         "mesh-noise slivers of half-depth <= 0.01)",
                                  pairs_tested=len(res), touching=[dict(a=r["a"], b=r["b"], tri_pairs=r["tri_pairs"], common_mm3=r["common_mm3"],
                                                                       half_depth=r.get("max_half_depth"), intended=r["intended"])
                                                                  for r in res if r["tri_pairs"] or r["contained"]],
                                  not_intended=bad, all_ok=len(bad) == 0)
    print("O2", len(res), "pairs, interferences:", [(r["a"], r["b"], r["common_mm3"]) for r in bad], round(time.time() - T0, 1), flush=True)

if "X1" in WANT:
    pr = os.path.join(T4, "parts_ram.json")
    xr = []
    if os.path.exists(pr):
        rj = json.load(open(pr))
        rparts = rj["parts"] if isinstance(rj, dict) and "parts" in rj else rj
        rnames = [r["name"] for r in rparts if os.path.exists(os.path.join(T4, "stl", r["name"] + ".stl"))]
        for n in rnames:
            bm = load(n); bm.faces.ensure_lookup_table()
            BM[n] = bm; BMF[n] = bm.faces; TREE[n] = BVHTree.FromBMesh(bm, epsilon=0.0)
            VERTS[n] = np.array([tuple(v.co) for v in bm.verts]); BB[n] = bbox_of(VERTS[n])
        for a in NAMES:
            for b in rnames:
                if not bb_overlap(BB[a], BB[b]):
                    continue
                t = time.time()
                r = pair_test(a, b, max_pts=60000)
                if r["tri_pairs"] or r["contained"]:
                    r.update(a=a, b=b, intended=intended(a, b), time_s=round(time.time() - t, 1))
                    xr.append(r)
                    v = r["common_mm3"]
                    flag = "" if ((v is not None and (v < 0.02 or r.get("max_half_depth", 0) <= 0.02)) or r["intended"]) else "   <-- overlap"
                    print(f"   X {a:18s} x {b:18s} tri pairs {r['tri_pairs']:5d} common {v} mm3 half-depth {r.get('max_half_depth')} "
                          f"{r['intended'] or ''}{flag}", flush=True)
                    for c in r.get("clusters", [])[:3]:
                        if c["common_mm3"] >= 0.02:
                            print("        ", c, flush=True)
        # minimum distance of the big OBAL parts to the RAM parts (vertex -> surface), for the report
        near = []
        for a in ("T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_klb_L", "T_klb_P", "T_drziak_led", "T_drziak_repro", "reproduktor"):
            for b in rnames:
                if not bb_overlap(BB[a], BB[b], 1.5):
                    continue
                V = VERTS[b]
                m = np.all((V >= BB[a][:3] - 1.5) & (V <= BB[a][3:] + 1.5), axis=1)
                best = (9e9, None)
                for p in V[m][::max(1, int(m.sum() / 6000))]:
                    d = TREE[a].find_nearest(Vector(p), 1.5)
                    if d[0] is not None and d[3] < best[0]:
                        best = (d[3], p)
                if best[1] is not None:
                    near.append(dict(a=a, b=b, min_dist=round(float(best[0]), 3), at=[round(float(q), 2) for q in best[1]]))
        gaps = {}
        if "T_ram" in VERTS:
            Vr = VERTS["T_ram"]
            rsh = np.hypot(Vr[:, 1] - C.SH_Y, Vr[:, 2] - C.SH_Z)
            for tag, sx in (("L", 1), ("P", -1)):
                for part, msk, what in ((f"T_bok_{tag}", (sx * Vr[:, 0] > C.X_COL_STOP + 0.1), "T_ram beyond the stop-ring face (ribs, spigot, clip)"),
                                        (f"T_klb_{tag}", (sx * Vr[:, 0] > C.X_COL_STOP + 0.1) & (rsh > 5.3), "T_ram beyond the stop-ring face, spigot excluded"),
                                        (f"T_klb_{tag}", (sx * Vr[:, 0] > C.X_COL_BOSS + 0.1) & (rsh <= 5.3), "column spigot D10 in the joint recess D10.2")):
                    best = (9e9, None)
                    for pnt in Vr[msk]:
                        d = TREE[part].find_nearest(Vector(pnt), 6.0)
                        if d[0] is not None and d[3] < best[0]:
                            best = (d[3], pnt)
                    gaps[f"{part}: {what}"] = dict(min_dist=None if best[1] is None else round(float(best[0]), 3),
                                                   at=None if best[1] is None else [round(float(q), 2) for q in best[1]], ram_vertices=int(msk.sum()))
        near.sort(key=lambda q: q["min_dist"])
        OUT["X1_vs_ram"] = dict(note="information for the integrator (cross-module K2 is not a module check): OBAL STLs against the RAM STLs "
                                     "found in stl/ at the time of the run", ram_parts=len(rnames),
                                overlaps=[dict(a=r["a"], b=r["b"], tri_pairs=r["tri_pairs"], common_mm3=r["common_mm3"], half_depth=r.get("max_half_depth"),
                                               clusters=r.get("clusters", [])[:4], intended=r["intended"]) for r in xr],
                                ram_column_gap=gaps, nearest=near[:40])
        print("X1 column gaps", json.dumps(gaps)[:1500], flush=True)
        print("X1 done", len(xr), "touching pairs; nearest:", [(q["a"], q["b"], q["min_dist"]) for q in near[:14]], round(time.time() - T0, 1), flush=True)

if "F1" in WANT:
    CENT = {}

    def min_gap(a, b, mask_a=None, cap=3.0):
        """smallest distance from the vertices of a (optionally masked) to the surface of b"""
        if a not in CENT:
            CENT[a] = np.concatenate([VERTS[a], np.array([tuple(f.calc_center_median()) for f in BM[a].faces])])
        V = CENT[a]                                       # vertices + triangle centroids (cylinders have vertices only at their ends)
        if mask_a is not None:
            V = V[mask_a(V)]
        best = (9e9, None)
        for pnt in V:
            d = TREE[b].find_nearest(Vector(pnt), cap)
            if d[0] is not None and d[3] < best[0]:
                best = (d[3], pnt)
        return dict(min=None if best[1] is None else round(float(best[0]), 3), at=None if best[1] is None else [round(float(q), 2) for q in best[1]])
    sy, sz = C.SH_Y, C.SH_Z
    f1 = {
        "door <-> centre band (all): seam 0.25, ledge 0.2, hooks": min_gap("T_dvere", "T_stred"),
        "door hooks (z > -11.9) <-> wall": min_gap("T_dvere", "T_stred", lambda V: V[:, 2] > -11.9),
        "frame magnets <-> door magnets (air gap 0.2)": min_gap("magnet_dvierka_1", "magnet_zarubna_1"),
        "door boss <-> magnet pad of the frame": min_gap("T_dvere", "T_stred", lambda V: (np.abs(V[:, 0]) > 20) & (np.abs(V[:, 2] + 24) < 4.5)),
        "cap seam lip <-> centre band (0.15)": min_gap("T_bok_L", "T_stred", lambda V: V[:, 0] < C.X_BAND),
        "cap edge <-> band edge (seam 0.5)": min_gap("T_bok_L", "T_stred", lambda V: V[:, 0] > C.X_CAP - 0.01),
        "joint body <-> socket bore (0.5)": min_gap("T_klb_L", "T_bok_L", lambda V: V[:, 0] > C.X_SEAT + 0.3),
        "joint neck <-> seat-flange hole (0.25)": min_gap("T_klb_L", "T_bok_L", lambda V: (V[:, 0] < C.X_SEAT - 0.05) & (np.hypot(V[:, 1] - sy, V[:, 2] - sz) > 10.9)),
        "light guide plug <-> bar opening (0.2)": min_gap("T_svetlovod", "T_stred", lambda V: V[:, 1] < -37.6),
        "grille plug <-> slot (0.2)": min_gap("T_mriezka", "T_stred", lambda V: V[:, 1] < -38.3),
        "LED holder <-> centre band": min_gap("T_drziak_led", "T_stred"),
        "LED holder <-> light guide": min_gap("T_drziak_led", "T_svetlovod"),
        "LED holder <-> speaker ring": min_gap("T_drziak_led", "T_drziak_repro"),
        "speaker <-> its 3 boss scallops (0.15)": min_gap("reproduktor", "T_stred"),
        "speaker <-> grille flange": min_gap("reproduktor", "T_mriezka"),
        "gasket <-> grille flange": min_gap("tesnenie_repro", "T_mriezka"),
        "bush <-> joint bore (0.025)": min_gap("T_puzdro_L", "T_klb_L", lambda V: V[:, 0] > 44.3),
    }
    OUT["F1_fits_measured"] = f1
    for k, v in f1.items():
        print("   F1", k, v, flush=True)

json.dump(OUT, open(OUTF, "w"), indent=1)
print("done", sorted(OUT), round(time.time() - T0, 1))
