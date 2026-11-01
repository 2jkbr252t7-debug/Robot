"""
NOVA mini v8.0 - HEAD variant A+ "A s jemne zakriveným sklom" (HP01..HP07).
Run from the repo root:  /opt/venv/cad/bin/python -m nova_v8.cad_head_aplus
Exports STL + STEP + manifest "head_aplus" into build_v8_var_aplus/ (never into build/ or build_v8/),
plus build_v8_var_aplus/blank/ : HP04F_prirez.svg (1:1 blank + vinyl mask + mould rib template) and
HP04F_prirez.dxf (laser-cut outline).

Same white shell, back cover, ears and protruding black bezel as head A (shell / back cover / ears are
taken from the concept module nova_v8/head_a.py, wall set to the v8 value 2.0 and lifted +1 mm to the
v8 heights), but the cover and the bezel face that holds it are a gentle SINGLE-CURVATURE cylinder
(vertical axis, R180 outside) -> premium "2.5D" face that is not flat, yet buildable at home:

  cover HP04 = smoked CAST PMMA 2.0 mm, laser-cut FLAT as the developed blank HP04F (92.5 x 60 R16),
  then heat-bent (oven 150-160 C) by gravity over a convex MDF mould R178 (= inner radius), so the
  visible outer face never touches the mould.  Black mask on the inside outside the display window
  (black vinyl - single curvature takes a flat sticker - or spray paint) -> dead front: glossy black when
  off, eyes shine through.  Alternative: 0.75-1.0 mm smoked PC cold-bent into the bezel seat
  (R180 > 150 x t).  The cover ends 7 mm inside the head silhouette, no wrap around the corners.

Geometry (assembly coordinates, mm; FRONT = -Y, RIGHT = -X, joint J3 = tilt about X at y 0 z 127):
  cylinder axis vertical through (x 0, y +137.7);  cover outer R180 / inner R178, apex y -42.3,
  sag 6.0 mm over the 92 mm width, bending strain 0.56 %
  bezel face = concentric cylinder R180.5 (cover sits 0.5 mm below the face), protrudes 9.8 mm from
  the white rim at the centre line and 2.6 mm at the sides (x +-50.5, the R2.4 edge rolls into the rim)
  flat 3.5" board 86 x 56 x 6 (HP07, internal) at y -34.0 .. -28.0: gap to the cover 6.3 mm at the
  centre, 1.0 mm at the board edges (x +-43), 2.4 mm at the edges of the active area.

Parts (sub "head_aplus", joint "J3")
  HP01     Hlavný obal hlavy        white        head A shell 106 x 66 x 74, wall 2.0, barrel pocket 36x40
  HP02     Zadný kryt hlavy         white        back cover 88 x 50 R15, seam 0.6
  HP03     Predný rám (zakrivený)   black        frame 101 x 69 R23.5, cylindrical face R180.5,
                                                 radial seat for the cover, curved 1.4 mm ledge, skirt
  HP04     Krycie sklo (zakrivené)  glass        smoked PMMA 2.0, R180/R178, radial edges
  HP04E    Obsah displeja – oči     eye          RENDER-ONLY pills 10.5 x 17.5 on the cover curvature
  HP04C    Okienko kamery           black_gloss  RENDER-ONLY camera dot (z 180.5, top print band)
  HP04F    Rozvinutý prírez skla    glass        INTERNAL flat blank 92.5 x 60 R16 x 0.1 (laser outline)
  HP05-R/L Ucho pravé / ľavé        black        Ø28 ear discs, 4 mm proud
  HP06-R/L LED krúžok ucha          cyan_led     Ø23 / Ø17 light guides
  HP07     Displej 3.5" (maketa)    display      INTERNAL fit dummy 86 x 56 x 6 (ESP32-S3 board)

Deviations (local constants, nova_v8/spec.py untouched): head front at y -42.8 (A: -38) because the
curved cover must clear the flat display at its edges; display centred on z 154 (= glass centre), so
the top 1.5 mm of the active area hides behind the 7 mm top print band with the camera.
export_all(): STEP files are rewritten from untessellated copies - nova.cad.common.export_parts() meshes a
shape for the STL before its STEP export, which corrupted the fillet-heavy back cover (invalid, wrong volume).
"""
from __future__ import annotations

import copy
import math
import os
import sys
import time

from build123d import (BuildSketch, Cylinder, Face, Plane, Pos, RectangleRounded, Solid, Sphere, export_step, extrude,
                       import_step, mirror)
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
from nova_v8 import concept as C  # noqa: E402
from nova_v8 import head_a as HA  # noqa: E402  (concept head A: shell, back cover, ears are reused)
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8_var_aplus")
SUB = "head_aplus"
MANIFEST = "head_aplus"

H = S.HEAD
BZ, GL, EAR, EYE, CAM = H["bezel"], H["glass"], H["ear"], H["eyes"], H["camera"]
W, HH, Y0, ZC = H["w"], H["h"], H["y0"], H["zc"]            # 106 x 74, rim plane y -33, centre z 154
DZ = H["z0"] - C.HEAD["z0"]                                  # +1.0: concept head A sits 1 mm lower
DISP_W, DISP_H, DISP_T = S.DISPLAY["outline"]               # 86 x 56 x 6
ACT_W, ACT_H = S.DISPLAY["active"]                          # 73.44 x 48.96

# ---- curved cover (local constants of this variant) -----------------------------------------------
R_OUT = 180.0              # outer radius of the cover (vertical cylinder axis)
T_COVER = 2.0              # smoked cast PMMA 2.0 mm
R_IN = R_OUT - T_COVER     # 178 = radius of the convex bending mould
R_MID = R_OUT - T_COVER / 2   # neutral layer: the flat blank is developed here
BLANK_W, BLANK_H, BLANK_R = 92.5, GL["h"], GL["r"]          # developed blank 92.5 x 60 R16 (front view ~92 x 60)
DISP_ZC = ZC               # display board centred on the glass
Y_DISP_FRONT = -34.0       # flat display front face (board back -28, 6 mm in front of the pocket wall)
DISP_CR = 3.0              # assumed corner radius of the board outline
EDGE_GAP = 1.0             # cover (inner face) -> display front at the board edges x = +-43
RECESS = 0.5               # cover front sits 0.5 below the bezel face
CLR = 0.3                  # cover edge -> bezel seat (heat-bent part tolerance)
ADH = 0.2                  # double-sided tape / glue under the cover edge
LEDGE_W, LEDGE_T = 2.5, 1.4   # curved support ledge in the bezel
SKIRT_END = Y0 + 9.0       # bezel skirt reaches 9 mm into the shell (y -24)
SKIRT_WALL = 1.8
BZ_FRONT_FILLET = 2.4      # soft outer edge of the black frame
SEAT_EDGE = 0.4            # break on the seat edge in the bezel face
DISP_RELIEF = 0.3          # clearance pockets in the bezel for the board corners
PRINT_TOP = GL["print_top"]   # 7 mm top print band (camera)
MASK_MARGIN = 0.6          # mask window = active area + 0.6 (top edge limited by the print band)
CAM_HOLE_D = 3.6           # clear hole in the mask for the camera
BLANK_GAP = 0.5            # the flat blank part floats 0.5 in front of the cover apex

# derived positions
SAG_IN_EDGE = R_IN - math.sqrt(R_IN ** 2 - (DISP_W / 2) ** 2)          # 5.27
Y_IN_APEX = Y_DISP_FRONT - EDGE_GAP - SAG_IN_EDGE                       # -41.27
Y_OUT_APEX = Y_IN_APEX - T_COVER                                        # -43.27
Y_AX = Y_OUT_APEX + R_OUT                                               # +136.73 (cylinder axis)
R_FACE = R_OUT + RECESS                                                 # bezel face radius 180.5
Y_FACE_APEX = Y_AX - R_FACE                                             # -43.77
R_LEDGE_BACK = R_IN - ADH - LEDGE_T                                     # 176.4

J = "J3"


# ===========================================================================================
# helpers
# ===========================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    return Plane(origin=(cx, y, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=ZC):
    with BuildSketch(plane_y(y0, cx, cz)) as sk:
        RectangleRounded(w, h, r)
    return extrude(sk.sketch, y1 - y0)


def cyl_z(r, height=200.0):
    """Solid vertical cylinder about the cover axis."""
    return Pos(0, Y_AX, ZC) * Cylinder(r, height)


def cyl_y(r, y0, y1, x, z):
    """Solid cylinder along Y from y0 to y1 centred on (x, z)."""
    lo, hi = min(y0, y1), max(y0, y1)
    return Solid.make_cylinder(r, hi - lo, Plane(origin=(x, lo, z), x_dir=(1, 0, 0), z_dir=(0, 1, 0)))


def y_on_cyl(r, x):
    return Y_AX - math.sqrt(r * r - x * x)


def r_axis(p):
    return math.hypot(p.X, p.Y - Y_AX)


check, retry, edges_where, try_fillet = HA.check, HA.retry, HA.edges_where, HA.try_fillet


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


def display_dummy(grow=0.0):
    g = grow
    return rr_prism_y(DISP_W + 2 * g, DISP_H + 2 * g, DISP_CR + g, Y_DISP_FRONT - g, Y_DISP_FRONT + DISP_T + g,
                      cz=DISP_ZC)


# ===========================================================================================
# HP01 / HP02 / HP05 / HP06 - reused from the concept head A (v8 wall, +1 mm)
# ===========================================================================================

def head_a_parts():
    HA.WALL = H["wall"]                                     # 2.0 (concept sketch: 2.2)
    HA.FRONT_GAP = (W - BZ["w"]) / 2 - HA.WALL              # 0.5 -> white rim 2.5 like head A
    h01, h02 = HA.shells()
    ear_l, ring_l = HA.ear_left()
    up = Pos(0, 0, DZ)
    h01, h02, ear_l, ring_l = (up * s for s in (h01, h02, ear_l, ring_l))
    ear_r, ring_r = mirror(ear_l, Plane.YZ), mirror(ring_l, Plane.YZ)
    return h01, h02, ear_r, ear_l, ring_r, ring_l


# ===========================================================================================
# HP03 curved bezel, HP04 cover, HP04E eyes, HP04C camera dot, HP04F flat blank
# ===========================================================================================

def bezel():
    bw, bh, br = BZ["w"], BZ["h"], BZ["r"]
    raw = rr_prism_y(bw, bh, br, Y_FACE_APEX - 2.0, SKIRT_END)
    b = check("HP03 raw", raw & cyl_z(R_FACE))                     # cylindrical face R180.5
    loop = edges_where(b, lambda p: abs(r_axis(p) - R_FACE) < 0.02)
    b = try_fillet(b, loop, BZ_FRONT_FILLET, "HP03 front edge")
    # radial seat for the cover (+ tape), curved ledge, opening, skirt cavity behind the ledge
    seat = radial_patch(R_IN - ADH, R_FACE + 2.0, BLANK_W + 2 * CLR, BLANK_H + 2 * CLR, BLANK_R + CLR)
    opening = radial_patch(R_LEDGE_BACK - 2.0, R_FACE + 2.0, BLANK_W - 2 * LEDGE_W, BLANK_H - 2 * LEDGE_W,
                           BLANK_R - LEDGE_W)
    cavity = rr_prism_y(bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL, Y_FACE_APEX - 2.0,
                        SKIRT_END + 1.0) & cyl_z(R_LEDGE_BACK)
    b = retry(lambda: b - seat, "HP03 seat")
    b = retry(lambda: b - opening, "HP03 opening")
    b = retry(lambda: b - cavity, "HP03 cavity")
    b = retry(lambda: b - display_dummy(grow=DISP_RELIEF), "HP03 display relief")
    sols = b.solids()
    if len(sols) != 1:
        raise RuntimeError(f"HP03: {len(sols)} solids")
    b = sols[0]
    e_seat = edges_where(b, lambda p: abs(r_axis(p) - R_FACE) < 0.02)
    b = try_fillet(b, e_seat, SEAT_EDGE, "HP03 seat edge")
    return check("HP03", b, vmin=3000)


def cover():
    return check("HP04", radial_patch(R_IN, R_OUT, BLANK_W, BLANK_H, BLANK_R), vmin=5000)


def eyes():
    """Render-only warm pills 10.5 x 17.5, 0.02..0.08 mm in front of the curved cover (clear of the 0.02 STL chord error)."""
    out = None
    for sx in (-1, 1):
        sc = R_OUT * math.asin(sx * EYE["x"] / R_OUT)               # front-view x -> arc length
        e = radial_patch(R_OUT + 0.02, R_OUT + 0.08, EYE["w"], EYE["h"], EYE["w"] / 2, r_ref=R_OUT,
                         sc=sc, zc=EYE["z"])
        out = e if out is None else out + e
    return check("HP04E", out)


def camera_dot():
    """Render-only lens: very low spherical cap sitting on the cover (x 0 = apex)."""
    r, sag = CAM["d"] / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_OUT_APEX - sag + rs, CAM["z"]) * Sphere(rs)
    lens = sph & cyl_y(r, Y_OUT_APEX - 1.0, Y_OUT_APEX, 0.0, CAM["z"])     # cover sags only 0.005 at x 1.4
    return check("HP04C", lens)


def flat_blank():
    """Developed (unbent) cover outline, 0.1 mm plate tangent in front of the cover apex - laser file."""
    y = Y_OUT_APEX - BLANK_GAP
    return check("HP04F", rr_prism_y(BLANK_W, BLANK_H, BLANK_R, y - 0.1, y))


# ===========================================================================================
# manufacturing numbers + 1:1 drawing of the blank, the vinyl mask and the mould rib
# ===========================================================================================

def mask_numbers():
    """Mask window / camera hole, developed on the INNER face (where the vinyl / paint goes)."""
    xw = ACT_W / 2 + MASK_MARGIN                                    # front-view half width 37.32
    z_top = ZC + BLANK_H / 2 - PRINT_TOP                            # 177.0 (7 mm print band above)
    z_bot = DISP_ZC - ACT_H / 2 - MASK_MARGIN                       # 128.9
    s_w = R_IN * math.asin(xw / R_IN)                               # developed half width on R178
    return dict(win_w=2 * s_w, win_h=z_top - z_bot, win_r=2.0, win_zc=(z_top + z_bot) / 2,
                win_top_from_edge=ZC + BLANK_H / 2 - z_top, win_bot_from_edge=z_bot - (ZC - BLANK_H / 2),
                cam_from_top=ZC + BLANK_H / 2 - CAM["z"], mask_w=BLANK_W * R_IN / R_MID - 0.6,
                mask_h=BLANK_H - 0.6)


def glass_numbers():
    sag_out = R_OUT - math.sqrt(R_OUT ** 2 - (R_OUT * math.sin(BLANK_W / 2 / R_MID)) ** 2)
    x_act = ACT_W / 2
    gap_c = Y_DISP_FRONT - Y_IN_APEX
    gap_act = Y_DISP_FRONT - y_on_cyl(R_IN, x_act)
    gap_edge = Y_DISP_FRONT - y_on_cyl(R_IN, DISP_W / 2)
    proj_w = 2 * R_OUT * math.sin(BLANK_W / 2 / R_MID)
    return dict(R_out=R_OUT, R_in=R_IN, t=T_COVER, blank=(BLANK_W, BLANK_H, BLANK_R), proj_w=proj_w,
                sag=sag_out, gap_center=gap_c, gap_active_edge=gap_act, gap_board_edge=gap_edge,
                bezel_proud_center=Y0 - Y_FACE_APEX, bezel_proud_side=Y0 - y_on_cyl(R_FACE, BZ["w"] / 2),
                strain_pct=100 * (T_COVER / 2) / R_MID, y_out_apex=Y_OUT_APEX, y_axis=Y_AX)


def write_blank_files(out_dir):
    d = os.path.join(out_dir, "blank")
    os.makedirs(d, exist_ok=True)
    g, m = glass_numbers(), mask_numbers()
    mould_w, mould_side = 150.0, 25.0
    mould_sag = R_IN - math.sqrt(R_IN ** 2 - (mould_w / 2) ** 2)
    L = []
    a = L.append
    a('<?xml version="1.0" encoding="UTF-8"?>')
    a('<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">')
    a('<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#222}.cut{fill:none;stroke:#e00000;stroke-width:0.15}'
      '.ax{stroke:#0060c0;stroke-width:0.2;stroke-dasharray:4 1 1 1;fill:none}.dim{stroke:#555;stroke-width:0.15;fill:none}'
      '</style>')
    a('<rect x="0" y="0" width="297" height="210" fill="#ffffff"/>')
    a('<text x="12" y="12" font-size="5.2" font-weight="bold">NOVA mini v8 – hlava A+ – krycie sklo HP04: prírez, maska, forma (mierka 1:1)</text>')
    a(f'<text x="12" y="18.5" font-size="3.2">Liate PMMA dymové {T_COVER:.1f} mm · valcový ohyb, zvislá os · R vonk. {R_OUT:.0f} / '
      f'R vnút. = R formy {R_IN:.0f} · rozvinuté na neutrálnej vrstve R {R_MID:.0f} · tlač bez zmeny mierky (100 %)</text>')
    # --- blank ---
    bx, by = 14.0, 32.0
    a(f'<text x="{bx}" y="{by - 4}" font-size="3.4" font-weight="bold">1  Prírez (laser, červená = rez)</text>')
    a(f'<rect class="cut" x="{bx}" y="{by}" width="{BLANK_W}" height="{BLANK_H}" rx="{BLANK_R}" ry="{BLANK_R}"/>')
    cx = bx + BLANK_W / 2
    a(f'<line class="ax" x1="{cx}" y1="{by - 2}" x2="{cx}" y2="{by + BLANK_H + 2}"/>')
    a(f'<text x="{cx + 1}" y="{by + BLANK_H + 5}" font-size="2.6" fill="#0060c0">os ohybu ∥ (vrchol oblúka)</text>')
    a(f'<text x="{bx + 2}" y="{by + 6}" font-size="2.6">HORE ↑</text>')
    a(f'<line class="dim" x1="{bx}" y1="{by + BLANK_H + 9}" x2="{bx + BLANK_W}" y2="{by + BLANK_H + 9}"/>')
    a(f'<text x="{cx - 8}" y="{by + BLANK_H + 13}" font-size="3">{BLANK_W:.1f} mm</text>')
    a(f'<text x="{bx + BLANK_W + 2}" y="{by + BLANK_H / 2}" font-size="3">{BLANK_H:.0f}</text>')
    a(f'<text x="{bx + 2}" y="{by + BLANK_H - 3}" font-size="2.4">rohy R{BLANK_R:.0f}</text>')
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
             f'v-{m["win_h"] - 2 * wr} a{wr},{wr} 0 0 1 {wr},-{wr} Z ')
    rh = CAM_HOLE_D / 2
    path += f'M{ccx - rh},{ccy} a{rh},{rh} 0 1 0 {CAM_HOLE_D},0 a{rh},{rh} 0 1 0 -{CAM_HOLE_D},0 Z'
    a(f'<path d="{path}" fill="#111" fill-rule="evenodd" stroke="#e00000" stroke-width="0.12"/>')
    a(f'<text x="{wx + 3}" y="{wy + 8}" font-size="2.8" fill="#444">okno displeja {m["win_w"]:.1f} × {m["win_h"]:.1f} R{wr:.0f}</text>')
    a(f'<text x="{wx + 3}" y="{wy + 12}" font-size="2.4" fill="#444">aktívna plocha 3.5" + 0.6 mm</text>')
    a(f'<text x="{wx + 3}" y="{wy + 15.5}" font-size="2.4" fill="#444">horný pás {PRINT_TOP:.0f} mm (kamera), dolný {m["win_bot_from_edge"]:.1f} mm</text>')
    a(f'<polyline points="{ccx + rh},{ccy} {mx + mw - 6},{my - 1.5} {mx + mw + 1},{my - 1.5}" fill="none" stroke="#e00000" stroke-width="0.15"/>')
    a(f'<text x="{mx + mw + 2}" y="{my - 0.6}" font-size="2.4">otvor kamery Ø{CAM_HOLE_D}, stred {m["cam_from_top"]:.1f} od hornej hrany</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 8}" font-size="2.4">symetrická – zvnútra</text>')
    a(f'<text x="{mx + mw + 2}" y="{my + 11.5}" font-size="2.4">sa nezrkadlí</text>')
    a(f'<text x="{mx}" y="{my + mh + 5}" font-size="2.5">rozvinuté na vnútornom povrchu R{R_IN:.0f}: {mw:.1f} × {mh:.1f} '
      f'(o 0.3 menšie po obvode) – nalepiť až PO ohnutí</text>')
    # --- mould rib template ---
    fx, fy = 14.0, 118.0
    base = fy + mould_side + mould_sag + 6
    a(f'<text x="{fx}" y="{fy - 4}" font-size="3.4" font-weight="bold">3  Šablóna rebra formy 1:1 – MDF 18 mm, 6 ks zlepiť (blok 108 mm)</text>')
    p0 = (fx, base - mould_side)
    p1 = (fx + mould_w, base - mould_side)
    a(f'<path d="M{fx},{base} L{p0[0]},{p0[1]} A{R_IN},{R_IN} 0 0 1 {p1[0]},{p1[1]} L{p1[0]},{base} Z" '
      f'fill="#f3e6cf" stroke="#000" stroke-width="0.25"/>')
    a(f'<line class="ax" x1="{fx + mould_w / 2}" y1="{base - mould_side - mould_sag - 3}" x2="{fx + mould_w / 2}" y2="{base + 2}"/>')
    a(f'<text x="{fx + 4}" y="{base - 6}" font-size="3">R {R_IN:.0f} (konvexná, hladká)</text>')
    a(f'<text x="{fx + 4}" y="{base - 2}" font-size="2.5">šírka {mould_w:.0f} · výška v strede {mould_side + mould_sag:.1f} · na krajoch {mould_side:.0f}</text>')
    # --- scale bar ---
    sy = 196.0
    a(f'<line x1="{fx}" y1="{sy}" x2="{fx + 100}" y2="{sy}" stroke="#000" stroke-width="0.4"/>')
    for i in range(11):
        hh = 3 if i % 5 == 0 else 1.6
        a(f'<line x1="{fx + 10 * i}" y1="{sy}" x2="{fx + 10 * i}" y2="{sy - hh}" stroke="#000" stroke-width="0.25"/>')
    a(f'<text x="{fx}" y="{sy + 5}" font-size="3">kontrola mierky tlače: 100 mm</text>')
    # --- notes ---
    nx, ny = 176.0, 120.0
    notes = [
        "Postup (domáca dielňa):",
        "1. Objednať laserom rezaný prírez z LIATEHO dymového PMMA",
        f"    {T_COVER:.1f} mm (priepustnosť ~30–40 %). Extrudované PMMA sa pri",
        "    ohreve zmršťuje – najprv skúšobný kus, prípadne korekcia.",
        "2. Sušiť 1–2 h pri 80 °C (inak bubliny), fólie odstrániť.",
        "3. Rúra 150–160 °C, 4–8 min na papieri na pečenie,",
        "    kým nie je mäkký ako koža.",
        "4. Položiť stredom (modrá os) na formu R178, nechať",
        "    dosadnúť vlastnou váhou, len jemne pridržať v rohoch",
        "    (rukavice); chladnúť na forme 10 min.",
        "5. Masku nalepiť/nastriekať zvnútra (okno zakryť fóliou).",
        "6. Vlepiť do rámu HP03 na obojstrannú pásku 0.2 mm.",
        f"Alternatíva: PC 0.75–1.0 mm za studena (R{R_OUT:.0f} > 150×t),",
        "    drží ho zakrivená opierka rámu + páska 1 mm.",
        f"Medzera k displeju: stred {g['gap_center']:.1f} mm, okraj DPS {g['gap_board_edge']:.1f} mm.",
    ]
    for i, t in enumerate(notes):
        a(f'<text x="{nx}" y="{ny + 4.6 * i}" font-size="2.7"{" font-weight=\"bold\"" if i == 0 else ""}>{t}</text>')
    a('</svg>')
    svg = os.path.join(d, "HP04F_prirez.svg")
    with open(svg, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    dxf = os.path.join(d, "HP04F_prirez.dxf")
    try:
        from build123d import ExportDXF, Unit
        with BuildSketch() as sk:
            RectangleRounded(BLANK_W, BLANK_H, BLANK_R)
        exp = ExportDXF(unit=Unit.MM)
        exp.add_layer("REZ")
        exp.add_shape(sk.sketch.faces()[0].outer_wire(), layer="REZ")
        exp.write(dxf)
    except Exception as ex:  # pragma: no cover
        print("  (DXF export skipped:", ex, ")")
        dxf = None
    return svg, dxf


# ===========================================================================================

def build():
    h01, h02, ear_r, ear_l, ring_r, ring_l = head_a_parts()
    up, fy, ex = 90.0, 35.0, 28.0
    g = glass_numbers()
    return [
        PartRec("HP01", "Hlavný obal hlavy", h01, "white", SUB, J, (0, 0, up),
                note="biely obal 106×66×74 ako hlava A, rohy spredu R26, zadná hrana R20, stena 2.0, "
                     "kapsa 36×40 pre valec náklonu Ø30"),
        PartRec("HP02", "Zadný kryt hlavy", h02, "white", SUB, J, (0, fy, up),
                note="servisný kryt 88×50 R15 premietnutý na zadnú plochu, škára 0.6"),
        PartRec("HP03", "Predný rám (zakrivený)", bezel(), "black", SUB, J, (0, -fy, up),
                note=f"čierny rám 101×69 R23.5, čelo valec R{R_FACE:.1f} (zvislá os), vystupuje "
                     f"{g['bezel_proud_center']:.1f} mm v strede / {g['bezel_proud_side']:.1f} mm na bokoch, "
                     f"radiálne lôžko skla + zakrivená opierka {LEDGE_T} mm"),
        PartRec("HP04", "Krycie sklo (zakrivené)", cover(), "glass", SUB, J, (0, -fy - 10, up),
                note=f"dymové liate PMMA {T_COVER:.1f} mm ohnuté za tepla, valec R{R_OUT:.0f}/R{R_IN:.0f}, "
                     f"rozvinutý prírez {BLANK_W}×{BLANK_H:.0f} R{BLANK_R:.0f}, čierna maska zvnútra (mŕtvy predok)"),
        PartRec("HP04E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -fy - 10, up),
                note="len objekt pre render: dve teplé pilulky 10.5×17.5 na zakrivení skla"),
        PartRec("HP04C", "Okienko kamery", camera_dot(), "black_gloss", SUB, J, (0, -fy - 10, up),
                note="len objekt pre render: kamera za sklom v hornom páse masky (otvor v maske Ø3.6)"),
        PartRec("HP04F", "Rozvinutý prírez skla", flat_blank(), "glass", SUB, J, (0, -fy - 40, up), internal=True,
                note=f"rovinný prírez na laser {BLANK_W}×{BLANK_H:.0f} R{BLANK_R:.0f}, hr. 0.1 (len obrys); "
                     f"forma MDF konvexná R{R_IN:.0f}"),
        PartRec("HP05-R", "Ucho pravé", ear_r, "black", SUB, J, (-ex, 0, up),
                note="čierny disk Ø28, vystupuje 4 mm, dotyk + mikrofón"),
        PartRec("HP05-L", "Ucho ľavé", ear_l, "black", SUB, J, (ex, 0, up),
                note="čierny disk Ø28, vystupuje 4 mm, dotyk + mikrofón"),
        PartRec("HP06-R", "LED krúžok ucha pravý", ring_r, "cyan_led", SUB, J, (-ex, 0, up),
                note="svetlovod Ø23/Ø17, tyrkysová LED"),
        PartRec("HP06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (ex, 0, up),
                note="svetlovod Ø23/Ø17, tyrkysová LED"),
        PartRec("HP07", "Displej 3.5\" (maketa)", display_dummy(), "display", SUB, J, (0, -fy + 5, up), internal=True,
                note=f"maketa dosky ESP32-S3 + 3.5\" IPS 86×56×6 (rovná), čelo y {Y_DISP_FRONT}; medzera ku sklu "
                     f"{g['gap_center']:.1f} mm v strede / {g['gap_board_edge']:.1f} mm na okraji DPS"),
    ]


def export_all(parts):
    """export_parts(step=True), then rewrite every STEP from an untessellated copy: the STL mesh that
    export_parts() puts on a shape before its STEP export can corrupt fillet-heavy solids (HP02 came back
    invalid with a wrong volume) - each rewritten STEP is re-imported and checked."""
    pristine = {p.id: copy.deepcopy(p.shape) for p in parts}
    recs = export_parts(parts, MANIFEST, step=True, out_dir=OUT_DIR)
    for pid, shp in pristine.items():
        path = os.path.join(OUT_DIR, "step", f"{pid}.step")
        export_step(copy.deepcopy(shp), path)
        back = import_step(path)
        if not back.is_valid or abs(back.volume - shp.volume) > 1e-3 * max(1.0, shp.volume):
            raise RuntimeError(f"{pid}: STEP round trip failed")
    return recs, pristine


if __name__ == "__main__":
    t = time.time()
    parts = build()
    recs, by = export_all(parts)
    for r in recs:
        print(f"  {r['id']:8s} {r['mat']:11s} valid={by[r['id']].is_valid} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    clean = [PartRec(p.id, p.name, by[p.id], p.mat, p.sub, p.joint) for p in parts]
    print("  overlaps:", HA.overlaps(clean) or "none")
    disp = by["HP07"]
    for pid in ("HP01", "HP03", "HP04"):
        print(f"  display clearance to {pid}: {disp.distance_to(by[pid]):.2f} mm")
    print(f"  cover clearance to HP03: {by['HP04'].distance_to(by['HP03']):.2f} mm")
    g = glass_numbers()
    print("  glass:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()})
    print("  mask:", {k: round(v, 2) for k, v in mask_numbers().items()})
    svg, dxf = write_blank_files(OUT_DIR)
    print("  blank files:", svg, dxf)
    print(f"[{MANIFEST}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT_DIR}")
