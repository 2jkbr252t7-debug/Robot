"""NOVA mini - T4 torso, module OBAL (shells and everything mounted on them).

Parts (registry keys):  T_stred, T_bok_L, T_bok_P, T_dvere, T_klb_L, T_klb_P, T_puzdro_L, T_puzdro_P, T_svetlovod,
T_mriezka, T_drziak_led, T_drziak_repro + bought parts (reproduktor, tesnenie_repro, DPS_led, magnets, disc springs,
screws F8 / F13, inserts of F1).  Frame, numbers and the cached exterior come from t4_common (never redefined here).

Recipe for every shell part (keeps all booleans transversal, no slivers, no coincident loft faces):
    blank  = outer_solid & <planar / prismatic region>                (band, cap, door outline)
    cavity = inner_solid(2.2) - <primitive add-ons, NOT clipped>      (tube, bosses, socket ... cut out of the cavity)
    part   = blank - cavity                                            -> wall 2.2 + add-ons ending exactly on the wall
    part   = part - <primitive cutters>  (+ late add-ons that live inside a through opening: door ledge, magnet pads)
Every heavy step is cached as BREP in ./cache/obal_<VER>_<step>.brep (delete them or run with --rebuild after a change).

Run:   /opt/venv/cad/bin/python t4_obal.py [--rebuild] [--only name,name] [--no-export]
       -> stl/<name>.stl, step/<name>.step, parts_obal.json
"""
from __future__ import annotations
import os, sys, json, math, time, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t4_common as C                                                                                  # noqa: E402

VER = "v1"
T0 = time.time()
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(f"[obal {time.time() - T0:6.1f}s] {s}", flush=True)


# =====================================================================================================================
# 0. LOCAL constants of this module (interfaces between OBAL parts only; shared numbers live in t4_common)
# =====================================================================================================================
Z_FLARE = -6.6                  # collar tube: 45 deg gusset cone starts here (meets the wall where the tube gap is 1.0)
FLARE_AZ = ((50.0, 130.0), (230.0, 310.0))      # gussets only in the +-Y sectors (steep wall = acute crevice there)
VENT = dict(d=1.6, z=0.4)       # 2 vent holes through the collar tube into the ring seat (trough between tube and shelf)
TOP_GAP_X = 20.6                # door ledge omitted along the top edge for |x| < this (spec 18.0; hooks reach 20.25)
LEDGE_TOP_Z = -16.5             # ... above this height
HOOK = dict(x=16.0, z=-12.0, tab_u=4.0, tab_w=(2.5, 3.6), tab_v=(-1.5, 3.3), root_u=4.25, root_w=3.8, root_v=(-2.05, 3.0))
PAD = dict(r=4.0, w=(4.7, 7.2), arm_u=5.9, riser_u=(3.6, 5.9), pocket_d=5.1, pocket_depth=2.1, push_d=1.5)
DBOSS = dict(r=4.0, w=4.5, pocket_d=5.1, pocket_depth=2.1)       # door magnet boss (face at inset 4.5)
NOTCH = dict(w=12.0, h=1.2, depth_y=0.85)                         # finger-nail notch in the door's bottom edge
BOSS_FACE_LED = -31.4           # LED boss face (spec -33.0: a 5 mm pilot would break through the 2.2 wall there)
PILOT_LED = 4.3                 # pilot depth in the LED bosses (remaining skin >= 1.2)
SPK_AZ = (30.0, 150.0, 270.0)   # speaker bosses (spec 90 / 210 / 330: the 90 deg boss sits inside the LED box)
SPK_SEAT_D = 28.3
FLANGE_GUIDE = (33.6, 8.0, 1.2, 1.5)      # light-guide flange w x h x t, corner r (spec 35 wide: hits the LED bosses)
FLANGE_GRILLE = (23.0, 5.2)               # grille flange pill (inside the gasket ID 24), flat back at Y_GRILLE_BACK
Y_GRILLE_BACK = -36.7
GRILLE_SLOTS = dict(n=5, w=0.8, h=1.8, pitch=3.6)
HOLDER = dict(x=16.8, z=(C.Z_BAR - 3.5, C.Z_BAR + 3.5), y_back=-30.1, front_inset=3.5,
              chan_back=(14.4, 1.5), chan_front=(15.5, 2.1), rebate=(15.15, 2.1, 0.8),
              ear=dict(x=(15.3, 22.3), t=2.0, z=3.0))
RING = dict(ri=13.0, ro=16.0, t=1.6, ear_r=2.6, flat_z=-36.3)     # speaker clamp ring (flat top under the LED holder)
GASKET = dict(ri=11.9, ro=14.0)
LIP = dict(clear=0.15, t=1.6, x_tip=C.X_CAP - 2.5, x_root=C.X_CAP + 0.4, z_bot=-77.7, root_w=4.3, root_x=(C.XS - 0.3, C.X_CAP + 0.75))
KEY = dict(w=2.9, r=(7.0, 10.9), h=1.4)                           # anti-rotation key of T_klb (column slot 3.0 x 1.5 at az 0)
SEAT_NOTCH_R = 14.0             # wire notch in the cap seat flange (spec 13.2; 14.0 lets the wires pass the stop ring r 12.8)
BUSH = dict(d=8.0, x=(44.0, C.X_KLB_END - 0.006), flange=(10.0, 42.0, 44.0), blind=(4.0, 6.0))
SPRING = dict(do=10.0, di=5.2, t=0.5, x=(41.0, 41.5, 42.0))
SPEAKER_MASS, GASKET_MASS = 6.0, 0.05

bd = None


def _init():
    global bd
    if bd is None:
        bd = C._bd()
    return bd


# =====================================================================================================================
# 1. numeric helpers on the analytic exterior
# =====================================================================================================================
def F_outer(P):
    P = np.atleast_2d(P).astype(float)
    d = C.TOP - P[:, 2]
    a = np.interp(d, C.PD, C.PA); b = np.interp(d, C.PD, C.PB); n = np.interp(d, C.PD, C.PN)
    return (np.abs(P[:, 0]) / a) ** n + (np.abs(P[:, 1]) / b) ** n - 1.0


def normal(P, h=(1e-3, 1e-3, 0.08)):
    """outward unit normal(s) of the exterior side surface at point(s) P"""
    P = np.atleast_2d(P).astype(float); g = np.zeros_like(P)
    for k in range(3):
        e = np.zeros(3); e[k] = h[k]
        g[:, k] = (F_outer(P + e) - F_outer(P - e)) / (2 * h[k])
    return g / np.linalg.norm(g, axis=1)[:, None]


def frame(x, z, side):
    """point on the exterior at (x, z) on the front (side -1) / back (+1) wall: (p, n outward, u horizontal (+x), v up)"""
    p = np.array([x, C.y_surface(x, z, side), z], float)
    n = normal(p)[0]
    u = np.cross(n, [0, 0, 1.0]); u /= np.linalg.norm(u)
    if u[0] < 0:
        u = -u
    v = np.cross(u, n)
    if v[2] < 0:
        v = -v
    return p, n, u, v


def loc_frame(x, z, side):
    """build123d Location of the local frame (X = u along the wall, Y = v up the wall, Z = w = INSET depth)"""
    _init()
    p, n, u, v = frame(x, z, side)
    pl = bd.Plane(origin=tuple(p), x_dir=tuple(u), z_dir=tuple(-n))
    # make sure the local Y axis is v (up); for the front wall u x (-n) flips, then mirror u
    if np.dot(np.array(tuple(pl.y_dir)), v) < 0:
        pl = bd.Plane(origin=tuple(p), x_dir=tuple(-u), z_dir=tuple(-n))
    return pl.location


def lbox(loc, u0, u1, v0, v1, w0, w1):
    return loc * C.box(u0, u1, v0, v1, w0, w1)


def lcyl(loc, r, w0, w1, u=0.0, v=0.0):
    return loc * C.cyl_z(r, w0, w1, u, v)


def seam_outline(w, x=C.X_BAND, count=144, zc=-42.0):
    """closed outline (count, 2) = (y, z) of the region 'inside the exterior AND at least w from it' in the plane x.
    Polar about (y 0, z zc); used for the straight-extruded seam lips of the side caps."""
    ph = np.linspace(0, 2 * np.pi, count, endpoint=False)
    c, s = np.cos(ph), np.sin(ph)

    def ok(rho):
        Q = np.stack([np.full(count, x), rho * c, zc + rho * s], 1)
        return C.inside_outer(Q) & (C.dist_outer(Q) >= w)
    lo = np.zeros(count); hi = np.full(count, 70.0)
    assert ok(lo + 1.0).all()
    for _ in range(40):
        mid = 0.5 * (lo + hi); m = ok(mid)
        lo = np.where(m, mid, lo); hi = np.where(m, hi, mid)
    rho = 0.5 * (lo + hi)
    return np.stack([rho * c, zc + rho * s], 1)


def pan_keep_r(z):
    """radius static parts must stay outside of at height z (PAN_ENV + 1.0), None below / above the table"""
    for z0, z1, r in C.PAN_ENV:
        if z0 <= z <= z1:
            return r + 1.0
    return None


# =====================================================================================================================
# 2. CAD helpers
# =====================================================================================================================
def K(name, fn):
    """cached step (BREP in ./cache)"""
    return C.cached(f"obal_{VER}_{name}", fn, verbose=True)


def one(s):
    _init()
    sol = s.solids()
    if len(sol) == 1:
        return sol[0]
    sol = sorted(sol, key=lambda q: -q.volume)
    if len(sol) > 1 and sol[1].volume > 1e-3:
        log(f"   WARNING: boolean gave {len(sol)} solids, volumes {[round(q.volume, 3) for q in sol[:5]]} - keeping the largest")
    return sol[0]


def step(name, fn):
    t = time.time()
    s = K(name, fn)
    log(f"step {name:26s} {time.time() - t:6.1f} s  solids {len(s.solids())}  vol {s.volume:10.1f}  valid {s.is_valid}")
    return s


def fuse_all(shapes):
    s = shapes[0]
    return s.fuse(*shapes[1:]) if len(shapes) > 1 else s


def wedge(az0, az1, z0, z1, R=90.0):
    _init()
    p = [bd.Vector(0, 0, z0)] + [bd.Vector(R * math.cos(math.radians(a)), R * math.sin(math.radians(a)), z0) for a in (az0, az1)]
    return bd.extrude(bd.Face(bd.Wire.make_polygon(p, close=True)), amount=z1 - z0)


def prism_x(outline_yz, x0, x1):
    """closed outline (n, 2) of (y, z) points -> periodic spline -> prism from x0 to x1"""
    _init()
    w = bd.Wire([bd.Edge.make_spline([bd.Vector(x0, y, z) for y, z in outline_yz], periodic=True)])
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def poly_prism_x(pts_yz, x0, x1):
    _init()
    w = bd.Wire.make_polygon([bd.Vector(x0, y, z) for y, z in pts_yz], close=True)
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def vpill_y(w, h, x, z, y0, y1):
    """vertical stadium w wide (x) x h tall (z), extruded along y"""
    r = w / 2
    return C.box(x - r, x + r, y0, y1, z - h / 2 + r, z + h / 2 - r) + C.cyl_y(r, y0, y1, x, z - h / 2 + r) + C.cyl_y(r, y0, y1, x, z + h / 2 - r)


def mirror_x(s):
    _init()
    return bd.mirror(s, about=bd.Plane.YZ)


def spk_boss_xz():
    return [(C.SPK_BOSS["pcd_r"] * math.cos(math.radians(a)), C.SPEAKER["z"] + C.SPK_BOSS["pcd_r"] * math.sin(math.radians(a))) for a in SPK_AZ]


def klb_yz(az, r):
    return C.SH_Y + r * math.cos(math.radians(az)), C.SH_Z + r * math.sin(math.radians(az))


# =====================================================================================================================
# 3. T_stred  (centre band)
# =====================================================================================================================
def _stred_adds():
    """primitive add-ons that are cut out of the cavity (so they end exactly on the wall)"""
    _init()
    A = [C.cyl_z(C.R_TUBE, C.Z_BORE_BOT, 3.0)]                                           # collar tube (solid, bore later)
    cone = bd.Pos(0, 0, (Z_FLARE + 3.0) / 2) * bd.Cone(C.R_TUBE, C.R_TUBE + (3.0 - Z_FLARE), 3.0 - Z_FLARE)
    for a0, a1 in FLARE_AZ:
        A.append(cone & wedge(a0, a1, -12.0, 5.0))                                       # +-Y gussets
    r, (zb, zt) = C.BOSS_STRED["r"], C.BOSS_STRED["z"]
    for x, y in C.SCR_STRED:                                                             # 4 screw bosses
        sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
        A.append(C.cyl_z(r, zb - 2.0, zt, x, y))
        A.append(bd.Pos(x, y, zt + 1.4) * bd.Cone(r, 0.4, 2.8))                          # printable top (no flat overhang)
        xw = x + 0.5 * sx                                                                # web 2.0 thick, clear of the door
        A.append(poly_prism_x([(y, zb - 2.0), (y, zt), (y + 30 * sy, zt + 30), (y + 30 * sy, zb - 2.0)], xw - 1.0, xw + 1.0))
        ya, yb = sorted((y, y + 26 * sy))
        A.append(C.box(x - r, x + r, ya, yb, zb - 2.0, zb + 1.6))                        # crevice fill at the lip
    for x, z in C.LED_BOSS:                                                              # LED-holder bosses
        A.append(C.cyl_y(2.5, -50.0, BOSS_FACE_LED, x, z))
    for x, z in spk_boss_xz():                                                           # speaker bosses
        A.append(C.cyl_y(2.5, -50.0, C.SPEAKER["y"][1], x, z))
    return A


def _stred_cuts():
    _init()
    cuts = [C.cyl_z(C.R_BORE, C.Z_BORE_BOT - 0.1, C.TOP + 0.1),
            bd.Pos(0, 0, C.Z_BORE_BOT + 0.2) * bd.Cone(C.R_BORE + 0.6, C.R_BORE, 0.6),                     # 0.5 x 45 lead-in
            C.door_prism(C.SEAM / 2),
            C.pill_prism_y(*C.BAR, 0, C.Z_BAR, -60, -34.0),
            C.pill_prism_y(*C.SLOT, 0, C.Z_SLOT, -60, -34.0),
            C.box(C.LIP_RELIEF["x"][0], C.LIP_RELIEF["x"][1], -C.LIP_RELIEF["y_min"], -20.0, C.Z_WHITE - 0.1, -79.5),
            C.cyl_x(VENT["d"] / 2, -32.0, 32.0, 0.0, VENT["z"])]
    for x, y in C.SCR_STRED:
        cuts.append(C.insert_hole("M2.5", (x, y, C.Z_WHITE), "z", 1, mat="resin"))
    for x, z in C.LED_BOSS:
        cuts.append(C.cyl_y(0.85, BOSS_FACE_LED - PILOT_LED, BOSS_FACE_LED + 0.1, x, z))
    for x, z in spk_boss_xz():
        cuts.append(C.cyl_y(0.85, C.SPEAKER["y"][1] - 5.0, C.SPEAKER["y"][1] + 0.1, x, z))
        cuts.append(C.cyl_y(SPK_SEAT_D / 2, C.SPEAKER["y"][0] - 0.15, C.SPEAKER["y"][1] + 0.1, 0.0, C.SPEAKER["z"]) &
                    C.cyl_y(2.6, -50, -20, x, z))                                                          # seat D28.3 scallop
    return cuts


def _pad(x, z):
    """static magnet pad of the door frame for x > 0 (mirror for x < 0): disc + arm + riser to the wall, pocket open to the door"""
    L = loc_frame(x, z, +1)
    w0, w1 = PAD["w"]
    s = lcyl(L, PAD["r"], w0, w1) + lbox(L, 0.0, PAD["arm_u"], -PAD["r"], PAD["r"], w0, w1) + \
        lbox(L, PAD["riser_u"][0], PAD["riser_u"][1], -PAD["r"], PAD["r"], 0.9, w1)
    s = s - lcyl(L, PAD["pocket_d"] / 2, w0 - 0.5, w0 + PAD["pocket_depth"]) - lcyl(L, PAD["push_d"] / 2, w0, w1 + 0.5)
    for z0, z1, r in C.PAN_ENV:                                                          # stay 1.0 outside the pan sweep
        if z1 > z - 6 and z0 < z + 6:
            s = s - C.cyl_z(r + 1.0, z0, z1)
    return one(s)


def _ledge_parts():
    """door frame ledge (tested recipe of the spec): inside part 2.4..4.0 behind the door rim, outside part 2.0..4.0 on the wall"""
    i20, i24, i40 = C.inner_solid(2.0), C.inner_solid(2.4), C.inner_solid(4.0)
    ring_in = C.door_prism(C.SEAM / 2) - C.door_prism(C.SEAM / 2 - C.DOOR_LEDGE["inside"])
    ring_out = C.door_prism(C.SEAM / 2 + C.DOOR_LEDGE["outside"]) - C.door_prism(C.SEAM / 2)
    gap = C.box(-TOP_GAP_X, TOP_GAP_X, 5, 60, LEDGE_TOP_Z, 0.0)
    lin = step("ledge_in0", lambda: one((ring_in & i24) - i40))
    lout = step("ledge_out0", lambda: one((ring_out & i20) - i40))

    def trim_in():
        s = lin - gap
        for x, z in C.DOOR_MAGNETS["xz"]:                                                # scallops around the door bosses
            s = s - lcyl(loc_frame(x, z, +1), DBOSS["r"] + 0.3, 1.5, DBOSS["w"] + 0.3)
        return s

    lin2 = step("ledge_in1", trim_in)
    lout2 = step("ledge_out1", lambda: lout - gap)
    return lin2, lout2


def build_stred():
    _init()
    blank = step("stred_outer", lambda: one(C.outer_solid() & C.box(-C.X_BAND, C.X_BAND, -80, 80, C.Z_WHITE, C.TOP + 5)))
    cav = step("stred_cavity", lambda: one(C.inner_solid(C.WALL).cut(*_stred_adds())))
    s2 = step("stred_shell", lambda: one(blank - cav))
    s3 = step("stred_cut", lambda: one(s2.cut(*_stred_cuts())))

    def pads():
        P = []
        for x, z in C.DOOR_MAGNETS["xz"]:
            p = _pad(abs(x), z)
            P.append(p if x > 0 else mirror_x(p))
        return one(s3.fuse(*P))
    s4 = step("stred_pads", pads)
    lin, lout = _ledge_parts()
    s5 = step("stred_ledge", lambda: one(s4.fuse(*lin.solids(), *lout.solids())))
    return s5


# =====================================================================================================================
# 4. T_bok_L / T_bok_P  (side caps)
# =====================================================================================================================
_LIPMEMO = {}


def _lip_prisms():
    """continuous seam lip of the LEFT cap: straight extrusion along X of the band's inner edge outline (plane x = X_BAND)
    moved 0.15 inward, 1.6 thick, from x 31.05 into the cap; root block inside the cap wall"""
    if "v" in _LIPMEMO:
        return _LIPMEMO["v"]
    o_out = seam_outline(C.WALL + LIP["clear"])
    o_in = seam_outline(C.WALL + LIP["clear"] + LIP["t"])
    o_root = seam_outline(LIP["root_w"])
    zcut = C.box(-90, 90, -90, 90, LIP["z_bot"], 20)
    lip = (prism_x(o_out, LIP["x_tip"], LIP["x_root"]) - prism_x(o_in, LIP["x_tip"] - 1, LIP["x_root"] + 1)) & zcut
    root = (C.box(LIP["root_x"][0], LIP["root_x"][1], -60, 60, LIP["z_bot"], 20) - prism_x(o_root, LIP["root_x"][0] - 1, LIP["root_x"][1] + 1))
    _LIPMEMO["v"] = (one(lip), one(root))
    return _LIPMEMO["v"]


def build_bok_L():
    _init()
    sy, sz = C.SH_Y, C.SH_Z
    blank = step("bokL_outer", lambda: one(C.outer_solid() & C.box(C.X_CAP, 80, -80, 80, C.Z_WHITE, C.TOP + 5)))
    lip, root = step("bokL_lip", lambda: _lip_prisms()[0]), step("bokL_root", lambda: _lip_prisms()[1])
    cav = step("bokL_cavity", lambda: one(C.inner_solid(C.WALL).cut(C.cyl_x(16.0, C.X_COL_STOP, 70.0, sy, sz), root)))
    s2 = step("bokL_shell", lambda: one(blank - cav))

    def cuts():
        yn, zn = klb_yz(C.KLB_WIRE["az"], 0.0)
        notch = C.box(C.X_COL_STOP - 0.2, C.X_SEAT + 0.2, sy - C.KLB_WIRE["notch_w"] / 2, sy + C.KLB_WIRE["notch_w"] / 2,
                      sz - SEAT_NOTCH_R, sz - C.R_SEAT_HOLE + 1.0)
        return one(s2.cut(C.cyl_x(C.R_SOCKET, C.X_SEAT, 70.0, sy, sz), C.cyl_x(C.R_SEAT_HOLE, 30.0, C.X_SEAT + 0.5, sy, sz), notch))
    s3 = step("bokL_cut", cuts)
    s4 = step("bokL_lipfuse", lambda: one(s3 + lip))
    return s4


# =====================================================================================================================
# 5. T_dvere  (back door)
# =====================================================================================================================
def _hook(sx):
    L = loc_frame(HOOK["x"], HOOK["z"], +1)
    root = lbox(L, -HOOK["root_u"], HOOK["root_u"], HOOK["root_v"][0], HOOK["root_v"][1], -6.0, HOOK["root_w"])
    tab = lbox(L, -HOOK["tab_u"], HOOK["tab_u"], HOOK["tab_v"][0], HOOK["tab_v"][1], HOOK["tab_w"][0], HOOK["tab_w"][1])
    return (root, tab) if sx > 0 else (mirror_x(root), mirror_x(tab))


def build_dvere():
    _init()
    blank = step("dvere_outer", lambda: one(C.outer_solid() & C.door_prism(0.0)))

    def cavity():
        A = []
        for x, z in C.DOOR_MAGNETS["xz"]:
            b = lcyl(loc_frame(abs(x), z, +1), DBOSS["r"], -6.0, DBOSS["w"])
            A.append(b if x > 0 else mirror_x(b))
        A += [_hook(1)[0], _hook(-1)[0]]
        return one(C.inner_solid(C.WALL).cut(*A))
    cav = step("dvere_cavity", cavity)
    s2 = step("dvere_shell", lambda: one(blank - cav))

    def cuts():
        T = []
        for x, z in C.DOOR_MAGNETS["xz"]:
            b = lcyl(loc_frame(abs(x), z, +1), DBOSS["pocket_d"] / 2, DBOSS["w"] - DBOSS["pocket_depth"], DBOSS["w"] + 0.5)
            T.append(b if x > 0 else mirror_x(b))
        zb = C.Z_DOOR - C.DOOR[1] / 2
        ys = C.y_surface(0.0, zb + 0.6, +1)
        T.append(C.pill_prism_y(NOTCH["w"], 2 * NOTCH["h"], 0.0, zb, ys - NOTCH["depth_y"], 60.0))
        return one(s2.cut(*T))
    s3 = step("dvere_cut", cuts)
    s4 = step("dvere_hooks", lambda: one(s3.fuse(_hook(1)[1], _hook(-1)[1])))
    return s4


# =====================================================================================================================
# 6. shoulder joints, bushes
# =====================================================================================================================
def build_klb_L():
    _init()
    sy, sz = C.SH_Y, C.SH_Z
    xs, xe = C.X_SH, C.X_KLB_END
    prof = [(C.X_COL_BOSS, 0.0), (C.X_COL_BOSS, C.R_KLB_NECK), (C.X_SEAT, C.R_KLB_NECK)] + \
           [(max(C.X_SEAT, xs + dx), r) for dx, r in C.KLB_PROFILE] + [(xe, 0.0)]
    f = bd.Face(bd.Wire.make_polygon([bd.Vector(x, r, 0) for x, r in prof], close=True))
    s = bd.Pos(0, sy, sz) * bd.revolve(f, axis=bd.Axis.X, revolution_arc=360)
    yk, zk = klb_yz(0.0, 0.0)
    s = s + C.box(C.X_COL_BOSS - KEY["h"], C.X_COL_BOSS + 0.6, sy + KEY["r"][0], sy + KEY["r"][1], sz - KEY["w"] / 2, sz + KEY["w"] / 2)
    cuts = [C.cyl_x(C.KLB_BUSH["bore_d"] / 2, C.KLB_BUSH["bore_x_in"] - 0.1, xe + 1.0, sy, sz),
            C.cyl_x(C.KLB_BUSH["recess_d"] / 2, C.X_COL_BOSS - 2.0, C.KLB_BUSH["bore_x_in"], sy, sz)]
    for az in C.KLB_SCREWS["az"]:
        y, z = klb_yz(az, C.KLB_SCREWS["pcd_r"])
        cuts += [C.cyl_x(C.SCREWS["M2"][1] / 2, C.X_COL_BOSS - 2.0, C.KLB_SCREWS["head_seat_x"] + 0.1, y, z),
                 C.cyl_x(C.KLB_SCREWS["cbore_d"] / 2, C.KLB_SCREWS["head_seat_x"], xe + 1.0, y, z)]
    for az in C.KLB_MAGNETS["az"]:
        y, z = klb_yz(az, C.KLB_MAGNETS["pcd_r"])
        cuts.append(C.magnet_hole(C.KLB_MAGNETS["size"][0], C.KLB_MAGNETS["size"][1], (xe, y, z), "x", -1))
    gw, gd = C.KLB_WIRE["groove"]
    cuts.append(C.box(C.X_SEAT - 0.1, xs + 4.2 + 0.1, sy - gw / 2, sy + gw / 2, sz - 14.0, sz - (13.5 - gd)))       # wire groove, underside
    return one(s.cut(*cuts))


def build_puzdro_L():
    _init()
    sy, sz = C.SH_Y, C.SH_Z
    fd, fx0, fx1 = BUSH["flange"]
    s = C.cyl_x(BUSH["d"] / 2, fx1 - 0.5, BUSH["x"][1], sy, sz) + C.cyl_x(fd / 2, fx0, fx1, sy, sz)
    return one(s - C.cyl_x(BUSH["blind"][0] / 2, BUSH["x"][1] - BUSH["blind"][1], BUSH["x"][1] + 1.0, sy, sz))


# =====================================================================================================================
# 7. front stack: light guide, LED holder + PCB, grille, speaker, gasket, clamp ring
# =====================================================================================================================
def build_svetlovod():
    _init()
    fw, fh, ft, fr = FLANGE_GUIDE
    plug = step("guide_plug", lambda: one(C.pill_prism_y(*C.GUIDE["plug"], 0, C.Z_BAR, -60, -25) & C.outer_solid()))
    fl = step("guide_flange", lambda: one(C.rrect_prism_y(fw, fh, fr, 0, C.Z_BAR, -60, -26) & C.inner_solid(C.WALL)))
    return step("guide", lambda: one((plug + fl) - C.inner_solid(C.WALL + ft)))


def build_mriezka():
    _init()
    plug = step("grille_plug", lambda: one(C.pill_prism_y(*C.GRILLE["plug"], 0, C.Z_SLOT, -60, -30) & C.outer_solid()))
    fl = step("grille_flange", lambda: one(C.pill_prism_y(*FLANGE_GRILLE, 0, C.Z_SLOT, -60, -31) & C.inner_solid(C.WALL)))

    def fin():
        n, w, h, p = (GRILLE_SLOTS[k] for k in ("n", "w", "h", "pitch"))
        slots = [vpill_y(w, h, (i - (n - 1) / 2) * p, C.Z_SLOT, -60, -30) for i in range(n)]
        return one(((plug + fl) & C.box(-40, 40, -60, Y_GRILLE_BACK, -60, -30)).cut(*slots))
    return step("grille", fin)


def build_drziak_led():
    _init()
    H = HOLDER
    z0, z1 = H["z"]
    zc = C.Z_BAR

    def mk():
        body = C.box(-H["x"], H["x"], -45.0, H["y_back"], z0, z1) & C.inner_solid(H["front_inset"])
        e = H["ear"]
        for sx in (1, -1):
            xa, xb = sorted((sx * e["x"][0], sx * e["x"][1]))
            ear = C.rbox(xa, xb, BOSS_FACE_LED, BOSS_FACE_LED + e["t"], zc - e["z"], zc + e["z"], 1.0, "y")
            body = body + ear

        def rect(y, hx, hz):
            return bd.Wire.make_polygon([bd.Vector(-hx, y, zc - hz), bd.Vector(hx, y, zc - hz), bd.Vector(hx, y, zc + hz),
                                         bd.Vector(-hx, y, zc + hz)], close=True)
        yb = H["y_back"] - H["rebate"][2]
        chan = bd.Solid.make_loft([rect(yb + 0.01, *H["chan_back"]), rect(-37.5, *H["chan_front"])])
        cuts = [chan, C.box(-H["rebate"][0], H["rebate"][0], yb, H["y_back"] + 3.0, zc - H["rebate"][1], zc + H["rebate"][1])]
        for x, z in C.LED_BOSS:
            cuts.append(C.cyl_y(C.SCREWS["M2"][1] / 2, BOSS_FACE_LED - 1, BOSS_FACE_LED + e["t"] + 1, x, z))
        return one(body.cut(*cuts))
    return step("led_holder", mk)


def build_dps_led():
    L = C.LED_PCB
    w, h, t = L["size"]
    y1 = L["y_front"] + t
    s = C.box(-w / 2, w / 2, L["y_front"], y1, C.Z_BAR - h / 2, C.Z_BAR + h / 2)
    lw, lh, lt = L["led"]
    for i in range(L["n"]):
        x = (i - (L["n"] - 1) / 2) * L["pitch"]
        s = s + C.box(x - lw / 2, x + lw / 2, L["y_front"] - lt, L["y_front"] + 0.05, C.Z_BAR - lh / 2, C.Z_BAR + lh / 2)
    return one(s)


def build_reproduktor():
    return C.cyl_y(C.SPEAKER["d"] / 2, C.SPEAKER["y"][0], C.SPEAKER["y"][1], 0.0, C.SPEAKER["z"])


def build_tesnenie():
    _init()
    ring = C.cyl_y(GASKET["ro"], -45.0, C.SPEAKER["y"][0], 0.0, C.SPEAKER["z"]) - C.cyl_y(GASKET["ri"], -46.0, -30.0, 0.0, C.SPEAKER["z"])
    return step("gasket", lambda: one(ring & C.inner_solid(C.WALL)))


def build_drziak_repro():
    _init()
    y0 = C.SPEAKER["y"][1]; y1 = y0 + RING["t"]
    zs = C.SPEAKER["z"]
    s = C.cyl_y(RING["ro"], y0, y1, 0.0, zs)
    for x, z in spk_boss_xz():
        s = s + C.cyl_y(RING["ear_r"], y0, y1, x, z)
    cuts = [C.cyl_y(RING["ri"], y0 - 1, y1 + 1, 0.0, zs), C.box(-30, 30, y0 - 1, y1 + 1, RING["flat_z"], 0.0)]
    for x, z in spk_boss_xz():
        cuts.append(C.cyl_y(C.SCREWS["M2"][1] / 2, y0 - 1, y1 + 1, x, z))
    return one(s.cut(*cuts))


# =====================================================================================================================
# 8. registry
# =====================================================================================================================
def _door_magnets():
    """(door magnets, frame magnets): cylinders D5 x 2 along the local normal at the 4 positions"""
    d, t = C.DOOR_MAGNETS["size"]
    door, fr = [], []
    for x, z in C.DOOR_MAGNETS["xz"]:
        L = loc_frame(abs(x), z, +1)
        a = lcyl(L, d / 2, DBOSS["w"] - t, DBOSS["w"])
        b = lcyl(L, d / 2, PAD["w"][0], PAD["w"][0] + t)
        door.append(a if x > 0 else mirror_x(a)); fr.append(b if x > 0 else mirror_x(b))
    return door, fr


PRINTED = {
    # name: (builder, group, material, label_sk)
    "T_stred": (build_stred, "resin_white", "Stredný pás trupu (predok – vrch – chrbát) s lôžkom goliera"),
    "T_bok_L": (build_bok_L, "resin_white", "Bočný kryt ľavý s objímkou ramena"),
    "T_bok_P": (None, "resin_white", "Bočný kryt pravý s objímkou ramena"),
    "T_dvere": (build_dvere, "resin_white", "Zadné servisné dvierka (magnety, háčiky)"),
    "T_klb_L": (build_klb_L, "resin_black", "Ramenný kĺb ľavý (čierny)"),
    "T_klb_P": (None, "resin_black", "Ramenný kĺb pravý (čierny)"),
    "T_puzdro_L": (build_puzdro_L, "pom", "Drážkované puzdro ramena ľavé (trecia spojka)"),
    "T_puzdro_P": (None, "pom", "Drážkované puzdro ramena pravé (trecia spojka)"),
    "T_svetlovod": (build_svetlovod, "resin_clear", "Svetlovod svetelného pásika (matný)"),
    "T_mriezka": (build_mriezka, "resin_grey", "Mriežka reproduktora"),
    "T_drziak_led": (build_drziak_led, "resin_black", "Držiak LED pásika (svetelná komora)"),
    "T_drziak_repro": (build_drziak_repro, "petg", "Prítlačný krúžok reproduktora"),
}
MIRRORS = {"T_bok_P": "T_bok_L", "T_klb_P": "T_klb_L", "T_puzdro_P": "T_puzdro_L"}


def build(only=None):
    """registry of the module: dict[name] = t4_common.part(shape, group, mat, printed, label_sk, ...)"""
    _init()
    R, times = {}, {}

    def want(n):
        return only is None or n in only

    for name, (fn, mat, label) in PRINTED.items():
        if not want(name):
            continue
        t = time.time()
        if fn is None:
            src = MIRRORS[name]
            s = K("part_" + name, lambda: one(mirror_x(K("part_" + src, PRINTED[src][0]))))
        else:
            s = K("part_" + name, fn)
        R[name] = C.part(one(s), "T", mat, True, label)
        times[name] = time.time() - t
        log(f"part {name}: {times[name]:.1f} s")
    if only is not None and not any(n not in PRINTED for n in only):
        return _finish(R, times)

    t = time.time()
    B = {}
    B["reproduktor"] = (build_reproduktor(), "Reproduktor Ø28 × 5 mm, 8 Ω / 1,5 W", SPEAKER_MASS)
    B["tesnenie_repro"] = (build_tesnenie(), "Penové tesnenie reproduktora (PORON 1 mm, Ø28 / Ø23,8)", GASKET_MASS)
    B["DPS_led"] = (build_dps_led(), "LED pásik 30 × 4 mm, 6 × WS2812B-2020", 0.25)
    dm, fm = _door_magnets()
    for i, s in enumerate(dm):
        B[f"magnet_dvierka_{i + 1}"] = (s, "Magnet dvierok N52 Ø5 × 2 (v dvierkach)", None)
    for i, s in enumerate(fm):
        B[f"magnet_zarubna_{i + 1}"] = (s, "Magnet dvierok N52 Ø5 × 2 (v ráme)", None)
    md, mt = C.KLB_MAGNETS["size"]
    for sx, tag in ((1, "L"), (-1, "P")):
        for i, az in enumerate(C.KLB_MAGNETS["az"]):
            y, z = klb_yz(az, C.KLB_MAGNETS["pcd_r"])
            B[f"magnet_klb_{tag}{i + 1}"] = (C.magnet(md, mt, (sx * C.X_KLB_END, y, z), "x", -sx), "Magnet ramena N52 Ø3 × 2", None)
        for i in range(2):
            x0, x1 = SPRING["x"][i], SPRING["x"][i + 1]
            xa, xb = sorted((sx * x0, sx * x1))
            sp = C.cyl_x(SPRING["do"] / 2, xa, xb, C.SH_Y, C.SH_Z) - C.cyl_x(SPRING["di"] / 2, xa - 1, xb + 1, C.SH_Y, C.SH_Z)
            B[f"pruzina_klb_{tag}{i + 1}"] = (one(sp), "Tanierová pružina DIN 2093 10 × 5,2 × 0,4", 0.17)
        for i, az in enumerate(C.KLB_SCREWS["az"]):
            y, z = klb_yz(az, C.KLB_SCREWS["pcd_r"])
            B[f"skrutka_klb_{tag}{i + 1}"] = (one(C.screw("M2", 10, (sx * C.KLB_SCREWS["head_seat_x"], y, z), "x", -sx)),
                                              "Skrutka M2 × 10 s valcovou hlavou (kĺb → stĺpik)", None)
    for i, (x, z) in enumerate(C.LED_BOSS):
        B[f"skrutka_led_{i + 1}"] = (one(C.screw("M2", 6, (x, BOSS_FACE_LED + HOLDER["ear"]["t"], z), "y", -1)),
                                     "Skrutka M2 × 6 do plastu (držiak LED)", None)
    for i, (x, z) in enumerate(spk_boss_xz()):
        B[f"skrutka_repro_{i + 1}"] = (one(C.screw("M2", 6, (x, C.SPEAKER["y"][1] + RING["t"], z), "y", -1)),
                                       "Skrutka M2 × 6 do plastu (krúžok reproduktora)", None)
    for i, (x, y) in enumerate(C.SCR_STRED):
        B[f"vlozka_stred_{i + 1}"] = (one(C.insert("M2.5", (x, y, C.Z_WHITE), "z", 1)), "Mosadzná vložka M2,5 × 4 (lepená)", None)
    for name, (s, label, mass) in B.items():
        if not want(name):
            continue
        mat = "bought"
        if name.startswith("magnet"):
            mat = "magnet"
        elif name.startswith("skrutka") or name.startswith("pruzina"):
            mat = "steel"
        elif name.startswith("vlozka"):
            mat = "brass"
        elif name == "DPS_led":
            mat = "pcb"
        extra = {} if mass is None else dict(mass=mass)
        R[name] = C.part(one(s), "T", mat, False, label, **extra)
    log(f"bought parts: {time.time() - t:.1f} s")
    return _finish(R, times)


def _finish(R, times):
    for n, p in R.items():
        p["build_s"] = round(times.get(n, 0.0), 1)
    return R


BBOX_EXPECT = {      # (x0, x1, y0, y1, z0, z1) from the spec, tolerance 0.06 unless None
    "T_stred": (-C.X_BAND, C.X_BAND, -40.01, None, C.Z_WHITE, C.TOP),      # back extreme is inside the door opening
    "T_bok_L": (LIP["x_tip"], 52.5, -33.4, 33.4, C.Z_WHITE, None),
    "T_dvere": (-28.0, 28.0, None, None, -72.0, None),
    "T_klb_L": (C.X_COL_BOSS - KEY["h"], C.X_KLB_END, C.SH_Y - 13.5, C.SH_Y + 13.5, C.SH_Z - 13.5, C.SH_Z + 13.5),
    "T_puzdro_L": (42.0, C.X_KLB_END - 0.006, C.SH_Y - 5.0, C.SH_Y + 5.0, C.SH_Z - 5.0, C.SH_Z + 5.0),
    "reproduktor": (-14.0, 14.0, -36.6, -31.6, -65.0, -37.0),
    "DPS_led": (-15.0, 15.0, -31.74, -30.1, -34.5, -30.5),
}


def main():
    args = sys.argv[1:]
    if "--rebuild" in args:
        for f in glob.glob(os.path.join(C.CACHE, f"obal_{VER}_*.brep")):
            os.remove(f)
    only = None
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    R = build(only)
    recs = []
    print(f"\n{'part':22s} {'valid':5s} {'sol':3s} {'vol(mesh)':>10s} {'mass g':>7s} {'build s':>7s}  bbox x / y / z")
    for name, p in R.items():
        t = time.time()
        if "--no-export" in args:
            rec = C.check_part(name, p)
            rec["volume_mesh"] = round(C.mesh_volume(p["shape"]), 2)
            dens = C.DENS.get(p["mat"])
            rec.update(group=p["group"], mat=p["mat"], printed=p["printed"], label_sk=p["label_sk"],
                       mass_g=p.get("mass", round(rec["volume_mesh"] * dens, 2) if dens else None))
        else:
            rec = C.export_part(name, p, HERE)
        rec["build_s"] = p.get("build_s", 0.0)
        rec["export_s"] = round(time.time() - t, 1)
        exp = BBOX_EXPECT.get(name)
        if exp:
            rec["bbox_expected"] = exp
            rec["bbox_ok"] = all(e is None or abs(a - e) <= 0.06 for a, e in zip(rec["bbox"], exp))
            rec["ok"] = bool(rec["ok"] and rec["bbox_ok"])
        recs.append(rec)
        b = rec["bbox"]
        print(f"{name:22s} {str(rec['valid']):5s} {rec['n_solids']:3d} {rec['volume_mesh']:10.1f} {str(rec['mass_g']):>7s} "
              f"{rec['build_s']:7.1f}  {b[0]:7.2f}..{b[1]:6.2f} / {b[2]:7.2f}..{b[3]:6.2f} / {b[4]:7.2f}..{b[5]:6.2f}"
              f"{'' if rec['ok'] else '   <-- NOT OK'}", flush=True)
    if only is None:
        json.dump(recs, open(os.path.join(HERE, "parts_obal.json"), "w"), indent=1, ensure_ascii=False)
    bad = [r["name"] for r in recs if not r["ok"]]
    print(f"\n{len(recs)} parts, not ok: {bad}, total {time.time() - T0:.1f} s")


if __name__ == "__main__":
    main()
