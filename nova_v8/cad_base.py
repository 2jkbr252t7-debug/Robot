"""
NOVA mini v8.1 - BASE (drive module), "MODERNÝ - NIČ NEVIDNO".  Run from the repo root:

    /opt/venv/cad/bin/python -m nova_v8.cad_base            # build + export (build_v8/, manifest "base")
    /opt/venv/cad/bin/python -m nova_v8.cad_base --check    # + STEP round-trip + interference (own + other v8 modules)

Numbers: nova_v8/spec.py (BASE incl. the v8.1 block, TORSO).  Local construction constants are marked below; the
deviations from spec.py are listed in DEVIATIONS (also printed) - spec.py is NOT edited here.

LOOK (v8.1): a closed monolithic white shell 130 x 108 (plan R26, top R8) whose skirt comes down to z 3 all round.
No arches, no openings in the sides or the top except the black turntable seat.  Under the skirt edge: the 360 deg
cyan underglow ring (lights the desk, status light), behind it the slim dark tray.  Wheels Ø34, casters, sensors,
hatches, dock pads, USB-C, button and the speaker micro-perforation are all on the underside.  The only screws
(4x M2.5 shell screws) sit under the battery hatches; the hatches themselves are tool-less.

VISIBLE parts (sub "base", joint "")
  B01      Horny kryt zakladne       white   monolithic shell 130 x 108 x (3..39), wall 2.2, skirt edge R0.6;
                                             Ø83 opening for B09, 4 screw bosses inside (M2.5 from below)
  B02      Spodna vanicka            black   chassis tray: floor z 2.5..4.5 (outline inset 5.2), perimeter wall,
                                             flange over the underglow ring (locates B01, 0.2) + 4 snap barbs,
                                             wheel tubs up to the shell, 2 battery bays + 4 screw pillars, speaker
                                             front chamber + micro-perforation, caster/cliff/dock/USB/button holes
  B-UG     Prstenec podsvietenia     cyan    360 deg PMMA opal light guide, inset 3.0..5.0, z 2.0..6.6, R1 outer-
                                             lower edge (emits down + out onto the desk), snap groove in the inner
                                             face (z 3.6..4.8) for the 4 B02 barbs; LED flex above it
  B04-R/L  Pneumatika                rubber  Ø34 x 10 TPU 85A (or a bought 34 mm N20 wheel) - only the bottom shows
  B05-R/L  Disk kolesa               gloss   5 spokes, D-bore 3 mm for the N20 shaft
  B06      Puzdra gulovych koliesok  black   2 cups pressed into the floor, ball bottom 0.4 above the desk
  B07      Gulky Ø12                 gloss   black POM / Si3N4 balls (no bright dot in the shadow gap)
  B08      Okienka senzorov padu     glass   4 IR-pass windows 7 x 4 (tangential, corners), recessed 0.3
  B09      Sedlo otocneho taniera    black   FIXED black seat ring Ø82/Ø62 flush in the top under the rotating
                                             torso disc T04 (dark 1 mm gap), anti-tilt slide rim 0.5 under T04,
                                             4 tabs clamped under the B01 top wall (no screws)
  B10      Zasuvka USB-C             metal   vertical receptacle on BE2, mouth 0.4 inside the floor (underside rear)
  B11-1/2  Poklop baterie            black   tool-less: 2 hook tongues + 2 snaps, thumb pocket, stepped light-tight
                                             seam; covers the 4 shell screws
  B12      Kontakty dokovania        metal   2 gold pads Ø6 under the rear (dock), pogo pins from the boards
  B13      Tlacidlo                  black   recessed power button cap (underside rear), 1.0 deep
  B17      Zaslepka servisneho otvoru black  flush TPE plug over the Ø7 service hole (M3 yaw screw)
INTERNAL parts (internal=True)
  B14      Nosny mostik pohonu       grey    N20 saddles + straps, tower + walls under the yaw hub, screwed from
                                             ABOVE into 4 tray bosses (no screw through the floor)
  B15      Naboj otacania trupu      grey    FIXED yaw hub: Ø30 spigot for the 6806 inner ring (z 32..39), Ø34 land,
                                             top z 39 carries the STS3215 horn E21H; cable trough, rim under B09
  BM2-R/L  Motor N20 s enkoderom     metal   12 x 10 x (9 + 15) + encoder, D-shaft 3 x 10
  BM4      Drziaky motorov (2x)      metal   bent steel straps, 2x M2 each (from above)
  BM5      Kontakty baterii          metal   + plates and - springs
  BE1-1/2  Clanok 18650              battery Ø18.5 x 65 along X at y -21 / +21, on the hatches
  BE2      DPS nabijania (lava)      pcb     USB-C, 2S charger IP2326, protection, JST battery, left dock pogo
  BE6      DPS tlacidla (prava)      pcb     tact switch for B13, right dock pogo
  BE3      Senzory padu TCRT5000     pcb     4x, clipped to the floor above the windows
  BE4      LED pas podsvietenia      pcb     2.7 mm FPC ring (inset 2.45..5.15) with 24x WS2812B-2020 on top of B-UG
  BE5      Reproduktor Ø28           black   vertical, fires -Y into the sealed front chamber -> floor perforation
  BW1      Slucka kabla otacania     black   Ø6 bundle, 160 deg loop in the B15 trough (fixed exit -20 deg -> T04 slot)

YAW (J1) INTERFACE - shared with nova_v8/cad_torso.py (unchanged from v8.0)
  * The rotating black disc under the torso is the torso's T04 (Ø77 x 2.5, z 40..42.5, housing OD45 for the 6806
    outer ring down to z 31.5, arc cable slot r 23..29 at 155..205 deg).  The base adds the FIXED black seat ring B09
    (Ø82, flush with the top z 39) so the 1 mm gap under T04 reads as one black joint; its slide rim (r 33.5..35.5,
    top z 39.5) stops the torso tilting (0.5 mm under T04) - the thin 6806 does not have to take shock moments.
  * 6806 (torso M21) z 32..39: inner ring on the B15 spigot Ø30 (slip fit + Loctite 641), resting on the Ø34 land.
    STS3215 horn (torso E21H, joint "") on the spigot top z 39, 4x M2.  1x M3x25 from below through the Ø7 service
    hole (closed by B17) -> bridge tower -> B15 -> horn -> servo spline = axial retention of the torso.
  * Load path: T04 -> 6806 -> B15 land -> B14 tower/walls -> tray bosses -> floor.  Tilt: T04 -> B09 rim -> B15 rim.
  * Assembly: B14 into the tray (4x M2.5 from above), motors + straps (M2 from above), B15 on B14 (4x M2.5 from the
    trough), horn on the spigot, cable loop, electronics, cells; B09 laid on the B15 rim; B01 lowered over everything
    (B09 tabs clamped under its top wall), 4x M2.5 from below in the hatch ears; torso with T04 + 6806 lowered onto
    the spigot (spline into the horn), M3x25 from below, plug B17; cells + hatches.  Before B01: the LED flex is
    stuck (its PSA) to the flange underside, then the light guide B-UG is pushed up from below until its inner groove
    snaps over the 4 barbs on the tray wall (straight mid-sides, the ring bows 0.25 mm there; no glue, removable).
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Compound, Cylinder, Edge, Face, Plane, Pos, Rot, Solid, Sphere, Vector,
                       Wire, extrude, fillet, offset, revolve)

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
SKIRT_Z0 = BS["skirt_z0"]                             # 3.0  closed skirt edge, all round
UG_Z0, UG_T0 = BS["underglow"]["z"], BS["underglow"]["inset"]    # 2.0, 3.0
WH = BS["wheel"]
WR, WWID, WX, WY, WZ = WH["d"] / 2, WH["w"], WH["x"], WH["y"], WH["axle_z"]   # 17, 10, 52, 4, 17
CELL_D, CELL_L = BS["batteries"]["d"], BS["batteries"]["len"]
YH = BS["yaw_hub"]
BRG_ID, BRG_OD, BRG_W = YH["bearing"]                 # 6806: 30 / 42 x 7
T_Z0 = S.TORSO["z0"]                                  # 40 torso bottom (T04 underside)
RING_OD = S.TORSO["bottom_plate"]["ring_od"]          # 77 (T04, torso module)

# ---------------------------------------------------------------------------------------------------------
# local construction constants (layout decisions of this module; deviations listed in DEVIATIONS)
# ---------------------------------------------------------------------------------------------------------
CAV_TOP = B_TOP - WALL             # 36.8 inner face of the B01 top wall
SKIRT_R = 0.6                      # crisp skirt edge -> sharp shadow line
# underglow ring + tray (all "t" values = inset from the outer plan outline)
UG_T1, UG_Z1, UG_R = 5.0, 6.6, 1.0  # light guide 2.0 x 4.6, R1 on the outer-lower edge
LED_Z1 = 7.6                       # flex + LEDs on top of the guide (z 6.6..7.6)
TRAY_T0, TRAY_WT = 5.2, 1.2        # tray floor outline / perimeter wall (inner face t 6.4)
TRAY_Z0, FLOOR_TOP = 2.5, 4.5      # floor 2.0, bottom 2.5 above the desk
TRAY_WALL_Z1 = 14.0
FLANGE_T0, FLANGE_Z0, FLANGE_Z1 = 2.4, LED_Z1, 9.2   # locates B01 (0.2) and closes the ring groove from above
FLEX_T0, FLEX_T1 = 2.45, 5.15      # LED flex envelope (2.7 mm FPC) between the guide top and the flange
# B-UG retention (review fix): 4 snap barbs on the tray wall outer face (straight mid-sides, where the ring can bow)
# engage a continuous groove in the inner face of the light guide; ring pushed up from below, no glue, no screws
UG_GROOVE = (3.6, 4.8, 0.35)       # z0, z1, depth into the guide inner face (inset 4.65..5.0)
BARB = dict(z0=3.7, zr=4.2, z1=4.7, h=0.45, L=10.0)   # ramp z0->zr (insertion), flat top z1 (retention), tip inset 4.75
SEAM = 0.45                        # visible seams (hatch, B09, windows)
# wheel tubs (black, internal walls of the tray around each wheel)
TUB_X0, TUB_T = 44.3, 1.2          # inner wall |x| 44.3..45.5
TUB_HW = 21.0                      # void half-length in Y (tyre ±17)
SLOT_X0, SLOT_HW = 45.9, 13.0      # floor slot |x| 45.9..58.6, y WY ± 13
# yaw interface (J1 parts T04 / M21 / E21H are modelled by the torso module)
BRG_Z1 = YH["z_top"]               # 39  bearing top = hub top = horn bottom
BRG_Z0 = BRG_Z1 - BRG_W            # 32
HUB_TOP = BRG_Z1
SPIGOT_R = BRG_ID / 2 - 0.01       # 6806 inner ring seat (slip fit, Loctite 641)
LAND_R = 17.0
HORN_PCD = 14.0
TROUGH_Z0, TROUGH_T = 26.5, 2.0    # B15 trough floor z 26.5..28.5
TROUGH_R, RIM_T, RIM_Z1 = 38.0, 1.5, 35.4      # rim top 0.2 under B09
LOOP_R, LOOP_Z, LOOP_RB = 26.5, 31.6, 3.0
FIX_EXIT = (LOOP_R * math.cos(math.radians(-20)), LOOP_R * math.sin(math.radians(-20)), 4.0)
RISER_XY = (-(23.0 + 29.0) / 2, 0.0)                                   # into the T04 slot r 23..29 at 180 deg
# B09 seat ring
B09_RI, B09_RO, B09_Z0 = 31.0, 41.0, 35.6
B09_TAB_R = 44.0
B09_RIM = (33.5, 35.5, 0.5)
B01_OPEN_R = B09_RO + 0.5          # 0.5 seam
# drive
GB_FACE = 43.5
GB_L, CAN_L = BS["motor"]["gearbox_len"], BS["motor"]["body"][2] - BS["motor"]["gearbox_len"]   # 9, 15
MOT_H, MOT_W = 12.0, 10.0
SHAFT_L = 10.0
BRIDGE_Z0, BRIDGE_PLATE = 7.0, 2.5  # bridge plate z 7..9.5 on 4 tray bosses (screws from above)
BRIDGE_Y = (-5.5, 11.0)
TOWER = dict(x=6.0, y=11.0, cx=3.5, cy=9.5)
HUB_SCREW_Y = 7.5
BRIDGE_SCREWS = [(24.0, -2.5), (-24.0, -2.5), (24.0, 8.0), (-24.0, 8.0)]
# batteries (2 bays, cells on the hatches; no inner wall - the bridge is the inner stop)
CELL_Y, CELL_Z0 = 21.0, FLOOR_TOP + 0.1
BAY_X = 35.5                       # inner end faces |x|
BAY_YI, BAY_YO = 11.5, 30.7        # opening inner edge / outer wall inner face (|y|)
HATCH_YO = 31.0                    # opening outer edge (outer wall overhangs 0.3 -> snap)
BAY_WALL, BAY_Z1 = 1.4, 20.0
PILLAR = dict(x0=BAY_X + BAY_WALL, x1=TUB_X0 + 0.5, hw=3.6, z1=20.0, sx=39.6)   # B01 screw pillars (into the tubs)
HATCH_X = 42.9                     # hatch opening |x| (covers the pillar counterbores r 2.6 at |x| 39.6)
STEP_W, STEP_Z = 0.8, TRAY_Z0 + 1.2   # stepped (light-tight) hatch seam: lower 1.2 mm of the floor cut 0.8 wider
B01_SCREWS = [(sx * PILLAR["sx"], sy * CELL_Y) for sx in (1, -1) for sy in (1, -1)]
# underside items
CASTER_Y = 39.9
CASTER_LIFT = 0.4                 # review fix: balls 0.4 above the desk -> the wheels always carry the load
CUP_R, CUP_Z0, CUP_Z1 = 7.5, 2.8 + CASTER_LIFT, 14.0 + CASTER_LIFT
BALL_R = BS["caster"]["d"] / 2
BALL_Z = BALL_R + CASTER_LIFT      # ball centre
CLIFF_T = 10.0                     # cliff windows on the corner diagonals, 10 mm inside the outline
DOCK_XY = [(-36.0, 41.0), (36.0, 41.0)]
DOCK_D = BS["dock_pads"]["d"]
USB_XY = (-24.0, 40.0)
BTN_XY = (24.0, 40.0)
BOARD_Z0, BOARD_T = 10.25, 1.6     # charger / button boards (USB-C receptacle 7.35 tall below)
BOARD_STANDOFFS = [(-31.0, 45.0), (-14.0, 44.5), (31.0, 45.0), (14.0, 44.5)]
# speaker (front left, vertical, fires -Y into a sealed front chamber)
SPK = dict(x=28.0, z=19.0, y_face=-41.2, d=BS["speaker"]["d"], h=BS["speaker"]["h"])
CH = dict(x0=13.0, x1=43.0, yb=-42.4, z1=34.6, t=1.2)
PERF = dict(x0=16.0, x1=40.0, rows=(-46.3, -44.9, -43.5), pitch=1.6, d=1.0)   # Ø1.0: 46 holes = 36 mm² open
TCRT = (10.4, 5.8, 7.0)
BIG = 400.0

DEVIATIONS = [
    "batérie y ±28 -> ±21 (pri ±28 by šachty zasahovali do guľových koliesok a okraja vaničky; články ležia na "
    "poklopoch, vnútornú stenu šachty nahrádza mostík pohonu)",
    "guľové kolieska y (-40, +44) -> ±39.9 (musia byť vnútri steny vaničky y 47.6 – pás podsvietenia); guľky čierne "
    "POM/Si3N4 namiesto oceľových (v tieňovej škáre nesvietia)",
    "senzory pádu (±52, ±44) -> (±49.1, ±40.4): pôvodná poloha leží v páse podsvietenia / stene vaničky (10 mm od "
    "obrysu na uhlopriečke rohu)",
    "USB-C (-20, 46) -> (-24, 40), tlačidlo (20, 46) -> (24, 40): y 46 je v stene vaničky, x kvôli puzdru kolieska",
    "dokovacie plôšky (±8, 50) -> (±36, 41): y 50 je pod okrajom/prstencom, ±8 koliduje so zadným kolieskom; rozostup "
    "72 mm pomáha dokovaniu",
    "reproduktor (0,-28) naležato -> zvislo vpredu vľavo (x 28, z 19), strieľa dopredu do uzavretej komôrky, ktorá "
    "ústi mikroperforáciou v dne pri prednom okraji (Ø28 sa naležato medzi články, kolieska a senzory nezmestí)",
    "podsvietenie: z=2.0 = spodná (vyžarovacia) plocha svetlovodu, inset 3.0 = jeho vonkajšia plocha; prierez "
    "2.0 × 4.6, vonkajšia spodná hrana R1",
    "čierny prstenec pod trupom: otočný tanier Ø77 ostáva T04 trupu (J1); základňa pridáva pevné čierne sedlo B09 Ø82 "
    "zarovno s vrchom (tmavá 1 mm škára + doraz proti nakloneniu 0.5 mm pod T04)",
    "skrutky: B01 4× M2.5 zdola v ušiach pod poklopmi batérií (bez poklopu nie sú vidieť), mostík zhora do výstupkov "
    "vaničky, poklopy bez skrutiek (2 háčiky + 2 západky); servisný otvor Ø7 (M3 otáčania) zakrýva gumová zátka B17",
    "náboj otáčania ako vo v8.0: čap Ø30 pre vnútorný krúžok 6806 namiesto stĺpika Ø24 zo spec yaw_hub.d",
    "ovládač motorov DRV8833 nie je v základni (TORSO.controller); v základni je nabíjanie 2S IP2326 + ochrana",
    "revízia: guľové kolieska o 0.4 mm vyššie (guľka z 0.4–12.4) – pri 4 tuhých bodoch na z 0 by na nerovnom stole "
    "jedno koleso viselo vo vzduchu; teraz sú kolesá vždy zaťažené a robot sa kolíše max. 0.6° na jedno koliesko",
    "revízia: svetlovod B-UG nemal žiadne uchytenie (len príruba zhora, zospodu nič) – pridané 4 západky na stene "
    "vaničky + drážka 0.35 na vnútornej strane prstenca; tenký 0.4 mm 'lem' príruby odstránený (nevyrobiteľný)",
    "revízia: flex LED BE4 rozšírený z 1.6 na 2.7 mm (inset 2.45–5.15) – LED 2020 má 2.0 mm a na 1.6 mm flex sa nezmestí",
    "revízia: mikroperforácia reproduktora Ø0.8 -> Ø1.0 (46 otvorov, 36 mm² – stále neviditeľné zboku, lepší zvuk)",
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
        if (p1 - corners[(i + 1) % 4][0]).length > 1e-6:
            edges.append(Edge.make_line(p1, corners[(i + 1) % 4][0]))
    return Face(Wire(edges))


def rr_prism(w, d, r, z0, z1, cx_=0.0, cy_=0.0):
    return extrude(rr_face(w, d, r, z0, cx_, cy_), z1 - z0, dir=(0, 0, 1))


def plan(t, z0, z1):
    """Prism of the base plan outline inset by t (rounded rectangle 130 x 108 R26 -> offset inward)."""
    return rr_prism(BW - 2 * t, BD - 2 * t, BR - t, z0, z1)


def rr_rot(w, d, r, z0, z1, x, y, ang):
    return Pos(x, y, 0) * Rot(0, 0, ang) * rr_prism(w, d, r, z0, z1)


def stadium_x(x, y, w, h, z0, z1):
    """Stadium (long axis // X, length w, width h) prism along Z."""
    r = h / 2
    return (bx(x - (w / 2 - r), x + (w / 2 - r), y - r, y + r, z0, z1) + cz(r, z0, z1, x - (w / 2 - r), y)
            + cz(r, z0, z1, x + (w / 2 - r), y)).clean()


def inset_of(x, y):
    """Distance of a plan point from the outer outline, measured inward."""
    hx, hy = BW / 2 - BR, BD / 2 - BR
    dx, dy = abs(x) - hx, abs(y) - hy
    if dx > 0 and dy > 0:
        return BR - math.hypot(dx, dy)
    return min(BW / 2 - abs(x), BD / 2 - abs(y))


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


def cliff_xy():
    """Cliff windows on the line corner centre -> spec point (±52, ±44), moved to CLIFF_T inside the outline."""
    ccx, ccy = BW / 2 - BR, BD / 2 - BR          # 39, 28
    a = math.atan2(44.0 - ccy, 52.0 - ccx)       # direction corner centre -> spec point (52, 44)
    rr = BR - CLIFF_T
    out = []
    for sx, sy in ((1, -1), (-1, -1), (1, 1), (-1, 1)):
        out.append((sx * (ccx + rr * math.cos(a)), sy * (ccy + rr * math.sin(a))))
    return out


CLIFF = cliff_xy()


def corner_frame(x, y):
    """Tangent angle (deg) of the corner arc at a point near a plan corner - the sensors lie tangentially."""
    ccx = math.copysign(BW / 2 - BR, x)
    ccy = math.copysign(BD / 2 - BR, y)
    return math.degrees(math.atan2(y - ccy, x - ccx)) + 90.0


# ---------------------------------------------------------------------------------------------------------
# B01 shell
# ---------------------------------------------------------------------------------------------------------

def cover_cavity():
    """Inner void of B01 (uniform 2.2 wall incl. the top rounding); extends below the open bottom."""
    c = plan(WALL, SKIRT_Z0 - 2.0, CAV_TOP)
    return fillet(c.edges().group_by(Axis.Z)[-1], TOP_R - WALL)


_CAV = {}


def cav():
    if "c" not in _CAV:
        _CAV["c"] = cover_cavity()
        _CAV["in"] = offset(_CAV["c"], amount=-0.8)
    return _CAV["c"], _CAV["in"]


def b01_shell():
    outer = plan(0.0, SKIRT_Z0, B_TOP)
    outer = fillet(outer.edges().group_by(Axis.Z)[-1], TOP_R)
    outer = fillet(outer.edges().group_by(Axis.Z)[0], SKIRT_R)
    shell = outer - cav()[0]
    # opening for the black seat ring B09 (0.5 seam), soft top edge
    shell = shell - cz(B01_OPEN_R, CAV_TOP - 1, B_TOP + 1)
    ed = [e for e in shell.edges() if abs(e.bounding_box().min.Z - B_TOP) < 0.01 and abs(e.bounding_box().max.Z - B_TOP) < 0.01
          and abs(e.bounding_box().size.X - 2 * B01_OPEN_R) < 0.05]
    shell = try_fillet(shell, ed, 0.4, "B09 opening")
    # 4 screw bosses (M2.5 from below through the tray pillars, heads under the battery hatches)
    for (x, y) in B01_SCREWS:
        boss = cz(2.8, PILLAR["z1"], CAV_TOP + 0.5, x, y) - cz(1.05, PILLAR["z1"] - 1, PILLAR["z1"] + 11, x, y)
        shell = shell + boss
    return check("B01", shell)


# ---------------------------------------------------------------------------------------------------------
# B02 tray
# ---------------------------------------------------------------------------------------------------------

def tub_solid(sx):
    t = bx(sx * TUB_X0, sx * (BW / 2 - TRAY_T0), WY - TUB_HW - TUB_T, WY + TUB_HW + TUB_T, FLOOR_TOP - 0.01, B_TOP)
    return t & cav()[0]


def well_void(sx):
    v = bx(sx * (TUB_X0 + TUB_T), sx * (BW / 2 - TRAY_T0 - TRAY_WT), WY - TUB_HW, WY + TUB_HW, FLOOR_TOP, B_TOP)
    return v & cav()[1]


def hatch_shape(sy, grow=0.0, z0=TRAY_Z0 - 1, z1=FLOOR_TOP + 0.01):
    """Battery opening: one plain rounded rectangle under the bay that also covers the 2 shell-screw pillars."""
    yc = sy * (BAY_YI + HATCH_YO) / 2
    w, d = 2 * HATCH_X + 2 * grow, (HATCH_YO - BAY_YI) + 2 * grow
    return rr_prism(w, d, 3.0 + grow, z0, z1, 0, yc)


def battery_bay(sy):
    w = BAY_WALL
    walls = bx(-BAY_X - w, BAY_X + w, sy * BAY_YO, sy * (BAY_YO + w), FLOOR_TOP - 0.01, BAY_Z1)
    for ex in (1, -1):
        walls = walls + bx(ex * BAY_X, ex * (BAY_X + w), sy * BAY_YI, sy * (BAY_YO + w), FLOOR_TOP - 0.01, BAY_Z1)
        p = PILLAR
        pil = bx(ex * p["x0"] - ex * 0.01, ex * p["x1"], sy * CELL_Y - p["hw"], sy * CELL_Y + p["hw"], FLOOR_TOP - 0.01, p["z1"])
        pil = pil - cz(1.45, FLOOR_TOP - 1, p["z1"] + 1, ex * p["sx"], sy * CELL_Y)
        pil = pil - cz(2.6, FLOOR_TOP - 1, FLOOR_TOP + 2.0, ex * p["sx"], sy * CELL_Y)       # screw head counterbore
        walls = walls + pil
    for xx in (-18.0, 18.0):                                                                   # snap windows
        walls = walls - bx(xx - 3.4, xx + 3.4, sy * (BAY_YO - 0.1), sy * (BAY_YO + 0.9), FLOOR_TOP - 0.1, FLOOR_TOP + 1.0)
    return walls


def cliff_clips(x, y):
    ang = corner_frame(x, y)
    L = TCRT[0]
    clips = None
    for s in (-1, 1):
        c = Pos(x, y, 0) * Rot(0, 0, ang) * bx(s * (L / 2 + 0.2), s * (L / 2 + 1.4), -2.0, 2.0, FLOOR_TOP - 0.01,
                                               FLOOR_TOP + 4.0)
        clips = c if clips is None else clips + c
    return clips


def speaker_chamber():
    """Sealed front chamber in front of the speaker: baffle (Ø24 hole), side walls, roof, front wall up to the roof."""
    c = CH
    t = c["t"]
    yf = -(BD / 2 - TRAY_T0 - TRAY_WT)             # tray wall inner face y -47.6
    baffle = bx(c["x0"], c["x1"], c["yb"], c["yb"] + t, FLOOR_TOP - 0.01, c["z1"])
    baffle = baffle - cy(12.0, c["yb"] - 1, c["yb"] + t + 1, SPK["x"], SPK["z"])
    sides = bx(c["x0"], c["x0"] + t, yf - 0.5, c["yb"], FLOOR_TOP - 0.01, c["z1"]) + \
        bx(c["x1"] - t, c["x1"], yf - 0.5, c["yb"], FLOOR_TOP - 0.01, c["z1"])
    roof = bx(c["x0"], c["x1"], yf - 0.5, c["yb"] + t, c["z1"] - t, c["z1"])
    front = bx(c["x0"], c["x1"], -BD / 2, yf + 0.01, TRAY_WALL_Z1 - 0.01, c["z1"]) & plan(TRAY_T0, 0, 50)
    return (baffle + sides + roof + front) & plan(TRAY_T0, 0, 50)


def perf_holes():
    p = PERF
    holes = []
    for j, yy in enumerate(p["rows"]):
        x = p["x0"] + (p["pitch"] / 2 if j % 2 else 0.0)
        while x <= p["x1"] + 1e-6:
            holes.append(cz(p["d"] / 2, TRAY_Z0 - 1, FLOOR_TOP + 1, x, yy))
            x += p["pitch"]
    return holes


def ug_barbs():
    """4 snap barbs on the tray wall outer face (inset TRAY_T0) at the straight mid-sides: lower ramp for pushing the
    light guide up, flat top that sits in the guide's inner groove (0.1 play)."""
    b = BARB
    out = []
    for axis, sgn in (("y", -1), ("y", 1), ("x", -1), ("x", 1)):
        w = (BD / 2 if axis == "y" else BW / 2) - TRAY_T0          # wall outer face distance from the centre
        prof = [(w - 0.05, b["z0"]), (w + b["h"], b["zr"]), (w + b["h"], b["z1"]), (w - 0.05, b["z1"])]
        if axis == "y":
            pts = [Vector(-b["L"] / 2, sgn * u, z) for (u, z) in prof]
            d = (b["L"], 0, 0)
        else:
            pts = [Vector(sgn * u, -b["L"] / 2, z) for (u, z) in prof]
            d = (0, b["L"], 0)
        out.append(extrude(Face(Wire.make_polygon(pts, close=True)), amount=b["L"], dir=d))
    return union(out)


def b02_tray():
    t = plan(TRAY_T0, TRAY_Z0, FLOOR_TOP)
    t = try_fillet(t, t.edges().group_by(Axis.Z)[0], 0.6, "tray bottom edge")
    t = t + (plan(TRAY_T0, FLOOR_TOP - 0.01, TRAY_WALL_Z1) - plan(TRAY_T0 + TRAY_WT, 0, 50))     # perimeter wall
    t = t + (plan(FLANGE_T0, FLANGE_Z0, FLANGE_Z1) - plan(TRAY_T0 + 0.5, 0, 50))                # flange over the ring
    t = t + ug_barbs()                                                                          # B-UG snaps
    for sx in (1, -1):
        t = t + tub_solid(sx)
    for sy in (1, -1):
        t = t + battery_bay(sy)
    for (x, y) in CLIFF:
        t = t + cliff_clips(x, y)
    t = t + speaker_chamber()
    for (x, y) in BRIDGE_SCREWS:                                                          # bridge bosses (blind)
        t = t + (cz(2.8, FLOOR_TOP - 0.01, BRIDGE_Z0, x, y) - cz(1.0, TRAY_Z0 + 0.8, BRIDGE_Z0 + 1, x, y))
    for (x, y) in BOARD_STANDOFFS:
        t = t + (cz(2.2, FLOOR_TOP - 0.01, BOARD_Z0, x, y) - cz(0.8, FLOOR_TOP + 1.5, BOARD_Z0 + 1, x, y))
    # ---- cuts ----
    cuts = []
    for sx in (1, -1):
        cuts.append(well_void(sx))
        x0, x1 = sx * SLOT_X0, sx * (BW / 2 - TRAY_T0 - TRAY_WT)
        cuts.append(rr_prism(abs(x1 - x0), 2 * SLOT_HW, 2.0, TRAY_Z0 - 1, FLOOR_TOP + 0.5, (x0 + x1) / 2, WY))
        cuts.append(cx(2.5, sx * (TUB_X0 - 1), sx * (TUB_X0 + TUB_T + 1), WY, WZ))           # N20 shaft
    for sy in (1, -1):
        cuts.append(hatch_shape(sy))
        cuts.append(hatch_shape(sy, grow=STEP_W, z1=STEP_Z))
        cuts.append(cz(CUP_R + 0.1, TRAY_Z0 - 1, FLOOR_TOP + 1, 0, sy * CASTER_Y))
    for (x, y) in CLIFF:
        cuts.append(rr_rot(7.0 + 2 * SEAM - 0.1, 4.0 + 2 * SEAM - 0.1, 2.0, TRAY_Z0 - 1, FLOOR_TOP + 1, x, y, corner_frame(x, y)))
    for (x, y) in DOCK_XY:
        cuts.append(cz(DOCK_D / 2 + 0.1, TRAY_Z0 - 1, TRAY_Z0 + 1.25, x, y) + cz(1.2, TRAY_Z0, FLOOR_TOP + 1, x, y))
    cuts.append(stadium_x(USB_XY[0], USB_XY[1], 9.6, 3.9, TRAY_Z0 - 1, FLOOR_TOP + 1))
    cuts.append(stadium_x(USB_XY[0], USB_XY[1], 11.4, 5.7, TRAY_Z0 - 1, TRAY_Z0 + 0.4))       # soft recess
    cuts.append(cz(3.0, TRAY_Z0 - 1, FLOOR_TOP + 1, *BTN_XY))
    cuts.append(cz(4.2, TRAY_Z0 - 1, TRAY_Z0 + 0.4, *BTN_XY))
    cuts.append(cz(3.5, TRAY_Z0 - 1, FLOOR_TOP + 1))                                          # service hole (B17)
    cuts.extend(perf_holes())
    t = t - Compound(cuts)
    return check("B02", t)


def b_ug_ring():
    r = plan(UG_T0, UG_Z0, UG_Z1) - plan(UG_T1, UG_Z0 - 1, UG_Z1 + 1)
    ed = [e for e in r.edges() if abs(e.position_at(0.5).Z - UG_Z0) < 0.01
          and abs(inset_of(e.position_at(0.5).X, e.position_at(0.5).Y) - UG_T0) < 0.1]
    r = try_fillet(r, ed, UG_R, "underglow emitting edge")
    gz0, gz1, gd = UG_GROOVE                                   # snap groove in the inner face (barbs on B02)
    r = r - (plan(UG_T1 - gd, gz0, gz1) - plan(UG_T1 + 0.5, gz0 - 1, gz1 + 1))
    return check("B-UG", r)


# ---------------------------------------------------------------------------------------------------------
# small visible parts
# ---------------------------------------------------------------------------------------------------------

def wheel(sx):
    xc = sx * WX
    t = cx(WR, xc - WWID / 2, xc + WWID / 2, WY, WZ)
    t = fillet(t.edges(), 2.5)
    t = t - cx(12.0, xc - 10, xc + 10, WY, WZ)
    for g in (-2.3, 2.3):
        t = t - (cx(WR + 1, xc + g - 0.4, xc + g + 0.4, WY, WZ) - cx(WR - 0.6, xc - 10, xc + 10, WY, WZ))
    hub_w = WWID - 2.0
    h = cx(12.0, xc - hub_w / 2, xc + hub_w / 2, WY, WZ)
    xo = xc + sx * hub_w / 2
    xi = xc - sx * hub_w / 2
    h = h + cx(3.5, xi, xi - sx * 2.0, WY, WZ)
    dish = cx(10.0, xo - sx * 1.6, xo + sx * 1.0, WY, WZ)
    dish = dish - cx(4.2, xo - 3, xo + 3, WY, WZ)
    spokes = None
    for k in range(5):
        sp = Pos(xo, WY, WZ) * Rot(90 + 72 * k, 0, 0) * Pos(0, 0, 7.0) * Box(4.0, 2.2, 6.4)
        spokes = sp if spokes is None else spokes + sp
    spokes = spokes & cx(10.4, xo - sx * 1.6, xo, WY, WZ)
    h = h - (dish - spokes)
    shaft = cx(1.5, xi - sx * 2.1, xc + sx * 1.8, WY, WZ)
    h = h - (shaft - bx(xc - 8, xc + 8, WY - 2, WY + 2, WZ + 1.0, WZ + 2))
    h = h - cx(1.3, xo - sx * 0.6, xo + sx * 1, WY, WZ)
    return check("tyre", t), check("hub", h)


def casters():
    cups, balls = [], []
    for sy in (-1, 1):
        y = sy * CASTER_Y
        cup = cz(CUP_R, CUP_Z0, CUP_Z1, 0, y)
        cup = fillet(cup.edges().group_by(Axis.Z)[0], 0.8)
        cup = cup + bx(-CUP_R - 3.5, CUP_R + 3.5, y - 3, y + 3, FLOOR_TOP, FLOOR_TOP + 1.2)     # ears on the floor
        cup = cup - Pos(0, y, BALL_Z) * Sphere(BALL_R + 0.25)
        cups.append(cup)
        balls.append(Pos(0, y, BALL_Z) * Sphere(BALL_R))
    return check("B06", Compound(cups), multi=True), check("B07", Compound(balls), multi=True)


def cliff_windows():
    ws = []
    for (x, y) in CLIFF:
        a = corner_frame(x, y)
        w = rr_rot(7.0, 4.0, 1.6, TRAY_Z0 + 0.3, FLOOR_TOP + 0.1, x, y, a) + rr_rot(9.4, 6.4, 2.4, FLOOR_TOP, FLOOR_TOP + 0.5, x, y, a)
        ws.append(w)
    return check("B08", Compound(ws), multi=True)


def b09_seat():
    r = cz(B09_RO, B09_Z0, B_TOP) - cz(B09_RI, B09_Z0 - 1, B_TOP + 1)
    top = [e for e in r.edges() if abs(e.bounding_box().min.Z - B_TOP) < 0.01 and abs(e.bounding_box().max.Z - B_TOP) < 0.01]
    r = try_fillet(r, top, 0.4, "B09 top edges")
    ri, ro, h = B09_RIM
    rim = ring_z(ri, ro, B_TOP - 0.3, B_TOP + h)
    rim = try_fillet(rim, [e for e in rim.edges() if abs(e.bounding_box().min.Z - (B_TOP + h)) < 0.01], 0.2, "rim")
    r = r + rim
    for a in (0, 90, 180, 270):
        tab = (Rot(0, 0, a) * bx(B09_RO - 0.1, B09_TAB_R + 1, -6.0, 6.0, B09_Z0, CAV_TOP)) & cz(B09_TAB_R, B09_Z0 - 1, B_TOP)
        r = r + tab
    return check("B09", r)


def b10_usb():
    x, y = USB_XY
    z0 = TRAY_Z0 + 0.4
    s = stadium_x(x, y, 8.94, 3.26, z0, BOARD_Z0)
    s = s - stadium_x(x, y, 8.34, 2.56, z0 - 1, z0 + 6.6)
    s = s + bx(x - 3.3, x + 3.3, y - 0.35, y + 0.35, z0 + 1.0, z0 + 6.7)       # tongue
    return check("B10", s)


def b11_hatch(sy):
    yc = sy * CELL_Y
    h = hatch_shape(sy, grow=STEP_W - SEAM, z0=TRAY_Z0, z1=STEP_Z)
    h = try_fillet(h, h.edges().group_by(Axis.Z)[0], 0.4, "hatch edge")
    h = h + hatch_shape(sy, grow=-SEAM, z0=STEP_Z - 0.01, z1=FLOOR_TOP)
    yi = sy * (BAY_YI + SEAM)                                  # hatch inner edge
    for xx in (-12.0, 12.0):                                   # hook tongues over the floor (hinge side)
        h = h + bx(xx - 2.5, xx + 2.5, sy * (BAY_YI - 1.5), yi + sy * 0.8, FLOOR_TOP, FLOOR_TOP + 1.0)
        h = h + bx(xx - 2.5, xx + 2.5, yi, yi + sy * 0.8, FLOOR_TOP - 0.3, FLOOR_TOP + 0.01)
    yo = sy * (HATCH_YO - SEAM)                                # hatch outer edge
    for xx in (-18.0, 18.0):                                   # snap barbs under the outer bay wall
        h = h + bx(xx - 3.0, xx + 3.0, yo - sy * 1.0, sy * (BAY_YO + 0.7), FLOOR_TOP, FLOOR_TOP + 0.7)
    h = h - stadium_x(21.0, yo - sy * 2.6, 10.0, 3.2, TRAY_Z0 - 1, TRAY_Z0 + 0.5)                 # thumb pocket 0.5
    for dx in (-18.0, 0.0, 18.0):                              # cell cradle ribs
        h = h + (bx(dx - 0.8, dx + 0.8, yc - 6, yc + 6, FLOOR_TOP - 0.01, FLOOR_TOP + 1.2)
                 - cx(CELL_D / 2 + 0.1, -40, 40, yc, CELL_Z0 + CELL_D / 2))
    return check(f"B11 {sy}", h)


def b12_dock():
    pads = []
    for (x, y) in DOCK_XY:
        p = cz(DOCK_D / 2, TRAY_Z0 + 0.2, TRAY_Z0 + 1.2, x, y)
        p = fillet(p.edges().group_by(Axis.Z)[0], 0.3)
        p = p + cz(1.0, TRAY_Z0 + 1.19, FLOOR_TOP + 0.6, x, y)                # rivet stem (pogo target)
        pads.append(p)
    return check("B12", Compound(pads), multi=True)


def b13_button():
    x, y = BTN_XY
    b = cz(2.55, TRAY_Z0 + 1.0, 6.6, x, y) + cz(3.6, FLOOR_TOP + 0.1, FLOOR_TOP + 0.7, x, y)
    b = try_fillet(b, b.edges().group_by(Axis.Z)[0], 0.4, "button")
    return check("B13", b)


def b17_plug():
    p = cz(3.3, TRAY_Z0 + 0.2, FLOOR_TOP, 0, 0) + cz(4.2, FLOOR_TOP, FLOOR_TOP + 0.6, 0, 0)
    p = p - cz(1.8, FLOOR_TOP - 0.5, FLOOR_TOP + 1, 0, 0)
    return check("B17", p)


# ---------------------------------------------------------------------------------------------------------
# internal: drive bridge, yaw hub, motors, electronics
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
    b = bx(-43, 43, BRIDGE_Y[0], BRIDGE_Y[1], z0, zp)
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
    b = b - bx(-tw["cx"], tw["cx"], -tw["cy"], tw["cy"], z0 - 1, top - 2.0)                  # cavity (M3 yaw screw)
    b = b - cz(1.7, top - 3, top + 1)
    for yy in (-HUB_SCREW_Y, HUB_SCREW_Y):
        b = b - cz(1.35, top - 3, top + 1, 0, yy)
    for (x, y) in BRIDGE_SCREWS:                                                            # 4x M2.5 from ABOVE
        b = b - cz(1.4, z0 - 1, zp + 1, x, y) - cone_z(1.4, 2.6, zp - 1.2, zp + 0.001, x, y) - cz(2.6, zp, zp + 20, x, y)
        b = b - cz(1.1, top - 8, top + 1, x + math.copysign(2.5, x), y)                     # pilots for the trough screws
    return check("B14", b)


def hub_screws_xy():
    return [(x + math.copysign(2.5, x), y) for (x, y) in BRIDGE_SCREWS]


def b15_hub():
    """Fixed yaw hub: trough floor (cable loop) + Ø34 column + Ø30 spigot in the 6806 inner ring, top z 39 = E21H."""
    z0, z1 = TROUGH_Z0, TROUGH_Z0 + TROUGH_T
    h = cz(TROUGH_R, z0, z1)
    h = h + ring_z(TROUGH_R - RIM_T, TROUGH_R, z1 - 0.01, RIM_Z1)
    h = h + cz(LAND_R, z1 - 0.01, BRG_Z0)
    sp = cz(SPIGOT_R, BRG_Z0 - 0.01, HUB_TOP)
    sp = try_fillet(sp, sp.edges().group_by(Axis.Z)[-1], 0.4, "spigot lead-in")
    h = h + sp
    h = h - cz(1.7, z0 - 1, HUB_TOP + 1)
    for yy in (-HUB_SCREW_Y, HUB_SCREW_Y):
        h = h - cz(1.0, z0 - 1, z0 + 7.0, 0, yy)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h - cz(0.8, HUB_TOP - 6, HUB_TOP + 1, HORN_PCD / 2 * math.cos(a), HORN_PCD / 2 * math.sin(a))
    for (x, y) in hub_screws_xy():
        hh = cz(1.4, z1 - 4, z1 + 1, x, y) + cone_z(1.4, 2.6, z1 - 1.2, z1 + 0.001, x, y) + cz(2.6, z1, z1 + 2, x, y)
        h = h - hh
    h = h - cz(FIX_EXIT[2], z0 - 1, z1 + 1, FIX_EXIT[0], FIX_EXIT[1])
    rim_top = [e for e in h.edges() if abs(e.bounding_box().min.Z - RIM_Z1) < 0.01 and abs(e.bounding_box().max.Z - RIM_Z1) < 0.01]
    h = try_fillet(h, rim_top, 0.5, "rim top")
    return check("B15", h)


def n20_motor(sx):
    xg0, xg1 = GB_FACE - GB_L, GB_FACE
    xc0 = xg0 - CAN_L
    m = bx(sx * (xg0 + 0.9), sx * (xg1 - 0.9), WY - MOT_W / 2 + 0.4, WY + MOT_W / 2 - 0.4, WZ - MOT_H / 2 + 0.4, WZ + MOT_H / 2 - 0.4)
    for (a, b_) in ((xg0, xg0 + 0.9), (xg1 - 0.9, xg1)):
        m = m + bx(sx * a, sx * b_, WY - MOT_W / 2, WY + MOT_W / 2, WZ - MOT_H / 2, WZ + MOT_H / 2)
    for (yy, zz) in ((WY - 3.8, WZ - 4.8), (WY + 3.8, WZ - 4.8), (WY - 3.8, WZ + 4.8), (WY + 3.8, WZ + 4.8)):
        m = m + cx(0.6, sx * xg0, sx * xg1, yy, zz)
    m = m + cx(2.0, sx * xg1 - sx * 0.01, sx * (xg1 + 0.8), WY, WZ)
    m = m + cx(1.475, sx * (xg1 + 0.8) - sx * 0.01, sx * (xg1 + SHAFT_L), WY, WZ) - \
        bx(sx * (xg1 + 2.0), sx * (xg1 + SHAFT_L + 1), WY - 3, WY + 3, WZ + 1.0, WZ + 3)
    can = cx(MOT_H / 2, sx * xc0, sx * xg0 + sx * 0.01, WY, WZ) & bx(-BIG, BIG, WY - MOT_W / 2, WY + MOT_W / 2, -BIG, BIG)
    m = m + can
    m = m + cx(4.5, sx * (xc0 - 1.0), sx * xc0 + sx * 0.01, WY, WZ)
    m = m + cx(3.0, sx * (xc0 - 3.0), sx * (xc0 - 1.0) + sx * 0.01, WY, WZ)
    m = m + bx(sx * (xc0 - 4.0), sx * (xc0 - 3.0), WY - 5.5, WY + 5.5, WZ - 6.5, WZ + 6.5)
    m = m + bx(sx * (xc0 - 7.0), sx * (xc0 - 4.0), WY - 3.5, WY + 3.5, WZ - 1.5, WZ + 2.0)
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


def cell(sy):
    yc, zc = sy * CELL_Y, CELL_Z0 + CELL_D / 2
    plus = 1 if sy < 0 else -1
    xp = plus * (BAY_X - 0.5)
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
        out.append(bx(plus * (BAY_X - 0.5), plus * BAY_X, yc - 5, yc + 5, zc - 5.5, zc + 5.5))
        xw = -plus * BAY_X
        pl = bx(xw, xw + plus * 0.5, yc - 5, yc + 5, zc - 5.5, zc + 5.5)
        xm = plus * (BAY_X - 0.5 - CELL_L)
        spring = Pos(xw + plus * 0.5, yc, zc) * Rot(0, 90 * plus, 0) * \
            Solid.make_cone(4.0, 2.2, abs(xm - (xw + plus * 0.5)) - 0.05)
        out.append(pl + spring)
    return check("BM5", Compound(out), multi=True)


def board(sx):
    """Rear boards: sx=-1 charger (USB-C, IP2326, protection, JST), sx=+1 button board.  Both carry a dock pogo."""
    z0, z1 = BOARD_Z0, BOARD_Z0 + BOARD_T
    b = rr_prism(30.0, 13.8, 2.0, z0, z1, sx * 25.0, 39.9)
    for (x, y) in BOARD_STANDOFFS:
        if x * sx > 0:
            b = b - cz(1.1, z0 - 1, z1 + 1, x, y)
    dx, dy = DOCK_XY[0 if sx < 0 else 1]
    comps = [b, cz(0.8, FLOOR_TOP + 0.6, z0 + 0.01, dx, dy), cz(1.7, z0 - 2.5, z0 + 0.01, dx, dy)]    # pogo pin + barrel
    if sx < 0:
        comps += [bx(-21.0, -17.0, 36.0, 40.0, z1, z1 + 0.8),          # IP2326
                  bx(-17.0, -12.5, 41.0, 45.5, z1, z1 + 3.0),          # inductor
                  bx(-30.0, -27.0, 36.0, 39.0, z1, z1 + 1.0),          # 2S protection
                  bx(-26.0, -23.0, 41.5, 44.5, z1, z1 + 1.0),          # dual MOSFET
                  bx(-38.0, -33.5, 34.5, 40.5, z1, z1 + 6.0)]          # JST-PH battery
    else:
        x, y = BTN_XY
        comps += [bx(x - 3.0, x + 3.0, y - 3.0, y + 3.0, 6.75, z0 + 0.01),   # tact switch (under the board)
                  cz(1.75, 6.6, 6.76, x, y),                               # plunger
                  bx(30.0, 36.0, 34.5, 38.5, z1, z1 + 4.2)]                # JST-SH to the torso bundle
    return check("BE2" if sx < 0 else "BE6", union(comps))


def cliff_pcbs():
    out = []
    L, Wd, H = TCRT
    for (x, y) in CLIFF:
        ang = corner_frame(x, y)
        zb = FLOOR_TOP + 0.6
        body = bx(-L / 2, L / 2, -Wd / 2, Wd / 2, zb, zb + H)
        for s in (-1, 1):
            body = body - cz(1.4, zb - 0.1, zb + 0.5, s * 2.5, 0)
        pcb = bx(-L / 2, L / 2, -Wd / 2, Wd / 2, zb + H, zb + H + 0.8)
        out.append(Pos(x, y, 0) * Rot(0, 0, ang) * (body + pcb))
    return check("BE3", Compound(out), multi=True)


def led_flex():
    f = plan(FLEX_T0, UG_Z1, LED_Z1) - plan(FLEX_T1, UG_Z1 - 1, LED_Z1 + 1)
    return check("BE4", f)


def speaker():
    x, z, yf, r, hh = SPK["x"], SPK["z"], SPK["y_face"], SPK["d"] / 2, SPK["h"]
    s = cy(r, yf, yf + 1.0, x, z) - cy(r - 1.6, yf - 1, yf + 0.6, x, z)       # frame
    s = s + cy(r - 1.6, yf + 0.5, yf + 1.2, x, z)                             # membrane
    s = s + cy(9.0, yf + 0.9, yf + hh, x, z)                                  # magnet
    s = s + bx(x + 9.0, x + 13.0, yf + 1.0, yf + 2.6, z - 1.2, z + 1.2)       # terminals
    return check("BE5", s)


def cable_loop():
    c = Edge.make_circle(LOOP_RB, Plane(origin=(LOOP_R, 0, LOOP_Z), z_dir=(0, 1, 0)))
    a0 = math.degrees(math.atan2(FIX_EXIT[1], FIX_EXIT[0]))
    arc = Rot(0, 0, a0) * revolve(Face(Wire([c])), Axis.Z, 180.0 - a0)
    fx, fy = FIX_EXIT[0], FIX_EXIT[1]
    down = cz(LOOP_RB, 21.0, LOOP_Z, fx, fy)
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
    t1 = time.time()
    shell = b01_shell()
    print(f"  B01 {time.time() - t1:.1f}s")
    t1 = time.time()
    tray = b02_tray()
    print(f"  B02 {time.time() - t1:.1f}s")
    I = dict(internal=True)
    parts = [
        PartRec("B01", "Horný kryt základne", shell, "white", SUB, "", (0, 0, 70),
                note="monolitický 130×108×(3–39), R26/R8, stena 2.2, lem až po z 3 – bez podbehov, bez otvorov"),
        PartRec("B02", "Spodná vanička", tray, "black", SUB, "", (0, 0, -35),
                note="dno z 2.5–4.5, obvodová stena + príruba nad prstencom (vedie B01) + 4 západky prstenca, vane kolies, šachty batérií"),
        PartRec("B-UG", "Prstenec podsvietenia 360°", b_ug_ring(), "cyan_led", SUB, "", (0, 0, -20),
                note="PMMA opál 2×4.6, inset 3–5, spodná plocha z 2.0, R1 smerom von – svieti na stôl; zacvakne do 4 západiek vaničky"),
        PartRec("B04-R", "Pneumatika pravá", tyres["R"], "rubber", SUB, "", (-40, 0, -45), note="Ø34×10 TPU 85A"),
        PartRec("B04-L", "Pneumatika ľavá", tyres["L"], "rubber", SUB, "", (40, 0, -45), note="Ø34×10 TPU 85A"),
        PartRec("B05-R", "Disk kolesa pravý", hubs["R"], "black_gloss", SUB, "", (-52, 0, -45), note="D otvor 3 mm (N20)"),
        PartRec("B05-L", "Disk kolesa ľavý", hubs["L"], "black_gloss", SUB, "", (52, 0, -45), note="D otvor 3 mm (N20)"),
        PartRec("B06", "Puzdrá guľových koliesok", cups, "black", SUB, "", (0, 0, -60), note="zalisované do dna; guľka 0.4 mm nad stolom (kolesá vždy zaťažené)"),
        PartRec("B07", "Guľky Ø12", balls, "black_gloss", SUB, "", (0, 0, -75), note="čierne POM / Si3N4"),
        PartRec("B08", "Okienka senzorov pádu (4×)", cliff_windows(), "glass", SUB, "", (0, 0, -60),
                note="IR priepustný čierny akrylát 7×4, zapustené 0.3"),
        PartRec("B09", "Sedlo otočného taniera", b09_seat(), "black", SUB, "", (0, 0, 25),
                note="pevný čierny krúžok Ø82/62 zarovno s vrchom, doraz proti nakloneniu 0.5 pod T04, bez skrutiek"),
        PartRec("B10", "Zásuvka USB-C (zospodu)", b10_usb(), "metal", SUB, "", (0, 0, -60), note="nabíjanie 5 V / servis"),
        PartRec("B11-1", "Poklop batérie predný", b11_hatch(-1), "black", SUB, "", (0, 0, -70),
                note="bez skrutiek: 2 háčiky + 2 západky; pod ním skrutky krytu"),
        PartRec("B11-2", "Poklop batérie zadný", b11_hatch(1), "black", SUB, "", (0, 0, -70),
                note="bez skrutiek: 2 háčiky + 2 západky; pod ním skrutky krytu"),
        PartRec("B12", "Kontakty dokovania", b12_dock(), "metal", SUB, "", (0, 0, -60), note="2× Ø6 pozlátené, rozostup 72"),
        PartRec("B13", "Tlačidlo napájania (zospodu)", b13_button(), "black", SUB, "", (0, 0, -60),
                note="zapustené 1 mm – nestlačí sa o stôl"),
        PartRec("B17", "Záslepka servisného otvoru", b17_plug(), "black", SUB, "", (0, 0, -60), note="Ø7, nad skrutkou M3 otáčania"),
        # ---- internal ----
        PartRec("B14", "Nosný mostík pohonu", b14_bridge(), "grey", SUB, "", (0, 0, 10),
                note="PETG; lôžka N20, veža pod nábojom; 4× M2.5 zhora do vaničky", **I),
        PartRec("B15", "Náboj otáčania trupu", b15_hub(), "grey", SUB, "", (0, 0, 40),
                note="PETG; čap Ø30 pre 6806 (z 32–39), unášač E21H, žľab slučky kábla, okraj pod B09", **I),
        PartRec("BM2-R", "Motor N20 s enkodérom pravý", n20_motor(-1), "metal", SUB, "", (-25, 0, 10),
                note="6 V 1:100–1:150, magnetický enkodér", **I),
        PartRec("BM2-L", "Motor N20 s enkodérom ľavý", n20_motor(1), "metal", SUB, "", (25, 0, 10),
                note="6 V 1:100–1:150, magnetický enkodér", **I),
        PartRec("BM4", "Držiaky motorov N20 (2×)", straps(), "metal", SUB, "", (0, 0, 25), note="oceľové, 2× M2 zhora", **I),
        PartRec("BM5", "Kontakty batérií", contacts(), "metal", SUB, "", (0, 0, -20), note="+ plôšky a − pružiny", **I),
        PartRec("BE1-1", "Článok 18650 predný", cell(-1), "battery", SUB, "", (0, 0, -45), **I),
        PartRec("BE1-2", "Článok 18650 zadný", cell(1), "battery", SUB, "", (0, 0, -45), **I),
        PartRec("BE2", "DPS nabíjania (USB-C, 2S)", board(-1), "pcb", SUB, "", (0, 0, 20),
                note="IP2326 + ochrana 2S + JST-PH + pogo doku", **I),
        PartRec("BE6", "DPS tlačidla", board(1), "pcb", SUB, "", (0, 0, 20), note="tlačidlo + pogo doku", **I),
        PartRec("BE3", "Senzory pádu TCRT5000 (4×)", cliff_pcbs(), "pcb", SUB, "", (0, 0, -15), **I),
        PartRec("BE4", "LED pás podsvietenia", led_flex(), "pcb", SUB, "", (0, 0, -10), note="24× WS2812B-2020 na flexe 2.7 mm, prilepený pod prírubou", **I),
        PartRec("BE5", "Reproduktor Ø28", speaker(), "black", SUB, "", (0, -15, 20),
                note="8 Ω 1–2 W, do prednej komôrky -> mikroperforácia v dne", **I),
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
    """Parts of the other v8 modules that can touch the base: try their build(), fall back to their STEP export."""
    import glob
    import importlib
    import json
    from build123d import import_step
    out = []
    try:
        mod = importlib.import_module("nova_v8.cad_torso")
        for p in mod.build():
            if p.shape.bounding_box().min.Z < 60:
                out.append(p)
        print("   torso parts from cad_torso.build()")
        return out
    except Exception as e:  # noqa: BLE001
        print(f"   cad_torso.build() failed ({str(e)[:80]}) -> STEP fallback")
    for fn in sorted(glob.glob(os.path.join(OUT_DIR, "manifest", "*.json"))):
        if os.path.basename(fn) == MANIFEST + ".json":
            continue
        for r in json.load(open(fn)):
            if r["bbox"]["min"][2] > 60:
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


def step_roundtrip(parts):
    from build123d import import_step
    bad = []
    for p in parts:
        s = import_step(os.path.join(OUT_DIR, "step", f"{p.id}.step"))
        v0, v1 = p.shape.volume, s.volume
        ok = all(so.is_valid for so in s.solids()) and abs(v1 - v0) < 1e-3 * max(v0, 1.0) + 0.05
        if not ok:
            bad.append((p.id, round(v0, 2), round(v1, 2)))
    return bad


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
        print("STEP round-trip problems:", step_roundtrip(ps))
        print("own interference:", interference(ps))
        oth = other_v8_parts()
        print(f"other v8 parts near the base: {[o.id for o in oth]}")
        bad = []
        for p in ps:
            for o in oth:
                v = _overlap(p.shape, o.shape)
                if v > 0.3 or v < 0:
                    bad.append((p.id, o.id, round(v, 2)))
        print("cross-module interference:", bad)
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
