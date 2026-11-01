"""
NOVA – NECK (N01, N02, N06, N07-R, N07-L).  Run:  /opt/venv/cad/bin/python -m nova.cad.neck

Kinematics / function
  N01  Spodný golier      – fixed on the torso top (J1).  Elliptical concave flange, bore Ø36 for the
                            pan hub, cored underside with radial ribs, Ø39.4 locating spigot + 2 snap barbs
                            into the Ø40 torso neck hole.
  N02  Plast krku         – cosmetic concave "trumpet" (2 halves split in the YZ plane, clipped around
                            the pan hub with 4 internal tabs).  Pans with the head (J2).
  N06  Kryt náklonu       – hollow T-housing (barrel // X + stem) carrying the tilt servo (J2).
                            −X end wall: Ø14 bore for the servo output; +X end open Ø26 (servo is slid in,
                            closed by an internal bearing plug).  Oval 12×6 cable slot in the stem bottom.
  N07-R/L Koncové krytky  – domed hub caps on the barrel ends, fixed to the head frame (tilt J3).
                            Ø12 hub spigot enters the barrel end bore; Ø10 recess = screw cover seat.
Every number comes from spec.NECK / spec.TILT_AXIS unless it is a small local detail constant.
"""
from __future__ import annotations

import math

from build123d import (Axis, Box, Edge, Face, Plane, Pos, Rot, Solid, Vector, Wire, revolve, offset,
                       BuildSketch, SlotOverall, extrude, Locations, Align, Cylinder, Polyline, BuildLine,
                       make_face, Compound)

from nova import spec
from nova.cad.common import PartRec, run_module

N = spec.NECK
CO, CN, TH, CP = N["collar"], N["cone"], N["tilt_housing"], N["caps"]
AX_Y, AX_Z = spec.TILT_AXIS["y"], spec.TILT_AXIS["z"]          # tilt axis // X
PX, PY = spec.PAN_AXIS["x"], spec.PAN_AXIS["y"]                 # pan axis // Z

# ---- local detail constants (not shared with other modules) ---------------------------------
SEAM = 0.6            # standard seam / groove width
EPS = 0.01


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def ell_wire(a: float, b: float, z: float) -> Wire:
    """Ellipse (half-axes a // X, b // Y) at height z, centred on the pan axis."""
    if a >= b:
        e = Edge.make_ellipse(a, b, Plane(origin=(PX, PY, z)))
    else:
        e = Edge.make_ellipse(b, a, Plane(origin=(PX, PY, z), x_dir=(0, 1, 0)))
    return Wire([e])


def ell_prism(a: float, b: float, z0: float, z1: float) -> Solid:
    f = Face(ell_wire(a, b, z0))
    return Solid.extrude(f, Vector(0, 0, z1 - z0))


def cyl_z(r: float, z0: float, z1: float, x: float = PX, y: float = PY) -> Solid:
    return Solid.make_cylinder(r, z1 - z0, Plane(origin=(x, y, z0)))


def cyl_x(r: float, x0: float, x1: float, y: float = AX_Y, z: float = AX_Z) -> Solid:
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def ring_z(r_in: float, r_out: float, z0: float, z1: float) -> Solid:
    return cyl_z(r_out, z0, z1) - cyl_z(r_in, z0 - 1, z1 + 1)


def edges_where(shape, pred):
    return [e for e in shape.edges() if pred(e)]


def bb(e):
    return e.bounding_box()


def is_circle_at_z(r: float, z: float, tol: float = 0.05):
    def f(e):
        b = bb(e)
        return (abs(b.min.Z - z) < tol and abs(b.max.Z - z) < tol and abs(b.size.X - 2 * r) < 2 * tol + 0.02
                and abs(b.size.Y - 2 * r) < 2 * tol + 0.02)
    return f


def revolve_profile(pts_or_edges) -> Solid:
    """Revolve a closed profile given in the XZ half plane (x = radius) around the pan axis."""
    w = Wire(pts_or_edges)
    f = Face(w)
    s = revolve(f, Axis((PX, PY, 0), (0, 0, 1)), 360)
    return s.solids()[0] if hasattr(s, "solids") else s


def check(name, s):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    return s


# ---------------------------------------------------------------------------
# N01  Spodný golier – elliptical concave collar, fixed on the torso
# ---------------------------------------------------------------------------
A0, B0 = CO["w"] / 2, CO["d"] / 2            # 29 x 23 half axes
C_Z0, C_Z1 = CO["z0"], CO["z1"]              # 139 .. 145.5
R_BORE = CO["bore_d"] / 2                    # 18
R_LIP = CO["lip_d"] / 2                      # 20
EDGE_T = 1.7                                 # thin outer edge height (~1.5 visible after the R0.9 round)
Z_E = C_Z0 + EDGE_T                          # top of the edge band
Z_FT = C_Z1 - CO["lip_h"]                    # 144.5 = top of the flare / foot of the lip
GROOVE_D = 0.5
R_FT = R_LIP + SEAM + 0.4                    # 21.0 : flare top radius (0.4 shelf outside the groove)
WALL_N01 = 1.5


def _flare_sections(n=18, p=2.0, z_shift=0.0):
    ws = []
    for i in range(n + 1):
        u = i / n
        a = A0 + (R_FT - A0) * u
        b = B0 + (R_FT - B0) * u
        z = Z_E + (Z_FT - Z_E) * u ** p + z_shift
        ws.append(ell_wire(a, b, z))
    return ws


def collar_n01():
    flare = Solid.make_loft(_flare_sections())
    band = ell_prism(A0, B0, C_Z0, Z_E)
    body = band.fuse(flare).clean()
    body = check("N01 body", body)
    # rounds: outer rim top (biggest first), rim bottom break, flare/shelf edge
    rim_top = edges_where(body, lambda e: abs(bb(e).max.Z - Z_E) < 0.02 and abs(bb(e).min.Z - Z_E) < 0.02
                          and bb(e).size.X > 2 * A0 - 0.1)
    body = body.fillet(0.9, rim_top)
    rim_bot = edges_where(body, lambda e: abs(bb(e).max.Z - C_Z0) < 0.02 and bb(e).size.X > 2 * A0 - 0.1)
    body = body.fillet(0.35, rim_bot)
    shelf = edges_where(body, is_circle_at_z(R_FT, Z_FT))
    body = body.fillet(0.3, shelf)
    # lip Ø40 x 1 on top (overlaps 0.5 into the flare for a robust fuse)
    lip = cyl_z(R_LIP, Z_FT - 0.5, C_Z1)
    lip = lip.fillet(0.45, edges_where(lip, is_circle_at_z(R_LIP, C_Z1)))
    body = body.fuse(lip).clean()
    # groove line between flange and lip (0.6 wide, 0.5 deep)
    body = body - ring_z(R_LIP, R_LIP + SEAM, Z_FT - GROOVE_D, Z_FT + 0.6)
    body = check("N01 lip", body)

    # cored underside: shell of WALL_N01 following the concave top, 6 radial ribs, bore wall 1.8
    core_src = ell_prism(A0, B0, C_Z0 - 8, Z_E).fuse(Solid.make_loft(_flare_sections())).clean()
    shrunk = offset(core_src, amount=-WALL_N01)
    shrunk = shrunk.solids()[0] if hasattr(shrunk, "solids") else shrunk
    z_ceiling = Z_FT - GROOVE_D - WALL_N01
    pocket = shrunk & Pos(PX, PY, (C_Z0 - 10 + z_ceiling) / 2) * Box(80, 80, z_ceiling - (C_Z0 - 10))
    pocket = pocket - cyl_z(R_BORE + 1.8, C_Z0 - 20, C_Z1 + 5)
    rib_t = 1.2
    for k in range(3):
        rib = Pos(PX, PY, C_Z0 + 0.4 + 5) * Rot(0, 0, 30 + 60 * k) * Box(80, rib_t, 10)
        pocket = pocket - rib
    vol_before = body.volume
    body = body - pocket
    if body.volume > vol_before - 50:
        print("  ! N01 coring had no effect")
    # bore through
    body = body - cyl_z(R_BORE, C_Z0 - 20, C_Z1 + 5)
    body = body.fillet(0.3, edges_where(body, is_circle_at_z(R_BORE, C_Z1)))
    body = check("N01 cored", body)

    # locating spigot (into the Ø40 torso neck hole) + 2 snap barbs at ±X with relief slots
    sp_r = spec.TORSO["neck_hole_d"] / 2 - 0.3            # 19.7
    sp_z0 = C_Z0 - 3.4                                    # below the 2.4 mm torso top wall + barb
    spig = ring_z(R_BORE, sp_r, sp_z0, C_Z0 + 0.5)
    for sx in (1, -1):
        prof = [(sx * (sp_r - 0.3), sp_z0), (sx * (sp_r + 0.15), sp_z0), (sx * (sp_r + 0.9), sp_z0 + 0.8),
                (sx * (sp_r + 0.9), sp_z0 + 1.0), (sx * (sp_r - 0.3), sp_z0 + 1.0)]
        w = Wire.make_polygon([Vector(x, -3.0 + PY, z) for x, z in prof], close=True)
        barb = Solid.extrude(Face(w), Vector(0, 6.0, 0))
        spig = spig.fuse(barb)
        for sy in (1, -1):   # relief slots -> flexible finger
            spig = spig - Pos(PX + sx * R_LIP, PY + sy * 3.6, sp_z0 + 1.4) * Box(6, 0.8, 2.8 + EPS)
    body = body.fuse(spig).clean()
    return check("N01", body)


# ---------------------------------------------------------------------------
# N02  Plast krku – concave trumpet, 2 halves (split YZ), seam grooves front/back
# ---------------------------------------------------------------------------
K_Z0, K_Z1 = CN["z0"], CN["z1"]
K_RB, K_RT, K_W = CN["r_bottom"], CN["r_top"], CN["wall"]
K_P = 1.8                                       # concavity exponent of the trumpet profile


def cone_r(z):
    t = (z - K_Z0) / (K_Z1 - K_Z0)
    return K_RT + (K_RB - K_RT) * (1 - t) ** K_P


def cone_dr(z):
    t = (z - K_Z0) / (K_Z1 - K_Z0)
    return -(K_RB - K_RT) * K_P * (1 - t) ** (K_P - 1) / (K_Z1 - K_Z0)


def cone_r_in(z, wall=K_W):
    return cone_r(z) - wall * math.sqrt(1 + cone_dr(z) ** 2)   # normal wall thickness = wall


def cone_solid(r_fn, z0, z1, n=24):
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    pts = [Vector(PX + r_fn(z), PY, z) for z in zs]
    sp = Edge.make_spline(pts)
    e_top = Edge.make_line(pts[-1], Vector(PX, PY, z1))
    e_ax = Edge.make_line(Vector(PX, PY, z1), Vector(PX, PY, z0))
    e_bot = Edge.make_line(Vector(PX, PY, z0), pts[0])
    return revolve_profile([sp, e_top, e_ax, e_bot])


def trumpet_n02():
    n = 24
    zs = [K_Z0 + (K_Z1 - K_Z0) * i / n for i in range(n + 1)]
    out_pts = [Vector(PX + cone_r(z), PY, z) for z in zs]
    in_pts = [Vector(PX + cone_r_in(z), PY, z) for z in reversed(zs)]
    e_out = Edge.make_spline(out_pts)
    e_top = Edge.make_line(out_pts[-1], in_pts[0])
    e_in = Edge.make_spline(in_pts)
    e_bot = Edge.make_line(in_pts[-1], out_pts[0])
    s = revolve_profile([e_out, e_top, e_in, e_bot])
    s = check("N02 rev", s)
    r_in_top, r_in_bot = cone_r_in(K_Z1), cone_r_in(K_Z0)
    s = s.fillet(0.6, edges_where(s, is_circle_at_z(K_RB, K_Z0)))
    s = s.fillet(0.6, edges_where(s, is_circle_at_z(K_RT, K_Z1)))
    s = s.fillet(0.4, edges_where(s, is_circle_at_z(r_in_top, K_Z1)))
    s = s.fillet(0.3, edges_where(s, is_circle_at_z(r_in_bot, K_Z0)))
    # 4 internal clip tabs at the bottom (engage the pan hub)
    for k in range(4):
        tab = Pos(PX, PY, K_Z0 + 0.9) * Rot(0, 0, 45 + 90 * k) * Pos(r_in_bot - 0.4, 0, 0) * Box(2.2, 4.0, 1.8)
        s = s.fuse(tab)
    # seam grooves (0.5 wide, 0.5 deep) where the two halves meet: front (−Y) and back (+Y), plane x = 0
    seam_w, seam_d = 0.5, 0.5
    inner = cone_solid(lambda z: cone_r(z) - seam_d, K_Z0 - 1, K_Z1 + 1)
    slab = Pos(PX, PY, (K_Z0 + K_Z1) / 2) * Box(seam_w, 2 * K_RB + 6, K_Z1 - K_Z0 + 4)
    s = s - (slab - inner)
    return check("N02", s.clean())


# ---------------------------------------------------------------------------
# N06  Kryt náklonu – hollow T: barrel // X + stem, R4 blend, grooves, cable slot
# ---------------------------------------------------------------------------
R_BAR, L_BAR = TH["barrel_d"] / 2, TH["barrel_len"]        # 15, 48
R_STEM, Z_STEM0 = TH["stem_d"] / 2, TH["stem_z0"]          # 10.25, 158
W_N06 = 2.0
BLEND_R = 4.0
Z_LAND = K_Z1 + 0.5          # the R4 blend is trimmed here so it lands 0.5 above the N02 rim (no clash)
BORE_SERVO = 14.0            # −X end wall bore (servo output spline / horn)


def tilt_housing_n06():
    x0, x1 = PX - L_BAR / 2, PX + L_BAR / 2
    barrel = cyl_x(R_BAR, x0, x1)
    stem = cyl_z(R_STEM, Z_STEM0, AX_Z)
    t = barrel.fuse(stem).clean()
    z_lo = AX_Z - R_BAR
    z_hi = AX_Z - math.sqrt(R_BAR ** 2 - R_STEM ** 2)
    sad = edges_where(t, lambda e: bb(e).min.Z > z_lo - 0.05 and bb(e).max.Z < z_hi + 0.05
                      and bb(e).max.Z - bb(e).min.Z > 0.5)
    t = t.fillet(BLEND_R, sad)
    t = check("N06 blend", t)
    ends = edges_where(t, lambda e: abs(abs(bb(e).min.X - PX) - L_BAR / 2) < 0.02
                       and abs(bb(e).max.X - bb(e).min.X) < 0.02 and bb(e).size.Z > 2 * R_BAR - 0.1)
    t = t.fillet(1.5, ends)
    t = t.fillet(0.8, edges_where(t, is_circle_at_z(R_STEM, Z_STEM0)))
    t = check("N06 rounds", t)
    # trim the R4 blend below Z_LAND back to the plain stem (it would clash with the N02 top rim)
    trim = cyl_z(R_BAR + 5, Z_STEM0 - 1, Z_LAND) - cyl_z(R_STEM, Z_STEM0 - 2, Z_LAND + 1)
    t = t - trim
    t = t.fillet(0.25, edges_where(t, lambda e: abs(bb(e).min.Z - Z_LAND) < 0.02 and abs(bb(e).max.Z - Z_LAND) < 0.02
                                    and bb(e).size.X > 2 * R_STEM + 0.5))
    # circumferential grooves 3 mm from each barrel end
    for sx in (-1, 1):
        xc = PX + sx * (L_BAR / 2 - 3.0)
        g = cyl_x(R_BAR + 1, xc - SEAM / 2, xc + SEAM / 2) - cyl_x(R_BAR - GROOVE_D, xc - 1, xc + 1)
        t = t - g
    # hollow: barrel cavity (open at +X for servo insertion) + stem cavity
    cav = cyl_x(R_BAR - W_N06, x0 + W_N06, x1 + 1).fuse(cyl_z(R_STEM - W_N06, Z_STEM0 + W_N06, AX_Z))
    t = t - cav
    t = t - cyl_x(BORE_SERVO / 2, x0 - 1, x0 + W_N06 + 1)            # −X end: servo output bore
    # oval cable slot 12x6 (long axis // X) through the stem bottom
    sw, sh = TH["cable_slot"]
    with BuildSketch(Plane(origin=(PX, PY, Z_STEM0 - 1))) as sk:
        SlotOverall(sw, sh)
    t = t - extrude(sk.sketch, W_N06 + 2)
    return check("N06", t.clean())


# ---------------------------------------------------------------------------
# N07  Koncové krytky – domed hub caps (tilt with the head)
# ---------------------------------------------------------------------------
R_CAP, L_CAP, DOME, GAP = CP["d"] / 2, CP["len"], CP["dome"], CP["gap"]
X_CAP0 = L_BAR / 2 + GAP                        # 24.6
CAP_EDGE_R = 2.5
RECESS_D, RECESS_T = 10.0, 0.5
HUB_D, HUB_L = 12.0, 2.4


def cap_local():
    """Cap in a local frame: axis = +Z, inner face at z=0, dome apex at z=L_CAP."""
    zc = L_CAP - DOME
    cyl = Solid.make_cylinder(R_CAP, zc)
    rs = (R_CAP ** 2 + DOME ** 2) / (2 * DOME)
    sph = Solid.make_sphere(rs, Plane(origin=(0, 0, L_CAP - rs)))
    dome = sph & Solid.make_cylinder(R_CAP, DOME + 1, Plane(origin=(0, 0, zc)))
    c = cyl.fuse(dome).clean()
    c = c.fillet(CAP_EDGE_R, edges_where(c, is_circle_at_z(R_CAP, zc)))
    c = c.fillet(0.5, edges_where(c, is_circle_at_z(R_CAP, 0.0)))
    c = c - Solid.make_cylinder(RECESS_D / 2, 2, Plane(origin=(0, 0, L_CAP - RECESS_T)))
    hub = Solid.make_cylinder(HUB_D / 2, HUB_L + 0.5, Plane(origin=(0, 0, -HUB_L)))
    hub = hub.fillet(0.4, edges_where(hub, is_circle_at_z(HUB_D / 2, -HUB_L)))
    c = c.fuse(hub).clean()
    return check("N07", c)


def cap_n07(side: int):
    """side = -1 -> right cap (−X), +1 -> left cap (+X)."""
    c = cap_local()
    return check("N07 placed", Pos(PX + side * X_CAP0, AX_Y, AX_Z) * Rot(0, side * 90, 0) * c)


# ---------------------------------------------------------------------------
def build():
    return [
        PartRec("N01", "Spodný golier", collar_n01(), "black", "neck", "J1", (0, 0, 20),
                note="pevne na trupe; elipsa 58×46, otvor Ø36, nákružok Ø40, čap Ø39.4 + 2 západky"),
        PartRec("N02", "Plast krku", trumpet_n02(), "black", "neck", "J2", (0, 0, 45),
                note="2 polovice (delenie YZ), škára 0.5 vpredu/vzadu, otáča sa s hlavou (J2)"),
        PartRec("N06", "Kryt náklonu", tilt_housing_n06(), "black", "neck", "J2", (0, 0, 80),
                note="dutý T-diel, servo náklonu vnútri, otvor Ø14 pre výstup serva, kanál káblov 12×6"),
        PartRec("N07-R", "Koncová krytka pravá", cap_n07(-1), "black", "neck", "J3", (-35, 0, 80),
                note="pripevnená k ráme hlavy, kryt skrutky Ø10"),
        PartRec("N07-L", "Koncová krytka ľavá", cap_n07(+1), "black", "neck", "J3", (35, 0, 80),
                note="pripevnená k ráme hlavy, kryt skrutky Ø10"),
    ]


if __name__ == "__main__":
    run_module(build, "neck")
