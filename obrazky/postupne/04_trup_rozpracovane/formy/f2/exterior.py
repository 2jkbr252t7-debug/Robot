"""NOVA mini - exterior form variant f2 "Kapsula" (torso, base, arms) - build123d 0.13.
Run:  /opt/venv/cad/bin/python /tmp/claude-0/gapwf/fin/T1/forma/f2/exterior.py   -> cad/*.step, stl/*.stl, parts.json
World mm, Z up, floor z = 0, FRONT = -Y, robot RIGHT = -X.  All parts in WORLD position, rest pose (J1 = 0, arms 0).

Construction (see shape.py for the analytic section functions):
  every visible white surface = Solid.make_loft through closed periodic splines (SEC_N points evenly spaced in arc
  length) at stations <= 1.5 mm apart along the profile arc; flat ends (torso bottom, base foot seam, dish floor) are
  made tangent by extra sections IN the end plane (head_common recipe).  Shells = outer - offset(outer, -WALL); every
  cut / split comes after the offset.  Dark trim parts (collar trim ring, jewel ring, shoulder caps, foot) are small
  revolved / extruded parts with edge rounds."""
import sys, os, math, json, time, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shape as S
from build123d import (Vector, Wire, Edge, Solid, Compound, Box, Cylinder, Pos, Rot, Axis, Plane, Face, Location,
                       offset, fillet, extrude, revolve, export_step, export_stl, Torus, Sketch, BuildSketch,
                       Polyline, make_face, BuildLine, mirror)

OUT = os.path.dirname(os.path.abspath(__file__))
SEC_N = 160          # points per section (arc-length spaced)
DS = 1.5             # loft station spacing along the profile arc (mm)
WALL = 2.0           # shell wall (normal offset)
SEAM = 0.5           # parting-line gap
ARM_SEC_N = 144


# ================================================================================================ generic helpers
def cached(name, fn, *keys):
    """BREP disk cache keyed by the given parameters + the source of the shape functions they depend on (lofts,
    offsets and booleans of the fine lofts take minutes).  keys may contain functions (their source is hashed)."""
    import hashlib, inspect
    from build123d import import_brep, export_brep
    parts = [str(SEC_N), str(DS), str(WALL), str(ARM_SEC_N)]
    for k in keys:
        parts.append(inspect.getsource(k) if callable(k) else json.dumps(k, sort_keys=True, default=str))
    h = hashlib.md5("|".join(parts).encode()).hexdigest()[:10]
    fn_ = f"{OUT}/tmp/cache_{name}_{h}.brep"
    if os.path.exists(fn_):
        return one(import_brep(fn_))
    s = fn()
    export_brep(s, fn_)
    return s


def wire_3d(P):
    V = [Vector(*p) for p in P]
    n = len(V)
    return Wire([Edge.make_spline(V, periodic=True, parameters=[i / n for i in range(n + 1)])])


def loft_rings(rings):
    return one(Solid.make_loft([wire_3d(r) for r in rings]))


def offset_rings(rings, d):
    """move every ring point by -d along the surface normal (finite differences along the ring and across rings;
    rings ordered bottom -> top, points CCW seen from +Z, so n = t_ring x t_across points outward)"""
    import numpy as np
    R = np.array(rings, dtype=float)                     # (m, n, 3)
    m, n, _ = R.shape
    tu = np.roll(R, -1, axis=1) - np.roll(R, 1, axis=1)
    tv = np.empty_like(R)
    tv[1:-1] = R[2:] - R[:-2]
    tv[0] = R[1] - R[0]
    tv[-1] = R[-1] - R[-2]
    N = np.cross(tu, tv)
    L = np.linalg.norm(N, axis=2, keepdims=True)
    N = N / np.maximum(L, 1e-12)
    # end rings lie in a plane: use the plane normal (outward = away from the neighbouring ring)
    for i, j in ((0, 1), (m - 1, m - 2)):                 # (the end rings sit in the flat end planes)
        N[i] = np.array([0.0, 0.0, 1.0 if N[j, :, 2].mean() > 0 else -1.0])
    Q = R - d * N
    return [[tuple(p) for p in ring] for ring in Q]


def boff(s, d):
    """offset by -d, then convert the OCC offset surfaces to B-splines (booleans on Geom_OffsetSurface faces
    silently return wrong volumes - verified: half of the inner solid came out 15 % too small)"""
    from OCP.ShapeCustom import ShapeCustom
    o = offset(s, amount=-d)
    return one(Solid(ShapeCustom.ConvertToBSpline_s(one(o).wrapped, True, True, True, False)))


TK = (S.T, S.torso_profile_dense, S.torso_section_pts, S.dimple, S.se_dense, S.arc_resample, S.stations_from_profile)
BK = (S.B, S.base_profile_dense, S.smooth5, S.se_dense, S.arc_resample, S.stations_from_profile)
AK = (S.A, S.arm_params, S._half_se, S.arm_section_pts, S.arm_profile_dense, S.se_close, S.smooth5, S.arc_resample,
      S.stations_from_profile)


def wire_xy(pts, z):
    V = [Vector(x, y, z) for x, y in pts]
    n = len(V)
    return Wire([Edge.make_spline(V, periodic=True, parameters=[i / n for i in range(n + 1)])])


def one(s):
    if hasattr(s, "solids"):
        sl = s.solids()
        if len(sl) == 1:
            return Solid(sl[0].wrapped)
        if len(sl) > 1:
            sl = sorted(sl, key=lambda q: -q.volume)
            return Solid(sl[0].wrapped)
    return s


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def zcyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def xcyl(r, x0, x1, y, z):
    x0, x1 = sorted((x0, x1))
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def ycyl(r, y0, y1, x, z):
    y0, y1 = sorted((y0, y1))
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def stadium_y(w, h, y0, y1, x, z):
    """stadium (rounded slot, full round ends) w x h in XZ, extruded along Y from y0 to y1"""
    r = h / 2
    s = box(x - w / 2 + r, x + w / 2 - r, y0, y1, z - r, z + r)
    s = s + ycyl(r, y0, y1, x - w / 2 + r, z) + ycyl(r, y0, y1, x + w / 2 - r, z)
    return one(s)


def rrect_y(w, h, r, y0, y1, x, z):
    b = box(x - w / 2, x + w / 2, y0, y1, z - h / 2, z + h / 2)
    return fillet(b.edges().filter_by(Axis.Y), r)


def rrect_z(w, h, r, z0, z1, x, y):
    b = box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1)
    return fillet(b.edges().filter_by(Axis.Z), r)


def chk(name, s):
    bb = s.bounding_box()
    print(f"  {name:22s} valid={s.is_valid} vol={s.volume:10.1f}  x {bb.min.X:7.2f}..{bb.max.X:7.2f}  "
          f"y {bb.min.Y:7.2f}..{bb.max.Y:7.2f}  z {bb.min.Z:7.2f}..{bb.max.Z:7.2f}", flush=True)
    return s


def se_prism_z(a, b, n, z0, z1, count=160):
    pts = S.arc_resample(S.se_dense(a, b, n), count)
    w = wire_xy(pts, z0)
    return extrude(Face(w), amount=z1 - z0)


# ================================================================================================ TORSO
@functools.lru_cache(None)
def torso_outer():
    return cached("torso_outer", _torso_outer, *TK)


@functools.lru_cache(None)
def torso_rings():
    prof = S.torso_profile_dense()
    st = S.stations_from_profile(prof, DS)
    rings = []
    r0 = S.T["r_bot"]
    for k in (4.0, 3.0, 2.0, 1.0):                       # flat bottom: sections IN the plane z_b (G1/G2 to the belly)
        rings.append([(x, y, S.T["z_b"]) for x, y in S.torso_section_pts(r0 - k, r0 - k, 2.0, S.T["z_b"], SEC_N)])
    for z, a, b, n in st:
        rings.append([(x, y, z) for x, y in S.torso_section_pts(a, b, n, z, SEC_N)])
    r1 = S.T["r_top"]
    for k in (1.0, 2.0, 3.0, 4.0):                       # white top: sections IN the plane z_t (inside the collar hole)
        rings.append([(x, y, S.T["z_t"]) for x, y in S.torso_section_pts(r1 - k, r1 - k, 2.0, S.T["z_t"], SEC_N)])
    return rings


def _torso_outer():
    return loft_rings(torso_rings())


@functools.lru_cache(None)
def torso_inner():
    return cached("torso_inner", lambda: loft_rings(offset_rings(torso_rings(), WALL)), *TK, offset_rings)


TORSO_HOLE_R = 30.6                     # white top hole (black trim ring r 28.35..30.8 + 0.4 seam... see trim_ring)
POCKET_R, POCKET_X = 13.5, 37.5         # shoulder pocket (envelope.json)
LIGHT_T = dict(w=36.0, h=4.5, z=101.5)
GRILLE = dict(w=30.0, h=3.0, z=83.5)
SPLIT_Y = 2.0                           # front panel / rear shell parting plane (through the shoulder axis)


@functools.lru_cache(None)
def torso_shell():
    return cached("torso_shell", _torso_shell, *TK, offset_rings, _torso_shell, TORSO_HOLE_R, POCKET_R, POCKET_X, LIGHT_T, GRILLE)


def _torso_shell():
    sh = one(torso_outer() - torso_inner())
    cut = zcyl(TORSO_HOLE_R, 120.0, 140.0)
    for sx in (-1, 1):
        cut = cut + xcyl(POCKET_R, sx * 33.0, sx * 60.0, S.T["SHY"], S.T["SHZ"])     # clean through the wall
    cut = cut + zcyl(7.0, 38.0, 48.0, -18.0, 0.0)                                  # J1 spline through the floor
    cut = cut + stadium_y(LIGHT_T["w"] + 0.3, LIGHT_T["h"] + 0.3, -50, -30, 0.0, LIGHT_T["z"])
    cut = cut + stadium_y(GRILLE["w"] + 0.3, GRILLE["h"] + 0.3, -50, -30, 0.0, GRILLE["z"])
    return one(sh - cut)


@functools.lru_cache(None)
def torso_split():
    sh = torso_shell()
    front = one(sh & box(-80, 80, -80, SPLIT_Y - SEAM / 2, 0, 200))
    rear = one(sh & box(-80, 80, SPLIT_Y + SEAM / 2, 80, 0, 200))
    return front, rear


@functools.lru_cache(None)
def torso_outer_off(d):
    return cached(f"torso_off{d}", lambda: loft_rings(offset_rings(torso_rings(), d)), *TK, offset_rings)


def insert_y(w, h, z, recess, depth, kind="stadium"):
    """light guide / grille insert in a front slot: flush - recess with the torso outer surface, `depth` deep"""
    pr = stadium_y(w, h, -60, -20, 0.0, z)
    return one((pr & torso_outer_off(recess)) - torso_outer_off(recess + depth))


def trim_ring():
    """black collar trim ring = the flat collar plateau r <= 29.8 at z 133 (B-verified), quarter round R1 down to
    z 132 at r 30.8 (= white top level), flange under the white top wall; the B collar ring is glued inside r 28.35"""
    pts = [(28.35, 128.4), (32.6, 128.4), (32.6, 129.6), (30.8, 129.6), (30.8, 133.0), (28.35, 133.0)]
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    s = revolve(sk.sketch, axis=Axis.Z)
    s = one(s)
    # select the outer top circle (r 30.8, z 133)
    sel = []
    for ed in s.edges():
        bb = ed.bounding_box()
        if abs(bb.max.Z - 133.0) < 1e-4 and abs(bb.min.Z - 133.0) < 1e-4 and bb.max.X > 30.5:
            sel.append(ed)
    s = fillet(sel, 0.98)
    return one(s)


def jewel_ring():
    """dark glossy ring under the torso (rotates with J1): r 20.5..36, z 41..43, full-round outer edge"""
    s = zcyl(36.0, 41.0, 43.0) - zcyl(20.5, 40.0, 44.0)
    s = one(s)
    sel = [ed for ed in s.edges() if ed.bounding_box().max.X > 35.9]
    s = one(fillet(sel, 0.98))
    s = one(s - zcyl(10.8, 40.0, 44.0, -18.0, 0.0))                                  # J1 pinion orbit (pack)
    return s


# ================================================================================================ BASE
@functools.lru_cache(None)
def base_outer():
    return cached("base_outer", _base_outer, *BK)


@functools.lru_cache(None)
def base_rings():
    prof = S.base_profile_dense()
    st = S.stations_from_profile(prof, DS)
    rings = []
    af, bf, nf = S.B["a_f"], S.B["b_f"], S.B["n_f"]
    for k in (4.0, 3.0, 2.0, 1.0):                        # flat foot-seam plane (tangent continuation inward)
        rings.append([(x, y, S.B["z_f"]) for x, y in S.arc_resample(S.se_dense(af - k, bf - k, nf), SEC_N)])
    for z, a, b, n in st:
        rings.append([(x, y, z) for x, y in S.arc_resample(S.se_dense(round(a, 9), round(b, 9), round(n, 9)), SEC_N)])
    rd = S.B["r_d"]
    for k in (1.0, 2.0, 3.0, 4.0):                        # flat dish floor
        rings.append([(x, y, S.B["z_d"]) for x, y in S.arc_resample(S.se_dense(rd - k, rd - k, 2.0), SEC_N)])
    return rings


def _base_outer():
    return loft_rings(base_rings())


@functools.lru_cache(None)
def base_inner():
    return cached("base_inner", lambda: loft_rings(offset_rings(base_rings(), WALL)), *BK, offset_rings)


FOOT = dict(z0=6.0, z1=S.B["z_f"], a=S.B["a_f"] - 0.5, b=S.B["b_f"] - 0.5, n=S.B["n_f"])
# packaging shifts (<= 3 mm, documented in forma.md): ToF 2.0 forward, USB-C 1.5 back, switch 1.0 back
SHIFT = {"Z_ToF": (0, -1.5, 0), "Z_USB_C": (0, 1.5, 0), "Z_vypinac": (0, 1.0, 0),
         "T_riadenie": (0, 0, 3.0), "T_zosilnovac": (1.5, 0, 3.0)}      # boards 3 mm up: room for the egg belly
BAY = dict(x=34.25, y0=6.5, y1=45.5, r=5.0)
SH = dict(usb=(0.0, 33.2), sw=(18.0, 27.5), led=(-11.0, 33.2))      # back openings (x, z)
TOF = dict(w=14.0, h=6.0, r=2.9, z=28.5)            # dark IR window (VL53L1X apertures ~ 5 x 2.5)
LIGHT_B = dict(w=44.0, h=4.0, z=20.0)


LIP_Z = 12.5                            # below this the base shell is a solid flange ring outside the bottom opening


@functools.lru_cache(None)
def base_inner_eff():
    """inner void of the base shell: the ring-offset inner, but not in the flange zone below LIP_Z outside the bottom
    opening (the lower roll meets the foot seam there; the offset loft left only 1.37 mm in the corners)"""
    opening = se_prism_z(S.B["a_f"] - 2.6, S.B["b_f"] - 2.6, S.B["n_f"], 0.0, LIP_Z + 0.01)
    flange = one(box(-90, 90, -70, 70, 0.0, LIP_Z) - opening)
    return cached("base_inner_eff", lambda: one(base_inner() - flange), *BK, offset_rings, LIP_Z)


@functools.lru_cache(None)
def base_shell():
    return cached("base_shell", _base_shell, *BK, offset_rings, LIP_Z, _base_shell, FOOT, BAY, SH, TOF, LIGHT_B)


def _base_shell():
    sh = one(base_outer() - base_inner_eff())
    cut = se_prism_z(S.B["a_f"] - 2.6, S.B["b_f"] - 2.6, S.B["n_f"], 0.0, S.B["z_f"] + 4.0)   # open bottom, 2.6 lip
    cut = cut + zcyl(29.0, 34.0, 44.0)                                                         # J1 top opening
    cut = cut + rrect_y(TOF["w"] + 0.3, TOF["h"] + 0.3, TOF["r"], -70, -40, 0.0, TOF["z"])
    cut = cut + stadium_y(LIGHT_B["w"] + 0.3, LIGHT_B["h"] + 0.3, -70, -40, 0.0, LIGHT_B["z"])
    cut = cut + stadium_y(9.5, 3.8, 40, 70, SH["usb"][0], SH["usb"][1])
    cut = cut + ycyl(3.5, 40, 70, SH["sw"][0], SH["sw"][1])
    cut = cut + ycyl(1.3, 40, 70, SH["led"][0], SH["led"][1])
    return one(sh - cut)


@functools.lru_cache(None)
def base_outer_off(d):
    return cached(f"base_off{d}", lambda: loft_rings(offset_rings(base_rings(), d)), *BK, offset_rings)


def base_insert(prism, recess, depth):
    return one((prism & base_outer_off(recess)) - base_outer_off(recess + depth))


def foot_plate():
    """dark recessed foot = bottom cover (chassis plate) with wheel slots, cliff windows and the two bay openings"""
    f = se_prism_z(FOOT["a"], FOOT["b"], FOOT["n"], FOOT["z0"], FOOT["z1"])
    try:
        sel = [e for e in f.edges() if abs(e.center().Z - FOOT["z0"]) < 1e-3]
        f = one(fillet(sel, 1.2))
    except Exception as ex:
        print("foot fillet failed", ex)
    cut = None
    for sx in (-1, 1):
        c = rrect_z(11.5, 36.0, 3.0, 0, 20, sx * 54.0, 0.0)
        cut = c if cut is None else cut + c
        for sy in (-1, 1):
            cut = cut + rrect_z(9.5, 7.5, 1.2, 0, 20, sx * 40.0, sy * 31.0)
    for sy in (-1, 1):
        y0, y1 = BAY["y0"] - SEAM, BAY["y1"] + SEAM
        cut = cut + rrect_z(2 * (BAY["x"] + SEAM), y1 - y0, BAY["r"] + SEAM, 0, 20, 0.0, sy * (y0 + y1) / 2)
    return one(f - cut)


def bay_cover(sy):
    y0, y1 = BAY["y0"], BAY["y1"]
    c = rrect_z(2 * BAY["x"], y1 - y0, BAY["r"], FOOT["z0"], FOOT["z1"], 0.0, sy * (y0 + y1) / 2)
    c = one(c - zcyl(7.0, 0, 20, 0.0, sy * 34.0))                                     # caster hole
    return c


# ================================================================================================ ARMS
def _arm_loft(s=0.0):
    prof = S.arm_profile_dense(s=s)
    st = S.stations_from_profile(prof, DS)
    rows = [r for r in st if r[5] > 1.2 and (r[3] + r[4]) > 1.2]
    first, last = rows[0], rows[-1]
    xc, yc = S.A["x_c"], S.A["y_c"]

    def sec_at(z, f=1.0):
        P = S.arm_section_pts(z, ARM_SEC_N, s=s)
        return wire_xy([(xc + (x - xc) * f, yc + (y - yc) * f) for x, y in P], z)
    secs = [sec_at(first[0], f) for f in (0.4, 0.7)]          # tiny tangent end caps (head_common recipe)
    secs += [sec_at(r[0]) for r in rows]
    secs += [sec_at(last[0], f) for f in (0.7, 0.4)]
    return one(Solid.make_loft(secs))


@functools.lru_cache(None)
def arm_outer_L():
    return cached("arm_outer", lambda: _arm_loft(0.0), *AK, _arm_loft)


@functools.lru_cache(None)
def arm_inner_L():
    """inner skin = the same loft with every body size shrunk by WALL and the end closures ending WALL earlier
    (OCC offset fails on the tiny end caps)"""
    return cached("arm_inner", lambda: _arm_loft(WALL), *AK, _arm_loft)


SERVO_A = dict(x0=46.5, x1=67.5, y0=-2.7, y1=6.7, z0=96.75, z1=117.25)


@functools.lru_cache(None)
def arm_halves_L():
    sh = one(arm_outer_L() - arm_inner_L())
    sv = SERVO_A
    win = box(40.0, 49.5, sv["y0"] - 0.2, sv["y1"] + 0.2, sv["z0"] - 0.2, sv["z1"] + 0.2)   # servo window, inner skin
    sh = one(sh - win)
    xc = S.A["x_c"]
    inner = one(sh & box(30, xc - SEAM / 2, -40, 40, 30, 140))
    outer = one(sh & box(xc + SEAM / 2, 90, -40, 40, 30, 140))
    return inner, outer


def cap_L():
    """black shoulder cap (rotates with the arm): ring r 5.9..12.5, x 44.2..46.5, rounded rim"""
    s = one(xcyl(12.5, 44.2, 46.5, S.T["SHY"], S.T["SHZ"]) - xcyl(5.9, 40, 50, S.T["SHY"], S.T["SHZ"]))
    sel = [e for e in s.edges() if e.bounding_box().size.Y > 24.0]
    try:
        s = one(fillet(sel, 0.9))
    except Exception as ex:
        print("cap fillet failed", ex)
    return s


def mirror_x(s):
    return one(s.mirror(Plane.YZ))


# ================================================================================================ build all
def build():
    t0 = time.time()
    P = {}       # name -> (solid, group, color, label)
    print("TORSO", flush=True)
    chk("torso_outer", torso_outer())
    chk("torso_inner", torso_inner())
    fr, re_ = torso_split()
    P["T_trup_predny"] = (fr, "T", "white", "trup – predný diel (magnety)")
    P["T_trup_zadny"] = (re_, "T", "white", "trup – zadná škrupina")
    P["T_lem_goliera"] = (trim_ring(), "T", "black", "čierny lem goliera (plošina r 29,8 v z 133)")
    P["T_sokel"] = (jewel_ring(), "T", "black_gloss", "tmavý lesklý prstenec pod trupom (otočný, J1)")
    P["T_svetlovod"] = (insert_y(LIGHT_T["w"], LIGHT_T["h"], LIGHT_T["z"], 0.25, 3.0), "T", "glow",
                        "svetlovod hrude (PMMA)")
    P["T_mriezka"] = (insert_y(GRILLE["w"], GRILLE["h"], GRILLE["z"], 0.5, 2.0), "T", "grey", "mriežka reproduktora")
    print("  torso done", round(time.time() - t0), flush=True)
    print("BASE", flush=True)
    chk("base_outer", base_outer())
    chk("base_inner", base_inner())
    P["Z_skrupina"] = (base_shell(), "B", "white", "podstavec – horná škrupina (oblúčik s miskou)")
    P["Z_spodok"] = (foot_plate(), "B", "black", "tmavá päta / spodný kryt")
    P["Z_kryt_bat_P"] = (bay_cover(-1), "B", "black", "kryt batérie predný (nesie guľôčku)")
    P["Z_kryt_bat_Z"] = (bay_cover(+1), "B", "black", "kryt batérie zadný (nesie guľôčku)")
    P["Z_okno_ToF"] = (base_insert(rrect_y(TOF["w"], TOF["h"], TOF["r"] - 0.15, -80, -30, 0.0, TOF["z"]), 0.3, 2.0),
                       "B", "glass", "okno ToF (tmavé IR)")
    P["Z_svetlovod"] = (base_insert(stadium_y(LIGHT_B["w"], LIGHT_B["h"], -80, -30, 0.0, LIGHT_B["z"]), 0.25, 3.0),
                        "B", "glow", "svetlovod podstavca")
    P["Z_led_nabijania"] = (base_insert(ycyl(1.15, 30, 80, SH["led"][0], SH["led"][1]), 0.2, 3.0), "B", "glow",
                            "LED nabíjania")
    print("  base done", round(time.time() - t0), flush=True)
    print("ARMS", flush=True)
    chk("arm_outer_L", arm_outer_L())
    chk("arm_inner_L", arm_inner_L())
    ai, ao = arm_halves_L()
    P["A_L_vnutorna"] = (ai, "AL", "white", "ľavé krídlo – vnútorná polovica")
    P["A_L_vonkajsia"] = (ao, "AL", "white", "ľavé krídlo – vonkajšia polovica")
    P["A_L_kryt"] = (cap_L(), "AL", "black", "ľavá ramenná čiapočka")
    P["A_R_vnutorna"] = (mirror_x(ai), "AR", "white", "pravé krídlo – vnútorná polovica")
    P["A_R_vonkajsia"] = (mirror_x(ao), "AR", "white", "pravé krídlo – vonkajšia polovica")
    P["A_R_kryt"] = (mirror_x(cap_L()), "AR", "black", "pravá ramenná čiapočka")
    print("  arms done", round(time.time() - t0), flush=True)
    for n, v in P.items():
        chk(n, v[0])
    return P


def export_all(P, fine=True):
    os.makedirs(f"{OUT}/cad", exist_ok=True)
    os.makedirs(f"{OUT}/stl", exist_ok=True)
    meta = []
    tol, ang = (0.01, 0.05) if fine else (0.05, 0.3)      # brief: <= 0.01 / 0.1 (angular tightened for reflections)
    for n, (s, g, c, lab) in P.items():
        export_step(s, f"{OUT}/cad/{n}.step")
        a_ = 0.1 if (fine and n == "Z_skrupina") else ang     # the base inner skin (crest R ~1) explodes at 0.05
        export_stl(s, f"{OUT}/stl/{n}.stl", tolerance=tol, angular_tolerance=a_)
        meta.append({"name": n, "group": g, "color": c, "label": lab, "stl": f"{OUT}/stl/{n}.stl",
                     "step": f"{OUT}/cad/{n}.step", "volume_mm3": round(s.volume, 1),
                     "mass_g_resin": round(s.volume * 1.15e-3, 1)})
        print("exported", n, flush=True)
    # surface-only solids for checks / zebra
    for n, s in (("_torso_outer", torso_outer()), ("_base_outer", base_outer()), ("_arm_outer_L", arm_outer_L())):
        export_stl(s, f"{OUT}/stl/{n}.stl", tolerance=tol, angular_tolerance=ang)
        export_step(s, f"{OUT}/cad/{n}.step")
    json.dump({"parts": meta, "note": "world frame, rest pose; groups as t1lib (T turns with J1, AR/AL swing about "
               "the shoulder axis X at y 2, z 112)"}, open(f"{OUT}/parts.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    P = build()
    export_all(P, fine="--coarse" not in sys.argv)
    print("DONE")
