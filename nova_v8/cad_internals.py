"""
NOVA mini v8.1 - INTERNAL COMPONENTS (manifest "internals").  Run from the repo root:

    /opt/venv/cad/bin/python -m nova_v8.cad_internals              # build + export (build_v8/, manifest "internals")
    /opt/venv/cad/bin/python -m nova_v8.cad_internals --check      # + STEP round trip + clearance vs base/torso/head
    ... --camera                                                   # + the optional camera IH06 (needs an H03 change)
    ... --out <dir>                                                # export somewhere else (previews)

Simplified but recognisable bought components (+ the few small parts that tie them to the shells) at their
functional positions.  Every part is internal=True, in FINAL ASSEMBLY coordinates (nova_v8/spec.py: mm, Z up,
FRONT = -Y, robot RIGHT = -X).  sub = subassembly, joint = the group it moves with: base "" | torso J1 (yaw servo,
arm servos, pan servo, 6805/6806, controller, chest board) | pan stage J2 | head J3 | right arm J4 | left arm J5.
Ids use their own "I" namespace (IB base, IT torso, IN neck, IH head, IW cables) so stl/<ID>.stl in build_v8/ never
collides with the shell modules.

Interfaces (servo seats, bearing housings, board slots, cable holes) are READ from the current shell modules
nova_v8/cad_base.py, cad_torso.py, cad_head.py (getattr with fallbacks, see INTERFACE) -> the components follow the
shells when those change.  spec.py is not edited (DEVIATIONS are printed on every run).

The shell modules keep simple envelopes of the same bought components (BM2, BE1.., E21.., E31..).  SUPERSEDES maps
each detailed part here to the envelope it replaces; render with "exclude": SUPERSEDED (or exclude "I*").

HEAD (J3)    IH01 LCD 3.5" · IH02 ESP32-S3 board (JC3248W535 / Waveshare, parts inside the H07 window) · IH03 S3
             module · IH04 tilt micro servo (beside the barrel pocket, shaft z 147, 1:1 gears H11/H09 of the head
             module) · IH07-R/L ear PCBs Ø23 (6x WS2812B-2020) · IH08 INMP441 mic (flat on the barrel-pocket
             ceiling, bottom port sealed onto a hidden vent slot -> hears through the open pocket mouth)
             · [IH06 optional OV2640 camera, --camera]
NECK         IN01 pan micro servo (J1, shaft (0, 20), gears N04 -> N03) · IN02 its 18 mm horn in N04 · IN03 6805
TORSO (J1)   IT01 STS3215 (spline DOWN) · IT02 Ø20 horn on the base hub ("") · IT03 M3x20 + washer from below into
             the spline = axial coupling ("") · IT04 6806 · IT05-R/L arm micro servos · IT06-R/L 13 mm horns =
             A04 keys (J4/J5) · IT07 carrier PCB (MP1584 5 V, 74LVC1G126 servo-bus driver, connectors) · IT08
             ESP32-C3 SuperMini · IT09 chest board (5x WS2812B-2020 + VL53L0X + LTR-303) · IT10 black chest frame
             with light baffle (3 windows: LED bar / ToF / ALS behind the one smoked strip)
BASE ("")    IB01/02/03-R/L N20 + encoder + D-shaft · IB04-kP/kM bay contacts (+ plate, - conical spring) · IB05-1/2
             18650 · IB06 Ø28 speaker (vertical, fires into the sealed front chamber) · IB07-1..4 TCRT5000 cliff
             boards · IB08 underglow flex ring (24x WS2812B-2020 into the opal guide) · IB09-1 charger board
             (IP2326 + 2S protection + AO4407A main P-MOSFET, carries USB-C B10) · IB09-2 BASE NODE + power button
             (STM32G030 servo-bus slave, DRV8833, 5 V buck, 3.3 V LDO; 6x6 self-locking switch -> MOSFET gate)
             · IB10-1/2 dock pogo pins.  Both base boards black solder mask (they lie under the rear B01/B09 seam).
CABLES       IW1-1/2/3 neck bundle Ø3, 6 wires, split at J1/J2/J3 · IW2 J1 ROLLING LOOP: flat 6-wire band on edge in
             the B15 trough (outer run on the fixed rim, U-turn R6, inner run on the rotating T04 housing), constant
             length 209 mm for J1 ±150 deg · IW3 band end -> Ø4.2 riser through the T04 slot -> JST-GH on IT07

ELECTRICAL ARCHITECTURE (review 2)
  head ESP32-S3 --UART 1 Mbit (neck: 5 V, GND 26 AWG + TX, RX, SPK+-)--> torso ESP32-C3 --1-wire servo bus-->
  STS3215 (J1) + [SCS0009 option] + BASE NODE STM32G030 (motors, encoders A/B, 4 cliff sensors, underglow, local
  cliff stop).  Only VBAT, GND, BUS, SPK+, SPK-, GND cross J1 -> the J1 cable can be a real rolling loop.
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Compound, Cylinder, Edge, Face, Location, Plane, Pos, Rot, Solid, Sphere,
                       Vector, Wire, extrude, fillet, revolve)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "internals"


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


def ring_z(x, y, ri, ro, z0, z1):
    return cyl_z(x, y, ro, z0, z1) - cyl_z(x, y, ri, z0 - 1, z1 + 1)


def union(shapes):
    out = None
    for s in shapes:
        if s is None:
            continue
        out = s if out is None else out + s
    return out


def try_fillet(shape, edges, r):
    try:
        out = fillet(edges, r) if not hasattr(shape, "fillet") else shape.fillet(r, edges)
        if out.is_valid and abs(out.volume) > 0:
            return out
    except Exception:  # noqa: BLE001
        pass
    return shape


def rr_face_xy(w, d, r):
    """Rounded rectangle face centred at the origin of the XY plane."""
    hw, hd = w / 2, d / 2
    r = min(r, hw - 1e-3, hd - 1e-3)
    corners = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        cx, cy = sx * (hw - r), sy * (hd - r)
        corners.append([Vector(cx + r * math.cos(math.radians(a0 + t)), cy + r * math.sin(math.radians(a0 + t)), 0)
                        for t in (0, 45, 90)])
    edges = []
    for i, (p0, pm, p1) in enumerate(corners):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        edges.append(Edge.make_line(p1, corners[(i + 1) % 4][0]))
    return Face(Wire(edges))


def rr_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    """Rounded rectangle (w along X, d along Y) extruded z0 -> z1."""
    return Pos(cx, cy, z0) * extrude(rr_face_xy(w, d, r), z1 - z0)


def rr_y(w, h, r, y0, y1, cx=0.0, cz=0.0):
    """Rounded rectangle (w along X, h along Z) extruded y0 -> y1."""
    pl = Plane(origin=(cx, min(y0, y1), cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    return extrude(pl.location * rr_face_xy(w, h, r), abs(y1 - y0), dir=(0, 1, 0))


def rr_x(d, h, r, x0, x1, cy=0.0, cz=0.0):
    """Rounded rectangle (d along Y, h along Z) extruded x0 -> x1."""
    pl = Plane(origin=(min(x0, x1), cy, cz), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    return extrude(pl.location * rr_face_xy(d, h, r), abs(x1 - x0), dir=(1, 0, 0))


def frame(origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location


def tube(points, r, closed=False, t0=None, t1=None):
    """Swept round tube (cable bundle) through the points (smooth B-spline path); optional end tangents so
    consecutive segments meet with coincident end faces."""
    pts = [Vector(*p) for p in points]
    if t0 is not None and t1 is not None:
        path = Wire([Edge.make_spline(pts, tangents=[Vector(*t0).normalized(), Vector(*t1).normalized()])])
    else:
        path = Wire([Edge.make_spline(pts, periodic=closed)])
    t0 = path.tangent_at(0)
    sec = Wire([Edge.make_circle(r, Plane(origin=pts[0], z_dir=t0))])
    s = Solid.sweep(sec, path)
    if not s.is_valid or s.volume <= 0:
        raise RuntimeError("tube sweep failed")
    return s


def solid1(s):
    """Fuse to one clean solid when the pieces touch; keep a compound of solids otherwise."""
    try:
        s = s.clean()
    except Exception:  # noqa: BLE001
        pass
    return s


# ============================================================================================
# purchased components - catalogue envelopes with the recognisable features
# ============================================================================================
MS = S.MICRO_SERVO
MS_L, MS_W, MS_H = 22.8, MS["body"][1], MS["body"][2]       # 22.8 x 12.2 x 22.7 (case)
MS_SHAFT_END = 5.9          # spline axis from the near end of the case
MS_TABS = MS["tabs_len"]    # 32.5
MS_TAB_Z = (15.9, 18.4)     # tab underside / top above the case bottom
MS_TAB_HOLE = 2.45
MS_DOME_R, MS_DOME_H = 5.9, 3.0
MS_SPL_R = 2.4
MS_SPL_H = MS["height_with_spline"] - MS_H - MS_DOME_H      # 2.8
MS_SPL_TOP = MS_DOME_H + MS_SPL_H                           # 5.8 above the case top


def micro_servo_local():
    """MG90S / SCS0009 envelope.  Local frame (same convention as cad_torso / cad_head): origin = spline axis on the
    case top plane, +Z = output, +X = toward the far end of the case."""
    x0, x1 = -MS_SHAFT_END, MS_L - MS_SHAFT_END
    hw = MS_W / 2
    c = bx(x0, x1, -hw, hw, -MS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 0.6)
    # case split lines (top cover / middle / bottom cover) - the MG90S look
    for zg in (-3.6, -MS_H + 3.2):
        band = bx(x0 - 1, x1 + 1, -hw - 1, hw + 1, zg - 0.2, zg + 0.2) - bx(x0 + 0.25, x1 - 0.25, -hw + 0.25,
                                                                              hw - 0.25, zg - 1, zg + 1)
        c = c - band
    t0, t1 = MS_TAB_Z[0] - MS_H, MS_TAB_Z[1] - MS_H
    xc = (x0 + x1) / 2
    tab = bx(xc - MS_TABS / 2, xc + MS_TABS / 2, -hw, hw, t0, t1)
    hole_far = MS_L - MS_SHAFT_END + MS_TAB_HOLE
    hole_near = MS_SHAFT_END + MS_TAB_HOLE
    for hx in (-hole_near, hole_far):
        tab = tab - cyl_z(hx, 0, 1.0, t0 - 1, t1 + 1) - bx(hx, hx + math.copysign(5, hx), -0.5, 0.5, t0 - 1, t1 + 1)
    c = c + tab
    # gear dome, second boss, spline
    c = c + cyl_z(0, 0, MS_DOME_R, -0.01, MS_DOME_H) + cyl_z(7.2, 0, 2.8, -0.01, 1.2)
    c = c + cyl_z(0, 0, MS_SPL_R, MS_DOME_H - 0.01, MS_SPL_TOP) - cyl_z(0, 0, 0.8, MS_SPL_TOP - 2.0, MS_SPL_TOP + 1)
    c = c + bx(x1 - 0.01, x1 + 1.6, -1.6, 1.6, -MS_H + 0.8, -MS_H + 4.0)       # cable strain relief
    return c


def servo_horn_local(arm=15.0, trimmed=None, double=False):
    """Single (or double) arm horn on the micro-servo spline (local frame of micro_servo_local).
    trimmed = arm length kept (mm from the axis) when the horn is cut to fit a coupler."""
    z0, z1 = MS_DOME_H + 0.3, MS_SPL_TOP + 1.4                 # 3.3 .. 7.2
    zt = z1 - 1.6
    L = trimmed if trimmed else arm
    hub = cyl_z(0, 0, 3.5, z0, z1)
    pts = [Vector(0, 3.0, 0), Vector(L, 2.0, 0), Vector(L, -2.0, 0), Vector(0, -3.0, 0)]
    blade = Pos(0, 0, zt) * extrude(Face(Wire.make_polygon(pts, close=True)), z1 - zt)
    blade = blade + cyl_z(L, 0, 2.0, zt, z1)
    h = hub + blade
    if double:
        h = h + Rot(0, 0, 180) * blade
    for k in range(3):
        xh = L - 1.0 - 3.0 * k
        if xh > 4.5:
            h = h - cyl_z(xh, 0, 0.55, zt - 1, z1 + 1)
            if double:
                h = h - cyl_z(-xh, 0, 0.55, zt - 1, z1 + 1)
    h = h - cyl_z(0, 0, MS_SPL_R + 0.05, z0 - 1, MS_SPL_TOP) - cyl_z(0, 0, 1.1, z0 - 1, z1 + 1)
    return h


def horn_stadium_local(L, W, z_hub0, z_bl0, z_top, holes=True):
    """Double servo horn as bought (or trimmed): stadium blade L x W from z_bl0 to z_top, hub Ø7 from z_hub0,
    spline bore + horn-screw hole (local frame of micro_servo_local, blade along local X)."""
    r = W / 2
    blade = bx(-L / 2 + r, L / 2 - r, -r, r, z_bl0, z_top) + cyl_z(-L / 2 + r, 0, r, z_bl0, z_top) + \
        cyl_z(L / 2 - r, 0, r, z_bl0, z_top)
    h = blade + cyl_z(0, 0, 3.5, z_hub0, z_top)
    if holes:
        for xh in (L / 2 - r, L / 2 - r - 2.6):
            if xh > 4.6:
                h = h - cyl_z(xh, 0, 0.55, z_bl0 - 1, z_top + 1) - cyl_z(-xh, 0, 0.55, z_bl0 - 1, z_top + 1)
    h = h - cyl_z(0, 0, MS_SPL_R + 0.05, z_hub0 - 1, MS_SPL_TOP) - cyl_z(0, 0, 1.1, z_hub0 - 1, z_top + 1)
    return h


STS_L, STS_W, STS_H = S.TORSO["yaw_servo"]["body"]           # 45.2 x 24.7 x 35
STS_SHAFT_END = STS_W / 2                                   # output axis centred in the square end
STS_X0, STS_X1 = -STS_SHAFT_END, STS_L - STS_SHAFT_END      # -12.35 .. 32.85
STS_BOSS = (5.0, 1.5)                                       # output boss r / h
STS_SPL = (2.95, 3.0)                                       # 25T spline r / length


def sts3215_local():
    """Feetech STS3215 (12 V/7.4 V serial bus servo).  Local frame as cad_torso: origin = output axis on the output
    face, +Z = output (case at z < 0), +X = toward the far end (bus connectors)."""
    hw = STS_W / 2
    c = bx(STS_X0, STS_X1, -hw, hw, -STS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 1.8)
    for zg in (-5.5, -STS_H + 6.0):          # top cover / middle / bottom cover
        band = bx(STS_X0 - 1, STS_X1 + 1, -hw - 1, hw + 1, zg - 0.25, zg + 0.25) - \
            bx(STS_X0 + 0.35, STS_X1 - 0.35, -hw + 0.35, hw - 0.35, zg - 1, zg + 1)
        c = c - band
    # mounting holes M2: 4 on the output face, 4 on the rear face, 2 per side wall
    for (x, y) in ((-7.5, -8.5), (-7.5, 8.5), (27.5, -8.5), (27.5, 8.5)):
        c = c - cyl_z(x, y, 1.0, -3.0, 0.1) - cyl_z(x, y, 1.0, -STS_H - 0.1, -STS_H + 3.0)
    for x in (2.0, 22.0):
        for sy in (1, -1):
            c = c - cyl_y(x, -STS_H / 2, 1.0, sy * hw - 3.0 * sy, sy * (hw + 0.1))
    # two bus connectors (3-pin) in the far end face
    for yc in (-5.5, 5.5):
        c = c - bx(STS_X1 - 3.0, STS_X1 + 0.1, yc - 3.6, yc + 3.6, -STS_H + 8.0, -STS_H + 12.5)
    # label recess on the rear face, passive rear boss on the axis (for a dual-support bracket)
    c = c - bx(STS_X0 + 14.0, STS_X1 - 4.0, -8.0, 8.0, -STS_H - 0.1, -STS_H + 0.3)
    c = c - ring_z(0, 0, 3.6, 4.0, -STS_H - 0.1, -STS_H + 0.3)      # passive rear bearing ring (flush)
    # output boss + spline (the spline sits inside the horn hub bore)
    c = c + cyl_z(0, 0, STS_BOSS[0], -0.01, STS_BOSS[1])
    c = c + cyl_z(0, 0, STS_SPL[0], STS_BOSS[1] - 0.01, STS_BOSS[1] + STS_SPL[1])
    c = c - cyl_z(0, 0, 1.25, STS_BOSS[1] + STS_SPL[1] - 4.0, STS_BOSS[1] + STS_SPL[1] + 0.1)   # M3 thread
    return c


def bearing_z(x, y, ri, ro, z0, z1):
    """Deep-groove ball bearing with 2RS seals: inner / outer race rings, seal discs recessed 0.3."""
    t = (ro - ri) * 0.22
    b = ring_z(x, y, ri, ro, z0, z1)
    for zz in ((z0 - 0.1, z0 + 0.3), (z1 - 0.3, z1 + 0.1)):
        b = b - ring_z(x, y, ri + t, ro - t, *zz)
    # 0.3 chamfers on the race edges (looks like a bearing, not a washer)
    return b


def n20_local(enc=True):
    """N20 gear motor with magnetic encoder.  Local frame: output axis = +X, origin = gearbox front face centre.
    Section 12 (Y) x 10 (Z).  Returns (motor, encoder, shaft) solids."""
    g0, g1 = -S.BASE["motor"]["gearbox_len"], 0.0               # gearbox x -9 .. 0
    m0 = g0 - 15.0                                              # motor can -24 .. -9
    gb = bx(g0 + 0.8, g1 - 0.8, -5.7, 5.7, -4.7, 4.7) + bx(g1 - 0.8, g1, -6, 6, -5, 5) + bx(g0, g0 + 0.8, -6, 6,
                                                                                               -5, 5)
    for (yy, zz) in ((-4.6, 0), (4.6, 0)):                      # 2x M1.6 tapped holes in the front plate
        gb = gb - cyl_x(yy, zz, 0.8, g1 - 1.5, g1 + 0.1)
    gb = gb + cyl_x(0, 0, 2.0, g1 - 0.01, g1 + 0.8)             # shaft bushing
    can = cyl_x(0, 0, 6.0, m0, g0 + 0.01) & bx(m0 - 1, g0 + 1, -6.5, 6.5, -5.0, 5.0)
    cap = cyl_x(0, 0, 5.4, m0 - 1.8, m0 + 0.01) & bx(m0 - 3, m0 + 1, -6, 6, -4.4, 4.4)
    term = bx(m0 - 2.6, m0 - 1.79, -1.0, 1.0, 3.0, 4.2) + bx(m0 - 2.6, m0 - 1.79, -1.0, 1.0, -4.2, -3.0)
    mag = cyl_x(0, 0, 3.0, m0 - 1.8 - 1.1, m0 - 1.79)          # encoder magnet disc on the rear shaft
    motor = gb + can + cap + term + mag
    shaft = cyl_x(0, 0, 1.48, g1 + 0.8, g1 + 10.0) - bx(g1 + 2.0, g1 + 10.1, 1.0, 2.0, -2, 2)   # D-shaft 3 / 2.5
    encoder = None
    if enc:
        e0 = m0 - 1.8 - 1.1 - 0.4                               # 0.4 air gap behind the magnet (-27.3)
        pcb = rr_x(12.0, 11.0, 1.5, e0 - 1.0, e0)
        con = bx(e0 - 3.8, e0 - 0.99, -4.0, 4.0, -1.6, 1.6) + bx(e0 - 1.8, e0 - 0.99, -2.5, 2.5, 2.2, 3.6)   # JST + hall
        encoder = pcb + con
    return motor, encoder, shaft


def cell_18650_x(xc, y, z_bottom):
    """18650 Li-ion cell lying along X (positive button toward +X)."""
    r = S.BASE["batteries"]["d"] / 2
    L = S.BASE["batteries"]["len"]
    zc = z_bottom + r
    body = cyl_x(y, zc, r, xc - L / 2, xc + L / 2 - 0.8)
    body = try_fillet(body, body.edges(), 0.8)
    body = body - (cyl_x(y, zc, r + 1, xc - L / 2 + 2.0, xc - L / 2 + 2.6) - cyl_x(y, zc, r - 0.35, xc - L / 2 + 1.9,
                                                                                         xc - L / 2 + 2.7))
    btn = cyl_x(y, zc, 3.4, xc + L / 2 - 0.81, xc + L / 2)
    return body + btn


def speaker_z(x, y, d, h, z_face, down=True):
    """Small round speaker (frame rim + cone + dust cap + magnet pot).  z_face = rim (front) face.
    down=True: the front faces -Z (rim at the bottom, magnet on top)."""
    r = d / 2
    pts = [Vector(r, 0, 0), Vector(r, 0, 0.8), Vector(r - 1.4, 0, 0.8), Vector(7.5, 0, h - 2.2),
           Vector(7.5, 0, h), Vector(0, 0, h), Vector(0, 0, h - 2.6), Vector(r - 2.6, 0, 0.6), Vector(r - 1.4, 0, 0)]
    sp = revolve(Face(Wire.make_polygon(pts, close=True)), Axis.Z, 360)
    sp = sp + cyl_z(0, 0, 3.2, h - 2.7, h - 1.6)               # dust cap
    sp = sp + bx(r - 3.0, r + 0.01, -1.5, 1.5, 0.79, 1.6)       # solder tabs
    if not down:
        sp = Pos(0, 0, 0) * Rot(180, 0, 0) * sp
    return Pos(x, y, z_face) * sp


def ws2812_2020(x, y, z, face="-Z"):
    """WS2812B-2020 LED (2.2 x 2.0 x 0.84) sitting on a board surface at (x, y, z), emitting toward `face`."""
    if face == "-Z":
        return bx(x - 1.1, x + 1.1, y - 1.0, y + 1.0, z - 0.84, z + 0.01)
    if face == "+Z":
        return bx(x - 1.1, x + 1.1, y - 1.0, y + 1.0, z - 0.01, z + 0.84)
    if face == "-Y":
        return bx(x - 1.1, x + 1.1, y - 0.84, y + 0.01, z - 1.0, z + 1.0)
    raise ValueError(face)


# ============================================================================================
# INTERFACE - read from the CURRENT shell modules (local construction values there, not in spec.py), with the
# values of 2026-11-01 18:00 as fallbacks.  Importing a shell module only defines its constants / functions.
# ============================================================================================
BS, TS, NK, HD, DSP = S.BASE, S.TORSO, S.NECK, S.HEAD, S.DISPLAY


def _shell(name):
    import importlib
    try:
        return importlib.import_module(f"nova_v8.{name}")
    except Exception as ex:  # noqa: BLE001
        print(f"  [internals] nova_v8.{name} not importable ({ex!r}) - using fallback interface values")
        return None


_B, _T, _H = _shell("cad_base"), _shell("cad_torso"), _shell("cad_head")
IFACE_SRC = {}


def _g(m, name, default):
    v = getattr(m, name, None) if m is not None else None
    IFACE_SRC[name] = "shell" if v is not None else "fallback"
    return default if v is None else v


# ---- base (nova_v8/cad_base.py) -----------------------------------------------------------
WH = BS["wheel"]
WX, WY, WZ, W_R, W_W = WH["x"], WH["y"], WH["axle_z"], WH["d"] / 2, WH["w"]   # 52, 4, 17, 17, 10
B_TOP = BS["z1"]                                    # 39
GB_FACE = _g(_B, "GB_FACE", 43.5)                   # N20 gearbox front face |x| (wheel inner face |x| 47)
CELL_Y = _g(_B, "CELL_Y", 21.0)                     # cell axes y = +-21 (base deviation from spec +-28)
CELL_Z0 = _g(_B, "CELL_Z0", 4.6)                    # cell bottom (on the hatch)
BAY_X = _g(_B, "BAY_X", 35.5)                       # bay inner end faces |x| (contacts)
CELL_L, CELL_D = BS["batteries"]["len"], BS["batteries"]["d"]
FLOOR_TOP = _g(_B, "FLOOR_TOP", 4.5)                # tray floor top face
TRAY_Z0 = _g(_B, "TRAY_Z0", 2.5)                    # tray floor underside
CLIFF = [tuple(map(float, p)) for p in _g(_B, "CLIFF", [(49.1, -40.4), (-49.1, -40.4), (49.1, 40.4),
                                                        (-49.1, 40.4)])]
UG_T0, UG_T1 = _g(_B, "UG_T0", 3.0), _g(_B, "UG_T1", 5.0)          # light-guide ring inset (outer / inner)
UG_Z1, LED_Z1 = _g(_B, "UG_Z1", 6.6), _g(_B, "LED_Z1", 7.6)        # guide top / LED flex top
BOARD_Z0, BOARD_T = _g(_B, "BOARD_Z0", 10.25), _g(_B, "BOARD_T", 1.6)
BOARD_STANDOFFS = _g(_B, "BOARD_STANDOFFS", [(-31.0, 45.0), (-14.0, 44.5), (31.0, 45.0), (14.0, 44.5)])
USB_XY = _g(_B, "USB_XY", (-24.0, 40.0))
BTN_XY = _g(_B, "BTN_XY", (24.0, 40.0))
DOCK_XY = _g(_B, "DOCK_XY", [(-36.0, 41.0), (36.0, 41.0)])
SPK = _g(_B, "SPK", dict(x=28.0, z=19.0, y_face=-41.2, d=28.0, h=5.0))   # vertical, fires -Y
YAW_BRG = BS["yaw_hub"]["bearing"]                  # 6806 30 / 42 x 7
YAW_Z1 = BS["yaw_hub"]["z_top"]                     # 39 bearing top = hub top = horn bottom
LOOP_R, LOOP_Z = _g(_B, "LOOP_R", 26.5), _g(_B, "LOOP_Z", 31.6)       # base's own (single-arc) loop envelope BW1
FIX_EXIT = _g(_B, "FIX_EXIT", (24.9, -9.06, 4.0))
RISER_XY = _g(_B, "RISER_XY", (-26.0, 0.0))
TROUGH_Z0 = _g(_B, "TROUGH_Z0", 26.5)
TOWER_ROOF_Z = TROUGH_Z0 - 2.0                      # underside of the bridge-tower roof (M3 head seat)
TROUGH_FLOOR = TROUGH_Z0 + _g(_B, "TROUGH_T", 2.0)  # 28.5 trough floor top
TROUGH_RIM_IN = _g(_B, "TROUGH_R", 38.0) - _g(_B, "RIM_T", 1.5)    # 36.5 inner face of the fixed trough rim
B09_Z0 = _g(_B, "B09_Z0", 35.6)                     # underside of the B09 seat ring (ceiling of the trough, r > 31)

# ---- torso (nova_v8/cad_torso.py) ---------------------------------------------------------
YS_Z0 = _g(_T, "YS_Z0", TS["yaw_servo"]["z_body"][0])     # 45 output face of the STS3215
ARM_Z, ARM_Y = S.ARM["axis"]["z"], S.ARM["axis"]["y"]     # 89, 0
ARM_TOP_X = _g(_T, "ARM_TOP_X", 37.2)                     # arm-servo case top |x| (spline tip 43)
PAN_Y = _g(_T, "PAN_SERVO_Y", 20.0)                       # pan servo shaft (0, 20) - 1:1 gears
PAN_TOP_Z = _g(_T, "PAN_TOP_Z", 85.8)                     # pan servo case top
PB_Z0, PB_Z1 = _g(_T, "PB_Z0", 96.0), _g(_T, "PB_Z1", 103.0)   # 6805
PB_RI, PB_RO = NK["pan_bearing"][0] / 2, NK["pan_bearing"][1] / 2
PAN_HORN_Z0, PAN_HORN_Z1 = _g(_T, "PAN_HORN_Z0", 89.0), _g(_T, "PAN_HORN_Z1", 92.1)
PAN_G_Z0 = _g(_T, "G_Z0", 90.5)                           # N04 gear face (horn blade bottom)
CTRL = dict(_g(_T, "PCB", dict(x=24.0, y0=18.0, t=1.6, z0=44.2, z1=62.7)))   # controller slot in T08 (XZ)
E25 = dict(_g(_T, "E25", dict(x=23.0, z0=77.0, z1=91.0, y0=-30.8, t=1.6, boss=(21.0, 84.0))))
CHS = TS["chest_strip"]                                   # 34 x 5 at z 84
T_WALL = TS["wall"]
YH_RO = _g(_T, "YH_RO", 22.5)                             # rotating 6806 housing of T04 (OD 45) = inner drum of the loop
T05_FLANGE = 0.8                                          # T05 flange behind the wall (skin 2.0 .. 2.8)
TILT_Y, TILT_Z = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]            # 0, 127

# ---- head (nova_v8/cad_head.py, variant A) ------------------------------------------------
DSP_W, DSP_H, DSP_T = DSP["outline"]                      # 86 x 56 x 6
Y_DSP0, Y_DSP1 = _g(_H, "Y_DSP0", -33.8), _g(_H, "Y_DSP1", -27.8)       # LCD front / board back
DSP_ZC = _g(_H, "DSP_ZC", HD["glass"]["zc"])              # 154
TILT_SERVO_TOP_X = _g(_H, "SV_TOP_X", 22.3)               # tilt servo case top |x| (shaft toward -X)
TILT_SERVO_Z = _g(_H, "SERVO_Z", TILT_Z + 20.0)           # 147
EAR = HD["ear"]
X_EAR_IN = _g(_H, "X_EAR_IN", 48.8)                       # ear rear face / stop ring (PCB seat)
CAM = HD["camera"]
PK_CEIL_TOP = _g(_H, "PK_TOP", HD["barrel_pocket"]["ceiling_z"]) + _g(_H, "PK_WALL", 2.0)   # 146.5 pocket ceiling top
VENT_X = _g(_H, "VENT_X", (-14.0, -10.5, -7.0, 7.0, 10.5))     # hidden vent slots in the pocket ceiling
VENT_Y = _g(_H, "VENT_Y", (-13.0, 1.0))

# ---- local layout of the internal components (decisions of this module) --------------------
CELL_PLUS_GAP = 0.5         # + tip 0.5 inside the bay end face (on the + plate)
SPRING_H = 4.9              # - spring length (compressed)
CLIFF_PCB = (10.4, 6.0, 0.8, 0.8)   # tangential x radial x t, shifted 0.8 toward the corner centre (tray wall R19.6)
CLIFF_Z0 = FLOOR_TOP + 0.6
POGO_Z0 = FLOOR_TOP + 0.6   # tip on the B12 rivet stem
UG_LEDS, UG_FLEX_T = 24, 0.3
CHEST_LEDS = (-10.0, -5.0, 0.0, 5.0, 10.0)               # 5x WS2812B-2020 light bar (= T06 glow)
TOF_X, ALS_X = 14.5, -14.5
CAM_Z = 185.6               # proposal: lens through the black bezel top rail (see DEVIATIONS)
ROOF_IN_Z = HD["z1"] - HD["wall"]                       # 189 flat inner roof of H01 (|x| < 27)
# INMP441 (review 2): flat on the barrel-pocket ceiling, bottom port over the -X vent slot x -10.5 -> hears the room
# through the open pocket mouth around the neck (the v1 spot under the roof was visible through the top bezel seam)
MIC_PORT = (VENT_X[1] if len(VENT_X) > 1 else -10.5, (VENT_Y[0] + VENT_Y[1]) / 2)     # (-10.5, -6.0)
MIC = dict(x=MIC_PORT[0] - 1.5, y=MIC_PORT[1], foam=0.5)                             # module centre, VHB 0.5
# cable way points (x, y, z)
NECK_PATH_J1 = [(-12.0, 20.3, 68.8), (-12.6, 17.0, 70.5), (-14.6, 11.0, 74.5), (-15.0, 9.0, 79.5),
                (-9.0, 5.5, 84.5), (-3.0, 1.5, 87.6), (0.0, 0.0, 89.4)]
NECK_PATH_J2 = [(0.0, 0.0, 89.4), (0.0, 0.0, 96.0), (0.0, 0.0, 108.0), (0.0, 0.5, 120.0), (0.0, 4.5, 130.0),
                (0.0, 9.2, 136.2), (0.0, 10.4, 137.6)]
NECK_PATH_J3 = [(0.0, 10.4, 137.6), (0.0, 10.0, 142.0), (0.0, 9.0, 146.5), (-3.0, 3.0, 151.0),
                (-12.0, -7.0, 159.0), (-24.0, -16.0, 165.0), (-30.0, -21.0, 167.0),
                (-30.5, -25.0, 167.25)]                  # review 2: ends on the 5 V / UART JST (x -34..-27) of IH02
NECK_T0, NECK_T3 = (0, 0, 1), (0, -1, 0)
YAW_T1 = (0, 1, 0)
YAW_LOOP_Z_IN = 21.0

# ---- J1 cable: ROLLING LOOP of a flat 6-wire band (review 2) ------------------------------------------------
# v1 had an 18-20 wire Ø6 bundle as ONE 200 deg arc (92 mm): at J1 +150 that path needs 162 mm, at -150 there are
# 69 mm of slack - and a Ø6 bundle cannot fold in the 14 mm wide trough.  Now the base has its own node (IB09-2:
# STM32G030 + DRV8833 + 5 V), so only VBAT, GND (24 AWG), the 1-wire servo bus, speaker +/- and a spare GND (28 AWG)
# cross J1.  The band (6 silicone wires side by side, Kapton-taped, standing ON EDGE) runs from the fixed exit CW
# along the fixed trough rim (outer run), makes a U-turn and runs back CCW wrapped on the rotating T04 bearing
# housing (inner run) to the riser into the T04 slot.  Turning the torso by dJ1 moves the U-turn by
# dJ1 * r_i / (r_o + r_i) - constant length, constant bend radius (6 mm = 4.6 x the 24 AWG OD), ±150 deg.
YB_T, YB_H = 1.3, 6.2                               # band thickness (radial) x height (2 x 1.3 + 4 x 0.9)
YB_ZC = (TROUGH_FLOOR + min(B09_Z0, TROUGH_FLOOR + 7.0)) / 2 - 0.15     # 31.9 (0.3 above the floor, 0.6 under B09)
YB_RO = TROUGH_RIM_IN - YB_T / 2 - 0.25             # 35.6 outer run centre (0.25 from the rim)
YB_RI = YH_RO + YB_T / 2 + 0.35                     # 23.5 inner run centre (0.35 from the rotating housing)
YB_RB = (YB_RO - YB_RI) / 2                         # 6.05 U-turn bend radius
YB_F = math.degrees(math.atan2(FIX_EXIT[1], FIX_EXIT[0]))     # -20 fixed exit (base B15 hole)
YB_DF = 15.0                                        # exit -> outer run transition (bundle fans into the band)
YB_FO = YB_F - YB_DF                                # -35 outer run starts here (going CW)
YB_RISER = math.degrees(math.atan2(RISER_XY[1], RISER_XY[0])) % 360.0   # 180 riser angle at J1 = 0 (T04 slot centre)
YB_SC = 8.0                                         # band S-curve r_i -> riser radius over the last 8 deg
YB_M0 = YB_RISER - YB_SC                            # 172 inner-run end at J1 = 0
YB_RS = YB_RI + 2.4                                 # 25.9 riser bundle radius (T04 slot r 23..29, housing 22.5)
YB_FAN_H = -62.0                                    # heading of the exit fan after the bend (deg)
J1_RANGE = (-150.0, 150.0)
YB_MARGIN = 3.0                                     # inner run never shorter than 3 deg at J1 = -150


def yaw_loop(j1=0.0):
    """Rolling-loop state for a torso angle j1 (deg): (outer run deg, inner run deg, U-turn angle abs deg).
    Angles are CW distances from the outer-run start YB_FO; the moving end M = YB_M0 + j1."""
    def m_cw(j):      # continuous in j: 145 - j (at J1 +150 the riser is 5 deg past the outer-run start, radially inside)
        return ((YB_FO - YB_M0) % 360.0) - j
    m_max = max(m_cw(j) for j in J1_RANGE)
    lp = YB_RO * math.radians(m_max + YB_MARGIN)                     # band length minus the U-turn
    m = m_cw(j1)
    o = math.degrees((lp + YB_RI * math.radians(m)) / (YB_RO + YB_RI))
    return o, o - m, YB_FO - o


def yaw_loop_length():
    o, i, _ = yaw_loop(0.0)
    return YB_RO * math.radians(o) + YB_RI * math.radians(i) + math.pi * YB_RB


YAW_TORSO_PATH = [(-26.2, 2.5, 45.0), (-26.5, 4.0, 50.0), (-25.0, 8.5, 55.5),
                  (-21.5, 11.5, 59.0), (-18.7, 13.5, 59.85)]     # -> JST-GH 6p on the front face of IT07

# The shell modules keep simple envelopes of the same bought components (for their own clearance checks).  This
# module is the detailed set; for x-ray / section renders and the BOM use ONE of them: exclude the shell ids below
# (render job "exclude": SUPERSEDED) or exclude "I*".
SUPERSEDES = {
    "IB01-R": ["BM2-R"], "IB02-R": ["BM2-R"], "IB03-R": ["BM2-R"],
    "IB01-L": ["BM2-L"], "IB02-L": ["BM2-L"], "IB03-L": ["BM2-L"],
    "IB04-1P": ["BM5"], "IB04-1M": ["BM5"], "IB04-2P": ["BM5"], "IB04-2M": ["BM5"],
    "IB05-1": ["BE1-1"], "IB05-2": ["BE1-2"], "IB06": ["BE5"],
    "IB07-1": ["BE3"], "IB07-2": ["BE3"], "IB07-3": ["BE3"], "IB07-4": ["BE3"], "IB08": ["BE4"],
    "IB09-1": ["BE2"], "IB09-2": ["BE6"], "IB10-1": ["BE2"], "IB10-2": ["BE6"], "IW2": ["BW1"],
    "IT01": ["E21"], "IT02": ["E21H"], "IT04": ["M21"], "IT05-R": ["E22-R"], "IT05-L": ["E22-L"],
    "IT06-R": ["E22H-R"], "IT06-L": ["E22H-L"], "IT07": ["E24"], "IT08": ["E24"], "IT09": ["E25"],
    "IN01": ["E23"], "IN02": ["E23H"], "IN03": ["M22"],
    "IH01": ["E31"], "IH02": ["E31"], "IH03": ["E31"], "IH04": ["E32"], "IH07-R": ["E33-R"], "IH07-L": ["E33-L"],
}
SUPERSEDED = sorted({x for v in SUPERSEDES.values() for x in v})
NEW_ONLY_HERE = ["IT03", "IT10", "IH06 (option)", "IH08", "IW1-1", "IW1-2", "IW1-3", "IW3",
                 "IB09-2 base node (STM32G030 + DRV8833 + 5 V)"]

DEVIATIONS = [
    "kábel krku 6 vodičov namiesto 4 (5 V, GND, TX, RX + pár reproduktora): reproduktor je v základni, zosilňovač na "
    "doske hlavy; zväzok Ø3 prejde otvormi Ø8 v N03/N02 aj štrbinou valca",
    "voliteľná kamera: spec z 180.5 leží na hornej hrane dosky 86×56 (z 182) - za sklom nie je miesto; návrh: objektív "
    "Ø6 za čiernou hornou lištou rámu H03 na z 185.6 (čierne na čiernom = neviditeľné), modul nad doskou -> modul hlavy "
    "musí doplniť otvor Ø3 + vrecko v H03 a presunúť H04C",
    "držiak 18650 = tlačené šachty B02 nad poklopmi + kupované kontakty (+ plôška / − kužeľová pružina, IB04); samostatný "
    "kupovaný držiak sa medzi mostík a stenu vaničky nezmestí",
    "hruď: 5 LED (rozloženie E25 trupu) + 'malý vnútorný rám' = čierny rámik so svetelnou clonou IT10 (nosný rám je "
    "T07/T08 trupu, neduplikuje sa)",
    "tlačidlo zapnutia: samoaretačné 6×6 (push-on/push-off) namiesto momentového spínača BE6 - netreba soft-power obvod; "
    "tlačidlo (~0.1 A) spína len hradlo P-MOSFETu AO4407A (−30 V / 12 A) na IB09-1, prúd robota (špičky ~5 A) ním netečie",
    "revízia 2 – UZOL ZÁKLADNE: motory N20 (DRV8833), enkodéry A/B, 4 senzory pádu a podsvietenie riadi STM32G030 "
    "na DPS IB09-2 (slave na 1-vodičovej zbernici serv, ako ďalšie 'servo'); DRV8833 teda nie je v trupe "
    "(spec TORSO.controller). Dôvod: v1 viedla cez J1 zväzok Ø6 s 18–20 vodičmi ako jeden oblúk 200° (92 mm) – pri "
    "J1 +150° by chýbalo 70 mm kábla, pri −150° by 69 mm voľného kábla nemalo kam ísť a Ø6 sa v žľabe šírky 14 mm "
    "neohne. Teraz cez J1 idú 6 vodičov (VBAT, GND 24 AWG, zbernica, reproduktor ±, GND) ako plochý pás vo valivej "
    "slučke (konštantná dĺžka 209 mm, ohyb R6, ±150°). ESP32-C3 v trupe potom stačí 11 z 13 GPIO – v1 obchádzka "
    "PCA9685 + ADS1115 odpadá; rozpis pinov v BOM_v8.md, kap. 7",
    "skrutka otáčania M3×20 (nie M3×25 z popisu základne): s podložkou na strope veže B14 (z 24.5) by M3×25 prešla "
    "5 mm za závit v drážkovaní STS3215",
    "mikrofón INMP441 (revízia 2) naležato na strope kapsy valca, spodný port utesnený penovým krúžkom nad skrytou "
    "vetracou štrbinou x −10.5 – počuje cez otvorené ústie kapsy okolo krku. Hlava v8.1 zrušila otvor mikrofónu v "
    "uchu a Guition JC3248W535 mikrofón nemá; poloha v1 pod stropom bola spredu vidieť cez hornú škáru rámu",
    "USB-C / tlačidlo / dok podľa základne v8.1: USB (-24, 40), tlačidlo (24, 40), pogo piny (±36, 41) na 2 DPS nad "
    "zadným kolieskom (nie spec (-20, 46) / (20, 46) / (±8, 50))",
    "podsvietenie: 24× WS2812B-2020 na flex prstenci nad opálovým svetlovodom B-UG (návrh základne), svietia dole",
    "kábel krku: 5 V a GND 26 AWG (špičky ~2 A: doska + podsvietenie LCD + servo náklonu + LED uší + zosilňovač), "
    "TX, RX a reproduktor 30 AWG; 30 AWG pre napájanie (~0.9 A) by nestačil",
    "DPS IB09-1/IB09-2 s čiernou maskou: ležia priamo pod zadnou časťou škáry B01/B09 a zhora boli cez ňu vidieť",
]


# ============================================================================================
# part builders (global coordinates)
# ============================================================================================

# ---------------- head ----------------
DSP_Y_LCD1 = Y_DSP0 + 3.0                # LCD back / PCB front (-30.8)
DSP_Y_PCB1 = Y_DSP1 - 1.4                # PCB back (-29.2) = face of the H07 clamp pad
DSP_WIN = (74.0, 42.0)                   # component field on the back (inside the H07 window 76 x 44)


def ih01_lcd():
    lcd = rr_y(DSP_W - 1.0, DSP_H - 1.0, 1.5, Y_DSP0, DSP_Y_LCD1, cz=DSP_ZC)
    # FPC tail folded around the bottom edge to the board connector
    fpc = bx(-9.0, 9.0, DSP_Y_LCD1 - 0.01, DSP_Y_LCD1 + 0.19, DSP_ZC - DSP_H / 2 + 0.5, DSP_ZC - DSP_H / 2 + 6.0)
    return lcd + fpc


def ih02_board():
    """Head board (JC3248W535 class): 86 x 56 PCB, all parts on the back inside the H07 window field."""
    y0, y1 = DSP_Y_LCD1 + 0.2, DSP_Y_PCB1      # -30.6 .. -29.2
    zc = DSP_ZC
    b = rr_y(DSP_W, DSP_H, 2.0, y0, y1, cz=zc)
    for (x, z) in ((-40.0, zc - 24.0), (40.0, zc - 24.0), (-40.0, zc + 24.0), (40.0, zc + 24.0)):
        b = b - cyl_y(x, z, 1.1, y0 - 1, y1 + 1)                          # 4x M2 mounting holes
    zb, zt = zc - DSP_WIN[1] / 2, zc + DSP_WIN[1] / 2                     # component field z 133 .. 175
    yc = y1 - 0.01
    comps = [
        bx(-4.47, 4.47, yc, y1 + 3.26, zb + 0.5, zb + 7.85),              # USB-C receptacle (service, module out)
        bx(-34.0, -28.0, yc, y1 + 4.2, zb + 2.0, zb + 6.5),               # JST 1.25 speaker (-> neck bundle)
        bx(-34.0, -27.0, yc, y1 + 4.2, zt - 10.0, zt - 5.5),              # JST 1.25 5 V / UART (neck bundle)
        bx(-24.0, -17.0, yc, y1 + 4.2, zt - 10.0, zt - 5.5),              # JST 1.25 ears + tilt servo
        bx(12.0, 26.0, yc, y1 + 1.8, zb + 1.0, zb + 13.0),                # micro-SD slot
        bx(-24.0, -12.0, yc, y1 + 1.2, zc - 4.0, zc + 4.0),               # LCD / touch FPC connectors
        bx(-8.0, 0.0, yc, y1 + 1.0, zc - 12.0, zc - 4.0),                 # codec / amp
        bx(30.0, 34.0, yc, y1 + 1.5, zb + 2.0, zb + 6.0),                 # BOOT / RST buttons
        bx(-9.0, -3.0, yc, y1 + 2.0, zb + 10.0, zb + 16.0),               # 3.3 V regulator + inductor
    ]
    return union([b] + comps)


def ih03_s3_module():
    y1 = DSP_Y_PCB1
    m = bx(6.0, 24.0, y1, y1 + 0.8, DSP_ZC - 6.0, DSP_ZC + 19.5)          # module PCB 18 x 25.5 (antenna up)
    can = bx(7.1, 22.9, y1 + 0.79, y1 + 3.1, DSP_ZC - 5.0, DSP_ZC + 12.6)  # shield can 15.8 x 17.6
    return m + can


def ih06_camera():
    """Optional OV2640 FPC camera (66 deg): lens Ø6 x 3.5 + 8 x 8 sensor PCB above the display board, FPC down to
    the board.  Lens through the black bezel top rail (see DEVIATIONS: spec z 180.5 sits on the board edge)."""
    y_front = Y_DSP0 + 0.3
    lens = cyl_y(0.0, CAM_Z, 3.0, y_front, y_front + 3.5)
    pcb = bx(-4.0, 4.0, y_front + 3.49, y_front + 4.5, CAM_Z - 3.2, CAM_Z + 3.2)
    fpc = bx(-3.5, 3.5, y_front + 4.49, y_front + 4.7, DSP_ZC + DSP_H / 2 - 4.0, CAM_Z - 3.19)
    return lens + pcb + fpc


def ih08_mic():
    """INMP441 I2S MEMS microphone module 14 x 13 (review 2).  The INMP441 is BOTTOM-PORTED (sound hole through the
    module PCB under the mic can).  v1 hung it under the roof right behind the top bezel seam - it was visible
    through that seam from the front (id-pass check) and heard only through a 0.5 mm slit behind the front module.
    Now it lies FLAT ON THE BARREL-POCKET CEILING (H01, z 146.5), held by a 0.5 mm VHB foam ring whose hole seals
    the port onto the -X hidden vent slot (x -10.5): sound path = open pocket mouth around the neck -> 2.5 mm gap
    over the barrel -> slot -> port (~6 mm, short, no hole outside, nothing in a sight line; far from the +X tilt
    servo).  Wires (6) go up to the head board's expansion header."""
    px, py = MIC_PORT
    x, y = MIC["x"], MIC["y"]
    z0 = PK_CEIL_TOP + MIC["foam"]                                            # PCB underside 147.0
    hx, hy = 7.0, 6.5
    foam = bx(x - hx + 0.5, x + hx - 0.5, y - hy + 0.5, y + hy - 0.5, PK_CEIL_TOP + 0.01, z0 + 0.01) - \
        cyl_z(px, py, 0.9, PK_CEIL_TOP - 1, z0 + 1)                          # VHB ring, hole over the port
    pcb = bx(x - hx, x + hx, y - hy, y + hy, z0, z0 + 1.0) - cyl_z(x + 4.5, y + 4.0, 1.1, z0 - 1, z0 + 2)
    pcb = pcb - cyl_z(px, py, 0.5, z0 - 1, z0 + 2)                            # acoustic port (through the PCB)
    can = bx(px - 2.0, px + 2.0, py - 1.5, py + 1.5, z0 + 0.99, z0 + 2.0)     # INMP441 can over the port
    hdr = bx(x - hx + 0.6, x - hx + 3.1, y - 5.0, y + 5.0, z0 + 0.99, z0 + 2.6)   # 6 wire pads + soldered leads
    return union([foam, pcb, can, hdr])


def tilt_servo_frame():
    return frame((TILT_SERVO_TOP_X, TILT_Y, TILT_SERVO_Z), (0, 0, 1), (-1, 0, 0))


def ih04_tilt_servo():
    return tilt_servo_frame() * micro_servo_local()


def ear_pcb(sx, mic=False):
    ey, ez = EAR["y"], EAR["z"]
    x0 = sx * X_EAR_IN
    t = 1.0
    p = cyl_x(ey, ez, EAR["ring_od"] / 2, x0, x0 + sx * t)
    xl = x0 + sx * t
    leds = []
    for k in range(6):
        a = math.radians(30 + 60 * k)
        cy, cz = ey + 10.0 * math.cos(a), ez + 10.0 * math.sin(a)
        leds.append(Pos(xl + sx * 0.42 - sx * 0.005, cy, cz) * Rot(math.degrees(a), 0, 0) * Box(0.85, 2.0, 2.2))
    if mic:      # MEMS microphone (INMP441 class) in the centre, port toward the ear
        leds.append(Pos(xl + sx * 0.5, ey, ez) * Box(1.01, 3.5, 2.65))
    else:        # level shifter / cap on the other ear
        leds.append(Pos(xl + sx * 0.3, ey, ez) * Box(0.61, 2.0, 1.25))
    # wire pads + 3-wire pigtail stub toward the inside
    p = p + bx(x0 - sx * 1.2, x0 + sx * 0.01, ey - 2.0, ey + 2.0, ez - 9.5, ez - 7.5)
    return union([p] + leds)


# ---------------- neck / pan ----------------
def pan_servo_frame():
    return frame((0.0, PAN_Y, PAN_TOP_Z), (1, 0, 0), (0, 0, 1))


def in01_pan_servo():
    return pan_servo_frame() * micro_servo_local()


def in02_pan_horn():
    """Standard double horn 18 x 5.6 of the pan servo, seated in the N04 gear recess (drives the pan stage 1:1):
    hub z 89.0..92.1, blade z 90.5..92.1 (cad_torso E23H)."""
    z_top = PAN_HORN_Z1 - PAN_TOP_Z
    h = horn_stadium_local(18.0, 5.6, PAN_HORN_Z0 - PAN_TOP_Z, PAN_G_Z0 - PAN_TOP_Z, z_top)
    return pan_servo_frame() * h


def in03_pan_bearing():
    return bearing_z(0, 0, PB_RI, PB_RO, PB_Z0, PB_Z1)


# ---------------- torso ----------------
def yaw_frame():
    return frame((0.0, 0.0, YS_Z0), (1, 0, 0), (0, 0, -1))


def it01_sts3215():
    return yaw_frame() * sts3215_local()


def it02_yaw_horn():
    """Aluminium disc horn Ø20 (25T) bolted to the fixed base hub: disc z 39..41.5, hub to 43.4."""
    z_spl0 = YS_Z0 - STS_BOSS[1] - STS_SPL[1]           # 40.5 spline tip
    h = cyl_z(0, 0, 10.0, YAW_Z1, YAW_Z1 + 2.5) + cyl_z(0, 0, 4.5, YAW_Z1 + 2.49, YS_Z0 - STS_BOSS[1] - 0.1)
    h = try_fillet(h, h.edges().group_by(Axis.Z)[0], 0.4)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h - cyl_z(7.0 * math.cos(a), 7.0 * math.sin(a), 1.1, YAW_Z1 - 1, YAW_Z1 + 3)
    for k in range(4):                                   # 4 lightening / tool holes
        a = math.radians(90 * k)
        h = h - cyl_z(7.0 * math.cos(a), 7.0 * math.sin(a), 0.9, YAW_Z1 - 1, YAW_Z1 + 3)
    h = h - cyl_z(0, 0, STS_SPL[0] + 0.05, z_spl0 - 0.1, YS_Z0) - cyl_z(0, 0, 1.6, YAW_Z1 - 1, YS_Z0)
    return h


YAW_SCREW_L = 20.0          # M3 x 20: washer on the bridge-tower roof underside, 4 mm thread in the spline


def it03_yaw_screw():
    """M3 x 20 DIN 912 + DIN 433 washer from below (service hole Ø7 under the B17 plug -> bridge tower cavity ->
    tower roof -> B15 bore -> horn) into the STS3215 spline thread = the axial coupling of J1."""
    seat = TOWER_ROOF_Z                                 # 24.5 washer top = roof underside
    w_t = 0.5
    z_head1 = seat - w_t                                # head top (under the washer)
    tip = z_head1 + YAW_SCREW_L
    tip = min(tip, YS_Z0 - 0.6)                         # never deeper than the spline thread
    s = cyl_z(0, 0, 1.2, z_head1 - 0.01, tip) + cyl_z(0, 0, 2.75, z_head1 - 3.0, z_head1)
    s = s + ring_z(0, 0, 1.6, 3.0, z_head1 - 0.01, seat)
    hexs = Pos(0, 0, z_head1 - 3.0 - 0.01) * extrude(Face(Wire.make_polygon(
        [Vector(1.3 * math.cos(math.radians(60 * k)), 1.3 * math.sin(math.radians(60 * k)), 0) for k in range(6)],
        close=True)), 2.0)
    return s - hexs


def it04_yaw_bearing():
    return bearing_z(0, 0, YAW_BRG[0] / 2, YAW_BRG[1] / 2, YAW_Z1 - YAW_BRG[2], YAW_Z1)


def arm_servo_frame(sx):
    return frame((sx * ARM_TOP_X, ARM_Y, ARM_Z), (0, -1, 0), (sx, 0, 0))


def it05_arm_servo(sx):
    return arm_servo_frame(sx) * micro_servo_local()


def it06_arm_horn(sx):
    """Double horn trimmed to 13 mm = the key that drives the A04 joint coupler (cad_torso HORN_ARM 13 x 5.6 x 1.6,
    blade from the spline tip |x| 43 to 44.6, hub from 40.4)."""
    h = horn_stadium_local(13.0, 5.6, MS_DOME_H + 0.2, MS_SPL_TOP, MS_SPL_TOP + 1.6, holes=False)
    return arm_servo_frame(sx) * (Rot(0, 0, 90) * h)


def tssop_y(x0, x1, z0, z1, y_face, toward, body_h=1.2, lead_w=None):
    """SMD IC (TSSOP / MSOP / SO-8) on a vertical board face y_face, growing toward -Y (toward=-1) or +Y (+1):
    body x0..x1 / z0..z1 + a thin gull-wing lead slab (wider in z)."""
    lw = lead_w if lead_w is not None else (z1 - z0) + 2.0
    zc = (z0 + z1) / 2
    yb = y_face + toward * body_h
    body = bx(x0, x1, y_face - toward * 0.01, yb, z0, z1)
    leads = bx(x0 + 0.3, x1 - 0.3, y_face - toward * 0.01, y_face + toward * 0.25, zc - lw / 2, zc + lw / 2)
    return body + leads


def it07_controller():
    """Carrier PCB 48 x 18.5 (vertical in the T08 slots, behind the rear door): MP1584 5 V (micro servos, head,
    chest LEDs), 74LVC1G126 half-duplex driver of the 1 Mbit servo bus, connectors; the ESP32-C3 SuperMini is IT08.
    Review 2: the motor driver and all base sensors moved to the base node IB09-2 (it is a slave on the same servo
    bus), so the C3 needs 11 of its 13 GPIO (UART0 head, UART1 bus + DIR, I2C ToF/ALS, chest LED data, 3 PWM for
    MG90S) - the v1 PCA9685 + ADS1115 work-around and the DRV8833 module are gone; only 6 wires cross J1."""
    C = CTRL
    y0, y1 = C["y0"], C["y0"] + C["t"]
    z0, z1 = C["z0"], C["z1"]
    b = bx(-C["x"], C["x"], y0, y1, z0, z1)
    comps = [
        bx(-21.0, -5.0, y0 - 3.4, y0 + 0.01, z0 + 1.0, z0 + 11.5),       # MP1584 5 V module (front side)
        bx(-21.0, -16.0, y0 - 5.2, y0 - 3.39, z0 + 3.0, z0 + 8.0),       # its inductor (clear of the T08 wall)
        tssop_y(4.0, 6.0, z0 + 13.5, z0 + 16.4, y0, -1, body_h=1.0, lead_w=3.0),   # 74LVC1G126 (SOT-23-5)
        bx(0.5, 3.5, y0 - 0.9, y0 + 0.01, z0 + 9.0, z0 + 12.0),          # bus pull-up + 1k series R / ESD (0603)
        bx(9.0, 16.0, y0 - 2.0, y0 + 0.01, z0 + 3.0, z0 + 7.0),          # 470 uF/10 V polymer cap (servo 5 V rail)
        bx(-22.8, -14.6, y0 - 4.5, y0 + 0.01, z1 - 5.2, z1 - 0.5),       # JST-GH 6p: J1 band (VBAT GND BUS SPK+- GND)
        bx(-23.0, -8.0, y0 - 1.0, y1 + 4.0, z1 - 0.01, z1 + 6.0),        # servo headers (3 x 3-pin + STS bus)
        bx(19.0, 23.5, y0 - 1.0, y1 + 4.0, z1 - 0.01, z1 + 6.0),         # neck / chest JST
    ]
    return union([b] + comps)


def it08_supermini():
    C = CTRL
    y1 = C["y0"] + C["t"]
    z0 = C["z0"]
    pcb = bx(-22.5, 0.0, y1 + 2.5, y1 + 3.5, z0 + 0.25, z0 + 18.25)
    pins = bx(-21.5, -1.0, y1, y1 + 2.51, z0 + 1.0, z0 + 3.5) + bx(-21.5, -1.0, y1, y1 + 2.51, z0 + 15.0, z0 + 17.5)
    chip = bx(-15.0, -10.0, y1 + 3.49, y1 + 4.3, z0 + 6.5, z0 + 11.5)
    ant = bx(-4.0, -1.0, y1 + 3.49, y1 + 4.6, z0 + 3.0, z0 + 15.0)     # ceramic antenna
    usb = bx(-23.4, -16.0, y1 + 3.49, y1 + 6.7, z0 + 5.5, z0 + 14.5)    # USB-C (flashing through the door)
    return pcb + pins + chip + ant + usb


def it09_chest_pcb():
    """Chest board behind the smoked dead-front strip (T05): 5x WS2812B-2020 light bar, VL53L0X ToF (x +14.5)
    and LTR-303 ambient-light sensor (x -14.5) behind the same dark window; 2x M2 from behind into T01 bosses."""
    y0, zc = E25["y0"], CHS["z"]
    t = E25["t"]
    b = bx(-E25["x"], E25["x"], y0, y0 + t, E25["z0"], E25["z1"])
    for sx in (1, -1):
        b = b - cyl_y(sx * E25["boss"][0], E25["boss"][1], 1.1, y0 - 1, y0 + t + 1)
    comps = [ws2812_2020(x, y0, zc, "-Y") for x in CHEST_LEDS]
    comps.append(bx(TOF_X - 2.2, TOF_X + 2.2, y0 - 1.0, y0 + 0.01, zc - 1.2, zc + 1.2))   # VL53L0X 4.4 x 2.4 x 1
    comps.append(bx(ALS_X - 1.0, ALS_X + 1.0, y0 - 0.7, y0 + 0.01, zc - 1.0, zc + 1.0))   # LTR-303 2 x 2 x 0.7
    for x in (-7.5, 7.5):
        comps.append(bx(x - 0.5, x + 0.5, y0 - 0.5, y0 + 0.01, zc + 0.9, zc + 1.7))       # decoupling caps
    comps.append(bx(-6.0, 6.0, y0 + t - 0.01, y0 + t + 3.0, zc + 1.5, zc + 5.0))         # JST-SH 6p (back)
    return union([b] + comps)


def _inner_skin(d):
    """Torso volume inside the offset d of the outer skin (exact offset from cad_torso when available)."""
    if _T is not None and hasattr(_T, "off"):
        try:
            return _T.off(d)
        except Exception as ex:  # noqa: BLE001
            print(f"  [internals] cad_torso.off({d}) failed: {ex!r} - superellipse approximation")
    from nova.cad.common import superellipse_wire
    w = superellipse_wire(TS["w"] / 2 - d, TS["d"] / 2 - d, TS["n"], 70.0, count=96)
    return extrude(Face(w), 30.0)


def it10_chest_frame():
    """Small internal frame of the chest: black PETG light baffle between T05 and the board.  Separates the LED
    bar from the ToF / ALS windows (no optical cross-talk through the shared dead-front strip), clears the 2
    board bosses, front face follows the T05 flange (offset 2.9), back face on the board."""
    y0, zc = E25["y0"], CHS["z"]
    hh = 4.0
    f = bx(-18.4, 18.4, y0 - 6.0, y0, zc - hh, zc + hh) & _inner_skin(T_WALL + T05_FLANGE + 0.1)
    f = f - bx(-11.4, 11.4, y0 - 7, y0 + 1, zc - 1.9, zc + 1.9)                 # LED bar window
    f = f - bx(TOF_X - 2.4, 17.6, y0 - 7, y0 + 1, zc - 1.9, zc + 1.9)            # ToF window
    f = f - bx(-16.6, ALS_X + 1.6, y0 - 7, y0 + 1, zc - 1.9, zc + 1.9)           # ALS window
    for sx in (1, -1):
        f = f - cyl_y(sx * E25["boss"][0], E25["boss"][1], 2.6, y0 - 8, y0 + 1)   # boss clearance
    return f


# ---------------- base ----------------
def motor_frame(sx):
    return frame((sx * GB_FACE, WY, WZ), (sx, 0, 0), (0, -sx, 0))


def ib_motor(sx):
    m, e, sh = n20_local()
    f = motor_frame(sx)
    return f * m, f * e, f * sh


def ib_cell(sy):
    """Front cell (+ toward +X) and rear cell (+ toward -X): series loop, + tip 0.5 inside the bay end face."""
    c = cell_18650_x(0.0, 0.0, 0.0)
    plus = 1 if sy < 0 else -1
    if plus < 0:
        c = Rot(0, 0, 180) * c
    xc = plus * (BAY_X - CELL_PLUS_GAP - CELL_L / 2)
    return Pos(xc, sy * CELL_Y, CELL_Z0) * c


def spring_x(x0, x1, y, z, r0=4.0, r1=2.2, wire=0.35, turns=4.0):
    """Conical battery spring along X from x0 (base, radius r0) to x1 (tip, radius r1)."""
    L = abs(x1 - x0)
    s = 1 if x1 > x0 else -1
    pts = []
    n = int(turns * 24)
    for k in range(n + 1):
        u = k / n
        r = r0 + (r1 - r0) * u
        a = 2 * math.pi * turns * u
        pts.append((x0 + s * (wire + (L - 2 * wire) * u), y + r * math.cos(a), z + r * math.sin(a)))
    foot = Pos(x0 + s * 0.6 * wire, y + r0, z) * Sphere(wire * 1.05)       # welded foot on the plate
    return tube(pts, wire) + foot


def ib_contacts(sy):
    """Bay contacts of one cell: nickel-plated + plate (with solder tab) and - plate with a conical spring."""
    yc, zc = sy * CELL_Y, CELL_Z0 + CELL_D / 2
    plus = 1 if sy < 0 else -1
    xp = plus * BAY_X
    pp = bx(xp - plus * CELL_PLUS_GAP, xp, yc - 4.5, yc + 4.5, zc - 5.0, zc + 5.0)   # cell + tip rests on it
    pp = pp + bx(xp - plus * CELL_PLUS_GAP, xp, yc - 1.5, yc + 1.5, zc + 4.99, zc + 9.0)   # solder tab up
    xm = -plus * BAY_X
    mp = bx(xm, xm + plus * 0.4, yc - 4.5, yc + 4.5, zc - 5.0, zc + 5.0)
    mp = mp + bx(xm, xm + plus * 0.4, yc - 1.5, yc + 1.5, zc + 4.99, zc + 9.0)
    x_cell_minus = plus * (BAY_X - CELL_PLUS_GAP - CELL_L)                           # - end of the cell
    spr = spring_x(xm + plus * 0.4, x_cell_minus - plus * 0.05, yc, zc)
    return pp, mp + spr


def ib_speaker():
    """Ø28 speaker standing vertically, front face y_face toward -Y (into the sealed front chamber)."""
    sp = speaker_z(0.0, 0.0, SPK["d"], SPK["h"], 0.0, down=True)     # front toward -Z
    return Pos(SPK["x"], SPK["y_face"], SPK["z"]) * Rot(-90, 0, 0) * sp


def ib_cliff(x, y):
    """TCRT5000 on a 12 x 6.8 mini PCB, looking down through its IR window (tangential in the corner)."""
    ccx = math.copysign(BS["w"] / 2 - BS["plan_r"], x)
    ccy = math.copysign(BS["d"] / 2 - BS["plan_r"], y)
    ang = math.degrees(math.atan2(y - ccy, x - ccx)) + 90.0
    L, W, H = 10.2, 5.8, 7.0
    z0 = CLIFF_Z0
    body = bx(-L / 2, L / 2, -W / 2, W / 2, z0, z0 + H)
    for s_ in (-1, 1):
        body = body - cyl_z(s_ * 2.5, 0, 1.4, z0 - 0.1, z0 + 0.5)       # emitter / detector lenses
    body = body - bx(-0.35, 0.35, -W / 2 - 1, W / 2 + 1, z0 - 0.1, z0 + 3.0)   # divider slot
    pl, pw, pt, sh = CLIFF_PCB
    pcb = bx(-pl / 2, pl / 2, -pw / 2 + sh, pw / 2 + sh, z0 + H, z0 + H + pt)   # local +y = toward the corner centre
    con = bx(-3.8, 3.8, -1.6 + sh, 1.6 + sh, z0 + H + pt - 0.01, z0 + H + pt + 3.2)    # JST-SH 3-pin
    return Pos(x, y, 0) * Rot(0, 0, ang) * (body + pcb + con)


def ib_board(sx):
    """Rear underside boards (bridging the rear caster, BLACK solder mask - they lie under the rear B01/B09 seam):
    sx=-1 charger (IP2326 2S boost charger + 2S protection + AO4407A main switch + JST; carries the vertical USB-C =
    base part B10), sx=+1 power button + BASE NODE (review 2): 6x6 self-locking switch for B13 underneath; on top an
    STM32G030K8T6 (servo-bus slave, single-wire half-duplex USART), DRV8833 (both N20, PWM + DIR), 5 V 2 A buck
    (underglow, encoders, cliff sensors), 3.3 V LDO, JST-GH 6p for the J1 band and JST-SH for the motors; the
    cliff sensors and the underglow flex are soldered to pads.  Cliff stop is local (motors off in < 1 ms)."""
    z0, z1 = BOARD_Z0, BOARD_Z0 + BOARD_T
    xc = sx * 25.0
    b = rr_z(30.0, 13.8, 2.0, z0, z1, xc, 39.9)
    for (x, y) in BOARD_STANDOFFS:
        if x * sx > 0:
            b = b - cyl_z(x, y, 1.1, z0 - 1, z1 + 1)
    dx, dy = DOCK_XY[0 if sx < 0 else 1]
    b = b - cyl_z(dx, dy, 0.9, z0 - 1, z1 + 1)                         # pogo pin THT hole
    comps = [b]
    if sx < 0:
        ux, uy = USB_XY
        # main power switch (review fix): the 6x6 self-locking button on IB09-2 only switches the GATE of this
        # P-MOSFET (AO4407A, -30 V / 12 A, SO-8); a 6x6 switch is rated ~0.1 A, the robot peaks at ~5 A
        comps += [bx(-16.0, -12.1, 34.0, 38.9, z1 - 0.01, z1 + 1.5),     # AO4407A body (SO-8 4.9 x 3.9)
                  bx(-16.95, -11.15, 34.3, 38.6, z1 - 0.01, z1 + 0.25),  # its gull-wing leads
                  bx(-15.2, -13.6, 39.6, 40.4, z1 - 0.01, z1 + 0.45),    # 100k gate pull-up (0603)
                  bx(-21.0, -17.0, 35.5, 39.5, z1 - 0.01, z1 + 0.8),     # IP2326 (QFN)
                  bx(-17.0, -12.5, 41.0, 45.5, z1 - 0.01, z1 + 3.0),     # 4.7 uH inductor
                  bx(-30.0, -27.0, 35.5, 38.5, z1 - 0.01, z1 + 1.0),     # 2S protection IC
                  bx(-26.0, -23.0, 42.5, 45.5, z1 - 0.01, z1 + 1.0),     # dual MOSFET
                  bx(-38.0, -33.5, 33.3, 39.3, z1 - 0.01, z1 + 6.0),     # JST-PH battery
                  bx(ux - 5.6, ux - 4.6, uy - 2.6, uy + 2.6, z1 - 0.01, z1 + 1.2),   # USB-C shell tabs (soldered)
                  bx(ux + 4.6, ux + 5.6, uy - 2.6, uy + 2.6, z1 - 0.01, z1 + 1.2)]
    else:
        x, y = BTN_XY
        sw = bx(x - 3.0, x + 3.0, y - 3.0, y + 3.0, 6.95, z0 + 0.01)   # 6x6 self-locking switch body
        sw = sw + cyl_z(x, y, 1.75, 6.6, 6.96)                          # plunger on the B13 cap
        comps += [sw,
                  bx(13.5, 20.5, 35.2, 42.2, z1 - 0.01, z1 + 1.6),       # STM32G030K8T6 (LQFP-32 7 x 7)
                  bx(12.5, 21.5, 34.2, 43.2, z1 - 0.01, z1 + 0.25),      # its leads (9 x 9)
                  bx(23.0, 28.0, 40.8, 45.2, z1 - 0.01, z1 + 1.2),       # DRV8833PWP (HTSSOP-16)
                  bx(23.3, 27.7, 39.8, 46.2, z1 - 0.01, z1 + 0.25),      # its leads
                  bx(23.4, 26.4, 34.3, 37.3, z1 - 0.01, z1 + 1.1),       # TPS563201 5 V buck (SOT-23-6)
                  bx(29.0, 33.0, 39.4, 43.4, z1 - 0.01, z1 + 2.0),       # its 4.7 uH inductor (4 x 4)
                  bx(26.9, 29.9, 34.3, 37.3, z1 - 0.01, z1 + 1.1),       # AP2112K 3.3 V LDO (SOT-23-5)
                  bx(30.4, 39.4, 34.0, 38.2, z1 - 0.01, z1 + 4.2),       # JST-GH 6p: J1 band from the torso
                  bx(32.6, 39.6, 43.2, 46.6, z1 - 0.01, z1 + 2.9)]       # JST-SH 6p: N20 motors + encoders
    return union(comps)


def ib_pogo(x, y):
    """Spring (pogo) pin from the board down onto the B12 pad rivet (robot side of the dock contact)."""
    pin = cyl_z(x, y, 0.75, POGO_Z0, BOARD_Z0 - 2.5 + 0.01) + cyl_z(x, y, 1.5, BOARD_Z0 - 2.5, BOARD_Z0)
    pin = pin + cyl_z(x, y, 0.7, BOARD_Z0 + BOARD_T - 0.01, BOARD_Z0 + BOARD_T + 1.2)      # soldered tail
    pin = pin + cyl_z(x, y, 0.85, BOARD_Z0 - 0.01, BOARD_Z0 + BOARD_T + 0.01)               # through the hole
    return pin


def outline_at(a, b, r, s):
    """Point + unit tangent at arc length s along the CCW rounded rectangle (half sizes a, b, radius r), starting
    at (a, -(b - r)) going up the +X side."""
    L1 = 2 * (b - r)
    Lc = math.pi * r / 2
    L2 = 2 * (a - r)
    segs = [("l", (a, -(b - r)), (0, 1), L1), ("c", (a - r, b - r), 0.0, Lc),
            ("l", (a - r, b), (-1, 0), L2), ("c", (-(a - r), b - r), 90.0, Lc),
            ("l", (-a, b - r), (0, -1), L1), ("c", (-(a - r), -(b - r)), 180.0, Lc),
            ("l", (-(a - r), -b), (1, 0), L2), ("c", (a - r, -(b - r)), 270.0, Lc)]
    for kind, p, d, L in segs:
        if s <= L + 1e-9:
            if kind == "l":
                return p[0] + d[0] * s, p[1] + d[1] * s, d[0], d[1]
            t = math.radians(d + math.degrees(s / r))
            return p[0] + r * math.cos(t), p[1] + r * math.sin(t), -math.sin(t), math.cos(t)
        s -= L
    return a, -(b - r), 0, 1


def ib_underglow():
    """360 deg underglow: polyimide flex ring (inset 3.2..4.8) with 24x WS2812B-2020 facing DOWN into the opal
    PMMA light guide B-UG (the base part) - the flex sits on the guide top, under the B02 flange."""
    t0, t1 = UG_T0 + 0.2, UG_T1 - 0.2
    zf0 = LED_Z1 - UG_FLEX_T
    ring = rr_z(BS["w"] - 2 * t0, BS["d"] - 2 * t0, BS["plan_r"] - t0, zf0, LED_Z1) - \
        rr_z(BS["w"] - 2 * t1, BS["d"] - 2 * t1, BS["plan_r"] - t1, zf0 - 1, LED_Z1 + 1)
    tm = (UG_T0 + UG_T1) / 2
    a, b, r = BS["w"] / 2 - tm, BS["d"] / 2 - tm, BS["plan_r"] - tm
    per = 4 * (a - r) + 4 * (b - r) + 2 * math.pi * r
    leds = []
    for k in range(UG_LEDS):
        x, y, tx, ty = outline_at(a, b, r, (k + 0.5) * per / UG_LEDS)
        ang = math.degrees(math.atan2(ty, tx))
        leds.append(Pos(x, y, (UG_Z1 + zf0) / 2 + 0.005) * Rot(0, 0, ang) * Box(2.2, 1.4, zf0 - UG_Z1 + 0.01))
    return union([ring] + leds)


# ---------------- cables ----------------
def cable_neck():
    """6-wire neck bundle Ø3 (5 V, GND, TX, RX + speaker pair), split at the joints so posed renders stay
    consistent: IW1-1 torso (J1) controller -> under the pan axis; IW1-2 pan stage (J2) up the hollow cone into
    the barrel; IW1-3 head (J3) barrel slot -> pocket ceiling -> board connector."""
    r = 1.5
    up, slot = (0, 0, 1), (0, 1, 1)
    return (tube(NECK_PATH_J1, r, t0=NECK_T0, t1=up), tube(NECK_PATH_J2, r, t0=up, t1=slot),
            tube(NECK_PATH_J3, r, t0=slot, t1=NECK_T3))


def _band_sector(r, a0, a1):
    """Band run on radius r (centre line) between the absolute angles a0 < a1 (deg): exact annular sector."""
    z0, z1 = YB_ZC - YB_H / 2, YB_ZC + YB_H / 2
    face = Face(Wire.make_polygon([Vector(r - YB_T / 2, 0, z0), Vector(r + YB_T / 2, 0, z0),
                                   Vector(r + YB_T / 2, 0, z1), Vector(r - YB_T / 2, 0, z1)], close=True))
    return Rot(0, 0, a0) * revolve(face, Axis.Z, a1 - a0)


def _polar(r, a_deg, z):
    a = math.radians(a_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def band_sweep(points, t0, t1):
    """Flat band ON EDGE (YB_T radial x YB_H vertical) swept along a horizontal spline at z = YB_ZC (fixed binormal
    Z keeps it upright)."""
    pts = [Vector(p[0], p[1], YB_ZC) for p in points]
    path = Wire([Edge.make_spline(pts, tangents=[Vector(*t0).normalized(), Vector(*t1).normalized()])])
    t = path.tangent_at(0)
    pl = Plane(origin=pts[0], x_dir=Vector(0, 0, 1).cross(t), z_dir=t)
    sec = Face.make_rect(YB_T, YB_H, pl)
    sol = Solid.sweep(sec, path)                       # corrected Frenet: planar path -> stays upright
    if not sol.is_valid or sol.volume <= 0:
        raise RuntimeError("band sweep failed")
    return sol


def cable_yaw(j1=0.0):
    """J1 band as a rolling loop (see yaw_loop).
    IW2 (base, ""): round Ø4.2 bundle up through the Ø8 exit hole of B15, 90 deg bend R3.25 just above the floor,
    flat fan into the outer run; outer run CW along the fixed rim, U-turn, inner run CCW on the rotating housing,
    S-curve out to the riser radius.  IW3 (torso J1): the band gathers into a round Ø4.2 bundle that rises through
    the T04 slot and runs to the JST-GH on IT07.  Exact revolved / half-annulus solids for the runs (a spline would
    bulge into the 0.25-0.35 mm clearances)."""
    o, i, u_abs = yaw_loop(j1)
    m_abs = u_abs + i                                                 # == YB_M0 + j1 (mod 360)
    outer = _band_sector(YB_RO, u_abs, YB_FO)
    inner = _band_sector(YB_RI, u_abs, m_abs)
    # U-turn: half annulus in the horizontal plane, centre on the radial line at u_abs, on its CW side
    cx_, cy_, _ = _polar((YB_RO + YB_RI) / 2, u_abs, 0.0)
    ring = ring_z(cx_, cy_, YB_RB - YB_T / 2, YB_RB + YB_T / 2, YB_ZC - YB_H / 2, YB_ZC + YB_H / 2)
    half = Pos(cx_, cy_, YB_ZC) * Rot(0, 0, u_abs) * bx(-20, 20, -20, 0, -10, 10)
    uturn = ring & half
    # fixed exit: vertical round bundle in the hole -> 90 deg bend -> flat fan -> outer-run start (CW tangent)
    rr = 2.1
    fx, fy = FIX_EXIT[0], FIX_EXIT[1]
    z_a = TROUGH_FLOOR + 0.1
    R = YB_ZC - z_a
    d1 = Vector(math.cos(math.radians(YB_FAN_H)), math.sin(math.radians(YB_FAN_H)), 0)
    disk = Face(Wire([Edge.make_circle(rr, Plane(origin=(fx, fy, z_a), z_dir=(0, 0, 1)))]))
    bend = revolve(disk, Axis((fx + R * d1.X, fy + R * d1.Y, z_a), tuple(Vector(0, 0, 1).cross(d1))), 90).solids()[0]
    riser_f = cyl_z(fx, fy, rr, YAW_LOOP_Z_IN, z_a) + bend          # face-to-face (an 0.001 overlap lost the bend)
    b_pt = (fx + R * d1.X, fy + R * d1.Y)
    fo = math.radians(YB_FO)
    fan = band_sweep([b_pt, _polar(YB_RO, YB_FO, 0)[:2]], (d1.X, d1.Y, 0), (math.sin(fo), -math.cos(fo), 0))
    # moving end: S-curve from the inner run (CCW tangent) out to the riser radius
    ma, mr = math.radians(m_abs), math.radians(m_abs + YB_SC)
    scurve = band_sweep([_polar(YB_RI, m_abs, 0)[:2], _polar(YB_RS, m_abs + YB_SC, 0)[:2]],
                        (-math.sin(ma), math.cos(ma), 0), (-math.sin(mr), math.cos(mr), 0))
    base = union([riser_f, fan, outer, uturn, inner, scurve])
    # IW3: round bundle from the S-curve end, up through the T04 slot, to the torso path
    a_r = m_abs + YB_SC                                               # == YB_RISER + j1
    pts = [_polar(YB_RS, a_r, YB_ZC), _polar(YB_RS, a_r + 3.0, YB_ZC + 1.2), _polar(YB_RS, a_r + 5.0, YB_ZC + 3.6),
           _polar(YB_RS, a_r + 4.0, 38.0), _polar(YB_RS, a_r + 2.0, 41.5)]
    torso = tube(pts + YAW_TORSO_PATH, rr, t0=(-math.sin(mr), math.cos(mr), 0.0), t1=YAW_T1)
    return base, torso


# ============================================================================================
# assembly
# ============================================================================================

def check(pid, s, multi=False):
    if s is None:
        raise RuntimeError(f"{pid}: no shape")
    try:
        s = s.clean()
    except Exception:  # noqa: BLE001
        pass
    if not s.is_valid:
        from OCP.ShapeFix import ShapeFix_Shape
        from build123d import Shape
        fx = ShapeFix_Shape(s.wrapped)
        fx.Perform()
        s2 = Shape.cast(fx.Shape())
        if s2.is_valid:
            s = s2 if not isinstance(s2, Compound) or len(s2.solids()) != 1 else s2.solids()[0]
    if not s.is_valid:
        raise RuntimeError(f"{pid}: invalid shape")
    n = len(s.solids())
    if n != 1 and not multi:
        print(f"   [WARN] {pid}: {n} solids")
    if n == 1 and isinstance(s, Compound):
        s = s.solids()[0]
    return s


def build(camera=None):
    """camera=None -> only with --camera on the command line (the optional camera needs an H03 change)."""
    if camera is None:
        camera = "--camera" in sys.argv
    t0 = time.time()
    P = []

    def add(pid, name, shp, mat, sub, joint, expl, note=""):
        P.append(PartRec(pid, name, check(pid, shp), mat, sub, joint, expl, True, note))

    # ---------------- head (J3) ----------------
    add("IH01", "LCD 3.5\" IPS 480×320 s dotykom", ih01_lcd(), "display", "head", "J3", (0, -30, 0),
        note="85×55×3.0, FPC zahnuté okolo spodnej hrany k doske")
    add("IH02", "Doska ESP32-S3 3.5\" (Guition JC3248W535 / Waveshare)", ih02_board(), "pcb", "head", "J3",
        (0, -22, 0), note="86×56×1.6, súčiastky len v okne H07; JST 5 V/UART + reproduktor (krk), JST uši + servo")
    add("IH03", "Modul ESP32-S3-WROOM-1 N16R8", ih03_s3_module(), "metal", "head", "J3", (0, -18, 0),
        note="tienenie 15.8×17.6, anténa hore (nad ňou žiadny kov)")
    add("IH04", "Servo náklonu hlavy (MG90S / SCS0009)", ih04_tilt_servo(), "servo", "head", "J3", (14, 0, 0),
        note="v hlave vedľa kapsy valca, telo hore, hriadeľ ∥ X na z 147 → pár 20z/20z (H11 → H09 na valci)")
    if camera:
        add("IH06", "Kamera OV2640 (voliteľná)", ih06_camera(), "black", "head", "J3", (0, -20, 12),
            note="NÁVRH: objektív Ø6 za čiernou hornou lištou H03 (z 185.6) - H03 potrebuje otvor Ø3 + vrecko")
    for side, sx in (("R", -1), ("L", 1)):
        add(f"IH07-{side}", f"DPS ucha {'pravá' if side == 'R' else 'ľavá'} (6× WS2812B-2020)", ear_pcb(sx),
            "pcb", "head", "J3", (sx * 16, 0, 0), note="Ø23×1.0, LED na r 10 pod svetlovodom H06")
    add("IH08", "MEMS mikrofón INMP441 (I2S)", ih08_mic(), "pcb", "head", "J3", (0, 0, 14),
        note="naležato na strope kapsy valca, spodný port cez penový krúžok VHB nad skrytou štrbinou x -10.5 – "
             "počuje cez otvorené ústie kapsy okolo krku; zvonka žiadny otvor, nie je v zornom poli žiadnej škáry")
    print(f"  head {time.time() - t0:.1f}s")

    # ---------------- neck ----------------
    add("IN01", "Servo otáčania hlavy (MG90S / SCS0009)", in01_pan_servo(), "servo", "neck", "J1", (0, 16, 0),
        note="zvislo v koľajniciach T07, hriadeľ (0, 20), prevod 1:1 ozubenými kolesami N04 → N03")
    add("IN02", "Ramienko pan serva (dvojramenné)", in02_pan_horn(), "white", "neck", "J1", (0, 16, 8),
        note="v drážke kolesa N04, skrutka ramienka M2")
    add("IN03", "Ložisko 6805-2RS (otáčanie hlavy)", in03_pan_bearing(), "metal", "neck", "J1", (0, 0, 16),
        note="25×37×7, z 96–103; vonkajší krúžok v T07, vnútorný nesie čap N02 – hlava nikdy nevisí na serve")
    print(f"  neck {time.time() - t0:.1f}s")

    # ---------------- torso (J1) ----------------
    add("IT01", "Servo otáčania trupu Feetech STS3215", it01_sts3215(), "servo", "torso", "J1", (0, 0, -6),
        note="45.2×24.7×35, drážkovanie DOLE na osi J1, telo z 45–80, zbernica 1 Mbit, 7.4 V priamo z 2S")
    add("IT02", "Ramienko STS3215 Ø20 (pevné na náboji základne)", it02_yaw_horn(), "metal", "torso", "",
        (0, 0, -16), note="hliník 25T, 4× M2 do náboja B15 na r 7; otáča sa telo serva okolo neho")
    add("IT03", "Axiálna skrutka M3×20 + podložka (spojka náboja)", it03_yaw_screw(), "metal", "torso", "",
        (0, 0, -34), note="zospodu cez servisný otvor (zátka B17), vežu B14 a náboj B15 do drážkovania serva")
    add("IT04", "Ložisko 6806-2RS (otáčanie trupu)", it04_yaw_bearing(), "metal", "torso", "J1", (0, 0, -24),
        note="30×42×7, z 32–39; nesie trup + hlavu, servo prenáša len krútiaci moment")
    for side, sx, j in (("R", -1, "J4"), ("L", 1, "J5")):
        nm = "pravé" if side == "R" else "ľavé"
        add(f"IT05-{side}", f"Servo ramena {nm} (MG90S / SCS0009)", it05_arm_servo(sx), "servo", "torso", "J1",
            (sx * 12, 0, 0), note="hriadeľ na osi ramena (y 0, z 89), telo dopredu, úchyty T01 / T07")
        add(f"IT06-{side}", f"Adaptér ramienka {'pravý' if side == 'R' else 'ľavý'} (skrátené dvojramenné)",
            it06_arm_horn(sx), "white", "arm_" + side, j, (sx * 20, 0, 0),
            note="13 mm, kľúč v drážke spojky A04, skrutka ramienka M2 axiálne")
    add("IT07", "Nosná DPS trupu (5 V MP1584 + budič zbernice 74LVC1G126 + konektory)", it07_controller(),
        "pcb", "torso", "J1", (0, 20, 0),
        note="48×18.5 zvislo v drážkach T08, servis cez zadné dvierka; motory a senzory základne riadi uzol IB09-2 "
             "na tej istej zbernici – ESP32-C3 využije 11 z 13 GPIO, cez J1 idú len 4 vodiče + reproduktor")
    add("IT08", "ESP32-C3 SuperMini", it08_supermini(), "pcb", "torso", "J1", (0, 26, 0),
        note="22.5×18 na lištách; USB-C na programovanie za dvierkami")
    add("IT09", "Hrudná DPS (5× WS2812B-2020 + VL53L0X + LTR-303)", it09_chest_pcb(), "pcb", "torso", "J1",
        (0, -22, 0), note="za dymovým pásom T05; svetelný pás v strede, senzory na krajoch, 2× M2 do T01")
    add("IT10", "Rámik hrudnej DPS so svetelnou clonou", it10_chest_frame(), "black", "torso", "J1",
        (0, -30, 0), note="čierne PETG medzi T05 a DPS: 3 okienka (LED / ToF / ALS), bez presvitu do senzora")
    print(f"  torso {time.time() - t0:.1f}s")

    # ---------------- base ("") ----------------
    for side, sx in (("R", -1), ("L", 1)):
        nm = "pravý" if side == "R" else "ľavý"
        m, e, sh = ib_motor(sx)
        add(f"IB01-{side}", f"Motor N20 {nm} (6 V, 1:150)", m, "metal", "base", "", (sx * 14, 0, 0),
            note="12×10, prevodovka 9 + motor 15, magnet enkodéra na zadnom hriadeli")
        add(f"IB02-{side}", f"Enkodér N20 {nm} (Hall, 7 PPR)", e, "pcb", "base", "", (sx * 6, 0, 0),
            note="DPS 12×11 + JST-SH 6-pin")
        add(f"IB03-{side}", f"Hriadeľ kolesa {nm} (D 3 mm)", sh, "metal", "base", "", (sx * 24, 0, 0),
            note="výstupný hriadeľ N20 3×10 s plôškou, v D-otvore disku B05")
    for k, sy in ((1, -1), (2, 1)):
        nm = "predný" if sy < 0 else "zadný"
        pp, mp = ib_contacts(sy)
        add(f"IB04-{k}P", f"Kontakt + batérie {nm}", pp, "metal", "base", "", (0, 0, 12),
            note="poniklovaná plôška v čele šachty B02, spájkovacie očko hore")
        add(f"IB04-{k}M", f"Kontakt − batérie s pružinou {nm}", mp, "metal", "base", "", (0, 0, 12),
            note="kužeľová pružina 4 závity, vymeniteľný článok zospodu cez poklop")
        add(f"IB05-{k}", f"Článok 18650 {nm}", ib_cell(sy), "battery", "base", "", (0, 0, -18),
            note="Li-ion 3.6 V, 2S zapojenie, kupovať lokálne (nie AliExpress)")
    add("IB06", "Reproduktor Ø28 (8 Ω, 2 W)", ib_speaker(), "black", "base", "", (0, -12, 0),
        note="zvislo, strieľa dopredu do uzavretej komôrky → mikroperforácia v dne pri prednom okraji")
    for k, (x, y) in enumerate(CLIFF, 1):
        add(f"IB07-{k}", f"Senzor pádu TCRT5000 #{k}", ib_cliff(x, y), "pcb", "base", "", (0, 0, 10),
            note="mini DPS 12×6.8, pozerá dole cez IR okienko B08")
    add("IB08", "LED prstenec podsvietenia 360° (24× WS2812B-2020)", ib_underglow(), "pcb", "base", "",
        (0, 0, -10), note="flex 0.3 mm na svetlovode B-UG, LED svietia dole do opálového PMMA")
    add("IB09-1", "DPS nabíjania 2S (IP2326 + ochrana, USB-C zospodu)", ib_board(-1), "black", "base", "",
        (0, 0, 10), note="čierna maska (leží pod zadnou škárou B01/B09); nesie vertikálnu USB-C B10, JST-PH batéria, "
                         "hlavný spínač P-MOSFET AO4407A")
    add("IB09-2", "DPS uzla základne + tlačidlo (STM32G030 + DRV8833 + 5 V)", ib_board(1), "black", "base", "",
        (0, 0, 10), note="čierna maska; uzol na zbernici serv (1 vodič): 2× N20 s enkodérmi A/B, 4 senzory pádu, "
                         "podsvietenie, lokálne zastavenie pri okraji stola; zospodu samoaretačné tlačidlo 6×6 pod B13 "
                         "(spína len hradlo MOSFETu na IB09-1)")
    for k, (x, y) in enumerate(DOCK_XY, 1):
        add(f"IB10-{k}", f"Pružinový kontakt doku #{k}", ib_pogo(float(x), float(y)), "metal", "base", "",
            (0, 0, 8), note="pogo pin z DPS na nit plôšky B12")
    print(f"  base {time.time() - t0:.1f}s")

    # ---------------- cables ----------------
    c1, c2, c3 = cable_neck()
    add("IW1-1", "Kábel krku – trup (6 vodičov)", c1, "black", "torso", "J1", (0, 0, 0),
        note="5 V + GND 2× 26 AWG (špičky ~2 A), TX, RX + pár reproduktora 4× 30 AWG; od nosnej DPS k osi hlavy")
    add("IW1-2", "Kábel krku – čap a valec", c2, "black", "neck", "J2", (0, 0, 0),
        note="stredom N03/N02 do valca N06, von štrbinou hore-vzadu")
    add("IW1-3", "Kábel krku – hlava", c3, "black", "head", "J3", (0, 0, 0),
        note="otvorom v strope kapsy k doske ESP32-S3")
    yb, yt = cable_yaw()
    add("IW2", "Valivá slučka kábla otáčania trupu (plochý pás 6 vodičov)", yb, "black", "base", "", (0, 0, 0),
        note=f"pás {YB_T}×{YB_H} na hranu: VBAT+GND 24 AWG, zbernica, reproduktor ±, GND 28 AWG; vonkajší beh na "
             f"pevnom okraji žľabu r {YB_RO:.1f}, oblúk R{YB_RB:.1f}, vnútorný beh na otočnom puzdre T04 r {YB_RI:.1f}; "
             f"dĺžka {yaw_loop_length():.0f} mm, ±150° bez zberacieho krúžku")
    add("IW3", "Kábel otáčania – trup", yt, "black", "torso", "J1", (0, 0, 0),
        note="koniec pásu → zväzok Ø4.2 cez drážku T04 → JST-GH 6p na nosnej DPS IT07")
    print(f"  cables {time.time() - t0:.1f}s")
    return P


# ============================================================================================
# checks
# ============================================================================================

def _overlap(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    if ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y or \
            ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z:
        return 0.0
    try:
        ab = a & b
    except Exception:  # noqa: BLE001
        return -1.0
    if ab is None:
        return 0.0
    try:
        return float(ab.volume)
    except Exception:  # noqa: BLE001
        return -1.0


def self_interference(parts, tol=0.05):
    bad = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            v = _overlap(parts[i].shape, parts[j].shape)
            if v > tol or v < 0:
                bad.append((parts[i].id, parts[j].id, round(v, 3)))
    return bad


def other_modules(names=("base", "torso", "head")):
    """build() of the other v8 shell modules (latest source)."""
    import importlib
    out = []
    for n in names:
        try:
            m = importlib.import_module(f"nova_v8.cad_{n}")
            t = time.time()
            ps = m.build()
            print(f"  loaded nova_v8.cad_{n}: {len(ps)} parts ({time.time() - t:.0f}s)")
            out += ps
        except Exception as ex:  # noqa: BLE001
            print(f"  [could not build nova_v8.cad_{n}] {ex!r}")
    return out


def clearance_report(parts, others, tol=0.05):
    """Overlaps of every internal component with the shell-module parts, in 3 classes:
       hits  = against a designed / visible shell part (real interference - must be empty),
       dups  = against the shell's own envelope of the SAME component (SUPERSEDES - expected),
       env   = against a shell envelope of ANOTHER bought component (disappears when the superseded envelopes are
               excluded; reported for information)."""
    hits, dups, env = [], [], []
    sup = set(SUPERSEDED)
    intended = {("IH04", "H11"): "press fit: Ø4.8 MG90S spline in the Ø4.4 bore of the H11 gear (cad_head design)"}
    for p in parts:
        for o in others:
            v = _overlap(p.shape, o.shape)
            if v > tol or v < 0:
                rec = (p.id, o.id, round(v, 2))
                if (p.id, o.id) in intended:
                    dups.append(rec + (intended[(p.id, o.id)],))
                elif o.id in SUPERSEDES.get(p.id, []):
                    dups.append(rec)
                elif o.id in sup:
                    env.append(rec)
                else:
                    hits.append(rec)
    return hits, dups, env


def step_roundtrip(parts):
    from build123d import import_step
    bad = []
    for p in parts:
        fn = os.path.join(OUT_DIR, "step", p.id + ".step")
        try:
            s = import_step(fn)
            v = s.volume
            if not s.is_valid or abs(v - p.shape.volume) > 1e-3 * max(1.0, p.shape.volume):
                bad.append((p.id, round(v, 2), round(p.shape.volume, 2), s.is_valid))
        except Exception as ex:  # noqa: BLE001
            bad.append((p.id, repr(ex)))
    return bad


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    if "--out" in sys.argv:                      # preview export somewhere else (keeps build_v8 untouched)
        OUT_DIR = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
    recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
    for r in recs:
        print(f"  {r['id']:7s} {r['mat']:8s} {r['sub']:6s} {r['joint']:3s} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("DEVIATIONS:")
    for d in DEVIATIONS:
        print("  -", d)
    print("J1 rolling loop (band %.1f x %.1f, r_o %.2f, r_i %.2f, bend R%.2f, length %.1f mm):"
          % (YB_T, YB_H, YB_RO, YB_RI, YB_RB, yaw_loop_length()))
    for j in (-150, -75, 0, 75, 150):
        o_, i_, u_ = yaw_loop(j)
        print(f"   J1 {j:+5d}: outer run {o_:6.1f} deg, inner run {i_:6.1f} deg, U-turn at {u_ % 360:6.1f} deg")
    print("self interference:", self_interference(ps))
    if "--check" in sys.argv:
        print("STEP round trip problems:", step_roundtrip(ps))
        oth = other_modules()
        hits, dups, env = clearance_report(ps, oth)
        print("CLEARANCE HITS (internal component vs designed / visible shell part):")
        for h in hits:
            print("   ", h)
        print("vs superseded shell envelopes of OTHER components:", env)
        print("DUPLICATES (same component, shell envelope superseded):", dups)
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
