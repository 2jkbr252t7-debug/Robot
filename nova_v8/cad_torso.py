"""
NOVA mini v8.0 - TORSO + NECK + ARMS (manifest "torso").
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.cad_torso [--check]
Exports STL + STEP + manifest into build_v8/ (never build/, which holds the finished v7.3).

Numbers: nova_v8/spec.py (TORSO, NECK, ARM, MICRO_SERVO, BASE.yaw_hub).  Upgraded from the approved concept
nova_v8/body.py (same outer look) to a buildable FDM design: 2.0 walls, 0.6 seams, snap fits + few hidden M2.

Kinematics / joint tags
  J1  torso (rotates on the base):  T01 T02-R/L T03 T04 T05 T06, N01 collar, A05 rings, all torso internals
  J2  pan stage:  N02 cone + spigot, N06 barrel cover, N03 hub gear
  J4/J5  arms:  A01..A04 (-R on -X = J4, -L on +X = J5) + arm servo horns
  ""  E21H yaw-servo horn (bolted to the hub fixed in the base)

Torso (superellipse 88 x 72 n2.7, z 40..105, R16 top / R8 bottom)
  T04  black turntable plate  = disc OD77 x 2.5 (z 40..42.5) - the white shells stand on it.  Underneath: housing
       OD45 for the 6806 outer race (bore 42 z 32..39, shoulder ID36 at z 39..40) reaching into the base top opening;
       ID36 through-hole for the STS3215 horn/hub, arc slot r23..29 for the yaw cable loop, 8x M2 countersunk from
       below (4 side shells, 2 band, 2 cradle).  Printed top-face-down (housing up) -> no supports.
  T01  centre band |x| <= 26.7 front -> top -> back, open bottom.  Neck hole D30, 2 collar pin holes, 3 bosses for
       the pan bracket T07 (M2 from below), 2 bottom bosses (M2 from below through T04), LED + sensor slots,
       2 bosses for the front sensor/LED board E25, rear service door opening 36 x 24 R6 with a 2.5 mm frame ledge.
  T02-R/L side shells |x| >= 27.3: seam ledges (tongue under the band edge, closes the 0.6 seam from behind and
       holds the shell against moving out), shoulder: hole D22.4 for the A05 ring + boss + stop lip (bore D16),
       2 tab blocks for the arm micro servo (2x M2 pilots), 2 bottom screw tabs (M2 from below through T04).
  T03  rear service door (band piece), 2 bottom hooks + 1 top snap latch, pry notch in the band.  No screws.
  T05  cyan light guide 28 x 3.5 (z 86) flush, flange behind the wall;  T06 frosted sensor window 18 x 3.5 (z 76),
       recessed 0.5, flange behind the wall.
Neck
  N01  black collar 42 x 34 (z 105..110), drafted 22 deg, bore D28, 2 locating pins + VHB on the band top (J1).
  N02  black cone r13 -> r10 (z 110..117) + spigot: D26 through the collar, shoulder D27.2 on the 6805 inner race
       (z 103), D25 in the bearing (z 96..103), bottom web with 2x M2 (from above, inside the bore) into N03 and a
       D8 cable hole.  Saddle-trimmed 0.3 off the barrel.  Snap ledge at z 112 for the N06 stem.  (J2)
  N06  black barrel D30 x 30 on the tilt axis (y 0, z 127), wall 2, end walls 3.5 with a cross-horn recess (1.8)
       + D3.2 pivot hole + 2 screw bosses on BOTH ends (tilt servo side chosen by the head), 2 decorative grooves,
       cable exit slot top-back, snap stem D15.6 into N02.  (J2)
  N07  dropped: the barrel ends carry the tilt-servo horn / pivot pin directly (no rotating caps needed).
Arms (egg from spec.ARM, built for the left arm, mirrored for the right)
  A01  white outer shell (local x >= +0.3), 1.8 wall.   A02 white inner shell (local x <= -0.3) + snap lip into A01
       + hub D18 on the shoulder axis with the A04 socket D15 and 2x M2 (heads on the split side, hidden by A01).
  A03  black TPU tip (inner-front-bottom), plug captured inside both shells, 0.6 seam.
  A04  black joint coupler D14.6 (x 43 -> 54.5): trimmed servo horn in a slot at the inner end, axial horn screw,
       2x M2 pilots from A02.  Rotates with the arm.      A05 black ring OD22/ID16 (= shoulder bore), 0.7 proud (J1).
Internals (internal=True)
  T07  pan bracket (PETG): 6805 housing (lip below the outer race), plate screwed to the 3 band bosses, two rails
       with tab grooves - the pan servo + gear N04 slide in from the back (1 retaining M2 at the rail ends).
  T08  yaw-servo cradle (PETG) on T04: 1.5 plate, 3 cradle walls (servo torque), 4 pads, 2 strap posts, PCB slot.
  T09  hold-down strap over the STS3215 (2x M2 into the T08 posts).
  N03  hub gear 20T m1 + flange D30 under the 6805 inner race (J2).   N04  servo gear 20T m1 on the pan horn.
  E21  Feetech STS3215 45.2 x 24.7 x 35, spline down on the yaw axis, body z 45..80;  E21H its disc horn ("").
  E22-R/L  MG90S arm servos (shaft on the shoulder axis, body toward the front, tabs on the T02 blocks).
  E22H-R/L trimmed horns;  E23 MG90S pan servo (shaft at y 20, gear-coupled 1:1 to the pan stage); E23H horn.
  E24  controller board 48 x 18.5 (ESP32-C3 SuperMini 22.5 x 18 + DRV8833 module 18 x 16) in the T08 slot, behind
       the rear door.   E25  front board (3x WS2812B behind T05, VL53L0X behind T06).   M21 6806, M22 6805.
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Cone, Cylinder, Edge, Face, Location, Plane, Pos, Rot, Sphere, Vector,
                       Wire, extrude, fillet, mirror, offset, revolve, scale)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts, superellipse_wire  # noqa: E402
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "torso"
BIG = 400.0

# ============================================================================================
# shared numbers (spec)
# ============================================================================================
TS, NK, AR, MS, BS = S.TORSO, S.NECK, S.ARM, S.MICRO_SERVO, S.BASE
TA, TB, TN = TS["w"] / 2, TS["d"] / 2, TS["n"]            # 44, 36, 2.7
T_Z0, T_Z1 = TS["z0"], TS["z1"]                            # 40, 105
R_TOP, R_BOT = TS["r_top"], TS["r_bottom"]                 # 16, 8
WALL = TS["wall"]                                          # 2.0
BAND_HW = TS["band"]["half_w"]                             # 27
SEAM = TS["band"]["seam"]                                  # 0.6
HS = SEAM / 2
LED, SEN, SH = TS["led"], TS["sensor"], TS["shoulder"]
T04_H, RING_OD = TS["bottom_plate"]["h"], TS["bottom_plate"]["ring_od"]
Z_SH = T_Z0 + T04_H                                        # 42.5 white shells stand on T04
YS = TS["yaw_servo"]
YS_L, YS_W, YS_H = YS["body"]                              # 45.2, 24.7, 35
YS_Z0, YS_Z1 = YS["z_body"]                                # 45, 80
YAW_BRG = BS["yaw_hub"]["bearing"]                         # 30/42 x 7
YAW_BRG_Z1 = BS["yaw_hub"]["z_top"]                        # 39
CO, CN = NK["collar"], NK["cone"]
PAN_BRG = NK["pan_bearing"]                                # 25/37 x 7
TLY, TLZ = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]      # 0, 127
BAR_R, BAR_L = NK["barrel_d"] / 2, NK["barrel_len"]        # 15, 30
EGG = AR["egg"]
AX_Y, AX_Z = AR["axis"]["y"], AR["axis"]["z"]              # 0, 89
MID, SPLAY = AR["mid_x"], AR["abduction_deg"]
assert abs(SH["z"] - AX_Z) < 1e-9

# ============================================================================================
# local design constants
# ============================================================================================
# --- micro servo (MG90S class) catalogue envelope -----------------------------------------------
MS_L, MS_W, MS_H = 22.8, MS["body"][1], MS["body"][2]      # 22.8 x 12.2 x 22.7 (case incl. tab level)
MS_SHAFT_END = 5.9         # shaft centre from the near end of the case (dome tangent to end + sides)
MS_TABS = MS["tabs_len"]   # 32.5
MS_TAB_Z = (15.9, 18.4)    # tab underside / top above the case bottom
MS_TAB_HOLE = 2.45         # hole centre from the tab end
MS_DOME_R, MS_DOME_H = 5.9, 3.0
MS_SPL_R, MS_SPL_H = 2.4, MS["height_with_spline"] - MS_H - MS_DOME_H     # 2.8
MS_OVER = MS_H + MS_DOME_H + MS_SPL_H                       # 28.5
TAB_X1 = MS_TAB_Z[1] - MS_H                                 # tab top relative to the case top (-4.3)
HOLE_FAR = MS_L - MS_SHAFT_END + MS_TAB_HOLE                # 19.35 from the shaft
HOLE_NEAR = MS_SHAFT_END + MS_TAB_HOLE                      # 8.35

# --- STS3215 ----------------------------------------------------------------------------------
YS_SHAFT_END = YS_W / 2    # output axis assumed centred in the square end (catalogue drawing not available)
YS_X0, YS_X1 = -YS_SHAFT_END, YS_L - YS_SHAFT_END          # -12.35 .. +32.85 (body toward robot LEFT, +X)
YS_HW = YS_W / 2

# --- arm servo placement -----------------------------------------------------------------------
ARM_SPL_X = 43.0                                           # spline tip |x| (just inside the shell surface 44)
ARM_TOP_X = ARM_SPL_X - MS_SPL_H - MS_DOME_H               # case top |x| 37.2
ARM_BOT_X = ARM_TOP_X - MS_H                               # case bottom |x| 14.5
ARM_TAB_X0, ARM_TAB_X1 = ARM_BOT_X + MS_TAB_Z[0], ARM_BOT_X + MS_TAB_Z[1]   # 30.4 .. 32.9

# --- pan drive: 1:1 spur gears 20T m1 (centre distance 20) ---------------------------------------
G_Z, G_M = 20, 1.0
G_CD = G_Z * G_M                                           # 20
G_Z0, G_Z1 = 90.5, 94.5                                    # gear face
PB_Z0, PB_Z1 = 96.0, 96.0 + PAN_BRG[2]                     # 6805 z 96..103 (top = band top underside)
PB_RI, PB_RO = PAN_BRG[0] / 2, PAN_BRG[1] / 2              # 12.5, 18.5
PAN_SERVO_Y = G_CD                                         # pan servo shaft (0, 20)
PAN_HORN_Z0, PAN_HORN_Z1 = 89.0, 92.1
PAN_SPL_TOP = 91.6
PAN_TOP_Z = PAN_SPL_TOP - MS_SPL_H - MS_DOME_H             # case top 85.8
PAN_BOT_Z = PAN_TOP_Z - MS_H                               # 63.1
PAN_TAB_Z0, PAN_TAB_Z1 = PAN_BOT_Z + MS_TAB_Z[0], PAN_BOT_Z + MS_TAB_Z[1]   # 79.0 .. 81.5
assert abs(PB_Z1 - (T_Z1 - WALL)) < 1e-9

# --- T07 pan bracket ---------------------------------------------------------------------------
T07_HOUSE_Z0 = 95.3        # housing underside (0.2 above the arm-servo cases, z 95.1)
T07_LIP_RI = 17.0
T07_HOUSE_RO = 20.5
T07_EARS = [(-20.0, -21.0), (20.0, -21.0), (-20.0, 22.0)]
T07_PLATE_Z = (96.0, 99.0)
RAIL_Y = (13.0, 28.5)
RAIL_L, RAIL_R = (-13.5, -6.2), (17.2, 24.0)   # x 24.3+ = side-shell ledge

# --- T04 / T08 ----------------------------------------------------------------------------------
YH_RO, YH_Z0 = 22.5, 31.5                                  # 6806 housing OD45 down to z 31.5
YH_BORE_R = YAW_BRG[1] / 2                                 # 21
YH_SHOULDER_R = 18.0
CABLE_SLOT = dict(r0=23.0, r1=29.0, a0=155.0, a1=205.0)
POST_A, POST_B = (-17.5, 0.0, 2.5), (35.2, 0.0, 2.2)       # strap posts (x, y, r)
SIDE_TABS = [(31.0, -18.0), (31.0, 18.0)]                  # side-shell bottom tabs (+X; mirrored)
BAND_SCREWS = [(0.0, -30.5), (0.0, 30.5)]
T04_SCREWS = [(sx * x, y) for sx in (1, -1) for (x, y) in SIDE_TABS] + BAND_SCREWS + \
    [(POST_A[0], POST_A[1]), (POST_B[0], POST_B[1])]
T08_Z1 = Z_SH + 1.5                                        # 44.0 cradle plate top
T08_HOLE_R = 12.0                                          # horn hub r 4.5 / output boss r 5 clearance
CRADLE_Z1 = 60.0
CR_T = 1.6
PCB = dict(x=24.0, y0=18.0, t=1.6, z0=44.2, z1=62.7)
STRAP_Z = (YS_Z1, YS_Z1 + 2.5)                             # 80 .. 82.5 (arm servo cases start at 82.9)

# --- door / front board -------------------------------------------------------------------------
DOOR = dict(w=36.0, h=24.0, r=6.0, zc=60.0)
E25 = dict(x=20.0, z0=71.0, z1=91.0, y0=-31.6, t=1.6, boss=(18.0, 80.0))

# --- neck ----------------------------------------------------------------------------------------
COLLAR_TAPER = 22.0
COLLAR_BORE_R = 14.0
NECK_HOLE_R = 15.0
COLLAR_PINS = [(-17.0, 0.0), (17.0, 0.0)]
SPIGOT_SH_R = 13.6
BAR_END = 3.5              # barrel end-wall thickness
HORN_RECESS = 1.8
SADDLE_GAP = 0.3

# --- arms ----------------------------------------------------------------------------------------
ZC = EGG["widest_z"] - AX_Z                 # -18
C_TOP = EGG["top_z"] - EGG["widest_z"]      # 28
C_BOT = EGG["widest_z"] - EGG["bottom_z"]   # 23
HW_, HT_ = EGG["half_w"], EGG["half_t"]     # 13, 7
ARM_WALL = 1.8
TIP_ZTOP = EGG["bottom_z"] + 11.0           # A03 patch top on the front silhouette (concept: 11 above bottom)
TIP_YB = 1.5
TIP_TILT = 45.0
HUB_R, HUB_X0 = 9.0, 51.5                    # A02 hub on the shoulder axis
A04_R, A04_X0, A04_X1 = 7.3, ARM_SPL_X, 54.5
A05_RI, A05_RO, A05_X0 = SH["bore_d"] / 2, 11.0, 40.0
A05_X1 = TA + 0.7                            # 44.7
HORN_ARM = (13.0, 5.6, 1.6)                  # trimmed micro-servo horn (length, width, thickness)
PANEL_INSET, PANEL_GROOVE, PANEL_GROOVE_D = 3.0, 0.45, 0.4   # concept lens-panel shadow groove on A01 (R01 detail)


# ============================================================================================
# helpers
# ============================================================================================

def bx(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, r, z0, z1):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_x(y, z, r, x0, x1):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_y(x, z, r, y0, y1):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def union(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out + s
    return out


def rr_face_xy(w, d, r):
    """Rounded rectangle face centred at the origin of the XY plane."""
    hw, hd = w / 2, d / 2
    corners = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        cx, cy = sx * (hw - r), sy * (hd - r)
        pts = [Vector(cx + r * math.cos(math.radians(a0 + t)), cy + r * math.sin(math.radians(a0 + t)), 0)
               for t in (0, 45, 90)]
        corners.append(pts)
    edges = []
    for i, (p0, pm, p1) in enumerate(corners):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        edges.append(Edge.make_line(p1, corners[(i + 1) % 4][0]))
    return Face(Wire(edges))


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    return Pos(cx, cy, z0) * extrude(rr_face_xy(w, d, r), z1 - z0)


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=0.0):
    """Rounded rectangle (w along X, h along Z) extruded from y0 to y1."""
    pl = Plane(origin=(cx, y0, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    return extrude(pl.location * rr_face_xy(w, h, r), y1 - y0, dir=(0, 1, 0))


def stadium_y(xc, zc, w, h, y0, y1):
    r = h / 2
    s = bx(xc - (w / 2 - r), xc + (w / 2 - r), y0, y1, zc - r, zc + r)
    return (s + cyl_y(xc - (w / 2 - r), zc, r, y0, y1) + cyl_y(xc + (w / 2 - r), zc, r, y0, y1)).clean()


def place(shape, origin, z_dir, x_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location * shape


def csk_hole(x, y, z_face, r_hole=1.2, r_head=2.2, depth=6.0):
    """Countersunk hole from a downward-facing face at z_face (screw from below)."""
    h = cyl_z(x, y, r_hole, z_face - 1, z_face + depth)
    k = r_head - r_hole
    c = Pos(x, y, z_face - 0.01) * Cone(r_head, r_hole, k + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return h + c + cyl_z(x, y, r_head, z_face - 2, z_face)


def check(name, s, vol_min=1.0):
    assert s is not None, name
    sol = s.solids()
    assert len(sol) >= 1, f"{name}: no solids"
    for so in sol:
        assert so.is_valid, f"{name}: invalid solid"
    assert s.volume > vol_min, f"{name}: volume {s.volume}"
    return s


def try_fillet(shape, edges, r, name=""):
    if not edges:
        return shape
    try:
        f = shape.fillet(r, edges)
        if f.is_valid and abs(f.volume - shape.volume) < 0.05 * shape.volume:
            return f
    except Exception as e:  # noqa: BLE001
        print(f"   [fillet skipped] {name}: {str(e)[:80]}")
    return shape


def fuse(a, b, name=""):
    """a + b with a validity / volume guard (coincident B-spline faces silently corrupt OCC fuses)."""
    r = a + b
    ok = r.is_valid and r.volume >= max(a.volume, b.volume) - 1e-3 and r.volume <= a.volume + b.volume + 1e-3
    assert ok, f"fuse failed: {name} ({a.volume:.0f} + {b.volume:.0f} -> {r.volume:.0f}, valid={r.is_valid})"
    return r


_cache: dict = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ============================================================================================
# torso outer body + offsets
# ============================================================================================

def body():
    def mk():
        w = superellipse_wire(TA, TB, TN, T_Z0, count=96)
        s = extrude(Face(w), T_Z1 - T_Z0, dir=(0, 0, 1))
        s = fillet(s.edges().group_by(Axis.Z)[-1], R_TOP)
        s = fillet(s.edges().group_by(Axis.Z)[0], R_BOT)
        assert s.is_valid
        return s
    return cached("body", mk)


def off(d):
    if d <= 0:
        return body()

    def mk():
        o = offset(body(), amount=-d)
        assert o.is_valid and o.volume < body().volume - 500, f"offset {d} failed"
        return o
    return cached(("off", round(d, 3)), mk)


def skin(d0, d1):
    return cached(("skin", d0, d1), lambda: off(d0) - off(d1))


def above(z=Z_SH):
    return bx(-BIG, BIG, -BIG, BIG, z, BIG)


def wall():
    return cached("wall", lambda: (body() - off(WALL)) & above())


# ============================================================================================
# gears
# ============================================================================================

def gear_face(z, m, phase_deg=0.0, backlash=0.12, n_inv=7):
    pa = math.radians(20.0)
    rp = m * z / 2
    rb, ra, rf = rp * math.cos(pa), rp + m, rp - 1.25 * m

    def inv(a):
        return math.tan(a) - a
    psi = math.pi / (2 * z) - backlash / (2 * rp)

    def fa(r):
        r = max(r, rb)
        return psi + inv(pa) - inv(math.acos(rb / r))
    rs = [rb + (ra - rb) * i / (n_inv - 1) for i in range(n_inv)]
    pts = []
    for k in range(z):
        c = math.radians(phase_deg) + 2 * math.pi * k / z
        a_root = fa(rb) - 0.02
        seq = [(rf, c - a_root)] + [(r, c - fa(r)) for r in rs] + [(r, c + fa(r)) for r in reversed(rs)] + \
              [(rf, c + a_root)]
        pts += [Vector(r * math.cos(a), r * math.sin(a), 0) for r, a in seq]
    return Face(Wire.make_polygon(pts, close=True))


def gear(z, m, cx, cy, z0, z1, phase_deg=0.0):
    return Pos(cx, cy, z0) * extrude(gear_face(z, m, phase_deg), z1 - z0)


# ============================================================================================
# purchased components (catalogue envelopes)
# ============================================================================================

def micro_servo_local():
    """MG90S envelope.  Local frame: origin = spline axis on the case top plane, +Z = output, +X = toward the
    far end of the case."""
    x0, x1 = -MS_SHAFT_END, MS_L - MS_SHAFT_END
    c = bx(x0, x1, -MS_W / 2, MS_W / 2, -MS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 0.6, "servo case")
    t0, t1 = MS_TAB_Z[0] - MS_H, MS_TAB_Z[1] - MS_H
    xc = (x0 + x1) / 2
    tab = bx(xc - MS_TABS / 2, xc + MS_TABS / 2, -MS_W / 2, MS_W / 2, t0, t1)
    for hx in (-HOLE_NEAR, HOLE_FAR):
        tab = tab - cyl_z(hx, 0, 1.0, t0 - 1, t1 + 1) - bx(hx, hx + math.copysign(5, hx), -0.5, 0.5, t0 - 1, t1 + 1)
    c = c + tab
    c = c + cyl_z(0, 0, MS_DOME_R, -0.01, MS_DOME_H) + cyl_z(7.2, 0, 2.8, -0.01, 1.2)
    c = c + cyl_z(0, 0, MS_SPL_R, MS_DOME_H - 0.01, MS_DOME_H + MS_SPL_H)
    c = c + bx(x1 - 0.01, x1 + 1.6, -1.6, 1.6, -MS_H + 0.8, -MS_H + 4.0)       # cable strain relief
    return c


def sts3215_local():
    """Feetech STS3215 envelope 45.2 x 24.7 x 35.  Local frame: origin = output axis on the horn face, +Z = output."""
    c = bx(YS_X0, YS_X1, -YS_HW, YS_HW, -YS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 1.5, "sts case")
    for zg in (-4.0, -YS_H + 5.0):          # case split lines
        ring = bx(YS_X0 - 1, YS_X1 + 1, -YS_HW - 1, YS_HW + 1, zg - 0.25, zg + 0.25) - \
            bx(YS_X0 + 0.3, YS_X1 - 0.3, -YS_HW + 0.3, YS_HW - 0.3, zg - 1, zg + 1)
        c = c - ring
    c = c + cyl_z(0, 0, 5.0, -0.01, 1.5)                     # output boss (spline inside the horn)
    c = c + cyl_z(0, 0, 2.95, 1.49, 1.6)
    c = c + bx(YS_X0 - 2.0, YS_X0 + 0.01, -3.0, 3.0, -YS_H + 2.0, -YS_H + 7.0)   # cable exit (shaft end, top)
    return c


def bearing(ri, ro, z0, z1, x=0.0, y=0.0):
    w = z1 - z0
    t = (ro - ri) * 0.28
    b = cyl_z(x, y, ro, z0, z1) - cyl_z(x, y, ri, z0 - 1, z1 + 1)
    groove = (cyl_z(x, y, ro - t, z0 - 1, z1 + 1) - cyl_z(x, y, ri + t, z0 - 1, z1 + 1)) - \
        cyl_z(x, y, ro, z0 + 0.35, z1 - 0.35)
    return b - groove if w > 1 else b


def horn_micro_x(sx):
    """Trimmed micro-servo horn on an arm servo spline (global, side sx)."""
    hub = cyl_x(AX_Y, AX_Z, 3.5, sx * (ARM_TOP_X + MS_DOME_H + 0.2), sx * (ARM_SPL_X + HORN_ARM[2])) - \
        cyl_x(AX_Y, AX_Z, MS_SPL_R, sx * (ARM_TOP_X + MS_DOME_H), sx * ARM_SPL_X)
    L, W, T = HORN_ARM
    arm = bx(sx * ARM_SPL_X, sx * (ARM_SPL_X + T), -W / 2, W / 2, AX_Z - L / 2 + W / 2, AX_Z + L / 2 - W / 2)
    arm = arm + cyl_x(0, AX_Z - L / 2 + W / 2, W / 2, sx * ARM_SPL_X, sx * (ARM_SPL_X + T)) + \
        cyl_x(0, AX_Z + L / 2 - W / 2, W / 2, sx * ARM_SPL_X, sx * (ARM_SPL_X + T))
    return (hub + arm).clean()


# ============================================================================================
# TORSO shells
# ============================================================================================

def side_shell_left():
    w = wall()
    s = w & bx(BAND_HW + HS, BIG, -BIG, BIG, -BIG, BIG)
    seam_e = [e for e in s.edges() if abs(e.bounding_box().min.X - (BAND_HW + HS)) < 0.02 and
              abs(e.bounding_box().max.X - (BAND_HW + HS)) < 0.02]
    s = try_fillet(s, seam_e, 0.3, "side seam")
    # seam ledge (tongue under the band edge): closes the seam from behind, keeps the shell from moving out
    # (start above z 43.5: the offset skins also contain the bottom slab z 42..43.4)
    ledge = (skin(WALL, 3.4) & bx(24.3, 28.2, -BIG, BIG, Z_SH + 1.0, BIG)) + \
        (skin(1.0, 2.2) & bx(BAND_HW + HS, 28.2, -BIG, BIG, Z_SH + 1.0, BIG))     # overlapping pieces (no shared face)
    s = s + ledge
    # shoulder: boss + hole for the A05 ring + stop lip (bore D16 = A05 ID)
    boss = cyl_x(AX_Y, AX_Z, 13.5, A05_X0 - 1.0, TA + 2) & off(0.3)       # never share the outer skin face
    s = fuse(s, boss, "shoulder boss")
    s = s - cyl_x(AX_Y, AX_Z, A05_RO + 0.2, A05_X0, TA + 5) - cyl_x(AX_Y, AX_Z, 8.6, A05_X0 - 3, TA + 5)
    # arm-servo tab blocks (screws M2 from the inside through the tabs)
    tx = ARM_TAB_X1 + 0.05
    b1 = bx(tx, 41.5, -(HOLE_FAR + 3.65), -(MS_L - MS_SHAFT_END) - 0.2, AX_Z - 3.5, AX_Z + 3.5)
    b2 = bx(tx, A05_X0 - 0.95, MS_SHAFT_END + 0.2, HOLE_NEAR + 4.15, AX_Z - 3.5, AX_Z + 3.5) + \
        bx(tx, 38.0, MS_SHAFT_END + 0.2, HOLE_NEAR + 4.15, AX_Z + 3.4, 106)
    s = fuse(s, (b1 + b2) & off(1.0), "tab blocks")
    for hy in (-HOLE_FAR, HOLE_NEAR):
        s = s - cyl_x(hy, AX_Z, 0.8, tx - 0.5, 39.0)
    # bottom screw tabs (M2 from below through T04)
    for (x, y) in SIDE_TABS:
        t = (cyl_z(x, y, 3.0, Z_SH, Z_SH + 3.5) + bx(x, 44, y - 3, y + 3, Z_SH, Z_SH + 3.5)) & off(1.0)
        s = s + t - cyl_z(x, y, 0.8, Z_SH - 1, Z_SH + 3.0)
    return s


def band():
    w = wall()
    b = w & bx(-(BAND_HW - HS), BAND_HW - HS, -BIG, BIG, -BIG, BIG)
    seam_e = [e for e in b.edges() if abs(abs(e.bounding_box().min.X) - (BAND_HW - HS)) < 0.02 and
              abs(abs(e.bounding_box().max.X) - (BAND_HW - HS)) < 0.02]
    b = try_fillet(b, seam_e, 0.3, "band seam")
    # neck hole + collar pin holes
    b = b - cyl_z(0, 0, NECK_HOLE_R, 98, 110)
    for (x, y) in COLLAR_PINS:
        b = b - cyl_z(x, y, 1.35, 100, 110)
    # bosses for the pan bracket T07 (M2 from below)
    for (x, y) in T07_EARS:
        b = b + (cyl_z(x, y, 3.0, T07_PLATE_Z[1], 106) & off(1.0))
        b = b - cyl_z(x, y, 0.8, T07_PLATE_Z[1] - 1, T07_PLATE_Z[1] + 3.5)
    # bottom bosses (M2 from below through T04)
    for (x, y) in BAND_SCREWS:
        sy = 1 if y > 0 else -1
        t = (cyl_z(x, y, 3.0, Z_SH, Z_SH + 4.5) + bx(x - 3, x + 3, y, y + sy * 8, Z_SH, Z_SH + 4.5)) & off(1.0)
        b = b + t - cyl_z(x, y, 0.8, Z_SH - 1, Z_SH + 4.0)
    # light guide + sensor window slots
    b = b - stadium_y(0, LED["z"], LED["w"], LED["h"], -TB - 5, -TB + 5)
    b = b - stadium_y(0, SEN["z"], SEN["w"], SEN["h"], -TB - 5, -TB + 5)
    # bosses for the front board E25
    for sx in (1, -1):
        bx_, bz_ = E25["boss"]
        b = b + (cyl_y(sx * bx_, bz_, 2.5, -TB - 1, E25["y0"]) & off(1.0))
        b = b - cyl_y(sx * bx_, bz_, 0.8, E25["y0"] - 1, E25["y0"] + 3.5 - 6.0)
    # rear service door: opening + frame ledge + notches for the door hooks + pry notch
    dw, dh, dr, dz = DOOR["w"], DOOR["h"], DOOR["r"], DOOR["zc"]
    b = b - rr_prism_y(dw, dh, dr, 15, 45, 0, dz)
    frame = (skin(WALL, 3.4) & rr_prism_y(dw + 6, dh + 6, dr + 3, 15, 45, 0, dz)) - \
        rr_prism_y(dw - 5, dh - 5, dr - 2.5, 14, 46, 0, dz)
    b = b + frame
    for (nx, nw, z0, z1) in door_hook_spots():
        b = b - (bx(nx - nw / 2 - 0.5, nx + nw / 2 + 0.5, 15, 45, z0 - 0.4, z1 + 0.4) & skin(1.95, 3.6))
    b = b - (bx(-4, 4, 15, 45, dz - dh / 2 - 1.2, dz - dh / 2 + 0.1) & skin(-0.01, 1.2))
    return b


def door_hook_spots():
    dh, dz = DOOR["h"], DOOR["zc"]
    zb, zt = dz - dh / 2, dz + dh / 2
    return [(-10.0, 6.0, zb - 2.7, zb + 2.0), (10.0, 6.0, zb - 2.7, zb + 2.0), (0.0, 8.0, zt - 2.0, zt + 2.7)]


def door():
    dw, dh, dr, dz = DOOR["w"], DOOR["h"], DOOR["r"], DOOR["zc"]
    d = wall() & rr_prism_y(dw - SEAM, dh - SEAM, dr - HS, 15, 45, 0, dz)
    zb, zt = dz - dh / 2, dz + dh / 2
    for (nx, nw, z0, z1) in door_hook_spots():
        if z0 < zb:          # bottom hooks: reach under the band wall below the opening
            inner = bx(nx - nw / 2, nx + nw / 2, 15, 45, zb + HS, z1)
            outer = bx(nx - nw / 2, nx + nw / 2, 15, 45, z0, zb + HS + 0.01)
        else:                # top latch: flexes, bump catches behind the band wall
            inner = bx(nx - nw / 2, nx + nw / 2, 15, 45, z0, zt - HS)
            outer = bx(nx - nw / 2, nx + nw / 2, 15, 45, zt - HS - 0.01, z1)
        d = d + (inner & skin(1.0, 3.3)) + (outer & skin(2.1, 3.3))
    return d


def light_guide():
    t = stadium_y(0, LED["z"], LED["w"] - 0.2, LED["h"] - 0.2, -TB - 5, -TB + 4) & body()
    t = t & bx(-BIG, BIG, -BIG, -(TB - WALL) + 0.01, -BIG, BIG)
    fl = stadium_y(0, LED["z"], 30.0, 6.0, -(TB - WALL) - 0.0, -(TB - WALL) + 0.6) & off(WALL)
    return t + fl


def sensor_window():
    t = stadium_y(0, SEN["z"], SEN["w"] - 0.2, SEN["h"] - 0.2, -TB - 5, -TB + 4) & off(0.5)
    t = t & bx(-BIG, BIG, -BIG, -(TB - WALL) + 0.01, -BIG, BIG)
    fl = stadium_y(0, SEN["z"], 21.0, 6.0, -(TB - WALL), -(TB - WALL) + 0.6) & off(WALL)
    return t + fl


def plate_t04():
    d = cyl_z(0, 0, RING_OD / 2, T_Z0, Z_SH)
    d = try_fillet(d, d.edges().group_by(Axis.Z)[-1], 0.8, "T04 top")
    d = try_fillet(d, d.edges().group_by(Axis.Z)[0], 0.8, "T04 bottom")
    h = cyl_z(0, 0, YH_RO, YH_Z0, T_Z0 + 0.01)
    h = try_fillet(h, h.edges().group_by(Axis.Z)[0], 0.6, "housing")
    d = d + h
    d = d - cyl_z(0, 0, YH_BORE_R, YH_Z0 - 1, YAW_BRG_Z1) - cyl_z(0, 0, YH_SHOULDER_R, YH_Z0 - 2, Z_SH + 2)
    d = d - cable_slot(T_Z0 - 2, Z_SH + 2)
    for (x, y) in T04_SCREWS:
        d = d - csk_hole(x, y, T_Z0, 1.2, 2.2, 6)
    return d


def cable_slot(z0, z1):
    c = CABLE_SLOT
    rm, hw = (c["r0"] + c["r1"]) / 2, (c["r1"] - c["r0"]) / 2
    ring = cyl_z(0, 0, c["r1"], z0, z1) - cyl_z(0, 0, c["r0"], z0 - 1, z1 + 1)
    pts = [Vector(0, 0, 0)] + [Vector(60 * math.cos(math.radians(a)), 60 * math.sin(math.radians(a)), 0)
                               for a in (c["a0"], 180.0, c["a1"])]
    wedge = Pos(0, 0, z0) * extrude(Face(Wire.make_polygon(pts, close=True)), z1 - z0)
    s = ring & wedge
    for a in (c["a0"], c["a1"]):
        s = s + cyl_z(rm * math.cos(math.radians(a)), rm * math.sin(math.radians(a)), hw, z0, z1)
    return s


# ============================================================================================
# torso internals
# ============================================================================================

def cradle_t08():
    z0, z1 = Z_SH, T08_Z1
    p = bx(-20.5, 34.0, -(YS_HW + 0.2 + CR_T + 0.6), YS_HW + 0.2 + CR_T + 0.6, z0, z1) + \
        bx(-27.5, 27.5, YS_HW + 0.2 + CR_T + 0.6, 21.8, z0, z1)
    p = p + cyl_z(POST_B[0], POST_B[1], POST_B[2] + 0.4, z0, z1)
    p = p - cyl_z(0, 0, T08_HOLE_R, z0 - 1, z1 + 1)      # only horn hub / output boss clearance: the plate
    # carries the horn-end pads over the T04 opening (r 18)
    # cradle walls (torque reaction), open toward +X
    yi = YS_HW + 0.2
    for sy in (1, -1):
        p = p + bx(YS_X0 - 0.2 - CR_T, 24.0, sy * yi, sy * (yi + CR_T), z1 - 0.3, CRADLE_Z1)
    p = p + bx(YS_X0 - 0.2 - CR_T, YS_X0 - 0.2, -(yi + CR_T), yi + CR_T, z1 - 0.3, CRADLE_Z1)
    p = p - bx(YS_X0 - 3, YS_X0 + 1, -5, 5, CRADLE_Z1 - 7, CRADLE_Z1 + 1)       # cable notch
    # servo pads at the case corners
    for (xa, xb) in ((YS_X0, YS_X0 + 5), (YS_X1 - 5, YS_X1)):
        for sy in (1, -1):
            p = p + bx(xa, xb, sy * (YS_HW - 5), sy * YS_HW, z1 - 0.3, YS_Z0)
    # strap posts
    for (x, y, r) in (POST_A, POST_B):
        p = p + cyl_z(x, y, r, z1 - 0.3, STRAP_Z[0])
        p = p - cyl_z(x, y, 0.8, z0 - 1, z0 + 7) - cyl_z(x, y, 0.8, STRAP_Z[0] - 7, STRAP_Z[0] + 1)
    # PCB slot posts
    for sx in (1, -1):
        post = bx(sx * 23.0, sx * 27.0, PCB["y0"] - 1.2, PCB["y0"] + PCB["t"] + 2.2, z1 - 0.3, PCB["z1"] - 0.2)
        groove = bx(sx * 22.0, sx * (PCB["x"] + 0.6), PCB["y0"] - 0.15, PCB["y0"] + PCB["t"] + 0.15,
                    PCB["z0"] - 0.2, PCB["z1"] + 1)
        p = p + post - groove
    return p


def strap_t09():
    x0, x1 = POST_A[0] - 3.0, POST_B[0] + 1.8
    s = bx(x0 + 4, x1 - 4, -4, 4, *STRAP_Z) + cyl_z(x0 + 4, 0, 4, *STRAP_Z) + cyl_z(x1 - 4, 0, 4, *STRAP_Z)
    s = s & bx(x0, x1, -4, 4, *STRAP_Z)
    for (x, y, r) in (POST_A, POST_B):
        s = s - cyl_z(x, y, 1.1, STRAP_Z[0] - 1, STRAP_Z[1] + 1)
    return s


def pan_bracket_t07():
    h = cyl_z(0, 0, T07_HOUSE_RO, T07_HOUSE_Z0, PB_Z1)
    plate = bx(-24.0, 24.0, -24.0, -17.0, *T07_PLATE_Z) + bx(-24.0, RAIL_R[1], 9.0, RAIL_Y[1], T07_HOUSE_Z0,
                                                               T07_PLATE_Z[1])
    p = h + plate
    for (xa, xb) in (RAIL_L, RAIL_R):
        p = p + bx(xa, xb, RAIL_Y[0], RAIL_Y[1], PAN_TAB_Z0 - 2.0, T07_HOUSE_Z0 + 0.01)
    p = p + bx(RAIL_L[1], RAIL_R[0], 12.8, 13.7, PAN_TAB_Z0 - 2.0, PAN_TAB_Z0 + 1.0)        # front stop web
    # tab grooves (servo slides in from the back, +Y)
    gz0, gz1 = PAN_TAB_Z0 - 0.25, PAN_TAB_Z1 + 0.25
    p = p - bx(RAIL_L[1] - 5.2, RAIL_L[1] + 0.2, 12.0, 30.0, gz0, gz1)
    p = p - bx(RAIL_R[0] - 0.2, RAIL_R[0] + 5.2, 12.0, 30.0, gz0, gz1)
    # bearing seat + lip, neck cable / spigot clearance
    p = p - cyl_z(0, 0, PB_RO, PB_Z0, PB_Z1 + 1) - cyl_z(0, 0, T07_LIP_RI, T07_HOUSE_Z0 - 1, PB_Z1 + 1)
    # clearance for the servo gear + horn under the plate
    p = p - cyl_z(0, PAN_SERVO_Y, 11.6, G_Z0 - 2, T07_HOUSE_Z0 + 0.0)
    # ear holes (M2 into the band bosses) + rail retaining screw pilots at the back ends
    for (x, y) in T07_EARS:
        p = p - cyl_z(x, y, 1.15, T07_HOUSE_Z0 - 2, T07_PLATE_Z[1] + 1)
    for xc in (sum(RAIL_L) / 2, sum(RAIL_R) / 2):
        p = p - cyl_y(xc, PAN_TAB_Z1 + 4.0, 0.8, RAIL_Y[1] - 6, RAIL_Y[1] + 1)
    return p & off(WALL + 0.3)             # 0.3 clear of the band's inner skin everywhere


def hub_gear_n03():
    g = gear(G_Z, G_M, 0, 0, G_Z0, G_Z1, phase_deg=90.0 + 180.0 / G_Z)
    g = g + cyl_z(0, 0, 14.3, G_Z1 - 0.01, PB_Z0)      # covers the inner race (OD 28.5), clears the arm servos
    g = g - cyl_z(0, 0, 4.0, G_Z0 - 1, PB_Z0 + 1)
    for sx in (1, -1):
        g = g - cyl_z(sx * 7.0, 0, 0.8, G_Z0 + 0.8, PB_Z0 + 1)
    return g


def servo_gear_n04():
    g = gear(G_Z, G_M, 0, PAN_SERVO_Y, G_Z0, G_Z1, phase_deg=270.0)
    L = 18.3
    rec = bx(-L / 2 + 2.95, L / 2 - 2.95, PAN_SERVO_Y - 2.95, PAN_SERVO_Y + 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(-L / 2 + 2.95, PAN_SERVO_Y, 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(L / 2 - 2.95, PAN_SERVO_Y, 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(0, PAN_SERVO_Y, 3.7, G_Z0 - 1, PAN_HORN_Z1 + 0.1)
    g = g - rec - cyl_z(0, PAN_SERVO_Y, 1.3, G_Z0 - 1, G_Z1 + 1)
    for sx in (1, -1):
        g = g - cyl_z(sx * 6.5, PAN_SERVO_Y, 0.7, G_Z0, G_Z1 + 1)
    return g


def pan_horn_e23h():
    y = PAN_SERVO_Y
    hub = cyl_z(0, y, 3.5, PAN_HORN_Z0, PAN_HORN_Z1) - cyl_z(0, y, MS_SPL_R, PAN_HORN_Z0 - 0.1, PAN_SPL_TOP)
    L, W = 18.0, 5.6
    arm = bx(-L / 2 + W / 2, L / 2 - W / 2, y - W / 2, y + W / 2, G_Z0, PAN_HORN_Z1) + \
        cyl_z(-L / 2 + W / 2, y, W / 2, G_Z0, PAN_HORN_Z1) + cyl_z(L / 2 - W / 2, y, W / 2, G_Z0, PAN_HORN_Z1)
    return (hub + arm).clean() - cyl_z(0, y, MS_SPL_R, PAN_HORN_Z0 - 0.1, PAN_SPL_TOP)


def yaw_horn_e21h():
    h = cyl_z(0, 0, 10.0, YAW_BRG_Z1, YAW_BRG_Z1 + 2.5) + cyl_z(0, 0, 4.5, YAW_BRG_Z1 + 2.5, YS_Z0 - 1.6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h - cyl_z(7.0 * math.cos(a), 7.0 * math.sin(a), 1.1, YAW_BRG_Z1 - 1, YAW_BRG_Z1 + 3)
    return h - cyl_z(0, 0, 1.6, YAW_BRG_Z1 - 1, YS_Z0)


def controller_e24():
    b = bx(-PCB["x"], PCB["x"], PCB["y0"], PCB["y0"] + PCB["t"], PCB["z0"], PCB["z1"])
    y1 = PCB["y0"] + PCB["t"]
    # ESP32-C3 SuperMini 22.5 x 18 on headers (back side, toward the door), USB-C at its outer end
    sm = bx(-22.5, 0.0, y1 + 2.5, y1 + 3.5, PCB["z0"] + 0.25, PCB["z0"] + 18.25)
    pins = bx(-21.5, -1.0, y1 - 0.01, y1 + 2.5, PCB["z0"] + 1.0, PCB["z0"] + 3.5) + \
        bx(-21.5, -1.0, y1 - 0.01, y1 + 2.5, PCB["z0"] + 15.0, PCB["z0"] + 17.5)
    chip = bx(-15.0, -6.0, y1 + 3.49, y1 + 4.3, PCB["z0"] + 5.0, PCB["z0"] + 13.0)
    usb = bx(-23.4, -16.0, y1 + 3.49, y1 + 6.7, PCB["z0"] + 5.5, PCB["z0"] + 14.5)
    # DRV8833 module 18 x 16
    drv = bx(2.0, 20.0, y1 + 2.5, y1 + 3.5, PCB["z0"] + 1.0, PCB["z0"] + 17.0) + \
        bx(3.0, 19.0, y1 - 0.01, y1 + 2.5, PCB["z0"] + 1.5, PCB["z0"] + 4.0) + \
        bx(7.0, 13.0, y1 + 3.49, y1 + 4.5, PCB["z0"] + 6.0, PCB["z0"] + 12.0)
    # servo bus / motor / battery connectors standing on the top edge (clear of the pan servo case x -5.9..16.9)
    con = bx(-23.0, -8.0, PCB["y0"] - 1.0, PCB["y0"] + PCB["t"] + 4.0, PCB["z1"] - 0.01, PCB["z1"] + 6.0) + \
        bx(19.0, 23.5, PCB["y0"] - 1.0, PCB["y0"] + PCB["t"] + 4.0, PCB["z1"] - 0.01, PCB["z1"] + 6.0)
    return b + sm + pins + chip + usb + drv + con


def front_board_e25():
    y0 = E25["y0"]
    b = bx(-E25["x"], E25["x"], y0, y0 + E25["t"], E25["z0"], E25["z1"])
    for (x, y) in ((E25["boss"][0], E25["boss"][1]), (-E25["boss"][0], E25["boss"][1])):
        b = b - cyl_y(x, y, 1.1, y0 - 1, y0 + 3)
    leds = union(bx(x - 2.5, x + 2.5, y0 - 1.6, y0 + 0.01, LED["z"] - 2.5, LED["z"] + 2.5) for x in (-8, 0, 8))
    tof = bx(-5.0, 5.0, y0 - 1.0, y0 + 0.01, SEN["z"] - 3.0, SEN["z"] + 3.0) + \
        bx(-2.2, 2.2, y0 - 1.6, y0 - 0.99, SEN["z"] - 1.2, SEN["z"] + 1.2)
    return b + leds + tof


# ============================================================================================
# NECK
# ============================================================================================

def collar_n01():
    w0 = superellipse_wire(CO["w"] / 2, CO["d"] / 2, TN, CO["z0"], count=64)
    k = (CO["z1"] - CO["z0"]) * math.tan(math.radians(COLLAR_TAPER))
    w1 = superellipse_wire(CO["w"] / 2 - k, CO["d"] / 2 - k, TN, CO["z1"], count=64)
    from build123d import Solid
    c = Solid.make_loft([w0, w1], ruled=True)
    c = try_fillet(c, c.edges().group_by(Axis.Z)[-1], 1.4, "collar top")
    c = c - cyl_z(0, 0, COLLAR_BORE_R, CO["z0"] - 1, CO["z1"] + 1)
    for (x, y) in COLLAR_PINS:
        c = c + cyl_z(x, y, 1.2, CO["z0"] - 1.4, CO["z0"] + 0.01)
    return c


def cone_n02():
    z0, z1, rb, rt = CN["z0"], CN["z1"], CN["r_bottom"], CN["r_top"]
    pts = []
    n = 16
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        r = rt + (rb - rt) * ((z1 - z) / (z1 - z0)) ** 2
        pts.append(Vector(r, 0, z))
    edges = [Edge.make_line(Vector(0, 0, z0), pts[0]), Edge.make_spline(pts),
             Edge.make_line(pts[-1], Vector(0, 0, z1)), Edge.make_line(Vector(0, 0, z1), Vector(0, 0, z0))]
    trumpet = revolve(Face(Wire(edges)), Axis.Z, 360)
    c = trumpet + cyl_z(0, 0, rb, CO["z0"], z0 + 0.01) + cyl_z(0, 0, SPIGOT_SH_R, PB_Z1, CO["z0"] + 0.01) + \
        cyl_z(0, 0, PB_RI, PB_Z0, PB_Z1 + 0.01)
    # bore, snap ledge at z 112, bottom web with screws + cable hole
    c = c - cyl_z(0, 0, 10.0, PB_Z0 + 1.5, 112.0) - cyl_z(0, 0, 8.0, 111.99, z1 + 2)
    c = c - cyl_z(0, 0, 4.0, PB_Z0 - 1, PB_Z0 + 2)
    for sx in (1, -1):
        c = c - cyl_z(sx * 7.0, 0, 1.2, PB_Z0 - 1, PB_Z0 + 2)
    # saddle trim off the barrel
    c = c - cyl_x(TLY, TLZ, BAR_R + SADDLE_GAP, -BAR_L, BAR_L)
    return c


def barrel_n06():
    hb = BAR_L / 2
    b = cyl_x(TLY, TLZ, BAR_R, -hb, hb)
    b = try_fillet(b, b.edges(), 1.0, "barrel ends")
    # snap stem into N02 (two legs with hooks)
    stem = cyl_z(0, 0, 7.8, 108.5, TLZ - BAR_R + 2.5)
    b = b + stem
    b = b - cyl_x(TLY, TLZ, BAR_R - WALL, -(hb - BAR_END), hb - BAR_END)
    b = b - cyl_z(0, 0, 4.5, 107, TLZ)
    b = b - bx(-1.0, 1.0, -10, 10, 108.0, 112.4)
    for sx in (1, -1):
        hook = (cyl_z(0, 0, 9.1, 108.9, 111.7) - cyl_z(0, 0, 7.7, 108, 113)) & bx(sx * 3.0, sx * 10, -3.0, 3.0, 100,
                                                                                   120)
        b = b + hook
    # both ends: cross-horn recess, pivot hole, 2 screw bosses
    for sx in (1, -1):
        xa, xb = sx * (hb - HORN_RECESS), sx * (hb + 1)
        rec = bx(xa, xb, -9.6, 9.6, TLZ - 2.9, TLZ + 2.9) + bx(xa, xb, -2.9, 2.9, TLZ - 9.6, TLZ + 9.6) + \
            cyl_x(TLY, TLZ, 4.0, xa, xb)
        b = b - rec
        b = b - cyl_x(TLY, TLZ, 1.6, sx * (hb - BAR_END - 1), sx * (hb + 1))
        for sy in (1, -1):
            b = b + cyl_x(sy * 7.5, TLZ, 2.4, sx * (hb - BAR_END - 3.5), sx * (hb - BAR_END + 0.01))
            b = b - cyl_x(sy * 7.5, TLZ, 0.7, sx * (hb - BAR_END - 3.0), sx * (hb + 1))
        # decorative groove
        g0 = sx * (hb - 3.0)
        b = b - (cyl_x(TLY, TLZ, BAR_R + 1, g0 - 0.3, g0 + 0.3) - cyl_x(TLY, TLZ, BAR_R - 0.5, g0 - 1, g0 + 1))
    # cable exit top-back (wires to the head pocket ceiling)
    c45 = math.cos(math.radians(45))
    slot = Pos(0, TLY + 13 * c45, TLZ + 13 * c45) * Rot(45, 0, 0) * Box(9.0, 5.0, 8.0)
    b = b - slot
    return b


# ============================================================================================
# ARMS (left arm built, right mirrored)
# ============================================================================================

def egg_local(d=0.0):
    sph = Sphere(1.0)
    top = scale(sph & Pos(0, 0, 1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_TOP - d))
    bot = scale(sph & Pos(0, 0, -1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_BOT - d))
    return Pos(0, 0, ZC) * top.fuse(bot).clean()


def silhouette_prism(inset, x0, x1, n=120):
    """Prism along local +x of the egg side silhouette (YZ) offset inward by `inset` (concept body.py)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c = C_TOP if math.cos(t) >= 0 else C_BOT
        y, z = HW_ * math.sin(t), c * math.cos(t)
        ny, nz = c * math.sin(t), HW_ * math.cos(t)
        L = math.hypot(ny, nz)
        pts.append(Vector(x0, y - inset * ny / L, ZC + z - inset * nz / L))
    f = Face(Wire([Edge.make_spline(pts, periodic=True)]))
    return extrude(f, x1 - x0, dir=(1, 0, 0))


def panel_groove():
    ring = silhouette_prism(PANEL_INSET, 0.8, 12.0) - silhouette_prism(PANEL_INSET + PANEL_GROOVE, 0.0, 13.0)
    return ring & (egg_local() - egg_local(PANEL_GROOVE_D))


def halfspace(p: Vector, n: Vector, size=300.0):
    pl = Plane(origin=p, z_dir=n)
    return pl.location * Pos(0, 0, size / 2) * Box(size, size, size)


def tip_plane():
    za = TIP_ZTOP - AX_Z
    ya = -HW_ * math.sqrt(max(0.0, 1 - ((za - ZC) / C_BOT) ** 2))
    A = Vector(0, ya, za)
    B = Vector(0, TIP_YB, ZC - C_BOT * math.sqrt(1 - (TIP_YB / HW_) ** 2))
    d = (B - A).normalized()
    m = Vector(0, -d.Z, d.Y)
    mid = (A + B) * 0.5 - Vector(0, 0, ZC)
    if m.dot(mid) < 0:
        m = -m
    t = math.radians(TIP_TILT)
    n = (m * math.cos(t) + Vector(-1, 0, 0) * math.sin(t)).normalized()
    return A, n


def arm_left():
    loc = Pos(MID, AX_Y, AX_Z) * Rot(0, -SPLAY, 0)
    E0, Ei = egg_local(0.0), egg_local(ARM_WALL)
    shell = E0 - Ei
    A, n = tip_plane()
    hs_tip_out = halfspace(A + n * HS, n)               # A03 region
    hs_tip_cut = halfspace(A - n * HS, n)               # removed from the shells
    shell = shell - hs_tip_cut
    pos_x = bx(HS, 50, -50, 50, -80, 50)
    neg_x = bx(-50, -HS, -50, 50, -80, 50)
    a01 = shell & pos_x
    a02 = shell & neg_x
    # A02 snap lip (sits inside A01, 0.05 off its wall)
    lip = ((egg_local(1.0) - egg_local(2.9)) & bx(-1.5, -HS + 0.2, -50, 50, -80, 50)) + \
        ((egg_local(ARM_WALL + 0.05) - egg_local(2.9)) & bx(-HS - 0.2, 2.5, -50, 50, -80, 50))
    lip = lip - halfspace(A - n * 2.8, n)
    a02 = a02 + lip
    # A03 tip + captive plug
    plug = egg_local(ARM_WALL + 0.05) & (halfspace(A - n * 2.5, n) - halfspace(A + n * (HS + 0.4), n))
    tip = (E0 & hs_tip_out) + plug
    try:                                   # outer lens-panel groove (0.45 x 0.4) like the approved concept
        g = panel_groove()
        a01g, tipg = a01 - g, tip - g
        if a01g.is_valid and len(a01g.solids()) == 1 and abs(a01.volume - a01g.volume) < 60:
            a01 = a01g
            if tipg.is_valid and len(tipg.solids()) == 1:
                tip = tipg
        else:
            print("   [panel groove skipped: result check]")
    except Exception as ex:  # noqa: BLE001
        print("   [panel groove skipped]", str(ex)[:80])
    a01w, a02w, tipw = loc * a01, loc * a02, loc * tip
    # hub on the shoulder axis (global X), added to A02 before the socket is cut
    split_x = MID - HS                                  # approx split at the axis
    hub = cyl_x(AX_Y, AX_Z, HUB_R, HUB_X0, MID + 1.0) & (loc * neg_x)
    hub = try_fillet(hub, hub.faces().sort_by(Axis.X)[0].edges(), 0.8, "hub edge")
    a02w = a02w + hub
    a02w = a02w - cyl_x(AX_Y, AX_Z, A04_R + 0.2, HUB_X0 - 5, A04_X1)
    for sy in (1, -1):
        a02w = a02w - cyl_x(sy * 4.5, AX_Z, 1.2, A04_X1 - 0.1, MID + 2)
        a02w = a02w - cyl_x(sy * 4.5, AX_Z, 2.1, A04_X1 + 1.2, MID + 2)
    a01w = a01w - cyl_x(AX_Y, AX_Z, A04_R + 0.2, HUB_X0 - 5, A04_X1)
    tipw = tipw - cyl_x(AX_Y, AX_Z, HUB_R + 0.3, HUB_X0 - 5, MID + 2)
    _ = split_x
    # A04 joint coupler
    c = cyl_x(AX_Y, AX_Z, A04_R, A04_X0, A04_X1)
    c = try_fillet(c, c.faces().sort_by(Axis.X)[0].edges(), 0.5, "A04 edge")
    L, W, T = HORN_ARM
    rec = bx(A04_X0 - 1, A04_X0 + T + 0.1, -W / 2 - 0.15, W / 2 + 0.15, AX_Z - L / 2 + W / 2, AX_Z + L / 2 - W / 2) + \
        cyl_x(0, AX_Z - L / 2 + W / 2, W / 2 + 0.15, A04_X0 - 1, A04_X0 + T + 0.1) + \
        cyl_x(0, AX_Z + L / 2 - W / 2, W / 2 + 0.15, A04_X0 - 1, A04_X0 + T + 0.1) + \
        cyl_x(AX_Y, AX_Z, 3.7, A04_X0 - 1, A04_X0 + T + 0.1)
    c = c - rec - cyl_x(AX_Y, AX_Z, 1.2, A04_X0, A04_X1 + 1) - cyl_x(AX_Y, AX_Z, 2.3, A04_X0 + T + 1.2, A04_X1 + 1)
    for sy in (1, -1):
        c = c - cyl_x(sy * 4.5, AX_Z, 0.75, A04_X1 - 5, A04_X1 + 1)
    # A05 ring
    r = cyl_x(AX_Y, AX_Z, A05_RO, A05_X0, A05_X1) - cyl_x(AX_Y, AX_Z, A05_RI, A05_X0 - 1, A05_X1 + 1)
    r = try_fillet(r, [e for e in r.faces().sort_by(Axis.X)[-1].edges() if e.radius > A05_RO - 0.1], 0.5, "A05")
    return dict(A01=a01w, A02=a02w, A03=tipw, A04=c, A05=r)


# ============================================================================================
# build
# ============================================================================================

def build():
    t0 = time.time()
    P = []

    def add(pid, name, shp, mat, sub, joint, expl, internal=False, note=""):
        n = len(shp.solids())
        if n != 1 and not pid.startswith("E"):
            print(f"   [WARN] {pid}: {n} solids (printed part should be one piece)")
        P.append(PartRec(pid, name, check(pid, shp), mat, sub, joint, expl, internal, note))

    # ---- torso shells ----
    sl = side_shell_left()
    sr = mirror(sl, Plane.YZ)
    bd = band()
    add("T01", "Stredový pás trupu", bd, "white", "torso", "J1", (0, 0, 30),
        note="|x| ≤ 26.7 predok → vrch → chrbát; 3 nálitky pre T07, 2 skrutky M2 zospodu, otvor dvierok")
    add("T02-R", "Bočný kryt trupu pravý", sr, "white", "torso", "J1", (-30, 0, 0),
        note="jazýček pod pás, otvor ramena Ø22.4 + doraz, 2 bloky pre servo ruky, 2× M2 zospodu")
    add("T02-L", "Bočný kryt trupu ľavý", sl, "white", "torso", "J1", (30, 0, 0),
        note="zrkadlovo k T02-R")
    add("T03", "Servisné dvierka (chrbát)", door(), "white", "torso", "J1", (0, 25, 0),
        note="36×24 R6, 2 spodné háčiky + 1 horná západka, bez skrutiek")
    add("T04", "Otočný tanier trupu", plate_t04(), "black", "torso", "J1", (0, 0, -25),
        note="Ø77×2.5 + puzdro vonkajšieho krúžku 6806 (Ø42) dole, 8× M2 zápustné zospodu")
    add("T05", "Svetlovod trupu", light_guide(), "cyan_led", "torso", "J1", (0, -25, 0),
        note="28×3.5 zarovno, z 86, príruba za stenou")
    add("T06", "Okienko senzora", sensor_window(), "frost", "torso", "J1", (0, -25, 0),
        note="18×3.5, z 76, zapustené 0.5 (VL53L0X za ním)")
    print(f"  torso shells {time.time() - t0:.1f}s")

    # ---- neck ----
    add("N01", "Golier krku", collar_n01(), "black", "neck", "J1", (0, 0, 10),
        note="42×34, úkos 22°, 2 kolíky + VHB na pás")
    add("N02", "Kužeľ krku s čapom", cone_n02(), "black", "neck", "J2", (0, 0, 20),
        note="čap Ø25 v 6805, osadenie na vnútornom krúžku, 2× M2 zhora do N03, otvor pre káble Ø8")
    add("N06", "Valec náklonu", barrel_n06(), "black", "neck", "J2", (0, 0, 32),
        note="Ø30×30 na osi y 0 / z 127; na oboch čelách vybranie pre kríž serva + čap Ø3.2; zacvakne do N02")
    print(f"  neck {time.time() - t0:.1f}s")

    # ---- arms ----
    L = arm_left()
    for side, sx, j in (("R", -1, "J4"), ("L", 1, "J5")):
        g = {k: (v if sx > 0 else mirror(v, Plane.YZ)) for k, v in L.items()}
        sub = "arm_" + side
        nm = "pravá" if side == "R" else "ľavá"
        add(f"A01-{side}", f"Vonkajšia škrupina ruky {nm}", g["A01"], "white", sub, j, (sx * 30, 0, 0),
            note="vajce 99/71/48, ½š 13, ½h 7, odklon 8°, stena 1.8")
        add(f"A02-{side}", f"Vnútorná škrupina ruky {nm}", g["A02"], "white", sub, j, (sx * 22, 0, 0),
            note="náboj Ø18 s lôžkom A04, 2× M2 skryté pod A01, zámkový lem")
        add(f"A03-{side}", f"Špička ruky {nm}", g["A03"], "rubber", sub, j, (sx * 30, -8, -15),
            note="TPU, zátka zachytená medzi A01/A02")
        add(f"A04-{side}", f"Spojka kĺbu ramena {nm}", g["A04"], "black", sub, j, (sx * 14, 0, 0),
            note="Ø14.6, skrátené rameno serva v drážke, axiálna skrutka M2")
        add(f"A05-{side}", f"Krúžok ramena {nm}", g["A05"], "black", sub, "J1", (sx * 7, 0, 0),
            note="Ø22/Ø16 (otvor ramena), 0.7 nad povrchom, vlepený")
    print(f"  arms {time.time() - t0:.1f}s")

    # ---- internals ----
    add("T07", "Držiak otáčania hlavy", pan_bracket_t07(), "grey", "torso", "J1", (0, 0, 18), True,
        note="PETG: puzdro 6805, 3× M2 do pásu, koľajnice pre servo + ozubené koleso (zasunie sa zozadu)")
    add("T08", "Kolíska serva trupu", cradle_t08(), "grey", "torso", "J1", (0, 0, -8), True,
        note="PETG na T04: steny proti krútiacemu momentu STS3215, 2 stĺpiky, drážky pre DPS")
    add("T09", "Prítlačná lišta serva", strap_t09(), "grey", "torso", "J1", (0, 0, 14), True,
        note="2× M2 do stĺpikov T08")
    add("N03", "Ozubené koleso krku 20z", hub_gear_n03(), "grey", "neck", "J2", (0, 0, 8), True,
        note="m1, 20 z, príruba Ø30 pod vnútorným krúžkom 6805")
    add("N04", "Ozubené koleso serva 20z", servo_gear_n04(), "grey", "neck", "J1", (0, 8, 8), True,
        note="m1, 20 z, na ramienku pan serva, prevod 1:1 (os 20 mm)")
    add("M21", "Ložisko 6806-2RS", bearing(YAW_BRG[0] / 2, YAW_BRG[1] / 2, YAW_BRG_Z1 - YAW_BRG[2], YAW_BRG_Z1),
        "metal", "torso", "J1", (0, 0, -12), True, note="30×42×7, vonkajší krúžok v T04, vnútorný na náboji základne")
    add("M22", "Ložisko 6805-2RS", bearing(PB_RI, PB_RO, PB_Z0, PB_Z1), "metal", "torso", "J1", (0, 0, 14), True,
        note="25×37×7 v T07, nesie hlavu")
    yaw = place(sts3215_local(), (0, 0, YS_Z0), (0, 0, -1), (1, 0, 0))
    add("E21", "Servo trupu Feetech STS3215", yaw, "servo", "torso", "J1", (0, 0, -4), True,
        note="45.2×24.7×35, drážkovanie dole na osi J1, telo z 45–80")
    add("E21H", "Ramienko STS3215 (na náboji základne)", yaw_horn_e21h(), "metal", "torso", "", (0, 0, -16), True,
        note="disk Ø20, priskrutkovaný k nábojom základne")
    for side, sx, j in (("R", -1, "J4"), ("L", 1, "J5")):
        sv = place(micro_servo_local(), (sx * ARM_TOP_X, AX_Y, AX_Z), (sx, 0, 0), (0, -1, 0))
        add(f"E22-{side}", f"Servo ruky MG90S {'pravé' if side == 'R' else 'ľavé'}", sv, "servo", "torso", "J1",
            (sx * 12, 0, 0), True, note="MG90S / SCS0009, uši na blokoch T02, 2× M2")
        add(f"E22H-{side}", "Ramienko serva ruky (skrátené)", horn_micro_x(sx), "white", "arm_" + side, j,
            (sx * 14, 0, 0), True)
    pan = place(micro_servo_local(), (0, PAN_SERVO_Y, PAN_TOP_Z), (0, 0, 1), (1, 0, 0))
    add("E23", "Servo otáčania hlavy MG90S", pan, "servo", "torso", "J1", (0, 14, 0), True,
        note="v koľajniciach T07, ozubený prevod 1:1 na krk")
    add("E23H", "Ramienko pan serva", pan_horn_e23h(), "white", "torso", "J1", (0, 14, 6), True)
    add("E24", "Riadiaca DPS (ESP32-C3 SuperMini + DRV8833)", controller_e24(), "pcb", "torso", "J1", (0, 18, 0),
        True, note="48×18.5 v drážkach T08, prístup cez dvierka T03")
    add("E25", "Predná DPS (3× WS2812B + VL53L0X)", front_board_e25(), "pcb", "torso", "J1", (0, -14, 0), True,
        note="na 2 nálitkoch pásu, LED za T05, ToF za T06")
    print(f"  internals {time.time() - t0:.1f}s")
    return P


# ============================================================================================
# checks
# ============================================================================================

def interference(parts, others=(), tol=0.5):
    allp = list(parts) + list(others)
    own = {p.id for p in parts}
    bad = []
    for i in range(len(allp)):
        for j in range(i + 1, len(allp)):
            a, b = allp[i], allp[j]
            if a.id not in own and b.id not in own:
                continue
            ba, bb = a.shape.bounding_box(), b.shape.bounding_box()
            if ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y or \
                    ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z:
                continue
            try:
                ab = a.shape & b.shape
                v = 0.0 if ab is None else ab.volume
            except Exception:  # noqa: BLE001
                v = -1
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


def motion_check(parts, others=(), tol=0.5):
    """Sweep the joints in CAD (the renderer's pose pivots use the v7.3 axes) and report collisions."""
    from build123d import Axis as _Ax
    byid = {p.id: p for p in list(parts) + list(others)}
    out = []

    def hit(a, b):
        ba, bb = a.bounding_box(), b.bounding_box()
        if ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y or \
                ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z:
            return 0.0
        i = a & b
        return 0.0 if i is None else i.volume

    fixed_t = [p for p in byid.values() if p.joint == "J1"]
    upper = [p for p in byid.values() if p.joint in ("J2", "J3")]      # pan stage + head in the default pose
    base = [p for p in byid.values() if p.joint == "" and p.id != "E21H"]
    # arms (positive = forward / up, i.e. -rot about X like the renderer convention)
    for side, j in (("L", "J5"), ("R", "J4")):
        mov = [p for p in parts if p.joint == j]
        ax = _Ax((0, AX_Y, AX_Z), (1, 0, 0))
        for ang in (-30, 45, 90, 135, 180):
            for m in mov:
                sh = m.shape.rotate(ax, -ang)
                for f in fixed_t + base + upper:
                    v = hit(sh, f.shape)
                    if v > tol:
                        out.append((f"{j}={ang}", m.id, f.id, round(v, 1)))
    # pan stage about Z (N03/N04 gear mesh excluded)
    mov = [p for p in parts if p.joint == "J2" and p.id != "N03"]
    for ang in (-90, -45, 45, 90):
        for m in mov:
            sh = m.shape.rotate(_Ax.Z, ang)
            for f in fixed_t:
                v = hit(sh, f.shape)
                if v > tol:
                    out.append((f"J2={ang}", m.id, f.id, round(v, 1)))
    # torso yaw vs the base
    for ang in (-150, -90, 90, 150):
        for m in [p for p in parts if p.joint in ("J1", "J2", "J4", "J5")]:
            sh = m.shape.rotate(_Ax.Z, ang)
            for f in base:
                v = hit(sh, f.shape)
                if v > tol:
                    out.append((f"J1={ang}", m.id, f.id, round(v, 1)))
    return out


def other_modules():
    """build() of the other v8 modules whose manifests are present in build_v8/manifest."""
    import importlib
    import json
    out = []
    mdir = os.path.join(OUT_DIR, "manifest")
    for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        name = fn[:-5]
        if not fn.endswith(".json") or name == MANIFEST:
            continue
        for mod in (f"nova_v8.cad_{name}", f"nova_v8.{name}"):
            try:
                m = importlib.import_module(mod)
                out += m.build()
                print(f"  loaded {mod} ({len(json.load(open(os.path.join(mdir, fn))))} parts in manifest)")
                break
            except ModuleNotFoundError:
                continue
            except Exception as ex:  # noqa: BLE001
                print(f"  [could not build {mod}] {ex}")
                break
    return out


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
    for r in recs:
        print(f"  {r['id']:7s} {r['mat']:9s} {r['sub']:6s} {r['joint']:3s} {'int' if r['internal'] else '   '} "
              f"size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
    if "--check" in sys.argv:
        oth = other_modules() if "--others" in sys.argv else []
        print("interference:", interference(ps, oth))
        if "--motion" in sys.argv:
            print("motion:", motion_check(ps, oth))
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
