"""
NOVA – HEAD (H01..H06).  Run:  /opt/venv/cad/bin/python -m nova.cad.head

All parts are built in final assembly position (joint J3 = head tilt about the X axis through
spec.TILT_AXIS).  Every shared number comes from spec.HEAD / spec.NECK / spec.TILT_AXIS (v7.3) and the
assembly concept of docs/REVIEW_NOTES.md; the named constants below are purely local construction
values (clearances, rib / snap sizes).

Parts
  H01      Hlavný obal hlavy        white      rounded box shell 132 x 90 x 96, open front (0.3 gap to H03),
                                               closed neck pocket 56x56 R16 depth 35 with Ø18.4 U-slots for
                                               the N07 hubs, ear seats, 2x3 vents, 4 ribbed bosses for H11, back ledge
  H02      Zadný kryt hlavy         white      back cover 112x66 R20 projected on the rear surface,
                                               0.6 mm seam, 1.2 mm locating lip, 4 snap hooks + 1x M2 from below
  H03      Predný rám               black      frame 127x91 R29.5 protruding 7 mm, glass seat + 3 mm ledge with
                                               11 mm camera notch, skirt, 2 bottom hooks + 2 M2 bosses for H11
  H04      Sklo displeja            glass      119x79 R22 x 1.1 cover glass (one piece, print 9 top / 4 others)
  H04C     Okienko kamery           black_gloss  RENDER-ONLY: unprinted Ø3.2 camera window on the glass
  H04E     Obsah displeja – oči     eye        RENDER-ONLY: display content, two warm pill eyes
  H05-R/L  Ucho pravé / ľavé        black      Ø36 domed ear discs (touch + mic), snap-in from outside
  H06-R/L  LED krúžok ucha          cyan_led   Ø30/Ø23 light-guide rings
"""
from __future__ import annotations

import math

from build123d import (Align, Axis, Box, BuildSketch, Compound, Cylinder, Edge, Face, Locations, Plane, Pos, ShapeList,
                       RectangleRounded, Rot, SlotOverall, Solid, Vector, Wire, extrude, fillet,
                       mirror, offset, chamfer)

from nova import spec
from nova.cad.common import PartRec, run_module

H = spec.HEAD
W, D, HH = H["w"], H["d"], H["h"]          # 132 x 90 x 96
Y0, Y1 = H["y0"], H["y1"]                  # -46 (front rim) .. +44 (back)
Z0, Z1, ZC = H["z0"], H["z1"], H["zc"]     # 169 .. 265, centre 217
WALL = H["wall"]                           # 2.2
BZ = H["bezel"]
GL = H["glass"]
CAM = H["camera"]
DSP = H["display"]
EYE = H["eyes"]
EAR = H["ear"]
BC = H["back_cover"]
NR = H["neck_recess"]
VT = H["vents"]
TILT_Y, TILT_Z = spec.TILT_AXIS["y"], spec.TILT_AXIS["z"]

# ---- derived levels -----------------------------------------------------------------------
Y_BEZEL_FRONT = Y0 - BZ["protrude"]                  # -53
Y_GLASS_FRONT = Y_BEZEL_FRONT + GL["recess"]         # -52
Y_GLASS_BACK = Y_GLASS_FRONT + GL["t"]               # -50.9
Y_SKIRT_BACK = Y0 + BZ["depth"]                      # -30  (skirt reaches 16 mm behind the rim plane)
GZ = GL["zc"]                                        # glass centre z 216
X_EAR_OUT = W / 2 + EAR["protrude"]                  # 71.5 (dome apex)

# ---- local construction constants (not shared dimensions) ---------------------------------
SEAM = BC["seam"]        # 0.6
SEAM_BREAK = 0.3         # 0.3 x 45 deg break on both edges of visible static seams (review notes)
FRONT_GAP = 0.3          # uniform gap H03 <-> H01 front opening (v7.3: bezel R29.5)
SKIRT_WALL = 2.0         # bezel skirt wall
SKIRT_MIN_WALL = 0.6     # minimum skirt wall where it is notched for the display corners
SKIRT_END_CLR = 0.5      # skirt end stays 0.5 in front of the neck-pocket front wall (y = -30)
GLASS_CLR = 0.15         # glass <-> bezel seat clearance (per side)
PSA_T = 0.2              # glass adhesive (PSA) between glass and ledge
LEDGE_W = 3.0            # glass support ledge width (review notes: 3 mm, hidden behind the print)
LEDGE_T = 1.6            # glass support ledge thickness (display clamped behind it on 0.5 foam)
CAM_NOTCH_W = 11.0       # camera notch in the top centre of the ledge (review notes)
FRONT_SCREW_XZ = ((-40.0, 248.0), (40.0, 248.0))   # 2x M2 from behind (H11 -> H03), review notes
FRONT_SCREW_R = 2.8      # boss radius (stays 0.1 above the display outline)
FRONT_HOOK_X = (-36.0, 36.0)   # 2 bottom hooks of the front module into H11
EAR_HOLE_D = 36.4        # shell hole for the Ø36 ear (0.2 radial clearance)
EAR_SPIGOT_R = 16.5      # ear spigot radius (passes the H01 shoulder ring)
EAR_X_STEP = W / 2 - WALL  # 63.8 – ear step / H01 shoulder plane (inner wall surface)
EAR_X_RING_IN = 62.0     # inner face of the H01 shoulder ring (snap hooks catch here)
EAR_X_IN = 60.6          # inner end of the ear spigot
EAR_DOME = 0.8           # sag of the domed ear face
EAR_FILLET = 2.5         # ear outer edge fillet
EAR_CUP_R = 15.5         # ear PCB cup (H07 ring OD 29 fits)
EAR_CUP_X1 = 68.0        # cup ceiling
RING_PROUD = 0.2         # LED ring stands 0.2 mm proud of the ear face
RING_DEPTH = 2.2         # groove depth (measured at the ring ID)
POCKET_WALL = 2.0        # closed neck pocket wall
POCKET_RIM_R = 1.0       # round on the recess opening edge
LIP_T = 1.2              # H02 locating lip thickness
LIP_IN = 3.2             # H02 lip outer face inset from the cover outline
LIP_Y = 32.0             # H02 lip free edge (flat, y)
LEDGE_BACK_IN = 3.0      # H01 back ledge reaches 3.0 inside the cover outline (H02 edge rests on it)
LEDGE_BACK_OUT = 4.0     # ... and 4 mm outside the seam (bonded to the H01 wall)
LEDGE_BACK_T = 1.5       # back ledge thickness
H02_SCREW_XY = (0.0, 36.0)   # 1x M2 from below into H02 (review notes)
H02_HOOKS = (("top", -30.0), ("top", 30.0), ("right", None), ("left", None))   # 4 hooks
H11_BOSSES = ((40.0, 12.0, "roof"), (-40.0, 12.0, "roof"), (44.0, 12.0, "floor"), (-44.0, 12.0, "floor"))
BOSS_R = 3.5             # H11 screw boss radius (M2.5 thread-forming)
BOSS_HOLE_R = 1.1        # pilot hole Ø2.2
BOSS_H = 12.0            # boss height measured from the outer skin (9.8 above the inner wall)
RIB_T = 1.2              # boss rib thickness (~0.55 x wall: no sink marks on the visible skin)


# ===========================================================================================
# helpers
# ===========================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    """Plane at y whose normal is +Y (local u = +X, local v = -Z), centred at (cx, cz)."""
    return Plane(origin=(cx, y, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=ZC):
    """Rounded rectangle w (X) x h (Z) radius r, extruded along +Y from y0 to y1."""
    with BuildSketch(plane_y(y0, cx, cz)) as sk:
        RectangleRounded(w, h, r)
    return extrude(sk.sketch, y1 - y0)


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    """Rounded rectangle w (X) x d (Y) radius r, extruded along +Z from z0 to z1."""
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        with Locations((cx, cy)):
            RectangleRounded(w, d, r)
    return extrude(sk.sketch, z1 - z0)


def box(x0, x1, y0, y1, z0, z1):
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


def tube_x(ro, ri, x0, x1, y, z):
    return cyl_x(ro, x0, x1, y, z) - cyl_x(ri, min(x0, x1) - 1, max(x0, x1) + 1, y, z)


def wedge_y(ya, yb, t, width):
    """Snap wedge in a canonical frame: base on z=0 (sunk 0.3 for a clean union), grows toward +Z,
    catch face at y=ya (full height t), ramp down to zero at y=yb, centred on x=0, width along X."""
    pts = [(ya, -0.3), (ya, t), (yb, 0.0), (yb, -0.3)]
    w2 = width / 2
    face = Face(Wire.make_polygon([Vector(-w2, y, z) for y, z in pts], close=True))
    return Solid.extrude(face, Vector(width, 0, 0))


def on_frame(shape, side, along, level):
    """Place a canonical wedge (grows +Z) on a rounded-rect frame lying in XZ.
    'top' / 'bottom' -> along = x, level = z of the base surface (wedge grows +Z / -Z);
    'right' (+X) / 'left' (-X) -> along = z, level = x of the base surface (grows +X / -X)."""
    if side == "top":
        return Pos(along, 0, level) * shape
    if side == "bottom":
        return Pos(along, 0, level) * Rot(0, 180, 0) * shape
    if side == "right":
        return Pos(level, 0, along) * Rot(0, 90, 0) * shape
    return Pos(level, 0, along) * Rot(0, -90, 0) * shape


def retry(fn, label, tries=4):
    """build123d runs OCC booleans with SetRunParallel(True) – rare non-deterministic failures of
    complex cuts are retried instead of breaking the build."""
    err = None
    for _ in range(tries):
        try:
            out = fn()
            if out is not None and out.is_valid and out.volume > 0:
                return out
        except Exception as ex:  # pragma: no cover
            err = ex
    raise RuntimeError(f"{label}: boolean failed {tries}x ({err})")


def check(name, s, vmin=None):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    if vmin is not None and s.volume < vmin:
        raise RuntimeError(f"{name}: volume {s.volume:.0f} < {vmin}")
    return s


def step_safe(name, s):
    """Replace OffsetSurface faces (left by offset() on the B-spline corner blends of the back R28 loop)
    with exact B-spline surfaces.  STEPControl_Writer heals such faces IN PLACE: without this the in-memory
    H01/H02 turned invalid during export_step and the written STEP re-imported as an invalid solid with
    a wrong volume (H01 152700 mm3 instead of 88429)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_OffsetSurface
    from OCP.ShapeCustom import ShapeCustom
    from OCP.ShapeFix import ShapeFix_Shape
    from build123d import Shape

    def n_offset(sh):
        return sum(1 for f in sh.faces() if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_OffsetSurface)

    if n_offset(s) == 0:
        return s
    conv = ShapeCustom.ConvertToBSpline_s(s.wrapped, False, False, True, False)   # offset surfaces only
    fx = ShapeFix_Shape(conv)
    fx.Perform()
    sols = Shape.cast(fx.Shape()).solids()
    if len(sols) != len(s.solids()):
        raise RuntimeError(f"{name}: B-spline conversion changed the solid count")
    out = sols[0] if len(sols) == 1 else Compound(list(sols))
    if not out.is_valid or n_offset(out) or abs(out.volume - s.volume) > 1e-4 * s.volume:
        raise RuntimeError(f"{name}: B-spline conversion failed ({out.volume:.1f} vs {s.volume:.1f})")
    return out


def rr_dist(x, z, w, h, r, cx=0.0, cz=ZC):
    """Signed distance of (x, z) to a rounded rectangle w x h radius r (negative = inside)."""
    qx = abs(x - cx) - (w / 2 - r)
    qz = abs(z - cz) - (h / 2 - r)
    out = math.hypot(max(qx, 0.0), max(qz, 0.0))
    return out + min(max(qx, qz), 0.0) - r


def edges_on_rr(shape, y, w, h, r, cz=ZC, tol=0.02):
    """Edges lying in the plane y on the outline of a rounded rectangle (XZ)."""
    out = []
    for e in shape.edges():
        pts = [e.position_at(t) for t in (0.0, 0.5, 1.0)]
        if all(abs(p.Y - y) < tol and abs(rr_dist(p.X, p.Z, w, h, r, 0.0, cz)) < tol for p in pts):
            out.append(e)
    return ShapeList(out)


def outer_seam_edges(shape, skin, w, h, r, tol=0.03):
    """Edges of 'shape' on the projected (// Y) rounded-rect outline w x h r that lie on the outer skin."""
    out = []
    for e in shape.edges():
        pts = [e.position_at(t) for t in (0.1, 0.5, 0.9)]
        if not all(abs(rr_dist(p.X, p.Z, w, h, r)) < tol and p.Y > 15 for p in pts):
            continue
        if all(skin.distance_to(Vector(p.X, p.Y, p.Z)) < tol for p in pts):
            out.append(e)
    return ShapeList(out)


def try_chamfer(shape, edges, d, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = chamfer(edges, d)
        if out.is_valid and abs(out.volume - shape.volume) < 0.02 * shape.volume:
            return out
        print(f"  ({label}: chamfer result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: chamfer {d} skipped: {ex})")
    return shape


def try_fillet(shape, edges, r, label):
    if not edges:
        return shape
    try:
        out = fillet(edges, r)
        if out.is_valid:
            return out
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: fillet R{r} skipped: {ex})")
    return shape


# ===========================================================================================
# H01 / H02 – white shells
# ===========================================================================================

def head_body(front_fillet=True):
    body = rr_prism_y(W, HH, H["r_front_view"], Y0, Y1)                     # silhouette R32 // Y
    body = fillet(body.edges().group_by(Axis.Y)[-1], H["r_back"])          # back loop R28
    if front_fillet:
        body = fillet(body.edges().group_by(Axis.Y)[0], H["r_front_rim"])  # front rim R2
    return body


def ledge_inner_y(x, z, ledge):
    """y of the front-most (inner) face of the back ledge along a ray // Y at (x, z)."""
    pts = ledge.find_intersection_points(Axis((x, -10.0, z), (0, 1, 0)))
    ys = [p[0].Y if isinstance(p, tuple) else p.Y for p in pts]
    ys = [y for y in ys if y > 20]
    return min(ys)


def shells():
    body = head_body(True)
    body_nf = head_body(False)
    inner = offset(body, amount=-WALL)
    assert inner.volume < body.volume * 0.95, "offset failed"
    shell = check("shell", body - inner)

    # ---------------- H02: back cover = shell inside the projected rounded rectangle ----------
    yb = 10.0                                           # projection prisms start well behind the front
    cover_zone = rr_prism_y(BC["w"], BC["h"], BC["r"], yb, Y1 + 5)
    h02 = shell & cover_zone

    # ---------------- H01: main shell --------------------------------------------------------
    h01 = shell - rr_prism_y(BC["w"] + 2 * SEAM, BC["h"] + 2 * SEAM, BC["r"] + SEAM, yb, Y1 + 5)
    # front opening = bezel outline + uniform 0.3 gap (= inner wall outline, white rim 2.2 + gap 0.3)
    ow_, oh_, or_ = BZ["w"] + 2 * FRONT_GAP, BZ["h"] + 2 * FRONT_GAP, BZ["r"] + FRONT_GAP
    h01 = retry(lambda: h01 - rr_prism_y(ow_, oh_, or_, Y0 - 2, Y0 + WALL + 0.8), "front opening")

    # back ledge band under the H02 edge (also the floor of the 0.6 mm seam -> no see-through)
    slab = box(-W, W, yb - 2, Y1 + 5, Z0 - 5, Z1 + 5)                 # back region only (robust boolean)
    inner2 = offset(body_nf, amount=-(WALL + LEDGE_BACK_T))
    band = retry(lambda: (inner & slab) - (inner2 & slab), "ledge band")
    ow, oh, orr = (BC["w"] + 2 * (SEAM + LEDGE_BACK_OUT), BC["h"] + 2 * (SEAM + LEDGE_BACK_OUT),
                   BC["r"] + SEAM + LEDGE_BACK_OUT)
    iw, ih, ir = BC["w"] - 2 * LEDGE_BACK_IN, BC["h"] - 2 * LEDGE_BACK_IN, BC["r"] - LEDGE_BACK_IN
    ring = rr_prism_y(ow, oh, orr, yb, Y1 + 5) - rr_prism_y(iw, ih, ir, yb - 1, Y1 + 6)
    ledge = band & ring
    h01 = h01 + ledge

    # closed neck pocket: opening 56x56 R16 in the floor, 2 mm walls, ceiling at z0 + depth
    pz1 = Z0 + NR["depth"]                                             # 204
    pocket_out = rr_prism_z(NR["w"] + 2 * POCKET_WALL, NR["d"] + 2 * POCKET_WALL, NR["r"] + POCKET_WALL,
                            Z0 - 1, pz1 + POCKET_WALL, cy=TILT_Y)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 4.0)
    pocket_in = rr_prism_z(NR["w"], NR["d"], NR["r"], Z0 - 5, pz1, cy=TILT_Y)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 2.0)
    h01 = h01 + (pocket_out & body)
    h01 = h01 - pocket_in
    e_pk = [e for e in h01.edges()
            if e.bounding_box().max.Z < Z0 + 4.0
            and all(abs(rr_dist_xy(p.X, p.Y)) < 0.02 for p in (e.position_at(0), e.position_at(0.5), e.position_at(1)))]
    h01 = try_fillet(h01, ShapeList(e_pk), POCKET_RIM_R, "H01 pocket rim")
    # N07 hub passages: Ø18.4 at the tilt axis, opened to the bottom as a U-slot so that H01 can be
    # lowered vertically over the barrel with the caps + hubs already mounted (review notes, step 2)
    hr = NR["hub_hole_d"] / 2
    xw = NR["w"] / 2
    for sx in (-1, 1):
        x0_, x1_ = sx * (xw - 1.0), sx * (xw + POCKET_WALL + 1.0)
        h01 = h01 - cyl_x(hr, x0_, x1_, TILT_Y, TILT_Z)
        h01 = h01 - box(x0_, x1_, TILT_Y - hr, TILT_Y + hr, Z0 - 2, TILT_Z)

    # ear seats: Ø36.4 hole through the wall + inner shoulder ring (ear step rests on x = 63.8)
    e_y, e_z = EAR["y"], EAR["z"]
    for sx in (-1, 1):
        h01 = h01 + (tube_x(21.0, EAR_SPIGOT_R + 0.2, sx * EAR_X_RING_IN, sx * (EAR_X_STEP + 0.6), e_y, e_z) & body)
        h01 = h01 - cyl_x(EAR_HOLE_D / 2, sx * EAR_X_STEP, sx * (W / 2 + 3), e_y, e_z)
        h01 = h01 - cyl_x(EAR_SPIGOT_R + 0.2, sx * (EAR_X_RING_IN - 1), sx * (EAR_X_STEP + 0.01), e_y, e_z)

    # 4 screw bosses for the inner frame H11 (H01 -> H11 4x M2.5): 2 from the roof, 2 on the floor
    # Each boss is tied to the back wall by a 1.2 mm rib along +Y: it braces the 10 mm boss and removes the
    # undercut behind it for the core that is pulled forward (-Y) out of the front opening (review notes).
    # The rib stays 1 mm short of the boss face, so H11 seats on the bosses only; the roof ribs (z >= Z1-11)
    # and floor ribs (z <= Z0+11) stay clear of the H02 zone (z 183.4..250.6) and only merge into the ledge.
    for (x, y, where) in H11_BOSSES:
        if where == "roof":
            h01 = h01 + (cyl_z(BOSS_R, Z1 - BOSS_H, Z1, x, y) & body)
            h01 = h01 + (box(x - RIB_T / 2, x + RIB_T / 2, y, Y1 + 1, Z1 - BOSS_H + 1.0, Z1) & body)
            h01 = h01 - cyl_z(BOSS_HOLE_R, Z1 - BOSS_H - 0.5, Z1 - WALL - 1.0, x, y)
        else:
            h01 = h01 + (cyl_z(BOSS_R, Z0, Z0 + BOSS_H, x, y) & body)
            h01 = h01 + (box(x - RIB_T / 2, x + RIB_T / 2, y, Y1 + 1, Z0, Z0 + BOSS_H - 1.0) & body)
            h01 = h01 - cyl_z(BOSS_HOLE_R, Z0 + 6.0, Z0 + BOSS_H + 0.5, x, y)

    # 2 groups of 3 vent slots in the floor, front (long axis // X, pitch along Y)
    h01 = h01 - vent_cutter(Z0 - 3, Z0 + WALL + 2)

    # H02 retaining screw: M2 from below at (0, +36) through the H01 wall + ledge (counterbored)
    sx_, sy_ = H02_SCREW_XY
    z_top_ledge = H02_SCREW_Z0 - 0.5
    h01 = h01 - cyl_z(1.2, Z0 - 1, z_top_ledge + 1.0, sx_, sy_)
    h01 = h01 - cyl_z(2.2, Z0 - 1, outer_z_at(sy_) + 0.6, sx_, sy_)

    # small round on the inner edge of the front rim (the outer edge is the R2 rim)
    e_open = edges_on_rr(h01, Y0, ow_, oh_, or_)
    h01 = try_fillet(h01, e_open, 0.15, "H01 opening")
    # 0.3 x 45 deg break on the visible edges of the 0.6 mm back-cover seam (review notes)
    skin = Compound(body.faces())
    h01 = try_chamfer(h01, outer_seam_edges(h01, skin, BC["w"] + 2 * SEAM, BC["h"] + 2 * SEAM, BC["r"] + SEAM),
                      SEAM_BREAK, "H01 seam")
    h01 = check("H01", h01, vmin=60000)

    # ---------------- H02 lip + snap hooks + screw boss -----------------------------------------
    lw_o, lh_o, lr_o = BC["w"] - 2 * LIP_IN, BC["h"] - 2 * LIP_IN, BC["r"] - LIP_IN
    lip_ring = (rr_prism_y(lw_o, lh_o, lr_o, LIP_Y, Y1 + 5)
                - rr_prism_y(lw_o - 2 * LIP_T, lh_o - 2 * LIP_T, lr_o - LIP_T, LIP_Y - 1, Y1 + 6))
    h02 = h02 + (lip_ring & inner)
    # hooks: catch face sits just in front of the ledge's inner face (measured on the real ledge)
    for side, along in H02_HOOKS:
        along = ZC if along is None else along
        # sample the ledge over the hook footprint (hook top 0.6 out, +-4.5 along) – the face is inclined
        if side in ("top", "bottom"):
            lvl = ZC + (lh_o / 2 if side == "top" else -lh_o / 2)
            sg = 1 if side == "top" else -1
            yl = min(ledge_inner_y(along + da, lvl + sg * dr, ledge) for da in (-4.5, 0, 4.5) for dr in (0.25, 0.7))
        else:
            lvl = lw_o / 2 if side == "right" else -lw_o / 2
            sg = 1 if side == "right" else -1
            yl = min(ledge_inner_y(lvl + sg * dr, along + da, ledge) for da in (-4.5, 0, 4.5) for dr in (0.25, 0.7))
        yc = yl - 0.1
        hk = wedge_y(yc, max(LIP_Y + 0.2, yc - 2.4), 0.6, 9.0)
        h02 = h02 + on_frame(hk, side, along, lvl)
    # screw boss standing on the bottom lip, above the ledge footprint (H02 still pulls off in +Y)
    boss = box(sx_ - 3.0, sx_ + 3.0, sy_ - 3.0, Y1, H02_SCREW_Z0, H02_SCREW_Z0 + 6.5) & inner
    boss = boss - cyl_z(0.8, H02_SCREW_Z0 - 1, H02_SCREW_Z0 + 5.0, sx_, sy_)
    h02 = h02 + boss
    h02 = try_chamfer(h02, outer_seam_edges(h02, skin, BC["w"], BC["h"], BC["r"]), SEAM_BREAK, "H02 seam")
    h02 = check("H02", h02, vmin=8000)
    return step_safe("H01", h01), step_safe("H02", h02)


H02_SCREW_Z0 = ZC - BC["h"] / 2 + LIP_IN       # 187.2 – underside of the bottom lip (above the ledge footprint)


def outer_z_at(y):
    """z of the H01 outer surface on the back-bottom R28 rounding at x = 0 (y beyond the flat floor)."""
    yc_ = Y1 - H["r_back"]
    zc_ = Z0 + H["r_back"]
    dy = max(0.0, y - yc_)
    return zc_ - math.sqrt(max(0.0, H["r_back"] ** 2 - dy * dy))


def rr_dist_xy(x, y):
    """Signed distance to the neck-recess outline (56x56 R16 in XY, centred on the tilt axis)."""
    qx = abs(x) - (NR["w"] / 2 - NR["r"])
    qy = abs(y - TILT_Y) - (NR["d"] / 2 - NR["r"])
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - NR["r"]


def vent_cutter(z0, z1):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        for xc in VT["x"]:
            for i in range(VT["n"]):
                y = VT["y"] + (i - (VT["n"] - 1) / 2) * VT["pitch"]
                with Locations((xc, y)):
                    SlotOverall(VT["w"], VT["h"])
    return extrude(sk.sketch, z1 - z0)


Y_SKIRT_END = Y_SKIRT_BACK - SKIRT_END_CLR          # -30.5


# ===========================================================================================
# H03 – black front frame, H04 glass, H04C camera window, H04E eyes
# ===========================================================================================

def bezel():
    bw, bh, br = BZ["w"], BZ["h"], BZ["r"]
    b = rr_prism_y(bw, bh, br, Y_BEZEL_FRONT, Y_SKIRT_END)                  # frame + skirt, one outline
    b = fillet(b.edges().group_by(Axis.Y)[0], BZ["front_fillet"])          # R3 front edge
    # glass seat (recessed), support ledge (behind 0.2 PSA), hollow skirt
    gw, gh, gr = GL["w"] + 2 * GLASS_CLR, GL["h"] + 2 * GLASS_CLR, GL["r"] + GLASS_CLR
    y_ledge0 = Y_GLASS_BACK + PSA_T                                         # -50.7
    y_ledge1 = y_ledge0 + LEDGE_T                                           # -49.1
    b = b - rr_prism_y(gw, gh, gr, Y_BEZEL_FRONT - 1, y_ledge0, cz=GZ)
    b = b - rr_prism_y(GL["w"] - 2 * LEDGE_W, GL["h"] - 2 * LEDGE_W, GL["r"] - LEDGE_W,
                       y_ledge0 - 0.5, y_ledge1 + 0.01, cz=GZ)
    siw, sih, sir = bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL
    b = b - rr_prism_y(siw, sih, sir, y_ledge1, Y_SKIRT_END + 1)
    # crisp 0.4 round on the visible inner front edge (glass seat)
    e_in = edges_on_rr(b, Y_BEZEL_FRONT, gw, gh, gr, cz=GZ)
    b = try_fillet(b, e_in, 0.4, "H03 inner edge")
    # 11 mm camera notch in the top centre of the ledge (module pressed onto the glass by H12)
    z_seat_top = GZ + gh / 2
    b = b - box(-CAM_NOTCH_W / 2, CAM_NOTCH_W / 2, y_ledge0 - 0.01, y_ledge1 + 0.01,
                z_seat_top - LEDGE_W - 0.5, z_seat_top + 0.01)
    # vents: skirt floor gets the same slot pattern as the H01 floor (air path to the display)
    b = b - vent_cutter(ZC - bh / 2 - 1, ZC - sih / 2 + 0.6)
    # 2x M2 bosses (screws from behind through H11 / the H02 opening), tied into the skirt roof
    y_dsp_back = y_ledge1 + 0.5 + DSP["outline"][2]                         # display back plane (H11 front)
    for (x, z) in FRONT_SCREW_XZ:
        col = cyl_y(FRONT_SCREW_R, y_ledge1 - 0.3, y_dsp_back, x, z)
        col = col + box(x - FRONT_SCREW_R, x + FRONT_SCREW_R, y_ledge1 - 0.3, y_dsp_back, z, ZC + sih / 2 + 0.5)
        b = b + col
        b = b - cyl_y(0.8, y_dsp_back - 4.5, y_dsp_back + 1, x, z)
    # display envelope (+0.3): at zc 211.5 the square lower corners of the 105.5 x 67.2 module come within
    # 0.05 mm of the H01 inner wall (R29.8) – the skirt is notched locally there (reported spec issue)
    # (the notch never opens the visible outer skin: a 0.6 mm minimum wall is kept at the corners)
    dw, dh = DSP["outline"][0] / 2 + 0.3, DSP["outline"][1] / 2 + 0.3
    keep_in = rr_prism_y(bw - 2 * SKIRT_MIN_WALL, bh - 2 * SKIRT_MIN_WALL, br - SKIRT_MIN_WALL,
                         y_ledge1, y_dsp_back + 1.0)
    b = b - (box(-dw, dw, y_ledge1 + 0.2, y_dsp_back + 0.3, DSP["zc"] - dh, DSP["zc"] + dh) & keep_in)
    # 2 bottom hooks into H11 (tabs standing on the skirt floor behind the display, nose toward +Y)
    z_floor = ZC - sih / 2
    for x in FRONT_HOOK_X:
        ya, yb_ = y_dsp_back + 0.3, y_dsp_back + 1.8
        tab = box(x - 4.0, x + 4.0, ya, yb_, z_floor - 0.5, z_floor + 6.0)
        nose = Pos(x, 0, 0) * Solid.extrude(
            Face(Wire.make_polygon([Vector(-4.0, yb_ - 0.2, z_floor + 3.8), Vector(-4.0, yb_ + 1.2, z_floor + 4.8),
                                    Vector(-4.0, yb_ + 1.2, z_floor + 6.0), Vector(-4.0, yb_ - 0.2, z_floor + 6.0)],
                                   close=True)), Vector(8.0, 0, 0))
        b = b + tab + nose
    return check("H03", b, vmin=10000)


def glass():
    g = rr_prism_y(GL["w"], GL["h"], GL["r"], Y_GLASS_FRONT, Y_GLASS_BACK, cz=GZ)
    g = try_fillet(g, g.edges().group_by(Axis.Y)[0], 0.3, "H04 C-cut")
    return check("H04", g)


def camera_window():
    t = 0.1
    w = cyl_y(CAM["hole_d"] / 2, Y_GLASS_FRONT - t, Y_GLASS_FRONT, 0.0, CAM["z"])
    return check("H04C", w)


def eyes():
    t = 0.15
    out = None
    for sx in (-1, 1):
        with BuildSketch(plane_y(Y_GLASS_FRONT - t, sx * EYE["x"], EYE["z"])) as sk:
            SlotOverall(EYE["h"], EYE["w"], rotation=90)     # R = w/2 = 6.5 (stadium)
        e = extrude(sk.sketch, t)
        out = e if out is None else out + e
    return check("H04E", out)


# ===========================================================================================
# H05 ears + H06 LED rings (built for the LEFT ear, +X, in a local frame on the ear axis)
# ===========================================================================================

EAR_RS = ((EAR["d"] / 2) ** 2 + EAR_DOME ** 2) / (2 * EAR_DOME)      # dome sphere radius (~203)
EAR_SC = X_EAR_OUT - EAR_RS                                           # dome sphere centre on the ear axis


def dome_x(r, extra=0.0):
    """x of the ear dome (offset by 'extra' along the sphere radius) at radius r."""
    rr = EAR_RS + extra
    return EAR_SC + math.sqrt(rr * rr - r * r)


def dome_pt(r, extra=0.0):
    return (dome_x(r, extra), r)


def revolve_x(segs, start):
    """Closed (x, r) profile -> solid revolved 360 deg about the ear axis (local X axis).
    segs: ("L", (x, r)) line to point, ("A", (x, r) mid, (x, r) end) three-point arc."""
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
    face = Face(Wire(edges))
    return Solid.revolve(face, 360, Axis.X)


def dome_arc(r0, r1, extra=0.0):
    """Three-point arc segment along the dome from radius r0 to r1."""
    rm = (r0 + r1) / 2
    return ("A", dome_pt(rm, extra), dome_pt(r1, extra))


def ear_left():
    R = EAR["d"] / 2
    ro, ri = EAR["ring_od"] / 2, EAR["ring_id"] / 2
    g_o, g_i = ro + 0.1, ri - 0.1                                    # groove (0.1 clearance round the ring)
    ring_bot = dome_x(ri) - RING_DEPTH
    rmic = EAR["mic_hole_d"] / 2
    # R2.5 fillet between the Ø36 cylinder and the dome (exact tangent construction)
    f = EAR_FILLET
    fc_r = R - f
    fc_x = EAR_SC + math.sqrt((EAR_RS - f) ** 2 - fc_r ** 2)
    k = EAR_RS / (EAR_RS - f)
    t_dome = (EAR_SC + (fc_x - EAR_SC) * k, fc_r * k)               # tangent point on the dome
    t_cyl = (fc_x, R)                                                # tangent point on the cylinder
    a_mid = math.atan2(t_dome[1] - fc_r, t_dome[0] - fc_x) / 2 + math.pi / 4   # mid angle of the fillet arc
    f_mid = (fc_x + f * math.cos(a_mid), fc_r + f * math.sin(a_mid))
    ch = 0.4
    segs = [
        ("L", (EAR_X_IN, EAR_SPIGOT_R)),                             # spigot open end
        ("L", (EAR_X_STEP, EAR_SPIGOT_R)),                           # spigot -> step
        ("L", (EAR_X_STEP, R - ch)),
        ("L", (EAR_X_STEP + ch, R)),                                 # 0.4 chamfer on the step
        ("L", t_cyl),                                                # Ø36 cylinder
        ("A", f_mid, t_dome),                                        # R2.5 edge fillet
        dome_arc(t_dome[1], g_o),                                    # outer black land
        ("L", (ring_bot, g_o)),                                      # groove outer wall
        ("L", (ring_bot, g_i)),                                      # groove floor
        ("L", dome_pt(g_i)),                                         # groove inner wall
        dome_arc(g_i, rmic),                                         # centre dome
        ("L", (EAR_CUP_X1, rmic)),                                   # Ø1 microphone hole
        ("L", (EAR_CUP_X1, EAR_CUP_R)),                              # cup ceiling
    ]
    disc = revolve_x(segs, (EAR_X_IN, EAR_CUP_R))
    # 6 light windows from the cup into the groove
    rm = (ro + ri) / 2
    for kk in range(6):
        a = math.radians(30 + 60 * kk)
        disc = disc - cyl_x(0.8, EAR_CUP_X1 - 0.5, ring_bot + 0.1, rm * math.cos(a), rm * math.sin(a))
    # 3 snap hooks on the spigot: pass the Ø33.4 shoulder ring, catch behind its inner face (x = 62)
    xc = EAR_X_RING_IN - 0.05
    for kk in range(3):
        hk = wedge_y(xc, EAR_X_IN + 0.1, 0.7, 6.0)                  # canonical: along +Y = ear axis
        hk = Rot(0, 0, -90) * hk                                     # canonical Y -> +X
        hk = Pos(0, 0, EAR_SPIGOT_R - 0.05) * hk
        disc = disc + Rot(120 * kk + 90, 0, 0) * hk
    # H06 light-guide ring: sits on the groove floor, top follows the dome 0.2 proud, 0.15 edge breaks
    e = 0.15
    rsegs = [
        ("L", (ring_bot, ro)),
        ("L", (dome_x(ro, RING_PROUD) - e, ro)),
        ("L", dome_pt(ro - e, RING_PROUD)),
        dome_arc(ro - e, ri + e, RING_PROUD),
        ("L", (dome_x(ri, RING_PROUD) - e, ri)),
    ]
    ring = revolve_x(rsegs, (ring_bot, ri))
    ey, ez = EAR["y"], EAR["z"]
    return check("H05", Pos(0, ey, ez) * disc, vmin=3000), check("H06", Pos(0, ey, ez) * ring, vmin=300)


# ===========================================================================================

def build():
    h01, h02 = shells()
    ear_l, ring_l = ear_left()
    ear_r = mirror(ear_l, Plane.YZ)
    ring_r = mirror(ring_l, Plane.YZ)
    up = 150.0
    fy = 45.0
    ex = 40.0
    recs = [
        PartRec("H01", "Hlavný obal hlavy", h01, "white", "head", "J3", (0, 0, up),
                note="PC/ABS 2.2 mm, biely lem 2.2 + škára 0.3, uzavreté vybranie krku 56×56 R16 hĺ. 35, priechody Ø18.4 pre náboje N07, 2×3 vetracie štrbiny, 4 nálitky M2.5 pre H11 s rebrami k zadnej stene"),
        PartRec("H02", "Zadný kryt hlavy", h02, "white", "head", "J3", (0, fy, up),
                note="servisný kryt 112×66 R20, škára 0.6, lícovací lem 1.2, 4 háčiky + 1× M2 zdola pri (0, +36)"),
        PartRec("H03", "Predný rám", bezel(), "black", "head", "J3", (0, -fy, up),
                note="čierny soft-touch 127×91 R29.5, vystupuje 7 mm, osadenie skla 3 mm s výrezom 11 mm pre kameru, 2 háčiky + 2× M2 (±40, z 248) do H11"),
        PartRec("H04", "Sklo displeja", glass(), "glass", "head", "J3", (0, -fy, up),
                note="tvrdené sklo 119×79 R22 × 1.1, čierna potlač hore 9 mm / inde 4 mm, lepené PSA 0.2 mm"),
        PartRec("H04C", "Okienko kamery", camera_window(), "black_gloss", "head", "J3", (0, -fy, up),
                note="len objekt pre render (nie je diel): nepotlačené okienko Ø3.2 v potlači skla H04"),
        PartRec("H04E", "Obsah displeja – oči", eyes(), "eye", "head", "J3", (0, -fy, up),
                note="len objekt pre render (nie je diel): obsah displeja – dve teplé pilulky 13×21.5 R6.5"),
        PartRec("H05-R", "Ucho pravé", ear_r, "black", "head", "J3", (-ex, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1), zacvaknuté 3 zámkami"),
        PartRec("H05-L", "Ucho ľavé", ear_l, "black", "head", "J3", (ex, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1), zacvaknuté 3 zámkami"),
        PartRec("H06-R", "LED krúžok ucha pravý", ring_r, "cyan_led", "head", "J3", (-ex, 0, up),
                note="PMMA opál Ø30/Ø23, 12× LED"),
        PartRec("H06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", "head", "J3", (ex, 0, up),
                note="PMMA opál Ø30/Ø23, 12× LED"),
    ]
    for r in recs:                       # every exported solid must survive the STEP round trip
        r.shape = step_safe(r.id, r.shape)
    return recs


if __name__ == "__main__":
    run_module(build, "head")
