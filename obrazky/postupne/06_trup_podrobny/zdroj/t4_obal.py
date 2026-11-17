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
STEP_REV = {   # cached steps that changed after the first full build (cache name gets the suffix _r<n>)
    "stred_pads": 5, "stred_ledge": 5, "part_T_stred": 5,
    "dvere_cavity": 2, "dvere_shell": 2, "dvere_cut": 2, "dvere_hooks": 3, "part_T_dvere": 3,
    "grille_flange": 2, "grille": 2, "part_T_mriezka": 2,
    "part_T_klb_L": 2, "part_T_klb_P": 2,
    "part_T_drziak_repro": 2,
}
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
HOOK = dict(x=16.0, z=-12.0, tab_u=4.0, tab_w=(2.75, 3.6), tab_v=(-1.5, 3.3), root_u=4.25, root_w=3.8, root_v=(-2.05, 3.0))
#   tab_w rev 3: 2.5 left only 0.07 to the curved wall at the outer top corner of the flat tab (measured on the meshes); 2.75 -> 0.3
PAD = dict(r=4.0, w=(4.5, 7.2), arm_u=7.2, riser_u=(3.6, 7.2), pocket_d=5.1, pocket_depth=2.1, push_d=1.5,
           door_clear=0.3, w_clear=4.4,   # nothing of the pad inside the opening prism + 0.3 in front of the plane w 4.4
           pocket_du={-24.0: 0.5})
#   rev 4 (integrator, K4 / K10): at the two UPPER pads (z -24) the PAN_ENV + 1.0 trim left 0.46 .. 0.50 of resin beside the
#   magnet pocket and a 0.45 x 0.4 fin at the band step z -22 -> the pocket (and the frame magnet) sits 0.5 further out
#   along the wall (local u), and the pad is trimmed with ONE radius (the largest PAN_ENV band it touches + 1.0)
#   rev 3: (a) the riser of rev 1 (u 3.6..5.9) crossed the door edge and the door boss: 14.6 mm3 of interference -> riser
#   moved outside the opening, arm behind the door boss; (b) pad 4.5..7.2 (spec 4.7): floor behind the magnet pocket
#   0.6 instead of 0.4 (min feature); the door boss is 0.2 lower instead (face at inset 4.3), air gap 0.2 kept
DBOSS = dict(r=4.0, w=4.3, pocket_d=5.1, pocket_depth=2.1)       # door magnet boss D8 x 2.1 (face at inset 4.3; spec 4.5)
NOTCH = dict(w=12.0, h=1.2, depth_y=0.85)                         # finger-nail notch in the door's bottom edge
BOSS_FACE_LED = -31.4           # LED boss face (spec -33.0: a 5 mm pilot would break through the 2.2 wall there)
PILOT_LED = 4.3                 # pilot depth in the LED bosses (remaining skin >= 1.2)
SPK_AZ = (30.0, 150.0, 270.0)   # speaker bosses (spec 90 / 210 / 330: the 90 deg boss sits inside the LED box)
SPK_SEAT_D = 28.3
FLANGE_GUIDE = (33.6, 8.0, 1.2, 1.5)      # light-guide flange w x h x t, corner r (spec 35 wide: hits the LED bosses)
FLANGE_GRILLE = (22.4, 5.2)               # grille flange pill (0.3 inside the gasket ID 23.8), flat back at Y_GRILLE_BACK
Y_GRILLE_BACK = -36.7
GRILLE_SLOTS = dict(n=5, w=0.8, h=1.6, pitch=3.6)     # webs above / below the slots 0.6 (min feature)
HOLDER = dict(x=16.8, z=(C.Z_BAR - 3.5, C.Z_BAR + 3.5), y_back=-30.1, front_inset=3.5,
              chan_back=(14.4, 1.5), chan_front=(15.5, 2.1), rebate=(15.15, 2.1, 0.8),
              ear=dict(x=(15.3, 22.3), t=2.0, z=3.0))
RING = dict(ri=13.0, ro=16.0, t=1.6, ear_r=2.6, flat_z=-36.3,     # speaker clamp ring (flat top under the LED holder)
            notch=dict(x=(-17.5, -12.0), z=(-53.0, -49.0)))        # wire exit toward -X (speaker terminals turned there)
# cable exits / bend space of the two bought parts on the front wall (solids, so that K2 / K3 see them)
#   speaker: solder lugs on the back face inside the ring + 2 wires leaving through the ring notch toward -X
#   LED PCB: 3 solder pads on the back at the -X end, wires bent flat along the back toward -X (both: r >= 29.7 from the axis)
EXIT_SPK = dict(x=(-16.5, -8.0), y=(C.SPEAKER["y"][1], C.SPEAKER["y"][1] + 1.6), z=(-52.5, -49.5))
EXIT_LED = dict(x=(-15.0, -9.0), y=(-30.1, -28.9), z=(C.Z_BAR - 1.8, C.Z_BAR + 1.8))
GASKET = dict(ri=11.9, ro=14.0)
LIP = dict(clear=0.15, t=1.6, x_tip=C.X_CAP - 2.5, x_root=C.X_CAP + 0.4, z_bot=-77.7, root_w=4.3, root_x=(C.XS - 0.3, C.X_CAP + 0.75))
KEY = dict(w=2.9, r=(7.0, 10.9), h=1.4)                           # anti-rotation key of T_klb (column slot 3.0 x 1.5 at az 0)
SEAT_NOTCH_R = 14.0             # wire notch in the cap seat flange (spec 13.2; 14.0 lets the wires pass the stop ring r 12.8)
BUSH = dict(d=8.0, x=(44.0, C.X_KLB_END - 0.006), flange=(10.0, 42.0, 44.0), blind=(4.0, 6.0))
SPRING = dict(do=10.0, di=5.2, t=0.5, x=(41.0, 41.5, 42.0))
SPEAKER_MASS, GASKET_MASS = 6.0, 0.05



def _sync_common():
    """the numbers this module changed / added are mirrored in t4_common.OBAL ('additions by obal'); both copies must agree"""
    co = getattr(C, "OBAL", None)
    if co is None:
        return
    mine = dict(
        DOOR_LEDGE_TOP_GAP=dict(x=TOP_GAP_X, z_above=LEDGE_TOP_Z),
        DOOR_HOOK=dict(x=HOOK["x"], half_u=HOOK["tab_u"], inset=HOOK["tab_w"], v=HOOK["tab_v"]),
        DOOR_BOSS_FACE_INSET=DBOSS["w"], PAD_INSET=PAD["w"], PAD_RISER=dict(u=PAD["riser_u"], door_clear=PAD["door_clear"]),
        DOOR_NOTCH=dict(w=NOTCH["w"], h=NOTCH["h"], depth=NOTCH["depth_y"]),
        TUBE_GUSSET=dict(z_start=Z_FLARE, az=FLARE_AZ), TUBE_VENT=dict(d=VENT["d"], z=VENT["z"]),
        LED_BOSS_FACE_Y=BOSS_FACE_LED, LED_PILOT=PILOT_LED, SPK_BOSS_AZ=SPK_AZ, SPK_SEAT_D=SPK_SEAT_D,
        SPK_GASKET=dict(ri=GASKET["ri"], ro=GASKET["ro"]),
        SPK_RING=dict(ri=RING["ri"], ro=RING["ro"], t=RING["t"], notch=RING["notch"]),
        GUIDE_FLANGE=FLANGE_GUIDE[:3], GRILLE_FLANGE=FLANGE_GRILLE, GRILLE_BACK_Y=Y_GRILLE_BACK, GRILLE_SLOTS=GRILLE_SLOTS,
        EXIT_SPK=EXIT_SPK, EXIT_LED=EXIT_LED,
        SEAM_LIP=dict(clear=LIP["clear"], t=LIP["t"], x_tip=LIP["x_tip"], z_bot=LIP["z_bot"]),
        SEAT_NOTCH_R=SEAT_NOTCH_R, KLB_KEY=KEY, STL=dict(deflection_mm=STL_LIN, angular_rad=STL_ANG, relative=False))

    def same(a, b):
        if isinstance(a, dict):
            return isinstance(b, dict) and set(a) == set(b) and all(same(a[k], b[k]) for k in a)
        if isinstance(a, (tuple, list)):
            return isinstance(b, (tuple, list)) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(a - b) < 1e-6
        return a == b
    bad = [k for k in mine if k not in co or not same(mine[k], co[k])]
    assert not bad, f"t4_obal.py and t4_common.OBAL disagree on {bad}"


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
    rev = STEP_REV.get(name)
    return C.cached(f"obal_{VER}_{name}" + (f"_r{rev}" if rev else ""), fn, verbose=True)


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


def poly_prism_y(pts_xz, y0, y1):
    _init()
    w = bd.Wire.make_polygon([bd.Vector(x, y0, z) for x, z in pts_xz], close=True)
    return bd.extrude(bd.Face(w), amount=y1 - y0, dir=(0, 1, 0))


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
    du = PAD["pocket_du"].get(float(z), 0.0)
    s = lcyl(L, PAD["r"], w0, w1) + lbox(L, 0.0, PAD["arm_u"], -PAD["r"], PAD["r"], w0, w1) + \
        lbox(L, PAD["riser_u"][0], PAD["riser_u"][1], -PAD["r"], PAD["r"], 0.9, w1)
    s = s - lcyl(L, PAD["pocket_d"] / 2, w0 - 0.5, w0 + PAD["pocket_depth"], du) - lcyl(L, PAD["push_d"] / 2, w0, w1 + 0.5, du)
    # the door (panel, boss, 0.25 seam) owns everything inside the opening outline down to the boss face (inset 4.5):
    # the riser only exists outside the opening + 0.3 there, the arm passes behind the door boss (w >= 4.7)
    s = s - (C.door_prism(C.SEAM / 2 + PAD["door_clear"]) & lbox(L, -40.0, 40.0, -40.0, 40.0, -12.0, PAD["w_clear"]))
    # stay 1.0 outside the pan sweep: ONE radius for the whole pad = the largest PAN_ENV band it touches (a second, smaller
    # radius above the band step z -22 left a fin / feather edge on the rim of the pad disc)
    bands = [b for b in C.PAN_ENV if b[1] > z - PAD["r"] - 0.2 and b[0] < z + PAD["r"] + 0.2]
    if bands:
        s = s - C.cyl_z(max(b[2] for b in bands) + 1.0, z - 6.0, z + 6.0)
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
    rb = 13.5 - gd                                   # groove bottom radius 10.9
    x_st = xs + 4.2                                  # step face of the r 13.5 body
    # wire groove on the underside: opens through the shoulder face x 40.6 (into the notch of the cap seat flange), full
    # depth to 1.0 before the step face, then a ramp that leaves the surface inside the 45 deg chamfer of the D22 step
    # (rev 2: the plain box of rev 1 left two 0.1 mm notches in the neck and in the D22 journal)
    cuts.append(poly_prism_y([(C.X_SEAT, sz - 16.0), (C.X_SEAT, sz - rb), (x_st - 1.0, sz - rb), (x_st + 1.2, sz - (rb + 0.7)),
                              (x_st + 1.2, sz - 16.0)], sy - gw / 2, sy + gw / 2))
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
    nt = RING["notch"]
    cuts = [C.cyl_y(RING["ri"], y0 - 1, y1 + 1, 0.0, zs), C.box(-30, 30, y0 - 1, y1 + 1, RING["flat_z"], 0.0),
            C.box(nt["x"][0], nt["x"][1], y0 - 1, y1 + 1, nt["z"][0], nt["z"][1])]
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
        b = lcyl(L, d / 2, PAD["w"][0], PAD["w"][0] + t, PAD["pocket_du"].get(float(z), 0.0))
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
    B["vyvod_repro"] = (C.box(*EXIT_SPK["x"], *EXIT_SPK["y"], *EXIT_SPK["z"]),
                        "Vývody reproduktora + kábel JST-PH 2p 90 mm (rezervovaný priestor)", 0.4)
    B["vyvod_led"] = (C.box(*EXIT_LED["x"], *EXIT_LED["y"], *EXIT_LED["z"]),
                      "Spájkovacie plôšky LED pásika + kábel JST-SH 3p 90 mm (rezervovaný priestor)", 0.3)
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


STL_LIN, STL_ANG = 0.01, 0.1       # STL: ABSOLUTE chord deflection (mm) / angular deflection (rad)
STEP_MAX_MB = 12.0                 # STEP is a courtesy export: only written when the file stays below this size
STEP_BREP_MAX_MB = 8.0             # ... parts whose BREP is already larger carry trimmed loft surfaces -> STEP skipped


_sync_common()


def read_stl(path):
    """binary STL -> (V (n, 3) welded vertices, T (m, 3)), float64"""
    raw = np.fromfile(path, dtype=np.uint8)
    n = int(np.frombuffer(raw[80:84].tobytes(), dtype="<u4")[0])
    rec = np.frombuffer(raw[84:84 + 50 * n].tobytes(), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    P = rec["v"].reshape(-1, 3).astype(np.float64)
    key = np.round(P * 1e4).astype(np.int64)
    _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return P[idx], inv.reshape(-1, 3)


def mesh_stats(V, T):
    """watertightness of a welded triangle mesh: every undirected edge used exactly twice, once per direction"""
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    und = np.sort(e, 1)
    _, cnt = np.unique(und, axis=0, return_counts=True)
    dirk = e[:, 0].astype(np.int64) * (len(V) + 1) + e[:, 1]
    _, dcnt = np.unique(dirk, return_counts=True)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    dv = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    vol = float(dv.sum())
    cog = ((a + b + c) / 4.0 * dv[:, None]).sum(0) / vol if abs(vol) > 1e-9 else np.zeros(3)
    return dict(tris=int(len(T)), verts=int(len(V)), open_edges=int((cnt == 1).sum()), nonmanifold_edges=int((cnt > 2).sum()),
                flipped_edges=int((dcnt > 1).sum()), volume=vol, cog=[round(float(v), 3) for v in cog])


def export_abs(name, p, out=HERE, do_step=True):
    """stl/<name>.stl with ABSOLUTE deflection (build123d / t4_common.export_part mesh RELATIVE to the edge size, which left
    chord errors up to 0.28 mm on the big loft faces), watertight statistics read back from the written file, and
    step/<name>.step only when it stays below STEP_MAX_MB (otherwise step = None)."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    from OCP.BRepTools import BRepTools
    _init()
    s = p["shape"]
    os.makedirs(os.path.join(out, "stl"), exist_ok=True); os.makedirs(os.path.join(out, "step"), exist_ok=True)
    rec = C.check_part(name, p)
    f_stl = os.path.join(out, "stl", name + ".stl")
    BRepTools.Clean_s(s.wrapped)
    BRepMesh_IncrementalMesh(s.wrapped, STL_LIN, False, STL_ANG, True)
    w = StlAPI_Writer(); w.ASCIIMode = False
    w.Write(s.wrapped, f_stl)
    st = mesh_stats(*read_stl(f_stl))
    rec["volume_mesh"] = round(st["volume"], 2)
    rec["cog"] = st["cog"]
    rec["stl"] = dict(file=f"stl/{name}.stl", tris=st["tris"], open_edges=st["open_edges"], nonmanifold_edges=st["nonmanifold_edges"],
                      flipped_edges=st["flipped_edges"], deflection_mm=STL_LIN, mb=round(os.path.getsize(f_stl) / 1e6, 2))
    rec["watertight"] = bool(st["open_edges"] == 0 and st["nonmanifold_edges"] == 0 and st["flipped_edges"] == 0 and st["volume"] > 0)
    f_step = os.path.join(out, "step", name + ".step")
    rec["step"] = None
    if os.path.exists(f_step):
        os.remove(f_step)
    if do_step:
        tmp = os.path.join(C.CACHE, f"_size_{name}.brep")
        bd.export_brep(s, tmp)
        mb = os.path.getsize(tmp) / 1e6
        os.remove(tmp)
        if mb <= STEP_BREP_MAX_MB:
            bd.export_step(s, f_step)
            smb = os.path.getsize(f_step) / 1e6
            if smb <= STEP_MAX_MB:
                rec["step"] = f"step/{name}.step"
            else:
                os.remove(f_step); rec["step_skipped"] = f"STEP {smb:.0f} MB > {STEP_MAX_MB:.0f} MB"
        else:
            rec["step_skipped"] = f"BREP {mb:.0f} MB (trimmed loft surfaces) -> STEP would exceed {STEP_MAX_MB:.0f} MB"
    dens = C.DENS.get(p["mat"])
    rec.update(group=p["group"], mat=p["mat"], printed=p["printed"], label_sk=p["label_sk"],
               mass_g=p.get("mass", round(rec["volume_mesh"] * dens, 2) if dens else None))
    rec["ok"] = bool(rec["ok"] and rec["watertight"])
    return rec


def load_parts(path=None):
    """list of part records of parts_obal.json (dict layout with the key "parts"; the first version was a plain list)"""
    d = json.load(open(path or os.path.join(HERE, "parts_obal.json")))
    return d["parts"] if isinstance(d, dict) else d


DEVIATIONS = [   # where the built geometry differs from T4_spec.md / t4_common (reason in each line)
    "Collar tube: two 45 deg gusset cones in the +-Y sectors (azimuth 50..130 / 230..310, from z -6.6 up) instead of the 6 ribs of "
    "spec 4.3 - they fill the acute crevice between tube and wall (which the spec also asks to fill) and act as the +-50 / +-130 ribs; "
    "the 0 / 180 deg ribs (2.4 mm stubs to the band edge) are omitted.  2 vent holes D1.6 at z 0.4 through the tube (resin drain of "
    "the trough between tube and shelf; covered by the glued collar ring).",
    "Door frame ledge omitted along the top edge for |x| < 20.6 above z -16.5 (spec 18.0): the hook tabs reach |x| 20.25.",
    "Door magnets: door boss D8 x 2.1 with its face at inset 4.3 (spec 2.3 / 4.5), frame pad between inset 4.5 and 7.2 (spec 4.7 .. 7.2): "
    "the floor behind the frame pocket is 0.6 instead of 0.4 (min feature); air gap 0.2 kept.  The pad is carried by an arm behind "
    "the door boss and a riser that stays 0.3 outside the door opening (rev 1 crossed the door: 14.6 mm3).",
    "LED-holder bosses: face at y -31.4 (spec -33.0) and pilot D1.7 x 4.3 (spec x 5): with the spec numbers the pilot leaves < 1.2 "
    "of skin.  Skin behind the pilot 1.3.",
    "Speaker bosses at 30 / 150 / 270 deg (spec 90 / 210 / 330): the 90 deg boss would sit inside the LED box.",
    "Light-guide flange 33.6 x 8 x 1.2 (spec 35 wide: collides with the LED bosses at x +-19.5, r 2.5).",
    "Grille flange = pill 22.4 x 5.2 with a flat back at y -36.7 (spec 25 x 7 x 1.2): it has to fit inside the speaker gasket "
    "(ID 23.8) and in front of the speaker face; 5 slots 0.8 x 1.6 at 3.6 pitch (webs 0.6).",
    "Side caps: ONE continuous seam lip (1.6 thick, 2.5 under the band edge, 0.15 clearance, straight extrusion along X) instead of "
    "8 tabs - it also backs the whole seam against see-through (K8).  It ends at z -77.7 (cap spigot top -78.0).",
    "Wire notch of the cap seat flange cut to r 14.0 (spec 13.2): the wires have to pass outside the stop ring r 12.8.",
    "T_klb wire groove 1.6 x 2.6: runs out through a ramp inside the chamfer of the D22 step instead of a square end.",
    "T_dvere: finger-nail notch 12 x 1.2, 0.85 deep, in the bottom edge (asked for in the task; the spec removes the door with a "
    "suction cup).  Wall under the notch 1.35.",
    "Disc springs modelled as 2 flat rings of 0.5 (working height 1.0 in series).",
    "Frame magnet pads at z -24 (integrator): magnet pocket and frame magnet 0.5 further out along the wall than the door magnet "
    "(0.5 lateral offset of the pair), band-step fin removed: the PAN_ENV + 1.0 trim had left 0.46 .. 0.50 of resin beside the pocket.",
    "T_drziak_repro: wire notch 5.5 x 4 at azimuth 180 (toward -X) for the speaker leads; two reserved-space solids vyvod_repro / "
    "vyvod_led model the solder lugs and the first cable bend (not in the spec part list).",
    "STL written with ABSOLUTE deflection 0.01 mm (t4_common.export_part / build123d use a deflection relative to the edge size: "
    "chord errors up to 0.28 mm on the loft faces).  STEP skipped (null) for the 8 parts that carry trimmed loft surfaces.",
]
BOUGHT = {   # bought parts of the module: modelled size, source of the dimension, tolerance taken by the seat
    "reproduktor": "D28.0 x 5.0 mm, 8 ohm 1.5 W micro speaker (generic catalogue size, T4_spec 3.3); +-0.3; seat D28.3 between 3 "
                   "scallops, depth taken by the 0.85 foam gasket; terminals turned to -X (ring notch), exit space vyvod_repro",
    "tesnenie_repro": "PORON ring D28 / D23.8, 1.0 mm sheet compressed to 0.85 (cut from sheet)",
    "DPS_led": "30.0 x 4.0 x 0.8 mm strip, 6 x WS2812B-2020 (2.0 x 2.0 x 0.84, Worldsemi datasheet) at 5.0 pitch; custom / cut strip "
               "+-0.2; rebate 30.3 x 4.2 x 0.8; solder pads on the back at the -X end, exit space vyvod_led",
    "magnet_dvierka_* / magnet_zarubna_*": "N52 disc D5 x 2 (+-0.1 typical); pockets D5.1 x 2.1, glued, air gap 0.2",
    "magnet_klb_*": "N52 disc D3 x 2 (+-0.1); pockets D3.1 x 2.1 in the arm interface face",
    "pruzina_klb_*": "disc spring DIN 2093 10 x 5.2 x 0.4 (l0 0.7), 2 in series, modelled as rings of 0.5 working height",
    "skrutka_klb_*": "ISO 4762 M2 x 10 (head D3.8 x 2.0); clearance D2.3, counterbore D4.2",
    "skrutka_led_* / skrutka_repro_*": "thread-forming M2 x 6 pan head (head D3.8 x 2.0 modelled); pilot D1.7",
    "vlozka_stred_*": "brass insert M2.5 x 4.0, OD 3.5 (t4_common.INSERTS); hole D3.6, glued",
}
INTENDED_FITS = [   # designed contacts / overlaps inside the module (K2)
    "skrutka_led_* / skrutka_repro_* in the pilots D1.7 of T_stred: thread-forming engagement (overlap 3.3 .. 3.8 mm3 each)",
    "T_svetlovod flange, T_mriezka flange and tesnenie_repro on the inner wall of T_stred: coincident faces (glued / pressed)",
    "vlozka_stred_* in the D3.6 holes of the T_stred bosses (glued, 0.05 radial)",
    "magnets in their pockets D5.1 x 2.1 / D3.1 x 2.1 (glued)",
    "T_dvere in the opening (0.25 all round), 0.2 in front of the frame ledge, 0.1 in front of the pad risers (inward stop on 4 "
    "crescents at the magnet bosses); hook tabs 0.3 .. 0.55 behind the wall",
    "seam lip of T_bok_* under the edge of T_stred (0.15)",
    "T_klb_* shoulder on the seat flange of T_bok_* (x +-40.6), neck in the flange hole (0.25), body in the socket bore (0.5)",
    "T_puzdro_* in the bore D8.05 of T_klb_* (running fit), its flange on the disc springs",
    "DPS_led in the rebate of T_drziak_led; reproduktor between the 3 boss scallops, on the gasket, under T_drziak_repro",
]


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
    print(f"\n{'part':22s} {'valid':5s} {'sol':3s} {'wt':3s} {'vol(mesh)':>10s} {'mass g':>7s} {'build s':>7s} {'tris':>7s} {'step':4s}  bbox x / y / z")
    for name, p in R.items():
        t = time.time()
        rec = export_abs(name, p, HERE, do_step="--no-step" not in args)
        rec["build_s"] = p.get("build_s", 0.0)
        rec["export_s"] = round(time.time() - t, 1)
        exp = BBOX_EXPECT.get(name)
        if exp:
            rec["bbox_expected"] = exp
            rec["bbox_ok"] = all(e is None or abs(a - e) <= 0.06 for a, e in zip(rec["bbox"], exp))
            rec["ok"] = bool(rec["ok"] and rec["bbox_ok"])
        recs.append(rec)
        b = rec["bbox"]
        print(f"{name:22s} {str(rec['valid']):5s} {rec['n_solids']:3d} {'ok' if rec['watertight'] else 'NO':3s} {rec['volume_mesh']:10.1f} "
              f"{str(rec['mass_g']):>7s} {rec['build_s']:7.1f} {rec['stl']['tris']:7d} {'yes' if rec['step'] else '-':4s}  "
              f"{b[0]:7.2f}..{b[1]:6.2f} / {b[2]:7.2f}..{b[3]:6.2f} / {b[4]:7.2f}..{b[5]:6.2f}"
              f"{'' if rec['ok'] else '   <-- NOT OK'}", flush=True)
    pj = os.path.join(HERE, "parts_obal.json")
    if only is not None and os.path.exists(pj):                      # partial run: merge into the existing list
        old = load_parts(pj)
        new = {r["name"]: r for r in recs}
        recs_out = [new.pop(r["name"], r) for r in old] + list(new.values())
    else:
        recs_out = recs
    printed = [r for r in recs_out if r["printed"]]
    doc = dict(module="obal", generated=time.strftime("%Y-%m-%d %H:%M:%S"), frame="B frame, mm, rest pose", n_parts=len(recs_out),
               all_ok=all(r["ok"] for r in recs_out), not_ok=[r["name"] for r in recs_out if not r["ok"]],
               stl=dict(deflection_mm=STL_LIN, angular_rad=STL_ANG, note="absolute deflection (not relative to the edge size)"),
               step_rule=f"STEP only below {STEP_MAX_MB:.0f} MB; step = null for parts with trimmed loft surfaces",
               step_null=[r["name"] for r in recs_out if not r.get("step")],
               mass_printed_g=round(sum(r["mass_g"] or 0 for r in printed), 2),
               mass_bought_g=round(sum(r["mass_g"] or 0 for r in recs_out if not r["printed"]), 2),
               parts=recs_out, deviations=DEVIATIONS, intended_fits=INTENDED_FITS, bought=BOUGHT)
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    bad = [r["name"] for r in recs if not r["ok"]]
    print(f"\n{len(recs)} parts, not ok: {bad}, total {time.time() - T0:.1f} s")


if __name__ == "__main__":
    main()
