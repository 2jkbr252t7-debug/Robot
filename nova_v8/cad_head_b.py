"""
NOVA mini v8.0 - HEAD variant B "kapsula s vizorom" (frameless), MANUFACTURABLE curved visor.
Run from the repo root:  /opt/venv/cad/bin/python -m nova_v8.cad_head_b
Exports STL + STEP + manifest "head_b" into build_v8_var_b/ (never into build/ or build_v8/), plus the
laser-cut data of the visor (HB03F_blank.dxf/.svg, HB03_mould_rib.dxf, HB03_visor.json).

Upgrade of the concept nova_v8/head_b.py to the v8.0 numbers (nova_v8/spec.py: head z 117..191, tilt axis
y 0 / z 127, barrel pocket 36 x 40 R12 with the ceiling at z 144.5, 3.5" board 86 x 56 x 6, tilt micro servo
in the head beside the pocket) and to the cheap-to-make visor rule:

  * The visor is ONE SINGLE-CURVATURE piece: a vertical cylinder (outer R102 / inner R100) across the front.
    It is cut flat from smoked PMMA 2 mm (rounded rectangle 99 x 60, R25 top / R12 bottom corners) and
    heat-bent over a R100 former (a Ø200 PVC "KG DN200" pipe offcut or MDF ribs), or made of 0.75-1 mm PC
    cold-bent into the shell rebate.  Its edges are radial (as a bent, laser-cut sheet really is) and it
    ends at x = ±48, i.e. 3 mm BEFORE the plan corners start (R102 -> R18 at x = ±51): no tight wrap,
    no double curvature anywhere on the part.
  * Dead front: black mask on the inner face outside the display window (77 x 50 R6 developed) and a
    clear dot for the optional camera -> glossy black when off, eyes shine through.
  * The visor sits flush in the white shell with a 0.6 mm shadow gap on a 2.4 mm rebate (VHB tape 0.25).

Body: front-view silhouette 110 x 74 (top corners R32, bottom corners R19 - the micro servo beside the
pocket reaches x 42.7 at z 121, a R32 bottom corner would cut it) extruded along Y with a variable back loop R26 (top) -> R16 (bottom),
INTERSECT plan prism (front arc R102 + R18 plan corners), whole front loop rounded R6.  y -40.5 .. +31:
the flat display has to stay behind the R100 inner surface at its side edges (x ±43 -> sag 9.7 mm),
which sets the visor apex 10.3 mm in front of the display.

Parts (sub "head_b", joint "J3")
  HB01     Predny obal hlavy       white        wall 2.0, flush visor opening + rebate, barrel pocket 36x40 R12
                                                (walls 1.5, ceiling z 144.5, servo/pivot holes), display ribs,
                                                flush ear grooves + Ø1 mic ports, lip under the seam
  HB02     Zadny kryt hlavy        white        rear cap behind the vertical parting seam 0.6 at y +23
  HB03     Vizor                   glass        smoked PMMA 2.0, R102/R100 cylinder, 96 x 60 in the front view
  HB03E    Obsah displeja - oci    eye          RENDER-ONLY pills 10.5 x 17.5 (spec eyes) on the visor
  HB03C    Okienko kamery          black_gloss  RENDER-ONLY camera dot x 0 / z 180.5 (spec camera)
  HB05-R/L LED kruzok ucha         cyan_led     flush light-guide rings Ø23/Ø17, 0.25 below the skin
  HB03F    Rozvinuty prirez vizora glass        INTERNAL: flat blank 99 x 60 x 0.1 (developed at R101)
                                                0.6 mm in front of the visor apex - for laser cutting

Deviations from nova_v8/spec.py HEAD (variant A numbers, B is its own shape): w 110 (A 106), front-view
corners R32 / R19 (A R26), depth y -40.5 .. +31 (A -33 .. +33 + 5 mm bezel), ear rings flush Ø23/Ø17 at
y -3 / z 154 (A discs proud 4 mm).  Head bottom z 117, top z 191, tilt axis and pocket exactly per spec.
"""
from __future__ import annotations

import copy
import json
import math
import os
import sys
import time

from build123d import (Axis, Box, BuildSketch, Circle, Cylinder, Edge, ExportDXF, ExportSVG, GeomType, Locations,
                       Mode, Plane, Pos, Rectangle, RectangleRounded, ShapeList, SlotOverall, Solid, Sphere, Vector,
                       Wire, extrude, fillet)
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
from nova_v8.head_b import (check, cyl_x, edges_where, overlaps, retry, single, slab_y,  # noqa: E402
                            try_fillet)

OUT_DIR = os.path.join(ROOT, "build_v8_var_b")
SUB = "head_b"
MANIFEST = "head_b"

HD, NK, DSP = S8.HEAD, S8.NECK, S8.DISPLAY
Z0, Z1, ZC = HD["z0"], HD["z1"], HD["zc"]                 # 117 .. 191, centre 154
HH = Z1 - Z0                                              # 74
TILT_Y, TILT_Z = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]  # 0, 127
PK = HD["barrel_pocket"]                                  # 36 x 40 R12, ceiling z 144.5
EAR, EYE, CAM = HD["ear"], HD["eyes"], HD["camera"]
DISP_W, DISP_H, DISP_T = DSP["outline"]                   # 86 x 56 x 6
ACT_W, ACT_H = DSP["active"]                              # 73.44 x 48.96
SERVO = HD["tilt_servo"]["envelope"]                      # (25.5 along Z, 12.2 along Y, 23.2 along X)

# ---- local construction constants (variant B only; not shared dimensions) ------------------
W = 110.0                  # head width
R_TOP, R_BOT = 32.0, 19.0  # front-view corners (bottom limited by the tilt servo beside the pocket)
R_BACK_TOP, R_BACK_BOT = 26.0, 16.0   # variable back loop: soft capsule top, R16 at the bottom (< R_BOT)
R_FRONT = 6.0              # 3D round of the whole front loop (visor stays 1 mm inside its tangent line)
R_PF = 18.0                # plan corner: front arc -> side
X_PS = W / 2 + 5.0         # plan-prism side lines outside the head (no coincident faces)
WALL = 2.0

VIS_T = 2.0                            # smoked PMMA 2 mm (alt. PC 1.0 + 1.1 mm black VHB on the same rebate)
R_OUT = 102.0                          # outer radius of the visor = front surface of the head
R_IN = R_OUT - VIS_T                   # 100 = mould radius (Ø200 PVC KG pipe)
R_MID = R_OUT - VIS_T / 2              # 101 neutral radius -> development of the flat blank
VIS = dict(w=99.0, h=60.0, r_top=25.0, r_bot=12.0, zc=ZC)   # developed outline (u along R_MID, z)
GAP = 0.6                              # shadow gap visor <-> shell, parting seam width
TAPE = 0.25                            # VHB / double-sided tape on the rebate
LEDGE_W, LEDGE_OUT = 2.4, 1.4          # rebate: 2.4 under the visor edge, 1.4 beyond the opening
D_LEDGE0, D_LEDGE1 = 1.5, 3.9          # rebate band depth below the skin (merges into the 2.0 wall)

DISP_Y0 = -28.2                        # display glass front face (board back -22.2, pocket wall -21.5)
DISP_CR = 3.0                          # assumed corner radius of the board outline
DISP_SIDE_CLR = 0.5                    # board side edge (x ±43) -> R100 inner surface
DISP_RELIEF = 0.4                      # local relief pocket in HB01 around the board (front + sides)
YC = DISP_Y0 - DISP_SIDE_CLR + math.sqrt(R_IN ** 2 - (DISP_W / 2) ** 2)   # 61.58 plan centre of the cylinder
Y_FRONT = round(YC - R_OUT - 0.04, 1)  # -40.5 visor apex (x = 0)
YC = Y_FRONT + R_OUT                   # 61.5
Y_BACK = 31.0
Y_SEAM = 23.0                          # vertical parting plane (behind the 36x40 pocket, walls to y 21.5)
LIP_D0, LIP_D1, LIP_OUT = WALL + 0.05, D_LEDGE1, 3.0

RING_OD, RING_ID = EAR["ring_od"], EAR["ring_id"]          # 23 / 17
EAR_Y, EAR_Z = EAR["y"], EAR["z"]                          # -3, 154
RING_DEPTH, RING_GAP, RING_RECESS = 1.4, 0.15, 0.25
MIC_D = 1.0

PK_W, PK_D, PK_R, PK_CEIL = PK["w"], PK["d"], PK["r"], PK["ceiling_z"]
PK_WALL = 1.5
SERVO_SIDE = +1                        # tilt servo on the robot-LEFT side (+X) of the pocket
SPLINE_HOLE_D, PIVOT_HOLE_D = 7.5, 3.4
SERVO_X0 = PK_W / 2 + PK_WALL + 0.5   # 20.0 servo top face (shaft side)
SERVO_BOX = (SERVO_X0, SERVO_X0 + SERVO[2], -SERVO[1] / 2, SERVO[1] / 2, TILT_Z - 6.1, TILT_Z - 6.1 + SERVO[0])

RIB_T, RIB_D = 2.0, 4.0                # display ribs behind the board (top z 179..181, bottom z 127..129)
CAM_Z, CAM_D = CAM["z"], CAM["d"]      # 180.5, 2.8

WINDOW_MARGIN, WINDOW_R = 0.5, 6.0     # mask window = active area + 0.5, corners R6


# ===========================================================================================
# developed outline on the visor cylinder (u = arc length at R_MID, z)
# ===========================================================================================

def dev_dims(g=0.0):
    return VIS["w"] + 2 * g, VIS["h"] + 2 * g, VIS["r_top"] + g, VIS["r_bot"] + g


def cyl_pt(u, z, r):
    th = u / R_MID
    return Vector(r * math.sin(th), YC - r * math.cos(th), z)


def uz_of(p):
    """(u, z, radius) of a 3D point in the visor cylinder coordinates."""
    th = math.atan2(p.X, YC - p.Y)
    return th * R_MID, p.Z, math.hypot(p.X, YC - p.Y)


def dev_sd(u, z, g=0.0):
    """Signed distance (developed plane) to the visor outline grown by g (negative inside)."""
    w, h, rt, rb = dev_dims(g)
    zc = VIS["zc"]
    r = rt if z >= zc else rb
    qx = abs(u) - (w / 2 - r)
    qz = abs(z - zc) - (h / 2 - r)
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r


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


# ===========================================================================================
# parts
# ===========================================================================================

def ear_annulus(ro, ri, side=0):
    """Annulus along X through the ear centre; side -1 / +1 keeps only that half (x < 0 / x > 0)."""
    x0, x1 = {0: (-70, 70), -1: (-70, -1), 1: (1, 70)}[side]
    return cyl_x(ro, x0, x1, EAR_Y, EAR_Z) - cyl_x(ri, x0 - 1, x1 + 1, EAR_Y, EAR_Z)


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    with BuildSketch(Plane.XY.offset(z0)) as s:
        with Locations((cx, cy)):
            RectangleRounded(w, d, r)
    return extrude(s.sketch, z1 - z0)


def build_visor():
    v = retry(lambda: ring(R_OUT, R_IN) & dev_cutter(0.0), "visor")
    return check("HB03", single(v, "HB03"), 8000)   # sharp laser-cut edges, deburred by hand


def build_shells(sk: Skin):
    body = sk.body
    shell = sk.band(0, WALL)
    shell = retry(lambda: shell - dev_cutter(GAP), "visor opening")

    # ---- rebate (ledge) behind the shadow gap: 1.65 thick under the visor, merges into the wall outside
    ledge = retry(lambda: (sk.band(D_LEDGE0, D_LEDGE1) & dev_cutter(GAP + LEDGE_OUT)) - dev_cutter(-LEDGE_W),
                  "ledge band")
    ledge = retry(lambda: ledge - (ring(R_OUT + 1, R_OUT - (VIS_T + TAPE)) & dev_cutter(GAP)), "ledge seat")
    notch = Pos(0, Y_FRONT + 4, (CAM_Z - 2.2 + 195) / 2) * Box(12, 14, 195 - (CAM_Z - 2.2))
    ledge = retry(lambda: ledge - (notch & dev_cutter(GAP)), "camera notch")

    # ---- vertical parting seam behind the pocket ----
    h02 = retry(lambda: shell & slab_y(Y_SEAM + GAP / 2, Y_BACK + 5), "HB02")
    h01 = retry(lambda: shell & slab_y(Y_FRONT - 5, Y_SEAM - GAP / 2), "HB01 split")
    lip = retry(lambda: (sk.band(D_LEDGE0, LIP_D1) & slab_y(Y_SEAM - 3, Y_SEAM - GAP / 2))
                + (sk.band(LIP_D0, LIP_D1) & slab_y(Y_SEAM - 1.5, Y_SEAM + LIP_OUT)), "seam lip")
    h01 = retry(lambda: h01 + ledge, "add ledge")
    h01 = retry(lambda: h01 + lip, "add lip")

    # ---- display ribs (board back face rests on them; 4x M2 to the board holes at assembly) ----
    yb = DISP_Y0 + DISP_T
    ribs = (Pos(0, yb + RIB_D / 2, 180.0) * Box(2 * W, RIB_D, RIB_T)
            + Pos(0, yb + RIB_D / 2, 128.0) * Box(2 * W, RIB_D, RIB_T))
    ribs = retry(lambda: ribs & sk.inner(D_LEDGE0), "ribs")
    h01 = retry(lambda: h01 + ribs, "add ribs")

    # ---- barrel pocket 36 x 40 R12 open downwards, ceiling z 144.5, walls 1.5 ----
    p_in = rr_prism_z(PK_W, PK_D, PK_R, Z0 - 6, PK_CEIL, cy=TILT_Y)
    p_out = rr_prism_z(PK_W + 2 * PK_WALL, PK_D + 2 * PK_WALL, PK_R + PK_WALL, Z0 - 6, PK_CEIL + PK_WALL, cy=TILT_Y)
    h01 = retry(lambda: h01 + (p_out & body), "pocket walls")
    h01 = retry(lambda: h01 - p_in, "pocket")
    xs = SERVO_SIDE * (PK_W / 2 + PK_WALL / 2)
    h01 = retry(lambda: h01 - cyl_x(SPLINE_HOLE_D / 2, xs - 3, xs + 3, TILT_Y, TILT_Z), "servo spline hole")
    h01 = retry(lambda: h01 - cyl_x(PIVOT_HOLE_D / 2, -xs - 3, -xs + 3, TILT_Y, TILT_Z), "pivot hole")
    e_pk = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and abs(p.X) < PK_W / 2 + 0.05
                       and abs(p.Y - TILT_Y) < PK_D / 2 + 0.05)
    h01 = try_fillet(h01, e_pk, 0.8, "pocket rim")

    # ---- flush ear rings: groove 1.5 deep, ring 1.4 deep sitting 0.25 below the skin ----
    groove = retry(lambda: sk.band(0, RING_DEPTH + 0.1) & ear_annulus(RING_OD / 2 + RING_GAP, RING_ID / 2 - RING_GAP),
                   "ear groove")
    h01 = retry(lambda: h01 - groove, "ear grooves")
    h01 = retry(lambda: h01 - cyl_x(MIC_D / 2, -70, 70, EAR_Y, EAR_Z), "mic ports")
    rband = sk.band(RING_RECESS, RING_DEPTH)
    ring_l = single(retry(lambda: rband & ear_annulus(RING_OD / 2, RING_ID / 2, +1), "HB05-L"), "HB05-L")
    ring_r = single(retry(lambda: rband & ear_annulus(RING_OD / 2, RING_ID / 2, -1), "HB05-R"), "HB05-R")

    # ---- display relief: board outline +0.4 at the front and the sides (back face stays on the ribs);
    #      trims the rebate at the visor corners and <= 0.4 of the wall at the top corners
    g = DISP_RELIEF
    relief = HBC.rr_prism_y(DISP_W + 2 * g, DISP_H + 2 * g, DISP_CR + g, DISP_Y0 - g, DISP_Y0 + DISP_T, cz=ZC)
    h01 = retry(lambda: h01 - relief, "display relief")
    h01 = single(h01, "HB01")
    h02 = single(h02, "HB02")
    return (check("HB01", h01, 20000), check("HB02", h02, 2000),
            check("HB05-R", ring_r, 50), check("HB05-L", ring_l, 50))


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


def display_dummy(grow=0.0):
    g = grow
    return HBC.rr_prism_y(DISP_W + 2 * g, DISP_H + 2 * g, DISP_CR + g, DISP_Y0 - g, DISP_Y0 + DISP_T + g, cz=ZC)


def servo_dummy():
    x0, x1, y0, y1, z0, z1 = SERVO_BOX
    if SERVO_SIDE < 0:
        x0, x1 = -x1, -x0
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


# ===========================================================================================

def build():
    sk = Skin()
    h01, h02, ring_r, ring_l = build_shells(sk)
    h03 = build_visor()
    # independent copies: HB01/HB02 come from one split shell and the STEP writer edits shared edges
    h01, h02, ring_r, ring_l, h03 = (copy.deepcopy(x) for x in (h01, h02, ring_r, ring_l, h03))
    up, fy, ex = 80.0, 35.0, 28.0
    J = "J3"
    wb, hb, rt, rb = dev_dims(0.0)
    return [
        PartRec("HB01", "Predný obal hlavy", h01, "white", SUB, J, (0, 0, up),
                note="biela kapsula 110×74, rohy spredu R32/R19, čelo valec R102, stena 2.0, lícujúci otvor vizora "
                     "s drážkou 2.4 (páska VHB 0.25), kapsa valca 36×40 R12 (strop z 144.5), rebrá pre displej"),
        PartRec("HB02", "Zadný kryt hlavy", h02, "white", SUB, J, (0, fy, up),
                note="zadný kryt za zvislou deliacou škárou 0.6 (rovina y = +23, za kapsou valca), zadné zaoblenie premenlivé R26 hore → R16 dole"),
        PartRec("HB03", "Vizor", h03, "glass", SUB, J, (0, -fy, up),
                note=f"dymové PMMA {VIS_T:.1f} mm ohnuté za tepla na valec R{R_IN:.0f} (vonkajší R{R_OUT:.0f}), "
                     f"jednoduché zakrivenie, čelný pohľad 96×60, vnútri čierna maska mimo okna displeja"),
        PartRec("HB03C", "Okienko kamery", camera_dot(), "black_gloss", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: voliteľná kamera za čírym bodom v maske (x 0, z 180.5)"),
        PartRec("HB03E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: oči 10.5×17.5 z displeja svietia cez tónovaný vizor"),
        PartRec("HB05-R", "LED krúžok ucha pravý", ring_r, "cyan_led", SUB, J, (-ex, 0, up),
                note="lícujúci svetlovod Ø23/Ø17 v boku hlavy, tyrkysová LED, v strede mikrofón Ø1"),
        PartRec("HB05-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (ex, 0, up),
                note="lícujúci svetlovod Ø23/Ø17 v boku hlavy, tyrkysová LED, v strede mikrofón Ø1"),
        PartRec("HB03F", "Rozvinutý prírez vizora", flat_blank(), "glass", SUB, J, (0, -fy - 25, up), internal=True,
                note=f"plochý prírez na laser {wb:.1f}×{hb:.1f} mm, rohy R{rt:.0f} hore / R{rb:.0f} dole, "
                     f"rozvinutý na neutrálnom polomere R{R_MID:.0f}; ohnúť okolo zvislej osi na formu R{R_IN:.0f}"),
    ]


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
        camera_dot=dict(u=0.0, dz_from_centre=round(CAM_Z - VIS["zc"], 2), d_clear=3.5),
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
    rib = Pos(0, hb / 2 + 50) * rib

    dxf = ExportDXF()
    dxf.add_layer("REZ_PRIREZ").add_layer("MASKA_OKNO").add_layer("KAMERA_BOD").add_layer("OS_OHYBU")
    dxf.add_shape(blank.edges(), layer="REZ_PRIREZ")
    dxf.add_shape(win.edges(), layer="MASKA_OKNO")
    dxf.add_shape(cam.edges(), layer="KAMERA_BOD")
    dxf.add_shape(axis, layer="OS_OHYBU")
    dxf.write(os.path.join(out_dir, "HB03F_blank.dxf"))
    rdx = ExportDXF()
    rdx.add_layer("REZ_REBRO_FORMY")
    rdx.add_shape(Pos(0, -(hb / 2 + 50)) * rib, layer="REZ_REBRO_FORMY")
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


if __name__ == "__main__":
    from build123d import import_step
    t = time.time()
    parts = build()
    valid = {p.id: p.shape.is_valid for p in parts}          # before export (the STEP writer touches shared edges)
    recs = export_parts(parts, MANIFEST, step=True, out_dir=OUT_DIR)
    for p, r in zip(parts, recs):
        sv = import_step(os.path.join(OUT_DIR, "step", f"{p.id}.step")).is_valid
        print(f"  {r['id']:8s} {r['mat']:11s} valid={valid[p.id]} step_valid={sv} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    vis = [p for p in parts if not p.internal]
    print("  overlaps:", overlaps(vis) or "none")
    by = {p.id: p.shape for p in parts}
    disp = display_dummy()
    disp_front = HBC.rr_prism_y(DISP_W, DISP_H, DISP_CR, DISP_Y0, DISP_Y0 + DISP_T - 1.0, cz=ZC)
    ov = disp & by["HB01"]
    print(f"  display board: overlap with HB01 {0.0 if ov is None else ov.volume:.3f} mm3 (back face rests on the ribs), "
          f"clearance front/sides to HB01 {disp_front.distance_to(by['HB01']):.2f} mm, "
          f"to HB03 {disp.distance_to(by['HB03']):.2f} mm")
    print(f"  tilt servo envelope clearance to HB01: {servo_dummy().distance_to(by['HB01']):.2f} mm")
    skin = Skin().body
    ol = dev_wire(0.0, R_OUT)
    vmax = max(skin.distance_to(ol.position_at(i / 240)) for i in range(240))
    print(f"  visor outer outline max distance outside the body skin (0 = flush, pure cylinder): {vmax:.3f} mm")
    nums = export_manufacturing(OUT_DIR)
    print("  visor:", json.dumps(nums, ensure_ascii=False))
    print(f"[{MANIFEST}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT_DIR}")
