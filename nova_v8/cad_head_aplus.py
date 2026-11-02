"""
NOVA mini v8.1 - HEAD variant A+ "A s jemne zakriveným sklom" (curved R180 cover), manifest "head_aplus".
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.cad_head_aplus [--check] [--pose] [--full]
(--check / --pose test the A+ front against the other v8 modules; --full also re-tests the head A parts)
Exports STEP (first) + STL + manifest into build_v8_var_aplus/ (never build/ or build_v8/), plus
build_v8_var_aplus/blank/ : HP04F_prirez.svg (1:1 blank + vinyl mask + mould rib template), HP04F_prirez.dxf
(laser outline of the flat blank), HP04M_maska.dxf (plotter outline of the inner black mask) and
HP04_forma_rebro.dxf (laser outline of one MDF mould rib); the same 4 files are mirrored into nova_v8/sklo/ (the
versioned copy that nova_v8/export_v8.py packs).

A+ = the CURRENT v8.1 head A (nova_v8/cad_head.py, imported: shell, ears, tilt drive, display bracket, hidden
retention and the board position follow head A automatically) with ONLY the front bezel + cover replaced:
  * monolithic white shell HP01 (= H01): no back cover, no seam / screw / port / vent on the back, top or sides;
    the only visible split is white shell / protruding black bezel, 0.5 mm, even all round.
  * HP03 uses head A's closed-seam skirt (101.7 x 69.7, 0.15 clearance in the H01 opening: it centres the module and
    you look onto the black skirt step, never into the head - no guide ribs = no dashes in the seam), the same
    3 bosses for the bracket and the same hard Y stops -> front module = HP03 + HP04 + EP31 + HP07 (= H07) slides in
    along +Y like head A, 2 magnet pairs at the top, 2x M2 from the UNDERSIDE (flush counterbores, head tilted up).
  * board EP31 at EXACTLY the head A position (LCD front y -35.6, back -29.6) -> HP07 = H07 and the detailed head
    internals of nova_v8/cad_internals.py (IH01..IH08, IW1-3) are valid for A+ unchanged.
  * dead front: smoked cast PMMA 2.0 with a black inner mask (window = LCD active area + 0.5 per side, symmetric,
    as head A), face 0.3 under the bezel face; optional camera HP04C render-only/internal.
  * vents: as head A - air in through the barrel-pocket mouth (underside), slots in the pocket ceiling, out through
    the bezel seam at the top.  Nothing on the outside.

Curved cover (local constants of this variant):
  HP04 = smoked CAST PMMA 2.0, laser-cut FLAT as the developed blank HP04F (92.5 x 60 R16 on the neutral layer
  R179), heat-bent (150-160 C) by gravity over a convex MDF mould R178 (= inner radius) so the visible outer face
  never touches the mould; single curvature -> the black mask is a flat vinyl sticker (or paint).  Vertical
  cylinder axis at x 0, y +136.65; outer R180 / inner R178, projected 92.0 x 60, sag 6.0 mm.
  The flat LCD cannot be laminated to a curved cover (head A uses OCA) -> the LCD border rests on a 0.5 foam gasket
  on a FLAT seat (y -36.1) that the bezel forms between the curved cover seat and the board: a wedge, 5 mm thick on
  the top/bottom bands at the centre line.  At the board sides (|x| > 39.5) the wedge would get thinner than 0.6 ->
  it is relieved there and the cover passes the LCD edge with 0.6 clearance; the cover is bonded (VHB 0.2) on the
  curved seat R177.8 on the top/bottom bands and outside the board pocket (|x| 43.3 .. 45.9).
  This sets the cover position: apex y -43.35, bezel face apex y -43.65 -> the black frame protrudes 10.65 mm from
  the white rim at the centre line and 3.4 mm at the sides.  Air gap cover -> LCD: 5.75 at the centre, 1.9 at the
  active-area edge, 0.6 at the LCD edge -> the board's capacitive touch does NOT work through the A+ cover
  (head A: laminated, touch works) - the face is display-only (voice / app interaction).
  Tilt group (J3) 181 g, CG 14.7 ahead of / 26.7 above the tilt axis -> max 0.42 kg.cm on the MG90S over +-20 deg
  (head A 0.40; MG90S stall ~1.8 kg.cm).

Parts (sub "head_aplus"; J3 = head tilt about X through y 0 z 127, J2 = pan stage)
  HP01     Hlavny obal hlavy          white     = head A H01 (one piece, barrel pocket, tilt-servo rails, pivot
                                                bosses, ear cups, magnet blocks, underside screw pads, hidden vents)
  HP03     Predny ram (zakriveny)     black     101 x 69 R23.5, face = cylinder R180.3, curved cover seat + wedge
                                                board seat, window 75.4 x 51.0, closed-seam skirt 101.7 x 69.7 into
                                                HP01 (head A), 3 bosses for HP07
  HP04     Kryci sklo (zakrivene)     glass     smoked cast PMMA 2.0, R180/R178, radial edges (= bent laser blank)
  HP04E    Obsah displeja - oci       eye       RENDER-ONLY pills 10.5 x 17.5 on the cover curvature
  HP04C    Okienko kamery             black_gloss  RENDER-ONLY, internal: optional camera behind the mask band
  HP04F    Rozvinuty prirez skla      glass     INTERNAL flat blank 92.5 x 60 R16 x 0.1 (laser outline reference)
  HP05-R/L Ucho prave / lave          black     = head A H05 (Ø28 dome, flush light ring)
  HP06-R/L LED kruzok ucha            cyan_led  = head A H06
Internal (internal=True)
  HP07     Drziak displeja            grey      = head A H07 (3x M2 into HP03, magnet lugs, underside screw lugs)
  HP09     Ozubeny segment naklonu    grey      J2: = head A H09 (20T m1 sector on the N06 +X end)
  HP10     Puzdro capu naklonu        grey      J2: = head A H10
  HP11     Koliesko serva naklonu     grey      = head A H11 (20T m1 on the MG90S spline, 1:1)
  EP31     Displej ESP32-S3 3.5"      display   86 x 56 x 6 board, LCD front y -35.6 (flat, = head A position)
  EP32     Servo naklonu MG90S        servo     shaft (y 0, z 147) // X, beside the barrel pocket (+X)
  EP33-R/L DPS ucha                   pcb       Ø23 7x WS2812B module
  MP31-R/L Cap naklonu M3x12          metal     pivot pins on the tilt axis
  MP32-1..4 Magnet Ø6x3 N52           metal     front-module latch (2 in HP07, 2 in HP01)
  MP33-R/L Skrutka M2x6 zospodu       metal     DIN 7985, heads flush in the HP01 underside
HP09/HP10 duplicate head A's H09/H10 (same physical parts on the barrel) - when rendering A+ together with the
"head" manifest exclude one pair (nova_v8/make_sheets_v8.py drops the whole head A manifest for A+).

FDM: HP03 printed STANDING on its bottom edge (cylinder axis = printer Z) -> the R180.3 face is built from true
arcs, no stair-stepping; tree support under the top wall; sand + satin black.  HP01, HP05, HP06, HP07, HP09..HP11
as head A.

Deviations (local constants, nova_v8/spec.py untouched): bezel protrudes 10.65 mm at the centre / 3.4 at the
sides (spec bezel.protrude 5.0 = head A, flat); cover 92.5 x 60 developed (92.0 x 60 projected) instead of the
flat 92 x 60; LCD not laminated (air gap) -> no touch through the cover.
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Axis, BuildSketch, Circle, Cylinder, Edge, Face, Locations, Plane, Pos, RectangleRounded,
                       Solid, Sphere, Vector, Wire, import_step, mirror)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire
from OCP.BRepLib import BRepLib
from OCP.Geom import Geom_CylindricalSurface
from OCP.Geom2d import Geom2d_Ellipse, Geom2d_Line, Geom2d_TrimmedCurve
from OCP.gp import gp_Ax2d, gp_Ax3, gp_Dir, gp_Dir2d, gp_Elips2d, gp_Pnt, gp_Pnt2d
from OCP.ShapeFix import ShapeFix_Face

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import cad_head as HA  # noqa: E402  (v8.1 head A: shell, ears, tilt drive, bracket, retention)
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8_var_aplus")
SKLO_DIR = os.path.join(ROOT, "nova_v8", "sklo")   # versioned copy packed by nova_v8/export_v8.py (HP04* only)
SUB = "head_aplus"
MANIFEST = "head_aplus"
J = "J3"

# ---- shared with head A (read from nova_v8/cad_head.py) -------------------------------------------------
H = S.HEAD
BZ, GL, EYE, CAM = HA.BZ, HA.GL, HA.EYE, HA.CAM
Y0, ZC = HA.Y0, HA.ZC                                      # white front rim plane y -33, head centre z 154
DSP_W, DSP_H, DSP_T = HA.DSP_W, HA.DSP_H, HA.DSP_T         # 86 x 56 x 6
ACT_W, ACT_H = S.DISPLAY["active"]                         # 73.44 x 48.96
Y_DSP0, Y_DSP1, DSP_ZC = HA.Y_DSP0, HA.Y_DSP1, HA.DSP_ZC   # LCD front -35.6, board back -29.6, centre z 154
DSP_R, DSP_CLR = HA.DSP_R, HA.DSP_CLR
SK_W, SK_H, SK_R = HA.SK_W, HA.SK_H, HA.SK_R               # closed-seam skirt 101.7 x 69.7 (0.15 in the H01 opening)
SKIRT_END, SKIRT_WALL = HA.SKIRT_END, HA.SKIRT_WALL        # skirt to y -29.7, inner outline = face - 2 x 1.6
WIN_W, WIN_H = HA.WIN_W, HA.WIN_H                          # mask window 74.44 x 49.96 (active area + 0.5 / side)
LCD_HW = (DSP_W - 1.0) / 2                                 # 42.5 LCD (touch glass) half width (EP31 / IH01)

# ---- curved cover (local constants of this variant) ------------------------------------------------------
R_OUT = 180.0              # outer radius of the cover (vertical cylinder axis)
T_COVER = 2.0              # smoked cast PMMA 2.0 mm
R_IN = R_OUT - T_COVER     # 178 = radius of the convex bending mould
R_MID = R_OUT - T_COVER / 2   # 179 neutral layer: the flat blank is developed here
ADH = 0.2                  # VHB tape under the cover edge
R_SEAT = R_IN - ADH        # 177.8 curved cover seat in HP03
RECESS = 0.3               # cover front 0.3 under the bezel face (reads flush, absorbs the bending tolerance)
R_FACE = R_OUT + RECESS    # 180.3 bezel face
CLR = 0.3                  # cover edge -> bezel seat wall (heat-bent part tolerance)
FOAM = 0.5                 # closed-cell foam gasket LCD border -> flat seat (dust seal; no OCA possible on a curve)
Y_SEAT = Y_DSP0 - FOAM     # -36.1 flat board seat
G_LCD = 0.6                # cover back -> LCD edge clearance (sets the cover position)
SEAT_MIN = 0.6             # thinnest wedge kept under the flat seat (relieved where thinner)
LEDGE_T = 1.6              # curved ledge thickness where the bezel is hollow behind it
R_LB = R_SEAT - LEDGE_T    # 176.2
RIM, RIM_D = 1.6, 1.5      # locating rim around the board pocket behind the seat plane
BLANK_W, BLANK_H, BLANK_R = 92.5, GL["h"], GL["r"]          # developed blank 92.5 x 60 R16
COVER_EDGE = 0.3           # edge break on the outer cover edge (flame-polished laser edge)
BZ_FRONT_FILLET = 2.4      # soft outer edge of the black frame
SEAT_EDGE = 0.4            # break on the seat edge in the bezel face
OPEN_MARGIN = 0.5          # bezel window 0.5 outside the mask window (never seen through the window)
OPEN_R = 2.5
CAM_HOLE_D = 3.6           # optional clear hole in the mask for the camera
BLANK_GAP = 0.5            # the flat blank reference part floats 0.5 in front of the cover apex
MASK_INSET = 0.3           # vinyl mask 0.3 smaller than the cover all round

# derived positions
X_PK = DSP_W / 2 + DSP_CLR                                             # 43.3 board pocket half width
Y_AX = Y_DSP0 - G_LCD + math.sqrt(R_IN ** 2 - LCD_HW ** 2)             # +136.65 cylinder axis
Y_OUT_APEX = Y_AX - R_OUT                                              # -43.35
Y_IN_APEX = Y_AX - R_IN                                                # -41.35
Y_FACE_APEX = Y_AX - R_FACE                                            # -43.65
X_REL = math.sqrt(R_SEAT ** 2 - (Y_AX - (Y_SEAT - SEAT_MIN)) ** 2)     # 39.5: side relief of the wedge seat


def mask_window():
    """Mask window in the FRONT VIEW (x half width, z bottom, z top) = head A (active area + 0.5, symmetric)."""
    return WIN_W / 2, DSP_ZC - WIN_H / 2, DSP_ZC + WIN_H / 2


# ===========================================================================================
# helpers
# ===========================================================================================
check, retry, edges_where, try_fillet = HA.check, HA.retry, HA.edges_where, HA.try_fillet
try_chamfer = HA.try_chamfer
rr_prism_y, cyl_y, bx, union, solid1 = HA.rr_prism_y, HA.cyl_y, HA.bx, HA.union, HA.solid1


def cyl_z(r, height=200.0):
    """Solid vertical cylinder about the cover axis."""
    return Pos(0, Y_AX, ZC) * Cylinder(r, height)


def y_on_cyl(r, x):
    return Y_AX - math.sqrt(r * r - x * x)


def r_axis(p):
    return math.hypot(p.X, p.Y - Y_AX)


def s_dev(p, r_ref):
    """Developed (arc-length) coordinate of a point on radius r_ref."""
    return r_ref * math.atan2(p.X, Y_AX - p.Y)


def cyl_patch_face(r, w, h, rc, r_ref, sc=0.0, zc=ZC):
    """Exact trimmed face on the cylinder of radius r (cover axis) bounded by a rounded rectangle
    w x h, corner rc, centred at arc length sc / height zc - all lengths DEVELOPED on radius r_ref.
    Built from pcurves in the cylinder parameter space (u = s / r_ref, v = z): the corners are
    ellipses there, the face itself stays a true cylinder (no B-spline approximation)."""
    surf = Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, Y_AX, 0), gp_Dir(0, 0, 1), gp_Dir(0, -1, 0)), r)
    a, b = rc / r_ref, rc
    hu, hv = (w / 2 - rc) / r_ref, h / 2 - rc
    uc = sc / r_ref
    curves = []

    def seg(p, q):
        ln = math.dist(p, q)
        if ln > 1e-9:
            d = gp_Dir2d((q[0] - p[0]) / ln, (q[1] - p[1]) / ln)
            curves.append(Geom2d_TrimmedCurve(Geom2d_Line(gp_Pnt2d(*p), d), 0.0, ln))

    def arc(cu, cv, t0, t1):     # ellipse u = cu - a sin t, v = cv + b cos t
        el = Geom2d_Ellipse(gp_Elips2d(gp_Ax2d(gp_Pnt2d(cu, cv), gp_Dir2d(0, 1)), b, a))
        curves.append(Geom2d_TrimmedCurve(el, t0, t1))

    R_, L_, T_, B_ = uc + hu, uc - hu, zc + hv, zc - hv
    seg((R_ + a, B_), (R_ + a, T_))
    arc(R_, T_, -math.pi / 2, 0.0)
    seg((R_, T_ + b), (L_, T_ + b))
    arc(L_, T_, 0.0, math.pi / 2)
    seg((L_ - a, T_), (L_ - a, B_))
    arc(L_, B_, math.pi / 2, math.pi)
    seg((L_, B_ - b), (R_, B_ - b))
    arc(R_, B_, math.pi, 1.5 * math.pi)
    mw = BRepBuilderAPI_MakeWire()
    for c in curves:
        e = BRepBuilderAPI_MakeEdge(c, surf).Edge()
        BRepLib.BuildCurves3d_s(e)
        mw.Add(e)
    f = BRepBuilderAPI_MakeFace(surf, mw.Wire(), True).Face()
    fix = ShapeFix_Face(f)
    fix.Perform()
    f = fix.Face()
    BRepLib.BuildCurves3d_s(f)
    face = Face(f)
    if not face.is_valid:
        raise RuntimeError("cylinder patch face invalid")
    return face


def radial_patch(r0, r1, w, h, rc, r_ref=R_MID, sc=0.0, zc=ZC):
    """Solid between radii r0 < r1 whose side walls are RADIAL (normal to the sheet) - exactly what a
    flat laser-cut blank becomes after bending.  Outline developed on r_ref."""
    return check("radial patch", Solid.thicken(cyl_patch_face(r0, w, h, rc, r_ref, sc, zc), r1 - r0))


def rr_dist(x, z, w, h, r, cz=ZC):
    return HA.rr_dist(x, z, w, h, r, cz)


# ===========================================================================================
# HP03 curved bezel, HP04 cover, HP04E eyes, HP04C camera window, HP04F flat blank
# ===========================================================================================

def bezel():
    bw, bh, br = BZ["w"], BZ["h"], BZ["r"]
    # visible black frame: rounded rectangle 101 x 69 R23.5 cut by the face cylinder R180.3, soft front edge
    face = check("HP03 face", rr_prism_y(bw, bh, br, Y_FACE_APEX - 2.0, Y0) & cyl_z(R_FACE))
    loop = edges_where(face, lambda p: abs(r_axis(p) - R_FACE) < 0.02)
    face = try_fillet(face, loop, BZ_FRONT_FILLET, "HP03 front edge")
    # head A closed-seam skirt (0.35 step behind the visible face = black seam bottom, 0.15 in the H01 opening)
    skirt = rr_prism_y(SK_W, SK_H, SK_R, Y0 - 0.01, SKIRT_END)
    b = retry(lambda: face + skirt, "HP03 face + skirt")
    # hollow behind the curved ledge (1.6) and inside the skirt, except the block that forms the flat board seat
    cav = rr_prism_y(bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL, Y_FACE_APEX - 2.0,
                     SKIRT_END + 1.0) & cyl_z(R_LB)
    blk = rr_prism_y(2 * (X_PK + RIM), DSP_H + 2 * (DSP_CLR + RIM), DSP_R + DSP_CLR + RIM, Y_FACE_APEX - 3.0,
                     Y_SEAT + RIM_D, cz=DSP_ZC)
    b = retry(lambda: b - (cav - blk), "HP03 cavity")
    # board pocket behind the flat seat (board + 0.3), side relief where the wedge would be < 0.6
    pk = (DSP_W + 2 * DSP_CLR, DSP_H + 2 * DSP_CLR, DSP_R + DSP_CLR)
    b = retry(lambda: b - rr_prism_y(*pk, Y_SEAT, SKIRT_END + 1.0, cz=DSP_ZC), "HP03 board pocket")
    # (only UNDER the cover: radially behind the curved seat and inside the cover outline - at the 4 corners the
    #  board pocket reaches outside the R16 cover corners, where the black frame face must stay closed)
    seat_zone = radial_patch(R_SEAT - 10.0, R_SEAT + 0.01, BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR)
    rel = rr_prism_y(*pk, Y_FACE_APEX - 3.0, Y_SEAT + 0.01, cz=DSP_ZC) & seat_zone & \
        union([bx(sx * X_REL, sx * (X_PK + 1.0), Y_FACE_APEX - 4.0, Y_SEAT + 1.0, ZC - 40, ZC + 40) for sx in (1, -1)])
    b = retry(lambda: b - rel, "HP03 side relief")
    # window through the wedge (0.5 outside the mask window -> hidden behind the mask)
    xw, zb, zt = mask_window()
    xo, zo0, zo1 = xw + OPEN_MARGIN, zb - OPEN_MARGIN, zt + OPEN_MARGIN
    b = retry(lambda: b - rr_prism_y(2 * xo, zo1 - zo0, OPEN_R, Y_FACE_APEX - 3.0, Y_SEAT + 0.01,
                                     cz=(zo0 + zo1) / 2), "HP03 window")
    # 3 bosses for the HP07 (= H07) screws: head A positions, end faces on the board-back plane, ribs to the wall
    clip = rr_prism_y(bw - 0.4, bh - 0.4, br - 0.2, Y_FACE_APEX - 3.0, Y_DSP1 + 1.0) & cyl_z(R_FACE - 0.6)
    for (x, z) in HA.BZ_BOSSES:
        boss = cyl_y(HA.BOSS_R, Y_FACE_APEX - 2.0, Y_DSP1, x, z)
        if x != 0:
            boss = boss + bx(x, math.copysign(bw / 2 - 1.0, x), Y_FACE_APEX - 2.0, SKIRT_END, z - 1.0, z + 1.0)
        b = retry(lambda: b + (boss & clip), "HP03 boss")
    # curved cover seat (radial walls = the bent blank + 0.3), then the M2 pilots
    seat = radial_patch(R_SEAT, R_FACE + 2.0, BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR)
    b = retry(lambda: b - seat, "HP03 seat")
    for (x, z) in HA.BZ_BOSSES:
        b = retry(lambda: b - cyl_y(HA.PILOT_R, Y_DSP1 + 0.1, Y_DSP1 - 4.5, x, z), "HP03 pilot")
    b = solid1(b)
    if len(b.solids()) != 1:
        raise RuntimeError(f"HP03: {len(b.solids())} solids")
    e_sk = edges_where(b, lambda p: abs(p.Y - SKIRT_END) < 0.02 and abs(rr_dist(p.X, p.Z, SK_W, SK_H, SK_R)) < 0.02)
    b = try_chamfer(b, e_sk, 0.4, "HP03 skirt lead-in")
    sw, sh, sr = BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR
    e_seat = edges_where(b, lambda p: abs(r_axis(p) - R_FACE) < 0.02
                         and abs(rr_dist(s_dev(p, R_MID), p.Z, sw, sh, sr)) < 0.15)
    b = try_fillet(b, e_seat, SEAT_EDGE, "HP03 seat edge")
    return check("HP03", solid1(b), vmin=3000)


def cover():
    c = radial_patch(R_IN, R_OUT, BLANK_W, BLANK_H, BLANK_R)
    e = edges_where(c, lambda p: abs(r_axis(p) - R_OUT) < 0.02)
    c = try_fillet(c, e, COVER_EDGE, "HP04 edge")
    return check("HP04", c, vmin=5000)


def eyes():
    """Render-only warm pills 10.5 x 17.5, 0.02..0.10 mm in front of the curved cover (clear of the STL chord error)."""
    out = None
    for sx in (-1, 1):
        sc = R_OUT * math.asin(sx * EYE["x"] / R_OUT)               # front-view x -> arc length
        e = radial_patch(R_OUT + 0.02, R_OUT + 0.10, EYE["w"], EYE["h"], EYE["w"] / 2, r_ref=R_OUT,
                         sc=sc, zc=EYE["z"])
        out = e if out is None else out + e
    return check("HP04E", out)


def camera_dot():
    """Render-only lens of the OPTIONAL camera (internal): very low spherical cap on the cover (x 0 = apex)."""
    r, sag = CAM["d"] / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_OUT_APEX - sag + rs, CAM["z"]) * Sphere(rs)
    return check("HP04C", sph & cyl_y(r, Y_OUT_APEX - 1.0, Y_OUT_APEX, 0.0, CAM["z"]))


def flat_blank():
    """Developed (unbent) cover outline, 0.1 mm plate in front of the cover apex - laser reference."""
    y = Y_OUT_APEX - BLANK_GAP
    return check("HP04F", rr_prism_y(BLANK_W, BLANK_H, BLANK_R, y - 0.1, y))


# ===========================================================================================
# manufacturing numbers + 1:1 drawing of the blank, the vinyl mask and the mould rib
# ===========================================================================================

def mask_numbers():
    """Mask window / camera hole, developed on the INNER face (where the vinyl / paint goes)."""
    xw, z_bot, z_top = mask_window()                                # 37.22, 129.02, 178.98
    s_w = R_IN * math.asin(xw / R_IN)                               # developed half width on R178
    return dict(win_w=2 * s_w, win_h=z_top - z_bot, win_r=2.0, win_zc=(z_top + z_bot) / 2,
                win_top_from_edge=ZC + BLANK_H / 2 - z_top, win_bot_from_edge=z_bot - (ZC - BLANK_H / 2),
                cam_from_top=ZC + BLANK_H / 2 - CAM["z"], mask_w=BLANK_W * R_IN / R_MID - 2 * MASK_INSET,
                mask_h=BLANK_H - 2 * MASK_INSET, mask_r=BLANK_R - MASK_INSET)


def glass_numbers():
    half = BLANK_W / 2 / R_MID
    sag_out = R_OUT * (1 - math.cos(half))
    x_act = ACT_W / 2
    return dict(R_out=R_OUT, R_in=R_IN, t=T_COVER, blank=(BLANK_W, BLANK_H, BLANK_R),
                proj_w=2 * R_OUT * math.sin(half), sag=sag_out,
                gap_center=Y_DSP0 - Y_IN_APEX, gap_active_edge=Y_DSP0 - y_on_cyl(R_IN, x_act),
                gap_lcd_edge=Y_DSP0 - y_on_cyl(R_IN, LCD_HW),
                wedge_center=Y_SEAT - y_on_cyl(R_SEAT, 0.0), x_relief=X_REL,
                bezel_proud_center=Y0 - Y_FACE_APEX, bezel_proud_side=Y0 - y_on_cyl(R_FACE, BZ["w"] / 2),
                strain_pct=100 * (T_COVER / 2) / R_MID, y_out_apex=Y_OUT_APEX, y_axis=Y_AX)


MOULD_W, MOULD_SIDE, MOULD_RIBS, MOULD_T = 150.0, 25.0, 6, 18.0


def mould_rib_wire():
    """Outline of one MDF mould rib (local XY, mm): flat bottom 150, sides 25, convex top arc R178."""
    sag = R_IN - math.sqrt(R_IN ** 2 - (MOULD_W / 2) ** 2)
    hw = MOULD_W / 2
    p0, p1, p2, p3 = Vector(-hw, 0), Vector(hw, 0), Vector(hw, MOULD_SIDE), Vector(-hw, MOULD_SIDE)
    top = Vector(0, MOULD_SIDE + sag)
    edges = [Edge.make_line(p0, p1), Edge.make_line(p1, p2), Edge.make_three_point_arc(p2, top, p3),
             Edge.make_line(p3, p0)]
    return Wire(edges), sag


def write_blank_files(out_dir):
    d = os.path.join(out_dir, "blank")
    os.makedirs(d, exist_ok=True)
    g, m = glass_numbers(), mask_numbers()
    _, mould_sag = mould_rib_wire()
    L = []
    a = L.append
    a('<?xml version="1.0" encoding="UTF-8"?>')
    a('<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">')
    a('<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#222}.cut{fill:none;stroke:#e00000;stroke-width:0.15}'
      '.ax{stroke:#0060c0;stroke-width:0.2;stroke-dasharray:4 1 1 1;fill:none}.dim{stroke:#555;stroke-width:0.15;fill:none}'
      '</style>')
    a('<rect x="0" y="0" width="297" height="210" fill="#ffffff"/>')
    a('<text x="12" y="12" font-size="5.2" font-weight="bold">NOVA mini v8.1 – hlava A+ – krycie sklo HP04: prírez, maska, '
      'forma (mierka 1:1)</text>')
    a(f'<text x="12" y="18.5" font-size="3.2">Liate PMMA dymové {T_COVER:.1f} mm · valcový ohyb, zvislá os · R vonk. {R_OUT:.0f} / '
      f'R vnút. = R formy {R_IN:.0f} · rozvinuté na neutrálnej vrstve R {R_MID:.0f} · tlač bez zmeny mierky (100 %)</text>')
    # --- blank ---
    bx0, by0 = 14.0, 32.0
    a(f'<text x="{bx0}" y="{by0 - 4}" font-size="3.4" font-weight="bold">1  Prírez (laser, červená = rez)</text>')
    a(f'<rect class="cut" x="{bx0}" y="{by0}" width="{BLANK_W}" height="{BLANK_H}" rx="{BLANK_R}" ry="{BLANK_R}"/>')
    cx = bx0 + BLANK_W / 2
    a(f'<line class="ax" x1="{cx}" y1="{by0 - 2}" x2="{cx}" y2="{by0 + BLANK_H + 2}"/>')
    a(f'<text x="{cx + 1}" y="{by0 + BLANK_H + 5}" font-size="2.6" fill="#0060c0">os ohybu ∥ (vrchol oblúka)</text>')
    a(f'<text x="{bx0 + 2}" y="{by0 + 6}" font-size="2.6">HORE ↑</text>')
    a(f'<line class="dim" x1="{bx0}" y1="{by0 + BLANK_H + 9}" x2="{bx0 + BLANK_W}" y2="{by0 + BLANK_H + 9}"/>')
    a(f'<text x="{cx - 8}" y="{by0 + BLANK_H + 13}" font-size="3">{BLANK_W:.1f} mm</text>')
    a(f'<text x="{bx0 + BLANK_W + 2}" y="{by0 + BLANK_H / 2}" font-size="3">{BLANK_H:.0f}</text>')
    a(f'<text x="{bx0 + 2}" y="{by0 + BLANK_H - 3}" font-size="2.4">rohy R{BLANK_R:.0f}</text>')
    a(f'<text x="{bx0}" y="{by0 + BLANK_H + 18}" font-size="2.4">po ohnutí: pohľad spredu {g["proj_w"]:.1f} × {BLANK_H:.0f}, '
      f'priehyb {g["sag"]:.1f} mm, pomerné pretvorenie {g["strain_pct"]:.2f} %</text>')
    # --- vinyl mask (0.3 inset, symmetric window = head A) ---
    mx, my = 122.0, 32.0
    mw, mh, mr = m["mask_w"], m["mask_h"], m["mask_r"]
    wx = mx + mw / 2 - m["win_w"] / 2
    wy = my + (m["win_top_from_edge"] - MASK_INSET)
    ccx, ccy = mx + mw / 2, my + m["cam_from_top"] - MASK_INSET
    a(f'<text x="{mx}" y="{my - 4}" font-size="3.4" font-weight="bold">2  Maska – čierna fólia, VNÚTORNÁ strana</text>')
    path = (f'M{mx + mr},{my} h{mw - 2 * mr} a{mr},{mr} 0 0 1 {mr},{mr} '
            f'v{mh - 2 * mr} a{mr},{mr} 0 0 1 -{mr},{mr} h-{mw - 2 * mr} '
            f'a{mr},{mr} 0 0 1 -{mr},-{mr} v-{mh - 2 * mr} a{mr},{mr} 0 0 1 {mr},-{mr} Z ')
    wr = m["win_r"]
    path += (f'M{wx + wr},{wy} h{m["win_w"] - 2 * wr} a{wr},{wr} 0 0 1 {wr},{wr} v{m["win_h"] - 2 * wr} '
             f'a{wr},{wr} 0 0 1 -{wr},{wr} h-{m["win_w"] - 2 * wr} a{wr},{wr} 0 0 1 -{wr},-{wr} '
             f'v-{m["win_h"] - 2 * wr} a{wr},{wr} 0 0 1 {wr},-{wr} Z')
    a(f'<path d="{path}" fill="#111" fill-rule="evenodd" stroke="#e00000" stroke-width="0.12"/>')
    rh = CAM_HOLE_D / 2
    a(f'<circle cx="{ccx}" cy="{ccy}" r="{rh}" fill="none" stroke="#e00000" stroke-width="0.15" stroke-dasharray="0.8 0.5"/>')
    a(f'<text x="{wx + 3}" y="{wy + 8}" font-size="2.8" fill="#444">okno displeja {m["win_w"]:.1f} × {m["win_h"]:.1f} R{wr:.0f}</text>')
    a(f'<text x="{wx + 3}" y="{wy + 12}" font-size="2.4" fill="#444">aktívna plocha 3.5" + 0.5 mm (ako hlava A)</text>')
    a(f'<text x="{wx + 3}" y="{wy + 15.5}" font-size="2.4" fill="#444">pás hore aj dole {m["win_top_from_edge"] - MASK_INSET:.1f} mm, '
      f'bočné {(mw - m["win_w"]) / 2:.1f} mm</text>')
    a(f'<polyline points="{ccx + rh},{ccy} {mx + mw - 6},{my - 1.5} {mx + mw + 1},{my - 1.5}" fill="none" stroke="#e00000" stroke-width="0.15"/>')
    a(f'<text x="{mx + mw + 2}" y="{my - 0.6}" font-size="2.4">VOLITEĽNÝ otvor kamery Ø{CAM_HOLE_D}</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 3}" font-size="2.4">stred {m["cam_from_top"] - MASK_INSET:.1f} od hornej hrany</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 6.5}" font-size="2.4">(bez kamery nevyrezať)</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 12}" font-size="2.4">symetrická – zvnútra</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 15.5}" font-size="2.4">sa nezrkadlí</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 21}" font-size="2.4">plotter: HP04M_maska.dxf</text>')
    a(f'<text x="{mx}" y="{my + mh + 5}" font-size="2.5">rozvinuté na vnútornom povrchu R{R_IN:.0f}: {mw:.1f} × {mh:.1f} R{mr:.1f} '
      f'(o {MASK_INSET} menšie po obvode) – nalepiť až PO ohnutí</text>')
    # --- mould rib template ---
    fx, fy = 14.0, 124.0
    base = fy + MOULD_SIDE + mould_sag + 6
    a(f'<text x="{fx}" y="{fy - 4}" font-size="3.4" font-weight="bold">3  Šablóna rebra formy 1:1 – MDF {MOULD_T:.0f} mm, '
      f'{MOULD_RIBS} ks zlepiť (blok {MOULD_RIBS * MOULD_T:.0f} mm)</text>')
    p0 = (fx, base - MOULD_SIDE)
    p1 = (fx + MOULD_W, base - MOULD_SIDE)
    a(f'<path d="M{fx},{base} L{p0[0]},{p0[1]} A{R_IN},{R_IN} 0 0 1 {p1[0]},{p1[1]} L{p1[0]},{base} Z" '
      f'fill="#f3e6cf" stroke="#000" stroke-width="0.25"/>')
    a(f'<line class="ax" x1="{fx + MOULD_W / 2}" y1="{base - MOULD_SIDE - mould_sag - 3}" x2="{fx + MOULD_W / 2}" y2="{base + 2}"/>')
    a(f'<text x="{fx + 4}" y="{base - 6}" font-size="3">R {R_IN:.0f} (konvexná, hladká) – laser: HP04_forma_rebro.dxf</text>')
    a(f'<text x="{fx + 4}" y="{base - 2}" font-size="2.5">šírka {MOULD_W:.0f} · výška v strede {MOULD_SIDE + mould_sag:.1f} · '
      f'na krajoch {MOULD_SIDE:.0f}</text>')
    # --- scale bar ---
    sy = 196.0
    a(f'<line x1="{fx}" y1="{sy}" x2="{fx + 100}" y2="{sy}" stroke="#000" stroke-width="0.4"/>')
    for i in range(11):
        hh = 3 if i % 5 == 0 else 1.6
        a(f'<line x1="{fx + 10 * i}" y1="{sy}" x2="{fx + 10 * i}" y2="{sy - hh}" stroke="#000" stroke-width="0.25"/>')
    a(f'<text x="{fx}" y="{sy + 5}" font-size="3">kontrola mierky tlače: 100 mm</text>')
    # --- notes ---
    nx, ny = 176.0, 116.0
    notes = [
        "Postup (domáca dielňa):",
        "1. Objednať laserom rezaný prírez z LIATEHO dymového PMMA",
        f"    {T_COVER:.1f} mm (priepustnosť ~30–40 %). Extrudované PMMA sa pri",
        "    ohreve zmršťuje – najprv skúšobný kus, prípadne korekcia.",
        "2. Sušiť 1–2 h pri 80 °C (inak bubliny), fólie odstrániť.",
        "3. Rúra 150–160 °C, 4–8 min na papieri na pečenie,",
        "    kým nie je mäkký ako koža.",
        f"4. Položiť stredom (modrá os) na formu R{R_IN:.0f}, nechať",
        "    dosadnúť vlastnou váhou, len jemne pridržať v rohoch",
        "    (rukavice); chladnúť na forme 10 min.",
        "5. Masku nalepiť/nastriekať zvnútra (okno zakryť fóliou).",
        f"6. Vlepiť do zakriveného lôžka rámu HP03 (R{R_SEAT:.1f}) na pásku",
        f"    VHB {ADH} mm; čelo skla {RECESS} mm pod čelom rámu (pôsobí zarovno).",
        f"Alternatíva: PC 0.75–1.0 mm za studena (R{R_OUT:.0f} > 150×t).",
        f"Displej ostáva rovný na pene {FOAM} mm (klin rámu = rovné lôžko);",
        f"    vzduch k sklu: stred {g['gap_center']:.1f} mm, okraj LCD {g['gap_lcd_edge']:.1f} mm",
        "    -> dotyk cez zakrivené sklo nefunguje (len zobrazenie).",
        "Žiadne skrutky ani otvory zvonku – modul drží na magnetoch",
        "    + 2× M2 zospodu (ako hlava A).",
    ]
    for i, t in enumerate(notes):
        a(f'<text x="{nx}" y="{ny + 4.4 * i}" font-size="2.7"{" font-weight=\"bold\"" if i == 0 else ""}>{t}</text>')
    a('</svg>')
    svg = os.path.join(d, "HP04F_prirez.svg")
    with open(svg, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    dxfs = []
    try:
        from build123d import ExportDXF, Unit
        # laser outline of the flat blank
        with BuildSketch() as sk:
            RectangleRounded(BLANK_W, BLANK_H, BLANK_R)
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("REZ")
        exp.add_shape(sk.sketch.faces()[0].outer_wire(), layer="REZ")
        p = os.path.join(d, "HP04F_prirez.dxf")
        exp.write(p)
        dxfs.append(p)
        # plotter outline of the inner vinyl mask (outer edge, display window; optional camera hole on its own layer)
        with BuildSketch() as sk:
            RectangleRounded(m["mask_w"], m["mask_h"], m["mask_r"])
        with BuildSketch() as sw:
            with Locations((0, m["win_zc"] - ZC)):
                RectangleRounded(m["win_w"], m["win_h"], m["win_r"])
        with BuildSketch() as sc:
            with Locations((0, m["mask_h"] / 2 - (m["cam_from_top"] - MASK_INSET))):
                Circle(CAM_HOLE_D / 2)
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("MASKA")
        exp.add_layer("KAMERA_VOLITELNE")
        exp.add_shape(sk.sketch.faces()[0].outer_wire(), layer="MASKA")
        exp.add_shape(sw.sketch.faces()[0].outer_wire(), layer="MASKA")
        exp.add_shape(sc.sketch.faces()[0].outer_wire(), layer="KAMERA_VOLITELNE")
        p = os.path.join(d, "HP04M_maska.dxf")
        exp.write(p)
        dxfs.append(p)
        # one MDF rib of the convex bending mould
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("REZ")
        exp.add_shape(mould_rib_wire()[0], layer="REZ")
        p = os.path.join(d, "HP04_forma_rebro.dxf")
        exp.write(p)
        dxfs.append(p)
    except Exception as ex:  # pragma: no cover
        print("  (DXF export skipped:", ex, ")")
    # keep the versioned copy that nova_v8/export_v8.py packs into sklo/ in step (only this variant's HP04* files)
    if os.path.isdir(SKLO_DIR):
        import shutil
        for f in [svg] + dxfs:
            shutil.copy2(f, os.path.join(SKLO_DIR, os.path.basename(f)))
    return svg, dxfs


# ===========================================================================================

def build():
    t0 = time.time()
    h01 = HA.shell_h01()
    print(f"  shell {time.time() - t0:.1f}s")
    ear_l, ring_l = HA.ear_left()
    pcb_l = HA.ear_pcb_left()
    g = glass_numbers()
    U = 40.0          # head lift in exploded views (head A convention)
    P = [
        PartRec("HP01", "Hlavný obal hlavy", HA.step_safe("HP01", h01), "white", SUB, J, (0, 0, U),
                note="= H01 hlavy A: 106×66×74, JEDEN KUS bez zadného krytu (žiadna škára, skrutka, port ani vetranie "
                     "zvonku), kapsa valca so skrytými vetracími drážkami v strope, nálitky čapov M3, lišty serva, "
                     "misky uší, bloky s magnetmi, podložky skrutiek zospodu"),
        PartRec("HP03", "Predný rám (zakrivený)", bezel(), "black", SUB, J, (0, -45, U),
                note=f"101×69 R23.5, čelo valec R{R_FACE:.1f} (zvislá os), vystupuje {g['bezel_proud_center']:.1f} mm "
                     f"v strede / {g['bezel_proud_side']:.1f} mm na bokoch, zakrivené lôžko skla R{R_SEAT:.1f}, klin = "
                     f"rovné lôžko displeja (pena {FOAM}), lem 101.7×69.7 ako hlava A (vôľa 0.15, zavreté dno škáry), "
                     f"3 nálitky pre HP07"),
        PartRec("HP04", "Krycie sklo (zakrivené)", cover(), "glass", SUB, J, (0, -62, U),
                note=f"dymové liate PMMA {T_COVER:.1f} mm ohnuté za tepla, valec R{R_OUT:.0f}/R{R_IN:.0f}, rozvinutý "
                     f"prírez {BLANK_W}×{BLANK_H:.0f} R{BLANK_R:.0f}, čierna maska zvnútra (okno = aktívna plocha + 0.5), "
                     f"VHB {ADH}, {RECESS} mm pod čelom rámu; vzduch k LCD {g['gap_center']:.1f} mm v strede "
                     f"(dotyk cez sklo nefunguje)"),
        PartRec("HP04E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -62, U),
                note="len objekt pre render: dve pilulky 10.5×17.5 na zakrivení skla"),
        PartRec("HP04C", "Okienko kamery", camera_dot(), "black_gloss", SUB, J, (0, -62, U), internal=True,
                note="len objekt pre render: voliteľná kamera za maskou (zvonku nevidno)"),
        PartRec("HP04F", "Rozvinutý prírez skla", flat_blank(), "glass", SUB, J, (0, -95, U), internal=True,
                note=f"rovinný prírez na laser {BLANK_W}×{BLANK_H:.0f} R{BLANK_R:.0f} (len obrys, hr. 0.1); forma MDF "
                     f"konvexná R{R_IN:.0f}"),
        PartRec("HP05-R", "Ucho pravé", mirror(ear_l, Plane.YZ), "black", SUB, J, (-30, 0, U),
                note="= H05 hlavy A: Ø28 kupola, vystupuje 4 mm, bez otvoru"),
        PartRec("HP05-L", "Ucho ľavé", ear_l, "black", SUB, J, (30, 0, U),
                note="= H05 hlavy A: Ø28 kupola, vystupuje 4 mm, bez otvoru"),
        PartRec("HP06-R", "LED krúžok ucha pravý", mirror(ring_l, Plane.YZ), "cyan_led", SUB, J, (-42, 0, U),
                note="svetlovod Ø23/Ø17 zarovno s kupolou"),
        PartRec("HP06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (42, 0, U),
                note="svetlovod Ø23/Ø17 zarovno s kupolou"),
        PartRec("HP07", "Držiak displeja", HA.bracket_h07(), "grey", SUB, J, (0, -18, U), internal=True,
                note="= H07 hlavy A: pritlačí dosku na rovné lôžko HP03 (3× M2×6), horné oká s magnetmi, spodné oká "
                     "pre skrutky zospodu"),
        PartRec("HP09", "Ozubený segment náklonu", HA.barrel_disc(1, True), "grey", SUB, "J2", (12, 0, 0),
                internal=True, note="= H09 hlavy A: 20z m1 ±63° na +X konci valca N06"),
        PartRec("HP10", "Púzdro čapu náklonu", HA.barrel_disc(-1, False), "grey", SUB, "J2", (-12, 0, 0),
                internal=True, note="= H10 hlavy A na −X konci valca N06"),
        PartRec("HP11", "Koliesko serva náklonu", HA.servo_gear_h11(), "grey", SUB, J, (12, -10, U + 40),
                internal=True, note="= H11 hlavy A: 20z m1 na drážkovaní MG90S, prevod 1:1"),
        PartRec("EP31", "Displej ESP32-S3 3.5\" (doska)", HA.display_e31(), "display", SUB, J, (0, -30, U),
                internal=True, note=f"{S.DISPLAY['board']} – 86×56×6 rovná, čelo LCD y {Y_DSP0:.1f} (ako hlava A), na "
                                    f"pene {FOAM}; vzduch ku sklu {g['gap_center']:.1f} mm v strede / "
                                    f"{g['gap_lcd_edge']:.1f} mm na okraji LCD"),
        PartRec("EP32", "Servo náklonu MG90S", HA.servo_e32(), "servo", SUB, J, (22, -10, U + 40), internal=True,
                note="MG90S, hriadeľ (y 0, z 147) ∥ X, vedľa kapsy valca (+X), zasunie sa spredu do líšt"),
        PartRec("EP33-R", "DPS ucha pravá", mirror(pcb_l, Plane.YZ), "pcb", SUB, J, (-20, 0, U), internal=True,
                note="okrúhly modul 7× WS2812B Ø23"),
        PartRec("EP33-L", "DPS ucha ľavá", pcb_l, "pcb", SUB, J, (20, 0, U), internal=True,
                note="okrúhly modul 7× WS2812B Ø23"),
        PartRec("MP31-R", "Čap náklonu M3×12 pravý", HA.pin_m31(-1), "metal", SUB, J, (-18, 0, U), internal=True,
                note="DIN 912 M3×12 = čap na osi náklonu"),
        PartRec("MP31-L", "Čap náklonu M3×12 ľavý", HA.pin_m31(1), "metal", SUB, J, (18, 0, U), internal=True,
                note="DIN 912 M3×12 = čap na osi náklonu"),
    ]
    for i, (sx, in_h07) in enumerate(((-1, True), (1, True), (-1, False), (1, False))):
        P.append(PartRec(f"MP32-{i + 1}", f"Magnet Ø6×3 N52 ({'HP07' if in_h07 else 'HP01'}, "
                                          f"{'pravý' if sx < 0 else 'ľavý'})", HA.magnet(sx, in_h07), "metal", SUB, J,
                         (0, -18 if in_h07 else 0, U), internal=True,
                         note="neodýmový disk Ø6×3 N52 vlepený (CA) – drží vrch predného modulu"))
    for sx, side in ((-1, "R"), (1, "L")):
        P.append(PartRec(f"MP33-{side}", f"Skrutka M2×6 zospodu ({'pravá' if sx < 0 else 'ľavá'})", HA.screw_m33(sx),
                         "metal", SUB, J, (0, 0, U - 15), internal=True,
                         note="DIN 7985 M2×6, hlava zapustená zospodu v HP01, do oka HP07 – zvonku nevidno"))
    for p in P:
        check(p.id, p.shape)
    print(f"  build {time.time() - t0:.1f}s")
    return P


# ============================================================================================
# checks
# ============================================================================================

# intended overlaps (same fits as head A): M3 pivots thread-form into the HP01 pilots, HP11 pressed on the spline,
# M2 underside screws thread-form into the HP07 pilots
FITS = {("HP01", "MP31-R"), ("HP01", "MP31-L"), ("HP11", "EP32"), ("HP07", "MP33-R"), ("HP07", "MP33-L")}
# the detailed head components of nova_v8/cad_internals.py (made for head A, same positions in A+) duplicate
# the envelopes EP31 / EP32 / EP33 here; IH04 is pressed into HP11 like EP32
DUPES = {("IH01", "EP31"), ("IH02", "EP31"), ("IH03", "EP31"), ("IH04", "EP32"), ("IH04", "HP11"),
         ("IH07-R", "EP33-R"), ("IH07-L", "EP33-L")}
RENDER_ONLY = ("HP04C", "HP04E", "HP04F")


def others():
    """Parts of the other v8 modules in build_v8/manifest (base, torso, internals; head A excluded)."""
    return HA.other_parts(False)


NEW_PARTS = ("HP03", "HP04", "HP04E", "HP04C", "HP04F")     # the only geometry that differs from head A
PAN_STEPS = (-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90)


def pose_sweep(parts, oth, full=True):
    """Head-frame check (head A convention): J2 parts rotate by -tilt, J1 parts by -pan then -tilt.
    full=False checks only the A+ front (HP03 / HP04) against the torso / collar / arm rings - the rest is head A."""
    head = [p for p in parts if p.joint == "J3" and p.id not in RENDER_ONLY]
    outer = ("HP01", "HP03", "HP04", "HP05-R", "HP05-L", "MP33-R", "MP33-L") if full else ("HP03", "HP04")
    head_out = [p for p in parts if p.id in outer]
    j2 = [p for p in parts + oth if p.joint == "J2"]
    j1 = [p for p in oth if p.joint == "J1" and not p.internal and p.shape.bounding_box().max.Z > 99.0]
    gear_pair = {("HP11", "HP09"), ("HP09", "HP11")}
    servo_axis = Axis((0, HA.TILT_Y, HA.SERVO_Z), (1, 0, 0))
    res = []
    for th in (-20, -10, 0, 10, 20):
        if full:
            for q in j2:
                qs = q.shape.rotate(HA.TILT_AXIS, -th)
                for h in head:
                    hs = h.shape.rotate(servo_axis, th) if (h.id, q.id) in gear_pair else h.shape
                    v = HA.common_vol(hs, qs)
                    if v > 0.5 or v < 0:
                        res.append((f"tilt {th}", h.id, q.id, round(v, 2)))
        for ph in (PAN_STEPS if (abs(th) == 20 or not full) else ()):
            for q in j1:
                qs = q.shape.rotate(Axis.Z, -ph).rotate(HA.TILT_AXIS, -th)
                for h in head_out:
                    v = HA.common_vol(h.shape, qs)
                    if v > 0.5 or v < 0:
                        res.append((f"tilt {th} pan {ph}", h.id, q.id, round(v, 2)))
    return res


def bb_gap(a, b):
    """Lower bound of the distance between two shapes from their axis-aligned boxes."""
    d = [max(0.0, b.min.X - a.max.X, a.min.X - b.max.X), max(0.0, b.min.Y - a.max.Y, a.min.Y - b.max.Y),
         max(0.0, b.min.Z - a.max.Z, a.min.Z - b.max.Z)]
    return math.sqrt(sum(v * v for v in d))


def min_gaps(parts, oth, ids=("HP03", "HP04"), far=10.0):
    """Smallest distances of the curved front (HP03 / HP04; + HP01 with --full) to the collar / torso / arm rings
    over tilt -20..+20 and pan -90..+90 (head frame).  Exact distance only where the box bound can beat the best so
    far; pairs that never come closer than `far` are reported as '>far'.  Returns {pair: (gap mm, (tilt, pan))}."""
    out = {}
    mine = {p.id: p.shape for p in parts if p.id in ids}
    for q in oth:
        if q.internal or q.joint != "J1" or q.shape.bounding_box().max.Z < 95.0:
            continue
        poses = []
        for th in (-20, -10, 0, 10, 20):
            for ph in PAN_STEPS:
                poses.append(((th, ph), q.shape.rotate(Axis.Z, -ph).rotate(HA.TILT_AXIS, -th)))
        for hid, hs in mine.items():
            hb = hs.bounding_box()
            # HP01 (= head A H01, many faces): the coarse pose set of nova_v8/cad_head.py, the sweep covers the rest
            sel = [t for t in poses if hid != "HP01" or (t[0][0] in (-20, 0, 20) and t[0][1] in (-90, 0, 90))]
            cand = sorted(((bb_gap(hb, qs.bounding_box()), at, qs) for at, qs in sel), key=lambda t: t[0])
            if cand[0][0] > far:
                out[f"{hid}-{q.id}"] = (f">{far:g}", None)
                continue
            best, at_best = 1e9, None
            for g0, at, qs in cand:
                if g0 >= best:
                    break
                dd = hs.distance_to(qs)
                if dd < best:
                    best, at_best = dd, at
            out[f"{hid}-{q.id}"] = (round(best, 2), at_best)
    return out


DENS = {"white": 1.15, "black": 1.15, "grey": 1.0, "glass": 1.19, "cyan_led": 1.19, "black_gloss": 1.19}
FIXED_G = {"EP31": 50.0, "EP32": 13.4, "EP33-R": 2.5, "EP33-L": 2.5}


def mass_report(parts):
    """Mass + CG of the tilting group (J3) relative to the tilt axis, tilt-servo load over +-20 deg."""
    m_tot, my, mz = 0.0, 0.0, 0.0
    for p in parts:
        if p.joint != "J3" or p.id in RENDER_ONLY:
            continue
        c = p.shape.center()
        if p.id in FIXED_G:
            m = FIXED_G[p.id]
        elif p.mat == "metal":
            m = p.shape.volume / 1000 * (7.5 if p.id.startswith("MP32") else 7.85)
        else:
            m = p.shape.volume / 1000 * DENS.get(p.mat, 1.2)
        m_tot += m
        my += m * (c.Y - HA.TILT_Y)
        mz += m * (c.Z - HA.TILT_Z)
    cy, cz = my / m_tot, mz / m_tot
    lev = max(abs(cy * math.cos(math.radians(t)) - cz * math.sin(math.radians(t))) for t in range(-20, 21, 5))
    return dict(mass_g=round(m_tot, 1), cg_ahead=round(-cy, 1), cg_above=round(cz, 1),
                max_kgcm=round(m_tot / 1000 * lev / 10, 3))


def clean_stale(ids):
    """Remove STL/STEP files of parts that no longer exist (v8.0 HP02 back cover etc.)."""
    gone = []
    for d, ext in (("stl", ".stl"), ("step", ".step")):
        dd = os.path.join(OUT_DIR, d)
        if not os.path.isdir(dd):
            continue
        for fn in os.listdir(dd):
            if fn.endswith(ext) and fn[:-len(ext)] not in ids:
                os.remove(os.path.join(dd, fn))
                gone.append(fn)
    return gone


def verify_step(parts):
    bad = []
    for p in parts:
        s = import_step(os.path.join(OUT_DIR, "step", f"{p.id}.step"))
        v0 = p.shape.volume
        if not s.is_valid or abs(s.volume - v0) > 1e-4 * v0 + 0.01:
            bad.append((p.id, s.is_valid, round(s.volume, 2), round(v0, 2)))
    return bad


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
    print("  removed stale files:", clean_stale({p.id for p in ps}) or "none")
    for p, r in zip(ps, recs):
        print(f"  {r['id']:7s} {r['mat']:11s} {r['joint']:3s} {'int' if r['internal'] else '   '} "
              f"valid={p.shape.is_valid} size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
    bad = verify_step(ps)
    print("  STEP re-import:", f"{len(ps)} OK" if not bad else bad)
    print("  mass:", mass_report(ps))
    print("  interference (own):", HA.interference(ps, skip=FITS) or "none")
    by = {p.id: p.shape for p in ps}
    print(f"  EP31 clearance: HP03 {by['EP31'].distance_to(by['HP03']):.2f}  HP04 {by['EP31'].distance_to(by['HP04']):.2f}"
          f"  HP01 {by['EP31'].distance_to(by['HP01']):.2f} mm")
    print(f"  HP04 clearance to HP03: {by['HP04'].distance_to(by['HP03']):.2f} mm,  HP03 to HP01: "
          f"{by['HP03'].distance_to(by['HP01']):.2f} mm,  HP03 to HP07: {by['HP03'].distance_to(by['HP07']):.2f} mm")
    g = glass_numbers()
    print("  glass:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()})
    print("  mask:", {k: round(v, 2) for k, v in mask_numbers().items()})
    svg, dxfs = write_blank_files(OUT_DIR)
    print("  blank files:", svg, dxfs)
    if "--check" in sys.argv or "--pose" in sys.argv:
        full = "--full" in sys.argv          # HP01/ears/drive = head A parts (checked in nova_v8/cad_head.py)
        oth = others()
        print(f"  loaded {len(oth)} parts of other modules")
        if "--check" in sys.argv:
            mine = ps if full else [p for p in ps if p.id in NEW_PARTS]
            print(f"  interference ({'all' if full else 'A+ front'} with others):",
                  HA.interference(mine, oth, skip=FITS | DUPES) or "none")
            print("  min gaps over tilt +-20 / pan +-90:",
                  min_gaps(ps, oth, ("HP01", "HP03", "HP04") if full else ("HP03", "HP04")))
        if "--pose" in sys.argv:
            print("  pose sweep:", pose_sweep(ps, oth, full=full) or "none")
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
