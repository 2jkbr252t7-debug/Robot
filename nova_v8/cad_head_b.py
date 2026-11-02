"""
NOVA mini v8.1 - HEAD variant B "kapsula s vizorom" (frameless visor R100), manifest "head_b".
Run from the repo root:  /opt/venv/cad/bin/python -m nova_v8.cad_head_b [--check] [--pose] [--build-others]
Exports STL + STEP + manifest "head_b" into build_v8_var_b/ (never into build/ or build_v8/), plus the laser-cut
data of the visor (HB03F_blank.dxf/.svg, HB03_mould_rib.dxf, HB03_visor.json).

v8.1 review ("MODERNY - NIC NEVIDNO") of the v8.0 head B.  Defects found and fixed:
  * v8.0 tilt servo coaxial on +X was NOT buildable: its gear dome (r 5.9, x 17..20) ran through the 1.5 pocket wall
    (hole r 3.75) and its lower mounting tab (z 116.25) went through the head floor (z 117..119).
    -> B now uses the SAME tilt kit as head A v8.1 (nova_v8/cad_head.py, imported, identical parts): passive M3 pivots
    on the tilt axis (head load never on the servo), MG90S beside the pocket on +X with the shaft at (y 0, z 147),
    1:1 spur pair m1 20T/20T (HB11 on the servo, HB09 sector keyed into the N06 +X horn recess, HB10 on -X).
  * v8.0 display could not be installed: the 86 x 56 board does not pass the visor opening (its top corners lie
    outside the R25.6 opening corners) and from behind the barrel pocket stands in front of it.
    -> FRONT MODULE (like head A): white face part HB04 with the visor HB03 bonded flush on its rebate, the board
    HB13 clamped in the tray HB07 (4x M2 into HB04 bosses, from behind on the bench).  The module slides into the
    monolithic shell HB01 along +Y; its skirt runs inside HB01 with 0.15 clearance (centres the module, closes the
    seam bottom - you never look into the head), 2 magnet pairs at the top + 2x M2 from the UNDERSIDE hold it.
  * v8.0 had a seam + rear cap HB02 with no fastening at all -> HB02 deleted, HB01 is ONE piece (no seam, screw,
    port or vent on the back, top, sides).  The only body seam is the real split face part / shell (0.5, vertical
    plane y -23, behind the visor on the cheeks), plus the 0.6 shadow gap around the visor.
  * no neck-cable path -> cable hole in the pocket ceiling (as head A); no vents -> 5 hidden slots in the pocket
    ceiling (air: pocket mouth -> head -> face seam), the board's microphone / IH08 hears through the same path.
  * visible mic holes in the ears removed; ear rings now really lit: 3 light windows behind the groove + a cup for
    the Ø23 LED PCB HB14 inside.  Camera dot is internal (render-only, optional camera behind the mask).
  * display ribs did not meet the board holes -> tray HB07 (board between front lips and a rear frame).
  * collar N01 touched the underside at tilt +20 / pan >= 60 (0.39 mm) -> shallow spherical scoop R120 x 0.75
    ahead of the neck pocket (across the face seam, seen only from straight below).
  * visor: re-checked - HB03 is an exact cylinder (OCC Geom_CylindricalSurface R102 / R100, radial laser-cut
    edges), STL facets <= 2.6 deg, normal error < 0.7 deg.  A broad grey band in the front view is the
    specular image of the renderer's large FILL light (right of the camera, ~56 deg) in a mirror-gloss R100
    cylinder - it is physics, not faceting (see the report printed by __main__ / open issues).

Visor (unchanged, manufacturable): ONE single-curvature piece, smoked PMMA 2 mm (outer R102 / inner R100), laser
cut flat 99 x 60 (R25 top / R12 bottom, concentric with the R32 / R19 head corners) and heat-bent over a R100 former
(Ø200 PVC "KG DN200" pipe offcut or MDF ribs), black mask inside outside the display window (77 x 50 R6 developed).
Bonded with VHB 0.25 on the 2.4 mm rebate of HB04, 0.6 shadow gap, flush with the skin.  Touch is NOT usable on
head B (curved visor 0.6 .. 10.3 mm in front of the flat LCD) - voice / ToF interaction only.

Body: front-view silhouette 110 x 74 (R32 top / R19 bottom) along Y with a variable back loop R26 -> R16,
INTERSECT plan prism (front arc R102 + R18 plan corners), whole front loop R6: one G1 capsule, y -40.5 .. +31.

Parts (sub "head_b"; J3 = head tilt about X through y 0 z 127; J2 = pan stage)
  HB01     Obal hlavy               white      ONE piece y -22.75 .. +31, wall 2.0: barrel pocket 37.2 x 37.9 R12 (front
                                               wall moved back 2.1 for the board connectors), ceiling z 144.5, cable
                                               hole + 5 hidden vent slots, thrust pads, 2 pivot bosses (M3 pilots on
                                               the tilt axis), servo rails (+X, servo slides in from the front),
                                               gear slot, flush ear grooves with 3 light windows + LED cups, 2 roof
                                               blocks with magnets, 2 floor pads with flush counterbores
  HB03     Vizor                    glass      smoked PMMA 2.0, R102 / R100 cylinder, 96 x 60 in the front view
  HB03E    Obsah displeja - oci     eye        RENDER-ONLY pills 10.5 x 17.5 on the visor
  HB04     Celny diel               white      face part y -40.5 .. -23.25 (seam 0.5 to HB01): visor opening (0.6
                                               gap) + 2.4 rebate (VHB), skirt 1.6 x 2.6 into HB01, 4 bosses for HB07
  HB05-R/L LED kruzok ucha          cyan_led   flush light-guide rings Ø23 / Ø17, 0.25 below the skin
Internal (internal=True)
  HB03C    Okienko kamery           black_gloss RENDER-ONLY optional camera dot (behind the mask)
  HB03F    Rozvinuty prirez vizora  glass      flat blank 99 x 60 x 0.1 0.6 mm in front of the visor apex (laser data)
  HB07     Drziak displeja          grey       PETG tray: front lips (LCD border, behind the mask), rear frame,
                                               4x M2 into HB04, 2 top lugs with magnets, 2 bottom lugs (underside M2)
  HB09     Ozubeny segment naklonu  grey       J2: = H09 (20T m1 sector keyed into the N06 +X horn recess)
  HB10     Puzdro capu naklonu      grey       J2: = H10 (-X end)
  HB11     Koliesko serva naklonu   grey       J3: = H11 (20T m1 on the MG90S spline)
  HB12     Servo naklonu MG90S      servo      J3: = E32 / IH04 (shaft y 0 z 147 parallel to X, case up)
  HB13     Displej ESP32-S3 3.5"    display    LCD + board (nova_v8/cad_internals IH01-IH03 models, moved to B)
  HB14-R/L DPS ucha                 pcb        Ø23 x 1.6, 6x WS2812B-2020 under the light windows
  HB15-R/L Cap naklonu M3x12        metal      = M31 (DIN 912 pivots)
  HB16-1..4 Magnet Ø6x3 N52         metal      2 in the HB07 lugs, 2 in the HB01 roof blocks (0.2 gap)
  HB17-R/L Skrutka M2x6 zospodu     metal      DIN 7985, heads flush in the HB01 underside

Assembly: (1) HB09/HB10 on the barrel ends (neck finished).  (2) MG90S + HB11 slid into the HB01 rails from the
front opening, 1x M2 stop screw; ear PCBs into the cups, rings pressed in from outside.  (3) HB01 lowered over the
barrel, HB11 meshes radially with HB09.  (4) M3 pivots from inside through the front opening.  (5) Front module on the
bench: visor bonded into HB04 (VHB), board laid into HB04 face down, HB07 screwed on (4x M2 from behind), harness
plugged.  (6) module pushed into HB01 (+Y) until the magnets click, head tilted up: 2x M2 from below.
FDM (PETG): HB01 front rim on the bed (tree supports under the roof/ceiling, removed through the front), HB04 seam
face on the bed (supports under the rebate), HB07 flat.  Outside sanded + primer + satin white.

Deviations from nova_v8/spec.py HEAD (variant A numbers, B is its own shape): w 110 (A 106), front-view corners
R32 / R19, depth y -40.5 .. +31, ear rings flush Ø23 / Ø17 (no discs); barrel pocket 37.2 x 37.9 (spec 36 x 40:
+0.6 per side for the HB09/HB10 discs as head A, front wall 2.1 further back for the board connectors);
tilt servo NOT coaxial (same reasoning as head A).  Head bottom z 117, top z 191, tilt axis, ceiling z 144.5 per spec.
"""
from __future__ import annotations

import copy
import json
import math
import os
import sys
import time

from build123d import (Axis, Box, BuildSketch, Circle, Compound, Cylinder, Edge, ExportDXF, ExportSVG, GeomType,
                       Locations, Mode, Plane, Pos, Rectangle, RectangleRounded, Rot, ShapeList, SlotOverall, Solid,
                       Sphere, Vector, Wire, extrude, fillet)
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCP.Geom import Geom_CylindricalSurface
from OCP.gp import gp_Ax3, gp_Dir, gp_Pnt
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Solid
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import spec as S8  # noqa: E402
from nova_v8 import head_b as HBC  # noqa: E402  (concept head B: generic helpers reused)
from nova_v8 import cad_head as HA  # noqa: E402  (head A v8.1: the shared tilt kit)
from nova_v8.head_b import (check, cyl_x, edges_where, retry, single, slab_y, try_fillet)  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8_var_b")
SUB = "head_b"
MANIFEST = "head_b"

HD, NK, DSP = S8.HEAD, S8.NECK, S8.DISPLAY
Z0, Z1, ZC = HD["z0"], HD["z1"], HD["zc"]                 # 117 .. 191, centre 154
HH = Z1 - Z0                                              # 74
TILT_Y, TILT_Z = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]  # 0, 127
EAR, EYE, CAM = HD["ear"], HD["eyes"], HD["camera"]
DISP_W, DISP_H, DISP_T = DSP["outline"]                   # 86 x 56 x 6
ACT_W, ACT_H = DSP["active"]                              # 73.44 x 48.96

# ---- local construction constants (variant B only; not shared dimensions) ------------------
W = 110.0                  # head width
R_TOP, R_BOT = 32.0, 19.0  # front-view corners
R_BACK_TOP, R_BACK_BOT = 26.0, 16.0   # variable back loop
R_FRONT = 6.0              # 3D round of the whole front loop (visor stays 1 mm inside its tangent line)
R_PF = 18.0                # plan corner: front arc -> side
X_PS = W / 2 + 5.0         # plan-prism side lines outside the head (no coincident faces)
WALL = 2.0

VIS_T = 2.0                            # smoked PMMA 2 mm (alt. PC 1.0 + 1.1 mm black VHB on the same rebate)
R_OUT = 102.0                          # outer radius of the visor = front surface of the head
R_IN = R_OUT - VIS_T                   # 100 = mould radius (Ø200 PVC KG pipe)
R_MID = R_OUT - VIS_T / 2              # 101 neutral radius -> development of the flat blank
VIS = dict(w=99.0, h=60.0, r_top=25.0, r_bot=12.0, zc=ZC)   # developed outline (u along R_MID, z)
GAP = 0.6                              # shadow gap visor <-> face part
TAPE = 0.25                            # VHB on the rebate
LEDGE_W, LEDGE_OUT = 2.4, 1.4          # rebate: 2.4 under the visor edge, 1.4 beyond the opening
D_LEDGE0, D_LEDGE1 = 1.5, 3.9          # rebate band depth below the skin (merges into the 2.0 wall)

DISP_Y0 = -28.2                        # LCD front face (board side edge x +-43 -> 0.58 behind the R100 inner face)
DISP_CR = 3.0                          # assumed corner radius of the board outline
DISP_SIDE_CLR = 0.5
DISP_RELIEF = 0.4                      # relief in HB04 around the board (front + sides)
YC = DISP_Y0 - DISP_SIDE_CLR + math.sqrt(R_IN ** 2 - (DISP_W / 2) ** 2)   # plan centre of the visor cylinder
Y_FRONT = round(YC - R_OUT - 0.04, 1)  # -40.5 visor apex (x = 0)
YC = Y_FRONT + R_OUT                   # 61.5
Y_BACK = 31.0
PCB_BACK = DISP_Y0 + 4.6               # -23.6 (LCD 3.0 + 0.2 + PCB 1.4, cad_internals IH01/IH02)
COMP_BACK = PCB_BACK + 4.2             # -19.4 tallest board parts (JST 1.25)

# ---- face part / shell split (v8.1: the only body seam) -------------------------------------
Y_FS = -23.0                           # vertical parting plane face part HB04 / shell HB01
SEAM = 0.5                             # as head A / torso
SKIRT_CLR, SKIRT_T, SKIRT_L = 0.15, 1.6, 2.6
SK_D0, SK_D1 = WALL + SKIRT_CLR, WALL + SKIRT_CLR + SKIRT_T   # skirt band depth 2.15 .. 3.75 below the skin

# ---- barrel pocket + tilt kit (= head A v8.1) -----------------------------------------------
PK_W, PK_R, PK_TOP, PK_WALL = HA.PK_W, HA.PK_R, HA.PK_TOP, HA.PK_WALL    # 37.2, R12, ceiling 144.5, wall 2.0
PK_YF, PK_YB = -17.9, 20.0             # pocket inner front / back wall (A: -20 / +20); front moved back 2.1 so the
PK_D = PK_YB - PK_YF                   # board connectors (USB-C to y -20.3) clear the pocket front wall (-19.9)
PK_CY = (PK_YB + PK_YF) / 2
PK_X_IN, PK_X_OUT = HA.PK_X_IN, HA.PK_X_OUT     # 18.6 / 20.6

# ---- front module retention (magnets top, 2x M2 from the underside) --------------------------
Y_STOP = -19.7                         # tray top lug rear face = HB01 roof block front face
MAG_X, MAG_Z = 30.0, 182.8
MAG_R, MAG_T, MAG_POCKET_R, MAG_RECESS = HA.MAG_R, HA.MAG_T, HA.MAG_POCKET_R, HA.MAG_RECESS
MAG_LUG_Z = (179.5, 186.0)             # skirt inner face at x 30 lies at z ~186.5
SCR_X, SCR_Y = 26.0, -17.0             # underside screws beside the pocket (flat underside |x| < 36)
SCR_CB_R, SCR_CB_D, SCR_HOLE_R, PILOT_R = HA.SCR_CB_R, HA.SCR_CB_D, HA.SCR_HOLE_R, HA.PILOT_R
PAD_X0, PAD_X1, PAD_Y0, PAD_Y1 = 22.5, 29.5, -20.1, -14.0
PAD_Z1 = 121.0                         # floor pad top; tray bottom lug z 121.05 .. 125.0
LUG_Z0, LUG_Z1 = PAD_Z1 + 0.05, 125.0

# ---- tray HB07 (holds the board in the face part) -------------------------------------------
TR_Y1 = PCB_BACK + 2.0                 # -21.6 rear frame face
LIP_Y0, LIP_Y1 = DISP_Y0 - 0.85, DISP_Y0 - 0.05   # front lips (0.05 felt gap to the LCD glass)
LIP_X = 33.0                           # lips / bars only where the visor is >= 2.4 mm in front of them
TOP_BAR, TOP_LIP = (182.3, 184.0), 179.4          # LCD top 181.5, mask window top 179.0
BOT_BAR, BOT_LIP = (124.0, 125.7), 128.6          # LCD bottom 126.5, mask window bottom 129.0
TRAY_BOSSES = [(-20.0, 184.8), (20.0, 184.8), (-36.0, 123.4), (36.0, 123.4)]   # HB04 bosses, M2 x 6 from behind
BOSS_R = 2.2
TR_WIN = (76.0, 44.0, 5.0)             # rear frame window = component field of the board

# ---- ears -------------------------------------------------------------------------------------
RING_OD, RING_ID = EAR["ring_od"], EAR["ring_id"]          # 23 / 17
EAR_Y, EAR_Z = EAR["y"], EAR["z"]                          # -3, 154
RING_DEPTH, RING_GAP, RING_RECESS = 1.4, 0.15, 0.25
WIN_RO, WIN_RI = 10.9, 9.1             # light windows through the 0.5 wall left behind the groove
CUP_RO, CUP_RI, CUP_X0 = 13.3, 11.75, 49.0
EPCB_X1, EPCB_T = 51.4, 1.6            # ear PCB outer face |x| (LEDs 0.85 on top, under the windows)

# ---- neck clearance: at tilt +20 (looking down) and pan >= 60 the N01 collar edge rises 0.39 above the head
#      underside at y -24.5 .. -22.2 (across the face seam) -> shallow spherical scoop R120, 0.75 deep (Ø27 footprint,
#      edge slope < 7 deg), only visible from straight below; floor >= 1.25 (head A uses a chamfer here)
SCOOP_R, SCOOP_D, SCOOP_Y = 120.0, 0.75, -23.4

CAM_Z, CAM_D = CAM["z"], CAM["d"]      # 180.5, 2.8
WINDOW_MARGIN, WINDOW_R = 0.5, 6.0     # mask window = active area + 0.5, corners R6


# ===========================================================================================
# small helpers
# ===========================================================================================

def bx(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def cyl_y(r, y0, y1, x, z):
    return HBC.cyl_y(r, y0, y1, x, z)


def cyl_z(r, z0, z1, x, y):
    return HA.cyl_z(r, z0, z1, x, y)


def union(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out + s
    return out


def solid1(s):
    sols = s.solids()
    return sols[0] if len(sols) == 1 else s


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    with BuildSketch(Plane.XY.offset(z0)) as s:
        with Locations((cx, cy)):
            RectangleRounded(w, d, r)
    return extrude(s.sketch, z1 - z0)


def rr_dist_xy(x, y, w, d, r, cy=0.0):
    qx = abs(x) - (w / 2 - r)
    qy = abs(y - cy) - (d / 2 - r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


# ===========================================================================================
# developed outline on the visor cylinder (u = arc length at R_MID, z)
# ===========================================================================================

def dev_dims(g=0.0):
    return VIS["w"] + 2 * g, VIS["h"] + 2 * g, VIS["r_top"] + g, VIS["r_bot"] + g


def cyl_pt(u, z, r):
    th = u / R_MID
    return Vector(r * math.sin(th), YC - r * math.cos(th), z)


def dev_wire(g, r, n=15):
    """Closed wire on the cylinder of radius r whose development is the visor outline grown by g.
    Same (theta, z) outline at every radius -> lofting two of them gives radial side faces."""
    w, h, rt, rb = dev_dims(g)
    zc = VIS["zc"]
    k = r / R_MID
    corners = [(w / 2 - rt, h / 2 - rt, 0, rt), (-(w / 2 - rt), h / 2 - rt, 90, rt),
               (-(w / 2 - rb), -(h / 2 - rb), 180, rb), (w / 2 - rb, -(h / 2 - rb), 270, rb)]
    edges = []
    for i, (cu, cz, a0, rad) in enumerate(corners):
        angs = [math.radians(a0 + 90.0 * j / (n - 1)) for j in range(n)]
        pts = [cyl_pt(cu + rad * math.cos(t), zc + cz + rad * math.sin(t), r) for t in angs]
        tans = []
        for t in (angs[0], angs[-1]):
            th = (cu + rad * math.cos(t)) / R_MID
            du, dz = -math.sin(t), math.cos(t)
            tans.append(Vector(du * k * math.cos(th), du * k * math.sin(th), dz))
        edges.append(Edge.make_spline(pts, tangents=tans, parameters=[j / (n - 1) for j in range(n)]))
        if i == 0:
            a = w / 2 - rt
            edges.append(Edge.make_three_point_arc(cyl_pt(a, zc + h / 2, r), cyl_pt(0, zc + h / 2, r),
                                                   cyl_pt(-a, zc + h / 2, r)))
        elif i == 1:
            edges.append(Edge.make_line(cyl_pt(-w / 2, zc + h / 2 - rt, r), cyl_pt(-w / 2, zc - h / 2 + rb, r)))
        elif i == 2:
            a = w / 2 - rb
            edges.append(Edge.make_three_point_arc(cyl_pt(-a, zc - h / 2, r), cyl_pt(0, zc - h / 2, r),
                                                   cyl_pt(a, zc - h / 2, r)))
        else:
            edges.append(Edge.make_line(cyl_pt(w / 2, zc - h / 2 + rb, r), cyl_pt(w / 2, zc + h / 2 - rt, r)))
    return Wire(edges)


_CUT = {}


def cyl_cap(wire, r):
    """Exact trimmed face of the visor cylinder (radius r) bounded by a dev_wire."""
    surf = Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, YC, 0), gp_Dir(0, 0, 1), gp_Dir(0, -1, 0)), r)
    fx = ShapeFix_Face(BRepBuilderAPI_MakeFace(surf, wire.wrapped, True).Face())
    fx.Perform()
    return fx.Face()


def dev_cutter(g=0.0, r_hi=R_OUT + 8.0, r_lo=R_OUT - 14.0):
    """Radial-edged solid: the visor outline (grown by g) swept radially from r_lo to r_hi."""
    key = (round(g, 4), r_hi, r_lo)
    if key not in _CUT:
        w, h, rt, rb = dev_dims(g)
        area = w * h - 2 * (1 - math.pi / 4) * (rt * rt + rb * rb)
        v_est = area / R_MID * (r_hi ** 2 - r_lo ** 2) / 2
        w_hi, w_lo = dev_wire(g, r_hi), dev_wire(g, r_lo)
        lf = Solid.make_loft([w_hi, w_lo], ruled=True)      # 8 ruled (radial) side faces, no caps
        sew = BRepBuilderAPI_Sewing(1e-4)
        for f in lf.faces():
            sew.Add(f.wrapped)
        sew.Add(cyl_cap(w_hi, r_hi))
        sew.Add(cyl_cap(w_lo, r_lo))
        sew.Perform()
        shell = TopoDS.Shell(TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL).Current())
        fx = ShapeFix_Solid(BRepBuilderAPI_MakeSolid(shell).Solid())
        fx.Perform()
        best = Solid(fx.Solid())
        if not best.is_valid or abs(best.volume - v_est) > 0.01 * v_est:
            raise RuntimeError(f"dev_cutter {g}: invalid ({best.volume:.0f} vs estimate {v_est:.0f})")
        _CUT[key] = best
    return _CUT[key]


def ring(r_out, r_in, h=90.0):
    return Pos(0, YC, ZC) * (Cylinder(r_out, h) - Cylinder(r_in, h + 2))


def dev_face_2d(g=0.0):
    """Developed outline as a flat face on Plane.XY (x = u, y = z - zc) - the laser-cut blank."""
    w, h, rt, rb = dev_dims(g)
    with BuildSketch() as s:
        Rectangle(w, h)
        fillet(s.vertices().filter_by(lambda v: v.Y > 0), rt)
        fillet(s.vertices().filter_by(lambda v: v.Y < -h / 2 + 1e-6), rb)
    return s.sketch.faces()[0]


def window_dims():
    """Mask window developed on the blank: active area seen straight on, projected onto the inner face."""
    hx = ACT_W / 2 + WINDOW_MARGIN
    u = math.asin(hx / R_IN) * R_MID
    return 2 * u, ACT_H + 2 * WINDOW_MARGIN, WINDOW_R


# ===========================================================================================
# capsule body
# ===========================================================================================

def silhouette_prism(y0, y1):
    """Front-view outline W x HH (top corners R_TOP, bottom R_BOT) extruded along +Y from y0 to y1."""
    with BuildSketch() as s:
        Rectangle(W, HH)
        fillet(s.vertices().filter_by(lambda v: v.Y > 0), R_TOP)
        fillet(s.vertices().filter_by(lambda v: v.Y < -HH / 2 + 1e-6), R_BOT)
    pl = Plane(origin=(0, y0, ZC), x_dir=(1, 0, 0), z_dir=(0, -1, 0))   # local y -> global +Z
    face = pl.location * s.sketch.faces()[0]
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def back_loop_fillet(sil):
    """Variable-radius round of the back loop: R_BACK_TOP on the top edges, R_BACK_BOT on the bottom
    edges, linear along the short flat side lines (OCC per-edge radius laws)."""
    loop = sil.edges().group_by(Axis.Y)[-1]
    zt, zb = Z1 - R_TOP, Z0 + R_BOT
    try:
        mk = BRepFilletAPI_MakeFillet(sil.wrapped)
        mk.Add(R_BACK_BOT, loop[0].wrapped)
        n = mk.NbEdges(1)
        cls = []
        for i in range(1, n + 1):
            zm = Edge(mk.Edge(1, i)).position_at(0.5).Z
            cls.append("T" if zm > zt - 0.1 else ("B" if zm < zb + 0.1 else "S"))
        for i, c in enumerate(cls, start=1):
            if c == "T":
                mk.SetRadius(R_BACK_TOP, 1, i)
            elif c == "B":
                mk.SetRadius(R_BACK_BOT, 1, i)
            elif cls[(i - 2) % n] == "T":
                mk.SetRadius(R_BACK_TOP, R_BACK_BOT, 1, i)
            else:
                mk.SetRadius(R_BACK_BOT, R_BACK_TOP, 1, i)
        mk.Build()
        out = Solid(mk.Shape())
        if mk.IsDone() and out.is_valid and 0.8 * sil.volume < out.volume < sil.volume:
            return out
    except Exception as ex:  # pragma: no cover
        print(f"  (variable back loop failed: {ex})")
    print("  (variable back loop rejected -> constant R_BACK_BOT)")
    return fillet(loop, R_BACK_BOT)


def capsule_body():
    sil = back_loop_fillet(silhouette_prism(Y_FRONT - 6, Y_BACK))
    with BuildSketch(Plane.XY.offset(Z0 - 10)) as sk:
        with Locations((0, YC)):
            Circle(R_OUT)
        with Locations((0, (Y_FRONT - 5 + Y_BACK + 10) / 2)):
            Rectangle(2 * X_PS, Y_BACK + 10 - (Y_FRONT - 5), mode=Mode.INTERSECT)
        fillet(sk.vertices().filter_by(lambda v: v.Y < 0), R_PF)
    plan = extrude(sk.sketch, HH + 20)
    body = check("body", retry(lambda: sil & plan, "body"))
    front_loop = edges_where(body, lambda p: p.Y < Y_BACK - R_BACK_TOP - 1)
    front_loop = ShapeList([e for e in front_loop if e.geom_type != GeomType.LINE])
    body = fillet(front_loop, R_FRONT)
    return check("body", body)


class Skin(HBC.Skin):
    """Concept Skin (cached inward offsets, bands) on the v8 body."""

    def __init__(self):  # noqa: D107 - parent builds the concept body, we build ours
        self.body = capsule_body()
        self._off = {}

    def band_in(self, d0, d1, region, label="band"):
        """Skin layer between depth d0 and d1 INSIDE region: (outer & region) - (inner & region).  Local booleans:
        the full-body difference of two offsets fails sporadically in OCC ('Null TopoDS_Shape')."""
        def mk():
            a = (self.body if d0 == 0 else self.inner(d0)) & region
            b = self.inner(d1) & region
            return a - b
        return retry(mk, label, tries=6)


# ===========================================================================================
# purchased / bought-in parts
# ===========================================================================================

def board_hb13():
    """ESP32-S3 3.5" board: the detailed cad_internals models (IH01 LCD, IH02 board, IH03 module) moved to the B
    position (LCD front y -28.2).  Fallback: 86 x 56 x 6 envelope + 4.2 connector field."""
    try:
        from nova_v8 import cad_internals as CI
        dy = DISP_Y0 - CI.Y_DSP0
        parts = [Pos(0, dy, 0) * s for s in (CI.ih01_lcd(), CI.ih02_board(), CI.ih03_s3_module())]
        return Compound(parts)
    except Exception as ex:  # noqa: BLE001
        print(f"  (cad_internals board model not available: {ex!r} -> envelope)")
        e = HBC.rr_prism_y(DISP_W, DISP_H, DISP_CR, DISP_Y0, PCB_BACK, cz=ZC)
        return e + HBC.rr_prism_y(66.0, 40.0, 2.0, PCB_BACK - 0.01, COMP_BACK, cz=ZC)


def board_envelope(g=0.0, y1=PCB_BACK):
    return HBC.rr_prism_y(DISP_W + 2 * g, DISP_H + 2 * g, DISP_CR + g, DISP_Y0 - g, y1, cz=ZC)


def ear_pcb(sx):
    x1 = sx * EPCB_X1
    p = cyl_x(RING_OD / 2, x1 - sx * EPCB_T, x1, EAR_Y, EAR_Z)
    leds = []
    for k in range(6):
        a = math.radians(30 + 60 * k)
        cy, cz = EAR_Y + 10.0 * math.cos(a), EAR_Z + 10.0 * math.sin(a)
        leds.append(Pos(x1 + sx * 0.42, cy, cz) * Rot(math.degrees(a), 0, 0) * Box(0.85, 2.0, 2.2))
    p = p + HA.bx(x1 - sx * EPCB_T, x1 - sx * (EPCB_T + 1.2), EAR_Y - 2.0, EAR_Y + 2.0, EAR_Z - 9.5, EAR_Z - 7.5)
    return union([p] + leds)


def magnet(sx, in_tray):
    if in_tray:
        y0, y1 = Y_STOP - MAG_RECESS - MAG_T, Y_STOP - MAG_RECESS
    else:
        y0, y1 = Y_STOP + MAG_RECESS, Y_STOP + MAG_RECESS + MAG_T
    return cyl_y(MAG_R, y0, y1, sx * MAG_X, MAG_Z)


def screw_m2_under(sx):
    """DIN 7985 M2 x 6 pan head (Ø4.0 x 1.6), head flush in the HB01 underside counterbore."""
    zh = Z0 + SCR_CB_D - 1.6
    x, y = sx * SCR_X, SCR_Y
    head = cyl_z(2.0, zh, zh + 1.6, x, y)
    head = head - bx(x - 0.3, x + 0.3, y - 1.4, y + 1.4, zh - 0.1, zh + 0.8) - \
        bx(x - 1.4, x + 1.4, y - 0.3, y + 0.3, zh - 0.1, zh + 0.8)
    shank = cyl_z(1.0, zh + 1.59, zh + 1.6 + 6.0, x, y)
    return head + shank


# ===========================================================================================
# visible parts
# ===========================================================================================

def neck_scoop():
    return Pos(0, SCOOP_Y, Z0 + SCOOP_D - SCOOP_R) * Sphere(SCOOP_R)


def ear_annulus(ro, ri, side=0):
    """Annulus along X through the ear centre; side -1 / +1 keeps only that half (x < 0 / x > 0)."""
    x0, x1 = {0: (-70, 70), -1: (-70, -1), 1: (1, 70)}[side]
    return cyl_x(ro, x0, x1, EAR_Y, EAR_Z) - cyl_x(ri, x0 - 1, x1 + 1, EAR_Y, EAR_Z)


def build_visor():
    v = retry(lambda: ring(R_OUT, R_IN) & dev_cutter(0.0), "visor")
    return check("HB03", single(v, "HB03"), 8000)   # sharp laser-cut edges, deburred by hand


def build_face(sk: Skin):
    """HB04: white face part in front of the seam plane, visor opening + rebate, skirt into HB01, tray bosses."""
    face = sk.band_in(0, WALL, slab_y(Y_FRONT - 5, Y_FS - SEAM / 2), "face wall")
    # skirt = straight Y-prism of the HB01 rim opening (-0.15 / -1.75): on the cheeks the skin widens toward the back
    # (R18 plan blend), a skirt that followed the skin could not be pulled out of HB01 along -Y
    # (sections of the 3D inner offsets at the rim plane: B-spline edges, STEP-safe - a 2D offset() gives offset
    # curves that the STEP writer heals destructively)
    y_rim = Y_FS + SEAM / 2
    ya, yb = Y_FS - 2.5, Y_FS + SKIRT_L

    def prism(depth):
        sl = retry(lambda: sk.inner(depth) & slab_y(y_rim - 0.01, y_rim + 0.01), "rim slice")
        f = sl.faces().sort_by(Axis.Y)[0]
        return extrude(Pos(0, ya - f.center().Y, 0) * f, amount=yb - ya, dir=(0, 1, 0))
    skirt = retry(lambda: prism(SK_D0) - prism(SK_D1), "skirt prism")
    skirt = retry(lambda: skirt & sk.inner(1.0), "skirt under the skin")
    face = retry(lambda: face + skirt, "face + skirt")
    face = retry(lambda: face - dev_cutter(GAP), "visor opening")
    # rebate (ledge) behind the shadow gap: 1.65 under the visor, merges into the wall outside
    ledge = sk.band_in(D_LEDGE0, D_LEDGE1, dev_cutter(GAP + LEDGE_OUT), "ledge band")
    ledge = retry(lambda: ledge - dev_cutter(-LEDGE_W), "ledge inner edge")
    ledge = retry(lambda: ledge - (ring(R_OUT + 1, R_OUT - (VIS_T + TAPE)) & dev_cutter(GAP)), "ledge seat")
    notch = Pos(0, Y_FRONT + 4, (CAM_Z - 2.2 + 195) / 2) * Box(12, 14, 195 - (CAM_Z - 2.2))
    ledge = retry(lambda: ledge - (notch & dev_cutter(GAP)), "camera notch")     # optional camera behind the mask
    face = retry(lambda: face + ledge, "add ledge")
    # bosses for the 4 tray screws (end faces 0.05 in front of the tray frame)
    body = sk.body
    for (x, z) in TRAY_BOSSES:
        web = bx(x - 1.0, x + 1.0, -30.0, PCB_BACK - 0.05, z, Z1 + 1) if z > ZC else \
            bx(x - 1.0, x + 1.0, -30.0, PCB_BACK - 0.05, Z0 - 1, z)
        boss = (cyl_y(BOSS_R, -30.0, PCB_BACK - 0.05, x, z) + web) & body
        face = retry(lambda: face + boss, "tray boss")
        face = retry(lambda: face - cyl_y(0.8, PCB_BACK - 5.5, PCB_BACK + 1, x, z), "tray boss pilot")
    # relief around the board (front + sides 0.4)
    face = retry(lambda: face - board_envelope(DISP_RELIEF, PCB_BACK + 0.5), "board relief")
    face = retry(lambda: face - neck_scoop(), "neck clearance scoop")
    return check("HB04", single(face, "HB04"), 4000)


def build_shell(sk: Skin):
    """HB01: the monolithic shell behind the seam plane with the head A tilt kit interface."""
    body = sk.body
    h01 = sk.band_in(0, WALL, slab_y(Y_FS + SEAM / 2, Y_BACK + 5), "HB01 wall")

    # ---- barrel pocket: walls, thrust pads, pivot bosses (head A geometry, front wall moved back) ----
    pw, pd, pr, ptop = PK_W, PK_D, PK_R, PK_TOP
    pocket_out = rr_prism_z(pw + 2 * PK_WALL, pd + 2 * PK_WALL, pr + PK_WALL, Z0 - 1, ptop + PK_WALL, cy=PK_CY)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 4.0)
    pocket_in = rr_prism_z(pw, pd, pr, Z0 - 5, ptop, cy=PK_CY)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 3.0)
    h01 = retry(lambda: h01 + (pocket_out & body), "pocket walls")
    h01 = retry(lambda: h01 - pocket_in, "pocket")
    e_pk = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and abs(rr_dist_xy(p.X, p.Y, pw, pd, pr, PK_CY)) < 0.02)
    h01 = try_fillet(h01, e_pk, 1.0, "pocket rim")
    feats = []
    for sx in (1, -1):
        feats.append(cyl_x(5.0, sx * HA.PAD_X, sx * (PK_X_IN + 0.3), TILT_Y, TILT_Z))                 # thrust pad
        feats.append(cyl_x(HA.PIVOT_BOSS_R, sx * (PK_X_OUT - 0.5), sx * HA.PIVOT_BOSS_X1, TILT_Y, TILT_Z))
        feats.append(bx(sx * (PK_X_OUT - 0.5), sx * HA.PIVOT_BOSS_X1, -1.0, 1.0, Z0 + 0.5, TILT_Z) & body)
    h01 = retry(lambda: h01 + union(feats), "pivot bosses")

    # ---- tilt-servo rails (+X, open to the front): lower rail on the pocket wall, upper rail from the roof ----
    rx0, rx1 = HA.TAB_X0 - HA.RAIL_CLR, HA.TAB_X1 + HA.RAIL_CLR
    w_in, w_out = rx0 - HA.RAIL_WALL, rx1 + 3.0
    tz0 = HA.TAB_Z0 - HA.RAIL_CLR
    lo = bx(w_in, w_out, HA.RAIL_Y0, HA.RAIL_Y1, tz0 - HA.RAIL_WALL, HA.SV_Z0 - 0.3) + \
        bx(PK_X_OUT - 0.5, w_in + 0.01, HA.RAIL_Y0, HA.RAIL_Y1, tz0 - HA.RAIL_WALL, tz0)
    lo = lo - bx(rx0, rx1, HA.RAIL_Y0 - 1, HA.RAIL_STOP, tz0, HA.SV_Z0 + 1)
    lo = lo - cyl_y(PILOT_R, HA.RAIL_Y0 - 0.5, HA.RAIL_Y0 + 6.0, rx1 + 1.25, HA.TAB_Z0 + 2.45)   # M2 stop screw
    up = bx(w_in, w_out, HA.RAIL_Y0, HA.RAIL_Y1, HA.SV_Z1 + 0.3, Z1 + 1) & body
    up = up - bx(rx0, rx1, HA.RAIL_Y0 - 1, HA.RAIL_STOP, HA.SV_Z1 - 1, HA.TAB_Z1 + HA.RAIL_CLR)
    h01 = retry(lambda: h01 + lo + up, "servo rails")

    # ---- gear slot: HB11 + spline/dome path from the front opening to the mesh position ----
    sz = HA.SERVO_Z
    slot_a = bx(HA.SPL_TIP_X - 2.7, PK_X_IN + 0.01, -24.0, 11.6, sz - 11.5, sz + 11.6)
    slot_b = bx(HA.H11_X1, HA.SV_TOP_X + 0.3, -24.0, HA.MS_DOME_R + 0.5, sz - HA.MS_DOME_R - 0.5,
                sz + HA.MS_DOME_R + 0.5)
    h01 = retry(lambda: h01 - slot_a - slot_b, "gear slot")

    # ---- neck cable hole + hidden vent slots in the pocket ceiling ----
    h01 = retry(lambda: h01 - bx(-4.5, 4.5, 3.0, 15.0, ptop - 1, ptop + PK_WALL + 1), "cable hole")
    vents = union([bx(x - HA.VENT_W / 2, x + HA.VENT_W / 2, HA.VENT_Y[0], HA.VENT_Y[1], ptop - 1, ptop + PK_WALL + 1)
                   for x in HA.VENT_X])
    h01 = retry(lambda: h01 - vents, "ceiling vents")
    for sx in (1, -1):
        h01 = retry(lambda: h01 - cyl_x(HA.M3_PILOT_R, sx * (HA.PAD_X - 1), sx * (HA.PIVOT_BOSS_X1 + 1),
                                        TILT_Y, TILT_Z), "M3 pilot")

    # ---- front module retention: 2 roof blocks with magnets + 2 floor pads (flush counterbores) + stop ribs ----
    feats = []
    for sx in (1, -1):
        x0, x1 = sorted((sx * (MAG_X - 4.0), sx * (MAG_X + 4.0)))
        feats.append(bx(x0, x1, Y_STOP, Y_STOP + 5.2, MAG_LUG_Z[0], Z1 + 1) & body)
        x0, x1 = sorted((sx * PAD_X0, sx * PAD_X1))
        feats.append(bx(x0, x1, PAD_Y0, PAD_Y1, Z0 + 1.0, PAD_Z1) & body)
        feats.append(bx(x0, x1, PAD_Y1, PAD_Y1 + 1.5, Z0 + 1.0, LUG_Z1 - 1.0) & body)    # Y stop for the lug
    h01 = retry(lambda: h01 + union(feats), "retention blocks")
    for sx in (1, -1):
        h01 = retry(lambda: h01 - cyl_y(MAG_POCKET_R, Y_STOP - 0.01, Y_STOP + MAG_RECESS + MAG_T + 0.05,
                                        sx * MAG_X, MAG_Z), "magnet pocket")
        h01 = retry(lambda: h01 - cyl_z(SCR_CB_R, Z0 - 1, Z0 + SCR_CB_D, sx * SCR_X, SCR_Y)
                    - cyl_z(SCR_HOLE_R, Z0 - 1, PAD_Z1 + 1, sx * SCR_X, SCR_Y), "underside screw hole")

    # ---- flush ear rings: groove 1.5, 3 light windows through the rest of the wall, cup for the LED PCB ----
    groove = sk.band_in(0, RING_DEPTH + 0.1, ear_annulus(RING_OD / 2 + RING_GAP, RING_ID / 2 - RING_GAP), "ear groove")
    h01 = retry(lambda: h01 - groove, "ear grooves")
    for sx in (1, -1):        # windows only near the side walls (|x| > 47): from the groove bottom inward
        win = cyl_x(WIN_RO, sx * 47.0, sx * 70.0, EAR_Y, EAR_Z) - cyl_x(WIN_RI, sx * 46.0, sx * 71.0, EAR_Y, EAR_Z)
        for a in (90, 210, 330):
            win = win - Pos(0, EAR_Y, EAR_Z) * Rot(a, 0, 0) * bx(-75, 75, -0.8, 0.8, 0, WIN_RO + 1)   # 3 bridges
        win = retry(lambda: sk.inner(RING_DEPTH) & win, "light windows")
        h01 = retry(lambda: h01 - win, "ear light windows")
    for sx in (1, -1):
        cup = (cyl_x(CUP_RO, sx * CUP_X0, sx * (W / 2 + 1), EAR_Y, EAR_Z)
               - cyl_x(CUP_RI, sx * (CUP_X0 - 1), sx * (W / 2 + 2), EAR_Y, EAR_Z)) & body
        h01 = retry(lambda: h01 + cup, "ear cup")
    ring_l = single(sk.band_in(RING_RECESS, RING_DEPTH, ear_annulus(RING_OD / 2, RING_ID / 2, +1), "HB05-L"), "HB05-L")
    ring_r = single(sk.band_in(RING_RECESS, RING_DEPTH, ear_annulus(RING_OD / 2, RING_ID / 2, -1), "HB05-R"), "HB05-R")
    h01 = retry(lambda: h01 - neck_scoop(), "neck clearance scoop")
    e_cb = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and
                       abs(math.hypot(abs(p.X) - SCR_X, p.Y - SCR_Y) - SCR_CB_R) < 0.02)
    h01 = HA.try_chamfer(h01, e_cb, 0.3, "counterbore edge")
    h01 = single(h01, "HB01")
    return check("HB01", h01, 30000), check("HB05-R", ring_r, 50), check("HB05-L", ring_l, 50)


# ===========================================================================================
# internal parts
# ===========================================================================================

def tray_hb07(sk: Skin):
    """PETG tray: rear frame on the PCB back border, front lips on the LCD border (behind the visor mask),
    side stops, 4 screw ears (into HB04), 2 magnet lugs (top), 2 lugs for the underside screws."""
    y0, y1 = PCB_BACK, TR_Y1
    plate = HBC.rr_prism_y(DISP_W, DISP_H, DISP_CR, y0, y1, cz=ZC)
    ww, wh, wr = TR_WIN
    plate = plate - HBC.rr_prism_y(ww, wh, wr, y0 - 1, y1 + 1, cz=ZC)
    lx = LIP_X
    feats = [plate,
             bx(-lx, lx, LIP_Y0, y1, TOP_BAR[0], TOP_BAR[1]), bx(-lx, lx, LIP_Y0, LIP_Y1, TOP_LIP, TOP_BAR[0] + 0.01),
             bx(-lx, lx, LIP_Y0, y1, BOT_BAR[0], BOT_BAR[1]), bx(-lx, lx, LIP_Y0, LIP_Y1, BOT_BAR[1] - 0.01, BOT_LIP)]
    for sx in (1, -1):
        feats.append(bx(sx * (DISP_W / 2 + 0.3), sx * (DISP_W / 2 + 1.3), PCB_BACK - 0.8, y1, 140.0, 168.0))  # side stop
        feats.append(bx(sx * (DISP_W / 2 - 3.0), sx * (DISP_W / 2 + 0.31), PCB_BACK - 0.01, y1, 140.0, 168.0))
        x0, x1 = sorted((sx * (MAG_X - 4.0), sx * (MAG_X + 4.0)))
        feats.append(bx(x0, x1, y0, Y_STOP, MAG_LUG_Z[0], MAG_LUG_Z[1]))                     # magnet lug
        x0, x1 = sorted((sx * PAD_X0, sx * PAD_X1))
        feats.append(bx(x0, x1, y0, PAD_Y1, LUG_Z0, LUG_Z1))                                 # underside-screw lug
        feats.append(bx(x0, x1, y0, y1, LUG_Z0, BOT_BAR[1]))                                 # its web to the frame
    for (x, z) in TRAY_BOSSES:
        zw = (z - 4.0, z) if z > ZC else (z, z + 4.0)                                         # screw ear + web
        feats.append(cyl_y(BOSS_R + 0.3, y0, y1, x, z) + bx(x - 1.6, x + 1.6, y0, y1, zw[0], zw[1]))
    t = union(feats)
    # clear the top bar / lips around the top bosses and the optional camera
    for (x, z) in TRAY_BOSSES:
        if z > ZC:
            t = t - bx(x - BOSS_R - 0.3, x + BOSS_R + 0.3, LIP_Y0 - 1, PCB_BACK - 0.01, TOP_BAR[0], Z1)
    t = t - bx(-5.0, 5.0, LIP_Y0 - 1, LIP_Y1 + 0.01, TOP_LIP - 1, TOP_BAR[0])
    t = t - board_envelope(0.15, PCB_BACK)                         # board pocket (0.15 around the LCD / PCB)
    for (x, z) in TRAY_BOSSES:
        t = t - cyl_y(1.2, y0 - 1, y1 + 1, x, z)                    # M2 clearance
    for sx in (1, -1):
        t = t - cyl_z(PILOT_R, LUG_Z0 - 1, LUG_Z1 - 0.8, sx * SCR_X, SCR_Y)
        t = t - cyl_y(MAG_POCKET_R, Y_STOP - MAG_RECESS - MAG_T - 0.05, Y_STOP + 0.01, sx * MAG_X, MAG_Z)
    t = retry(lambda: t & sk.inner(SK_D1 + 0.25), "tray inside the skirt")
    return check("HB07", solid1(t), 1500)


def camera_dot():
    """Render-only lens: very low spherical cap on the visor apex line (x 0 -> visor surface y = Y_FRONT)."""
    r, sag = CAM_D / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_FRONT - sag + rs, CAM_Z) * Sphere(rs)
    lens = retry(lambda: sph & HBC.cyl_y(r, Y_FRONT - 1.0, Y_FRONT + 0.05, 0.0, CAM_Z), "lens")
    return check("HB03C", lens)


def eyes():
    """Render-only spec eyes (10.5 x 17.5 pills) following the R102 visor, 0.02..0.17 mm in front of it."""
    sh = Pos(0, YC, EYE["z"]) * Cylinder(R_OUT + 0.17, 40) - Pos(0, YC, EYE["z"]) * Cylinder(R_OUT + 0.02, 41)
    out = None
    for sx in (-1, 1):
        with BuildSketch(HBC.plane_y(Y_FRONT - 6, sx * EYE["x"], EYE["z"])) as s:
            SlotOverall(EYE["h"], EYE["w"], rotation=90)
        pill = extrude(s.sketch, 12)
        e = retry(lambda: pill & sh, "eye")
        out = e if out is None else retry(lambda: out + e, "eyes")
    return check("HB03E", out)


def flat_blank():
    """Developed visor (unbent) 0.1 mm thick, standing 0.6 mm in front of the visor apex."""
    f = dev_face_2d(0.0)
    pl = Plane(origin=(0, Y_FRONT - 0.6, VIS["zc"]), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return check("HB03F", extrude(pl.location * f, amount=0.1, dir=(0, -1, 0)))


# ===========================================================================================

def build():
    t0 = time.time()
    sk = Skin()
    h01, ring_r, ring_l = build_shell(sk)
    print(f"  HB01 {time.time() - t0:.1f}s")
    h04 = build_face(sk)
    h03 = build_visor()
    h07 = tray_hb07(sk)
    print(f"  HB04/HB03/HB07 {time.time() - t0:.1f}s")
    # independent copies (the STEP writer may touch edges shared through the common offsets)
    h01, h04, ring_r, ring_l, h03, h07 = (copy.deepcopy(x) for x in (h01, h04, ring_r, ring_l, h03, h07))
    # offset() leaves OffsetSurface faces -> exact B-splines (the STEP writer heals such faces in place)
    h01, h04, ring_r, ring_l, h07 = (HA.step_safe(n, x) for n, x in (("HB01", h01), ("HB04", h04), ("HB05-R", ring_r),
                                                                    ("HB05-L", ring_l), ("HB07", h07)))
    J = "J3"
    U, F = 40.0, 45.0          # head lift / front module pull-out in exploded views
    wb, hb, rt, rb = dev_dims(0.0)
    P = [
        PartRec("HB01", "Obal hlavy", h01, "white", SUB, J, (0, 0, U),
                note="biela kapsula 110×74 (spredu R32/R19, vzadu R26→R16), stena 2.0, JEDEN KUS bez zadného krytu "
                     "(žiadna škára, skrutka ani otvor vzadu/hore/na bokoch), kapsa valca 37.2×37.9 R12 so skrytými "
                     "vetracími drážkami a otvorom pre kábel, 2 nálitky čapov M3, lišty serva, drážky uší so "
                     "svetelnými okienkami, 2 bloky s magnetmi, 2 podložky skrutiek zospodu"),
        PartRec("HB04", "Čelný diel", h04, "white", SUB, J, (0, -F, U),
                note="biely čelný diel pred škárou 0.5 (rovina y −23): otvor vizora s tieňovou škárou 0.6 a "
                     "drážkou 2.4 (VHB 0.25), lem 1.6 zasunutý 2.6 mm do HB01 (zatvára dno škáry), 4 nálitky pre "
                     "držiak displeja"),
        PartRec("HB03", "Vizor", h03, "glass", SUB, J, (0, -F - 20, U),
                note=f"dymové PMMA {VIS_T:.1f} mm ohnuté za tepla na valec R{R_IN:.0f} (vonkajší R{R_OUT:.0f}), "
                     f"jednoduché zakrivenie, čelný pohľad 96×60, vnútri čierna maska mimo okna displeja, "
                     f"zalícovaný s povrchom"),
        PartRec("HB03E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -F - 28, U),
                note="len objekt pre render: oči 10.5×17.5 z displeja svietia cez tónovaný vizor"),
        PartRec("HB03C", "Okienko kamery", camera_dot(), "black_gloss", SUB, J, (0, -F - 28, U), internal=True,
                note="len objekt pre render: voliteľná kamera za čírym bodom v maske (zvonku nevidno)"),
        PartRec("HB05-R", "LED krúžok ucha pravý", ring_r, "cyan_led", SUB, J, (-28, 0, U),
                note="lícujúci svetlovod Ø23/Ø17 v boku hlavy (0.25 pod povrchom), svieti cez 3 okienka v stene"),
        PartRec("HB05-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (28, 0, U),
                note="lícujúci svetlovod Ø23/Ø17 v boku hlavy (0.25 pod povrchom), svieti cez 3 okienka v stene"),
        PartRec("HB03F", "Rozvinutý prírez vizora", flat_blank(), "glass", SUB, J, (0, -F - 45, U), internal=True,
                note=f"plochý prírez na laser {wb:.1f}×{hb:.1f} mm, rohy R{rt:.0f} hore / R{rb:.0f} dole, "
                     f"rozvinutý na neutrálnom polomere R{R_MID:.0f}; ohnúť okolo zvislej osi na formu R{R_IN:.0f}"),
        PartRec("HB07", "Držiak displeja", h07, "grey", SUB, J, (0, -F + 22, U), internal=True,
                note="PETG: predné lišty na okraji LCD (za maskou vizora), zadný rám na okraji DPS, 4× M2×6 do HB04, "
                     "2 horné oká s magnetmi, 2 spodné oká pre skrutky zospodu"),
        PartRec("HB09", "Ozubený segment náklonu", HA.barrel_disc(1, True), "grey", SUB, "J2", (12, 0, 0),
                internal=True, note="= H09 hlavy A: 20z m1 ±63°, kríž do vybrania valca N06 (+X), 2× M2"),
        PartRec("HB10", "Púzdro čapu náklonu", HA.barrel_disc(-1, False), "grey", SUB, "J2", (-12, 0, 0),
                internal=True, note="= H10 hlavy A: kríž bez zubov na −X konci valca"),
        PartRec("HB11", "Koliesko serva náklonu", HA.servo_gear_h11(), "grey", SUB, J, (12, -10, U + 40),
                internal=True, note="= H11 hlavy A: 20z m1 na drážkovaní MG90S, prevod 1:1"),
        PartRec("HB12", "Servo náklonu MG90S", HA.servo_e32(), "servo", SUB, J, (22, -10, U + 40), internal=True,
                note="MG90S / SCS0009 22.8×12.2×22.7, hriadeľ (y 0, z 147) ∥ X, telo hore vedľa kapsy, zasunie sa "
                     "spredu do líšt HB01 (rovnaká súprava náklonu ako hlava A)"),
        PartRec("HB13", "Displej ESP32-S3 3.5\" (doska)", board_hb13(), "display", SUB, J, (0, -F + 10, U),
                internal=True, note=DSP["board"] + " – 86×56, LCD 0.6–10.3 mm za vizorom (dotyk sa nepoužíva)"),
    ]
    for sx, side, nm in ((-1, "R", "pravá"), (1, "L", "ľavá")):
        P.append(PartRec(f"HB14-{side}", f"DPS ucha {nm}", ear_pcb(sx), "pcb", SUB, J, (sx * 20, 0, U),
                         internal=True, note="Ø23×1.6, 6× WS2812B-2020 pod svetelnými okienkami, vlepená do misky"))
    for sx, side, nm in ((-1, "R", "pravý"), (1, "L", "ľavý")):
        P.append(PartRec(f"HB15-{side}", f"Čap náklonu M3×12 {nm}", HA.pin_m31(sx), "metal", SUB, J,
                         (sx * 18, 0, U), internal=True, note="= M31: DIN 912 M3×12 do pilotu v HB01, beží v Ø3.2 valca"))
    for i, (sx, in_tray) in enumerate(((-1, True), (1, True), (-1, False), (1, False))):
        P.append(PartRec(f"HB16-{i + 1}", f"Magnet Ø6×3 N52 ({'HB07' if in_tray else 'HB01'}, "
                                          f"{'pravý' if sx < 0 else 'ľavý'})", magnet(sx, in_tray), "metal", SUB, J,
                         (0, -F + 22 if in_tray else 0, U), internal=True,
                         note="neodýmový disk Ø6×3 N52 vlepený (CA), páry sa priťahujú cez medzeru 0.2"))
    for sx, side, nm in ((-1, "R", "pravá"), (1, "L", "ľavá")):
        P.append(PartRec(f"HB17-{side}", f"Skrutka M2×6 zospodu {nm}", screw_m2_under(sx), "metal", SUB, J,
                         (0, 0, U - 15), internal=True,
                         note="DIN 7985 M2×6, hlava zapustená v HB01 zospodu (Ø4.4×1.7), do oka HB07 – zvonku nevidno"))
    for p in P:
        check(p.id, p.shape)
    print(f"  build {time.time() - t0:.1f}s")
    return P


# ===========================================================================================
# manufacturing data (laser blank, mould rib, numbers)
# ===========================================================================================

def visor_numbers():
    ww, wh, wr = window_dims()
    wb, hb, rt, rb = dev_dims(0.0)
    hx_act = ACT_W / 2
    y_in_act = YC - math.sqrt(R_IN ** 2 - hx_act ** 2)
    y_in_brd = YC - math.sqrt(R_IN ** 2 - (DISP_W / 2) ** 2)
    th = wb / 2 / R_MID
    return dict(
        material="dymové (tónované) PMMA 2.0 mm, priepustnosť ~25-35 %; alt. PC 0.75-1.0 mm za studena",
        thickness=VIS_T, r_outer=R_OUT, r_inner_mould=R_IN, r_neutral=R_MID,
        blank=dict(w=round(wb, 2), h=round(hb, 2), r_top=rt, r_bottom=rb),
        bend_angle_deg=round(math.degrees(wb / R_MID), 1),
        front_view=dict(w=round(2 * R_OUT * math.sin(th), 2), h=hb, sagitta=round(R_OUT * (1 - math.cos(th)), 2)),
        window=dict(w=round(ww, 2), h=round(wh, 2), r=wr, zc=ZC, note="na príreze: stred okna = stred prírezu"),
        camera_dot=dict(u=0.0, dz_from_centre=round(CAM_Z - VIS["zc"], 2), d_clear=3.5,
                        note="voliteľné: bez kamery maska bez bodu"),
        mount="lepené páskou VHB 0.25 do drážky 2.4 čelného dielu HB04, tieňová škára 0.6, zalícované s povrchom",
        display_gap_center=round(DISP_Y0 - (Y_FRONT + VIS_T), 2),
        display_gap_active_edge=round(DISP_Y0 - y_in_act, 2),
        display_gap_board_edge=round(DISP_Y0 - y_in_brd, 2),
        cold_bend_ratio_pc_1mm=round(R_IN / 1.0, 0), cold_bend_ratio_pc_075=round(R_IN / 0.75, 0),
    )


def export_manufacturing(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    blank = dev_face_2d(0.0)
    ww, wh, wr = window_dims()
    with BuildSketch() as s:
        RectangleRounded(ww, wh, wr)
    win = s.sketch.faces()[0]
    cam = Pos(0, CAM_Z - VIS["zc"]) * Circle(1.75).faces()[0]
    axis = Edge.make_line((0, -VIS["h"] / 2 - 6), (0, VIS["h"] / 2 + 6))
    hb = VIS["h"]
    # mould rib (MDF 12 mm, 5 pieces at 25 mm pitch) - arc R_IN over a 150 mm chord + 25 mm base
    c = 75.0
    sag = R_IN - math.sqrt(R_IN ** 2 - c ** 2)
    top = Edge.make_three_point_arc((-c, 0), (0, sag), (c, 0))
    rib = Wire([top, Edge.make_line((c, 0), (c, -25)), Edge.make_line((c, -25), (-c, -25)),
                Edge.make_line((-c, -25), (-c, 0))])

    dxf = ExportDXF()
    dxf.add_layer("REZ_PRIREZ").add_layer("MASKA_OKNO").add_layer("KAMERA_BOD_VOLITELNE").add_layer("OS_OHYBU")
    dxf.add_shape(blank.edges(), layer="REZ_PRIREZ")
    dxf.add_shape(win.edges(), layer="MASKA_OKNO")
    dxf.add_shape(cam.edges(), layer="KAMERA_BOD_VOLITELNE")
    dxf.add_shape(axis, layer="OS_OHYBU")
    dxf.write(os.path.join(out_dir, "HB03F_blank.dxf"))
    rdx = ExportDXF()
    rdx.add_layer("REZ_REBRO_FORMY")
    rdx.add_shape(rib, layer="REZ_REBRO_FORMY")
    rdx.write(os.path.join(out_dir, "HB03_mould_rib.dxf"))
    svg = ExportSVG(margin=5)
    svg.add_layer("rez", line_color="red", line_weight=0.2)
    svg.add_layer("maska", line_color="black", line_weight=0.15)
    svg.add_layer("os", line_color="blue", line_weight=0.1)
    svg.add_shape(blank.edges(), layer="rez")
    svg.add_shape(win.edges(), layer="maska")
    svg.add_shape(cam.edges(), layer="maska")
    svg.add_shape(axis, layer="os")
    svg.write(os.path.join(out_dir, "HB03F_blank.svg"))
    nums = visor_numbers()
    nums["rib"] = dict(chord=2 * c, sag=round(sag, 2), base=25.0, count="5x MDF 12 mm, rozostup 25 mm")
    with open(os.path.join(out_dir, "HB03_visor.json"), "w") as f:
        json.dump(nums, f, ensure_ascii=False, indent=1)
    return nums


# ===========================================================================================
# checks
# ===========================================================================================

def bb_overlap(a, b, tol=0.0):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.min.X > bb.max.X + tol or bb.min.X > ba.max.X + tol or ba.min.Y > bb.max.Y + tol or
                bb.min.Y > ba.max.Y + tol or ba.min.Z > bb.max.Z + tol or bb.min.Z > ba.max.Z + tol)


def common_vol(a, b):
    if not bb_overlap(a, b):
        return 0.0
    try:
        c = a & b
        return 0.0 if c is None else c.volume
    except Exception:  # noqa: BLE001
        return -1.0


# intended overlaps: M3 pivots thread-form into the HB01 pilots, HB11 bore pressed onto the spline, the underside
# M2 screws thread-form into the HB07 lug pilots; render-only parts are skipped
FITS = {("HB01", "HB15-R"), ("HB01", "HB15-L"), ("HB11", "HB12"), ("HB07", "HB17-R"), ("HB07", "HB17-L")}
RENDER_ONLY = {"HB03C", "HB03E", "HB03F"}


def interference(parts, others=(), tol=0.5, skip=FITS):
    allp = [p for p in list(parts) + list(others) if p.id not in RENDER_ONLY]
    own = {p.id for p in parts}
    bad = []
    for i in range(len(allp)):
        for j in range(i + 1, len(allp)):
            a, b = allp[i], allp[j]
            if a.id not in own and b.id not in own:
                continue
            if (a.id, b.id) in skip or (b.id, a.id) in skip:
                continue
            v = common_vol(a.shape, b.shape)
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


# head A parts and the head-A-positioned internals are replaced by this variant
REPLACED_PREFIX = ("H0", "H1", "E3", "M3", "IH0", "IW1-3")


def other_parts(build_others=False):
    """Body parts of the other v8 modules (build_v8/manifest): STEP import of their last export, or their build()."""
    import importlib
    from build123d import import_step
    base = os.path.join(ROOT, "build_v8")
    out = []
    for fn in sorted(os.listdir(os.path.join(base, "manifest"))):
        name = fn[:-5]
        if not fn.endswith(".json") or name == "head":
            continue
        if build_others:
            m = importlib.import_module(f"nova_v8.cad_{name}")
            recs = m.build()
            out += [r for r in recs if not r.id.startswith(REPLACED_PREFIX)]
            continue
        for r in json.load(open(os.path.join(base, "manifest", fn))):
            if r["id"].startswith(REPLACED_PREFIX):
                continue
            stp = os.path.join(base, "step", f"{r['id']}.step")
            if os.path.exists(stp):
                out.append(PartRec(r["id"], r["name"], import_step(stp), r["mat"], r["sub"], r["joint"],
                                   tuple(r["explode"]), r["internal"], r["note"]))
    return out


TILT_AXIS = Axis((0, TILT_Y, TILT_Z), (1, 0, 0))


def pose_sweep(parts, others):
    """Head frame: J2 parts rotate by -tilt, J1 parts by -pan then -tilt.  Collisions > 0.5 mm3."""
    head = [p for p in parts if p.joint == "J3" and p.id not in RENDER_ONLY]
    head_out = [p for p in parts if p.id in ("HB01", "HB04", "HB03", "HB17-R", "HB17-L")]
    j2 = [p for p in parts + others if p.joint == "J2"]
    j1 = [p for p in others if p.joint == "J1" and not p.internal and p.shape.bounding_box().max.Z > 95.0]
    gear_pair = {("HB11", "HB09"), ("HB09", "HB11")}
    res = []
    for th in (-20, -10, 0, 10, 20):
        for q in j2:
            qs = q.shape.rotate(TILT_AXIS, -th)
            for h in head:
                hs = h.shape.rotate(Axis((0, TILT_Y, HA.SERVO_Z), (1, 0, 0)), th) if (h.id, q.id) in gear_pair \
                    else h.shape
                v = common_vol(hs, qs)
                if v > 0.5 or v < 0:
                    res.append((f"tilt {th}", h.id, q.id, round(v, 2)))
        for ph in ((-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90) if abs(th) in (0, 20) else ()):
            for q in j1:
                qs = q.shape.rotate(Axis.Z, -ph).rotate(TILT_AXIS, -th)
                for h in head_out:
                    v = common_vol(h.shape, qs)
                    if v > 0.5 or v < 0:
                        res.append((f"tilt {th} pan {ph}", h.id, q.id, round(v, 2)))
    return res


def min_gaps(parts, others):
    """Smallest distances of the outer head parts to neck/torso over the tilt / pan range."""
    outer = [p.shape for p in parts if p.id in ("HB01", "HB04")]
    out = {}
    for q in others + [p for p in parts if p.joint == "J2"]:
        if q.id not in ("N06", "N02", "N01", "T01", "T02", "HB09", "HB10", "A05-R", "A05-L"):
            continue
        best = 1e9
        for th in (-20, 0, 20):
            phs = (0,) if q.joint == "J2" else (0, 45, 90, -90)
            for ph in phs:
                qs = q.shape.rotate(Axis.Z, -ph) if q.joint == "J1" else q.shape
                qs = qs.rotate(TILT_AXIS, -th)
                for o in outer:
                    try:
                        best = min(best, o.distance_to(qs))
                    except Exception:  # noqa: BLE001 - BRepExtrema fails on some B-spline pairs
                        if common_vol(o, qs) > 0.01:
                            best = -1.0
        out[q.id] = round(best, 2) if best < 1e8 else "n/a"
    return out


def insertion_check(parts):
    """Front module (HB04 + HB03 + HB07 + HB13 + tray magnets) pulled out along -Y: no collision with HB01 and the
    parts already in it (underside screws removed).  Servo + HB11 slid out of the rails along -Y likewise."""
    by = {p.id: p.shape for p in parts}
    mod = [by[i] for i in ("HB04", "HB03", "HB07", "HB13", "HB16-1", "HB16-2")]
    fixed = [by[i] for i in ("HB01", "HB16-3", "HB16-4", "HB15-R", "HB15-L", "HB14-R", "HB14-L", "HB12", "HB11")]
    worst = 0.0
    for d in (0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 18.0, 25.0):
        for m in mod:
            mm = Pos(0, -d, 0) * m
            for f in fixed:
                worst = max(worst, common_vol(mm, f))
    sv = [by["HB12"], by["HB11"]]
    worst_s = 0.0
    for d in (1, 3, 6, 10, 15, 22, 30, 38):
        for m in sv:
            mm = Pos(0, -float(d), 0) * m
            worst_s = max(worst_s, common_vol(mm, by["HB01"]))
    return round(worst, 3), round(worst_s, 3)


DENS = {"white": 1.25, "black": 1.25, "grey": 1.27, "glass": 1.19, "cyan_led": 1.19, "metal": 7.8}
FIXED_G = {"HB12": 13.4, "HB13": 50.0, "HB14-R": 2.0, "HB14-L": 2.0}


def mass_report(parts):
    m_tot, my, mz = 0.0, 0.0, 0.0
    for p in parts:
        if p.joint != "J3" or p.id in RENDER_ONLY:
            continue
        c = p.shape.center()
        m = FIXED_G.get(p.id, p.shape.volume / 1000 * DENS.get(p.mat, 1.2))
        m_tot += m
        my += m * (c.Y - TILT_Y)
        mz += m * (c.Z - TILT_Z)
    cy, cz = my / m_tot, mz / m_tot
    lev = max(abs(cy * math.cos(math.radians(t)) - cz * math.sin(math.radians(t))) for t in range(-20, 21, 5))
    return dict(mass_g=round(m_tot, 1), cg_ahead=round(-cy, 1), cg_above=round(cz, 1),
                max_kgcm=round(m_tot / 1000 * lev / 10, 3))


def visor_report(h03):
    """Exactness of the visor: OCC surface types of its faces + STL facet / normal error of the exported mesh."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    cyl = []
    for f in h03.faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() == GeomAbs_Cylinder:
            cyl.append(round(ad.Cylinder().Radius(), 4))
    import struct
    import numpy as np
    d = open(os.path.join(OUT_DIR, "stl", "HB03.stl"), "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    v = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    v = v["v"].astype(float)
    c = v.mean(1)
    r = np.hypot(c[:, 0], YC - c[:, 1])
    nn = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    nn /= np.linalg.norm(nn, axis=1)[:, None] + 1e-12
    outer = (r > R_OUT - 0.5) & (np.abs(nn[:, 2]) < 0.5)
    tn = np.stack([c[:, 0], c[:, 1] - YC, 0 * c[:, 0]], 1)
    tn /= np.linalg.norm(tn, axis=1)[:, None]
    dev = np.degrees(np.arccos(np.clip(np.abs((nn * tn).sum(1)), 0, 1)))
    th = np.arctan2(v[..., 0], YC - v[..., 1])
    span = np.degrees(th.max(1) - th.min(1))
    return dict(cylinder_faces=sorted(set(cyl)), stl_outer_tris=int(outer.sum()),
                facet_deg_max=round(float(span[outer].max()), 2), normal_err_deg_max=round(float(dev[outer].max()), 2))


def precise_volume(shape):
    """GProp volume with eps 1e-6 (the default .volume is ~0.2 % off on spline-trimmed cylinders)."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, g, 1e-6, False)
    return g.Mass()


def verify_step(parts):
    from build123d import import_step
    bad = []
    for p in parts:
        s = import_step(os.path.join(OUT_DIR, "step", f"{p.id}.step"))
        v0, v1 = precise_volume(p.shape), precise_volume(s)
        if not s.is_valid or abs(v1 - v0) > 1e-4 * v0 + 0.01:
            bad.append((p.id, s.is_valid, round(v1, 2), round(v0, 2)))
    return bad


if __name__ == "__main__":
    t = time.time()
    parts = build()
    valid = {p.id: p.shape.is_valid for p in parts}          # before export (the STEP writer touches shared edges)
    # stale files of removed parts (v8.0 HB02 rear cap) out of this variant's build folder
    for sub, ext in (("stl", "stl"), ("step", "step")):
        for fn in os.listdir(os.path.join(OUT_DIR, sub)) if os.path.isdir(os.path.join(OUT_DIR, sub)) else []:
            if fn.endswith("." + ext) and fn[:-len(ext) - 1] not in {p.id for p in parts}:
                os.remove(os.path.join(OUT_DIR, sub, fn))
    recs = export_parts(parts, MANIFEST, step=True, out_dir=OUT_DIR)
    for p, r in zip(parts, recs):
        print(f"  {r['id']:8s} {r['mat']:11s} {r['joint']:3s} {'int' if r['internal'] else '   '} valid={valid[p.id]} "
              f"size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("  STEP re-import:", verify_step(parts) or f"{len(parts)} OK")
    by = {p.id: p.shape for p in parts}
    print("  visor exactness:", visor_report(by["HB03"]))
    print("  mass (J3):", mass_report(parts))
    print("  interference (own):", interference(parts) or "none")
    lcd_front = HBC.rr_prism_y(DISP_W, DISP_H, DISP_CR, DISP_Y0, DISP_Y0 + 3.0, cz=ZC)
    print(f"  board: LCD front -> visor {lcd_front.distance_to(by['HB03']):.2f} mm, -> HB04 "
          f"{lcd_front.distance_to(by['HB04']):.2f} mm, board -> HB01 {by['HB13'].distance_to(by['HB01']):.2f} mm")
    print(f"  servo -> HB01 {by['HB12'].distance_to(by['HB01']):.2f} mm, seam HB04/HB01 "
          f"{by['HB04'].distance_to(by['HB01']):.2f} mm (skirt clearance), visor -> HB04 "
          f"{by['HB03'].distance_to(by['HB04']):.2f} mm (VHB)")
    print("  module / servo pull-out collision (mm3):", insertion_check(parts))
    skin = Skin().body
    ol = dev_wire(0.0, R_OUT)
    vmax = max(skin.distance_to(ol.position_at(i / 240)) for i in range(240))
    print(f"  visor outer outline max distance outside the body skin (0 = flush): {vmax:.3f} mm")
    if "--check" in sys.argv or "--pose" in sys.argv:
        oth = other_parts("--build-others" in sys.argv)
        print(f"  loaded {len(oth)} parts of the other v8 modules")
        if "--check" in sys.argv:
            print("  interference (with others):", interference(parts, oth) or "none")
            print("  min gaps head <-> neck/torso over tilt +-20 / pan +-90:", min_gaps(parts, oth))
        if "--pose" in sys.argv:
            print("  pose sweep:", pose_sweep(parts, oth) or "none")
    nums = export_manufacturing(OUT_DIR)
    print("  visor:", json.dumps(nums, ensure_ascii=False))
    print(f"[{MANIFEST}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT_DIR}")
