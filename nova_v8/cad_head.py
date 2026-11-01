"""
NOVA mini v8.0 - HEAD variant A (flat glass), manifest "head".
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.cad_head [--check] [--pose] [--build-others]
Exports STL + STEP + manifest into build_v8/ (never build/, which holds the finished v7.3).

Numbers: nova_v8/spec.py (HEAD, NECK, DISPLAY, MICRO_SERVO).  Upgraded from the approved concept
nova_v8/head_a.py (same outer look, lifted +1 mm to the v8 heights, wall 2.2 -> 2.0) to a buildable FDM design.
Barrel interface = nova_v8/cad_torso.py N06 (D30 x 30 on the tilt axis y 0 z 127, end walls 3.5 with a 1.8 mm
cross-horn recess, D3.2 pivot hole and 2 screw pilots at y +-7.5 on BOTH ends).

Tilt drive (J3) - DEVIATION from spec.HEAD.tilt_servo (coaxial servo is geometrically impossible):
  an MG90S coaxial with the tilt axis (z 127) reaches x 38..43 with its case bottom at z 121.1, but the head's R26
  front-view corners put the inner floor there at z 122..125 (max allowed far end x 35.5 even with the case top
  INSIDE the barrel end).  Therefore:
    * the head pivots on TWO coaxial M3 x 12 socket screws (M31-R/L) threaded into bosses on the pocket walls,
      running in the barrel's D3.2 pivot holes -> the head load never sits on the servo spline,
    * the MG90S (E32) sits in the head on the robot's LEFT (+X), case up, shaft parallel to X at (y 0, z 147)
      = 20 mm above the tilt axis; a 1:1 spur pair m1 20T/20T (H11 on the servo, H09 sector bolted into the N06
      +X horn recess with the 2 existing screw pilots) drives the tilt.  Head CG ahead of the axis keeps the
      flanks loaded (no rattle).  H10 = toothless twin of H09 on the -X end (longer pivot bearing).

Parts (J3 = head tilt about X through y 0 z 127; J2 = pan stage)
  H01      Hlavny obal hlavy        white     106 x 66 x 74 (R26 front view, R20 back loop), wall 2.0, open front
                                              (0.5 gap to H03), barrel pocket 37.2 x 40 R12 (ceiling z 144.5) with
                                              gear slot, 2 pivot bosses (M3 pilots on the tilt axis), 2 tab rails for
                                              the tilt servo (slides in from the front, 1x M2 stop screw), 2 bosses +
                                              1 slot for the front module, ear cups with stop rings, back-cover
                                              ledge + pry notch, neck cable hole in the pocket ceiling
  H02      Zadny kryt hlavy         white     88 x 50 R15 projected on the back, 0.6 seam, 2 top tongues + 1 bottom
                                              snap latch, no screws
  H03      Predny ram               black     101 x 69 R23.5, protrudes 5 mm, glass seat, 1.4 ledge (window 85 x 50),
                                              display pocket, skirt 4 mm into H01, 3 bosses for H07
  H04      Kryci sklo               glass     92 x 60 R16 x 2.0 smoked cast PMMA (laser cut), black mask inside
                                              (top band 7 mm, others 4 mm), bonded on the H03 ledge with 0.1 VHB
  H04C     Okienko kamery           black_gloss  RENDER-ONLY camera dot in the top band (optional camera)
  H04E     Obsah displeja - oci     eye       RENDER-ONLY two pill eyes 10.5 x 17.5
  H05-R/L  Ucho prave / lave        black     Ø28 domed discs, 4 mm proud; rear recess for the Ø23 LED module,
                                              ring groove with 3 bridges; pushed into the H01 ear cup + CA glue
  H06-R/L  LED kruzok ucha          cyan_led  Ø23 / Ø17 light-guide rings (clear PETG / PMMA)
Internal (internal=True)
  H07      Drziak displeja          grey      PETG frame: clamps the 86 x 56 board on the H03 ledge (3x M2x6 into H03),
                                              front module -> H01: 1 bottom tongue + 2x M2x8 (from the back opening)
  H09      Ozubeny segment naklonu  grey      J2: 20T m1 sector (+-63 deg) keyed into the N06 +X horn recess, 2x M2
  H10      Puzdro capu naklonu      grey      J2: same key without teeth on the -X end
  H11      Koliesko serva naklonu   grey      J3: 20T m1 on the MG90S spline (Ø4.4 press-fit + horn screw M2)
  E31      Displej ESP32-S3 3.5"    display   86 x 56 x 6 board (Guition JC3248W535 / Waveshare ESP32-S3-Touch-LCD-3.5)
  E32      Servo naklonu MG90S      servo     22.8 x 12.2 x 22.7, tabs 32.5, shaft (y 0, z 147) parallel to X
  E33-R/L  DPS ucha                 pcb       Ø23 7x WS2812B-5050 round module (AliExpress), in the ear recess
  M31-R/L  Cap naklonu M3x12        metal     DIN 912 M3 x 12 = pivot pins on the tilt axis

FDM (PETG, 0.4 nozzle): H01 front rim on the bed (pocket ceiling, rails, roof block, side walls vertical; supports
only under the back-cover ledge, the pocket front wall (41 mm bridge) and the ear stop rings); H03 face down with
support under the glass ledge; H02 tree supports on the outer face; H05 face up; H07/H09/H10/H11 flat, no supports.
Fasteners: 2x M3x12 DIN 912 (pivots), 3x M2x6 (H07 -> H03), 2x M2x8 (module -> H01), 2x M2x6 (H09/H10 -> N06),
1x M2x6 + washer (servo stop), 1x M2 horn screw (from the MG90S kit).  Mass ~182 g, CG 11.5 ahead / 26 above the
tilt axis -> max 0.36 kg.cm at +20 deg (MG90S 1.8 kg.cm), the load never changes flank (no backlash rattle).

Assembly: (1) H09/H10 bolted onto the barrel ends (neck finished).  (2) MG90S + H11 slid into the H01 rails from
the FRONT opening, 1x M2 stop screw.  (3) H01 lowered vertically over the barrel - H11 meshes radially with H09.
(4) M31 pins from inside (L-key 2.5 through the back opening).  (5) ears + LED modules pushed in from outside.
(6) front module (H04 bonded in H03, foam 0.5, E31, H07 3x M2) -> tongue into the pocket-front slot, 2x M2 from
the back opening.  (7) H02: top tongues in, bottom latch clicks.  Neck bundle 4 wires (5V GND TX RX) through the
barrel slot and the pocket-ceiling hole; the tilt servo is powered from that 5 V and driven by the head ESP32-S3.
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, BuildSketch, Compound, Cylinder, Edge, Face, Locations, Plane, Pos,
                       RectangleRounded, Rot, ShapeList, SlotOverall, Solid, Sphere, Vector, Wire, chamfer, extrude,
                       fillet, mirror, offset)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "head"
SUB = "head"

# ============================================================================================
# shared numbers (spec)
# ============================================================================================
H, NK, DSP, MS = S.HEAD, S.NECK, S.DISPLAY, S.MICRO_SERVO
W, HH = H["w"], H["h"]                               # 106 x 74
Y0, Y1 = H["y0"], H["y1"]                            # -33 (front rim plane) .. +33
Z0, Z1, ZC = H["z0"], H["z1"], H["zc"]               # 117 .. 191, centre 154
R_FV, R_BACK, WALL = H["r_front_view"], H["r_back"], H["wall"]   # 26, 20, 2.0
BZ, GL, CAM, EAR, EYE, BC, BP = H["bezel"], H["glass"], H["camera"], H["ear"], H["eyes"], H["back_cover"], \
    H["barrel_pocket"]
TILT_Y, TILT_Z = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]      # 0, 127
BAR_R, BAR_L = NK["barrel_d"] / 2, NK["barrel_len"]              # 15, 30
BAR_X = BAR_L / 2                                                # barrel end faces at |x| 15
DSP_W, DSP_H, DSP_T = DSP["outline"]                             # 86 x 56 x 6

# ============================================================================================
# local construction constants
# ============================================================================================
FRONT_GAP = (W - BZ["w"]) / 2 - WALL           # 0.5 gap H03 <-> H01 opening (wall 2.0)
R_RIM = 1.6                 # round on the outer edge of the white front rim
SEAM = BC["seam"]           # 0.6
SEAM_BREAK = 0.25           # chamfer on visible seam edges
LEDGE_BACK_T, LEDGE_BACK_IN, LEDGE_BACK_OUT = 1.2, 2.5, 3.0   # H01 ledge under the back-cover seam
LATCH_X = (21.5, 28.5)       # H02 bottom snap latches (|x|), beside the pocket back wall

# --- front stack (along Y) -------------------------------------------------------------------
Y_BZ_FRONT = Y0 - BZ["protrude"]               # -38.0
BZ_FRONT_FILLET = 2.4
GLASS_T, GLASS_RECESS, GLASS_CLR, PSA = 2.0, 0.7, 0.15, 0.1
Y_GL_FRONT = Y_BZ_FRONT + GLASS_RECESS         # -37.3
Y_GL_BACK = Y_GL_FRONT + GLASS_T               # -35.3
Y_LEDGE0 = Y_GL_BACK + PSA                     # -35.2
LEDGE_T = 1.4
Y_LEDGE1 = Y_LEDGE0 + LEDGE_T                  # -33.8
GZ = GL["zc"]                                  # 154
PRINT_TOP, PRINT_SIDE = GL["print_top"], 4.0   # black mask widths on the glass
WIN_W = GL["w"] - 2 * PRINT_SIDE               # 84 visible window
WIN_Z0, WIN_Z1 = GZ - GL["h"] / 2 + PRINT_SIDE, GZ + GL["h"] / 2 - PRINT_TOP   # 128 .. 177
WIN_ZC = (WIN_Z0 + WIN_Z1) / 2                 # 152.5
LEDGE_OPEN = (WIN_W + 1.0, WIN_Z1 - WIN_Z0 + 1.0, 10.0)     # 85 x 50 R10 (hidden behind the mask)
FOAM = 0.5
Y_DSP0 = Y_LEDGE1 + FOAM                       # -33.3 LCD front
Y_DSP1 = Y_DSP0 + DSP_T                        # -27.3 board back (components)
DSP_R = 2.0                                    # board corner radius
DSP_ZC = GZ                                    # board centred on the glass
DSP_CLR = 0.3
SKIRT_END = -29.0
SKIRT_WALL = 1.6
BZ_BOSSES = [(-45.6, 136.0), (45.6, 136.0), (0.0, 184.9)]   # H07 -> H03 screws (x, z)
BOSS_R, PILOT_R = 2.3, 0.8                     # M2 thread-forming into PETG (pilot Ø1.6)
H07_T = 2.0
Y_H07_1 = Y_DSP1 + H07_T                       # -25.3
H01_BOSSES = [(-46.5, 172.0), (46.5, 172.0)]   # front module -> H01 (2x M2x8 from the back opening)
TONGUE = dict(w=11.2, t=1.2, z0=121.8, y1=-22.6)      # H07 bottom tongue
SLOT_BLOCK = dict(w=14.0, y0=-25.0, z1=125.0)

# --- barrel pocket --------------------------------------------------------------------------
PK_W = BP["w"] + 2 * 0.6                       # 37.2 (spec 36: +0.6 per side for the H09/H10 discs)
PK_D, PK_R, PK_TOP = BP["d"], BP["r"], BP["ceiling_z"]       # 40, 12, 144.5
PK_WALL = 2.0
PK_X_IN = PK_W / 2                             # 18.6
PK_X_OUT = PK_X_IN + PK_WALL                   # 20.6
DISC_X0, DISC_X1 = BAR_X, BAR_X + 3.0          # H09/H10 disc on the barrel end face: |x| 15 .. 18
PAD_X = DISC_X1 + 0.3                          # 18.3 pocket thrust pads (axial play +-0.3)
PIVOT_BOSS_R, PIVOT_BOSS_X1 = 4.0, 24.0
RELIEF_D, RELIEF_Y1, RELIEF_PAD = 2.0, -28.6, 1.3   # underside chamfer ahead of the pocket mouth (collar N01)
M3_PILOT_R = 1.25

# --- tilt gear pair (1:1, m1, 20T) ----------------------------------------------------------
G_N, G_M = 20, 1.0
G_CD = G_N * G_M                               # 20 centre distance
SERVO_Z = TILT_Z + G_CD                        # 147 servo shaft
H11_X0, H11_X1 = BAR_X + 0.3, DISC_X1          # 15.3 .. 18.0 (clear of the barrel end face)
H11_HUB_R, H11_HUB_X1 = 4.2, 19.0
SECTOR_HALF = 63.0                             # sector half angle (gap centred) -> tilt +-20 + 2 teeth margin

# --- MG90S (catalogue envelope, same conventions as nova_v8/cad_torso.py) -------------------
MS_L, MS_W, MS_H = 22.8, MS["body"][1], MS["body"][2]      # 22.8 x 12.2 x 22.7
MS_SHAFT_END = 5.9
MS_TABS = MS["tabs_len"]                       # 32.5
MS_TAB_Z = (15.9, 18.4)                        # tab underside / top above the case bottom
MS_TAB_HOLE = 2.45
MS_DOME_R, MS_DOME_H = 5.9, 3.0
MS_SPL_R, MS_SPL_H = 2.4, MS["height_with_spline"] - MS_H - MS_DOME_H   # 2.8
SPL_TIP_X = 16.5                               # spline tip (1.2 web in H11 for the horn screw)
SPL_BASE_X = SPL_TIP_X + MS_SPL_H              # 19.3 = dome top
SV_TOP_X = SPL_BASE_X + MS_DOME_H              # 22.3 case top (output face)
SV_BOT_X = SV_TOP_X + MS_H                     # 45.0 case bottom
SV_Z0 = SERVO_Z - MS_SHAFT_END                 # 141.1 case lower end
SV_Z1 = SV_Z0 + MS_L                           # 163.9 case upper end
TAB_X0, TAB_X1 = SV_BOT_X - MS_TAB_Z[1], SV_BOT_X - MS_TAB_Z[0]   # 26.6 .. 29.1
TAB_ZC = (SV_Z0 + SV_Z1) / 2
TAB_Z0, TAB_Z1 = TAB_ZC - MS_TABS / 2, TAB_ZC + MS_TABS / 2      # 136.25 .. 168.75
RAIL_CLR = 0.15
RAIL_WALL = 1.6
RAIL_Y0, RAIL_Y1, RAIL_STOP = -7.0, 8.0, MS_W / 2 + 0.2           # open front, rear stop at y 6.3

# --- ears ------------------------------------------------------------------------------------
EAR_R = EAR["d"] / 2                           # 14
X_SIDE = W / 2                                 # 53
X_EAR_OUT = X_SIDE + EAR["protrude"]           # 57 dome apex
X_EAR_IN = 48.8                                # ear rear face = stop ring face
EAR_HOLE_R = EAR_R + 0.2
EAR_DOME, EAR_FILLET = 0.6, 1.6
RING_PROUD = 0.15
X_BRIDGE0, X_BRIDGE1 = 52.0, 52.8              # bridge layer under the ring groove (3 windows)
EAR_REC_R = 11.8                               # rear recess for the Ø23 module
MIC_R = 0.5
CUP_RO, CUP_STOP_RI, CUP_STOP_T = 15.5, 12.3, 1.0
EPCB_D, EPCB_T, ELED = 23.0, 1.6, (5.0, 1.5)   # 7-LED WS2812B-5050 module


# ============================================================================================
# helpers
# ============================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    return Plane(origin=(cx, y, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=ZC):
    with BuildSketch(plane_y(y0, cx, cz)) as sk:
        RectangleRounded(w, h, r)
    return extrude(sk.sketch, y1 - y0)


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        with Locations((cx, cy)):
            RectangleRounded(w, d, r)
    return extrude(sk.sketch, z1 - z0)


def bx(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def cyl_x(r, x0, x1, y, z):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos((lo + hi) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo)


def cyl_y(r, y0, y1, x, z):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, (lo + hi) / 2, z) * Rot(90, 0, 0) * Cylinder(r, hi - lo)


def cyl_z(r, z0, z1, x, y):
    lo, hi = min(z0, z1), max(z0, z1)
    return Pos(x, y, lo) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def prism_x(pts_yz, x0, x1):
    """Polygon in the YZ plane (list of (y, z)) extruded from x0 to x1."""
    wire = Wire.make_polygon([Vector(x0, y, z) for y, z in pts_yz], close=True)
    return Solid.extrude(Face(wire), Vector(x1 - x0, 0, 0))


def union(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out + s
    return out


def solid1(s):
    sols = s.solids()
    return sols[0] if len(sols) == 1 else s


def check(name, s, vmin=None):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    if vmin is not None and s.volume < vmin:
        raise RuntimeError(f"{name}: volume {s.volume:.0f} < {vmin}")
    return s


def retry(fn, label, tries=4):
    """OCC booleans run in parallel mode - retry rare non-deterministic failures."""
    err = None
    for _ in range(tries):
        try:
            out = fn()
            if out is not None and out.is_valid and out.volume > 0:
                return out
        except Exception as ex:  # pragma: no cover
            err = ex
    raise RuntimeError(f"{label}: boolean failed {tries}x ({err})")


def rr_dist(x, z, w, h, r, cz=ZC):
    qx = abs(x) - (w / 2 - r)
    qz = abs(z - cz) - (h / 2 - r)
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r


def rr_dist_xy(x, y, w, d, r, cy=0.0):
    qx = abs(x) - (w / 2 - r)
    qy = abs(y - cy) - (d / 2 - r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def edges_where(shape, pred):
    out = []
    for e in shape.edges():
        pts = [e.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if all(pred(p) for p in pts):
            out.append(e)
    return ShapeList(out)


def try_fillet(shape, edges, r, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = fillet(edges, r)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: fillet result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: fillet R{r} skipped: {ex})")
    return shape


def try_chamfer(shape, edges, d, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = chamfer(edges, d)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: chamfer result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: chamfer {d} skipped: {ex})")
    return shape


def step_safe(name, s):
    """Replace OffsetSurface faces (left by offset() on the R20 back-loop blends) with exact B-splines: the STEP
    writer heals such faces IN PLACE, which corrupted v7.3 H01/H02 (lesson from nova/cad/head.py)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_OffsetSurface
    from OCP.ShapeCustom import ShapeCustom
    from OCP.ShapeFix import ShapeFix_Shape
    from build123d import Shape

    def n_offset(sh):
        return sum(1 for f in sh.faces() if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_OffsetSurface)

    if n_offset(s) == 0:
        return s
    conv = ShapeCustom.ConvertToBSpline_s(s.wrapped, False, False, True, False)
    fx = ShapeFix_Shape(conv)
    fx.Perform()
    sols = Shape.cast(fx.Shape()).solids()
    if len(sols) != len(s.solids()):
        raise RuntimeError(f"{name}: B-spline conversion changed the solid count")
    out = sols[0] if len(sols) == 1 else Compound(list(sols))
    if not out.is_valid or n_offset(out) or abs(out.volume - s.volume) > 1e-4 * s.volume:
        raise RuntimeError(f"{name}: B-spline conversion failed ({out.volume:.1f} vs {s.volume:.1f})")
    return out


_cache: dict = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ============================================================================================
# outer body + offsets
# ============================================================================================

def head_body():
    def mk():
        b = rr_prism_y(W, HH, R_FV, Y0, Y1)
        return fillet(b.edges().group_by(Axis.Y)[-1], R_BACK)
    return cached("body", mk)


def inner(d):
    def mk():
        o = offset(head_body(), amount=-d)
        assert o.is_valid and o.volume < head_body().volume - 1000, f"offset {d} failed"
        return o
    return cached(("off", round(d, 3)), mk)


def band(d0, d1):
    """Skin layer between offsets d0 and d1 (d0 < d1) of the outer body."""
    return cached(("band", d0, d1), lambda: (head_body() if d0 <= 0 else inner(d0)) - inner(d1))


# ============================================================================================
# purchased components (catalogue envelopes)
# ============================================================================================

def micro_servo_local():
    """MG90S envelope.  Local frame: origin = spline axis on the case top plane, +Z = output, +X = toward the
    far end of the case (copy of the nova_v8/cad_torso.py convention)."""
    x0, x1 = -MS_SHAFT_END, MS_L - MS_SHAFT_END
    c = bx(x0, x1, -MS_W / 2, MS_W / 2, -MS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 0.6, "servo case")
    t0, t1 = MS_TAB_Z[0] - MS_H, MS_TAB_Z[1] - MS_H
    xc = (x0 + x1) / 2
    tab = bx(xc - MS_TABS / 2, xc + MS_TABS / 2, -MS_W / 2, MS_W / 2, t0, t1)
    hole_far = MS_L - MS_SHAFT_END + MS_TAB_HOLE
    hole_near = MS_SHAFT_END + MS_TAB_HOLE
    for hx in (-hole_near, hole_far):
        tab = tab - cyl_z(1.0, t0 - 1, t1 + 1, hx, 0) - bx(hx, hx + math.copysign(5, hx), -0.5, 0.5, t0 - 1, t1 + 1)
    c = c + tab
    c = c + cyl_z(MS_DOME_R, -0.01, MS_DOME_H, 0, 0) + cyl_z(2.8, -0.01, 1.2, 7.2, 0)
    c = c + cyl_z(MS_SPL_R, MS_DOME_H - 0.01, MS_DOME_H + MS_SPL_H, 0, 0)
    c = c + bx(x1 - 0.01, x1 + 1.6, -1.6, 1.6, -MS_H + 0.8, -MS_H + 4.0)       # cable strain relief
    return c


def servo_frame():
    """Tilt servo placement: local +Z (output) -> global -X, local +X (case far end) -> global +Z."""
    return Plane(origin=(SV_TOP_X, TILT_Y, SERVO_Z), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))


def servo_e32():
    return servo_frame().location * micro_servo_local()


def display_e31():
    lcd = rr_prism_y(DSP_W - 1.0, DSP_H - 1.0, DSP_R, Y_DSP0, Y_DSP0 + 3.0, cz=DSP_ZC)
    pcb = rr_prism_y(DSP_W, DSP_H, DSP_R, Y_DSP0 + 3.0, Y_DSP1 - 1.4, cz=DSP_ZC)
    comp = rr_prism_y(66.0, 40.0, 2.0, Y_DSP1 - 1.4 - 0.01, Y_DSP1, cz=DSP_ZC)   # ESP32-S3 module, connectors
    return lcd + pcb + comp


def ear_pcb_left():
    ey, ez = EAR["y"], EAR["z"]
    p = cyl_x(EPCB_D / 2, X_EAR_IN, X_EAR_IN + EPCB_T, ey, ez)
    s, h = ELED
    x0 = X_EAR_IN + EPCB_T
    leds = [bx(x0 - 0.01, x0 + h, ey - s / 2, ey + s / 2, ez - s / 2, ez + s / 2)]
    for k in range(6):
        a = math.radians(30 + 60 * k)
        cy, cz = ey + 8.0 * math.cos(a), ez + 8.0 * math.sin(a)
        leds.append(Pos(x0 + h / 2 - 0.005, cy, cz) * Rot(math.degrees(a), 0, 0) * Box(h + 0.01, s, s))
    return union([p] + leds)


def pin_m31(sx):
    """DIN 912 M3 x 12: head on the boss face |x| 24, shank to |x| 12 (tip in the barrel pivot hole)."""
    head = cyl_x(2.75, sx * PIVOT_BOSS_X1, sx * (PIVOT_BOSS_X1 + 3.0), TILT_Y, TILT_Z)
    head = head - cyl_x(1.3, sx * (PIVOT_BOSS_X1 + 1.2), sx * (PIVOT_BOSS_X1 + 3.1), TILT_Y, TILT_Z)  # hex ~ round
    shank = cyl_x(1.5, sx * (PIVOT_BOSS_X1 - 12.0), sx * (PIVOT_BOSS_X1 + 0.01), TILT_Y, TILT_Z)
    return head + shank


# ============================================================================================
# gears (YZ plane, axis // X)
# ============================================================================================

def gear_yz(n, m, cy, cz, phase_deg, backlash=0.12, npts=6):
    """Involute spur gear outline (pressure angle 20 deg) as a list of (y, z); tooth k centred at
    phase + k * 360/n (angle measured from +Y toward +Z)."""
    pa = math.radians(20.0)
    rp = n * m / 2
    rb, ra, rf = rp * math.cos(pa), rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a  # noqa: E731
    psi = math.pi / (2 * n) - backlash / (2 * rp)

    def half(r):
        if r <= rb:
            return psi + inv(pa)
        return psi + inv(pa) - inv(math.acos(rb / r))

    r0 = max(rb, rf)
    rs = [rf] + [r0 + (ra - r0) * i / npts for i in range(npts + 1)]
    pts = []
    for k in range(n):
        c = math.radians(phase_deg) + 2 * math.pi * k / n
        pts += [(r, c - half(r)) for r in rs] + [(r, c + half(r)) for r in reversed(rs)]
    return [(cy + r * math.cos(a), cz + r * math.sin(a)) for r, a in pts]


def wedge_x(cy, cz, a0, a1, r, x0, x1):
    """Pie wedge (angles a0..a1 deg from +Y toward +Z) around (cy, cz), radius r, extruded along X."""
    n = max(4, int(abs(a1 - a0) / 5))
    pts = [(cy, cz)] + [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                         cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return prism_x(pts, x0, x1)


def barrel_key(sx):
    """Cross key + hub that fills the N06 horn recess (1.8 deep, 0.2 floor clearance) on side sx."""
    xa, xb = sx * (BAR_X - 1.6), sx * (BAR_X + 0.01)
    k = bx(xa, xb, -9.4, 9.4, TILT_Z - 2.7, TILT_Z + 2.7) + bx(xa, xb, -2.7, 2.7, TILT_Z - 9.4, TILT_Z + 9.4) + \
        cyl_x(3.8, xa, xb, TILT_Y, TILT_Z)
    return k


def barrel_disc(sx, teeth):
    """H09 (teeth=True, +X) / H10 (-X): disc on the barrel end face + key, pivot bore, 2 screw holes."""
    x0, x1 = sx * DISC_X0, sx * DISC_X1
    hub = cyl_x(9.8, x0, x1, TILT_Y, TILT_Z)
    if teeth:
        g = prism_x(gear_yz(G_N, G_M, TILT_Y, TILT_Z, 90.0), min(x0, x1), max(x0, x1))
        wd = wedge_x(TILT_Y, TILT_Z, 90 - SECTOR_HALF, 90 + SECTOR_HALF, 13.0, min(x0, x1), max(x0, x1))
        d = (g & wd) + (hub - wd)
    else:
        d = hub
    d = d + barrel_key(sx)
    d = d - cyl_x(1.6, sx * (BAR_X - 2), sx * (DISC_X1 + 1), TILT_Y, TILT_Z)
    for sy in (1, -1):
        d = d - cyl_x(1.1, sx * (BAR_X - 2), sx * (DISC_X1 + 1), sy * 7.5, TILT_Z)
        d = d - cyl_x(2.1, sx * (DISC_X1 - 1.4), sx * (DISC_X1 + 1), sy * 7.5, TILT_Z)   # pan head M2 counterbore
    return solid1(d)


def servo_gear_h11():
    """20T on the servo spline; at tilt 0 a tooth GAP points down (-Z) toward the H09 tooth at +Z."""
    g = prism_x(gear_yz(G_N, G_M, TILT_Y, SERVO_Z, 270.0 + 180.0 / G_N), H11_X0, H11_X1)
    g = g + cyl_x(H11_HUB_R, H11_X1 - 0.01, H11_HUB_X1, TILT_Y, SERVO_Z)
    g = g - cyl_x(2.2, SPL_TIP_X, H11_HUB_X1 + 1, TILT_Y, SERVO_Z)          # Ø4.4 press fit on the spline
    g = g - cyl_x(1.1, H11_X0 - 1, SPL_TIP_X + 0.1, TILT_Y, SERVO_Z)        # horn screw M2
    return solid1(g)


# ============================================================================================
# H01 / H02 - white shell + back cover
# ============================================================================================

def ledge_ring(y0, y1):
    lo = SEAM + LEDGE_BACK_OUT
    return (rr_prism_y(BC["w"] + 2 * lo, BC["h"] + 2 * lo, BC["r"] + lo, y0, y1)
            - rr_prism_y(BC["w"] - 2 * LEDGE_BACK_IN, BC["h"] - 2 * LEDGE_BACK_IN, BC["r"] - LEDGE_BACK_IN,
                         y0 - 1, y1 + 1))


def shells():
    body = head_body()
    front = body.faces().sort_by(Axis.Y)[0]
    shell = offset(body, amount=-WALL, openings=[front])
    if shell.volume > 0.5 * body.volume:          # offset silently returned the unchanged solid
        shell = body - inner(WALL)
        shell = retry(lambda: shell - rr_prism_y(W - 2 * WALL, HH - 2 * WALL, R_FV - WALL, Y0 - 2, Y0 + WALL + 0.5),
                      "front opening")
    shell = check("shell", shell)
    rim_out = edges_where(shell, lambda p: abs(p.Y - Y0) < 0.02 and abs(rr_dist(p.X, p.Z, W, HH, R_FV)) < 0.02)
    shell = try_fillet(shell, rim_out, R_RIM, "rim outer")
    iw, ih, ir = W - 2 * WALL, HH - 2 * WALL, R_FV - WALL
    rim_in = edges_where(shell, lambda p: abs(p.Y - Y0) < 0.02 and abs(rr_dist(p.X, p.Z, iw, ih, ir)) < 0.02)
    shell = try_fillet(shell, rim_in, 0.2, "rim inner")
    shell = check("shell", shell)

    # ---- back cover split (projected rounded rectangle along Y) ----
    yb = 0.0
    h02 = solid1(shell & rr_prism_y(BC["w"], BC["h"], BC["r"], yb, Y1 + 5))
    h01 = solid1(shell - rr_prism_y(BC["w"] + 2 * SEAM, BC["h"] + 2 * SEAM, BC["r"] + SEAM, yb, Y1 + 5))
    skin = Compound(body.faces())

    def seam_edges(shape, w, h, r):
        return edges_where(shape, lambda p: p.Y > 10 and abs(rr_dist(p.X, p.Z, w, h, r)) < 0.03
                           and skin.distance_to(Vector(p.X, p.Y, p.Z)) < 0.03)

    h02 = try_chamfer(h02, seam_edges(h02, BC["w"], BC["h"], BC["r"]), SEAM_BREAK, "H02 seam")
    h01 = try_chamfer(h01, seam_edges(h01, BC["w"] + 2 * SEAM, BC["h"] + 2 * SEAM, BC["r"] + SEAM), SEAM_BREAK,
                      "H01 seam")

    # ---- seam backing ledge (the cover rests on it, the seam never shows the hollow inside) ----
    slab = bx(-W, W, yb, Y1 + 5, ZC - HH, ZC + HH)
    ledge = retry(lambda: band(WALL, WALL + LEDGE_BACK_T) & slab & ledge_ring(yb, Y1 + 5), "ledge")
    h01 = retry(lambda: h01 + ledge, "ledge fuse")
    # pry notch at the bottom centre of the seam (on the hidden underside of the back)
    notch = bx(-4.0, 4.0, 20.0, Y1 + 2, ZC - BC["h"] / 2 - SEAM - 1.0, ZC - BC["h"] / 2 + 0.1) & band(-0.01, 1.0)
    h01 = retry(lambda: h01 - notch, "pry notch")

    # ---- H02: 2 top tongues behind the ledge + 1 bottom snap latch ----
    zt, zb = ZC + BC["h"] / 2, ZC - BC["h"] / 2           # 179 / 129
    for sx in (1, -1):
        x0, x1 = sorted((sx * 17.0, sx * 27.0))
        t_root = band(WALL - 0.05, WALL + LEDGE_BACK_T + 1.6) & bx(x0, x1, 10, Y1 + 5, zt - 5.0, zt - LEDGE_BACK_IN - 0.2)
        t_up = band(WALL + LEDGE_BACK_T + 0.35, WALL + LEDGE_BACK_T + 1.6) & bx(x0, x1, 10, Y1 + 5, zt - 5.0,
                                                                                 zt + SEAM + LEDGE_BACK_OUT - 0.2)
        h02 = retry(lambda: h02 + t_root + t_up, "H02 tongue")
    zl0 = zb - SEAM - LEDGE_BACK_OUT - 1.1                    # latch lip under the ledge end (z 125.4)
    for sx in (1, -1):                                         # 2 latches beside the pocket back wall
        x0, x1 = sorted((sx * LATCH_X[0], sx * LATCH_X[1]))
        l_root = band(WALL - 0.05, WALL + LEDGE_BACK_T + 1.6) & bx(x0, x1, 10, Y1 + 5, zb + LEDGE_BACK_IN + 0.2,
                                                                    zb + 5.0)
        l_arm = band(WALL + LEDGE_BACK_T + 0.35, WALL + LEDGE_BACK_T + 1.6) & bx(x0, x1, 10, Y1 + 5, zl0, zb + 5.0)
        l_lip = band(WALL + 0.3, WALL + LEDGE_BACK_T + 0.4) & bx(x0, x1, 10, Y1 + 5, zl0, zl0 + 0.95)
        h02 = retry(lambda: h02 + l_root + l_arm + l_lip, "H02 latch")

    # ---- barrel pocket: walls, thrust pads, pivot bosses ----
    pw, pd, pr, ptop = PK_W, PK_D, PK_R, PK_TOP
    pocket_out = rr_prism_z(pw + 2 * PK_WALL, pd + 2 * PK_WALL, pr + PK_WALL, Z0 - 1, ptop + PK_WALL, cy=TILT_Y)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 4.0)
    pocket_in = rr_prism_z(pw, pd, pr, Z0 - 5, ptop, cy=TILT_Y)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 3.0)
    h01 = retry(lambda: h01 + (pocket_out & body), "pocket walls")
    h01 = retry(lambda: h01 - pocket_in, "pocket")
    e_pk = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and abs(rr_dist_xy(p.X, p.Y, pw, pd, pr, TILT_Y)) < 0.02)
    h01 = try_fillet(h01, e_pk, 1.0, "pocket rim")
    feats = []
    for sx in (1, -1):
        feats.append(cyl_x(5.0, sx * PAD_X, sx * (PK_X_IN + 0.3), TILT_Y, TILT_Z))                 # thrust pad
        feats.append(cyl_x(PIVOT_BOSS_R, sx * (PK_X_OUT - 0.5), sx * PIVOT_BOSS_X1, TILT_Y, TILT_Z))
        feats.append(bx(sx * (PK_X_OUT - 0.5), sx * PIVOT_BOSS_X1, -1.0, 1.0, Z0 + 0.5, TILT_Z) & body)  # rib
    h01 = retry(lambda: h01 + union(feats), "pivot bosses")

    # ---- tilt-servo rails (+X): lower rail on the pocket wall, upper rail hanging from the roof ----
    rx0, rx1 = TAB_X0 - RAIL_CLR, TAB_X1 + RAIL_CLR                  # groove 26.45 .. 29.25
    w_in, w_out = rx0 - RAIL_WALL, rx1 + 3.0                         # inner wall 1.6, outer wall 3.0 (stop screw)
    lo = bx(w_in, w_out, RAIL_Y0, RAIL_Y1, TAB_Z0 - RAIL_CLR - RAIL_WALL, SV_Z0 - 0.3) + \
        bx(PK_X_OUT - 0.5, w_in + 0.01, RAIL_Y0, RAIL_Y1, TAB_Z0 - RAIL_CLR - RAIL_WALL, TAB_Z0 - RAIL_CLR)
    lo = lo - bx(rx0, rx1, RAIL_Y0 - 1, RAIL_STOP, TAB_Z0 - RAIL_CLR, SV_Z0 + 1)
    lo = lo - cyl_y(PILOT_R, RAIL_Y0 - 0.5, RAIL_Y0 + 6.0, rx1 + 1.25, TAB_Z0 + 2.45)   # M2 stop screw + washer
    up = bx(w_in, w_out, RAIL_Y0, RAIL_Y1, SV_Z1 + 0.3, Z1 + 1) & body
    up = up - bx(rx0, rx1, RAIL_Y0 - 1, RAIL_STOP, SV_Z1 - 1, TAB_Z1 + RAIL_CLR)
    h01 = retry(lambda: h01 + lo + up, "servo rails")

    # ---- gear slot: H11 + spline/dome path from the front opening to the mesh position ----
    slot_a = bx(SPL_TIP_X - 2.7, PK_X_IN + 0.01, -24.0, 11.6, SERVO_Z - 11.5, SERVO_Z + 11.6)
    slot_b = bx(H11_X1, SV_TOP_X + 0.3, -24.0, MS_DOME_R + 0.5, SERVO_Z - MS_DOME_R - 0.5, SERVO_Z + MS_DOME_R + 0.5)
    h01 = retry(lambda: h01 - slot_a - slot_b, "gear slot")

    # ---- collar relief: at tilt +20 / pan +-90 the N01 top edge rises to z 117.3 just ahead of the pocket mouth
    #      -> 2.0 chamfer from the pocket front edge, floor thickened inside by a pad (wall stays >= 1.7) ----
    yr0, yr1 = -PK_D / 2, RELIEF_Y1
    pad = bx(-PK_X_OUT, PK_X_OUT, yr1, yr0 - 0.5, Z0 + 1.0, Z0 + WALL + RELIEF_PAD) & body
    h01 = retry(lambda: h01 + pad, "relief pad")
    rel = prism_x([(yr0 + 1.0, Z0 - 1.0), (yr0 + 1.0, Z0 + RELIEF_D), (yr0, Z0 + RELIEF_D), (yr1, Z0),
                   (yr1 - 1.0, Z0 - 1.0)], -PK_X_OUT, PK_X_OUT)
    h01 = retry(lambda: h01 - rel, "collar relief")

    # ---- neck cable hole (4 wires) in the pocket ceiling, behind the barrel slot ----
    h01 = retry(lambda: h01 - bx(-4.5, 4.5, 3.0, 15.0, ptop - 1, ptop + PK_WALL + 1), "cable hole")
    # ---- M3 pilots on the tilt axis (through pad, wall, boss) ----
    for sx in (1, -1):
        h01 = retry(lambda: h01 - cyl_x(M3_PILOT_R, sx * (PAD_X - 1), sx * (PIVOT_BOSS_X1 + 1), TILT_Y, TILT_Z),
                    "M3 pilot")

    # ---- front module: 2 screw bosses (top sides) + tongue slot block on the pocket front wall ----
    feats = []
    for (x, z) in H01_BOSSES:
        sx = math.copysign(1, x)
        feats.append(cyl_y(BOSS_R, Y0 + 0.6, Y_DSP1, x, z))
        feats.append(bx(x, sx * (X_SIDE - 0.5), Y0 + 0.6, Y_DSP1, z - 1.2, z + 1.2) & body)
    sb = SLOT_BLOCK
    feats.append(bx(-sb["w"] / 2, sb["w"] / 2, sb["y0"], -PK_D / 2 - 0.5, Z0 + 0.5, sb["z1"]) & body)
    h01 = retry(lambda: h01 + union(feats), "front bosses")
    for (x, z) in H01_BOSSES:
        h01 = retry(lambda: h01 - cyl_y(PILOT_R, Y_DSP1 + 0.1, Y_DSP1 - 5.5, x, z), "boss pilot")
    tg = TONGUE
    h01 = retry(lambda: h01 - bx(-tg["w"] / 2 - 0.2, tg["w"] / 2 + 0.2, sb["y0"] - 0.5, tg["y1"] + 0.2,
                                 tg["z0"] - 0.2, tg["z0"] + tg["t"] + 0.2), "tongue slot")

    # ---- ear holes + cups with stop rings (ears pushed in from outside, glued) ----
    ey, ez = EAR["y"], EAR["z"]
    for sx in (1, -1):
        cup = cyl_x(CUP_RO, sx * (X_EAR_IN - CUP_STOP_T), sx * (X_SIDE - 0.5), ey, ez) & body
        h01 = retry(lambda: h01 + cup, "ear cup")
        h01 = retry(lambda: h01 - cyl_x(EAR_HOLE_R, sx * X_EAR_IN, sx * (X_SIDE + 3.0), ey, ez), "ear hole")
        h01 = retry(lambda: h01 - cyl_x(CUP_STOP_RI, sx * (X_EAR_IN - CUP_STOP_T - 1), sx * (X_EAR_IN + 0.1), ey, ez),
                    "ear cup opening")
    e_ear = edges_where(h01, lambda p: abs(abs(p.X) - X_SIDE) < 1.5
                        and abs(math.hypot(p.Y - ey, p.Z - ez) - EAR_HOLE_R) < 0.02
                        and skin.distance_to(Vector(p.X, p.Y, p.Z)) < 0.03)
    h01 = try_fillet(h01, e_ear, 0.3, "ear hole edge")
    h01 = solid1(h01)
    return check("H01", h01, vmin=20000), check("H02", solid1(h02), vmin=3000)


# ============================================================================================
# H03 bezel, H04 glass, H04C camera window, H04E eyes, H07 display bracket
# ============================================================================================

def bezel():
    bw, bh, br = BZ["w"], BZ["h"], BZ["r"]
    b = rr_prism_y(bw, bh, br, Y_BZ_FRONT, SKIRT_END)
    b = fillet(b.edges().group_by(Axis.Y)[0], BZ_FRONT_FILLET)
    gw, gh, gr = GL["w"] + 2 * GLASS_CLR, GL["h"] + 2 * GLASS_CLR, GL["r"] + GLASS_CLR
    b = b - rr_prism_y(gw, gh, gr, Y_BZ_FRONT - 1, Y_LEDGE0, cz=GZ)
    lw, lh, lr = LEDGE_OPEN
    b = b - rr_prism_y(lw, lh, lr, Y_LEDGE0 - 0.5, Y_LEDGE1 + 0.01, cz=WIN_ZC)
    b = b - rr_prism_y(DSP_W + 2 * DSP_CLR, DSP_H + 2 * DSP_CLR, DSP_R + DSP_CLR, Y_LEDGE1, SKIRT_END + 1, cz=DSP_ZC)
    b = b - rr_prism_y(bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL, Y0, SKIRT_END + 1)
    # bosses for the H07 screws (end faces on the board-back plane y -27.3)
    for (x, z) in BZ_BOSSES:
        boss = cyl_y(BOSS_R, Y0 - 0.5, Y_DSP1, x, z)
        if x != 0:
            boss = boss + bx(x, math.copysign(bw / 2 - 1.0, x), Y0 - 0.5, SKIRT_END, z - 1.0, z + 1.0)
        b = b + (boss & rr_prism_y(bw - 0.4, bh - 0.4, br - 0.2, Y0 - 1, Y_DSP1 + 1))
        b = b - cyl_y(PILOT_R, Y_DSP1 + 0.1, Y_LEDGE1 + 0.2, x, z)
    # skirt notches around the H01 front-module bosses
    for (x, z) in H01_BOSSES:
        b = b - cyl_y(BOSS_R + 0.6, Y0 + 0.05, SKIRT_END + 1, x, z) - \
            bx(x, math.copysign(W, x), Y0 + 0.05, SKIRT_END + 1, z - 1.8, z + 1.8)
    e_in = edges_where(b, lambda p: abs(p.Y - Y_BZ_FRONT) < 0.02 and abs(rr_dist(p.X, p.Z, gw, gh, gr, GZ)) < 0.02)
    b = try_fillet(b, e_in, 0.4, "H03 seat edge")
    return check("H03", solid1(b), vmin=3000)


def glass():
    g = rr_prism_y(GL["w"], GL["h"], GL["r"], Y_GL_FRONT, Y_GL_BACK, cz=GZ)
    g = try_fillet(g, g.edges().group_by(Axis.Y)[0], 0.4, "H04 edge")
    return check("H04", g)


def camera_window():
    r, sag = CAM["d"] / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_GL_FRONT - sag + rs, CAM["z"]) * Sphere(rs)
    return check("H04C", sph & cyl_y(r, Y_GL_FRONT - 1.0, Y_GL_FRONT, 0.0, CAM["z"]))


def eyes():
    t = 0.15
    out = None
    for sx in (-1, 1):
        with BuildSketch(plane_y(Y_GL_FRONT - t, sx * EYE["x"], EYE["z"])) as sk:
            SlotOverall(EYE["h"], EYE["w"], rotation=90)
        e = extrude(sk.sketch, t)
        out = e if out is None else out + e
    return check("H04E", out)


def bracket_h07():
    plate = rr_prism_y(90.0, 60.0, 8.0, Y_DSP1, Y_H07_1, cz=DSP_ZC)
    lugs = [cyl_y(3.0, Y_DSP1, Y_H07_1, x, z) for (x, z) in BZ_BOSSES] + \
        [cyl_y(2.7, Y_DSP1, Y_H07_1, x, z) for (x, z) in H01_BOSSES]
    lugs += [bx(math.copysign(40.0, x), x, Y_DSP1, Y_H07_1, z - 2.7, z + 2.7) for (x, z) in H01_BOSSES]
    tg = TONGUE
    lugs.append(bx(-7.0, 7.0, Y_DSP1, Y_H07_1, tg["z0"], DSP_ZC - 25.0))
    lugs.append(bx(-tg["w"] / 2, tg["w"] / 2, Y_H07_1 - 0.01, tg["y1"], tg["z0"], tg["z0"] + tg["t"]))
    pad = rr_prism_y(DSP_W - 0.6, DSP_H - 0.6, DSP_R, Y_DSP1 - 1.4, Y_DSP1 + 0.01, cz=DSP_ZC) - \
        rr_prism_y(76.0, 44.0, 5.0, Y_DSP1 - 2, Y_DSP1 + 1, cz=DSP_ZC)
    b = plate + union(lugs) + pad
    b = b - rr_prism_y(76.0, 44.0, 5.0, Y_DSP1 - 2, Y_H07_1 + 1, cz=DSP_ZC)
    for (x, z) in BZ_BOSSES + H01_BOSSES:
        b = b - cyl_y(1.2, Y_DSP1 - 1, Y_H07_1 + 1, x, z)
    return check("H07", solid1(b), vmin=1500)


# ============================================================================================
# H05 ears + H06 LED rings (left ear, +X, revolved about the ear axis)
# ============================================================================================

EAR_RS = (EAR_R ** 2 + EAR_DOME ** 2) / (2 * EAR_DOME)
EAR_SC = X_EAR_OUT - EAR_RS


def dome_x(r, extra=0.0):
    rr = EAR_RS + extra
    return EAR_SC + math.sqrt(rr * rr - r * r)


def dome_pt(r, extra=0.0):
    return (dome_x(r, extra), r)


def dome_arc(r0, r1, extra=0.0):
    return ("A", dome_pt((r0 + r1) / 2, extra), dome_pt(r1, extra))


def revolve_x(segs, start):
    def v(p):
        return Vector(p[0], 0.0, p[1])
    edges, cur = [], start
    for sg in segs:
        if sg[0] == "L":
            edges.append(Edge.make_line(v(cur), v(sg[1])))
            cur = sg[1]
        else:
            edges.append(Edge.make_three_point_arc(v(cur), v(sg[1]), v(sg[2])))
            cur = sg[2]
    if math.dist(cur, start) > 1e-6:
        edges.append(Edge.make_line(v(cur), v(start)))
    return Solid.revolve(Face(Wire(edges)), 360, Axis.X)


def ear_left():
    R = EAR_R
    ro, ri = EAR["ring_od"] / 2, EAR["ring_id"] / 2
    g_o, g_i = ro + 0.1, ri - 0.1
    f = EAR_FILLET
    fc_r = R - f
    fc_x = EAR_SC + math.sqrt((EAR_RS - f) ** 2 - fc_r ** 2)
    k = EAR_RS / (EAR_RS - f)
    t_dome = (EAR_SC + (fc_x - EAR_SC) * k, fc_r * k)
    t_cyl = (fc_x, R)
    a_mid = math.atan2(t_dome[1] - fc_r, t_dome[0] - fc_x) / 2 + math.pi / 4
    f_mid = (fc_x + f * math.cos(a_mid), fc_r + f * math.sin(a_mid))
    segs = [
        ("L", (X_EAR_IN, R)),
        ("L", t_cyl),
        ("A", f_mid, t_dome),
        dome_arc(t_dome[1], g_o),
        ("L", (X_BRIDGE1, g_o)),
        ("L", (X_BRIDGE1, g_i)),
        ("L", dome_pt(g_i)),
        dome_arc(g_i, MIC_R),
        ("L", (X_BRIDGE0, MIC_R)),
        ("L", (X_BRIDGE0, EAR_REC_R)),
    ]
    disc = revolve_x(segs, (X_EAR_IN, EAR_REC_R))
    # 3 light windows through the bridge layer (bridges 1.4 wide at 90/210/330 deg)
    win = cyl_x(g_o, X_BRIDGE0 - 0.1, X_BRIDGE1 + 0.1, 0, 0) - cyl_x(g_i, X_BRIDGE0 - 0.2, X_BRIDGE1 + 0.2, 0, 0)
    for a in (90, 210, 330):
        win = win - Rot(a, 0, 0) * bx(X_BRIDGE0 - 1, X_BRIDGE1 + 1, -0.7, 0.7, 0, 20)
    disc = disc - win
    e = 0.15
    rsegs = [
        ("L", (X_BRIDGE1 + 0.05, ro)),
        ("L", (dome_x(ro, RING_PROUD) - e, ro)),
        ("L", dome_pt(ro - e, RING_PROUD)),
        dome_arc(ro - e, ri + e, RING_PROUD),
        ("L", (dome_x(ri, RING_PROUD) - e, ri)),
    ]
    ring = revolve_x(rsegs, (X_BRIDGE1 + 0.05, ri))
    ey, ez = EAR["y"], EAR["z"]
    return check("H05", solid1(Pos(0, ey, ez) * disc), vmin=1000), check("H06", Pos(0, ey, ez) * ring, vmin=50)


# ============================================================================================

def build():
    t0 = time.time()
    h01, h02 = shells()
    print(f"  shells {time.time() - t0:.1f}s")
    ear_l, ring_l = ear_left()
    pcb_l = ear_pcb_left()
    J = "J3"
    U = 40.0          # head lift in exploded views (all J3 parts), local offsets below follow the assembly order
    P = [
        PartRec("H01", "Hlavný obal hlavy", step_safe("H01", h01), "white", SUB, J, (0, 0, U),
                note="106×66×74, R26/R20, stena 2.0, kapsa valca 37.2×40 R12 so štrbinou kolies, 2 nálitky čapov M3 "
                     "na osi náklonu, lišty serva, 2 nálitky + drážka predného modulu, misky uší, lišta zadného krytu"),
        PartRec("H02", "Zadný kryt hlavy", step_safe("H02", h02), "white", SUB, J, (0, 45, U),
                note="88×50 R15, škára 0.6, 2 horné jazýčky + 1 spodná západka, bez skrutiek"),
        PartRec("H03", "Predný rám", bezel(), "black", SUB, J, (0, -45, U),
                note="101×69 R23.5, vystupuje 5 mm, lôžko skla, osadenie 1.4 (okno 85×50), 3 nálitky pre H07"),
        PartRec("H04", "Krycie sklo", glass(), "glass", SUB, J, (0, -62, U),
                note="dymový akrylát PMMA 2.0 rezaný laserom 92×60 R16, čierna maska zvnútra (hore 7, inde 4 mm), VHB"),
        PartRec("H04C", "Okienko kamery", camera_window(), "black_gloss", SUB, J, (0, -62, U),
                note="len objekt pre render: okienko voliteľnej kamery v hornom páse masky"),
        PartRec("H04E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -62, U),
                note="len objekt pre render: dve pilulky 10.5×17.5"),
        PartRec("H05-R", "Ucho pravé", mirror(ear_l, Plane.YZ), "black", SUB, J, (-30, 0, U),
                note="Ø28, vystupuje 4 mm, zadné vybranie pre LED modul Ø23, 3 mostíky, zalisuje sa + CA lepidlo"),
        PartRec("H05-L", "Ucho ľavé", ear_l, "black", SUB, J, (30, 0, U),
                note="Ø28, vystupuje 4 mm, zadné vybranie pre LED modul Ø23, 3 mostíky, zalisuje sa + CA lepidlo"),
        PartRec("H06-R", "LED krúžok ucha pravý", mirror(ring_l, Plane.YZ), "cyan_led", SUB, J, (-42, 0, U),
                note="svetlovod Ø23/Ø17 (číry PETG / PMMA)"),
        PartRec("H06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (42, 0, U),
                note="svetlovod Ø23/Ø17 (číry PETG / PMMA)"),
        PartRec("H07", "Držiak displeja", bracket_h07(), "grey", SUB, J, (0, -18, U), internal=True,
                note="PETG rám: pritlačí dosku 86×56 na osadenie H03 (3× M2×6), do H01 1 jazýček + 2× M2×8 zozadu"),
        PartRec("H09", "Ozubený segment náklonu", barrel_disc(1, True), "grey", "neck", "J2", (12, 0, 0),
                internal=True,
                note="20z m1, ±63°, kríž do vybrania valca N06 (+X), 2× M2 do pilotov valca, otvor Ø3.2 pre čap"),
        PartRec("H10", "Púzdro čapu náklonu", barrel_disc(-1, False), "grey", "neck", "J2", (-12, 0, 0),
                internal=True, note="rovnaký kríž bez zubov na −X konci valca, dlhšie ložisko čapu"),
        PartRec("H11", "Koliesko serva náklonu", servo_gear_h11(), "grey", SUB, J, (12, -10, U + 40), internal=True,
                note="20z m1 na drážkovaní MG90S (Ø4.4 natlačiť za tepla) + skrutka M2 zo sady serva, prevod 1:1"),
        PartRec("E31", "Displej ESP32-S3 3.5\" (doska)", display_e31(), "display", SUB, J, (0, -30, U),
                internal=True, note=DSP["board"] + " – obrys 86×56×6, pena 0.5 mm pred LCD"),
        PartRec("E32", "Servo náklonu MG90S", servo_e32(), "servo", SUB, J, (22, -10, U + 40), internal=True,
                note="MG90S 22.8×12.2×22.7, uši 32.5, hriadeľ (y 0, z 147) ∥ X, telo hore, zasunie sa spredu do líšt"),
        PartRec("E33-R", "DPS ucha pravá", mirror(pcb_l, Plane.YZ), "pcb", SUB, J, (-20, 0, U),
                internal=True, note="okrúhly modul 7× WS2812B-5050 Ø23 (AliExpress), vlepený do ucha"),
        PartRec("E33-L", "DPS ucha ľavá", pcb_l, "pcb", SUB, J, (20, 0, U), internal=True,
                note="okrúhly modul 7× WS2812B-5050 Ø23 (AliExpress), vlepený do ucha"),
        PartRec("M31-R", "Čap náklonu M3×12 pravý", pin_m31(-1), "metal", SUB, J, (-18, 0, U), internal=True,
                note="DIN 912 M3×12 do pilotu Ø2.5 v H01, beží v otvore Ø3.2 valca N06 / H10"),
        PartRec("M31-L", "Čap náklonu M3×12 ľavý", pin_m31(1), "metal", SUB, J, (18, 0, U), internal=True,
                note="DIN 912 M3×12 do pilotu Ø2.5 v H01, beží v otvore Ø3.2 H09 + valca N06"),
    ]
    for p in P:
        check(p.id, p.shape)
    print(f"  build {time.time() - t0:.1f}s")
    return P


# ============================================================================================
# checks
# ============================================================================================

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


def interference(parts, others=(), tol=0.5, skip=()):
    allp = list(parts) + list(others)
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


def other_parts(build_others=False):
    """Parts of the other v8 modules present in build_v8/manifest (STEP import = their last export;
    --build-others runs their build() instead)."""
    import importlib
    import json
    from build123d import import_step
    out = []
    mdir = os.path.join(OUT_DIR, "manifest")
    for fn in sorted(os.listdir(mdir)):
        name = fn[:-5]
        if not fn.endswith(".json") or name == MANIFEST:
            continue
        if build_others:
            m = importlib.import_module(f"nova_v8.cad_{name}")
            out += m.build()
            continue
        for r in json.load(open(os.path.join(mdir, fn))):
            stp = os.path.join(OUT_DIR, "step", f"{r['id']}.step")
            if os.path.exists(stp):
                out.append(PartRec(r["id"], r["name"], import_step(stp), r["mat"], r["sub"], r["joint"],
                                   tuple(r["explode"]), r["internal"], r["note"]))
    return out


TILT_AXIS = Axis((0, TILT_Y, TILT_Z), (1, 0, 0))
# intended overlaps: M3 screws thread-form into the Ø2.5 pilots, H11 Ø4.4 bore pressed onto the Ø4.8 spline
FITS = {("H01", "M31-R"), ("H01", "M31-L"), ("H11", "E32")}


def pose_sweep(parts, others):
    """Head frame check: J2 parts rotate by -tilt, J1 parts by -pan then -tilt.  Returns collisions > 0.5 mm3."""
    head = [p for p in parts if p.id in ("H01", "H03", "H07", "H11", "E31", "E32", "M31-R", "M31-L")]
    head_out = [p for p in parts if p.id in ("H01", "H03", "H05-R", "H05-L")]
    j2 = [p for p in parts + others if p.joint == "J2"]
    j1 = [p for p in others if p.joint == "J1" and p.id in ("N01", "T01")]
    gear_pair = {("H11", "H09"), ("H09", "H11")}
    res = []
    for th in (-20, -10, 0, 10, 20):
        for q in j2:
            qs = q.shape.rotate(TILT_AXIS, -th)
            for h in head:
                if (h.id, q.id) in gear_pair:
                    hs = h.shape.rotate(Axis((0, TILT_Y, SERVO_Z), (1, 0, 0)), th)   # 1:1 external mesh
                else:
                    hs = h.shape
                v = common_vol(hs, qs)
                if v > 0.5 or v < 0:
                    res.append((f"tilt {th}", h.id, q.id, round(v, 2)))
        for ph in ((-90, -67.5, -45, 0, 45, 67.5, 90) if abs(th) == 20 else ()):
            for q in j1:
                qs = q.shape.rotate(Axis.Z, -ph).rotate(TILT_AXIS, -th)
                for h in head_out:
                    v = common_vol(h.shape, qs)
                    if v > 0.5 or v < 0:
                        res.append((f"tilt {th} pan {ph}", h.id, q.id, round(v, 2)))
    return res


def verify_step(ids):
    from build123d import import_step
    out = []
    for pid in ids:
        s = import_step(os.path.join(OUT_DIR, "step", f"{pid}.step"))
        out.append((pid, s.is_valid, round(s.volume, 1)))
    return out


if __name__ == "__main__":
    t0 = time.time()
    ps = build()
    recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
    for p, r in zip(ps, recs):
        print(f"  {r['id']:6s} {r['mat']:11s} {r['joint']:3s} {'int' if r['internal'] else '   '} "
              f"valid={p.shape.is_valid} size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("  STEP re-import:", verify_step(["H01", "H02", "H03"]))
    print("  interference (own):", interference(ps, skip=FITS) or "none")
    if "--check" in sys.argv or "--pose" in sys.argv:
        oth = other_parts("--build-others" in sys.argv)
        print(f"  loaded {len(oth)} parts of other modules")
        if "--check" in sys.argv:
            print("  interference (with others):", interference(ps, oth, skip=FITS) or "none")
        if "--pose" in sys.argv:
            print("  pose sweep:", pose_sweep(ps, oth) or "none")
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")
