#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso, module PAN, REV. 2 (resin-only, slim serviceable pan stage + neck lift).

    /opt/venv/cad/bin/python t4_pan.py            build (printed parts cached by source hash), export, parts_pan.json
    /opt/venv/cad/bin/python t4_pan.py --rebuild  ignore the cache
    /opt/venv/cad/bin/python t4_pan.py --noexport build + table only

Numbers: t4_common.R2 (T4_spec.md section 17).  Module constants and every deviation from section 17: dict PAN2 below
(+ parts_pan.json["deviations"]).  Frame: pan-stage frame = B frame at pan 0, rest pose = lift 0, mm, Z up, FRONT = -Y.
Registry: build() -> dict[name] = t4_common.part(shape, group, mat, printed, label_sk, ...)  (rest pose, pan 0).
Pose functions (checks / integrator): pose_parts(lift) [lift group + crank], fpc_loop(pan) [pan rolling loop, B frame],
fpc_lift(lift) [lift loop, stage frame], ffc_tails_krk(lift), pigtail(lift), mk_rameno(theta), crank_angle(lift).

Printed (tough resin, Elegoo Tough class):  P_sachta (slim well + journal + hub disc + drum shroud + pads + rail),
                                            P_drziak_serva (lift-servo pocket + pan stop lug)
Metal (custom, hand made):                  L_ucho (304 stainless 1.5, bent; DXF flat pattern), L_pata (Al flat bar 20 x 4)
Bought:  koleso_pan (36T m0.8 brass), servo_zdvih (MG90S), rameno_zdvih (Al arm), cap_kluky (dowel 2 x 8), DPS_krk
         (+ 2 x ZIF Panasonic Y5B AYF530535), FFC pair (Molex Premo-Flex / Wurth WR-FFC 0.5 mm 5 p), pigtail + Molex PicoBlade
         inline pair, PTFE tapes, screws, inserts, nut, washers, dowel.
"""
from __future__ import annotations
import os, sys, math, time, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np                                    # noqa: E402
import t4_common as C                                 # noqa: E402
import build123d as bd                                # noqa: E402
from build123d import Vector                          # noqa: E402

R2 = C.R2
C.DENS.setdefault("alu", 2.70e-3)                     # runtime addition only (t4_common.py is NOT edited) - see notes
C.DENS.setdefault("stainless", 7.93e-3)
YL, ZL = C.Y_LIFT, C.Z_LIFT                           # lift servo shaft axis (along X): y 23.2, z -24.2
RC = R2["CRANK"]["r"]                                 # 10.00
ZS0 = C.Z_SLOT_REST                                   # -34.2  ear slot centre line at rest
TIMES = {}
AX = R2["GEAR_PAN"]["ax"]
PAN_AZ = math.degrees(math.atan2(AX[1], AX[0])) % 360.0          # 254.286 - pinion direction seen from the pan axis
C_PAN = math.hypot(*AX)                                           # 21.600


# =====================================================================================================================
# module constants (PAN rev. 2).  Everything not listed here comes from R2.  'dev' = deviation from section 17 (reason in
# DEVIATIONS / parts_pan.json).
# =====================================================================================================================
def _drum_az(clear=1.0, pan_max=90.3, r_pts=(15.5, 16.1, 16.7, 17.1, 17.5)):
    """shroud / lip end azimuths (stage frame) that keep `clear` to the pinion tip circle at the hard stops +-pan_max"""
    ra = R2["GEAR_PAN"]["pinion"]["da"] / 2

    def dmin(az, pan):
        cx, cy = C_PAN * math.cos(math.radians(PAN_AZ - pan)), C_PAN * math.sin(math.radians(PAN_AZ - pan))
        return min(math.hypot(r * math.cos(math.radians(az)) - cx, r * math.sin(math.radians(az)) - cy) - ra for r in r_pts)
    a0 = 8.0
    while dmin(a0, -pan_max) < clear:
        a0 += 0.05
    a1 = 140.0
    while dmin(a1, pan_max) < clear:
        a1 -= 0.05
    return round(a0, 2), round(a1, 2)


DRUM_AZ = _drum_az()

PAN2 = dict(
    # ---- P_sachta (slim well) -------------------------------------------------------------------------------------
    WELL=dict(xi=23.5, yi=11.0, ri=2.5, xo=25.1, yf=-12.6, yb=12.6, yb2=13.0, yb2_x=(-6.0, 23.2), r_max=26.50,
              z_top=-2.0, plate_z=(-3.5, -2.0)),
    RING=dict(r_in=24.37, r=26.37, z=(-10.0, -2.0), chamfer=0.5),        # journal ring (resin) + tape 0.13 = r 26.50
    RIBS=dict(x=(-12.5, 0.0, 12.5), t=2.0, z=(-10.0, -3.45)),
    HUB=dict(r=(6.5, 12.6), z=(-41.9, -40.65)),
    FLOOR=dict(y_min=3.3, az_max=135.0, z=(-41.9, -40.65)),               # dev: back floor plan region (pinion at the stops)
    EDGE=dict(front=-40.9, back=-41.9),
    DRUM=dict(r=(15.5, 16.7), az=DRUM_AZ, z=(-45.6, -41.9), end_r=0.6, lip_r=(16.7, 17.5), lip_z=(-42.5, -41.9),
              lip_az0=27.0),
    LANDS=dict(h=0.70, tape=0.13, z=(-38.0, -4.0), lead=0.7, front_x=((13.0, 17.0), (-17.0, -13.0)), back_x=((10.0, 15.0),),
               back_up=dict(x=(-17.0, -13.0), z=(-10.4, -4.0)), endm_y=((4.9, 8.4), (-8.4, -4.9)), endp_y=((4.9, 8.4),)),
    WIN_BACK=dict(x=(-20.9, -6.5), z_top=-10.9),
    WIN_END=dict(x=(23.3, 25.4), y=(-7.0, 3.4), z=(-40.9, -15.0)),       # dev: y -6.5..6.5 -> -7.0..3.4 (FFC fixed leg land)
    GROOVE=dict(y=(3.3, 7.2), x=(15.0, 25.6), depth=0.3, edge_r=0.6),     # FFC riser groove under the back floor (along +X)
    PAD_FACE=15.10, ROOT_R=1.0,
    PAD_A=dict(x=7.0, z=-15.8, r=3.65),                                   # dev: F10 positions; fixer rev2 (S5): r 3.5 -> 3.65 (wall 1.6 at D4.1)
    PAD_B=dict(x=18.4, z=(-38.0, -34.0), r=3.25),                         # stadium: dowel (z -38.0) + insert (z -34.0)
    F10=dict(A=(7.0, -15.8), B=(18.0, -33.3), dowel=(18.4, -38.0), dowel_d=2.0, dowel_hole=2.05, dowel_depth=3.0,
             dowel_len=5.0, torque=0.10),
    #   fixer rev2 (S5, lead decision): fingertip design case 0.10 N.m -> M2 x 4 x OD 4.0 inserts in D4.1 holes THROUGH the 4.0 back wall
    #   (flush with the pad face, 0.1 short of the well face); F10_B (18.4, -34.0) -> (18.0, -33.3): web 1.64 to the dowel hole and 1.73 to
    #   the r 26.50 stage trim at the pad face (round pad r 3.65 added to the dowel stadium PAD_B)
    PAD_B2=dict(r=3.65),
    #   F10_B at x 18.0 brings its DIN 433 washer (r 2.25) to x 15.75 - the MG90S case (x <= 16.0) sits on the plate face y 17.1 there:
    #   the washer + head sit in a 0.35 deep step of the plate (x 15.6 .. past the +X edge, z -35.62 .. the low-plate top; washer y 16.75 .. 17.05,
    #   plate 1.65 under it, compression only);
    #   the screw is driven with a 1.3 hex PRECISION screwdriver (blade 1.5 across corners) - a D4.5 shaft would touch the servo case
    F10_B_CB=dict(d=4.8, depth=0.35, z_low=-35.62),   # step bottom 0.07 under the washer, 1.36 to the dowel hole; tip 0.05 short of the well face
    RAIL=dict(x=(-6.0, 16.0), y=(13.0, 15.1), z=(-41.9, -33.9),           # new: bottom rail (tongue groove) for the pocket
              groove=dict(x=(-4.5, 14.5), y=(13.5, 15.2), z=(-39.4, -36.4))),
    # ---- lift module (P_drziak_serva) -----------------------------------------------------------------------------
    POCKET=dict(plate=dict(x=(-8.5, 17.0), y=(15.1, 17.1), z=(-41.9, -13.3), low=dict(x=(16.9, 20.9), z=(-41.9, -30.5))),
                tongue=dict(x=(-4.2, 14.2), y=(13.6, 15.1), z=(-39.35, -36.45)),
                turret=dict(x=(-8.5, -6.5), y=(15.1, 31.3), z=(-41.9, -13.3), far_top=dict(y=28.0, z=-17.0)),
                block=dict(x=(-8.5, -2.5), y=(15.1, 28.0), z=(-18.0, -13.3)),
                nut_slot=dict(x=(-5.45, -4.1), y=(21.15, 28.5), z=(-18.5, -12.8)),
                keyhole=[(6.05, (23.2, -24.2)), (3.05, (23.2, -29.8))],
                bridge=dict(r=(26.25, 31.6), az=(102.0, 131.7), z=(-43.6, -36.2), x_max=-6.6, z_low_top=-41.5, low_az0=106.5,
                            high=[((-16.9, -14.5), -37.4), ((-14.5, -6.6), -36.2)],      # tops: 1.0 under the arm tip / crank pin at BDC
                            key_holes=dict(x=(-10.0,), z=-38.5, d=2.4)),                 # F12 1.3 hex key along Y through the bridge
                lug=dict(r=(27.8, 31.6), az=(118.3, 131.7), z=(-47.2, -43.6), root_in=1.0, root_cw=0.8),
                clip=dict(plate_x=(20.9, 23.4), z=(-30.5, -18.0), ribs_x=((16.5, 17.1), (22.8, 23.4)), rib_y=(17.1, 20.6),
                          shelf_z=(-30.5, -29.0), notch_x=(19.0, 20.9))),
    # ---- crank / ear / foot ------------------------------------------------------------------------------------------
    ARM=dict(hub_r=3.5, hub_x=(-15.5, -12.5), arm_x=(-17.5, -15.5), half_w=2.5, tip_c=9.7, pin_hole=2.0, pin_x=(-19.9, -13.9),
             screw="M2.5 x 5 countersunk (ISO 10642) flush at x -17.5 into the servo output (thread UNVERIFIED)"),
    EAR=dict(t=1.5, plate_x=(-19.4, -17.9), y=(9.9, 25.1), z=(-40.5, -31.9), flange_y=(9.9, 11.4), flange_x_end=-7.5,
             flange_z=(-40.5, -36.5), bend_r=1.5, relief_z=(-36.5, -36.2), slot_w=2.20, slot_y=(11.6, 24.3),
             slot_z=(-35.30, -33.10), chamfer=1.5, holes_x=(-10.0,), hole_z=-38.5, hole_d=2.3, k_factor=0.4,
             dowel=dict(x=-13.2, z=-38.5, hole=2.05, foot_hole=2.05, foot_depth=3.0, len=4.5),   # integrator rev2: bonded in the ear, slip in the foot
             notch=dict(x=(-19.6, -14.5), z_top=-37.7),                                   # arm tip clearance at mid stroke
             fwd_trim=0.5),     # integrator rev2: plate above the relief kerf starts at y 10.4 (0.05 into the B neck back half at y 9.9)
    FOOT=dict(slot=dict(x=(9.0, 22.3), y=(-7.1, 6.7)), taps_x=(-10.0,), tap_z=-38.5, tap_d=1.6, tap_depth=7.0),
    # ---- electronics ---------------------------------------------------------------------------------------------------
    DPS=dict(x=(9.2, 22.2), y=(-6.9, 6.5), z=(-37.8, -37.0),
             zif=dict(x=(18.35, 22.2), z=(-39.0, -37.8), y=((-6.6, -2.1), (-1.6, 2.9)), part="Panasonic Y5B AYF530535 (0.5 mm, 5 p, top + bottom contact, 0.30 FFC); alt. Molex 54548-0572 (1.2 high)"),
             pads_top=[(12.6, y) for y in (0.4, 1.2, 2.0)] + [(13.2, y) for y in (-6.4, -5.4, -4.4, -3.4)],
             pads_bot=[(x, -1.85) for x in (10.6, 11.6, 12.6)]),
    # ---- FFC pair --------------------------------------------------------------------------------------------------------
    FFC=dict(w=3.0, t1=0.10, t=0.25, z=(-46.10, -43.10), r_in=16.825, r_out=23.375, static_az=30.0, u0=84.0,
             anchor_az=24.4, riser_az=(14.0, 24.4), band_F=(4.0, 7.0), x_wall=25.1, z_U0=-26.0, R_lift=3.125, R_bot=1.0,
             zh0=-38.25, zfold_x=(25.35, 28.35), band_A=(-5.85, -2.85), band_B=(-0.85, 2.15), zif_in=19.2,
             # integrator rev2: lift-loop U turned into the y-z plane (strip width radial, x 25.35..28.35) - every part of the loop
             # below z -28.5 stays at x <= 28.35, i.e. >= 1.0 from the OBAL front stack (inner faces y -29.4..-30.1) at any pan
             loop=dict(x=(25.35, 28.35), y_fix=6.875, y_mov=0.625, yc=3.75, cf_z=(-30.0, -29.4)),
             carrier=dict(z_run=-50.5, y_run=(20.35, 23.35), x_turn=21.74, zif_x=(-19.45, -12.35), zif_y=19.1, z_zif=-56.5)),
    PIGTAIL=dict(d=1.4, plug=dict(x=(17.2, 22.7), y=(17.2, 20.5), z=(-29.0, -17.0))),
    # ---- fixer rev2 (overenie2 findings) ---------------------------------------------------------------------------------
    FIX2=dict(
        journal_r=26.365,           # G1: every P_sachta surface in the PTFE band z -10.7 .. -1.9 at r <= 26.365 (was: 8 lands at 26.50)
        journal_z=(-10.7, -1.9),
        vents=dict(d=2.5, xy=[(sx * 6.25, sy * 18.0) for sx in (1, -1) for sy in (1, -1)] +
                   [(sx * 16.0, sy * 15.3) for sx in (1, -1) for sy in (1, -1)], z=(-3.6, -1.9)),   # M2: 8 vents through the top plate
        lip_trim=None,       # m1: the P_sachta trim (run 1: y >= 15.12 left 0.02; y >= 15.0 cut slivers into the drum shroud top) is replaced
                             # by a 0.35 x 0.15 rebate on the back-bottom edge of the P_drziak_serva plate (pocket_rebate below)
        pocket_rebate=dict(x=(-9.0, 9.5), y=(15.0, 17.2), z=(-42.0, -41.75)),   # plate bottom -41.9 -> -41.75 over the drum shroud / lip tops
        tongue_root_r=0.5, groove_chamfer=0.8,                          # S2: R0.5 tongue roots, 0.8 x 45 deg chamfer on the groove mouth
        ear_relief_d=1.0,                                               # S4: D1.0 drilled at the inner end of the bend-relief kerf
        under_r=16.72),                                                 # m2: FFC under-run starts on the arc r 16.72 (outside the shroud)
)
P2 = PAN2


# =====================================================================================================================
# helpers
# =====================================================================================================================
def one(s):
    """single Solid of a boolean result (largest solid)"""
    sol = list(s.solids()) if hasattr(s, "solids") else [q for x in s for q in x.solids()]
    return sol[0] if len(sol) == 1 else max(sol, key=lambda q: q.volume)


def fuse(shapes):
    shapes = [s for s in shapes if s is not None]
    return shapes[0] if len(shapes) == 1 else shapes[0].fuse(*shapes[1:])


def cut(base, cutters):
    cutters = [c for c in cutters if c is not None]
    return base.cut(*cutters) if cutters else base


def prism_x(pts_yz, x0, x1):
    w = bd.Wire.make_polygon([Vector(x0, y, z) for y, z in pts_yz], close=True)
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def prism_y(pts_xz, y0, y1):
    w = bd.Wire.make_polygon([Vector(x, y0, z) for x, z in pts_xz], close=True)
    return bd.extrude(bd.Face(w), amount=y1 - y0, dir=(0, 1, 0))


def prism_z(pts_xy, z0, z1):
    w = bd.Wire.make_polygon([Vector(x, y, z0) for x, y in pts_xy], close=True)
    return bd.extrude(bd.Face(w), amount=z1 - z0, dir=(0, 0, 1))


def pol(r, az_deg, cx=0.0, cy=0.0):
    a = math.radians(az_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def arc_pts(c, r, a0, a1, step=10.0):
    n = max(2, int(math.ceil(abs(a1 - a0) / step)) + 1)
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def sector(r0, r1, a0, a1, z0, z1, step=3.0):
    """annulus sector prism (polygonal arcs, chord error < 0.01 at r 32)"""
    n = max(2, int(math.ceil((a1 - a0) / step)) + 1)
    out = [pol(r1, a0 + (a1 - a0) * i / (n - 1)) for i in range(n)]
    inn = [pol(r0, a1 - (a1 - a0) * i / (n - 1)) for i in range(n)] if r0 > 0 else [(0.0, 0.0)]
    return prism_z(out + inn, z0, z1)


def tube_sector(ro, ri, a0, a1, z0, z1):
    """true cylindrical sector (exact arcs)"""
    t = C.cyl_z(ro, z0, z1) - C.cyl_z(ri, z0 - 0.5, z1 + 0.5) if ri > 0 else C.cyl_z(ro, z0, z1)
    return one(t & sector(0.0, ro * 1.2, a0, a1, z0 - 1, z1 + 1, 2.0))


def revolve_z(pts_rz):
    w = bd.Wire.make_polygon([Vector(r, 0, z) for r, z in pts_rz], close=True)
    return bd.revolve(bd.Face(w), axis=bd.Axis.Z, revolution_arc=360)


def strip_poly(pts, t):
    """closed polygon around an open centreline (list of 2-D points): the strip of thickness t"""
    Q = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - Q[-1][0], p[1] - Q[-1][1]) > 1e-6:
            Q.append(p)
    A = np.asarray(Q, float)
    T = np.zeros_like(A); T[1:-1] = A[2:] - A[:-2]; T[0] = A[1] - A[0]; T[-1] = A[-1] - A[-2]
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    L, R = A + N * t / 2, A - N * t / 2
    return [tuple(p) for p in L] + [tuple(p) for p in R[::-1]]


def fillet_strip(p0, p1, n1, n2, R, n=8, eps=0.03):
    """concave fillet material along a straight inside edge p0 -> p1; n1 / n2 = unit vectors along the two faces away
    from the edge (perpendicular to the edge).  Overlaps both faces by eps."""
    p0, p1, n1, n2 = (np.asarray(v, float) for v in (p0, p1, n1, n2))
    prof = [(-eps, -eps), (R, -eps)] + [(R + R * math.cos(math.radians(t)), R + R * math.sin(math.radians(t)))
                                        for t in np.linspace(-90.0, -180.0, n)] + [(-eps, R)]
    pts = [p0 + u * n1 + v * n2 for u, v in prof]
    w = bd.Wire.make_polygon([Vector(*p) for p in pts], close=True)
    d = p1 - p0
    return bd.extrude(bd.Face(w), amount=float(np.linalg.norm(d)), dir=tuple(d / np.linalg.norm(d)))


def tube_path(pts, r):
    """round tube (wire bundle) along a polyline: cylinders + spheres at the joints"""
    S = []
    for a, b in zip(pts[:-1], pts[1:]):
        v = Vector(*b) - Vector(*a)
        if v.length < 1e-6:
            continue
        cyl = bd.Cylinder(r, v.length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        S.append(bd.Location(bd.Plane(origin=a, z_dir=(v.X, v.Y, v.Z))) * cyl)
    S += [bd.Pos(*p) * bd.Sphere(r) for p in pts[1:-1]]
    return one(fuse(S))


def cable_sweep(ctrl, r):
    """round cable: circle swept along a spline through the control points (robust, smooth)"""
    sp = bd.Spline(*[Vector(*p) for p in ctrl])
    pl = bd.Plane(origin=sp @ 0, z_dir=sp % 0)
    return one(bd.sweep(pl * bd.Circle(r), path=sp))


def smooth_path(ctrl, n=24):
    """Catmull-Rom points through the control points (for cable centre lines)"""
    P = np.asarray(ctrl, float)
    P = np.vstack([P[0] - (P[1] - P[0]), P, P[-1] + (P[-1] - P[-2])])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return [tuple(float(c) for c in p) for p in out]


def path_len(pts):
    P = np.asarray(pts, float)
    return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())


def gear_profile(m, z, phase_deg=0.0, backlash=0.04, n_inv=7):
    """involute spur gear outline (20 deg), tooth k centred at phase + k * 360 / z (same generator as t4_ram)"""
    rp = m * z / 2; rb = rp * math.cos(math.radians(20.0)); ra = rp + m; rf = rp - 1.25 * m
    s = math.pi * m / 2 - backlash
    ap = math.radians(20.0)

    def inv(a):
        return math.tan(a) - a

    def half(r):
        return s / (2 * rp) + inv(ap) - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / (n_inv - 1) for i in range(n_inv)]
    pitch = 2 * math.pi / z
    out = []
    for k in range(z):
        c = math.radians(phase_deg) + k * pitch
        if rf < rb:
            out.append((rf, c - half(r0)))
        out += [(r, c - half(r)) for r in rs] + [(r, c + half(r)) for r in reversed(rs)]
        if rf < rb:
            out.append((rf, c + half(r0)))
        out.append((rf, c + pitch / 2))
    return [(r * math.cos(a), r * math.sin(a)) for r, a in out]


def crank_angle(lift):
    """servo angle (deg) for a lift 0 .. 20: lift = R (1 - cos theta)"""
    return math.degrees(math.acos(max(-1.0, min(1.0, 1.0 - lift / RC))))


def pin_pos(theta_deg):
    """crank-pin centre (y, z): bottom (theta 0) -> front (90) -> top (180)"""
    a = math.radians(theta_deg)
    return YL - RC * math.sin(a), ZL - RC * math.cos(a)


# =====================================================================================================================
# P_sachta - slim well (r <= 26.50), journal ring, hub disc, back floor, drum shroud, pads, rail
# =====================================================================================================================
def well_outline_pts():
    """outer outline of the well walls in plan (before the r 26.50 trim): back wall 2.0 for x yb2_x"""
    W = P2["WELL"]; xo = W["xo"]; xa, xb = W["yb2_x"]
    return [(-xo, W["yf"]), (xo, W["yf"]), (xo, W["yb"]), (xb, W["yb"]), (xb, W["yb2"]), (xa, W["yb2"]), (xa, W["yb"]), (-xo, W["yb"])]


def _land_y(x0, x1, side, z0, z1):
    L = P2["LANDS"]; yi = P2["WELL"]["yi"]; yf = side * (yi - L["h"]); yb = side * (yi + 0.15); d = L["h"] + 0.15
    return prism_x([(yb, z0 - d), (yf, z0), (yf, z1 - L["lead"]), (yb, z1 + 0.15)], x0, x1)


def _land_x(y0, y1, side, z0, z1):
    L = P2["LANDS"]; xi = P2["WELL"]["xi"]; xf = side * (xi - L["h"]); xb = side * (xi + 0.15); d = L["h"] + 0.15
    return prism_y([(xb, z0 - d), (xf, z0), (xf, z1 - L["lead"]), (xb, z1 + 0.15)], y0, y1)


def _pad_round(x, z, r, y0, y1, R):
    """cylindrical pad along +Y with an exact R root flare on the plane y = y0"""
    prof = [(0.0, y0 - 0.05), (r + R, y0 - 0.05), (r + R, y0)] + \
           [(r + R + R * math.cos(math.radians(t)), y0 + R + R * math.sin(math.radians(t))) for t in np.linspace(-90, -180, 9)] + \
           [(r, y1), (0.0, y1)]
    w = bd.Wire.make_polygon([Vector(rr, yy, 0) for rr, yy in prof], close=True)
    s = bd.revolve(bd.Face(w), axis=bd.Axis.Y, revolution_arc=360)
    return bd.Pos(x, 0, z) * s


def _pad_stadium(x, z0, z1, r, y0, y1, R):
    """vertical stadium pad (centres (x, z0), (x, z1)) along +Y with R root flares"""
    a, b = _pad_round(x, z0, r, y0, y1, R), _pad_round(x, z1, r, y0, y1, R)
    prof = [(x - r - R, y0 - 0.05), (x + r + R, y0 - 0.05), (x + r + R, y0)] + \
           [(x + r + R + R * math.cos(math.radians(t)), y0 + R + R * math.sin(math.radians(t))) for t in np.linspace(-90, -180, 9)] + \
           [(x + r, y1), (x - r, y1)] + \
           [(x - r - R - R * math.cos(math.radians(t)), y0 + R + R * math.sin(math.radians(t))) for t in np.linspace(-180, -90, 9)]
    mid = bd.extrude(bd.Face(bd.Wire.make_polygon([Vector(px, py, z0) for px, py in prof], close=True)), amount=z1 - z0, dir=(0, 0, 1))
    return one(fuse([a, b, mid]))


def mk_sachta():
    W, Rg, Rb, H, F, D = P2["WELL"], P2["RING"], P2["RIBS"], P2["HUB"], P2["FLOOR"], P2["DRUM"]
    xi, yi, ri, xo = W["xi"], W["yi"], W["ri"], W["xo"]
    zt = W["z_top"]; zp0 = W["plate_z"][0]; zf = P2["EDGE"]["front"]
    trim = C.cyl_z(W["r_max"], -50, 5)
    # ---- walls: outer outline (trimmed r 26.50) minus the inner rounded rectangle, z -40.9 .. -2.0
    outer = one(prism_z(well_outline_pts(), zf, zt) & trim)
    inner = C.rbox(-xi, xi, -yi, yi, zf - 1, zt + 1, ri, "z")
    walls = one(outer - inner)
    # ---- journal ring r 24.37 .. 26.37 (z -10 .. -2), lower outer chamfer 0.5; top plate z -3.5 .. -2.0
    rz0, rz1 = Rg["z"]; ch = Rg["chamfer"]
    ring = revolve_z([(Rg["r_in"], rz0), (Rg["r"] - ch, rz0), (Rg["r"], rz0 + ch), (Rg["r"], rz1), (Rg["r_in"], rz1)])
    plate = one(C.cyl_z(Rg["r"] - 0.01, zp0, zt) - inner)
    ribs = []
    for x in Rb["x"]:
        for s in (1, -1):
            ya, yb = sorted((s * (yi + 0.5), s * (Rg["r_in"] + 0.6)))
            ribs.append(C.box(x - Rb["t"] / 2, x + Rb["t"] / 2, ya, yb, Rb["z"][0], zp0 + 0.05))
    body = one(one(fuse([walls, ring, plate] + ribs)) - inner)         # the ring must not reach into the well corners (neck r 24.46)
    # ---- guide lands (PTFE strip seats)
    L = P2["LANDS"]; lz0, lz1 = L["z"]
    lands = [_land_y(a, b, -1, lz0, lz1) for a, b in L["front_x"]] + [_land_y(a, b, 1, lz0, lz1) for a, b in L["back_x"]]
    lands.append(_land_y(*L["back_up"]["x"], 1, *L["back_up"]["z"]))
    lands += [_land_x(a, b, -1, lz0, lz1) for a, b in L["endm_y"]] + [_land_x(a, b, 1, lz0, lz1) for a, b in L["endp_y"]]
    body = one(fuse([body] + lands))
    # ---- windows: back (ear / flange / crank) and +X end (FFC tails + pigtail, narrowed beside the fixed-leg land)
    Wb, We = P2["WIN_BACK"], P2["WIN_END"]
    body = one(cut(body, [C.box(*Wb["x"], yi - 0.5, W["yb2"] + 0.5, -45, Wb["z_top"]),
                          C.box(*We["x"], *We["y"], -45, We["z"][1])]))
    # ---- back floor (y >= 3.1, az <= 135) out to the walls + hub disc ring, z -41.9 .. -40.65
    fz0, fz1 = F["z"]
    a = math.radians(F["az_max"]); y0 = F["y_min"]
    reg = prism_z([(y0 / math.tan(a), y0), (40.0, y0), (40.0, 40.0), (40.0 / math.tan(a), 40.0)], fz0 - 0.5, fz1 + 0.5)
    floor = one(one(prism_z(well_outline_pts(), fz0, fz1) & trim & reg) - C.cyl_z(H["r"][0], fz0 - 1, fz1 + 1))   # keep r < 6.5 open (T_cap, F15)
    hub = C.tube_z(H["r"][1], H["r"][0], *H["z"])
    # walls of the back sector go down to -41.9 (the floor region covers the walls there; back window cut again below)
    body = one(fuse([body, floor, hub]))
    body = one(body - C.box(Wb["x"][0], Wb["x"][1], yi + 0.01, W["yb2"] + 0.5, fz1, Wb["z_top"]))   # floor stays under the window
    # ---- drum shroud r 15.5 .. 16.7 hanging from the back floor + FFC retaining lip (from lip_az0)
    a0, a1 = D["az"]; dz0, dz1 = D["z"]
    shroud = tube_sector(D["r"][1], D["r"][0], a0, a1, dz0, dz1 + 0.05)
    lip = tube_sector(D["lip_r"][1], D["lip_r"][0] - 0.05, D["lip_az0"], a1, D["lip_z"][0], D["lip_z"][1] + 0.05)
    body = one(fuse([body, shroud, lip]))
    # ---- rail (tongue groove for the pocket) + F10 pads with R1 root flares on the back wall face y 13.0
    Ra, Pa, Pb = P2["RAIL"], P2["PAD_A"], P2["PAD_B"]; pf = P2["PAD_FACE"]; Rr = P2["ROOT_R"]; yb2 = W["yb2"]
    rail = C.box(Ra["x"][0], Ra["x"][1], yb2 - 0.3, Ra["y"][1], *Ra["z"])
    padA = _pad_round(Pa["x"], Pa["z"], Pa["r"], yb2, pf, Rr)
    padB = _pad_stadium(Pb["x"], Pb["z"][0], Pb["z"][1], Pb["r"], yb2, pf, Rr)
    padB = one(fuse([padB, _pad_round(P2["F10"]["B"][0], P2["F10"]["B"][1], P2["PAD_B2"]["r"], yb2, pf, Rr)]))   # fixer rev2: insert B pad
    rail_root = fillet_strip((Ra["x"][0], yb2, Ra["z"][1]), (Ra["x"][1], yb2, Ra["z"][1]), (0, 1, 0), (0, 0, 1), Rr)
    body = one(fuse([body, rail, padA, padB, rail_root]))
    # ---- root fillets R1: hub disc / floor top against the wall inner faces (inside the well)
    zr = fz1
    roots = [fillet_strip((-6.0, -yi, zr), (6.0, -yi, zr), (0, 1, 0), (0, 0, 1), Rr),               # hub disc - front wall
             fillet_strip((Wb["x"][1], yi, zr), (xi - ri, yi, zr), (0, -1, 0), (0, 0, 1), Rr),      # floor - back wall
             fillet_strip((xi, We["y"][1] + 0.2, zr), (xi, yi - ri, zr), (-1, 0, 0), (0, 0, 1), Rr)]  # floor - +X pillar
    body = one(fuse([body] + roots))
    body = one(body & trim)                                                                    # every surface r <= 26.50
    Fx = P2["FIX2"]
    body = one(body - C.tube_z(40.0, Fx["journal_r"], *Fx["journal_z"]))   # fixer G1: journal band r <= 26.365 at EVERY azimuth (tape 0.13 -> 26.495)
    body = one(body - C.tube_z(40.0, D["lip_r"][1] + 0.05, fz0 - 8.0, fz0))                  # nothing below z -41.9 outside the drum
    # ---- cuts: windows again (fillet strips / pads must not close them), groove + edge round, inserts, dowel, pilots
    G = P2["GROOVE"]; gz1 = fz0 + G["depth"]
    N = [C.box(*Wb["x"], yi - 0.5, W["yb2"] + 0.5, fz1 + 0.01, Wb["z_top"]),
         C.box(*We["x"], *We["y"], -45, We["z"][1]),
         one(C.box(G["x"][0], G["x"][1], G["y"][0], G["y"][1], fz0 - 0.5, gz1) - C.cyl_z(D["r"][1], fz0 - 1.0, gz1 + 1.0))]   # outside the shroud
    er = G["edge_r"]
    N.append(prism_y([(xo + 0.05, gz1 - 0.05), (xo + 0.05, gz1 + er)] + arc_pts((xo - er, gz1 + er), er, 0, -90, 15) +
                     [(xo - er, gz1 - 0.05)], G["y"][0], G["y"][1]))
    Rgv = Ra["groove"]
    N.append(C.box(*Rgv["x"], *Rgv["y"], *Rgv["z"]))
    for (x, z) in (P2["F10"]["A"], P2["F10"]["B"]):
        N.append(C.cyl_y(R2["INSERT_HOLES"]["M2"]["hole"] / 2, yi - 0.5, pf + 0.5, x, z))   # fixer rev2: D4.1 through (M2 x 4 x OD 4.0 insert)
    dx, dz = P2["F10"]["dowel"]
    N.append(C.cyl_y(P2["F10"]["dowel_hole"] / 2, pf - P2["F10"]["dowel_depth"], pf + 0.5, dx, dz))
    # ---- fixer rev2: M2 vents (8 x D2.5 through the top plate into the pockets ring / ribs / walls - no suction cup when printed
    # top plate toward the build plate on supports; hidden under the collar disc), m1 lip bump under the pocket plate, S2 groove
    # mouth chamfers (room for the R0.5 tongue roots of P_drziak_serva)
    V = Fx["vents"]
    N += [C.cyl_z(V["d"] / 2, *V["z"], x, y) for x, y in V["xy"]]
    Lt = Fx["lip_trim"]
    if Lt:
        N.append(one(C.box(-20.0, 20.0, Lt["y_min"], 20.0, *Lt["z"]) & C.cyl_z(Lt["r"][1], Lt["z"][0] - 1, Lt["z"][1] + 1)))
    ch = Fx["groove_chamfer"]; gy1 = Ra["y"][1]
    for zg, sg in ((Rgv["z"][1], 1), (Rgv["z"][0], -1)):
        N.append(prism_x([(gy1 + 0.05, zg - sg * 0.05), (gy1 - ch, zg - sg * 0.05), (gy1 - ch, zg), (gy1 + 0.05, zg + sg * (ch + 0.05))],
                         Rgv["x"][0], Rgv["x"][1]))
    return one(cut(body, N)).clean()


# =====================================================================================================================
# koleso_pan - bought 36T m0.8 brass gear, face 4.0, bore 8 H7 (plain, no hub)
# =====================================================================================================================
def mk_koleso():
    G = R2["GEAR_PAN"]; z0, z1 = G["plane"]
    phase = PAN_AZ % (360.0 / 36)                       # a tooth faces the pinion (tooth gap of the pinion faces the axis)
    body = prism_z(gear_profile(G["m"], G["z"][1], phase, 0.04), z0, z1)
    return one(body - C.cyl_z(G["gear"]["bore"] / 2, z0 - 0.5, z1 + 0.5)).clean()


# =====================================================================================================================
# lift servo (bought, unchanged position) + pocket + crank
# =====================================================================================================================
def mk_servo():
    """MG90S (E2 model of the neck): case x -6.5 .. 16.0 (22.5) x y 17.1 .. 29.3 x z -41.1 .. -18.3, keyhole turret
    (boss r 5.9 + lobe r 2.9 at 5.6) 6.0 long, spline D4.8 x 3.0 with the horn-screw hole, upper tab kept (lower tab cut off),
    lead exit stub on the top end face near the bottom cover (x 11.4 .. 15.9)."""
    S = C.MG90S; xt, xb = C.LIFT_X; Lc = C.LIFT_CASE
    case = C.box(xt, xb, *Lc["y"], *Lc["z"])
    lr, ld = S["lobe"]
    tur = [C.cyl_x(S["boss_r"], xt - S["turret"], xt + 0.2, YL, ZL), C.cyl_x(lr, xt - S["turret"], xt + 0.2, YL, ZL - ld),
           C.box(xt - S["turret"], xt + 0.2, YL - lr, YL + lr, ZL - ld, ZL)]
    spl = C.cyl_x(S["spline"][0] / 2, xt - S["turret"] - S["spline"][1], xt - S["turret"] + 0.2, YL, ZL)
    T = S["tab"]; zt = Lc["z"][1]
    tab = C.box(xb - T["from_bottom"][1], xb - T["from_bottom"][0], *Lc["y"], zt - 0.2, zt + T["ext"])
    lead = C.box(11.4, 15.9, 21.7, 24.7, zt - 0.2, zt + 0.8)          # lead leaves flat, bent at once (see kabel_zdvih)
    s = one(fuse([case] + tur + [spl, tab, lead]))
    N = [C.cyl_x(T["hole_d"] / 2, xb - T["from_bottom"][1] - 0.5, xb - T["from_bottom"][0] + 0.5, YL, zt + T["hole"]),
         C.cyl_x(1.25, xt - S["turret"] - S["spline"][1] - 0.5, xt - S["turret"] + 2.0, YL, ZL)]
    return one(cut(s, N))


def _keyhole_yz(grow=0.0):
    (r1, c1), (r2, c2) = P2["POCKET"]["keyhole"]
    # lobe below the boss + its flanks (convex keyhole outline in the y-z plane)
    a = math.degrees(math.asin(min(1.0, (r2 + grow) / (r1 + grow))))
    pts = arc_pts(c1, r1 + grow, -90 + a, 270 - a, 6.0) + arc_pts(c2, r2 + grow, 180, 360, 15.0)
    return pts


def mk_drziak():
    Q = P2["POCKET"]; pl, tg, tu, bl, ns = Q["plate"], Q["tongue"], Q["turret"], Q["block"], Q["nut_slot"]
    S = [C.box(*pl["x"], *pl["y"], *pl["z"]), C.box(*pl["low"]["x"], *pl["y"], *pl["low"]["z"]),
         C.box(*tg["x"], *tg["y"], *tg["z"]),
         C.box(*tu["x"], tu["y"][0], tu["y"][1], tu["z"][0], tu["far_top"]["z"]),
         C.box(*tu["x"], tu["y"][0], tu["far_top"]["y"], tu["far_top"]["z"] - 0.1, tu["z"][1]),
         C.box(*bl["x"], *bl["y"], *bl["z"])]
    # ---- stop bridge + lug (sectors), trimmed to x <= -6.6; below z -41.9 only inside az >= 106.5
    B, Lg = Q["bridge"], Q["lug"]
    secb = sector(B["r"][0], B["r"][1], B["az"][0], B["az"][1], -41.9, -30.0)
    br = [one(secb & C.box(x0, x1, 0, 40, -41.95, ztop)) for (x0, x1), ztop in B["high"]]
    brl = sector(B["r"][0], B["r"][1], B["low_az0"], B["az"][1], B["z"][0], B["z_low_top"])
    lug = sector(Lg["r"][0], Lg["r"][1], Lg["az"][0], Lg["az"][1], Lg["z"][0], Lg["z"][1] + 0.05)
    # lug roots: R1.5 on the inner side (arc r 27.6, under the bridge), R0.8 on the CW contact side (pin 1 clearance)
    ri = Lg["r"][0]; R1 = Lg["root_in"]; zb = Lg["z"][1]
    prof = [(ri + 0.03, zb + 0.03), (ri - R1, zb + 0.03)] + \
           [(ri - R1 + R1 * math.cos(math.radians(t)), zb - R1 + R1 * math.sin(math.radians(t))) for t in np.linspace(90, 0, 9)] + \
           [(ri + 0.03, zb - R1)]
    wq = bd.Wire.make_polygon([Vector(rr, 0, zz) for rr, zz in prof], close=True)
    root_in = bd.revolve(bd.Face(wq), axis=bd.Axis.Z, revolution_arc=Lg["az"][1] - Lg["az"][0])
    root_in = bd.Rot(0, 0, Lg["az"][0]) * root_in
    a = math.radians(Lg["az"][0]); e = (math.cos(a), math.sin(a), 0.0); t_cw = (math.sin(a), -math.cos(a), 0.0)
    rc = Lg["root_cw"]
    ro_ = Lg["r"][1] - 0.06
    root_cw = fillet_strip((ri * e[0], ri * e[1], zb), (ro_ * e[0], ro_ * e[1], zb), t_cw, (0, 0, -1), rc)
    S += br + [brl, lug, root_in, root_cw]
    # fixer rev2 S2: R0.5 root fillets along the two long tongue / plate edges (bending root under L2; was R0)
    Rt = P2["FIX2"]["tongue_root_r"]; yp = tg["y"][1]
    S += [fillet_strip((tg["x"][0], yp, tg["z"][1]), (tg["x"][1], yp, tg["z"][1]), (0, 0, 1), (0, -1, 0), Rt),
          fillet_strip((tg["x"][0], yp, tg["z"][0]), (tg["x"][1], yp, tg["z"][0]), (0, 0, -1), (0, -1, 0), Rt)]
    body = one(fuse(S))
    # ---- cuts: keyhole (closed), F10 holes + dowel hole, F11 hole + nut slot, tool notches in the bridge, wire notch
    N = [prism_x(_keyhole_yz(0.0), tu["x"][0] - 1.0, tu["x"][1] + 1.0)]
    for (x, z) in (P2["F10"]["A"], P2["F10"]["B"]):
        N.append(C.cyl_y(2.3 / 2, pl["y"][0] - 3.0, pl["y"][1] + 0.5, x, z))
    Rb = P2["FIX2"]["pocket_rebate"]                                                       # fixer rev2 (m1): clear the drum shroud / lip top
    N.append(C.box(*Rb["x"], *Rb["y"], *Rb["z"]))                                         # (z <= -41.85, y <= 15.12) by 0.1
    cb = P2["F10_B_CB"]; xb_, zb_ = P2["F10"]["B"]                                        # fixer rev2: washer step at F10_B, OPEN to the
    N.append(C.box(xb_ - cb["d"] / 2, pl["low"]["x"][1] + 0.6, pl["y"][1] - cb["depth"], pl["y"][1] + 0.5,  # +X edge and the low-plate top
                   cb["z_low"], pl["low"]["z"][1] + 0.05))                                # (no thin rim; 1.65 of plate under the washer)
    dx, dz = P2["F10"]["dowel"]
    N.append(C.cyl_y(P2["F10"]["dowel_hole"] / 2, tg["y"][0] - 2.0, pl["y"][1], dx, dz))          # through the 2.0 plate (ends at the shelf)
    zt = C.LIFT_CASE["z"][1]; zh = zt + C.MG90S["tab"]["hole"]
    N.append(C.cyl_x(2.3 / 2, ns["x"][0] - 0.6, bl["x"][1] + 0.5, YL, zh))
    N.append(C.box(*ns["x"], *ns["y"], *ns["z"]))
    Kh = B["key_holes"]
    for x in Kh["x"]:
        N.append(C.cyl_y(Kh["d"] / 2, 15.0, 40.0, x, Kh["z"]))
    return one(cut(body, N)).clean()


def mk_rameno(theta=0.0):
    """bought aluminium single servo arm (simplified): hub D7 x 3 (x -15.5 .. -12.5) on the spline, arm 2.0 thick
    (x -17.5 .. -15.5), 5 wide, to r 12.2; crank-pin hole D2.0 at r 10.00; centre screw countersunk flush at x -17.5"""
    A = P2["ARM"]
    al = math.degrees(math.asin((A["hub_r"] - A["half_w"]) / A["tip_c"]))
    prof = arc_pts((YL, ZL), A["hub_r"], -al, 180.0 + al, 8.0) + arc_pts((YL, ZL - A["tip_c"]), A["half_w"], 180.0 + al, 360.0 - al, 12.0)
    arm = prism_x(prof, *A["arm_x"])
    hub = C.cyl_x(A["hub_r"], *A["hub_x"], YL, ZL)
    body = one(fuse([arm, hub]))
    N = [C.cyl_x(4.8 / 2, A["hub_x"][0] - 0.01, A["hub_x"][1] + 0.5, YL, ZL),
         C.screw_hole("M2.5c", 3.0, (A["arm_x"][0], YL, ZL), "x", 1, head_len=0.3),
         C.cyl_x(A["pin_hole"] / 2, A["arm_x"][0] - 0.3, A["arm_x"][1] + 0.3, YL, ZL - RC)]
    s = one(cut(body, N)).clean()
    return s if theta == 0 else one(bd.Pos(0, YL, ZL) * bd.Rot(-theta, 0, 0) * bd.Pos(0, -YL, -ZL) * s)


def mk_cap_kluky(theta=0.0):
    y, z = pin_pos(theta)
    return C.cyl_x(1.0, *P2["ARM"]["pin_x"], y, z)


def mk_skr_ramena(theta=0.0):
    return C.screw("M2.5c", 5, (P2["ARM"]["arm_x"][0], YL, ZL), "x", 1)


# =====================================================================================================================
# lift group: metal ear (bent 304 stainless 1.5) and aluminium foot
# =====================================================================================================================
def ear_xy_profile():
    """L section of the bent ear in plan (outer corner (x0, y0), thickness t, inner bend radius R)"""
    E = P2["EAR"]; t, R = E["t"], E["bend_r"]; x0, y0 = E["plate_x"][0], E["flange_y"][0]
    xe, ye = E["flange_x_end"], E["y"][1]
    ci = (x0 + t + R, y0 + t + R)              # bend centre
    outer = arc_pts(ci, R + t, 180, 270, 10.0)  # from (x0, ci_y) to (ci_x, y0)
    inner = arc_pts(ci, R, 270, 180, 10.0)
    return [(x0, ye)] + outer + [(xe, y0), (xe, y0 + t)] + inner + [(x0 + t, ye)]


def mk_ucho(lift=0.0):
    E = P2["EAR"]; t = E["t"]; x0, x1 = E["plate_x"]; z0, z1 = E["z"]; fz0, fz1 = E["flange_z"]
    y0, ye = E["y"]; R = E["bend_r"]; ch = E["chamfer"]
    low = prism_z(ear_xy_profile(), fz0, fz1)                                   # bent L over the flange height
    yb = y0 + t + R                                                           # flat plate starts here (bend tangent)
    yf = y0 + E.get("fwd_trim", 0.0)
    plate = prism_x([(yb - 0.02, fz0), (ye, fz0), (ye, z1 - ch), (ye - ch, z1), (yf, z1), (yf, E["relief_z"][1]),
                     (yb - 0.02, E["relief_z"][1])], x0, x1)
    body = one(fuse([low, plate]))
    hw = E["slot_w"] / 2; sy0, sy1 = E["slot_y"]; zc = (E["slot_z"][0] + E["slot_z"][1]) / 2
    N = [C.box(x0 - 0.5, x1 + 0.5, sy0 + hw, sy1 - hw, zc - hw, zc + hw), C.cyl_x(hw, x0 - 0.5, x1 + 0.5, sy0 + hw, zc),
         C.cyl_x(hw, x0 - 0.5, x1 + 0.5, sy1 - hw, zc),
         C.box(x0 - 0.5, x1 + 0.5, y0 - 0.5, yb, E["relief_z"][0], E["relief_z"][1])]            # bend relief kerf 0.3
    N += [C.cyl_y(E["hole_d"] / 2, y0 - 0.5, y0 + t + 0.5, hx, E["hole_z"]) for hx in E["holes_x"]]
    Dw = E["dowel"]; Nt = E["notch"]
    N.append(C.cyl_y(Dw["hole"] / 2, y0 - 0.5, y0 + t + 0.5, Dw["x"], Dw["z"]))
    N.append(C.box(Nt["x"][0], Nt["x"][1], y0 - 0.5, yb, Nt["z_top"], fz1 + 0.01))      # flange + bend lowered under the arm sweep
    N.append(C.cyl_x(P2["FIX2"]["ear_relief_d"] / 2, x0 - 0.5, x1 + 0.5, yb, sum(E["relief_z"]) / 2))   # fixer S4: D1.0 at the kerf end
    s = one(cut(body, N)).clean()
    return s if lift == 0 else bd.Pos(0, 0, lift) * s


def ear_flat_pattern():
    """flat pattern of L_ucho (k-factor 0.4): returns dict(outline=[...], circles=[(u, v, r)], slot=..., ba, dims)
    u = developed length from the flange end (x -7.5) through the bend to the far plate edge (y 25.1); v = z"""
    E = P2["EAR"]; t, R, k = E["t"], E["bend_r"], E["k_factor"]
    x0 = E["plate_x"][0]; y0, ye = E["y"]; xe = E["flange_x_end"]
    f_flat = xe - (x0 + t + R)                     # flange flat length  (x -16.4 .. -7.5)
    ba = math.pi / 2 * (R + k * t)                 # bend allowance
    p_flat = ye - (y0 + t + R)                     # plate flat (y 12.9 .. 25.1)
    u_b0, u_b1 = f_flat, f_flat + ba
    u_end = u_b1 + p_flat
    fz0, fz1 = E["flange_z"]; z0, z1 = E["z"]; ch = E["chamfer"]; rz0, rz1 = E["relief_z"]
    fwd = (y0 + t + R) - y0 - E.get("fwd_trim", 0.0)   # plate material forward of the bend tangent above the relief
    outline = [(0.0, fz0), (u_end, fz0), (u_end, z1 - ch), (u_end - ch, z1), (u_b1 - fwd, z1), (u_b1 - fwd, rz1),
               (u_b1, rz1), (u_b1, rz0), (0.0, fz1)]
    # the relief kerf between the bend zone and the forward plate part is the cut (u_b1 - fwd .. u_b1, rz0 .. rz1)
    nz = E["notch"]["z_top"]; u_n0 = xe - E["notch"]["x"][1]
    outline = [(0.0, fz0), (u_end, fz0), (u_end, z1 - ch), (u_end - ch, z1), (u_b1 - fwd, z1), (u_b1 - fwd, rz1),
               (u_b1, rz1), (u_b1, nz), (u_n0, nz), (u_n0, fz1), (0.0, fz1)]
    holes = [(xe - hx, E["hole_z"], E["hole_d"] / 2) for hx in E["holes_x"]] + [(xe - E["dowel"]["x"], E["dowel"]["z"], E["dowel"]["hole"] / 2)]
    sy0, sy1 = E["slot_y"]; hw = E["slot_w"] / 2; zc = (E["slot_z"][0] + E["slot_z"][1]) / 2
    slot = dict(u=(u_b1 + (sy0 - (y0 + t + R)) + hw, u_b1 + (sy1 - (y0 + t + R)) - hw), v=zc, r=hw)
    holes.append((u_b1, (rz0 + rz1) / 2, P2["FIX2"]["ear_relief_d"] / 2))     # fixer S4: D1.0 drilled at the inner kerf end
    return dict(outline=outline, holes=holes, slot=slot, bend_lines=(u_b0, u_b1), ba=round(ba, 3), k=k, t=t, R=R,
                u_end=round(u_end, 3), f_flat=round(f_flat, 3), p_flat=round(p_flat, 3), relief=dict(u=(u_b1 - fwd, u_b1), v=(rz0, rz1)))


def write_ear_dxf(path):
    """minimal DXF R12 (LINE / CIRCLE / ARC) of the flat pattern, origin = flange end at z 0; units mm"""
    fp = ear_flat_pattern()
    v0 = P2["EAR"]["flange_z"][0]
    ent = []

    def line(a, b, layer="CUT"):
        ent.append(f"0\nLINE\n8\n{layer}\n10\n{a[0]:.4f}\n20\n{a[1] - v0:.4f}\n30\n0\n11\n{b[0]:.4f}\n21\n{b[1] - v0:.4f}\n31\n0")
    O = fp["outline"]
    for a, b in zip(O, O[1:] + O[:1]):
        line(a, b)
    for u, v, r in fp["holes"]:
        ent.append(f"0\nCIRCLE\n8\nCUT\n10\n{u:.4f}\n20\n{v - v0:.4f}\n30\n0\n40\n{r:.4f}")
    s = fp["slot"]; (u0, u1), vc, r = s["u"], s["v"], s["r"]
    line((u0, vc + r), (u1, vc + r)); line((u0, vc - r), (u1, vc - r))
    ent.append(f"0\nARC\n8\nCUT\n10\n{u0:.4f}\n20\n{vc - v0:.4f}\n30\n0\n40\n{r:.4f}\n50\n90\n51\n270")
    ent.append(f"0\nARC\n8\nCUT\n10\n{u1:.4f}\n20\n{vc - v0:.4f}\n30\n0\n40\n{r:.4f}\n50\n270\n51\n90")
    Ez = P2["EAR"]["flange_z"]
    for ub in fp["bend_lines"]:
        line((ub, Ez[0]), (ub, Ez[1]), "BEND")
    with open(path, "w") as f:
        f.write("0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n" + "\n".join(ent) + "\n0\nENDSEC\n0\nEOF\n")
    return fp


def mk_pata(lift=0.0):
    Fo = R2["FOOT"]; F = P2["FOOT"]; z0, z1 = Fo["z"]
    body = C.rbox(*Fo["x"], *Fo["y"], z0, z1, Fo["corner_r"], "z")
    N = [C.cyl_z(Fo["hole_d"] / 2, z0 - 0.5, z1 + 0.5), C.box(F["slot"]["x"][0], Fo["x"][1] + 0.5, *F["slot"]["y"], z0 - 0.5, z1 + 0.5)]
    N += [C.cyl_y(F["tap_d"] / 2, Fo["y"][1] - F["tap_depth"], Fo["y"][1] + 0.5, x, F["tap_z"]) for x in F["taps_x"]]
    Dw = P2["EAR"]["dowel"]
    N.append(C.cyl_y(Dw["foot_hole"] / 2, Fo["y"][1] - Dw["foot_depth"], Fo["y"][1] + 0.5, Dw["x"], Dw["z"]))
    s = one(cut(body, N)).clean()
    return s if lift == 0 else bd.Pos(0, 0, lift) * s


def mk_dps_krk(lift=0.0):
    """DPS_krk: FR4 0.8 13.0 x 13.4, top face z -37.0 (0.5 under the neck bottom), 2 x ZIF (Panasonic Y5B AYF530535, 5 p 0.5 mm) on the underside
    (mouths at x 22.2 facing +X), 7 + 3 solder-pad keep-outs (neck wires on top, lift pigtail underneath)"""
    D = P2["DPS"]; z0, z1 = D["z"]; Z = D["zif"]
    S = [C.box(*D["x"], *D["y"], z0, z1)]
    S += [C.box(*Z["x"], y0, y1, Z["z"][0], z0 + 0.02) for y0, y1 in Z["y"]]
    S += [C.box(x - 0.4, x + 0.4, y - 0.3, y + 0.3, z1 - 0.02, z1 + 0.1) for x, y in D["pads_top"]]
    S += [C.box(x - 0.4, x + 0.4, y - 0.35, y + 0.35, z0 - 0.15, z0 + 0.02) for x, y in D["pads_bot"]]
    s = one(fuse(S))
    return s if lift == 0 else bd.Pos(0, 0, lift) * s


# =====================================================================================================================
# FFC pair (2 x 0.5 mm 5-pole, 3.0 wide, stacked = one strip 3.0 x 0.25) - pan rolling loop, riser, lift loop, tails
# =====================================================================================================================
def k_loop():
    F = P2["FFC"]
    return F["r_in"] / (F["r_in"] + F["r_out"])


def u_turn(pan):
    return P2["FFC"]["u0"] + k_loop() * pan


def loop_centreline(pan=0.0):
    """plan centre line (B frame) of the pan rolling loop at head pan `pan`: inner run on the drum from the rotating
    anchor (stage az 24.4) -> U-turn (R 3.275) -> outer run on the static wall -> static anchor (B az 26.3)"""
    F = P2["FFC"]; ri, ro = F["r_in"], F["r_out"]; u = u_turn(pan)
    a_in = F["anchor_az"] + pan
    a_st = F["static_az"] - math.degrees(F["w"] / 2 / ro)
    pts = [pol(ri, a) for a in np.arange(a_in, u - 0.5, 1.0)] + [pol(ri, u)]
    rm, Ru = (ri + ro) / 2, (ro - ri) / 2
    c = pol(rm, u); ur = (math.cos(math.radians(u)), math.sin(math.radians(u))); ut = (-ur[1], ur[0])
    for ph in np.arange(175.0, 4.0, -5.0):
        cs, sn = math.cos(math.radians(ph)), math.sin(math.radians(ph))
        pts.append((c[0] + Ru * (cs * ur[0] + sn * ut[0]), c[1] + Ru * (cs * ur[1] + sn * ut[1])))
    pts += [pol(ro, a) for a in np.arange(u, a_st, -1.0)] + [pol(ro, a_st)]
    return pts


def fpc_loop(pan=0.0):
    """pan rolling loop (stacked pair) in the B frame at pan `pan` (z band -46.1 .. -43.1)"""
    F = P2["FFC"]
    return prism_z(strip_poly(loop_centreline(pan), F["t"]), *F["z"])


def loop_lengths(pan=0.0):
    F = P2["FFC"]; u = u_turn(pan)
    inner = math.radians(u - (F["anchor_az"] + pan)) * F["r_in"]
    outer = math.radians(u - F["static_az"]) * F["r_out"]
    return inner, outer, math.pi * (F["r_out"] - F["r_in"]) / 2, u


def ffc_static():
    """static part (B frame): vertical through the deck slot at B az 30 (crease into the outer run), horizontal +Y through
    the cradle-wall slot at z -50.5, crease, stacked run -X at y 20.35 .. 23.35 to the carrier ZIF zone (approximate route
    in the RAM zone)"""
    F = P2["FFC"]; Cr = F["carrier"]; ro = F["r_out"]; t = F["t"]; hw = F["w"] / 2
    a = math.radians(F["static_az"]); c = (ro * math.cos(a), ro * math.sin(a))
    da = math.degrees(hw / ro)
    vert = tube_sector(ro + t / 2, ro - t / 2, F["static_az"] - da, F["static_az"] + da, Cr["z_run"] - t / 2, F["z"][1])
    zr = Cr["z_run"]
    hor = C.box(c[0] - hw, c[0] + hw, c[1] - 0.3, Cr["y_run"][1], zr - t / 2, zr + t / 2)
    run = C.box(Cr["zif_x"][0] - hw, c[0] + hw, *Cr["y_run"], zr - t / 2, zr + t / 2)
    return one(fuse([vert, hor, run]))


def ffc_carrier_tails():
    """FFC-A / FFC-B single (0.1, stiffened end 0.3) from the stacked run down into the FH12 ZIFs (top entry, z -53.5)"""
    F = P2["FFC"]; Cr = F["carrier"]; hw = F["w"] / 2; zr = Cr["z_run"]
    out = {}
    for nm, xc in zip(("ffc_A_nosic", "ffc_B_nosic"), Cr["zif_x"]):
        jog = C.box(xc - hw, xc + hw, Cr["zif_y"] - 0.15, Cr["y_run"][0] + 0.3, zr - 0.05 - 0.25, zr - 0.05 - 0.15)
        down = C.box(xc - hw, xc + hw, Cr["zif_y"] - 0.15, Cr["zif_y"] + 0.15, Cr["z_zif"], zr - 0.05 - 0.15)
        out[nm] = one(fuse([jog, down]))
    return out


def ffc_riser():
    """stage-fixed part: crease on the drum at the rotating anchor (stage az 14 .. 24.4), riser up the shroud face to the
    groove, radial-to-X run in the groove under the back floor (y 4.0 .. 7.0), wrap R 0.6 over the end-wall edge,
    fixed leg on the +X end wall (bonded part z -41.6 .. -30)"""
    F = P2["FFC"]; t = F["t"]; ri = 16.7; a0, a1 = F["riser_az"]
    crease = tube_sector(ri + 3 * F["t1"] + 0.45, ri, a0, a1 + 0.6, F["z"][0], F["z"][1])
    riser = tube_sector(ri + t, ri, a0, a1, F["z"][1] - 0.1, -41.6)
    yb0, yb1 = F["band_F"]; xw = F["x_wall"]; zg = -41.6
    ru = P2["FIX2"]["under_r"]                  # fixer m2: the run starts on the arc r 16.72 (outside the shroud r 16.7)
    arc = [(math.sqrt(ru ** 2 - y ** 2), y) for y in np.linspace(yb1, yb0, 7)]
    under = prism_z(arc + [(xw - 0.6, yb0), (xw - 0.6, yb1)], zg - t, zg)
    er = P2["GROOVE"]["edge_r"]
    wrap = prism_y(strip_poly(arc_pts((xw - er, zg + er), er + t / 2, -90, 0, 10), t), yb0, yb1)
    Lp = F["loop"]
    leg = C.box(xw, xw + t, yb0, yb1, zg + er - 0.05, Lp["cf_z"][0] + 0.05)
    return one(fuse([crease, riser, under, wrap, leg]))


def lift_loop_centreline(lift=0.0):
    """(y, z) centre line of the lift loop at `lift` (integrator rev2: U in the y-z plane, strip width along X 25.35..28.35):
    fixed leg (y 6.875) from the crease block CF (z -29.4) up to the U, U R 3.125 over the top, moving leg (y 0.625) down to
    the crease block CM on the moving end (z_h + 0.3).  Rolling loop: the U rises lift / 2."""
    F = P2["FFC"]; Lp = F["loop"]; R = F["R_lift"]
    zU = F["z_U0"] + lift / 2.0; zh = F["zh0"] + lift
    pts = [(Lp["y_fix"], Lp["cf_z"][1] - 0.02), (Lp["y_fix"], zU)] + arc_pts((Lp["yc"], zU), R, 0, 180, 7.5)
    pts += [(Lp["y_mov"], zU), (Lp["y_mov"], zh + 0.28)]
    return pts


def fpc_lift(lift=0.0):
    """stacked lift loop (y-z plane U) + crease block CM on the moving end (stage frame, moves with the foot except the fixed
    leg); CM = the folds that turn the two tails (bands A / B, horizontal) into the vertical moving leg"""
    F = P2["FFC"]; Lp = F["loop"]; zh = F["zh0"] + lift; t = F["t"]
    loop = prism_x(strip_poly(lift_loop_centreline(lift), t), *Lp["x"])
    # integrator rev2: fold block CF on top of the bonded leg - bend out (+X), SOFT 45 deg fold (not pressed flat, Kapton), bend up:
    # the strip leaves CF as the fixed leg of the y-z U.  CF is not bonded: for the stage removal it is opened and the free strip is
    # laid flat on the end wall (r <= 26.3), then the stage passes the glued ring
    cf = C.box(F["x_wall"], Lp["x"][1], F["band_F"][0], F["band_F"][1], *Lp["cf_z"])
    x0, x1 = Lp["x"]; ya, yb = F["band_A"][0], F["band_B"][1]; w = F["w"]
    # 45 deg fold of tail A: its folded part reaches x0 + (y - ya) only (triangle), full width from y ya + w on
    cm = prism_z([(x0, ya), (x0 + 0.01, ya), (x1, ya + w), (x1, yb), (x0, yb)], zh - 0.3, zh + 0.3)
    return one(fuse([loop, cm, cf]))


def ffc_tails_krk(lift=0.0):
    """single FFC-A / FFC-B (0.1, stiffened end 0.3 over the last 4 mm) from the Z-fold into the DPS_krk ZIFs"""
    F = P2["FFC"]; zh = F["zh0"] + lift; out = {}
    for nm, (y0, y1) in (("ffc_A_krk", F["band_A"]), ("ffc_B_krk", F["band_B"])):
        thin = C.box(F["zif_in"] + 4.0 - 0.05, F["zfold_x"][0] + 0.3, y0, y1, zh - 0.05, zh + 0.05)
        stiff = C.box(F["zif_in"], F["zif_in"] + 4.0, y0, y1, zh - 0.15, zh + 0.15)
        out[nm] = one(fuse([thin, stiff]))
    return out


def ffc_par(pan=0.0, lift=0.0):
    """the stacked pair as ONE solid (rest pose for the registry)"""
    return one(ffc_static().fuse(fpc_loop(pan), ffc_riser(), fpc_lift(lift), tol=0.002).clean())


def ffc_lengths():
    """developed length estimate per FFC (mm), rest pose"""
    F = P2["FFC"]; Cr = F["carrier"]
    inner, outer, U, u = loop_lengths(0.0)
    a = math.radians(F["static_az"]); c = (F["r_out"] * math.cos(a), F["r_out"] * math.sin(a))
    carrier = {}
    for nm, xc in zip("AB", Cr["zif_x"]):
        carrier[nm] = (F["z"][1] - Cr["z_run"]) + (Cr["y_run"][0] + 1.5 - c[1]) + (c[0] - xc) + 2.0 + (Cr["z_run"] - Cr["z_zif"])
    riser = 3.0 + 1.5 + (25.1 - 16.0) + 1.0
    Lp = F["loop"]
    cf = (Lp["x"][1] - F["x_wall"]) + (F["band_F"][1] - F["band_F"][0]) + 1.0          # bend out, 45 deg fold, bend up
    lift = path_len(lift_loop_centreline(0.0)) + (Lp["cf_z"][0] - (-41.0)) + cf
    zfold = {k: abs(Lp["y_mov"] - 0.5 * (F[f"band_{k}"][0] + F[f"band_{k}"][1])) + 3.0 + (F["zfold_x"][0] - F["zif_in"])
             for k in "AB"}
    out = {}
    for nm in "AB":
        tot = carrier[nm] + 3.0 + outer + U + inner + riser + lift + zfold[nm]
        out[nm] = dict(carrier=round(carrier[nm], 1), crease_static=3.0, outer_run=round(outer, 1), U=round(U, 1),
                       inner_run=round(inner, 1), riser=round(riser, 1), lift_loop=round(lift, 1), zfold_tail=round(zfold[nm], 1),
                       total=round(tot, 1), slack_203=round(203.0 - tot, 1))
    return out


# =====================================================================================================================
# lift-servo pigtail, inline connector (Molex PicoBlade 1.25, 3 p), MG90S lead
# =====================================================================================================================
def pigtail_ctrl(lift=0.0):
    """control points of the pigtail (3 x AWG30 silicone, bundle D1.4) from the DPS_krk underside pads, under the ZIFs,
    out through the end window under the crease block CM, +Y between the two legs of the lift-loop U, (at lift > 7.5 it
    hangs down there to z -32), under the crease block CF, then a hanging loop up to the bottom of the inline plug.
    integrator rev2: below z -28.5 every point keeps x <= 27.5 (bundle edge <= 28.2): >= 1.0 from the OBAL front stack at any
    pan (rev. 2 PAN route reached x 29.5)."""
    zp = -39.45 + lift; pl = P2["PIGTAIL"]["plug"]
    xm, ym = (pl["x"][0] + pl["x"][1]) / 2, (pl["y"][0] + pl["y"][1]) / 2
    zd = min(zp, -32.0)
    xc = 26.9                                             # bundle edge x <= 27.6 (front stack), >= 1.1 off the end wall x 25.1
    pts = [(12.6, -1.85, -38.75 + lift), (14.0, -1.85, zp), (20.0, -1.85, zp), (24.6, -1.85, zp), (26.3, -1.3, zp), (xc, 0.2, zp),
           (xc, 1.9, zp)]
    h = zp - zd                                           # drop between the legs of the U (0 below lift 7.45); the descent
    if h > 4.5:                                           # runs at y 2.95 (CM ends at 2.15, CF starts at 4.0)
        pts += [(xc, 2.8, zp - 0.7), (xc, 2.95, zp - 1.9), (xc, 2.95, zd + 1.9), (xc, 3.15, zd + 0.7), (xc, 4.3, zd)]
    elif h > 0.05:
        pts += [(xc, 2.95, zd + 0.5 * h), (xc, 4.3 + 0.15 * h, zd)]
    else:
        pts += [(xc, 3.6, zd)]
    zr = -31.4                                            # level of the rise toward the plug
    pts += [(xc, 7.6, zd), (26.7, 9.8, zd + 0.35 * (zr - zd) * 0.3), (26.0, 11.9, zd + 0.45 * (zr - zd)),
            (25.0, 13.9, zd + 0.85 * (zr - zd)), (23.8, 15.6, zr), (22.5, 17.0, zr + 0.2), (21.3, 18.1, zr + 0.6),
            (20.5, 18.65, zr + 1.05), (20.08, 18.82, pl["z"][0] - 0.7), (xm, ym, pl["z"][0] - 0.05), (xm, ym, pl["z"][0] + 0.5)]
    return pts


def pigtail(lift=0.0):
    return cable_sweep(pigtail_ctrl(lift), P2["PIGTAIL"]["d"] / 2)


def pigtail_tris(lift=0.0, step=0.1, nring=24):
    """integrator rev2: triangle mesh (n, 3, 3) of the pigtail tube built straight from its spline (the same curve as pigtail()).
    Used by the pose checks: the OCC mesher hangs on the swept surface at some lifts (e.g. 15.0) although the solid is valid.
    Ring radius r / cos(pi / nring) (circumscribed polygon: never smaller than the true tube); parallel-transport frames; end caps."""
    ctrl = pigtail_ctrl(lift); r = P2["PIGTAIL"]["d"] / 2 / math.cos(math.pi / nring)
    sp = bd.Spline(*[Vector(*p) for p in ctrl])
    n = max(20, int(sp.length / step) + 1)
    Q = np.array([tuple(sp @ t) for t in np.linspace(0.0, 1.0, 8 * n)])          # dense in the curve parameter ...
    sQ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
    sP = np.linspace(0.0, sQ[-1], n)                                              # ... resampled evenly by arc length
    P = np.stack([np.interp(sP, sQ, Q[:, i]) for i in range(3)], 1)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    ref = np.array([0.0, 0.0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    U = np.zeros_like(P); U[0] = np.cross(T[0], ref); U[0] /= np.linalg.norm(U[0])
    for i in range(1, n):
        u = U[i - 1] - np.dot(U[i - 1], T[i]) * T[i]
        U[i] = u / np.linalg.norm(u)
    W = np.cross(T, U)
    ang = np.linspace(0.0, 2 * math.pi, nring, endpoint=False)
    R = P[:, None, :] + r * (np.cos(ang)[None, :, None] * U[:, None, :] + np.sin(ang)[None, :, None] * W[:, None, :])
    tri = []
    for j in range(nring):
        k = (j + 1) % nring
        a, b, c, d = R[:-1, j], R[1:, j], R[1:, k], R[:-1, k]
        tri += [np.stack([a, b, c], 1), np.stack([a, c, d], 1)]
    for e, ring in ((P[0], R[0]), (P[-1], R[-1])):
        tri.append(np.stack([np.repeat(e[None], nring, 0), ring, np.roll(ring, -1, 0)], 1))
    return np.concatenate(tri, 0)


def mk_konektor():
    pl = P2["PIGTAIL"]["plug"]
    return C.box(*pl["x"], *pl["y"], *pl["z"])


def kabel_ctrl():
    pl = P2["PIGTAIL"]["plug"]; xm, ym = (pl["x"][0] + pl["x"][1]) / 2, (pl["y"][0] + pl["y"][1]) / 2
    return [(13.6, 22.6, -17.75), (15.4, 20.9, -17.25), (17.6, 19.6, -16.35), (19.2, 19.0, -16.0), (xm, ym, pl["z"][1] - 0.4)]


def mk_kabel():
    return cable_sweep(kabel_ctrl(), 0.6)


# =====================================================================================================================
# PTFE tapes, fasteners
# =====================================================================================================================
def ptfe_parts():
    Rg = P2["RING"]; J = R2["JOURNAL"]; L = P2["LANDS"]; t = L["tape"]; xi, yi = P2["WELL"]["xi"], P2["WELL"]["yi"]
    out = {"ptfe_pas_capu": one(C.tube_z(Rg["r"] + J["tape"], Rg["r"], *J["z"]))}
    yl, xl = yi - L["h"], xi - L["h"]; z0, z1 = L["z"][0] + 1.0, L["z"][1] - 2.0
    strips = [(a + 0.5, b - 0.5, -yl, -yl + t, z0, z1) for a, b in L["front_x"]]
    strips += [(a + 0.5, b - 0.5, yl - t, yl, z0, z1) for a, b in L["back_x"]]
    a, b = L["back_up"]["x"]; strips.append((a + 0.5, b - 0.5, yl - t, yl, L["back_up"]["z"][0] + 0.2, z1))
    strips += [(-xl, -xl + t, a + 0.25, b - 0.25, z0, z1) for a, b in L["endm_y"]]
    strips += [(xl - t, xl, a + 0.25, b - 0.25, z0, z1) for a, b in L["endp_y"]]
    for i, s in enumerate(strips, 1):
        out[f"ptfe_pasik_{i}"] = C.box(*s)
    return out


def iso7380(d, length, at, axis, sign):
    """ISO 7380-1 button head (M2: dk 3.5 k 1.3; M2.5 dk 4.7 k 1.375; M3 dk 5.7 k 1.65 - catalogue, UNVERIFIED)"""
    dk, k = {2.0: (3.5, 1.3), 2.5: (4.7, 1.375), 3.0: (5.7, 1.65)}[d]
    head = bd.Pos(0, 0, -k / 2) * bd.Cylinder(dk / 2, k)
    s = head + bd.Pos(0, 0, length / 2) * bd.Cylinder(d / 2, length)
    return one(bd.Pos(*at) * C._along(s, axis, sign))


def washer(di, do, t, at, axis, sign):
    s = bd.Pos(0, 0, t / 2) * (bd.Cylinder(do / 2, t) - bd.Cylinder(di / 2, t + 0.2))
    return one(bd.Pos(*at) * C._along(s, axis, sign))


def fasteners(lift=0.0):
    """dict name -> (solid, group, material, label, record)"""
    F = {}

    def add(name, solid, grp, mat, label, **rec):
        F[name] = (solid, grp, mat, label, rec)
    pf = P2["PAD_FACE"]; yp = P2["POCKET"]["plate"]["y"][1]
    for tag, (x, z) in (("A", P2["F10"]["A"]), ("B", P2["F10"]["B"])):
        wd = 4.5
        yp = P2["POCKET"]["plate"]["y"][1] - (P2["F10_B_CB"]["depth"] if tag == "B" else 0.0)   # fixer rev2: B sits in its counterbore
        add(f"podl_F10_{tag}", washer(2.2, wd, 0.3, (x, yp, z), "y", 1), "P", "steel",
            "podložka DIN 433 M2 (Ø4,5)", joint="F10", size="DIN 433 2.2x4.5x0.3 (DIN 125 Ø5 would touch the servo case)")
        add(f"skr_F10_{tag}", iso7380(2.0, 6.0, (x, yp + 0.3, z), "y", -1), "P", "steel", "skrutka ISO 7380 M2x6 (držiak – šachta)",
            joint="F10", size="ISO 7380-1 M2x6", head=(x, yp + 0.3, z), dir="-Y", tool_from="+Y (door, pan 0)",
            torque_Nm=P2["F10"]["torque"])
        add(f"vl_F10_{tag}", C.insert("M2", (x, pf, z), "y", -1), "P", "brass", "závitová vložka M2x4 OD4,0 lepená epoxidom",
            joint="F10", size="brass knurled insert M2 x 4 x OD 4.0, bonded (hole D4.1 through the 4.0 wall; fixer rev2)")
    dx, dz = P2["F10"]["dowel"]
    add("kolik_F10", C.cyl_y(1.0, pf - P2["F10"]["dowel_depth"], pf - P2["F10"]["dowel_depth"] + P2["F10"]["dowel_len"], dx, dz),
        "P", "steel", "kolík Ø2x5 ISO 8734 (lepený v šachte)", joint="F10", size="ISO 8734 2 m6 x 5 (bonded 3.5 in the pad)")
    zt = C.LIFT_CASE["z"][1]; zh = zt + C.MG90S["tab"]["hole"]; ns = P2["POCKET"]["nut_slot"]
    add("podl_F11", washer(2.2, 5.0, 0.3, (0.0, YL, zh), "x", 1), "P", "steel", "podložka DIN 125 M2", joint="F11", size="DIN 125 2.2x5x0.3")
    add("skr_F11", iso7380(2.0, 6.0, (0.3, YL, zh), "x", -1), "P", "steel", "skrutka ISO 7380 M2x6 (úchyt serva zdvihu)",
        joint="F11", size="ISO 7380-1 M2x6", head=(0.3, YL, zh), dir="-X", tool_from="+X (door at pan +85)",
        torque_Nm=R2["TORQUE"]["M2_nut_on_resin"])
    add("matica_F11", C.box(ns["x"][0] + 0.075, ns["x"][1] - 0.075, YL - 2.0, YL + 2.0, zh - 2.0, zh + 2.0), "P", "steel",
        "štvorhranná matica DIN 562 M2", joint="F11", size="DIN 562 M2 4.0 x 4.0 x 1.2")
    E = P2["EAR"]; Dw = E["dowel"]; yf = R2["FOOT"]["y"][1]
    add("kolik_F12", bd.Pos(0, 0, lift) * C.cyl_y(1.0, yf - Dw["foot_depth"], yf - Dw["foot_depth"] + Dw["len"], Dw["x"], Dw["z"]), "L", "steel",
        "kolík Ø2x4,5 (ucho – pätka, kov–kov, lepený v uchu)", joint="F12", size="ISO 8734 2 m6 x 4.5 (cut from x 5) bonded (Loctite 638) in the "
        "D2.05 ear-flange hole, 3.0 slip fit D2.05 in the Al foot (integrator rev2: the neck must pass the stage well and the collar-disc "
        "slot without a protruding dowel; the lift module brings the dowel in along -Y)")
    for i, hx in enumerate(E["holes_x"], 1):
        add(f"skr_F12_{i}", bd.Pos(0, 0, lift) * iso7380(2.0, 6.0, (hx, E["flange_y"][1], E["hole_z"]), "y", -1), "L", "steel",
            "skrutka ISO 7380 M2x6 (ucho – pätka, kov–kov)", joint="F12", size="ISO 7380-1 M2x6 + Loctite 222 (no washer: head on steel)",
            head=(hx, E["flange_y"][1], E["hole_z"]), dir="-Y", tool_from="+Y (door, pan 0, 1.3 hex key (long leg) through the D2.4 key hole of the stop bridge)",
            torque_Nm=R2["TORQUE"]["M2_metal"])
    return F


# =====================================================================================================================
# registry
# =====================================================================================================================
PRINTED = {   # name: (builder, group, material, Slovak label)
    "P_sachta": (mk_sachta, "P", "resin_black", "šachta krku (štíhla, r ≤ 26,5) s čapom, nábojom a bubnom FFC"),
    "P_drziak_serva": (mk_drziak, "P", "resin_black", "kapsa serva zdvihu s dorazom pan"),
}
PRINT = {   # fixer rev2 (M2 / K10): print records of the two PAN resin parts (cup-tested in K10)
    "P_sachta": dict(orientation="top plate (z -2 face) toward the build plate, axis vertical, RAISED >= 3 mm on supports (the 8 x D2.5 "
                                 "top-plate vents must open into the gap below the part)", u_away=(0.0, 0.0, -1.0), on_plate=False,
                     supports="top plate face r >= 24 (collar-disc glue land, sanded) and the plate face inside the ring; never on the journal "
                              "ring r 26.37, the guide lands or the drum shroud faces",
                     drains="8 x D2.5 vents through the top plate into the ring / rib pockets (fixer rev2 M2); the well is open at the bottom",
                     warp="journal ring tied by the top plate + ribs; sand the journal to fit (PTFE tape)"),
    "P_drziak_serva": dict(orientation="back plate (y 15.1 face) ON the build plate", u_away=(0.0, 1.0, 0.0), on_plate=True,
                           supports="none on the plate face; light supports under the bridge / lug overhangs (not on the lug contact faces)",
                           drains="open pocket, no closed cavity", warp="none (small part)"),
}
METAL = {
    "L_ucho": (mk_ucho, "L", "stainless", "ucho pätky – nerez 304 1,5 ohýbané (výkres DXF; len nerez 304, nie 5754)"),
    "L_pata": (mk_pata, "L", "alu", "pätka krku – Al plochá tyč 20x4"),
}


def _src_hash():
    src = open(os.path.abspath(__file__)).read() + json.dumps(P2, sort_keys=True, default=str) + json.dumps(R2, sort_keys=True, default=str)
    src += open(os.path.join(HERE, "t4_common.py")).read().split("# >>> additions by")[0]
    return hashlib.md5(src.encode()).hexdigest()[:10]


def cached_part(name, fn, rebuild=False):
    h = _src_hash()
    p = os.path.join(C.CACHE, f"pan2_{name}_{h}.brep")
    if os.path.exists(p) and not rebuild:
        TIMES[name] = 0.0
        return one(bd.import_brep(p))
    t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 1)
    for old in os.listdir(C.CACHE):
        if old.startswith(f"pan2_{name}_") and old.endswith(".brep"):
            os.remove(os.path.join(C.CACHE, old))
    bd.export_brep(s, p)
    return s


def build(rebuild=False, verbose=False):
    """registry of the PAN module (rev. 2): dict[name] = t4_common.part(...) - rest pose (lift 0, pan 0)"""
    parts = {}
    for name, (fn, grp, mat, label) in PRINTED.items():
        parts[name] = C.part(cached_part(name, fn, rebuild), grp, mat, True, label, print=PRINT[name])
        if verbose:
            print(f"  built {name} ({TIMES.get(name, 0)} s)", flush=True)
    for name, (fn, grp, mat, label) in METAL.items():
        parts[name] = C.part(cached_part(name, fn, rebuild), grp, mat, False, label)
    B = [  # name, builder, group, material, mass g (None = volume x density), label
        ("koleso_pan", mk_koleso, "P", "brass", None, "ozubené koleso pan 36z m0,8 mosadz, šírka 4, diera Ø8 H7 (kúpené)"),
        ("servo_zdvih", mk_servo, "P", "bought", 13.4, "servo zdvihu MG90S (spodný úchyt odrezaný)"),
        ("rameno_zdvih", mk_rameno, "P", "alu", None, "hliníkové rameno serva MG90S (kúpené), čap na r 10,00"),
        ("cap_kluky", mk_cap_kluky, "P", "steel", None, "čap kľuky Ø2x6 ISO 8734 (lisovaný + Loctite 638)"),
        ("skr_ramena", mk_skr_ramena, "P", "steel", None, "skrutka ramena M2,5x5 zápustná (kov–kov, závit serva NEOVERENÝ)"),
        ("DPS_krk", mk_dps_krk, "L", "pcb", 0.45, "doska krku FR4 0,8 + 2x ZIF Panasonic Y5B AYF530535 (5 p, 0,5 mm)"),
        ("ffc_par", ffc_par, "P", "fpc", None, "pár FFC 0,5 mm 5-pól. (spolu) – slučka pan + zdvih"),
        ("konektor_zdvih", mk_konektor, "P", "bought", 0.3, "spojka Molex PicoBlade 1,25 3-pól. (pár, voľne zaparkovaný, Kapton)"),
        ("kabel_zdvih", mk_kabel, "P", "bought", 0.3, "vodiče serva zdvihu (skrátené)"),
        ("pigtail_zdvih", pigtail, "L", "bought", 0.4, "pigtail serva zdvihu 3x AWG30 z DPS_krk"),
    ]
    for name, fn, grp, mat, mass, label in B:
        if name in ("ffc_par", "pigtail_zdvih"):
            s = cached_part(name, fn, rebuild)
        else:
            t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 2)
        extra = dict(mass=mass) if mass is not None else {}
        parts[name] = C.part(s, grp, mat, False, label, **extra)
    for name, s in ffc_tails_krk(0.0).items():
        parts[name] = C.part(s, "L", "fpc", False, "koniec FFC do ZIF na DPS_krk (s výstuhou 0,3)")
    for name, s in ffc_carrier_tails().items():
        parts[name] = C.part(s, "T", "fpc", False, "koniec FFC do ZIF FH12 na nosnej doske")
    for name, s in ptfe_parts().items():
        parts[name] = C.part(s, "P", "ptfe", False, "PTFE páska 0,13 (klzná plocha)")
    for name, (s, grp, mat, label, rec) in fasteners().items():
        parts[name] = C.part(s, grp, mat, False, label, fastener=rec)
    return parts


LIFT_PARTS = ("L_pata", "L_ucho", "DPS_krk", "skr_F12_1", "kolik_F12", "ffc_A_krk", "ffc_B_krk")
CRANK_PARTS = ("rameno_zdvih", "cap_kluky")


def pose_parts(lift=0.0):
    """solids of everything that moves with the lift (stage frame): foot group translated, crank rotated, cables re-posed"""
    th = crank_angle(lift)
    mv = bd.Pos(0, 0, lift)
    out = {"rameno_zdvih": mk_rameno(th), "cap_kluky": mk_cap_kluky(th), "L_pata": mk_pata(lift), "L_ucho": mk_ucho(lift),
           "DPS_krk": mk_dps_krk(lift), "pigtail_zdvih": pigtail(lift), "fpc_lift": fpc_lift(lift)}
    out.update(ffc_tails_krk(lift))
    F = fasteners(lift)
    for n in ("skr_F12_1", "kolik_F12"):
        out[n] = F[n][0]
    return out


def expected_bbox():
    W = P2["WELL"]; Fo = R2["FOOT"]; E = P2["EAR"]
    return {
        "L_pata": (*Fo["x"], *Fo["y"], *Fo["z"]),
        "L_ucho": (E["plate_x"][0], E["flange_x_end"], E["y"][0], E["y"][1], E["z"][0], E["z"][1]),
    }


SOURCES = {
    "koleso_pan": "plain spur gear m0.8 z36, 20 deg, face 4.0, d 28.8 / da 30.4, bore 8.00 H7, brass C3604 (KHK BSS0.8-36 class / "
                  "McMaster brass 0.8 mod / Accu 0.8MOD - shape and bore UNVERIFIED; if hubbed: hub faced off, bored 8 H7 on a lathe). "
                  "Teeth modelled with the t4_ram generator (backlash 0.04 per gear), a tooth faces the pinion (az 254.29)",
    "servo_zdvih": "TowerPro MG90S, E2 model of the neck (user drawing): case 22.5 x 12.2 x 22.8, turret D11.8 x 6.0 + lobe r 2.9 at 5.6, "
                   "spline D4.8 x 3.0 (tooth count 20/21/25 UNVERIFIED - count before buying the arm), upper tab 2.5, hole D2.2; lower tab cut off",
    "rameno_zdvih": "aluminium single servo arm for the MG90S spline (generic 'MG90S/SG90 aluminium servo arm 25T M2' listings - product, "
                    "thickness and hub UNVERIFIED); modelled hub D7 x 3, arm 2.0 x 5 to r 12.2; crank-pin hole D2.00 drilled at r 10.00 +-0.05",
    "cap_kluky": "dowel pin ISO 8734 2 m6 x 6, pressed + Loctite 638 into the Al arm (metal-metal), x -19.9 .. -13.9",
    "DPS_krk": "FR4 0.8, 13.0 x 13.4 (custom 2-layer, any PCB house); ZIF Panasonic Y5B AYF530535 (0.5 mm, 5 p, top + bottom "
               "contact, for 0.30 FFC, back lock; height about 1.0 - UNVERIFIED, vendor page not reachable) or Molex 54548-0572 (bottom contact, "
               "0.30 FFC, 1.2 high, search snippet); envelope modelled 1.2 high (z -39.0 .. -37.8).  fixer rev2: FH19C takes 0.20 FPC only",
    "ffc_par": "2 x stock FFC 0.5 mm pitch, 5 conductors, 3.0 wide, 0.10 flex / 0.3 stiffened ends, 203 mm, Type A (same side) - "
               "Molex Premo-Flex 15166 series 5-circuit 203 mm (part number UNVERIFIED) or Wurth WR-FFC 0.5 mm 5 p 200 mm; stacked pair "
               "modelled as one strip 3.0 x 0.25; creases (45 deg flat folds) only in the static / bonded parts",
    "konektor_zdvih": "Molex PicoBlade 1.25 mm 3 p wire-to-wire: 51047-0300 plug + 51021-0300 receptacle (hobby: pre-crimped 'micro JST "
                      "1.25 3-pin' pigtail pairs); mated envelope 5.5 x 3.3 x 12 (length UNVERIFIED)",
    "pigtail_zdvih": "3 x AWG30 silicone, bundle D1.4, about 70 mm, soldered to the 3 underside pads of DPS_krk",
    "kabel_zdvih": "MG90S lead shortened to about 40 mm, PicoBlade receptacle crimped / soldered on",
    "L_ucho": "304 stainless sheet 1.5 (preferred, section 17.5), inner bend R 1.5 (= t), k-factor 0.4; flat pattern stl/L_ucho_rozvin.dxf",
    "L_pata": "aluminium flat bar 20 x 4 (EN AW-6060 / 6061 / 5754), cut 44.6, filed to 19.6; 2 x M2 tapped (drill 1.6 x 7, thread 5)",
    "ptfe_pas_capu": "PTFE tape 0.13 x 7 x 167 on the journal ring (r 26.37 -> 26.50), z -10 .. -3",
}
for _i in range(1, 8):
    SOURCES[f"ptfe_pasik_{_i}"] = "PTFE tape 0.13 on the guide land (neck gap 0.30 bare / 0.17 taped)"
ASSEMBLY = {
    "P_sachta": ("B4", "inserts F10 + dowel bonded, PTFE tapes; 36T gear bonded under the hub disc on the deck set (centred by the taped boss)"),
    "koleso_pan": ("B4", "epoxy on the gear top face, gear tips centred in the drum shroud with a 0.3 shim strip, 24 h"),
    "ffc_par": ("B4", "rotating anchor (Kapton + epoxy dot) at stage az 14..24, riser + groove + fixed leg bonded flat (z -41.6 .. -30)"),
    "P_drziak_serva": ("B5 / T8", "MG90S inserted along -X (turret through the closed keyhole), F11; ear hung on the pin; module -Y "
                                  "through the door (tongue into the rail, dowel), F10 A/B"),
    "L_pata": ("B6", "drilled, slotted, tapped; bonded to the FRONT neck half only"),
    "DPS_krk": ("B6", "neck wires + pigtail soldered on the bench, board bonded into the foot slot"),
    "L_ucho": ("T8 / T11", "hung on the crank pin before the module goes in; F12 x 2 with a 1.3 hex key through the D2.4 key holes of the bridge"),
}
STEP_MAX = 12_000_000


def read_stl(path):
    import struct
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(float)


def mesh_stats(T):
    V, inv = np.unique(np.round(T.reshape(-1, 3), 5), axis=0, return_inverse=True)
    Fi = inv.reshape(-1, 3)
    Fi = Fi[(Fi[:, 0] != Fi[:, 1]) & (Fi[:, 1] != Fi[:, 2]) & (Fi[:, 0] != Fi[:, 2])]
    a, b, c = V[Fi[:, 0]], V[Fi[:, 1]], V[Fi[:, 2]]
    v6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    vol = v6.sum() / 6.0
    cog = ((a + b + c) * v6[:, None]).sum(0) / (24.0 * vol) if abs(vol) > 1e-9 else np.zeros(3)
    E = np.concatenate([Fi[:, [0, 1]], Fi[:, [1, 2]], Fi[:, [2, 0]]])
    key = np.sort(E, axis=1); key = key[:, 0].astype(np.int64) * (len(V) + 1) + key[:, 1]
    _, cnt = np.unique(key, return_counts=True)
    dkey = E[:, 0].astype(np.int64) * (len(V) + 1) + E[:, 1]
    _, dcnt = np.unique(dkey, return_counts=True)
    return dict(tris=int(len(Fi)), volume=float(vol), cog=[round(float(x), 3) for x in cog], open_edges=int((cnt == 1).sum()),
                nonmanifold_edges=int((cnt > 2).sum()), flipped_edges=int((dcnt > 1).sum()))


def main(argv):
    rebuild = "--rebuild" in argv
    T0 = time.time()
    print("== t4_pan rev2: build ==", flush=True)
    parts = build(rebuild, verbose=True)
    print(f"build {time.time() - T0:.1f} s, {len(parts)} parts", flush=True)
    exp = expected_bbox()
    recs, bad = [], []
    print(f"{'part':18s} {'grp':3s} {'mat':11s} valid sol {'volume':>9s}  bbox x / y / z{'':36s} build s")
    for name, p in parts.items():
        r = C.check_part(name, p)
        if name in exp:
            r["bbox_expected"] = [round(v, 3) for v in exp[name]]
            r["bbox_ok"] = all(abs(u - v) <= 0.06 for u, v in zip(r["bbox"], exp[name]))
            r["ok"] = r["ok"] and r["bbox_ok"]
        r["build_s"] = TIMES.get(name, 0.0) or 0.0
        b = r["bbox"]
        print(f"{name:18s} {p['group']:3s} {p['mat']:11s} {str(r['valid'])[0]}     {r['n_solids']}  {r['volume']:9.2f}  "
              f"{b[0]:7.2f}..{b[1]:7.2f} / {b[2]:7.2f}..{b[3]:7.2f} / {b[4]:7.2f}..{b[5]:7.2f}  {r['build_s']:5.1f}"
              + ("" if r["ok"] else "   <-- NOT OK" + (f" (bbox expected {r.get('bbox_expected')})" if not r.get("bbox_ok", True) else "")), flush=True)
        if not r["ok"]:
            bad.append(name)
        recs.append((name, p, r))
    if "--noexport" in argv:
        print("not exported; NOT OK:", bad)
        return 1 if bad else 0
    t = time.time()
    pj = os.path.join(HERE, "parts_pan.json")
    old_names = [e["name"] for e in json.load(open(pj))["parts"]] if os.path.exists(pj) else []
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True); os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    out, n_step = [], 0
    import t4_obal as O
    for name, p, r in recs:
        e = O.export_abs(name, p)
        for k in ("bbox_expected", "bbox_ok", "build_s"):
            if k in r:
                e[k] = r[k]
        n_step += e["step"] is not None
        e["ok"] = bool(r["ok"] and e["watertight"])
        if not e["ok"] and name not in bad:
            bad.append(name)
        if "fastener" in p:
            e["fastener"] = p["fastener"]
        if name in SOURCES:
            e["source"] = SOURCES[name]
        if name in ASSEMBLY:
            e["assembly_step"], e["assembly_dir"] = ASSEMBLY[name]
        if e["volume_mesh"] and p["mat"] in C.DENS and C.DENS[p["mat"]]:
            e["mass_g"] = p.get("mass", round(e["volume_mesh"] * C.DENS[p["mat"]], 2))
        out.append(e)
    stale = [n for n in old_names if n not in parts]
    for n in stale:
        for sub, ext in (("stl", ".stl"), ("step", ".step")):
            f = os.path.join(HERE, sub, n + ext)
            if os.path.exists(f):
                os.remove(f)
    fp = write_ear_dxf(os.path.join(HERE, "stl", "L_ucho_rozvin.dxf"))
    extra = {}
    fx = os.path.join(HERE, "pan2_work", "parts_pan_extra.json")
    if os.path.exists(fx):
        extra = json.load(open(fx))
    doc = dict(module="pan", revision=2, generated=time.strftime("%Y-%m-%d %H:%M:%S"),
               frame="B frame = pan-stage frame at pan 0, mm, rest pose (lift 0)",
               n_parts=len(out), all_ok=not bad, not_ok=bad, step_limit_bytes=STEP_MAX, removed_parts=stale,
               finished_parts_used=["golier_kotuc (P, glued on the stage top plate z -2)", "krk_predna_polovica / krk_zadna_polovica (L)"],
               ear_flat_pattern=dict(dxf="stl/L_ucho_rozvin.dxf", **{k: v for k, v in fp.items() if k not in ("outline",)}),
               ffc_lengths=ffc_lengths(), drum_az=DRUM_AZ, k_loop=round(k_loop(), 4),
               parts=out, pan2=json.loads(json.dumps(P2, default=str)))
    doc.update(extra)
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    mass = {}
    for e in out:
        if e.get("mass_g") is not None:
            mass[e["group"]] = mass.get(e["group"], 0.0) + e["mass_g"]
    print(f"exported {len(out)} STL + {n_step} STEP in {time.time() - t:.1f} s -> parts_pan.json; removed stale exports {stale}; "
          "mass by group (g): " + ", ".join(f"{g} {m:.2f}" for g, m in mass.items()))
    print("NOT OK:", bad if bad else "none", f"| total {time.time() - T0:.1f} s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
