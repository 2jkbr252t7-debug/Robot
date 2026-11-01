"""
NOVA – HEAD (H01..H06).  Run:  /opt/venv/cad/bin/python -m nova.cad.head

All parts are built in final assembly position (joint J3 = head tilt about the X axis through
spec.TILT_AXIS).  Every shared number comes from spec.HEAD / spec.NECK / spec.TILT_AXIS (v7.2);
the named constants below are purely local construction values (clearances, rib / snap sizes).

Parts
  H01      Hlavný obal hlavy        white      rounded box shell 132 x 90 x 96, 2.5 mm white rim,
                                               closed neck pocket, ear seats, vents, latches, bosses
  H02      Zadný kryt hlavy         white      back cover 112x66 R20 projected on the rear surface,
                                               0.6 mm seam, 1.2 mm locating lip + 6 snap hooks
  H03      Predný rám               black      frame 127x91 R30 protruding 7 mm, glass seat, ledge,
                                               skirt with latch windows, display bosses, camera cradle
  H04      Sklo displeja            glass      119x79 R22 x 1.1 cover glass (one piece)
  H04C     Okienko kamery           black_gloss  Ø3.2 lens window disc 0.1 mm proud of the glass
  H04E     Obsah displeja – oči     eye        two warm pill eyes lying on the glass
  H05-R/L  Ucho pravé / ľavé        black      Ø36 domed ear discs (touch + mic), snap-in
  H06-R/L  LED krúžok ucha          cyan_led   Ø30/Ø23 light-guide rings
"""
from __future__ import annotations

import math

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Edge, Face, GeomType, Locations, Plane, Pos, ShapeList,
                       RectangleRounded, Rot, SlotOverall, Solid, Sphere, Vector, Wire, extrude, fillet,
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
CAPS = spec.NECK["caps"]
BARREL_LEN = spec.NECK["tilt_housing"]["barrel_len"]

# ---- derived levels -----------------------------------------------------------------------
Y_BEZEL_FRONT = Y0 - BZ["protrude"]                  # -53
Y_GLASS_FRONT = Y_BEZEL_FRONT + GL["recess"]         # -52
Y_GLASS_BACK = Y_GLASS_FRONT + GL["t"]               # -50.9
Y_SKIRT_BACK = Y0 + BZ["depth"]                      # -30  (skirt reaches 16 mm behind the rim plane)
GZ = GL["zc"]                                        # glass centre z 216
X_EAR_OUT = W / 2 + EAR["protrude"]                  # 71.5 (dome apex)
X_CAP_OUT = BARREL_LEN / 2 + CAPS["gap"] + CAPS["len"]   # 24.6 – outer face (dome apex) of the N07 caps

# ---- local construction constants (not shared dimensions) ---------------------------------
SEAM = BC["seam"]        # 0.6
SKIRT_CLR = 0.2          # bezel skirt <-> white front opening (radial)
SKIRT_WALL = 2.0         # bezel skirt wall
SKIRT_END_CLR = 0.5      # skirt end stays 0.5 in front of the neck-pocket front wall (y = -30)
GLASS_CLR = 0.15         # glass <-> bezel seat clearance (per side)
LEDGE_W = 3.0            # glass support ledge width (hidden behind the 4 mm black print)
LEDGE_T = 1.6            # glass support ledge thickness (display front rests on its back face)
EAR_HOLE_D = 36.4        # shell hole for the Ø36 ear (0.2 radial clearance)
EAR_SPIGOT_R = 16.5      # ear spigot radius (passes the H01 shoulder ring)
EAR_X_STEP = W / 2 - WALL  # 63.8 – ear step / H01 shoulder plane (inner wall surface)
EAR_X_RING_IN = 62.0     # inner face of the H01 shoulder ring (snap hooks catch here)
EAR_X_IN = 60.6          # inner end of the ear spigot
EAR_DOME = 0.8           # sag of the domed ear face
EAR_FILLET = 2.5         # ear outer edge fillet
EAR_CUP_R = 15.5         # ear PCB cup
EAR_CUP_X1 = 68.0        # cup ceiling
RING_PROUD = 0.2         # LED ring stands 0.2 mm proud of the ear face
RING_DEPTH = 2.2         # groove depth (measured at the ring ID)
POCKET_WALL = 2.0        # closed neck pocket wall
HUB_GAP = 0.1            # head hub boss face <-> N07 cap apex
HUB_R_SERVO = 7.0        # -X hub boss radius (servo side)
HUB_R_PASSIVE = 10.5     # +X hub boss radius (passive side, cable passage) – stays 1.5 above the opening
HUB_SCREW_R = 8.6        # +X hub M2 screws at y = +-8.6
CABLE_BORE_D = 13.0      # = ID of the hollow pin in the 6703 bearing (spec CHANGELOG v7.1)
LIP_T = 1.2              # H02 locating lip thickness
LIP_IN = 3.2             # H02 lip outer face inset from the cover outline
LIP_Y = 32.0             # H02 lip free edge (flat, y)
LEDGE_BACK_IN = 3.0      # H01 back ledge reaches 3.0 inside the cover outline (H02 edge rests on it)
LEDGE_BACK_OUT = 4.0     # ... and 4 mm outside the seam (bonded to the H01 wall)
LEDGE_BACK_T = 1.5       # back ledge thickness
LATCH_H = 0.9            # H01 latch height (engages 0.4 mm into the bezel skirt window)
CAM_CRADLE_T = 1.0       # camera cradle rib thickness
DISPLAY_BOSS_DZ = 13.0   # display bosses at display zc +- 13 (inside the straight part of the skirt)


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


def circles(edges):
    return ShapeList([e for e in edges if e.geom_type == GeomType.CIRCLE])


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
    # front opening = bezel outline (2.5 mm white rim all round)
    h01 = h01 - rr_prism_y(BZ["w"], BZ["h"], BZ["r"], Y0 - 2, Y0 + WALL + 2)

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
    pz1 = Z0 + NR["depth"]                                             # 203
    pocket_out = rr_prism_z(NR["w"] + 2 * POCKET_WALL, NR["d"] + 2 * POCKET_WALL, NR["r"] + POCKET_WALL,
                            Z0 - 1, pz1 + POCKET_WALL, cy=TILT_Y)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 4.0)
    pocket_in = rr_prism_z(NR["w"], NR["d"], NR["r"], Z0 - 5, pz1, cy=TILT_Y)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 2.0)
    # tilt hub bosses: the N07 caps are screwed to the head here (head <-> cap torque path).
    #   -X (servo side): Ø14 hub, central M2.5 screw into the cap / servo horn.
    #   +X (passive side): Ø24 hub with the Ø13 cable passage (hollow pin ID 13 of the 6703 bearing)
    #                      and 2x M2 screws (horizontal pair).
    hubs = None
    xw = NR["w"] / 2                                                   # 28 = pocket side wall
    xo = xw + POCKET_WALL                                              # 30 = pocket wall outer face
    for sx, rh in ((-1, HUB_R_SERVO), (1, HUB_R_PASSIVE)):
        b_in = cyl_x(rh, sx * (X_CAP_OUT + HUB_GAP), sx * (xw + 0.5), TILT_Y, TILT_Z)
        b_out = cyl_x(rh + 1.0, sx * (xo - 0.5), sx * (xo + 3.0), TILT_Y, TILT_Z)
        hb = b_in + b_out
        hubs = hb if hubs is None else hubs + hb
    h01 = h01 + ((pocket_out + hubs) & body)
    h01 = h01 - pocket_in
    h01 = h01 + (hubs & pocket_in)                                     # inner hub stubs live in the pocket
    h01 = h01 - cyl_x(1.4, -(X_CAP_OUT - 1), -(xo + 4), TILT_Y, TILT_Z)          # M2.5 clearance
    h01 = h01 - cyl_x(2.6, -(xo + 1.5), -(xo + 4), TILT_Y, TILT_Z)               # screw head counterbore
    h01 = h01 - cyl_x(CABLE_BORE_D / 2, X_CAP_OUT - 1, xo + 4, TILT_Y, TILT_Z)   # cable passage
    for sy in (-1, 1):                                                 # 2x M2 (horizontal pair)
        h01 = h01 - cyl_x(1.1, X_CAP_OUT - 1, xo + 4, TILT_Y + sy * HUB_SCREW_R, TILT_Z)

    # ear seats: Ø36.4 hole through the wall + inner shoulder ring (ear step rests on x = 63.8)
    e_y, e_z = EAR["y"], EAR["z"]
    for sx in (-1, 1):
        h01 = h01 + (tube_x(21.0, EAR_SPIGOT_R + 0.2, sx * EAR_X_RING_IN, sx * (EAR_X_STEP + 0.6), e_y, e_z) & body)
        h01 = h01 - cyl_x(EAR_HOLE_D / 2, sx * EAR_X_STEP, sx * (W / 2 + 3), e_y, e_z)
        h01 = h01 - cyl_x(EAR_SPIGOT_R + 0.2, sx * (EAR_X_RING_IN - 1), sx * (EAR_X_STEP + 0.01), e_y, e_z)

    # 4 screw bosses for the inner frame H11 (2 hanging from the roof, 2 standing on the floor)
    bosses = None
    for (x, y, za, zb) in ((40, 12, Z1 - 12, Z1), (-40, 12, Z1 - 12, Z1),
                           (44, 12, Z0, Z0 + 12), (-44, 12, Z0, Z0 + 12)):
        b = cyl_z(3.5, za, zb, x, y)
        bosses = b if bosses is None else bosses + b
    h01 = h01 + (bosses & body)
    for (x, y, za, zb) in ((40, 12, Z1 - 12.5, Z1 - WALL - 1.0), (-40, 12, Z1 - 12.5, Z1 - WALL - 1.0),
                           (44, 12, Z0 + 6.0, Z0 + 12.5), (-44, 12, Z0 + 6.0, Z0 + 12.5)):
        h01 = h01 - cyl_z(1.1, za, zb, x, y)

    # bezel latches (wedges on the inner wall that click into the H03 skirt windows) + skirt stops
    lw = LATCH_H
    lt = wedge_y(LATCH_Y_CATCH, LATCH_Y_CATCH - 2.8, lw, 8.0)
    zi_top, zi_bot = Z1 - WALL, Z0 + WALL
    xi = W / 2 - WALL
    latches = [on_frame(lt, "bottom", x, zi_top) for x in LATCH_X_TOP]          # hang from the roof
    latches += [on_frame(lt, "top", x, zi_bot) for x in LATCH_X_BOT]            # stand on the floor
    latches += [on_frame(lt, "left", LATCH_Z_SIDE, xi), on_frame(lt, "right", LATCH_Z_SIDE, -xi)]
    for l in latches:
        h01 = h01 + (l & body)
    stops = []
    ys0, ys1 = Y_SKIRT_END + 0.1, Y_SKIRT_END + 3.1
    for x in (-12.0, 12.0):
        stops.append(box(x - 3, x + 3, ys0, ys1, zi_top - 2.6, zi_top + 0.5))
    for z in (ZC - 12.0, ZC + 12.0):
        for sx in (-1, 1):
            stops.append(box(sx * (xi - 2.6), sx * (xi + 0.5), ys0, ys1, z - 3, z + 3))
    for s in stops:
        h01 = h01 + (s & body)

    # 2 groups of 3 vent slots in the floor, front (long axis // X, pitch along Y)
    h01 = h01 - vent_cutter(Z0 - 3, Z0 + WALL + 2)

    # crisp 0.3 break on the front opening edge
    e_open = edges_on_rr(h01, Y0, BZ["w"], BZ["h"], BZ["r"])
    h01 = try_fillet(h01, e_open, 0.3, "H01 opening")
    # 1 mm round on the neck-recess opening edge
    e_pk = [e for e in h01.edges() if e.center().Z < Z0 + 3.5
            and abs(e.center().X) <= NR["w"] / 2 + 0.05 and abs(e.center().Y - TILT_Y) <= NR["d"] / 2 + 0.05
            and e.bounding_box().max.Z < Z0 + 4.0 and e.bounding_box().min.Z <= Z0 + 0.01 + 3.0]
    h01 = try_fillet(h01, e_pk, 1.0, "H01 pocket rim")
    h01 = check("H01", h01, vmin=60000)

    # ---------------- H02 lip + snap hooks ------------------------------------------------------
    lw_o, lh_o, lr_o = BC["w"] - 2 * LIP_IN, BC["h"] - 2 * LIP_IN, BC["r"] - LIP_IN
    lip_ring = (rr_prism_y(lw_o, lh_o, lr_o, LIP_Y, Y1 + 5)
                - rr_prism_y(lw_o - 2 * LIP_T, lh_o - 2 * LIP_T, lr_o - LIP_T, LIP_Y - 1, Y1 + 6))
    h02 = h02 + (lip_ring & inner)
    # hooks: catch face sits just in front of the ledge's inner face (measured on the real ledge)
    hook_pos = [("top", 0.0), ("top", -30.0), ("top", 30.0), ("bottom", 0.0), ("bottom", -30.0),
                ("bottom", 30.0), ("right", ZC), ("left", ZC)]
    for side, along in hook_pos:
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
    h02 = check("H02", h02, vmin=8000)
    return h01, h02


def vent_cutter(z0, z1):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        for xc in VT["x"]:
            for i in range(VT["n"]):
                y = VT["y"] + (i - (VT["n"] - 1) / 2) * VT["pitch"]
                with Locations((xc, y)):
                    SlotOverall(VT["w"], VT["h"])
    return extrude(sk.sketch, z1 - z0)


# skirt / latch layout (shared by H01 and H03)
Y_SKIRT_END = Y_SKIRT_BACK - SKIRT_END_CLR          # -30.5
LATCH_Y_CATCH = Y_SKIRT_END - 2.2                   # -32.7 catch face (faces +Y)
LATCH_X_TOP = (-26.0, 26.0)
LATCH_X_BOT = (0.0,)
LATCH_Z_SIDE = ZC


# ===========================================================================================
# H03 – black front frame, H04 glass, H04C camera window, H04E eyes
# ===========================================================================================

def bezel():
    front = rr_prism_y(BZ["w"], BZ["h"], BZ["r"], Y_BEZEL_FRONT, Y0)
    front = fillet(front.edges().group_by(Axis.Y)[0], BZ["front_fillet"])
    sw, sh, sr = BZ["w"] - 2 * SKIRT_CLR, BZ["h"] - 2 * SKIRT_CLR, BZ["r"] - SKIRT_CLR
    skirt = rr_prism_y(sw, sh, sr, Y0 - 0.5, Y_SKIRT_END)
    b = front + skirt
    # glass seat (recessed), support ledge, hollow skirt
    gw, gh, gr = GL["w"] + 2 * GLASS_CLR, GL["h"] + 2 * GLASS_CLR, GL["r"] + GLASS_CLR
    b = b - rr_prism_y(gw, gh, gr, Y_BEZEL_FRONT - 1, Y_GLASS_BACK, cz=GZ)
    y_ledge_back = Y_GLASS_BACK + LEDGE_T                       # -49.3 (display front face)
    b = b - rr_prism_y(GL["w"] - 2 * LEDGE_W, GL["h"] - 2 * LEDGE_W, GL["r"] - LEDGE_W,
                       Y_GLASS_BACK - 0.5, y_ledge_back + 0.01, cz=GZ)
    siw, sih, sir = sw - 2 * SKIRT_WALL, sh - 2 * SKIRT_WALL, sr - SKIRT_WALL
    b = b - rr_prism_y(siw, sih, sir, y_ledge_back, Y_SKIRT_END + 1)
    # crisp 0.4 round on the visible inner front edge (glass seat)
    e_in = edges_on_rr(b, Y_BEZEL_FRONT, gw, gh, gr, cz=GZ)
    b = try_fillet(b, e_in, 0.4, "H03 inner edge")

    # camera: notch in the ledge + U-cradle for the 8.5x8.5 module (open toward the display)
    cm = CAM["module"]
    cx0, cx1 = cm[0] / 2 + 0.15, cm[0] / 2 + 0.15 + CAM_CRADLE_T
    cz0 = CAM["z"] - cm[1] / 2 - 0.15
    cz1 = CAM["z"] + cm[1] / 2 + 0.15
    b = b - box(-cx0, cx0, Y_GLASS_BACK - 0.01, y_ledge_back + 0.01, cz0, cz1)
    yc1 = Y_GLASS_BACK + cm[2] + 0.5
    z_roof = ZC + sih / 2 + 0.5                                  # merges into the skirt roof
    for sx in (-1, 1):
        b = b + box(sx * cx0, sx * cx1, Y_GLASS_BACK + 0.3, yc1, cz0, z_roof)
    b = b + box(-cx1, cx1, Y_GLASS_BACK + 0.3, yc1, cz1, z_roof)

    # latch windows in the skirt (H01 wedges click in) – window spans the latch +-0.2 / ramp side
    win_y0, win_y1 = LATCH_Y_CATCH - 3.2, LATCH_Y_CATCH + 0.25
    for x in LATCH_X_TOP:
        b = b - box(x - 4.4, x + 4.4, win_y0, win_y1, ZC + sih / 2 - 1, ZC + sh / 2 + 1)
    for x in LATCH_X_BOT:
        b = b - box(x - 4.4, x + 4.4, win_y0, win_y1, ZC - sh / 2 - 1, ZC - sih / 2 + 1)
    for sx in (-1, 1):
        b = b - box(sx * (siw / 2 - 1), sx * (sw / 2 + 1), win_y0, win_y1, LATCH_Z_SIDE - 4.4, LATCH_Z_SIDE + 4.4)

    # vents: skirt floor gets the same slot pattern as the H01 floor (air path to the display)
    b = b - vent_cutter(ZC - sh / 2 - 1, ZC - sih / 2 + 0.6)

    # 4 display bosses on the skirt side walls (display bracket screws, M2.5 self-tapping)
    dx_out = DSP["outline"][0] / 2                                # 52.75
    skirt_env = rr_prism_y(sw - 0.4, sh - 0.4, sr - 0.2, Y0 - 1, Y_SKIRT_END)
    for sx in (-1, 1):
        for dz in (-DISPLAY_BOSS_DZ, DISPLAY_BOSS_DZ):
            z = DSP["zc"] + dz
            blk = box(sx * (dx_out + 1.8), sx * (siw / 2 + 0.5), y_ledge_back + DSP["outline"][2], Y_SKIRT_END - 6.5,
                      z - 3.2, z + 3.2)
            b = b + (blk & skirt_env)
            b = b - cyl_y(1.1, y_ledge_back + DSP["outline"][2] - 1, Y_SKIRT_END - 7.5,
                          sx * (dx_out + 1.8 + (siw / 2 - dx_out - 1.8) / 2), z)
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
    return [
        PartRec("H01", "Hlavný obal hlavy", h01, "white", "head", "J3", (0, 0, up),
                note="PC/ABS 2.2 mm, biely lem 2.5 mm, uzavretá kapsa krku 56×56 hĺ. 34, 2×3 vetracie štrbiny"),
        PartRec("H02", "Zadný kryt hlavy", h02, "white", "head", "J3", (0, fy, up),
                note="servisný kryt 112×66 R20, škára 0.6, lícovací lem 1.2 + 8 zámkov"),
        PartRec("H03", "Predný rám", bezel(), "black", "head", "J3", (0, -fy, up),
                note="čierny soft-touch 127×91 R30, vystupuje 7 mm, lôžko skla, 5 okienok zámkov, 4 nálitky displeja"),
        PartRec("H04", "Sklo displeja", glass(), "glass", "head", "J3", (0, -fy, up),
                note="tvrdené sklo 119×79 R22 × 1.1, čierna potlač 4 mm, okienko kamery bez potlače"),
        PartRec("H04C", "Okienko kamery", camera_window(), "black_gloss", "head", "J3", (0, -fy, up),
                note="Ø3.2 nepotlačené okienko kamery (UVC modul 8.5×8.5 za sklom)"),
        PartRec("H04E", "Obsah displeja – oči", eyes(), "eye", "head", "J3", (0, -fy, up),
                note="základný výraz – dve teplé pilulky 13×21.5 R6.5"),
        PartRec("H05-R", "Ucho pravé", ear_r, "black", "head", "J3", (-ex, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1), zacvaknuté 3 zámkami"),
        PartRec("H05-L", "Ucho ľavé", ear_l, "black", "head", "J3", (ex, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1), zacvaknuté 3 zámkami"),
        PartRec("H06-R", "LED krúžok ucha pravý", ring_r, "cyan_led", "head", "J3", (-ex, 0, up),
                note="PMMA opál Ø30/Ø23, 12× LED"),
        PartRec("H06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", "head", "J3", (ex, 0, up),
                note="PMMA opál Ø30/Ø23, 12× LED"),
    ]


if __name__ == "__main__":
    run_module(build, "head")
