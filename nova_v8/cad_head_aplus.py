"""
NOVA mini v8.1 - HEAD variant A+ "A s jemne zakriveným sklom" (curved R180 cover), manifest "head_aplus".
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.cad_head_aplus [--check] [--pose]
Exports STEP (first) + STL + manifest into build_v8_var_aplus/ (never build/ or build_v8/), plus
build_v8_var_aplus/blank/ : HP04F_prirez.svg (1:1 blank + vinyl mask + mould rib template), HP04F_prirez.dxf
(laser outline of the flat blank) and HP04_forma_rebro.dxf (laser outline of one MDF mould rib).

v8.1 "MODERNY - NIC NEVIDNO": A+ = the CURRENT v8.1 head A (nova_v8/cad_head.py, imported - its shell, ears,
tilt drive, display bracket and hidden retention follow head A automatically) with ONLY the front module
replaced by a gently curved one:
  * monolithic white shell HP01 (= H01): no back cover, no seam / screw / port / vent on the back, top or sides;
    the only visible split is white shell / protruding black bezel, 0.5 mm, even all round (6 guide ribs).
  * front module = HP03 curved bezel + HP04 curved cover + EP31 flat 3.5" board + HP07 bracket; it slides in
    along +Y exactly like head A (same skirt, ribs, 3 bracket bosses, display position y -33.8), 2 pairs of
    magnets at the top, 2x M2 from the UNDERSIDE (flush counterbores, reached with the head tilted +20 deg).
  * dead front: smoked cast PMMA 2.0 with a black inner mask, 0.3 mm under the bezel face; the optional camera
    (HP04C) is render-only/internal - nothing to see when the face is off.
  * vents: as head A - air in through the barrel-pocket mouth, slots in the pocket ceiling, out through the
    bezel seam at the top; the microphone hears through the same seam.  Nothing on the outside.

Curved cover (local constants of this variant):
  HP04 = smoked CAST PMMA 2.0 mm, laser-cut FLAT as the developed blank HP04F (92.5 x 60 R16 on the neutral
  layer R179), heat-bent (150-160 C) by gravity over a convex MDF mould R178 (= inner radius) so the visible
  outer face never touches the mould; single curvature -> the black mask is a flat vinyl sticker (or paint).
  Vertical cylinder axis at x 0, y +137.55; outer R180 / inner R178, projected 92.0 x 60, sag 6.0 mm.
  The cover is bonded (VHB 0.2) on a CURVED SEAT R177.8 that runs all round under the mask (support 4.4 .. 8.5
  mm wide).  Between the curved seat and the FLAT board the bezel fills a wedge whose flat back face (y -34.3)
  is the board seat (foam 0.5, board pressed by HP07 exactly as in head A) - the wedge is >= 0.6 thick at the
  board-pocket edge x +-43.3, which sets the cover position: apex y -42.45, bezel face apex y -42.75 ->
  the black frame protrudes 9.75 mm from the white rim at the centre line and 2.5 mm at the sides.
  Gap cover -> LCD: 6.65 mm at the centre, 1.4 mm at the board edges.

Parts (sub "head_aplus"; J3 = head tilt about X through y 0 z 127, J2 = pan stage)
  HP01     Hlavny obal hlavy          white     = head A H01 (one piece, barrel pocket, tilt-servo rails, pivot
                                                bosses, ear cups, magnet blocks, underside screw pads, hidden vents)
  HP03     Predny ram (zakriveny)     black     101 x 69 R23.5, face = cylinder R180.3, curved cover seat + wedge
                                                board seat, window 75.6 x 49.1, skirt 4 mm into HP01 with 6 guide
                                                ribs, 3 bosses for HP07 (head A interface)
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
  EP31     Displej ESP32-S3 3.5"      display   86 x 56 x 6 board, LCD front y -33.8 (flat)
  EP32     Servo naklonu MG90S        servo     shaft (y 0, z 147) // X, beside the barrel pocket (+X)
  EP33-R/L DPS ucha                   pcb       Ø23 7x WS2812B module
  MP31-R/L Cap naklonu M3x12          metal     pivot pins on the tilt axis
  MP32-1..4 Magnet Ø6x3 N52           metal     front-module latch (2 in HP07, 2 in HP01)
  MP33-R/L Skrutka M2x6 zospodu       metal     DIN 7985, heads flush in the HP01 underside
HP09/HP10 duplicate head A's H09/H10 (same physical parts on the barrel) - when rendering A+ together with the
"head" manifest exclude one pair.

FDM: HP03 printed STANDING on its bottom edge (cylinder axis = printer Z) -> the R180.3 face is built from true
arcs, no stair-stepping; tree support under the top skirt wall and the top ledge; sand + satin black.  HP01, HP05,
HP06, HP07, HP09..HP11 as head A.

Deviations (local constants, nova_v8/spec.py untouched): bezel protrudes 9.75 mm at the centre / 2.5 at the sides
(spec bezel.protrude 5.0 = head A, flat); cover 92.5 x 60 developed (92.0 x 60 projected) instead of the flat
92 x 60; the top 1.5 mm of the active area hides behind the 7 mm top mask band (same as head A).
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Axis, BuildSketch, Cylinder, Edge, Face, Plane, Pos, RectangleRounded, Solid, Sphere, Vector,
                       Wire, import_step, mirror)
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
SUB = "head_aplus"
MANIFEST = "head_aplus"
J = "J3"

# ---- shared with head A (read from nova_v8/cad_head.py) -------------------------------------------------
H = S.HEAD
BZ, GL, EYE, CAM = HA.BZ, HA.GL, HA.EYE, HA.CAM
Y0, ZC = HA.Y0, HA.ZC                                      # white front rim plane y -33, head centre z 154
DSP_W, DSP_H, DSP_T = HA.DSP_W, HA.DSP_H, HA.DSP_T         # 86 x 56 x 6
ACT_W, ACT_H = S.DISPLAY["active"]                         # 73.44 x 48.96
Y_DSP0, Y_DSP1, DSP_ZC = HA.Y_DSP0, HA.Y_DSP1, HA.DSP_ZC   # LCD front -33.8, board back -27.8, centre z 154
DSP_R, DSP_CLR, FOAM = HA.DSP_R, HA.DSP_CLR, HA.FOAM
SKIRT_END, SKIRT_WALL = HA.SKIRT_END, HA.SKIRT_WALL        # skirt to y -29, wall 1.6
Y_SEAT = Y_DSP0 - FOAM                                     # -34.3 flat board seat (= head A ledge back)

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
SEAT_MIN = 0.6             # thinnest point of the wedge board seat (at the board-pocket edge)
LEDGE_T = 1.6              # curved ledge thickness where the bezel is hollow behind it
R_LB = R_SEAT - LEDGE_T    # 176.2
RIM, RIM_D = 1.6, 1.5      # locating rim around the board pocket behind the seat plane
BLANK_W, BLANK_H, BLANK_R = 92.5, GL["h"], GL["r"]          # developed blank 92.5 x 60 R16
BZ_FRONT_FILLET = 2.4      # soft outer edge of the black frame
SEAT_EDGE = 0.4            # break on the seat edge in the bezel face
PRINT_TOP = GL["print_top"]   # 7 mm top mask band
MASK_MARGIN = 0.6          # mask window = active area + 0.6 (top edge limited by the band)
OPEN_MARGIN = 0.5          # bezel window 0.5 outside the mask window (never seen through the window)
OPEN_R = 2.5
CAM_HOLE_D = 3.6           # optional clear hole in the mask for the camera
BLANK_GAP = 0.5            # the flat blank reference part floats 0.5 in front of the cover apex

# derived positions
X_PK = DSP_W / 2 + DSP_CLR                                             # 43.3 board pocket half width
Y_AX = Y_SEAT - SEAT_MIN + math.sqrt(R_SEAT ** 2 - X_PK ** 2)          # +137.55 cylinder axis
Y_OUT_APEX = Y_AX - R_OUT                                              # -42.45
Y_IN_APEX = Y_AX - R_IN                                                # -40.45
Y_FACE_APEX = Y_AX - R_FACE                                            # -42.75


def mask_window():
    """Mask window in the FRONT VIEW (x half width, z bottom, z top)."""
    return ACT_W / 2 + MASK_MARGIN, DSP_ZC - ACT_H / 2 - MASK_MARGIN, ZC + BLANK_H / 2 - PRINT_TOP


# ===========================================================================================
# helpers
# ===========================================================================================
check, retry, edges_where, try_fillet = HA.check, HA.retry, HA.edges_where, HA.try_fillet
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
    raw = check("HP03 raw", rr_prism_y(bw, bh, br, Y_FACE_APEX - 2.0, SKIRT_END) & cyl_z(R_FACE))
    loop = edges_where(raw, lambda p: abs(r_axis(p) - R_FACE) < 0.02)
    b = try_fillet(raw, loop, BZ_FRONT_FILLET, "HP03 front edge")
    # hollow behind the curved ledge, except the wedge block that seats the board (+ locating rim)
    cav = rr_prism_y(bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL, Y_FACE_APEX - 2.0,
                     SKIRT_END + 1.0) & cyl_z(R_LB)
    blk = rr_prism_y(2 * (X_PK + RIM), DSP_H + 2 * (DSP_CLR + RIM), DSP_R + DSP_CLR + RIM, Y_FACE_APEX - 3.0,
                     Y_SEAT + RIM_D, cz=DSP_ZC)
    b = retry(lambda: b - (cav - blk), "HP03 cavity")
    # board pocket behind the flat seat (as head A: board + 0.3)
    b = retry(lambda: b - rr_prism_y(DSP_W + 2 * DSP_CLR, DSP_H + 2 * DSP_CLR, DSP_R + DSP_CLR, Y_SEAT,
                                     SKIRT_END + 1.0, cz=DSP_ZC), "HP03 board pocket")
    # window through the wedge (0.5 outside the mask window -> hidden behind the mask)
    xw, zb, zt = mask_window()
    xo, zo0, zo1 = xw + OPEN_MARGIN, zb - OPEN_MARGIN, zt + OPEN_MARGIN
    b = retry(lambda: b - rr_prism_y(2 * xo, zo1 - zo0, OPEN_R, Y_FACE_APEX - 3.0, Y_SEAT + 0.01,
                                     cz=(zo0 + zo1) / 2), "HP03 window")
    # 3 bosses for the HP07 screws (head A positions, end faces on the board-back plane) + ribs to the skirt
    for (x, z) in HA.BZ_BOSSES:
        boss = cyl_y(HA.BOSS_R, Y_FACE_APEX - 2.0, Y_DSP1, x, z)
        if x != 0:
            boss = boss + bx(x, math.copysign(bw / 2 - 1.0, x), Y0 - 0.5, SKIRT_END, z - 1.0, z + 1.0)
        clip = rr_prism_y(bw - 0.4, bh - 0.4, br - 0.2, Y_FACE_APEX - 3.0, Y_DSP1 + 1.0) & cyl_z(R_FACE - 0.6)
        b = retry(lambda: b + (boss & clip), "HP03 boss")
    # 6 guide ribs on the skirt (copy of head A: centre the module -> even 0.5 seam all round)
    ring = rr_prism_y(bw + 2 * HA.RIB_H, bh + 2 * HA.RIB_H, br + HA.RIB_H, HA.RIB_Y[0], HA.RIB_Y[1]) - \
        rr_prism_y(bw - 0.4, bh - 0.4, br - 0.2, HA.RIB_Y[0] - 1, HA.RIB_Y[1] + 1)
    wins = [bx(sx * 19.0, sx * 21.0, -40, -20, ZC + sz * 30, ZC + sz * 40) for sx in (1, -1) for sz in (1, -1)] + \
        [bx(sx * 45.0, sx * 60.0, -40, -20, ZC - 1.0, ZC + 1.0) for sx in (1, -1)]
    b = retry(lambda: b + (ring & union(wins)), "HP03 guide ribs")
    # curved cover seat (radial walls = the bent blank + 0.3), then the M2 pilots
    seat = radial_patch(R_SEAT, R_FACE + 2.0, BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR)
    b = retry(lambda: b - seat, "HP03 seat")
    for (x, z) in HA.BZ_BOSSES:
        b = retry(lambda: b - cyl_y(HA.PILOT_R, Y_DSP1 + 0.1, Y_DSP1 - 6.0, x, z), "HP03 pilot")
    b = solid1(b)
    if len(b.solids()) != 1:
        raise RuntimeError(f"HP03: {len(b.solids())} solids")
    sw, sh, sr = BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR
    e_seat = edges_where(b, lambda p: abs(r_axis(p) - R_FACE) < 0.02
                         and abs(rr_dist(s_dev(p, R_MID), p.Z, sw, sh, sr)) < 0.15)
    b = try_fillet(b, e_seat, SEAT_EDGE, "HP03 seat edge")
    return check("HP03", solid1(b), vmin=3000)


def cover():
    return check("HP04", radial_patch(R_IN, R_OUT, BLANK_W, BLANK_H, BLANK_R), vmin=5000)


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
    xw, z_bot, z_top = mask_window()                                # 37.32, 128.92, 177.0
    s_w = R_IN * math.asin(xw / R_IN)                               # developed half width on R178
    return dict(win_w=2 * s_w, win_h=z_top - z_bot, win_r=2.0, win_zc=(z_top + z_bot) / 2,
                win_top_from_edge=ZC + BLANK_H / 2 - z_top, win_bot_from_edge=z_bot - (ZC - BLANK_H / 2),
                cam_from_top=ZC + BLANK_H / 2 - CAM["z"], mask_w=BLANK_W * R_IN / R_MID - 0.6,
                mask_h=BLANK_H - 0.6)


def glass_numbers():
    half = BLANK_W / 2 / R_MID
    sag_out = R_OUT * (1 - math.cos(half))
    x_act = ACT_W / 2
    return dict(R_out=R_OUT, R_in=R_IN, t=T_COVER, blank=(BLANK_W, BLANK_H, BLANK_R),
                proj_w=2 * R_OUT * math.sin(half), sag=sag_out,
                gap_center=Y_DSP0 - Y_IN_APEX, gap_active_edge=Y_DSP0 - y_on_cyl(R_IN, x_act),
                gap_board_edge=Y_DSP0 - y_on_cyl(R_IN, DSP_W / 2),
                seat_min=Y_SEAT - y_on_cyl(R_SEAT, X_PK),
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
    # --- vinyl mask ---
    mx, my = 122.0, 32.0
    mw, mh = m["mask_w"], m["mask_h"]
    wx = mx + mw / 2 - m["win_w"] / 2
    wy = my + (m["win_top_from_edge"] - 0.3)
    ccx, ccy = mx + mw / 2, my + m["cam_from_top"] - 0.3
    a(f'<text x="{mx}" y="{my - 4}" font-size="3.4" font-weight="bold">2  Maska – čierna fólia, VNÚTORNÁ strana</text>')
    path = (f'M{mx + BLANK_R},{my} h{mw - 2 * BLANK_R} a{BLANK_R},{BLANK_R} 0 0 1 {BLANK_R},{BLANK_R} '
            f'v{mh - 2 * BLANK_R} a{BLANK_R},{BLANK_R} 0 0 1 -{BLANK_R},{BLANK_R} h-{mw - 2 * BLANK_R} '
            f'a{BLANK_R},{BLANK_R} 0 0 1 -{BLANK_R},-{BLANK_R} v-{mh - 2 * BLANK_R} a{BLANK_R},{BLANK_R} 0 0 1 {BLANK_R},-{BLANK_R} Z ')
    wr = m["win_r"]
    path += (f'M{wx + wr},{wy} h{m["win_w"] - 2 * wr} a{wr},{wr} 0 0 1 {wr},{wr} v{m["win_h"] - 2 * wr} '
             f'a{wr},{wr} 0 0 1 -{wr},{wr} h-{m["win_w"] - 2 * wr} a{wr},{wr} 0 0 1 -{wr},-{wr} '
             f'v-{m["win_h"] - 2 * wr} a{wr},{wr} 0 0 1 {wr},-{wr} Z')
    a(f'<path d="{path}" fill="#111" fill-rule="evenodd" stroke="#e00000" stroke-width="0.12"/>')
    rh = CAM_HOLE_D / 2
    a(f'<circle cx="{ccx}" cy="{ccy}" r="{rh}" fill="none" stroke="#e00000" stroke-width="0.15" stroke-dasharray="0.8 0.5"/>')
    a(f'<text x="{wx + 3}" y="{wy + 8}" font-size="2.8" fill="#444">okno displeja {m["win_w"]:.1f} × {m["win_h"]:.1f} R{wr:.0f}</text>')
    a(f'<text x="{wx + 3}" y="{wy + 12}" font-size="2.4" fill="#444">aktívna plocha 3.5" + {MASK_MARGIN} mm</text>')
    a(f'<text x="{wx + 3}" y="{wy + 15.5}" font-size="2.4" fill="#444">horný pás {PRINT_TOP:.0f} mm, dolný {m["win_bot_from_edge"]:.1f} mm, '
      f'bočné {(mw - m["win_w"]) / 2:.1f} mm</text>')
    a(f'<polyline points="{ccx + rh},{ccy} {mx + mw - 6},{my - 1.5} {mx + mw + 1},{my - 1.5}" fill="none" stroke="#e00000" stroke-width="0.15"/>')
    a(f'<text x="{mx + mw + 2}" y="{my - 0.6}" font-size="2.4">VOLITEĽNÝ otvor kamery Ø{CAM_HOLE_D}</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 3}" font-size="2.4">stred {m["cam_from_top"]:.1f} od hornej hrany</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 6.5}" font-size="2.4">(bez kamery nevyrezať)</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 12}" font-size="2.4">symetrická – zvnútra</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 15.5}" font-size="2.4">sa nezrkadlí</text>')
    a(f'<text x="{mx}" y="{my + mh + 5}" font-size="2.5">rozvinuté na vnútornom povrchu R{R_IN:.0f}: {mw:.1f} × {mh:.1f} '
      f'(o 0.3 menšie po obvode) – nalepiť až PO ohnutí</text>')
    # --- mould rib template ---
    fx, fy = 14.0, 118.0
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
        f"6. Vlepiť do zakriveného lôžka rámu HP03 (R{R_SEAT:.1f}, po celom",
        f"    obvode pod maskou) na obojstrannú pásku VHB {ADH} mm;",
        f"    čelo skla je {RECESS} mm pod čelom rámu (pôsobí zarovno).",
        f"Alternatíva: PC 0.75–1.0 mm za studena (R{R_OUT:.0f} > 150×t).",
        f"Medzera k displeju: stred {g['gap_center']:.1f} mm, okraj DPS {g['gap_board_edge']:.1f} mm",
        "    (klin rámu za sklom = rovné lôžko displeja, pena 0.5).",
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
        with BuildSketch() as sk:
            RectangleRounded(BLANK_W, BLANK_H, BLANK_R)
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("REZ")
        exp.add_shape(sk.sketch.faces()[0].outer_wire(), layer="REZ")
        p = os.path.join(d, "HP04F_prirez.dxf")
        exp.write(p)
        dxfs.append(p)
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("REZ")
        exp.add_shape(mould_rib_wire()[0], layer="REZ")
        p = os.path.join(d, "HP04_forma_rebro.dxf")
        exp.write(p)
        dxfs.append(p)
    except Exception as ex:  # pragma: no cover
        print("  (DXF export skipped:", ex, ")")
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
                     f"v strede / {g['bezel_proud_side']:.1f} mm na bokoch, zakrivené lôžko skla R{R_SEAT:.1f} po celom "
                     f"obvode, klin = rovné lôžko displeja, lem 4 mm do HP01 so 6 vodiacimi rebrami, 3 nálitky pre HP07"),
        PartRec("HP04", "Krycie sklo (zakrivené)", cover(), "glass", SUB, J, (0, -62, U),
                note=f"dymové liate PMMA {T_COVER:.1f} mm ohnuté za tepla, valec R{R_OUT:.0f}/R{R_IN:.0f}, rozvinutý "
                     f"prírez {BLANK_W}×{BLANK_H:.0f} R{BLANK_R:.0f}, čierna maska zvnútra (dead-front), VHB {ADH}, "
                     f"{RECESS} mm pod čelom rámu"),
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
                internal=True, note=f"{S.DISPLAY['board']} – 86×56×6 rovná, čelo LCD y {Y_DSP0}; medzera ku sklu "
                                    f"{g['gap_center']:.1f} mm v strede / {g['gap_board_edge']:.1f} mm na okraji DPS"),
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


def pose_sweep(parts, oth, full_j2=True):
    """Head-frame check (head A convention): J2 parts rotate by -tilt, J1 parts by -pan then -tilt."""
    head = [p for p in parts if p.joint == "J3" and p.id not in RENDER_ONLY]
    head_out = [p for p in parts if p.id in ("HP01", "HP03", "HP04", "HP05-R", "HP05-L", "MP33-R", "MP33-L")]
    j2 = [p for p in parts + oth if p.joint == "J2"]
    j1 = [p for p in oth if p.joint == "J1" and not p.internal and p.shape.bounding_box().max.Z > 99.0]
    gear_pair = {("HP11", "HP09"), ("HP09", "HP11")}
    servo_axis = Axis((0, HA.TILT_Y, HA.SERVO_Z), (1, 0, 0))
    res = []
    for th in ((-20, -10, 0, 10, 20) if full_j2 else (-20, 20)):
        for q in j2:
            qs = q.shape.rotate(HA.TILT_AXIS, -th)
            for h in head:
                hs = h.shape.rotate(servo_axis, th) if (h.id, q.id) in gear_pair else h.shape
                v = HA.common_vol(hs, qs)
                if v > 0.5 or v < 0:
                    res.append((f"tilt {th}", h.id, q.id, round(v, 2)))
        for ph in ((-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90) if abs(th) == 20 else ()):
            for q in j1:
                qs = q.shape.rotate(Axis.Z, -ph).rotate(HA.TILT_AXIS, -th)
                for h in head_out:
                    v = HA.common_vol(h.shape, qs)
                    if v > 0.5 or v < 0:
                        res.append((f"tilt {th} pan {ph}", h.id, q.id, round(v, 2)))
    return res


def min_gaps(parts, oth):
    """Smallest distances of the curved front (HP03 / HP04) and HP01 to the neck / torso / arms over tilt +-20 /
    pan 0, +-45, +-90 (head frame)."""
    out = {}
    mine = {p.id: p.shape for p in parts if p.id in ("HP01", "HP03", "HP04")}
    for q in oth:
        if q.internal or q.joint != "J1" or q.shape.bounding_box().max.Z < 95.0:
            continue
        for hid, hs in mine.items():
            best = 1e9
            for th in (-20, 0, 20):
                for ph in (-90, -45, 0, 45, 90):
                    qs = q.shape.rotate(Axis.Z, -ph).rotate(HA.TILT_AXIS, -th)
                    best = min(best, hs.distance_to(qs))
            out[f"{hid}-{q.id}"] = round(best, 2)
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
    vols = {p.id: p.shape.volume for p in ps}
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
          f"{by['HP03'].distance_to(by['HP01']):.2f} mm")
    g = glass_numbers()
    print("  glass:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()})
    print("  mask:", {k: round(v, 2) for k, v in mask_numbers().items()})
    svg, dxfs = write_blank_files(OUT_DIR)
    print("  blank files:", svg, dxfs)
    if "--check" in sys.argv or "--pose" in sys.argv:
        oth = others()
        print(f"  loaded {len(oth)} parts of other modules")
        if "--check" in sys.argv:
            print("  interference (with others):", HA.interference(ps, oth, skip=FITS | DUPES) or "none")
            print("  min gaps over tilt +-20 / pan +-90:", min_gaps(ps, oth))
        if "--pose" in sys.argv:
            print("  pose sweep:", pose_sweep(ps, oth, full_j2="--quick" not in sys.argv) or "none")
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
