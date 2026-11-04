"""
NOVA mini (v8) – CONCEPT model of the shared MINI BODY (everything except the head).
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.body
Exports STL + manifest "body_v8" into build_v8/ (never into build/, which holds the finished v7.3).

All shared numbers come from nova_v8/concept.py (not edited here).  Concept quality: clean outer surfaces,
correct proportions and materials, no internal details.  Local styling constants are marked below.

  base_v8   B01 white top cover (130 x 108 x 38 envelope, plan R26, top R8) with 2 wheel arches,
            B02 black bottom tray whose side wall is the 0.8 mm proud bumper/skirt band (z 4..11.5) and whose
                two tubs line the wheel wells (the arches read dark), B03 cyan light guide 40 x 3.5 at z 20,
            B04-R/L rubber tyres Ø36 x 10 + B05-R/L black hubs (5 spokes) on the axle x = ±52, y = 4, z = 18,
            B06 two ball-caster cups + B07 two Ø12 steel balls, B08 four cliff-sensor windows (underside),
            B09 black turntable ring Ø77 sunk 1 mm into the top, rotates with the torso (J1).
  torso_v8  superellipse 88 x 72 n 2.7, z 39..104, R16 top / R8 bottom; T01 centre band |x| <= 26.7 (front ->
            top -> back), T02-R/L side shells |x| >= 27.3, 0.6 seams closed 1.6 mm below the skin by the
            black T03 seam backing; T05 cyan LED 28 x 3.5 at z 84; T06 frosted sensor window 18 x 3.5 at z 74.
  neck_v8   N01 black collar 42 x 34 (z 104..109, J1), N02 flared cone r13 -> r10 (z 109..116, J2),
            N06 tilt barrel Ø30 on the tilt axis y 0 / z 126 (|x| <= 11.2, two 0.6 grooves, J2),
            N07-R/L domed end caps Ø29 (|x| 11.8..15, tilt with the head, J3) -> barrel envelope Ø30 x 30.
  arm_R/L   A01 white egg paddle (top 98 / widest 70 / bottom 47, half_w 13, half_t 7, splay 8°),
            A03 black (rubber) inner-front tip, A04 black joint cover Ø18 (rotates, J4/J5),
            A05 black socket ring Ø22 sunk in the torso side (fixed, J1).
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Cylinder, Edge, Face, Plane, Pos, Rot, Solid, Sphere, Vector, Wire,
                       extrude, fillet, mirror, offset, revolve, scale)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts, superellipse_wire  # noqa: E402
from nova_v8 import concept as C  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "body_v8"

BS, TS, NK, AR = C.BASE, C.TORSO, C.NECK, C.ARM

# ---- base ----------------------------------------------------------------------------------------
BW, BD, BR = BS["w"], BS["d"], BS["plan_r"]
B_TOP = BS["z1"]                       # 38
B_UNDER = BS["ground_clear"]           # 4  underside of the bottom tray
WH = BS["wheel"]                       # d 36, w 10, x 52, y 4
WR = WH["d"] / 2
WZ = WR                                # axle height: tyre touches z = 0
CAST = BS["caster"]
LEDB = BS["led"]

# local styling constants (concept)
SKIRT_TOP = 11.5        # top of the black skirt band (bottom tray side wall)
SKIRT_PROUD = 0.8       # skirt stands 0.8 proud of the white cover (bumper, protects the desk edge)
SKIRT_R_BOT, SKIRT_R_TOP = 2.5, 1.5
COVER_R_BOT = 1.0       # white cover bottom edge -> V shadow line against the skirt
ARCH_HW = 22.0          # wheel arch: half width (Y) around the axle y
ARCH_TOP = 29.5         # arch top stays below the R8 top rounding (z 30)
ARCH_R = 13.0           # arch corner radius
ARCH_EDGE_R = 1.2       # rounding of the arch edges on the white cover
WELL_X0 = 44.3          # inner face of the wheel-well tub (black), void starts at +1.2
WELL_T = 1.2
WELL_TOP = 36.8         # wheel well ceiling (tyre top 36.0)
TT_D, TT_RECESS, TT_PROUD = 77.0, 1.0, 0.7    # turntable ring Ø, recess depth in the cover, height above the top
CUP_D, CUP_Z0, CUP_Z1 = 16.0, 2.8, 14.0       # ball-caster cups (protrude 1.2 below the underside)
CLIFF_WIN = (7.0, 4.0, 1.6)                   # cliff-sensor window w x d x r (underside, recessed 0.4)
REAR = dict(usb_x=-24.0, btn_x=-36.0, z=22.0)  # USB-C (charging) + power button on the base back

# ---- torso ---------------------------------------------------------------------------------------
TA, TB, TN = TS["w"] / 2, TS["d"] / 2, TS["n"]
T_Z0, T_Z1 = TS["z0"], TS["z1"]
T_RT, T_RB = TS["r_top"], TS["r_bottom"]
BAND_HW = 27.0          # centre band |x| <= 27 (seam centre)
SEAM = 0.6
SEAM_DEPTH = 1.6        # black backing sits this deep below the skin
SENSOR = dict(w=18.0, h=3.5, z=74.0, recess=0.5)
SH_Z = TS["shoulder_z"]

# ---- neck ----------------------------------------------------------------------------------------
CO, CN = NK["collar"], NK["cone"]
TLY, TLZ = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]
BAR_R, BAR_L = NK["barrel_d"] / 2, NK["barrel_len"]
COLLAR_TAPER = 22.0     # draft of the collar sides (deg)
CAP_GAP = 0.6
CAP_LEN = 3.2
CAP_D = 29.0
BAR_CORE = BAR_L / 2 - CAP_LEN - CAP_GAP     # 11.2

# ---- arms ----------------------------------------------------------------------------------------
EGG = AR["egg"]
AX_Z = AR["axis"]["z"]
AX_Y = AR["axis"]["y"]
MID = AR["mid_x"]
SPLAY = AR["abduction_deg"]
ZC = EGG["widest_z"] - AX_Z            # local z of the widest section (-18)
C_TOP = EGG["top_z"] - EGG["widest_z"]  # 28
C_BOT = EGG["widest_z"] - EGG["bottom_z"]  # 23
HW_, HT_ = EGG["half_w"], EGG["half_t"]
RING_D, RING_X0 = 22.0, 38.5            # A05 socket ring (sunk into the torso side from |x| 38.5)
RING_X1 = TA + 0.7                      # 0.7 proud of the torso side at the equator
COVER_D = 18.0                          # A04 joint cover
COVER_X0 = RING_X1 + 0.3
COVER_X1 = MID - 2.0                    # ends inside the paddle
TIP_ZTOP = 58.0                         # A03 patch reaches this z on the front silhouette at the mid plane
TIP_YB = 1.5                            # ... and this local y under the bottom
TIP_TILT = 45.0                         # tilted toward the inner face (broad crescent inside, sliver outside)
PANEL_INSET, PANEL_GROOVE, PANEL_GROOVE_D = 3.0, 0.45, 0.4   # outer lens-panel shadow groove

BIG = 400.0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def bx(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, r, z0, z1):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_x(y, z, r, x0, x1):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_y(x, z, r, y0, y1):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def rr_face(w, d, r, z, cx=0.0, cy=0.0):
    """Rounded rectangle face in a horizontal plane (straight lines + quarter arcs)."""
    hw, hd = w / 2, d / 2
    pts = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = cx + sx * (hw - r), cy + sy * (hd - r)
        pts.append((ccx, ccy, a0))
    edges = []
    corners = []
    for ccx, ccy, a0 in pts:
        a1 = a0 + 90
        p0 = Vector(ccx + r * math.cos(math.radians(a0)), ccy + r * math.sin(math.radians(a0)), z)
        pm = Vector(ccx + r * math.cos(math.radians(a0 + 45)), ccy + r * math.sin(math.radians(a0 + 45)), z)
        p1 = Vector(ccx + r * math.cos(math.radians(a1)), ccy + r * math.sin(math.radians(a1)), z)
        corners.append((p0, pm, p1))
    for i, (p0, pm, p1) in enumerate(corners):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        q0 = corners[(i + 1) % 4][0]
        edges.append(Edge.make_line(p1, q0))
    return Face(Wire(edges))


def rr_prism(w, d, r, z0, z1, cx=0.0, cy=0.0):
    return extrude(rr_face(w, d, r, z0, cx, cy), z1 - z0, dir=(0, 0, 1))


def stadium_y(xc, zc, w, h, y0, y1):
    """Stadium (rounded slot, axis // X) prism along Y."""
    r = h / 2
    s = bx(xc - (w / 2 - r), xc + (w / 2 - r), y0, y1, zc - r, zc + r)
    s = s + cyl_y(xc - (w / 2 - r), zc, r, y0, y1) + cyl_y(xc + (w / 2 - r), zc, r, y0, y1)
    return s.clean()


def check(name, s, vol_min=1.0):
    assert s is not None, name
    if hasattr(s, "solids"):
        sol = s.solids()
        assert len(sol) >= 1, f"{name}: no solids"
        for so in sol:
            assert so.is_valid, f"{name}: invalid solid"
    assert s.volume > vol_min, f"{name}: volume {s.volume}"
    return s


def try_fillet(shape, edges, r, name=""):
    try:
        f = shape.fillet(r, edges)
        if f.is_valid and abs(f.volume - shape.volume) < 0.05 * shape.volume:
            return f
    except Exception as e:  # noqa: BLE001
        print(f"   [fillet skipped] {name}: {e}")
    return shape


# ---------------------------------------------------------------------------
# BASE
# ---------------------------------------------------------------------------

def cover_body():
    b = rr_prism(BW, BD, BR, SKIRT_TOP, B_TOP)
    b = fillet(b.edges().group_by(Axis.Z)[-1], BS["top_fillet"])
    b = fillet(b.edges().group_by(Axis.Z)[0], COVER_R_BOT)
    return b


def skirt_plate():
    p = SKIRT_PROUD
    s = rr_prism(BW + 2 * p, BD + 2 * p, BR + p, B_UNDER, SKIRT_TOP)
    s = fillet(s.edges().group_by(Axis.Z)[0], SKIRT_R_BOT)
    s = fillet(s.edges().group_by(Axis.Z)[-1], SKIRT_R_TOP)
    return s


def arch_prism(sx):
    """Inverted-U wheel arch through the side wall (x from 58 outward), open at the bottom."""
    yc = WH["y"]
    zb = -10.0
    # rounded rectangle in the YZ plane: half width ARCH_HW, from zb to ARCH_TOP, corners ARCH_R
    hw = ARCH_HW
    corners = [(yc + hw - ARCH_R, ARCH_TOP - ARCH_R, 0), (yc - hw + ARCH_R, ARCH_TOP - ARCH_R, 90),
               (yc - hw + ARCH_R, zb + ARCH_R, 180), (yc + hw - ARCH_R, zb + ARCH_R, 270)]
    x = 0.0
    arcs = []
    for cy, cz, a0 in corners:
        a = [math.radians(a0 + d) for d in (0, 45, 90)]
        arcs.append([Vector(x, cy + ARCH_R * math.cos(t), cz + ARCH_R * math.sin(t)) for t in a])
    edges = []
    for i, (p0, pm, p1) in enumerate(arcs):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        edges.append(Edge.make_line(p1, arcs[(i + 1) % 4][0]))
    f = Face(Wire(edges))
    x0, x1 = 58.0, 72.0
    pr = extrude(f, x1 - x0, dir=(1, 0, 0))
    pr = Pos(x0, 0, 0) * pr
    if sx < 0:
        pr = mirror(pr, Plane.YZ)
    return pr


def well_void(sx):
    yc = WH["y"]
    v = bx(sx * (WELL_X0 + WELL_T), sx * 58.6, yc - (ARCH_HW - 1.0), yc + (ARCH_HW - 1.0), -10, WELL_TOP)
    return v + arch_prism(sx)


def well_tub(sx):
    yc = WH["y"]
    return bx(sx * WELL_X0, sx * 59.0, yc - (ARCH_HW - 1.0) - WELL_T, yc + (ARCH_HW - 1.0) + WELL_T,
              B_UNDER, WELL_TOP + 0.5)


def caster_hole(y):
    return cyl_z(0, y, CUP_D / 2 + 0.2, -1, CUP_Z1 + 0.5)


def cliff_window_prism(x, y, z0, z1, grow=0.0):
    w, d, r = CLIFF_WIN
    return rr_prism(w + 2 * grow, d + 2 * grow, r + grow, z0, z1, cx=x, cy=y)


def _arch_edges(c):
    """Outer arch edges of the white cover (in the side planes |x| = BW/2, above the bottom rounding)."""
    out = []
    for e in c.edges():
        bb = e.bounding_box()
        if abs(abs(bb.min.X) - BW / 2) < 0.05 and abs(abs(bb.max.X) - BW / 2) < 0.05 and \
                bb.max.Z <= ARCH_TOP + 0.01 and bb.min.Z >= SKIRT_TOP + COVER_R_BOT - 0.1 and \
                abs(bb.center().Y - WH["y"]) < ARCH_HW + 0.05:
            out.append(e)
    return out


def rear_port_cut():
    """USB-C + power button openings on the base back (y = +BD/2)."""
    y1 = BD / 2
    c = stadium_y(REAR["usb_x"], REAR["z"], 9.4, 3.8, y1 - 6, y1 + 5)
    c = c + cyl_y(REAR["btn_x"], REAR["z"], 3.2, y1 - 6, y1 + 5)
    return c


def rear_ports():
    y1 = BD / 2
    usb = stadium_y(REAR["usb_x"], REAR["z"], 9.2, 3.6, y1 - 6, y1 - 0.6)
    usb = usb - stadium_y(REAR["usb_x"], REAR["z"], 8.4, 2.6, y1 - 3.0, y1)
    btn = cyl_y(REAR["btn_x"], REAR["z"], 3.0, y1 - 6, y1 - 0.3)
    btn = fillet(btn.faces().sort_by(Axis.Y)[-1].edges(), 0.6)
    return usb + btn


def base_parts():
    cover = cover_body()
    tray = skirt_plate()
    # arches first, round their outer edges, THEN open the wells (the fillet fails after the tub cut)
    for sx in (1, -1):
        cover = cover - arch_prism(sx)
    cover = try_fillet(cover, _arch_edges(cover), ARCH_EDGE_R, "arch edges")
    for sx in (1, -1):
        tub = well_tub(sx)
        cover = cover - tub
        tray = (tray + tub) - well_void(sx)
    for y in CAST["y"]:
        cover = cover - caster_hole(y)
        tray = tray - caster_hole(y)
    # turntable recess in the flat top
    cover = cover - cyl_z(0, 0, TT_D / 2 + 0.5, B_TOP - TT_RECESS, B_TOP + 1)
    # front light guide pocket, rear connector openings
    led_cut = stadium_y(0, LEDB["z"], LEDB["w"], LEDB["h"], -BD / 2 - 5, -BD / 2 + 3.5)
    cover = cover - led_cut - rear_port_cut()
    # cliff-sensor pockets (underside of the tray)
    for (x, y) in BS["cliff_sensors"]:
        tray = tray - cliff_window_prism(x, y, B_UNDER - 1, B_UNDER + 1.4, grow=0.1)

    led = stadium_y(0, LEDB["z"], LEDB["w"] - 0.2, LEDB["h"] - 0.2, -BD / 2 + 0.1, -BD / 2 + 3.5)

    # wheels
    tyres, hubs = {}, {}
    for sx, side in ((-1, "R"), (1, "L")):
        xc = sx * WH["x"]
        t = cyl_x(WH["y"], WZ, WR, xc - WH["w"] / 2, xc + WH["w"] / 2)
        t = fillet(t.edges(), 3.0)
        t = t - cyl_x(WH["y"], WZ, 13.0, xc - 10, xc + 10)
        tyres[side] = t
        hub_w = WH["w"] - 2.0
        h = cyl_x(WH["y"], WZ, 13.0, xc - hub_w / 2, xc + hub_w / 2)
        xo = xc + sx * hub_w / 2                     # outer face
        dish = cyl_x(WH["y"], WZ, 10.8, xo - sx * 1.6, xo + sx * 1.0) - cyl_x(WH["y"], WZ, 4.6, xo - 3, xo + 3)
        spokes = None
        for k in range(5):
            a = math.radians(90 + 72 * k)
            sp = Pos(xo, WH["y"], WZ) * Rot(math.degrees(a), 0, 0) * Pos(0, 0, 7.6) * Box(4.0, 2.4, 7.0)
            spokes = sp if spokes is None else spokes + sp
        spokes = spokes & cyl_x(WH["y"], WZ, 11.2, xo - sx * 1.6, xo)
        h = h - (dish - spokes)
        h = h - cyl_x(WH["y"], WZ, 1.6, xo - sx * 0.6, xo + sx * 1)    # axle screw dimple
        hubs[side] = h

    # ball casters: cup (black) + steel ball
    cups, balls = None, None
    for y in CAST["y"]:
        r = CAST["d"] / 2
        cup = cyl_z(0, y, CUP_D / 2, CUP_Z0, CUP_Z1)
        cup = fillet(cup.edges().group_by(Axis.Z)[0], 1.0)
        cup = cup - Pos(0, y, r) * Sphere(r + 0.2)
        ball = Pos(0, y, r) * Sphere(r)
        cups = cup if cups is None else cups + cup
        balls = ball if balls is None else balls + ball

    wins = None
    for (x, y) in BS["cliff_sensors"]:
        wdw = cliff_window_prism(x, y, B_UNDER + 0.4, B_UNDER + 1.4)
        wins = wdw if wins is None else wins + wdw

    ring = cyl_z(0, 0, TT_D / 2, B_TOP - TT_RECESS, B_TOP + TT_PROUD)
    ring = fillet(ring.edges().group_by(Axis.Z)[-1], 0.5)

    parts = [
        PartRec("B01", "Horný kryt základne", check("B01", cover), "white", "base_v8", "", (0, 0, 30),
                note="biely kryt 130×108×38, R26 v pôdoryse, R8 hore, podbehy kolies"),
        PartRec("B02", "Spodná vaňa s nárazníkom", check("B02", tray), "black", "base_v8", "", (0, 0, -20),
                note="čierny pás 0.8 mm nad bokom (chráni hranu stola), vane podbehov kolies"),
        PartRec("B03", "Svetlovod základne", check("B03", led), "cyan_led", "base_v8", "", (0, -25, 0),
                note="40×3.5 mm, z 20"),
        PartRec("B04-R", "Pneumatika pravá", check("B04-R", tyres["R"]), "rubber", "base_v8", "", (-30, 0, 0),
                note="Ø36×10 TPU, motor N20"),
        PartRec("B04-L", "Pneumatika ľavá", check("B04-L", tyres["L"]), "rubber", "base_v8", "", (30, 0, 0),
                note="Ø36×10 TPU, motor N20"),
        PartRec("B05-R", "Disk kolesa pravý", check("B05-R", hubs["R"]), "black_gloss", "base_v8", "", (-40, 0, 0)),
        PartRec("B05-L", "Disk kolesa ľavý", check("B05-L", hubs["L"]), "black_gloss", "base_v8", "", (40, 0, 0)),
        PartRec("B06", "Puzdrá guľových koliesok", check("B06", cups), "black", "base_v8", "", (0, 0, -30)),
        PartRec("B07", "Guľky Ø12", check("B07", balls), "metal", "base_v8", "", (0, 0, -40)),
        PartRec("B08", "Okienka senzorov pádu (4×)", check("B08", wins), "glass", "base_v8", "", (0, 0, -30),
                note="IR/ToF dole, v rohoch"),
        PartRec("B10", "USB-C a vypínač (zadná strana)", check("B10", rear_ports()), "black", "base_v8", "",
                (0, 25, 0), note="nabíjanie USB-C, tlačidlo napájania"),
        PartRec("B09", "Otočný prstenec trupu", check("B09", ring), "black", "base_v8", "J1", (0, 0, 15),
                note="Ø77, zapustený 1 mm, točí sa s trupom (STS3215 + 6806)"),
    ]
    return parts


# ---------------------------------------------------------------------------
# TORSO
# ---------------------------------------------------------------------------

def torso_body():
    w = superellipse_wire(TA, TB, TN, T_Z0, count=96)
    s = extrude(Face(w), T_Z1 - T_Z0, dir=(0, 0, 1))
    s = fillet(s.edges().group_by(Axis.Z)[-1], T_RT)
    s = fillet(s.edges().group_by(Axis.Z)[0], T_RB)
    assert s.is_valid
    return s


def torso_parts():
    body = torso_body()
    hs = SEAM / 2
    band = body & bx(-(BAND_HW - hs), BAND_HW - hs, -BIG, BIG, -BIG, BIG)
    side_r = body & bx(-BIG, -(BAND_HW + hs), -BIG, BIG, -BIG, BIG)
    side_l = body & bx(BAND_HW + hs, BIG, -BIG, BIG, -BIG, BIG)
    # 0.3 edge break on both sides of the visible seams (falls back to sharp edges if OCC refuses)
    def seam_edges(shp, xs):
        return [e for e in shp.edges() if abs(e.bounding_box().min.X - xs) < 0.02 and
                abs(e.bounding_box().max.X - xs) < 0.02]
    band = try_fillet(band, seam_edges(band, BAND_HW - hs) + seam_edges(band, -(BAND_HW - hs)), 0.3, "band seam")
    side_r = try_fillet(side_r, seam_edges(side_r, -(BAND_HW + hs)), 0.3, "side R seam")
    side_l = try_fillet(side_l, seam_edges(side_l, BAND_HW + hs), 0.3, "side L seam")
    core = offset(body, amount=-SEAM_DEPTH)
    assert core.is_valid and core.volume < body.volume - 1000
    backing = core & (bx(BAND_HW - hs, BAND_HW + hs, -BIG, BIG, -BIG, BIG) +
                      bx(-(BAND_HW + hs), -(BAND_HW - hs), -BIG, BIG, -BIG, BIG))

    led = TS["led"]
    led_cut = stadium_y(0, led["z"], led["w"], led["h"], -TB - 6, -TB + 4.5)
    band = band - led_cut
    led_part = stadium_y(0, led["z"], led["w"] - 0.2, led["h"] - 0.2, -TB - 6, -TB + 4.5) & offset(body, amount=-0.05)

    sen_cut = stadium_y(0, SENSOR["z"], SENSOR["w"], SENSOR["h"], -TB - 6, -TB + 4.0)
    band = band - sen_cut
    sen_part = stadium_y(0, SENSOR["z"], SENSOR["w"] - 0.2, SENSOR["h"] - 0.2, -TB - 6, -TB + 4.0) & \
        offset(body, amount=-SENSOR["recess"])

    # shoulder sockets: pockets for the A05 rings
    side_r = side_r - cyl_x(AX_Y, SH_Z, RING_D / 2 + 0.2, -RING_X0, -60)
    side_l = side_l - cyl_x(AX_Y, SH_Z, RING_D / 2 + 0.2, RING_X0, 60)

    return [
        PartRec("T01", "Stredový pás trupu", check("T01", band), "white", "torso_v8", "J1", (0, -20, 10),
                note="|x| ≤ 26.7: predok → vrch → chrbát"),
        PartRec("T02-R", "Bočný kryt trupu pravý", check("T02-R", side_r), "white", "torso_v8", "J1", (-25, 0, 0)),
        PartRec("T02-L", "Bočný kryt trupu ľavý", check("T02-L", side_l), "white", "torso_v8", "J1", (25, 0, 0)),
        PartRec("T03", "Tmavá výplň škár", check("T03", backing), "black", "torso_v8", "J1", (0, 0, 0),
                note="0.6 mm škáry sú 1.6 mm pod povrchom uzavreté čiernou"),
        PartRec("T05", "Svetlovod trupu", check("T05", led_part), "cyan_led", "torso_v8", "J1", (0, -30, 0),
                note="28×3.5 mm, z 84"),
        PartRec("T06", "Okienko senzora", check("T06", sen_part), "frost", "torso_v8", "J1", (0, -30, 0),
                note="ToF / svetlo, 18×3.5 mm, z 74, zapustené 0.5"),
    ]


# ---------------------------------------------------------------------------
# NECK
# ---------------------------------------------------------------------------

def neck_parts():
    # N01 collar: superellipse 42 x 34 echoing the torso, soft top edge
    w = superellipse_wire(CO["w"] / 2, CO["d"] / 2, 2.7, CO["z0"], count=64)
    try:   # flared like the v7.3 flange: sides drafted 22°, soft top edge
        k = (CO["z1"] - CO["z0"]) * math.tan(math.radians(COLLAR_TAPER))
        w1 = superellipse_wire(CO["w"] / 2 - k, CO["d"] / 2 - k, 2.7, CO["z1"], count=64)
        collar = Solid.make_loft([w, w1], ruled=True)
        collar = fillet(collar.edges().group_by(Axis.Z)[-1], 1.4)
        assert collar.is_valid
    except Exception as ex:  # noqa: BLE001
        print("   [collar taper skipped]", ex)
        collar = extrude(Face(w), CO["z1"] - CO["z0"], dir=(0, 0, 1))
        collar = fillet(collar.edges().group_by(Axis.Z)[-1], 2.2)

    # N02 flared cone (concave trumpet), saddle-trimmed by the barrel
    z0, z1, rb, rt = CN["z0"], CN["z1"], CN["r_bottom"], CN["r_top"]
    pts = []
    n = 14
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        r = rt + (rb - rt) * ((z1 - z) / (z1 - z0)) ** 2
        pts.append(Vector(r, 0, z))
    edges = [Edge.make_line(Vector(0, 0, z0), pts[0]), Edge.make_spline(pts),
             Edge.make_line(pts[-1], Vector(0, 0, z1)), Edge.make_line(Vector(0, 0, z1), Vector(0, 0, z0))]
    cone = revolve(Face(Wire(edges)), Axis.Z, 360)
    cone = cone - cyl_x(TLY, TLZ, BAR_R, -BAR_CORE - 1, BAR_CORE + 1)

    # N06 barrel core + 2 grooves
    bar = cyl_x(TLY, TLZ, BAR_R, -BAR_CORE, BAR_CORE)
    bar = fillet(bar.edges(), 0.8)
    for sx in (1, -1):
        g0 = sx * (BAR_CORE - 3.0)
        bar = bar - (cyl_x(TLY, TLZ, BAR_R + 1, g0 - 0.3, g0 + 0.3) - cyl_x(TLY, TLZ, BAR_R - 0.5, g0 - 1, g0 + 1))

    caps = {}
    for sx, side in ((-1, "R"), (1, "L")):
        xa, xb = sx * (BAR_CORE + CAP_GAP), sx * (BAR_L / 2)
        cap = cyl_x(TLY, TLZ, CAP_D / 2, xa, xb)
        outer = cap.faces().sort_by(Axis.X)[-1 if sx > 0 else 0]
        cap = try_fillet(cap, outer.edges(), 1.6, "cap dome")
        caps[side] = cap

    return [
        PartRec("N01", "Golier krku", check("N01", collar), "black", "neck_v8", "J1", (0, 0, 8),
                note="42×34, pevný na trupe"),
        PartRec("N02", "Kužeľ krku", check("N02", cone), "black", "neck_v8", "J2", (0, 0, 16),
                note="otáča sa s hlavou (pan servo v trupe)"),
        PartRec("N06", "Valec náklonu", check("N06", bar), "black", "neck_v8", "J2", (0, 0, 24),
                note="Ø30 na osi náklonu y 0 / z 126, servo náklonu vnútri"),
        PartRec("N07-R", "Krytka valca pravá", check("N07-R", caps["R"]), "black", "neck_v8", "J3", (-12, 0, 24)),
        PartRec("N07-L", "Krytka valca ľavá", check("N07-L", caps["L"]), "black", "neck_v8", "J3", (12, 0, 24)),
    ]


# ---------------------------------------------------------------------------
# ARMS
# ---------------------------------------------------------------------------

def egg_local(d: float = 0.0):
    """Egg (local frame: origin = joint point, +x outward), widest section at local z = ZC.
    d > 0: every semi-axis reduced by d (approximate inward offset, used for the shallow panel groove)."""
    sph = Sphere(1.0)
    top = scale(sph & Pos(0, 0, 1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_TOP - d))
    bot = scale(sph & Pos(0, 0, -1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_BOT - d))
    egg = top.fuse(bot).clean()
    return Pos(0, 0, ZC) * egg


def silhouette_prism(inset: float, x0: float, x1: float, n: int = 120):
    """Prism along local +x of the egg side silhouette (YZ) offset inward by `inset`."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c = C_TOP if math.cos(t) >= 0 else C_BOT
        y, z = HW_ * math.sin(t), c * math.cos(t)
        ny, nz = c * math.sin(t), HW_ * math.cos(t)          # outward normal of the ellipse
        L = math.hypot(ny, nz)
        pts.append(Vector(x0, y - inset * ny / L, ZC + z - inset * nz / L))
    f = Face(Wire([Edge.make_spline(pts, periodic=True)]))
    return extrude(f, x1 - x0, dir=(1, 0, 0))


def panel_groove():
    """0.45 mm shadow-gap groove (0.4 deep) outlining a lens panel on the OUTER face (v7.3 / R01 detail)."""
    ring = silhouette_prism(PANEL_INSET, 0.8, 12.0) - silhouette_prism(PANEL_INSET + PANEL_GROOVE, 0.0, 13.0)
    return ring & (egg_local() - egg_local(PANEL_GROOVE_D))


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
    n = m * math.cos(t) + Vector(-1, 0, 0) * math.sin(t)
    return A, n.normalized()


def halfspace(p: Vector, n: Vector, size=200.0):
    """Solid half-space {q : n.(q - p) >= 0} (big box)."""
    pl = Plane(origin=p, z_dir=n)
    return pl.location * Pos(0, 0, size / 2) * Box(size, size, size)


def arm_parts():
    egg = egg_local()
    A, n = tip_plane()
    hsp = halfspace(A, n)
    tip = egg & hsp
    paddle = egg - hsp
    try:
        g = panel_groove()
        p2 = paddle - g
        if p2.is_valid and len(p2.solids()) == 1:
            paddle = p2
            t2 = tip - g
            if t2.is_valid and t2.solids():
                tip = t2
    except Exception as ex:  # noqa: BLE001
        print("   [panel groove skipped]", ex)
    loc = Pos(MID, AX_Y, AX_Z) * Rot(0, -SPLAY, 0)
    tip_w, paddle_w = loc * tip, loc * paddle

    cover = cyl_x(AX_Y, AX_Z, COVER_D / 2, COVER_X0, COVER_X1)
    cover = try_fillet(cover, cover.faces().sort_by(Axis.X)[0].edges(), 1.0, "cover edge")
    paddle_w = paddle_w - cyl_x(AX_Y, AX_Z, COVER_D / 2 + 0.2, COVER_X0 - 1, COVER_X1 + 0.2)
    tip_w = tip_w - cyl_x(AX_Y, AX_Z, COVER_D / 2 + 0.2, COVER_X0 - 1, COVER_X1 + 0.2)

    ring = cyl_x(AX_Y, SH_Z, RING_D / 2, RING_X0, RING_X1)
    ring = try_fillet(ring, ring.faces().sort_by(Axis.X)[-1].edges(), 0.6, "ring edge")

    parts = []
    for side, sx in (("R", -1), ("L", 1)):
        j = "J4" if side == "R" else "J5"
        sub = "arm_" + side
        if sx > 0:
            p, t, c, r = paddle_w, tip_w, cover, ring
        else:
            p, t, c, r = (mirror(s, Plane.YZ) for s in (paddle_w, tip_w, cover, ring))
        e = sx
        parts += [
            PartRec(f"A01-{side}", f"Lopatka ruky {'pravá' if side == 'R' else 'ľavá'}", check("A01", p), "white",
                    sub, j, (e * 30, 0, 0), note="vajce: hore 98, max 70, dole 47, odklon 8°"),
            PartRec(f"A03-{side}", "Špička ruky", check("A03", t), "rubber", sub, j, (e * 30, 0, -15),
                    note="čierna mäkká špička – vnútorná predná strana"),
            PartRec(f"A04-{side}", "Kryt kĺbu ramena", check("A04", c), "black", sub, j, (e * 18, 0, 0),
                    note="Ø18, otáča sa s ramenom (servo v trupe)"),
            PartRec(f"A05-{side}", "Krúžok ramena", check("A05", r), "black", sub, "J1", (e * 8, 0, 0),
                    note="Ø22, pevný v trupe"),
        ]
    return parts


# ---------------------------------------------------------------------------

def build():
    parts = []
    for fn in (base_parts, torso_parts, neck_parts, arm_parts):
        t = time.time()
        ps = fn()
        print(f"  {fn.__name__}: {len(ps)} parts in {time.time() - t:.1f}s")
        parts += ps
    return parts


def interference(parts, tol=0.5):
    """Pairwise overlap volumes (mm^3) between parts that could touch."""
    bad = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i].shape, parts[j].shape
            ba, bb = a.bounding_box(), b.bounding_box()
            if ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y or \
                    ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z:
                continue
            try:
                ab = a & b
                v = 0.0 if ab is None else ab.volume
            except Exception:  # noqa: BLE001
                v = -1
            if v > tol or v < 0:
                bad.append((parts[i].id, parts[j].id, round(v, 2)))
    return bad


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    recs = export_parts(ps, MANIFEST, step=False, out_dir=OUT_DIR)
    for r in recs:
        print(f"  {r['id']:7s} {r['mat']:11s} {r['sub']:9s} {r['joint']:3s} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    if "--check" in sys.argv:
        print("interference:", interference(ps))
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
