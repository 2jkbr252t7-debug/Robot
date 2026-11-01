"""
NOVA mini v8.0 - BASE (drive module).  Run from the repo root:

    /opt/venv/cad/bin/python -m nova_v8.cad_base            # build + export (build_v8/, manifest "base")
    /opt/venv/cad/bin/python -m nova_v8.cad_base --check    # + interference report (own parts + other v8 modules)

Numbers: nova_v8/spec.py (BASE, TORSO).  Local construction constants are marked below; the deviations from
spec.py are listed in DEVIATIONS (also printed) - spec.py is NOT edited here.

VISIBLE parts (sub "base", joint "" unless noted)
  B01      Horny kryt zakladne       white   130 x 108 x (11.5..39), plan R26, top R8, wall 2.2; 2 wheel arches,
                                             Ø62 yaw opening under the T04 plate, front LED slot, rear USB-C +
                                             switch + speaker grille; inside: 4 screw bosses, speaker duct ring
  B02      Spodna vana s naraznikom  black   chassis tray: floor z 4..6, side wall = black bumper band z 4..11.5
                                             (0.8 proud), black wheel-well tubs up to the cover, 2 battery bays,
                                             caster / cliff / dock / service openings, sensor clips, PCB standoffs
  B03      Svetlovod zakladne        cyan    40 x 3.5 at z 21 (front)
  B04-R/L  Pneumatika                rubber  Ø34 x 10, TPU 85A (or the bought 34 mm N20 wheel)
  B05-R/L  Disk kolesa               gloss   5 spokes, D-bore 3 mm for the N20 shaft
  B06      Puzdra gulovych koliesok  black   2 cups (snap into the floor), ball protrudes 2.8 mm
  B07      Gulky Ø12                 metal   2 steel balls (bearing balls)
  B08      Okienka senzorov padu     glass   4 IR-pass windows 7 x 4 (tangential, corners)
  (B09)    -- not used: the black turntable ring is T04 of the torso module (rotates with J1, see below)
  B10      Zasuvka USB-C             metal   on the rear board, visible in the rear opening
  B11-1/2  Poklop baterie            black   2 hatches (front / rear cell), 1x M2 + 1 hook each (EU 2023/1542)
  B12      Kontakty dokovania        metal   2 pads Ø6 under the rear (future dock)
  B13      Vypinac                   black   slide-switch knob (rear)
INTERNAL parts (internal=True)
  B14      Nosny mostik pohonu       grey    holds both N20 motors (saddles + straps) and carries the yaw hub
  B15      Naboj otacania trupu      grey    FIXED yaw hub: Ø30 spigot for the 6806 inner ring (z 32..39) on a
                                             Ø34 land, top z 39 carries the E21H horn; cable trough Ø76 for the
                                             ±150° loop, Ø8 fixed cable exit
  B16      Svetelna komorka LED      white   light box behind B03
  BM2-R/L  Motor N20 s enkoderom     metal   12 x 10 x (9 gearbox + 15 motor) + encoder, D-shaft 3 x 10
  BM4      Drziaky motorov N20 (2x)  metal   bent steel straps, 2x M2 each
  BM5      Kontakty baterii          metal   + plates and - springs
  BE1-1/2  Clanok 18650              battery Ø18.5 x 65 along X at y -24 / +24, bottom z 6 (on the hatch)
  BE2      Zadna DPS                 pcb     USB-C, 2S charger IP2326, 2S protection, slide switch, JST battery
  BE3      Senzory padu TCRT5000     pcb     4x reflective IR sensor on a tiny PCB, clipped in the tray
  BE4      LED DPS zakladne          pcb     4x WS2812B-2020 behind the light guide
  BE5      Reproduktor Ø28           black   28 x 5 mm, faces the rear grille through the B01 duct ring
  BW1      Slucka kabla otacania     black   Ø6 bundle, 160° loop in the B15 trough (fixed exit -20° -> T04 slot 180°)

YAW (J1) INTERFACE - shared with nova_v8/cad_torso.py (torso parts, all J1 except the horn)
  * Ring decision: the black turntable ring visible under the torso ROTATES WITH THE TORSO (J1).  It is the torso's
    T04 (Ø77 x 2.5, z 40..42.5) because it also holds the 6806 outer ring (housing OD45 down to z 31.5) and the
    STS3215 cradle - so it is NOT duplicated here.  It floats 1.0 mm above the base top (z 39).
  * 6806 (torso M21) z 32..39: outer ring in T04, inner ring on the B15 spigot Ø30 (slip fit + Loctite 641), resting
    on the Ø34 land at z 32.  STS3215 horn (torso E21H, joint "") on the spigot top z 39, 4x M2 at r 7 / 45 deg.
    1x M3x25 from below (Ø7 service hole in B02 -> tower cavity of B14 -> Ø3.4 bore in B15 -> horn) into the servo
    spline = axial retention of the torso.  The servo only carries torque; the torso weight goes T04 -> outer ring ->
    inner ring -> B15 land -> B14 tower + 4 walls -> B02 floor.
  * Clearances to the rotating T04: housing r 22.5 / z >= 31.5 vs B15 column r 17 and trough floor z <= 28.5;
    B01 top opening r 31 (housing + T04 cable slot r 23..29), covered from above by the T04 disc r 38.5.
  * Cable: Ø6 bundle (battery 2S, 2 motors, 2 encoders, 4 cliff sensors, LED data, speaker) leaves the base cavity
    through the Ø8 exit at -20 deg (r 26.5, between the front cell bay and the bridge wall), lies as a ~160 deg loop
    in the B15 trough (r 23.5..29.5, z 28.5..34.6) and rises at 180 deg into the T04 arc slot (r 23..29, 155..205).
    Range ±150 deg -> loop 10..310 deg.  No mechanical end stop (software limit in the STS3215; a pin under T04 +
    block on the B15 rim would add one).
  * Assembly: B15 -> B14 on the bench (2x M2.5 from inside the tower + 4x M2.5 from the trough), motors + straps,
    B14 -> B02 (4x M2.5 from below), horn E21H on the spigot (4x M2), loop laid in the trough; torso with T04 +
    M21 lowered (inner ring slides over the spigot, spline enters the horn), M3x25 from below; electronics, cells;
    B01 over everything (4x M2.5 from below), hatches.
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Compound, Cylinder, Edge, Face, Plane, Pos, Rot, Solid, Sphere, Vector,
                       Wire, extrude, fillet, mirror, revolve)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "base"
SUB = "base"

# ---------------------------------------------------------------------------------------------------------
# spec numbers
# ---------------------------------------------------------------------------------------------------------
BS = S.BASE
BW, BD, BR = BS["w"], BS["d"], BS["plan_r"]          # 130 x 108, R26
B_TOP = BS["z1"]                                      # 39
TOP_R = BS["top_fillet"]                              # 8
WALL = BS["wall"]                                     # 2.2
BUMP = BS["bumper"]                                   # z 4 .. 11.5, 0.8 proud
B_UNDER, BUMP_TOP, PROUD = BUMP["z0"], BUMP["z1"], BUMP["proud"]
WH = BS["wheel"]
WR, WWID, WX, WY, WZ = WH["d"] / 2, WH["w"], WH["x"], WH["y"], WH["axle_z"]   # 17, 10, 52, 4, 17
LEDB = BS["led"]                                      # 40 x 3.5 at z 21
USB, SWB = BS["usb_c"], BS["switch"]
CLIFF = [tuple(map(float, p)) for p in BS["cliff_sensors"]["xy"]]
CELL_D, CELL_L, CELL_Z0 = BS["batteries"]["d"], BS["batteries"]["len"], BS["batteries"]["z"]
YH = BS["yaw_hub"]
BRG_ID, BRG_OD, BRG_W = YH["bearing"]                 # 6806: 30 / 42 x 7
HUB_D = YH["d"]                                       # 24 (servo-horn post)
T_Z0 = S.TORSO["z0"]                                  # 40 torso bottom
RING_OD = S.TORSO["bottom_plate"]["ring_od"]          # 77
RING_H = S.TORSO["bottom_plate"]["h"]                 # 2.5

# ---------------------------------------------------------------------------------------------------------
# local construction constants (layout decisions of this module; deviations listed in DEVIATIONS)
# ---------------------------------------------------------------------------------------------------------
FLOOR_TOP = B_UNDER + 2.0          # 6.0  tray floor 2.0 thick
COVER_R_BOT = 1.0                  # B01 bottom edge -> V shadow line against the bumper
SKIRT_R_BOT, SKIRT_R_TOP = 2.5, 1.5
CAV_TOP = B_TOP - WALL             # 36.8 inner face of the B01 top wall
LIP_Z1, LIP_T = 15.0, 1.2          # B02 locating lip inside the B01 wall (straight segments only)
# wheel arch / well
ARCH_HW, ARCH_TOP, ARCH_R, ARCH_EDGE_R = 21.0, 30.0, 13.0, 1.2
TUB_X0, TUB_T = 44.3, 1.2          # black tub inner wall |x| 44.3..45.5
WELL_TOP = 36.0                    # tyre top 34 -> 2 mm
# yaw interface - the J1 parts T04 (turntable plate, 6806 housing), M21 (6806) and E21H (horn) are modelled by
# the torso module (nova_v8/cad_torso.py); the base provides the FIXED hub that carries the inner ring + horn
BRG_Z1 = YH["z_top"]               # 39  bearing top = hub top = horn bottom
BRG_Z0 = BRG_Z1 - BRG_W            # 32
T04_HOUSING = dict(r=22.5, z0=31.5)            # rotating 6806 housing of T04 (cad_torso YH_RO / YH_Z0)
T04_SLOT = dict(r0=23.0, r1=29.0, a=180.0)      # T04 arc cable slot r 23..29, 155..205 deg
TOP_OPEN_R = 31.0                  # B01 top opening: housing (22.5) + slot sweep (29) + clearance; T04 Ø77 covers it
HUB_TOP = BRG_Z1                   # 39
SPIGOT_R = BRG_ID / 2 - 0.01       # 6806 inner ring seat (slip fit, Loctite 641)
LAND_R = 17.0                      # Ø34 column, its top face z 32 carries the inner ring
HORN_PCD = 14.0                    # E21H 4x M2 on r 7 at 45 deg
TROUGH_Z0, TROUGH_T = 26.5, 2.0    # B15 trough floor z 26.5..28.5
TROUGH_R, RIM_T, RIM_Z1 = 38.0, 1.5, 35.5
LOOP_R, LOOP_Z, LOOP_RB = 26.5, 31.6, 3.0
FIX_EXIT = (LOOP_R * math.cos(math.radians(-20)), LOOP_R * math.sin(math.radians(-20)), 4.0)   # Ø8 fixed exit
RISER_XY = (-(T04_SLOT["r0"] + T04_SLOT["r1"]) / 2, 0.0)                                     # into the T04 slot
# drive
GB_FACE = 43.5                     # N20 gearbox front face |x|
GB_L, CAN_L = BS["motor"]["gearbox_len"], BS["motor"]["body"][2] - BS["motor"]["gearbox_len"]   # 9, 15
MOT_H, MOT_W = 12.0, 10.0          # z (12) x y (10)
SHAFT_L = 10.0
BRIDGE_Z0, BRIDGE_PLATE = FLOOR_TOP, 2.5
TOWER = dict(x=6.0, y=11.5, cx=3.5, cy=10.0)
HUB_SCREW_Y = 7.5                  # 2x M2.5 from inside the tower cavity into the B15 post
# batteries (2 bays, user replaceable from below)
CELL_Y = 24.0
BAY_X = 35.5                       # inner end faces |x|
BAY_YI, BAY_YO = 14.0, 34.0        # inner faces of the long walls (|y|)
BAY_WALL, BAY_Z1 = 1.4, 20.0
EAR = dict(x=39.0, r=4.0)          # hatch screw ear (overlaps the 71 mm opening)
# others
CASTER_Y = (-44.0, 44.0)
CUP_R, CUP_Z0, CUP_Z1 = 7.5, 2.8, 14.0
BALL_R = BS["caster"]["d"] / 2
DOCK_XY = [(-12.0, 48.0), (12.0, 48.0)]
DOCK_D = BS["dock_pads"]["d"]
SPK = dict(x=26.0, z=21.0, y_face=48.0, d=BS["speaker"]["d"], h=BS["speaker"]["h"])
DUCT_RO, DUCT_RI = 8.5, 6.5
GRILLE_R, GRILLE_HOLE, GRILLE_PITCH = 5.8, 1.5, 2.6
BOSS_XY = [(44.0, 40.0), (-44.0, 40.0), (44.0, -40.0), (-44.0, -40.0)]
BOSS_R = 3.2
BRIDGE_SCREWS = [(24.0, -2.0), (-24.0, -2.0), (24.0, 10.0), (-24.0, 10.0)]
IO = dict(x0=-38.0, x1=-8.0, y0=38.0, y1=51.5, z0=16.77, t=1.6)
IO_STANDOFFS = [(-35.5, 47.5), (-14.0, 41.0)]
LEDBOX = dict(x=24.0, y0=-(BD / 2 - WALL), y1=-45.0, z0=15.0, z1=27.0)
CLIFF_WIN = (BS["cliff_sensors"]["window"][0], BS["cliff_sensors"]["window"][1], 1.6)
TCRT = (10.4, 5.8, 7.0)
BIG = 400.0

DEVIATIONS = [
    "batérie y ±28 -> ±24 (pri ±28 by sa články prekrývali s guľovými kolieskami; 2 šachty s poklopmi zospodu)",
    "predné guľové koliesko y -40 -> -44 (za prednou batériou; zadné ostáva +44)",
    "reproduktor (0,-28) naležato -> zvislo vzadu (26, y 43..48, z 21), smeruje do zadnej mriežky (spredu nie je miesto)",
    "dokovacie plôšky (±8, 50) -> (±12, 48) (kolízia s miskou zadného kolieska a s R2.5 spodnou hranou)",
    "otočný prstenec (TORSO.bottom_plate Ø77) modeluje modul trupu ako T04 (J1) spolu s ložiskom 6806 (M21) a unášačom "
    "(E21H); základňa dodáva len pevný náboj B15 (čap Ø30 namiesto stĺpika Ø24 zo spec yaw_hub.d)",
    "kábelový priechod Ø20 -> otvor v kryte Ø62 + oblúková drážka r 23..29 v T04 (trup) + pevný výstup Ø8 v žľabe B15 "
    "(Ø20 sa do žľabu okolo stĺpika nezmestí; zväzok Ø6 sa zapája až v trupe/základni)",
    "ovládač motorov DRV8833 nie je v základni (podľa TORSO.controller je na DPS v trupe); v základni je nabíjanie 2S "
    "IP2326 + ochrana na zadnej DPS",
]


# ---------------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------------

def bx(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cz(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def cx(r, x0, x1, y=0.0, z=0.0):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cy(r, y0, y1, x=0.0, z=0.0):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def ring_z(ri, ro, z0, z1, x=0.0, y=0.0):
    return cz(ro, z0, z1, x, y) - cz(ri, z0 - 1, z1 + 1, x, y)


def cone_z(r0, r1, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Solid.make_cone(r0, r1, z1 - z0)


def union(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out + s
    return out


def rr_face(w, d, r, z, cx_=0.0, cy_=0.0):
    """Rounded rectangle face in a horizontal plane (straight lines + quarter arcs)."""
    hw, hd = w / 2, d / 2
    corners = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = cx_ + sx * (hw - r), cy_ + sy * (hd - r)
        p = [Vector(ccx + r * math.cos(math.radians(a)), ccy + r * math.sin(math.radians(a)), z)
             for a in (a0, a0 + 45, a0 + 90)]
        corners.append(p)
    edges = []
    for i, (p0, pm, p1) in enumerate(corners):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        edges.append(Edge.make_line(p1, corners[(i + 1) % 4][0]))
    return Face(Wire(edges))


def rr_prism(w, d, r, z0, z1, cx_=0.0, cy_=0.0):
    return extrude(rr_face(w, d, r, z0, cx_, cy_), z1 - z0, dir=(0, 0, 1))


def rr_rot(w, d, r, z0, z1, x, y, ang):
    """Rounded-rectangle prism centred at (x, y), long side rotated by ang (deg) about Z."""
    return Pos(x, y, 0) * Rot(0, 0, ang) * rr_prism(w, d, r, z0, z1)


def stadium_y(xc, zc, w, h, y0, y1):
    """Stadium slot (long axis // X) as a prism along Y."""
    r = h / 2
    s = bx(xc - (w / 2 - r), xc + (w / 2 - r), y0, y1, zc - r, zc + r)
    return (s + cy(r, y0, y1, xc - (w / 2 - r), zc) + cy(r, y0, y1, xc + (w / 2 - r), zc)).clean()


def stadium_z(xc, yc, w, l, z0, z1):
    """Stadium (long axis // Y, width w along X) prism along Z."""
    r = w / 2
    s = bx(xc - r, xc + r, yc - (l / 2 - r), yc + (l / 2 - r), z0, z1)
    return (s + cz(r, z0, z1, xc, yc - (l / 2 - r)) + cz(r, z0, z1, xc, yc + (l / 2 - r))).clean()


def stadium_slot_z(x0, x1, y, w, z0, z1):
    """Slot along X (round ends), prism along Z."""
    r = w / 2
    return (bx(x0 + r, x1 - r, y - r, y + r, z0, z1) + cz(r, z0, z1, x0 + r, y) + cz(r, z0, z1, x1 - r, y)).clean()


def check(name, s, vmin=1.0, multi=False):
    assert s is not None, name
    sol = s.solids()
    assert len(sol) >= 1, f"{name}: no solids"
    bad = [i for i, so in enumerate(sol) if not so.is_valid]
    if bad:
        print(f"  !! {name}: invalid solids {bad}")
    if len(sol) > 1 and not multi:
        print(f"  !! {name}: {len(sol)} solids (expected 1)")
    assert s.volume > vmin, f"{name}: volume {s.volume}"
    return s


def try_fillet(shape, edges, r, name=""):
    if not edges:
        print(f"   [fillet skipped] {name}: no edges")
        return shape
    try:
        f = shape.fillet(r, edges)
        if f.is_valid and abs(f.volume - shape.volume) < 0.05 * shape.volume:
            return f
        print(f"   [fillet rejected] {name}")
    except Exception as e:  # noqa: BLE001
        print(f"   [fillet skipped] {name}: {str(e)[:60]}")
    return shape


def sensor_xy(x, y, inset=0.5):
    """Sensor body centre: the window position moved 0.5 mm toward the plan-corner centre (clears the R26 wall)."""
    ccx = math.copysign(BW / 2 - BR, x)
    ccy = math.copysign(BD / 2 - BR, y)
    d = math.hypot(x - ccx, y - ccy)
    return x - inset * (x - ccx) / d, y - inset * (y - ccy) / d


def corner_frame(x, y):
    """For a point near a plan corner: (angle of the tangent direction in deg) - sensors are oriented tangentially."""
    ccx = math.copysign(BW / 2 - BR, x)
    ccy = math.copysign(BD / 2 - BR, y)
    rad = math.atan2(y - ccy, x - ccx)
    return math.degrees(rad) + 90.0


# ---------------------------------------------------------------------------------------------------------
# B01 top cover
# ---------------------------------------------------------------------------------------------------------

def cover_outer():
    b = rr_prism(BW, BD, BR, BUMP_TOP, B_TOP)
    b = fillet(b.edges().group_by(Axis.Z)[-1], TOP_R)
    b = fillet(b.edges().group_by(Axis.Z)[0], COVER_R_BOT)
    return b


def cover_cavity(extra=0.0):
    """Inner void of B01 (uniform 2.2 wall incl. the top rounding); extends below the open bottom."""
    c = rr_prism(BW - 2 * WALL, BD - 2 * WALL, BR - WALL, BUMP_TOP - 2.0, CAV_TOP + extra)
    return fillet(c.edges().group_by(Axis.Z)[-1], TOP_R - WALL)


def arch_prism(sx):
    """Inverted-U wheel arch through the side wall, open at the bottom (YZ rounded rectangle, extruded in X)."""
    yc, zb, hw = WY, -10.0, ARCH_HW
    corners = [(yc + hw - ARCH_R, ARCH_TOP - ARCH_R, 0), (yc - hw + ARCH_R, ARCH_TOP - ARCH_R, 90),
               (yc - hw + ARCH_R, zb + ARCH_R, 180), (yc + hw - ARCH_R, zb + ARCH_R, 270)]
    arcs = []
    for ccy, ccz, a0 in corners:
        arcs.append([Vector(0, ccy + ARCH_R * math.cos(math.radians(a0 + d)), ccz + ARCH_R * math.sin(math.radians(a0 + d)))
                     for d in (0, 45, 90)])
    edges = []
    for i, (p0, pm, p1) in enumerate(arcs):
        edges.append(Edge.make_three_point_arc(p0, pm, p1))
        edges.append(Edge.make_line(p1, arcs[(i + 1) % 4][0]))
    pr = Pos(58.0, 0, 0) * extrude(Face(Wire(edges)), 14.0, dir=(1, 0, 0))
    return mirror(pr, Plane.YZ) if sx < 0 else pr


def _arch_edges(c):
    out = []
    for e in c.edges():
        bb = e.bounding_box()
        if abs(abs(bb.min.X) - BW / 2) < 0.05 and abs(abs(bb.max.X) - BW / 2) < 0.05 and \
                bb.max.Z <= ARCH_TOP + 0.01 and bb.min.Z >= BUMP_TOP + COVER_R_BOT - 0.1 and \
                abs(bb.center().Y - WY) < ARCH_HW + 0.05:
            out.append(e)
    return out


def grille_holes():
    holes = []
    ny = int(GRILLE_R / GRILLE_PITCH) + 2
    for j in range(-ny, ny + 1):
        zz = SPK["z"] + j * GRILLE_PITCH * math.sqrt(3) / 2
        off = 0.5 * GRILLE_PITCH if j % 2 else 0.0
        for i in range(-ny - 1, ny + 2):
            xx = SPK["x"] + i * GRILLE_PITCH + off
            if math.hypot(xx - SPK["x"], zz - SPK["z"]) <= GRILLE_R:
                holes.append(cy(GRILLE_HOLE / 2, BD / 2 - WALL - 1, BD / 2 + 1, xx, zz))
    return holes


def b01_cover():
    outer = cover_outer()
    cav = cover_cavity()
    shell = outer - cav
    for sx in (1, -1):
        shell = shell - arch_prism(sx)
    shell = try_fillet(shell, _arch_edges(shell), ARCH_EDGE_R, "arch edges")
    # screw bosses (M2.5 self-tapping from below through B02), fused into the top wall
    for (x, y) in BOSS_XY:
        boss = cz(BOSS_R, FLOOR_TOP + 0.2, CAV_TOP + 0.5, x, y) - cz(1.1, FLOOR_TOP, CAV_TOP - 3.0, x, y)
        shell = shell + boss
    # speaker duct ring on the rear inner wall (speaker glued to its face with foam tape)
    yw = BD / 2 - WALL
    duct = cy(DUCT_RO, SPK["y_face"], yw + 0.6, SPK["x"], SPK["z"]) - cy(DUCT_RI, SPK["y_face"] - 1, yw + 1, SPK["x"], SPK["z"])
    shell = shell + duct
    # yaw opening under the T04 turntable plate (soft top edge)
    shell = shell - cz(TOP_OPEN_R, CAV_TOP - 1, B_TOP + 1)
    ed = [e for e in shell.edges() if abs(e.bounding_box().min.Z - B_TOP) < 0.01 and abs(e.bounding_box().max.Z - B_TOP) < 0.01
          and abs(e.bounding_box().size.X - 2 * TOP_OPEN_R) < 0.05]
    shell = try_fillet(shell, ed, 0.6, "ring opening")
    # front LED slot, rear USB-C / switch / grille
    shell = shell - stadium_y(0, LEDB["z"], LEDB["w"], LEDB["h"], -BD / 2 - 5, -BD / 2 + WALL + 1)
    shell = shell - stadium_y(USB["x"], USB["z"], USB["w"], USB["h"], BD / 2 - WALL - 1, BD / 2 + 5)
    sw = Pos(SWB["x"], BD / 2, SWB["z"]) * Rot(90, 0, 0) * rr_prism(SWB["w"], SWB["h"], 1.0, -5, WALL + 1)
    shell = shell - sw
    for h in grille_holes():
        shell = shell - h
    return check("B01", shell)


# ---------------------------------------------------------------------------------------------------------
# B02 tray (chassis + bumper band + wheel tubs + battery bays)
# ---------------------------------------------------------------------------------------------------------

def tray_outer():
    p = PROUD
    s = rr_prism(BW + 2 * p, BD + 2 * p, BR + p, B_UNDER, BUMP_TOP)
    s = fillet(s.edges().group_by(Axis.Z)[0], SKIRT_R_BOT)
    s = fillet(s.edges().group_by(Axis.Z)[-1], SKIRT_R_TOP)
    return s


_CAV_IN = {}


def well_void(sx):
    """Wheel-well void: straight up to z 30, above that it follows the B01 inner surface 0.8 mm below it, so the
    black tub ceiling also lines the top rounding (no white cover visible from below)."""
    if "c" not in _CAV_IN:
        from build123d import offset
        _CAV_IN["c"] = offset(cover_cavity(), amount=-TUB_T + 0.4)
    lo = bx(sx * (TUB_X0 + TUB_T), sx * 75.0, WY - ARCH_HW, WY + ARCH_HW, -5.0, 30.0)
    hi = bx(sx * (TUB_X0 + TUB_T), sx * 75.0, WY - ARCH_HW, WY + ARCH_HW, 29.0, 40.0) & _CAV_IN["c"]
    return lo + hi


def tub_solid(sx):
    t = bx(sx * TUB_X0, sx * (BW / 2 - WALL), WY - ARCH_HW - TUB_T, WY + ARCH_HW + TUB_T, B_UNDER, CAV_TOP)
    return t & cover_cavity()


def lip():
    inner = rr_prism(BW - 2 * WALL - 0.4 - 2 * LIP_T, BD - 2 * WALL - 0.4 - 2 * LIP_T, BR - WALL - 0.2 - LIP_T,
                     FLOOR_TOP - 1, LIP_Z1 + 1)
    ring = rr_prism(BW - 2 * WALL - 0.4, BD - 2 * WALL - 0.4, BR - WALL - 0.2, BUMP_TOP - 0.01, LIP_Z1) + \
        rr_prism(BW - 2 * WALL + 0.2, BD - 2 * WALL + 0.2, BR - WALL + 0.1, FLOOR_TOP - 0.01, BUMP_TOP)
    ring = ring - inner
    keep = bx(-36, -10, -BIG, -40, 0, 40) + bx(10, 36, -BIG, -40, 0, 40) + bx(-36, -10, 40, BIG, 0, 40)
    lp = ring & keep
    return lp


def battery_bay(sy):
    yc = sy * CELL_Y
    w = BAY_WALL
    walls = bx(-BAY_X - w, BAY_X + w, sy * (BAY_YI - w), sy * BAY_YI, FLOOR_TOP - 0.01, BAY_Z1)
    walls = walls + bx(-BAY_X - w, BAY_X + w, sy * BAY_YO, sy * (BAY_YO + w), FLOOR_TOP - 0.01, BAY_Z1)
    for ex in (1, -1):
        walls = walls + bx(ex * BAY_X, ex * (BAY_X + w), sy * BAY_YI, sy * BAY_YO, FLOOR_TOP - 0.01, BAY_Z1)
    # hook slot in the -X end wall (hatch tongue)
    walls = walls - bx(-BAY_X - w - 1, -BAY_X + 0.1, yc - 4.3, yc + 4.3, FLOOR_TOP - 0.1, FLOOR_TOP + 1.4)
    # screw boss above the hatch ear (+X), bridged to the end wall
    boss = cz(3.5, FLOOR_TOP, FLOOR_TOP + 6.0, EAR["x"], yc) + bx(BAY_X, EAR["x"], yc - 3.5, yc + 3.5,
                                                                  FLOOR_TOP, FLOOR_TOP + 6.0)
    boss = boss - cz(0.8, FLOOR_TOP - 1, FLOOR_TOP + 5.0, EAR["x"], yc)
    return walls + boss


def hatch_opening(sy, grow=0.0):
    yc = sy * CELL_Y
    o = rr_prism(2 * BAY_X + 2 * grow, BAY_YO - BAY_YI + 2 * grow, 3.0 + grow, B_UNDER - 1, FLOOR_TOP + 0.01, 0, yc)
    return o + cz(EAR["r"] + grow, B_UNDER - 1, FLOOR_TOP + 0.01, EAR["x"], yc)


def countersink(x, y, d_hole=2.8, d_head=5.2, z_face=B_UNDER, up=True, depth=12.0):
    """Countersunk screw hole entering from the face z_face (from below when up=True)."""
    h = d_head / 2 - d_hole / 2
    if up:
        return cz(d_hole / 2, z_face - 1, z_face + depth, x, y) + cone_z(d_head / 2, d_hole / 2, z_face - 0.001, z_face + h, x, y) \
            + cz(d_head / 2, z_face - 2, z_face, x, y)
    return cz(d_hole / 2, z_face - depth, z_face + 1, x, y) + cone_z(d_hole / 2, d_head / 2, z_face - h, z_face + 0.001, x, y) \
        + cz(d_head / 2, z_face, z_face + 2, x, y)


def cliff_clips(x, y):
    ang = corner_frame(x, y)
    L, Wd = TCRT[0], TCRT[1]
    x, y = sensor_xy(x, y)
    clips = None
    for s in (-1, 1):
        c = Pos(x, y, 0) * Rot(0, 0, ang) * bx(s * (L / 2 + 0.2), s * (L / 2 + 1.4), -2.0, 2.0, FLOOR_TOP - 0.01, FLOOR_TOP + 4.0)
        clips = c if clips is None else clips + c
    return clips


def speaker_saddle():
    s = bx(SPK["x"] - 8, SPK["x"] + 8, SPK["y_face"] - 4.5, SPK["y_face"] - 0.5, FLOOR_TOP - 0.01, FLOOR_TOP + 3.0)
    return s - cy(SPK["d"] / 2 + 0.1, SPK["y_face"] - 10, SPK["y_face"] + 1, SPK["x"], SPK["z"])


def b02_tray():
    t = tray_outer()
    t = t - rr_prism(BW - 2 * WALL, BD - 2 * WALL, BR - WALL, FLOOR_TOP, 40)
    t = t + lip()
    for sx in (1, -1):
        t = t + tub_solid(sx)
    for sy in (1, -1):
        t = t + battery_bay(sy)
    for (x, y) in CLIFF:
        t = t + cliff_clips(x, y)
    t = t + speaker_saddle()
    for (x, y) in IO_STANDOFFS:
        t = t + (cz(2.5, FLOOR_TOP - 0.01, IO["z0"], x, y) - cz(0.8, FLOOR_TOP + 2, IO["z0"] + 1, x, y))
    # ---- cuts ----
    for sx in (1, -1):
        t = t - well_void(sx)
        t = t - arch_prism(sx)
        t = t - cx(2.5, sx * (TUB_X0 - 1), sx * (TUB_X0 + TUB_T + 1), WY, WZ)       # N20 shaft
    for sy in (1, -1):
        t = t - hatch_opening(sy, grow=0.3)
    for y in CASTER_Y:
        t = t - cz(CUP_R + 0.2, B_UNDER - 1, FLOOR_TOP + 1, 0, y)
    for (x, y) in CLIFF:
        w, d, r = CLIFF_WIN
        t = t - rr_rot(w + 0.2, d + 0.2, r + 0.1, B_UNDER - 1, FLOOR_TOP + 1, x, y, corner_frame(x, y))
    for (x, y) in DOCK_XY:
        t = t - cz(DOCK_D / 2 + 0.1, B_UNDER - 1, B_UNDER + 1.2, x, y) - cz(1.0, B_UNDER, FLOOR_TOP + 1, x, y)
    t = t - cz(3.5, B_UNDER - 1, FLOOR_TOP + 1)                                       # service hole (M3 of the yaw horn)
    for k in range(5):                                                                # vents under the charger
        yy = 39.5 + 2.6 * k
        t = t - stadium_slot_z(-31.0, -21.0, yy, 1.4, B_UNDER - 1, FLOOR_TOP + 1)
    for (x, y) in BOSS_XY + BRIDGE_SCREWS:
        t = t - countersink(x, y, depth=2.0 + 1.0)
    return check("B02", t)


# ---------------------------------------------------------------------------------------------------------
# small visible parts
# ---------------------------------------------------------------------------------------------------------

def b03_led():
    return check("B03", stadium_y(0, LEDB["z"], LEDB["w"] - 0.2, LEDB["h"] - 0.2, -BD / 2 + 0.1, -BD / 2 + WALL + 1.0))


def wheel(sx):
    xc = sx * WX
    t = cx(WR, xc - WWID / 2, xc + WWID / 2, WY, WZ)
    t = fillet(t.edges(), 2.5)
    t = t - cx(12.0, xc - 10, xc + 10, WY, WZ)
    for g in (-2.3, 2.3):                                     # two circumferential grooves (grip + look)
        t = t - (cx(WR + 1, xc + g - 0.4, xc + g + 0.4, WY, WZ) - cx(WR - 0.6, xc - 10, xc + 10, WY, WZ))
    hub_w = WWID - 2.0
    h = cx(12.0, xc - hub_w / 2, xc + hub_w / 2, WY, WZ)
    xo = xc + sx * hub_w / 2
    xi = xc - sx * hub_w / 2
    h = h + cx(3.5, xi, xi - sx * 2.0, WY, WZ)                   # inner boss on the N20 shaft
    dish = cx(10.0, xo - sx * 1.6, xo + sx * 1.0, WY, WZ)
    dish = dish - cx(4.2, xo - 3, xo + 3, WY, WZ)
    spokes = None
    for k in range(5):
        sp = Pos(xo, WY, WZ) * Rot(90 + 72 * k, 0, 0) * Pos(0, 0, 7.0) * Box(4.0, 2.2, 6.4)
        spokes = sp if spokes is None else spokes + sp
    spokes = spokes & cx(10.4, xo - sx * 1.6, xo, WY, WZ)
    h = h - (dish - spokes)
    shaft = cx(1.5, xi - sx * 2.1, xc + sx * 1.8, WY, WZ)
    h = h - (shaft - bx(xc - 8, xc + 8, WY - 2, WY + 2, WZ + 1.0, WZ + 2))  # D-bore 3 mm, flat at 2.5
    h = h - cx(1.3, xo - sx * 0.6, xo + sx * 1, WY, WZ)
    return check("tyre", t), check("hub", h)


def casters():
    cups, balls = [], []
    for y in CASTER_Y:
        cup = cz(CUP_R, CUP_Z0, CUP_Z1, 0, y)
        cup = fillet(cup.edges().group_by(Axis.Z)[0], 0.8)
        cup = cup + bx(-CUP_R - 3.5, CUP_R + 3.5, y - 3, y + 3, FLOOR_TOP, FLOOR_TOP + 1.2)     # ears on the floor
        for sx in (1, -1):                                                                      # snap barbs under the floor
            cup = cup + bx(sx * (CUP_R - 0.5), sx * (CUP_R + 0.5), y - 2, y + 2, B_UNDER - 0.7, B_UNDER - 0.05)
        cup = cup - Pos(0, y, BALL_R) * Sphere(BALL_R + 0.25)
        cups.append(cup)
        balls.append(Pos(0, y, BALL_R) * Sphere(BALL_R))
    return check("B06", Compound(cups), multi=True), check("B07", Compound(balls), multi=True)


def cliff_windows():
    w, d, r = CLIFF_WIN
    ws = [rr_rot(w, d, r, B_UNDER + 0.4, FLOOR_TOP, x, y, corner_frame(x, y)) for (x, y) in CLIFF]
    return check("B08", Compound(ws), multi=True)


def b10_usb():
    yf = BD / 2 - 0.4
    s = stadium_y(USB["x"], USB["z"], 8.94, 3.26, yf - 7.35, yf)
    s = s - stadium_y(USB["x"], USB["z"], 8.34, 2.56, yf - 6.6, yf + 1)
    s = s + bx(USB["x"] - 3.3, USB["x"] + 3.3, yf - 6.6, yf - 1.0, USB["z"] - 0.35, USB["z"] + 0.35)
    return check("B10", s)


def b11_hatch(sy):
    yc = sy * CELL_Y
    h = hatch_opening(sy, grow=0.0)
    h = h & bx(-BIG, BIG, -BIG, BIG, B_UNDER, FLOOR_TOP)
    h = try_fillet(h, h.edges().group_by(Axis.Z)[0], 0.6, "hatch edge")
    h = h + bx(-BAY_X - 2.8, -BAY_X + 0.6, yc - 4.0, yc + 4.0, FLOOR_TOP, FLOOR_TOP + 1.0)    # hook tongue
    h = h - countersink(EAR["x"], yc, d_hole=2.3, d_head=4.2, z_face=B_UNDER, depth=4.0)
    h = h - bx(EAR["x"] + EAR["r"] - 1.2, EAR["x"] + EAR["r"] + 1, yc - 2.0, yc + 2.0, B_UNDER - 1, B_UNDER + 0.8)   # pry notch
    for dx in (-18.0, 0.0, 18.0):                                                              # cell cradle ribs
        h = h + (bx(dx - 0.8, dx + 0.8, yc - 6, yc + 6, FLOOR_TOP, FLOOR_TOP + 1.2)
                 - cx(CELL_D / 2 + 0.1, -40, 40, yc, CELL_Z0 + CELL_D / 2))
    return check(f"B11 {sy}", h)


def b12_dock():
    pads = []
    for (x, y) in DOCK_XY:
        p = cz(DOCK_D / 2, B_UNDER + 0.2, B_UNDER + 1.2, x, y)
        p = fillet(p.edges().group_by(Axis.Z)[0], 0.3)
        pads.append(p)
    return check("B12", Compound(pads), multi=True)


def b13_switch():
    yf = BD / 2 - 0.8
    knob = bx(SWB["x"] - 2.0 - 1.2, SWB["x"] - 2.0 + 1.2, BD / 2 - 2.4, yf, SWB["z"] - 1.0, SWB["z"] + 1.0)
    return check("B13", knob)


# ---------------------------------------------------------------------------------------------------------
# internal: drive bridge, yaw hub, bearing, horn, light box
# ---------------------------------------------------------------------------------------------------------

def motor_envelope(sx, grow=0.0):
    xg0, xg1 = GB_FACE - GB_L, GB_FACE
    xc0 = xg0 - CAN_L
    g = bx(sx * (xg0 - grow), sx * (xg1 + grow), WY - MOT_W / 2 - grow, WY + MOT_W / 2 + grow,
           WZ - MOT_H / 2 - grow, WZ + MOT_H / 2 + grow)
    c = cx(MOT_H / 2 + grow, sx * xc0, sx * xg0, WY, WZ) & bx(-BIG, BIG, WY - MOT_W / 2 - grow, WY + MOT_W / 2 + grow, -BIG, BIG)
    return g + c


def b14_bridge():
    z0, zp = BRIDGE_Z0, BRIDGE_Z0 + BRIDGE_PLATE
    b = bx(-43, 43, -5, 11.5, z0, zp)
    top = TROUGH_Z0
    for sx in (1, -1):
        b = b + bx(sx * 37.5, sx * 42.5, -6, 14, z0, zp)                                  # strap ear plates
        b = b + bx(sx * 20.0, sx * 43.0, WY - MOT_W / 2, WY + MOT_W / 2, zp - 0.01, WZ - 2.0)  # saddle
        for (y0, y1) in ((-3, -1), (9, 11)):
            b = b + bx(sx * 19.0, sx * 34.0, y0, y1, zp - 0.01, top)                       # side walls (carry B15)
        for (y0, y1) in ((-6, -1), (9, 14)):
            b = b + bx(sx * 37.5, sx * 42.5, y0, y1, zp - 0.01, WZ - 4.0)                  # strap seats
        b = b - motor_envelope(sx, grow=0.1)
        for yy in (-4.0, 12.0):
            b = b - cz(0.8, zp, WZ, sx * 40.0, yy)                                         # strap screws M2
    tw = TOWER
    b = b + bx(-tw["x"], tw["x"], -tw["y"], tw["y"], zp - 0.01, top)
    b = b - bx(-tw["cx"], tw["cx"], -tw["cy"], tw["cy"], z0 - 1, top - 2.0)                  # cavity (M3 + B15 screws)
    b = b - cz(1.7, top - 3, top + 1)                                                       # M3 yaw screw
    for yy in (-HUB_SCREW_Y, HUB_SCREW_Y):
        b = b - cz(1.35, top - 3, top + 1, 0, yy)                                           # 2x M2.5 into the B15 post
    for (x, y) in BRIDGE_SCREWS:
        b = b - cz(1.1, z0 - 1, z0 + 9, x, y)                                               # pilots for the tray screws
        b = b - cz(1.1, top - 8, top + 1, x + math.copysign(2.5, x), y)                     # pilots for the trough screws
    return check("B14", b)


def hub_screws_xy():
    return [(x + math.copysign(2.5, x), y) for (x, y) in BRIDGE_SCREWS]


def b15_hub():
    """Fixed yaw hub: trough floor (cable loop) + Ø34 column + Ø30 spigot in the 6806 inner ring, top z 39 = E21H."""
    z0, z1 = TROUGH_Z0, TROUGH_Z0 + TROUGH_T
    h = cz(TROUGH_R, z0, z1)
    h = h + ring_z(TROUGH_R - RIM_T, TROUGH_R, z1 - 0.01, RIM_Z1)
    h = h + cz(LAND_R, z1 - 0.01, BRG_Z0)                                     # column, top = inner-ring land
    sp = cz(SPIGOT_R, BRG_Z0 - 0.01, HUB_TOP)
    sp = try_fillet(sp, sp.edges().group_by(Axis.Z)[-1], 0.4, "spigot lead-in")
    h = h + sp
    h = h - cz(1.7, z0 - 1, HUB_TOP + 1)                                      # Ø3.4 for the M3 servo-spline screw
    for yy in (-HUB_SCREW_Y, HUB_SCREW_Y):
        h = h - cz(1.0, z0 - 1, z0 + 7.0, 0, yy)                              # M2.5 pilots from below (tower cavity)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h - cz(0.8, HUB_TOP - 6, HUB_TOP + 1, HORN_PCD / 2 * math.cos(a), HORN_PCD / 2 * math.sin(a))  # E21H M2
    for (x, y) in hub_screws_xy():
        h = h - countersink(x, y, d_hole=2.8, d_head=5.2, z_face=z1, up=False, depth=4)
    h = h - cz(FIX_EXIT[2], z0 - 1, z1 + 1, FIX_EXIT[0], FIX_EXIT[1])
    rim_top = [e for e in h.edges() if abs(e.bounding_box().min.Z - RIM_Z1) < 0.01 and abs(e.bounding_box().max.Z - RIM_Z1) < 0.01]
    h = try_fillet(h, rim_top, 0.5, "rim top")
    return check("B15", h)


def n20_motor(sx):
    """N20 6V gear motor with magnetic encoder (AliExpress 'N20 encoder'), shaft along +sx X into the wheel."""
    xg0, xg1 = GB_FACE - GB_L, GB_FACE
    xc0 = xg0 - CAN_L
    m = bx(sx * (xg0 + 0.9), sx * (xg1 - 0.9), WY - MOT_W / 2 + 0.4, WY + MOT_W / 2 - 0.4, WZ - MOT_H / 2 + 0.4, WZ + MOT_H / 2 - 0.4)
    for (a, b_) in ((xg0, xg0 + 0.9), (xg1 - 0.9, xg1)):                       # gearbox plates
        m = m + bx(sx * a, sx * b_, WY - MOT_W / 2, WY + MOT_W / 2, WZ - MOT_H / 2, WZ + MOT_H / 2)
    for (yy, zz) in ((WY - 3.8, WZ - 4.8), (WY + 3.8, WZ - 4.8), (WY - 3.8, WZ + 4.8), (WY + 3.8, WZ + 4.8)):
        m = m + cx(0.6, sx * xg0, sx * xg1, yy, zz)                             # plate posts
    m = m + cx(2.0, sx * xg1 - sx * 0.01, sx * (xg1 + 0.8), WY, WZ)             # bearing boss
    m = m + cx(1.475, sx * (xg1 + 0.8) - sx * 0.01, sx * (xg1 + SHAFT_L), WY, WZ) - \
        bx(sx * (xg1 + 2.0), sx * (xg1 + SHAFT_L + 1), WY - 3, WY + 3, WZ + 1.0, WZ + 3)   # D-shaft
    can = cx(MOT_H / 2, sx * xc0, sx * xg0 + sx * 0.01, WY, WZ) & bx(-BIG, BIG, WY - MOT_W / 2, WY + MOT_W / 2, -BIG, BIG)
    m = m + can
    m = m + cx(4.5, sx * (xc0 - 1.0), sx * xc0 + sx * 0.01, WY, WZ)              # end cap
    m = m + cx(3.0, sx * (xc0 - 3.0), sx * (xc0 - 1.0) + sx * 0.01, WY, WZ)       # encoder magnet
    m = m + bx(sx * (xc0 - 4.0), sx * (xc0 - 3.0), WY - 5.5, WY + 5.5, WZ - 6.5, WZ + 6.5)   # encoder PCB
    m = m + bx(sx * (xc0 - 7.0), sx * (xc0 - 4.0), WY - 3.5, WY + 3.5, WZ - 1.5, WZ + 2.0)   # 6-pin connector
    return check("BM2", m)


def straps():
    out = []
    for sx in (1, -1):
        x0, x1 = sx * 37.5, sx * 42.5
        u = bx(x0, x1, WY - MOT_W / 2 - 0.8, WY + MOT_W / 2 + 0.8, WZ - 4.0, WZ + MOT_H / 2 + 0.8) - \
            bx(min(x0, x1) - 1, max(x0, x1) + 1, WY - MOT_W / 2, WY + MOT_W / 2, WZ - 5.0, WZ + MOT_H / 2)
        for (y0, y1) in ((-6, WY - MOT_W / 2 - 0.8), (WY + MOT_W / 2 + 0.8, 14)):
            u = u + bx(x0, x1, y0, y1, WZ - 4.0, WZ - 3.2)
        for yy in (-4.0, 12.0):
            u = u - cz(1.1, WZ - 5, WZ - 2, sx * 40.0, yy)
        out.append(u)
    return check("BM4", Compound(out), multi=True)


def b16_ledbox():
    L = LEDBOX
    c = bx(-L["x"], L["x"], L["y0"], L["y1"], L["z0"], L["z1"])
    c = c - bx(-L["x"] + 2.0, L["x"] - 2.0, L["y0"] - 1, L["y1"] - 1.2, L["z0"] + 2.0, L["z1"] - 2.0)
    c = c - stadium_y(0, LEDB["z"], LEDB["w"] + 0.4, LEDB["h"] + 0.4, L["y0"] - 1, L["y0"] + 1.5)
    return check("B16", c)


def led_pcb():
    y0 = LEDBOX["y1"] - 1.2 - 0.8
    b = bx(-20.0, 20.0, y0, y0 + 0.8, LEDB["z"] - 3.5, LEDB["z"] + 3.5)
    for x in (-15.0, -5.0, 5.0, 15.0):
        b = b + bx(x - 1.0, x + 1.0, y0 - 0.9, y0 + 0.01, LEDB["z"] - 1.0, LEDB["z"] + 1.0)
    return check("BE4", b)


def cell(sy):
    yc, zc = sy * CELL_Y, CELL_Z0 + CELL_D / 2
    plus = 1 if sy < 0 else -1                 # front cell + toward +X, rear cell + toward -X (series loop)
    xp = plus * (BAY_X - 0.5)                  # + terminal tip
    xb = xp - plus * 0.6
    xm = xb - plus * (CELL_L - 0.6)
    c = cx(CELL_D / 2, xm, xb, yc, zc)
    c = fillet(c.edges(), 0.8)
    c = c + cx(3.0, xb - plus * 0.05, xp, yc, zc)
    c = c - (cx(CELL_D / 2 + 1, xb - plus * 1.6, xb - plus * 1.0, yc, zc) - cx(CELL_D / 2 - 0.25, -50, 50, yc, zc))
    return check("BE1", c)


def contacts():
    out = []
    for sy in (1, -1):
        yc, zc = sy * CELL_Y, CELL_Z0 + CELL_D / 2
        plus = 1 if sy < 0 else -1
        out.append(bx(plus * (BAY_X - 0.5), plus * BAY_X, yc - 5, yc + 5, zc - 5.5, zc + 5.5))      # + plate
        xw = -plus * BAY_X
        pl = bx(xw, xw + plus * 0.5, yc - 5, yc + 5, zc - 5.5, zc + 5.5)
        xm = plus * (BAY_X - 0.5 - CELL_L)                                                       # - end of the cell
        spring = Pos(xw + plus * 0.5, yc, zc) * Rot(0, 90 * plus, 0) * \
            Solid.make_cone(4.0, 2.2, abs(xm - (xw + plus * 0.5)) - 0.05)
        out.append(pl + spring)
    return check("BM5", Compound(out), multi=True)


def io_board():
    I = IO
    z0, z1 = I["z0"], I["z0"] + I["t"]
    b = bx(I["x0"], I["x1"], I["y0"], I["y1"], z0, z1)
    for (x, y) in IO_STANDOFFS:
        b = b - cz(1.1, z0 - 1, z1 + 1, x, y)
    comps = [b,
             bx(SWB["x"] - 4.3, SWB["x"] + 4.3, BD / 2 - 6.6, BD / 2 - 2.4, z1, z1 + 3.4),        # slide switch body
             bx(-25.0, -21.0, 39.0, 43.0, z1, z1 + 0.8),                                        # IP2326
             bx(-31.0, -26.5, 38.5, 43.0, z1, z1 + 3.0),                                        # inductor
             bx(-12.0, -9.0, 44.0, 47.0, z1, z1 + 1.0),                                         # 2S protection
             bx(-19.5, -16.5, 44.0, 47.0, z1, z1 + 1.0),                                        # dual MOSFET
             bx(-37.5, -33.0, 38.5, 44.5, z1, z1 + 6.0)]                                        # JST-PH battery
    return check("BE2", union(comps))


def cliff_pcbs():
    out = []
    L, Wd, H = TCRT
    for (x, y) in CLIFF:
        ang = corner_frame(x, y)
        body = bx(-L / 2, L / 2, -Wd / 2, Wd / 2, FLOOR_TOP + 0.2, FLOOR_TOP + 0.2 + H)
        for s in (-1, 1):
            body = body - cz(1.4, FLOOR_TOP, FLOOR_TOP + 0.5, s * 2.5, 0)                     # lens recesses
        pcb = bx(-L / 2, L / 2, -Wd / 2, Wd / 2, FLOOR_TOP + 0.2 + H, FLOOR_TOP + 1.0 + H)
        px, py = sensor_xy(x, y)
        out.append(Pos(px, py, 0) * Rot(0, 0, ang) * (body + pcb))
    return check("BE3", Compound(out), multi=True)


def speaker():
    x, z, yf, r, hh = SPK["x"], SPK["z"], SPK["y_face"], SPK["d"] / 2, SPK["h"]
    s = cy(r, yf - 1.0, yf, x, z) - cy(r - 1.6, yf - 0.6, yf + 1, x, z)
    s = s + cy(r - 1.6, yf - 1.2, yf - 0.5, x, z)
    s = s + cy(9.0, yf - hh, yf - 0.9, x, z)
    s = s + bx(x + 9.0, x + 13.0, yf - 2.6, yf - 1.0, z - 1.2, z + 1.2)
    return check("BE5", s)


def cable_loop():
    c = Edge.make_circle(LOOP_RB, Plane(origin=(LOOP_R, 0, LOOP_Z), z_dir=(0, 1, 0)))
    a0 = math.degrees(math.atan2(FIX_EXIT[1], FIX_EXIT[0]))
    arc = Rot(0, 0, a0) * revolve(Face(Wire([c])), Axis.Z, 180.0 - a0)
    fx, fy = FIX_EXIT[0], FIX_EXIT[1]
    down = cz(LOOP_RB, 20.0, LOOP_Z, fx, fy)
    rx, ry = RISER_XY
    up = cz(LOOP_RB, LOOP_Z, B_TOP + 0.5, rx, ry) + Pos(rx, ry, LOOP_Z) * Sphere(LOOP_RB)
    link = cx(LOOP_RB, -LOOP_R, rx, 0, LOOP_Z)
    return check("BW1", arc + down + up + link + Pos(fx, fy, LOOP_Z) * Sphere(LOOP_RB) + Pos(-LOOP_R, 0, LOOP_Z) * Sphere(LOOP_RB))


# ---------------------------------------------------------------------------------------------------------

def build():
    t0 = time.time()
    tyres, hubs = {}, {}
    for sx, side in ((-1, "R"), (1, "L")):
        tyres[side], hubs[side] = wheel(sx)
    cups, balls = casters()
    print(f"  visible small parts {time.time() - t0:.1f}s")
    t1 = time.time()
    cover = b01_cover()
    print(f"  B01 {time.time() - t1:.1f}s")
    t1 = time.time()
    tray = b02_tray()
    print(f"  B02 {time.time() - t1:.1f}s")
    I = dict(internal=True)
    parts = [
        PartRec("B01", "Horný kryt základne", cover, "white", SUB, "", (0, 0, 70),
                note="130×108×(11.5–39), R26/R8, stena 2.2; podbehy, otvor Ø62 pod tanierom T04, 4× M2.5 zdola"),
        PartRec("B02", "Spodná vaňa s nárazníkom", tray, "black", SUB, "", (0, 0, -30),
                note="nosná vaňa: dno 2 mm, nárazník z 4–11.5 (0.8 von), vane kolies, 2 šachty batérií"),
        PartRec("B03", "Svetlovod základne", b03_led(), "cyan_led", SUB, "", (0, -30, 70), note="40×3.5, z 21, PMMA opál"),
        PartRec("B04-R", "Pneumatika pravá", tyres["R"], "rubber", SUB, "", (-40, 0, 0), note="Ø34×10 TPU 85A"),
        PartRec("B04-L", "Pneumatika ľavá", tyres["L"], "rubber", SUB, "", (40, 0, 0), note="Ø34×10 TPU 85A"),
        PartRec("B05-R", "Disk kolesa pravý", hubs["R"], "black_gloss", SUB, "", (-52, 0, 0), note="D otvor 3 mm (N20)"),
        PartRec("B05-L", "Disk kolesa ľavý", hubs["L"], "black_gloss", SUB, "", (52, 0, 0), note="D otvor 3 mm (N20)"),
        PartRec("B06", "Puzdrá guľových koliesok", cups, "black", SUB, "", (0, 0, -55),
                note="zacvaknuté do dna, guľa vyčnieva 2.8 mm"),
        PartRec("B07", "Guľky Ø12", balls, "metal", SUB, "", (0, 0, -70), note="oceľové guľky z ložísk"),
        PartRec("B08", "Okienka senzorov pádu (4×)", cliff_windows(), "glass", SUB, "", (0, 0, -55),
                note="IR priepustný čierny akrylát 7×4, zapustené 0.4"),
        PartRec("B10", "Zásuvka USB-C", b10_usb(), "metal", SUB, "", (0, 30, 0), note="nabíjanie 5 V, na zadnej DPS"),
        PartRec("B11-1", "Poklop batérie predný", b11_hatch(-1), "black", SUB, "", (0, 0, -70),
                note="1× M2 + jazýček; článok sa vyberá zospodu"),
        PartRec("B11-2", "Poklop batérie zadný", b11_hatch(1), "black", SUB, "", (0, 0, -70),
                note="1× M2 + jazýček; článok sa vyberá zospodu"),
        PartRec("B12", "Kontakty dokovania", b12_dock(), "metal", SUB, "", (0, 0, -55), note="2× Ø6 poniklované, budúci dok"),
        PartRec("B13", "Vypínač", b13_switch(), "black", SUB, "", (0, 30, 0), note="posuvný vypínač SK12D07"),
        # ---- internal ----
        PartRec("B14", "Nosný mostík pohonu", b14_bridge(), "grey", SUB, "", (0, 0, 10),
                note="PETG; 2 lôžka N20 + veža a steny pod nábojom; 4× M2.5 zdola do vane", **I),
        PartRec("B15", "Náboj otáčania trupu", b15_hub(), "grey", SUB, "", (0, 0, 40),
                note="PETG; pevný: čap Ø30 pre vnútorný krúžok 6806 (z 32–39), na ňom unášač E21H (4× M2), M3×25 zdola, "
                     "žľab slučky kábla", **I),
        PartRec("B16", "Svetelná komôrka LED", b16_ledbox(), "white", SUB, "", (0, -15, 70), note="biela, za B03", **I),
        PartRec("BM2-R", "Motor N20 s enkodérom pravý", n20_motor(-1), "metal", SUB, "", (-25, 0, 10),
                note="6 V 1:100–1:150, magnetický enkodér", **I),
        PartRec("BM2-L", "Motor N20 s enkodérom ľavý", n20_motor(1), "metal", SUB, "", (25, 0, 10),
                note="6 V 1:100–1:150, magnetický enkodér", **I),
        PartRec("BM4", "Držiaky motorov N20 (2×)", straps(), "metal", SUB, "", (0, 0, 25), note="oceľové, 2× M2", **I),
        PartRec("BM5", "Kontakty batérií", contacts(), "metal", SUB, "", (0, 0, -20), note="+ plôšky a − pružiny", **I),
        PartRec("BE1-1", "Článok 18650 predný", cell(-1), "battery", SUB, "", (0, 0, -45), **I),
        PartRec("BE1-2", "Článok 18650 zadný", cell(1), "battery", SUB, "", (0, 0, -45), **I),
        PartRec("BE2", "Zadná DPS (USB-C, nabíjanie 2S)", io_board(), "pcb", SUB, "", (0, 30, 20),
                note="IP2326 + ochrana 2S + vypínač + JST-PH", **I),
        PartRec("BE3", "Senzory pádu TCRT5000 (4×)", cliff_pcbs(), "pcb", SUB, "", (0, 0, -15), **I),
        PartRec("BE4", "LED DPS základne", led_pcb(), "pcb", SUB, "", (0, -15, 70), note="4× WS2812B-2020", **I),
        PartRec("BE5", "Reproduktor Ø28", speaker(), "black", SUB, "", (0, 15, 30), note="8 Ω 1–2 W, do zadnej mriežky", **I),
        PartRec("BW1", "Slučka kábla otáčania", cable_loop(), "black", SUB, "", (0, 0, 55),
                note="zväzok Ø6 (batéria, motory, enkodéry, senzory, LED, reproduktor), ±150°", **I),
    ]
    print(f"  base: {len(parts)} parts in {time.time() - t0:.1f}s")
    return parts


# ---------------------------------------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------------------------------------

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
    if isinstance(ab, (list, tuple)):
        return float(sum(x.volume for x in ab))
    return float(ab.volume)


def interference(parts, others=(), tol=0.3):
    bad = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            v = _overlap(parts[i].shape, parts[j].shape)
            if v > tol or v < 0:
                bad.append((parts[i].id, parts[j].id, round(v, 2)))
    for p in parts:
        for o in others:
            v = _overlap(p.shape, o.shape)
            if v > tol or v < 0:
                bad.append((p.id, o.id, round(v, 2)))
    return bad


def other_v8_parts():
    """Parts of the other v8 modules that have already written a manifest (loaded from their STEP export)."""
    import glob
    import json
    from build123d import import_step
    out = []
    for fn in sorted(glob.glob(os.path.join(OUT_DIR, "manifest", "*.json"))):
        if os.path.basename(fn) == MANIFEST + ".json":
            continue
        for r in json.load(open(fn)):
            if r["bbox"]["min"][2] > 60:          # only what can touch the base
                continue
            stp = os.path.join(OUT_DIR, "step", r["id"] + ".step")
            if not os.path.exists(stp):
                continue
            try:
                shp = import_step(stp)
            except Exception as e:  # noqa: BLE001
                print("   step import failed", r["id"], e)
                continue
            out.append(PartRec(r["id"], r["name"], shp, r["mat"], r["sub"], r["joint"]))
    return out


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
    for r in recs:
        print(f"  {r['id']:7s} {r['mat']:11s} {r['joint']:3s} int={int(r['internal'])} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("DEVIATIONS:")
    for d in DEVIATIONS:
        print("  -", d)
    if "--check" in sys.argv:
        oth = other_v8_parts()
        print(f"other v8 parts near the base: {[o.id for o in oth]}")
        print("interference:", interference(ps, oth))
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
