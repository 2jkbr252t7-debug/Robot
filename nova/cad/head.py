"""
NOVA – HEAD (H01..H06).  Run:  /opt/venv/cad/bin/python -m nova.cad.head

All parts are built in final assembly position (joint J3 = head tilt about the X axis through
spec.TILT_AXIS).  Every number comes from spec.HEAD / spec.NECK unless it is a purely local
construction value (clearances, rib sizes, snap geometry) – those are named constants below.

Parts
  H01   Hlavný obal hlavy          white      rounded box shell, 4 mm white rim, closed neck pocket
  H02   Zadný kryt hlavy           white      back cover projected on the rear surface, 0.6 mm seam
  H03   Predný rám                 black      protruding frame 124x88 R24, glass seat, skirt + snaps
  H04   Sklo displeja              glass      108x76 R16 x 1.1 cover glass, camera hole
  H04E  Obsah displeja – oči       eye        two warm pill eyes lying on the glass
  H05-R/L  Ucho pravé / ľavé       black      Ø36 domed ear discs (touch + mic)
  H06-R/L  LED krúžok ucha         cyan_led   Ø30/Ø23 light-guide rings
"""
from __future__ import annotations

import math

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Face, Locations, Plane, Pos,
                       RectangleRounded, Rot, SlotOverall, Solid, Sphere, Vector, Wire, extrude, fillet,
                       mirror, offset, chamfer)

from nova import spec
from nova.cad.common import PartRec, run_module

H = spec.HEAD
W, D, HH = H["w"], H["d"], H["h"]          # 132 x 100 x 96
Y0, Y1 = H["y0"], H["y1"]                  # -46 (front rim) .. +54 (back)
Z0, Z1, ZC = H["z0"], H["z1"], H["zc"]     # 166 .. 262, centre 214
WALL = H["wall"]                           # 2.2
BZ = H["bezel"]
GL = H["glass"]
EAR = H["ear"]
BC = H["back_cover"]
NR = H["neck_recess"]
VT = H["vents"]
TILT_Y, TILT_Z = spec.TILT_AXIS["y"], spec.TILT_AXIS["z"]

# ---- derived levels -----------------------------------------------------------------------
Y_BEZEL_FRONT = Y0 - BZ["protrude"]                  # -50.5
Y_GLASS_FRONT = Y_BEZEL_FRONT + GL["recess"]         # -49.5
Y_GLASS_BACK = Y_GLASS_FRONT + GL["t"]               # -48.4
Y_SKIRT_BACK = Y_BEZEL_FRONT + BZ["depth"]           # -34.5
X_EAR_OUT = W / 2 + EAR["protrude"]                  # 74

# ---- local construction constants (not shared dimensions) ---------------------------------
SKIRT_CLR = 0.2          # radial clearance bezel skirt <-> white front opening
SKIRT_WALL = 2.0         # bezel skirt wall
GLASS_CLR = 0.15         # glass <-> bezel seat clearance (per side)
LEDGE_W = 2.0            # glass support ledge width behind the glass
LEDGE_T = 1.6            # glass support ledge thickness (display front rests on its back face)
EAR_HOLE_D = 36.4        # shell hole for the Ø36 ear (0.2 radial clearance)
EAR_X_IN = 63.0          # inner end of the ear spigot (|x|)
EAR_DOME = 1.0           # sag of the domed ear face
EAR_FILLET = 3.0         # ear outer edge fillet
RING_PROUD = 0.2         # LED ring stands 0.2 mm proud of the ear face
RING_DEPTH = 2.0
POCKET_WALL = 2.0        # closed neck pocket wall
LIP_T = 1.2              # H02 locating lip thickness
LEDGE_BACK_W = 4.0       # H01 inner ledge band under the H02 edge (inside the opening)
LEDGE_BACK_T = 1.5
CAM_Z = 248.0            # spec says 250 – that leaves 0.4 mm of glass above the Ø3.2 hole (see report)


# ===========================================================================================
# helpers
# ===========================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    """Plane at height y whose normal is +Y (local u = +X, local v = -Z, centred at cx, cz)."""
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


def cyl_x(r, x0, x1, y, z):
    """Cylinder along X from x0 to x1."""
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos((lo + hi) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo)


def cyl_y(r, y0, y1, x, z):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, (lo + hi) / 2, z) * Rot(90, 0, 0) * Cylinder(r, hi - lo)


def cyl_z(r, z0, z1, x, y):
    lo, hi = min(z0, z1), max(z0, z1)
    return Pos(x, y, lo) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def tube_x(ro, ri, x0, x1, y, z):
    return cyl_x(ro, x0, x1, y, z) - cyl_x(ri, x0 - 1, x1 + 1, y, z)


def wedge(ya, yb, t, width):
    """Snap-hook wedge in a canonical frame: base on z=0 (sunk 0.3 for a clean union), outward +Z,
    catch face at y=ya (full height t), ramp down to zero height at y=yb, centred on x=0."""
    pts = [(ya, -0.3), (ya, t), (yb, 0.0), (yb, -0.3)]
    w2 = width / 2
    face = Face(Wire.make_polygon([Vector(-w2, y, z) for y, z in pts], close=True))
    return Solid.extrude(face, Vector(width, 0, 0))


def place_on(shape, side, along, level):
    """Place a canonical wedge (outward +Z) on a side of a rounded-rect frame lying in XZ:
    side 'top'/'bottom' -> 'along' = x, 'level' = z of the surface;  'right'(+X)/'left'(-X) ->
    'along' = z, 'level' = x of the surface."""
    if side == "top":
        return Pos(along, 0, level) * shape
    if side == "bottom":
        return Pos(along, 0, level) * Rot(0, 180, 0) * shape
    if side == "right":      # +X
        return Pos(level, 0, along) * Rot(0, 90, 0) * shape
    return Pos(level, 0, along) * Rot(0, -90, 0) * shape


def check(name, s):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    return s


# ===========================================================================================
# H01 / H02 – white shells
# ===========================================================================================

def head_body(front_fillet=True):
    body = rr_prism_y(W, HH, H["r_front_view"], Y0, Y1)
    body = fillet(body.edges().group_by(Axis.Y)[-1], H["r_back"])          # back loop R24
    if front_fillet:
        body = fillet(body.edges().group_by(Axis.Y)[0], H["r_front_rim"])  # front rim R2.5
    return body


def shells():
    body = head_body(True)
    body_nf = head_body(False)
    inner = offset(body, amount=-WALL)
    assert inner.volume < body.volume * 0.95, "offset failed"
    shell = check("shell", body - inner)

    # ---------------- H02: back cover = shell inside the projected rounded rectangle ----------
    yb = 20.0                                         # projection prisms start well behind the front
    cover_zone = rr_prism_y(BC["w"], BC["h"], BC["r"], yb, Y1 + 5)
    h02 = shell & cover_zone
    # locating lip (1.2 mm) inside the H01 ledge, free edge flat at y = 44
    lip_o_w = BC["w"] + 2 * BC["seam"] - 2 * LEDGE_BACK_W - 0.4
    lip_o_h = BC["h"] + 2 * BC["seam"] - 2 * LEDGE_BACK_W - 0.4
    lip_o_r = BC["r"] + BC["seam"] - LEDGE_BACK_W - 0.2
    lip_y0 = 44.0
    lip_ring = (rr_prism_y(lip_o_w, lip_o_h, lip_o_r, lip_y0, Y1 + 5)
                - rr_prism_y(lip_o_w - 2 * LIP_T, lip_o_h - 2 * LIP_T, lip_o_r - LIP_T, lip_y0 - 1, Y1 + 6))
    h02 = h02 + (lip_ring & inner)
    # 4 snap hooks on the lip that click under the H01 ledge
    hk = wedge(49.2, 46.2, 0.6, 10.0)
    h02 = h02 + place_on(hk, "top", 0, ZC + lip_o_h / 2)
    h02 = h02 + place_on(hk, "bottom", 0, ZC - lip_o_h / 2)
    h02 = h02 + place_on(hk, "right", ZC, lip_o_w / 2)
    h02 = h02 + place_on(hk, "left", ZC, -lip_o_w / 2)
    h02 = check("H02", h02)

    # ---------------- H01: main shell ------------------------------------------------------------
    s = BC["seam"]
    h01 = shell - rr_prism_y(BC["w"] + 2 * s, BC["h"] + 2 * s, BC["r"] + s, yb, Y1 + 5)
    # front opening = bezel outline
    h01 = h01 - rr_prism_y(BZ["w"], BZ["h"], BZ["r"], Y0 - 2, Y0 + WALL + 2)

    # inner ledge band under the H02 edge (also the floor of the 0.6 mm seam -> no see-through)
    inner2 = offset(body_nf, amount=-(WALL + LEDGE_BACK_T))
    band = inner - inner2
    lo_w, lo_h, lo_r = BC["w"] + 2 * s + 6, BC["h"] + 2 * s + 6, BC["r"] + s + 3
    li_w, li_h, li_r = BC["w"] + 2 * s - 2 * LEDGE_BACK_W, BC["h"] + 2 * s - 2 * LEDGE_BACK_W, BC["r"] + s - LEDGE_BACK_W
    ring = rr_prism_y(lo_w, lo_h, lo_r, yb, Y1 + 5) - rr_prism_y(li_w, li_h, li_r, yb - 1, Y1 + 6)
    h01 = h01 + (band & ring)

    # closed neck pocket: opening 68x46 R12 in the floor, 2 mm walls, ceiling at z0 + depth
    pz1 = Z0 + NR["depth"]                                             # 195
    pocket_out = rr_prism_z(NR["w"] + 2 * POCKET_WALL, NR["d"] + 2 * POCKET_WALL, NR["r"] + POCKET_WALL,
                            Z0 - 1, pz1 + POCKET_WALL)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 3.0)
    pocket_in = rr_prism_z(NR["w"], NR["d"], NR["r"], Z0 - 5, pz1)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 1.5)
    # tilt hub bosses on the pocket side walls (head <-> N07 caps / H11 frame, M2.5 screw)
    hubs = None
    for sx in (-1, 1):
        xw = sx * (NR["w"] / 2)
        b_in = cyl_x(6.0, xw - sx * 2.0, xw + sx * 0.5, TILT_Y, TILT_Z)          # inside pocket to |x|=32
        b_out = cyl_x(8.0, xw + sx * (POCKET_WALL - 0.5), xw + sx * (POCKET_WALL + 3.0), TILT_Y, TILT_Z)
        hb = b_in + b_out
        hubs = hb if hubs is None else hubs + hb
    h01 = h01 + ((pocket_out + hubs) & body)
    h01 = h01 - pocket_in
    for sx in (-1, 1):
        h01 = h01 - cyl_x(1.2, sx * 30, sx * 40, TILT_Y, TILT_Z)

    # ear holes + inner bearing tubes
    e_y, e_z = EAR["y"], EAR["z"]
    for sx in (-1, 1):
        h01 = h01 + (tube_x(21.0, EAR_HOLE_D / 2, sx * 61.0, sx * 64.6, e_y, e_z) & body)
        h01 = h01 - cyl_x(EAR_HOLE_D / 2, sx * 59.0, sx * (W / 2 + 3), e_y, e_z)

    # 4 screw bosses for the inner frame H11 (2 hanging from the roof, 2 standing on the floor)
    bosses = None
    for (x, y, za, zb) in ((40, 12, Z1 - 12, Z1), (-40, 12, Z1 - 12, Z1),
                           (44, 12, Z0, Z0 + 10), (-44, 12, Z0, Z0 + 10)):
        b = cyl_z(3.5, za, zb, x, y)
        bosses = b if bosses is None else bosses + b
    h01 = h01 + (bosses & body)
    for (x, y, za, zb) in ((40, 12, Z1 - 12.5, Z1 - WALL - 1.0), (-40, 12, Z1 - 12.5, Z1 - WALL - 1.0),
                           (44, 12, Z0 + WALL + 1.5, Z0 + 10.5), (-44, 12, Z0 + WALL + 1.5, Z0 + 10.5)):
        h01 = h01 - cyl_z(1.1, za, zb, x, y)

    # 6 vent slots in the floor, rear (long axis along Y, pitch along X)
    vy = VENT_Y
    with BuildSketch(Plane.XY.offset(Z0 - 3)) as sk:
        for i in range(VT["n"]):
            x = (i - (VT["n"] - 1) / 2) * VT["pitch"]
            with Locations((x, vy)):
                SlotOverall(VT["w"], VT["h"], rotation=90)
    h01 = h01 - extrude(sk.sketch, 9.0)

    h01 = check("H01", h01)
    return h01, h02


VENT_Y = 33.5            # spec y=30 would cut into the neck-pocket wall (pocket reaches y=25)


# ===========================================================================================
# H03 – black front frame, H04 glass, H04E eyes
# ===========================================================================================

def bezel():
    front = rr_prism_y(BZ["w"], BZ["h"], BZ["r"], Y_BEZEL_FRONT, Y0)
    front = fillet(front.edges().group_by(Axis.Y)[0], BZ["front_fillet"])
    sw, sh, sr = BZ["w"] - 2 * SKIRT_CLR, BZ["h"] - 2 * SKIRT_CLR, BZ["r"] - SKIRT_CLR
    skirt = rr_prism_y(sw, sh, sr, Y0 - 1.0, Y_SKIRT_BACK)
    b = front + skirt
    # glass seat (recessed 1 mm), support ledge, hollow skirt
    gw, gh, gr = GL["w"] + 2 * GLASS_CLR, GL["h"] + 2 * GLASS_CLR, GL["r"] + GLASS_CLR
    b = b - rr_prism_y(gw, gh, gr, Y_BEZEL_FRONT - 1, Y_GLASS_BACK)
    y_ledge_back = Y_GLASS_BACK + LEDGE_T
    b = b - rr_prism_y(GL["w"] - 2 * LEDGE_W, GL["h"] - 2 * LEDGE_W, GL["r"] - LEDGE_W,
                       Y_GLASS_BACK - 0.5, y_ledge_back + 0.01)
    b = b - rr_prism_y(sw - 2 * SKIRT_WALL, sh - 2 * SKIRT_WALL, sr - SKIRT_WALL, y_ledge_back, Y_SKIRT_BACK + 1)
    # crisp 0.4 mm round on the visible inner front edge
    try:
        e_in = [e for e in b.edges() if abs(e.center().Y - Y_BEZEL_FRONT) < 1e-3
                and abs(e.center().X) < gw / 2 + 0.01 and abs(e.center().Z - ZC) < gh / 2 + 0.01]
        b = fillet(e_in, 0.4)
    except Exception as ex:  # pragma: no cover
        print("  (bezel inner edge fillet skipped:", ex, ")")
    # camera notch in the ledge (module 8.5 x 8.5 sits above the display)
    b = b - Pos(0, (Y_GLASS_BACK + y_ledge_back) / 2, CAM_Z + 2.5) * Box(11.0, LEDGE_T + 0.2, 10.0)
    # snap hooks on the skirt: catch behind the H01 front wall (inner face y = -43.8)
    hk = wedge(Y0 + WALL + 0.2, Y0 + WALL + 2.8, 0.7, 9.0)
    for x in (-32.0, 32.0):
        b = b + place_on(hk, "top", x, ZC + sh / 2)
        b = b + place_on(hk, "bottom", x, ZC - sh / 2)
    for z in (ZC,):
        b = b + place_on(hk, "right", z, sw / 2)
        b = b + place_on(hk, "left", z, -sw / 2)
    # 4 screw bosses for the display / inner frame H11 (behind the ledge, outside the display outline)
    for (x, z) in ((44.0, 248.0), (-44.0, 248.0), (44.0, 175.0), (-44.0, 175.0)):
        boss = cyl_y(3.0, y_ledge_back - 0.2, Y_SKIRT_BACK - 4.0, x, z) - cyl_y(1.1, y_ledge_back + 1.0, Y_SKIRT_BACK, x, z)
        b = b + boss
    return check("H03", b)


def glass():
    g = rr_prism_y(GL["w"], GL["h"], GL["r"], Y_GLASS_FRONT, Y_GLASS_BACK)
    try:
        g = fillet(g.edges().group_by(Axis.Y)[0], 0.3)      # C-cut front edge
    except Exception:
        pass
    g = g - cyl_y(H["camera"]["hole_d"] / 2, Y_GLASS_FRONT - 1, Y_GLASS_BACK + 1, 0.0, CAM_Z)
    return check("H04", g)


def eyes():
    E = H["eyes"]
    t = 0.15
    out = None
    for sx in (-1, 1):
        with BuildSketch(plane_y(Y_GLASS_FRONT - t, sx * E["x"], E["z"])) as sk:
            SlotOverall(E["h"], E["w"], rotation=90)
        e = extrude(sk.sketch, t)
        out = e if out is None else out + e
    return out


# ===========================================================================================
# H05 ears + H06 LED rings (built for the LEFT ear, +X, then mirrored)
# ===========================================================================================

def ear_left():
    r = EAR["d"] / 2
    sag = EAR_DOME
    rs = (r * r + sag * sag) / (2 * sag)              # sphere radius of the dome (162.5)
    yc, zc = EAR["y"], EAR["z"]
    # local frame: axis = X through (0,0); positioned at the end
    disc = cyl_x(r, EAR_X_IN, X_EAR_OUT + 1.0, 0, 0)
    disc = disc & Pos(X_EAR_OUT - rs, 0, 0) * Sphere(rs)
    edge_out = [e for e in disc.edges() if e.center().X > X_EAR_OUT - 1.5]
    disc = fillet(edge_out, EAR_FILLET)
    edge_in = [e for e in disc.edges() if abs(e.center().X - EAR_X_IN) < 1e-3]
    disc = chamfer(edge_in, 0.5)
    # inner cup (LED / touch / mic PCB sits here)
    cup_x1 = 70.0
    disc = disc - cyl_x(15.5, EAR_X_IN - 1, cup_x1, 0, 0)
    # ring groove
    ro, ri = EAR["ring_od"] / 2, EAR["ring_id"] / 2
    x_dome_in = X_EAR_OUT - rs + math.sqrt(rs * rs - ri * ri)
    ring_bot = x_dome_in + RING_PROUD - RING_DEPTH
    disc = disc - tube_x(ro + 0.1, ri - 0.1, ring_bot - 0.05, X_EAR_OUT + 2, 0, 0)
    # 4 light windows from the cup into the groove + Ø1 microphone hole
    rm = (ro + ri) / 2
    for k in range(4):
        a = math.radians(45 + 90 * k)
        disc = disc - cyl_x(0.9, cup_x1 - 0.5, ring_bot + 0.1, rm * math.cos(a), rm * math.sin(a))
    disc = disc - cyl_x(EAR["mic_hole_d"] / 2, cup_x1 - 0.5, X_EAR_OUT + 1, 0, 0)
    # 3 snap fingers that click behind the H01 bearing tube (inner end |x| = 61)
    for k in range(3):
        f = Pos((EAR_X_IN + 60.6) / 2 + 0.2, 0, 17.2) * Box(EAR_X_IN - 60.6 + 0.4, 5.0, 1.2)
        f = f + Pos(60.6 + 0.2, 0, 17.8) * Box(0.4, 5.0, 1.8)
        disc = disc + Rot(120 * k, 0, 0) * f
    ring = tube_x(ro, ri, ring_bot, X_EAR_OUT + 2, 0, 0) & Pos(X_EAR_OUT - rs, 0, 0) * Sphere(rs + RING_PROUD)
    return Pos(0, yc, zc) * disc, Pos(0, yc, zc) * ring


# ===========================================================================================

def build():
    h01, h02 = shells()
    ear_l, ring_l = ear_left()
    ear_r = mirror(ear_l, Plane.YZ)
    ring_r = mirror(ring_l, Plane.YZ)
    up = 150.0
    return [
        PartRec("H01", "Hlavný obal hlavy", h01, "white", "head", "J3", (0, 0, up),
                note="PC/ABS 2.2 mm, 4 mm biely lem, uzavretá kapsa krku, 6 vetracích štrbín"),
        PartRec("H02", "Zadný kryt hlavy", h02, "white", "head", "J3", (0, 45, up),
                note="servisný kryt 100×66 R18, škára 0.6, lícovací lem + 4 zámky"),
        PartRec("H03", "Predný rám", bezel(), "black", "head", "J3", (0, -45, up),
                note="čierny soft-touch, vystupuje 4.5 mm, lôžko skla, 6 zámkov, 4 nálitky pre H11"),
        PartRec("H04", "Sklo displeja", glass(), "glass", "head", "J3", (0, -45, up),
                note="tvrdené sklo 1.1 mm, čierna potlač 4 mm, otvor kamery Ø3.2"),
        PartRec("H04E", "Obsah displeja – oči", eyes(), "eye", "head", "J3", (0, -45, up),
                note="základný výraz – dve teplé pilulky 11×19"),
        PartRec("H05-R", "Ucho pravé", ear_r, "black", "head", "J3", (-40, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1)"),
        PartRec("H05-L", "Ucho ľavé", ear_l, "black", "head", "J3", (40, 0, up),
                note="kapacitný dotyk + MEMS mikrofón (otvor Ø1)"),
        PartRec("H06-R", "LED krúžok ucha pravý", ring_r, "cyan_led", "head", "J3", (-40, 0, up),
                note="PMMA opál, 12× LED"),
        PartRec("H06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", "head", "J3", (40, 0, up),
                note="PMMA opál, 12× LED"),
    ]


if __name__ == "__main__":
    run_module(build, "head")
