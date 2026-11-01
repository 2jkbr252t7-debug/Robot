"""
NOVA – NECK (N01, N02, N06, N07-R, N07-L).  Run:  /opt/venv/cad/bin/python -m nova.cad.neck

Spec v7.2 (spec.NECK, spec.TILT_AXIS, spec.PAN_AXIS).  Kinematics / function:
  N01  Spodný golier      – fixed on the torso top (J1).  Elliptical 52 x 42 sloped flange (outer edge 2.0),
                            concave top rising to a groove line and a raised inner lip Ø35 x 1.2, bore Ø32.
                            Underside cored (1.5 wall) with radial ribs; Ø33.7 locating ring into the torso
                            Ø34 neck hole + 2 anti-rotation pins Ø2; bonded (VHB) to the torso top.
  N02  Plast krku         – cosmetic concave "trumpet", r(z) = r_top + (r_bot - r_top) * ((z1 - z)/(z1 - z0))^2,
                            wall 2.  Two halves split in the YZ plane (0.5 seam grooves front + back), clipped
                            on the pan hub by 4 internal tabs.  The top edge is a saddle trimmed 0.3 mm off
                            the barrel so the cone runs straight into the N06 underside.  Pans (J2).
  N06  Kryt náklonu       – horizontal barrel Ø40 x 36 // X on the tilt axis, NO visible stem.  Hollow
                            (wall 2): −X end wall with Ø14 bore for the tilt-servo output; +X end opening Ø32
                            (servo slid in, closed by the 6703 bearing plug – internal part).  Hidden Ø17.6
                            spigot under the barrel (inside N02) = mount on the pan hub (2x M2) and the 14 x 8
                            cable passage from the cone into the barrel.  0.6 grooves 3 mm from each end.
                            Pans (J2).
  N07-R/L Koncové krytky  – Ø39 x 6 domed hub caps, 0.6 gap to the barrel, fixed to the head frame (J3).
                            Ø12 x 0.5 centre recess = seat of the head-pocket boss (H01).  R: Ø12 spigot into
                            the servo-horn adapter, M2.5 pilot hole.  L: integral hollow pin OD17/ID13 running
                            in the 6703 bearing, Ø8 cable exit into the hollow head boss + 2x M2 pilots.
Every number comes from spec.NECK / spec.TILT_AXIS unless it is a small local detail constant.
"""
from __future__ import annotations

import math

from build123d import (Axis, Box, BuildSketch, Edge, Face, Plane, Pos, Rot, SlotOverall, Solid, Vector,
                       Wire, extrude, offset, revolve)

from nova import spec
from nova.cad.common import PartRec, run_module

N = spec.NECK
CO, CN, TH, CP = N["collar"], N["cone"], N["tilt_housing"], N["caps"]
AX_Y, AX_Z = spec.TILT_AXIS["y"], spec.TILT_AXIS["z"]          # tilt axis // X
PX, PY = spec.PAN_AXIS["x"], spec.PAN_AXIS["y"]                 # pan axis // Z

# ---- local detail constants (not shared with other modules) ---------------------------------
SEAM = 0.6            # standard seam / groove width
GROOVE_D = 0.5        # depth of decorative grooves
EPS = 0.01


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def ell_wire(a: float, b: float, z: float) -> Wire:
    """Ellipse (half-axes a // X, b // Y) at height z, centred on the pan axis."""
    if abs(a - b) < 1e-6:
        return Wire([Edge.make_circle(a, Plane(origin=(PX, PY, z)))])
    if a > b:
        e = Edge.make_ellipse(a, b, Plane(origin=(PX, PY, z)))
    else:
        e = Edge.make_ellipse(b, a, Plane(origin=(PX, PY, z), x_dir=(0, 1, 0)))
    return Wire([e])


def ell_prism(a: float, b: float, z0: float, z1: float) -> Solid:
    return Solid.extrude(Face(ell_wire(a, b, z0)), Vector(0, 0, z1 - z0))


def cyl_z(r: float, z0: float, z1: float, x: float = PX, y: float = PY) -> Solid:
    return Solid.make_cylinder(r, z1 - z0, Plane(origin=(x, y, z0)))


def cyl_x(r: float, x0: float, x1: float, y: float = AX_Y, z: float = AX_Z) -> Solid:
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def ring_z(r_in: float, r_out: float, z0: float, z1: float) -> Solid:
    return cyl_z(r_out, z0, z1) - cyl_z(r_in, z0 - 1, z1 + 1)


def ring_x(r_in: float, r_out: float, x0: float, x1: float) -> Solid:
    return cyl_x(r_out, x0, x1) - cyl_x(r_in, x0 - 1, x1 + 1)


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


def is_circle_at_x(r: float, x: float, tol: float = 0.05):
    def f(e):
        b = bb(e)
        return (abs(b.min.X - x) < tol and abs(b.max.X - x) < tol and abs(b.size.Z - 2 * r) < 2 * tol + 0.02
                and abs(b.size.Y - 2 * r) < 2 * tol + 0.02)
    return f


def solid_of(s):
    if hasattr(s, "solids"):
        ss = s.solids()
        if len(ss) == 1:
            return ss[0]
        return max(ss, key=lambda q: q.volume)
    return s


def revolve_profile(edges) -> Solid:
    """Revolve a closed profile given in the XZ half plane (x = radius) around the pan axis."""
    s = revolve(Face(Wire(edges)), Axis((PX, PY, 0), (0, 0, 1)), 360)
    return solid_of(s)


def check(name, s):
    s = solid_of(s)
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    return s


# ---------------------------------------------------------------------------
# N01  Spodný golier – elliptical sloped flange, fixed on the torso
# ---------------------------------------------------------------------------
A0, B0 = CO["w"] / 2, CO["d"] / 2            # 26 x 21 half axes
C_Z0, C_Z1 = CO["z0"], CO["z1"]              # 142 .. 148.5
R_BORE = CO["bore_d"] / 2                    # 16
R_LIP = CO["lip_d"] / 2                      # 17.5
EDGE_H = CO["edge_h"]                        # 2.0 outer edge height
Z_E = C_Z0 + EDGE_H                          # 144  top of the edge band
Z_FT = C_Z1 - CO["lip_h"]                    # 147.3 = flange top / foot of the lip
R_GRV = R_LIP + SEAM                         # 18.1 outer radius of the groove line
R_FT = R_GRV + 0.5                           # 18.6 flange top radius (0.5 shelf outside the groove)
FLARE_P = 1.8                                # concavity of the flange (z ~ u^p, u = 0 at the edge)
RIM_R = 0.8                                  # round of the outer rim top
WALL_N01 = 1.5
LOC_R = spec.TORSO["neck_hole_d"] / 2 - 0.15  # 16.85 locating ring OD (0.15 play in the torso Ø34 hole)
LOC_DEPTH = 1.4                              # stays above the 61805 bearing under the 2.4 torso top wall
PIN_X, PIN_D, PIN_L = 22.5, 2.0, 1.4         # anti-rotation pins (holes in the torso top)


def _flare_sections(n=20):
    ws = []
    for i in range(n + 1):
        u = i / n
        a = A0 + (R_FT - A0) * u
        b = B0 + (R_FT - B0) * u
        z = Z_E + (Z_FT - Z_E) * u ** FLARE_P
        ws.append(ell_wire(a, b, z))
    return ws


def collar_n01():
    flare = Solid.make_loft(_flare_sections())
    band = ell_prism(A0, B0, C_Z0, Z_E)
    body = check("N01 body", band.fuse(flare).clean())
    # rounds: outer rim top (biggest first), rim bottom break
    rim_top = edges_where(body, lambda e: abs(bb(e).max.Z - Z_E) < 0.02 and abs(bb(e).min.Z - Z_E) < 0.02
                          and bb(e).size.X > 2 * A0 - 0.1)
    body = body.fillet(RIM_R, rim_top)
    rim_bot = edges_where(body, lambda e: abs(bb(e).max.Z - C_Z0) < 0.02 and bb(e).size.X > 2 * A0 - 0.1)
    body = body.fillet(0.3, rim_bot)
    shelf = edges_where(body, is_circle_at_z(R_FT, Z_FT))
    body = body.fillet(0.3, shelf)
    # raised inner lip Ø35 x 1.2 (overlaps 0.5 into the flange for a robust fuse)
    lip = cyl_z(R_LIP, Z_FT - 0.5, C_Z1)
    lip = lip.fillet(0.4, edges_where(lip, is_circle_at_z(R_LIP, C_Z1)))
    body = body.fuse(lip).clean()
    # groove line between flange and lip (0.6 wide, 0.5 deep)
    body = body - ring_z(R_LIP, R_GRV, Z_FT - GROOVE_D, Z_FT + 0.6)
    body = check("N01 lip", body)

    # cored underside: pocket = flange body shrunk by the wall, ceiling below the groove; 6 radial ribs
    core_src = ell_prism(A0, B0, C_Z0 - 8, Z_E).fuse(Solid.make_loft(_flare_sections())).clean()
    shrunk = solid_of(offset(core_src, amount=-WALL_N01))
    z_ceiling = Z_FT - GROOVE_D - WALL_N01
    pocket = shrunk & Pos(PX, PY, (C_Z0 - 10 + z_ceiling) / 2) * Box(80, 80, z_ceiling - (C_Z0 - 10))
    pocket = pocket - cyl_z(R_BORE + 1.6, C_Z0 - 20, C_Z1 + 5)
    rib_t = 1.2
    for k in range(3):
        pocket = pocket - Pos(PX, PY, C_Z0 + 5) * Rot(0, 0, 30 + 60 * k) * Box(80, rib_t, 10)
    # pin bosses
    for sx in (1, -1):
        pocket = pocket - cyl_z(PIN_D / 2 + 1.2, C_Z0 - 1, C_Z1, x=PX + sx * PIN_X)
    vol_before = body.volume
    body = body - pocket
    if body.volume > vol_before - 50:
        print("  ! N01 coring had no effect")
    # bore through
    body = body - cyl_z(R_BORE, C_Z0 - 20, C_Z1 + 5)
    body = body.fillet(0.3, edges_where(body, is_circle_at_z(R_BORE, C_Z1)))
    body = check("N01 cored", body)

    # locating ring into the torso Ø34 neck hole + 2 anti-rotation pins
    loc = ring_z(R_BORE, LOC_R, C_Z0 - LOC_DEPTH, C_Z0 + 0.5)
    loc = loc.fillet(0.25, edges_where(loc, is_circle_at_z(LOC_R, C_Z0 - LOC_DEPTH)))
    body = body.fuse(loc)
    for sx in (1, -1):
        pin = cyl_z(PIN_D / 2, C_Z0 - PIN_L, C_Z0 + 0.5, x=PX + sx * PIN_X)
        pin = pin.fillet(0.3, edges_where(pin, is_circle_at_z(PIN_D / 2, C_Z0 - PIN_L)))
        body = body.fuse(pin)
    return check("N01", body.clean())


# ---------------------------------------------------------------------------
# N02  Plast krku – concave trumpet, 2 halves (split YZ), seam grooves front/back
# ---------------------------------------------------------------------------
K_Z0, K_Z1 = CN["z0"], CN["z1"]
K_RB, K_RT, K_W = CN["r_bottom"], CN["r_top"], CN["wall"]
R_BAR, L_BAR = TH["barrel_d"] / 2, TH["barrel_len"]        # 20, 36
TOP_GAP = 0.3                                              # N02 saddle top edge <-> barrel surface
SKIRT_RO = R_BORE - 0.5                                    # 15.5 labyrinth skirt in the N01 bore (0.5 play)
SKIRT_RI = 14.3
SKIRT_L = 2.5                                              # skirt reaches z 146.5 (collar lip top 148.5)


def cone_r(z):
    """Spec profile: r(z) = r_top + (r_bot - r_top) * ((z1 - z) / (z1 - z0))^2."""
    u = (K_Z1 - z) / (K_Z1 - K_Z0)
    return K_RT + (K_RB - K_RT) * u * u


def cone_dr(z):
    u = (K_Z1 - z) / (K_Z1 - K_Z0)
    return -2.0 * (K_RB - K_RT) * u / (K_Z1 - K_Z0)


def cone_inner_pt(z, wall=K_W):
    """Point of the inner wall surface at normal distance `wall` from the outer profile point at z."""
    d = cone_dr(z)
    s = math.sqrt(1 + d * d)
    return cone_r(z) - wall / s, z + wall * d / s


def trumpet_n02():
    n = 32
    zs = [K_Z0 + (K_Z1 - K_Z0) * i / n for i in range(n + 1)]
    out_pts = [Vector(PX + cone_r(z), PY, z) for z in zs]
    # inner wall = normal offset; extended to the same top / bottom planes
    inn = [cone_inner_pt(z) for z in zs]
    # bottom: intersect the inner offset with z = K_Z0 (extrapolate linearly with the first segment)
    (r0, z0), (r1, z1) = inn[0], inn[1]
    r_in_bot = r0 + (r1 - r0) * (K_Z0 - z0) / (z1 - z0)
    inn = [(r_in_bot, K_Z0)] + [p for p in inn if K_Z0 + 0.05 < p[1] < K_Z1 - 0.05] + [(K_RT - K_W, K_Z1)]
    in_pts = [Vector(PX + r, PY, z) for r, z in reversed(inn)]
    e_out = Edge.make_spline(out_pts)
    e_top = Edge.make_line(out_pts[-1], in_pts[0])
    e_in = Edge.make_spline(in_pts)
    e_bot = Edge.make_line(in_pts[-1], out_pts[0])
    s = check("N02 rev", revolve_profile([e_out, e_top, e_in, e_bot]))
    s = s.fillet(0.3, edges_where(s, is_circle_at_z(K_RB, K_Z0)))
    # labyrinth skirt hanging into the N01 bore (hides the 0.5 rotation gap above the lip)
    sk = ring_z(SKIRT_RI, SKIRT_RO, K_Z0 - SKIRT_L, K_Z0 + 0.5)
    sk = sk.fillet(0.25, edges_where(sk, lambda e: abs(bb(e).max.Z - (K_Z0 - SKIRT_L)) < 0.02))
    s = s.fuse(sk).clean()
    # saddle top: trimmed by the barrel cylinder grown by TOP_GAP -> the cone runs into the barrel
    s = s - cyl_x(R_BAR + TOP_GAP, PX - L_BAR, PX + L_BAR)
    s = check("N02 saddle", s)
    # 4 internal clip tabs at the bottom (snap into a groove of the pan hub, r 12.5)
    for k in range(4):
        tab = (Pos(PX, PY, K_Z0 + 1.2) * Rot(0, 0, 45 + 90 * k)
               * Pos((12.8 + r_in_bot + 0.6) / 2, 0, 0) * Box(r_in_bot + 0.6 - 12.8, 4.0, 1.6))
        s = s.fuse(tab)
    # seam grooves (0.5 wide, 0.5 deep) where the two halves meet: front (−Y) and back (+Y), plane x = 0
    seam_w, seam_d = 0.5, 0.5
    zs2 = [K_Z0 - 1 + (K_Z1 + 1 - (K_Z0 - 1)) * i / 36 for i in range(37)]
    pts = [Vector(PX + cone_r(min(max(z, K_Z0 - 1), K_Z1)) - seam_d, PY, z) for z in zs2]
    sp = Edge.make_spline(pts)
    inner = revolve_profile([sp, Edge.make_line(pts[-1], Vector(PX, PY, zs2[-1])),
                             Edge.make_line(Vector(PX, PY, zs2[-1]), Vector(PX, PY, zs2[0])),
                             Edge.make_line(Vector(PX, PY, zs2[0]), pts[0])])
    slab = Pos(PX, PY, (K_Z0 + K_Z1) / 2) * Box(seam_w, 2 * K_RB + 6, K_Z1 - K_Z0 + 6)
    s = s - (slab - inner)
    return check("N02", s.clean())


# ---------------------------------------------------------------------------
# N06  Kryt náklonu – barrel // X, no stem, R2 ends, grooves, hidden spigot + 14x8 cable passage
# ---------------------------------------------------------------------------
W_N06 = 2.0
END_R = 2.0                  # barrel end edge rounds (spec "edges R2")
GROOVE_X = 3.0               # groove centre distance from each barrel end
BORE_SERVO = 14.0            # −X end wall bore (servo output spline / horn adapter)
OPEN_D = 32.0                # +X end opening (servo insertion, 6703 bearing plug seat)
SPIG_R = 8.8                 # hidden mounting spigot (inside N02: inner wall r >= 9.5)
SPIG_Z0 = 153.0              # spigot bottom (pan-hub flange, 2x M2)
RIB_RI, RIB_RO = 16.9, 17.9  # labyrinth ring rib on the barrel end faces
RIB_H = 0.9                  # protrudes 0.9 beyond the barrel end (0.3 into the cap recess)


def tilt_housing_n06():
    x0, x1 = PX - L_BAR / 2, PX + L_BAR / 2
    t = cyl_x(R_BAR, x0, x1)
    t = t.fillet(END_R, edges_where(t, lambda e: bb(e).size.Z > 2 * R_BAR - 0.1))
    t = check("N06 barrel", t)
    # circumferential grooves 3 mm from each barrel end
    for sx in (-1, 1):
        xc = PX + sx * (L_BAR / 2 - GROOVE_X)
        t = t - ring_x(R_BAR - GROOVE_D, R_BAR + 1, xc - SEAM / 2, xc + SEAM / 2)
    # hollow: cavity r 18 from the −X end wall to the +X end lip; +X lip opening Ø32
    t = t - cyl_x(R_BAR - W_N06, x0 + W_N06, x1 - W_N06)
    t = t - cyl_x(OPEN_D / 2, x1 - W_N06 - 1, x1 + 1)
    t = t - cyl_x(BORE_SERVO / 2, x0 - 1, x0 + W_N06 + 1)            # −X end: servo output bore
    # labyrinth ribs on both end faces, entering the cap recess (the 0.6 gap is not see-through)
    for sx in (-1, 1):
        xe = PX + sx * L_BAR / 2
        rib = ring_x(RIB_RI, RIB_RO, min(xe - sx * 0.3, xe + sx * RIB_H), max(xe - sx * 0.3, xe + sx * RIB_H))
        t = t.fuse(rib)
    t = check("N06 hollow", t.clean())
    # hidden spigot under the barrel (inside N02) + cable passage 14 x 8 (long axis // X)
    z_in = AX_Z - (R_BAR - W_N06) + 0.5
    spig = cyl_z(SPIG_R, SPIG_Z0, z_in)
    spig = spig.fillet(0.4, edges_where(spig, is_circle_at_z(SPIG_R, SPIG_Z0)))
    t = t.fuse(spig).clean()
    sw, sh = TH["cable_slot"]
    with BuildSketch(Plane(origin=(PX, PY, SPIG_Z0 - 1))) as sk:
        SlotOverall(sw, sh)
    t = t - extrude(sk.sketch, z_in - SPIG_Z0 + 3)
    # 2x M2 pilot holes for the pan-hub screws (in the thick wall along Y)
    for sy in (-1, 1):
        t = t - cyl_z(0.8, SPIG_Z0 - 1, SPIG_Z0 + 6, y=PY + sy * 6.6)
    # 2 internal ribs on the −X end wall (servo flange stop) – kept inside the cavity
    for sz in (-1, 1):
        t = t.fuse(Pos(x0 + W_N06 + 1.0, AX_Y, AX_Z + sz * 13.0) * Box(2.2, 6.0, 5.0)
                   & cyl_x(R_BAR - W_N06 + 0.5, x0, x1))
    return check("N06", t.clean())


# ---------------------------------------------------------------------------
# N07  Koncové krytky – domed hub caps (tilt with the head)
# ---------------------------------------------------------------------------
R_CAP, L_CAP, DOME, GAP = CP["d"] / 2, CP["len"], CP["dome"], CP["gap"]
X_CAP0 = L_BAR / 2 + GAP                        # 18.6 inner face
CAP_EDGE_R = 2.5
RECESS_D, RECESS_T = 12.0, 0.5
SPIG_D, SPIG_L = 12.0, 2.4                      # R: spigot into the servo-horn adapter (barrel bore Ø14)
PIN_OD, PIN_ID, PIN_LEN = 17.0, 13.0, 6.0       # L: hollow pin in the 6703 bearing (ID 17)
CABLE_D = 8.0
CAP_REC_R, CAP_REC_T = RIB_RO + 0.3, 1.2        # inner-face recess (0.3 radial / 0.9 axial play to the rib)
CAP_CORE_R, CAP_CORE_Z = 16.7, 3.0              # deep core under the dome (walls 1.5..1.9)
CAP_HUB_R = PIN_OD / 2 + 1.6                    # 10.1 solid hub around the spigot / hollow pin


def cap_local(side: int):
    """Cap in a local frame: axis = +Z, inner face at z=0, dome apex at z=L_CAP."""
    zc = L_CAP - DOME
    c = Solid.make_cylinder(R_CAP, zc)
    rs = (R_CAP ** 2 + DOME ** 2) / (2 * DOME)
    sph = Solid.make_sphere(rs, Plane(origin=(0, 0, L_CAP - rs)))
    dome = sph & Solid.make_cylinder(R_CAP, DOME + 1, Plane(origin=(0, 0, zc)))
    c = c.fuse(dome).clean()
    c = c.fillet(CAP_EDGE_R, edges_where(c, is_circle_at_z(R_CAP, zc)))
    c = c.fillet(0.5, edges_where(c, is_circle_at_z(R_CAP, 0.0)))
    # centre recess Ø12 x 0.5 (depth measured at the recess rim on the dome)
    sag = (RECESS_D / 2) ** 2 / (2 * rs)
    c = c - Solid.make_cylinder(RECESS_D / 2, 2, Plane(origin=(0, 0, L_CAP - sag - RECESS_T)))
    # inner-face recess (cores the cap + receives the barrel labyrinth rib), centre boss left
    core = Solid.make_cylinder(CAP_REC_R, CAP_REC_T + 1, Plane(origin=(0, 0, -1)))
    # deep core (uniform ~1.5-1.9 wall under the dome) with 6 radial ribs to the hub
    core = core.fuse(Solid.make_cylinder(CAP_CORE_R, CAP_CORE_Z + 1, Plane(origin=(0, 0, -1))))
    core = core - Solid.make_cylinder(CAP_HUB_R, 10, Plane(origin=(0, 0, -2)))
    for k in range(6):
        core = core - Rot(0, 0, 30 + 60 * k) * Pos(R_CAP / 2 + 2, 0, 0) * Box(R_CAP, 1.2, 12)
    c = c - core
    if side < 0:      # R: spigot + M2.5 pilot (screw from the head boss)
        sp = Solid.make_cylinder(SPIG_D / 2, SPIG_L + 0.5, Plane(origin=(0, 0, -SPIG_L)))
        sp = sp.fillet(0.4, edges_where(sp, is_circle_at_z(SPIG_D / 2, -SPIG_L)))
        c = c.fuse(sp).clean()
        c = c - Solid.make_cylinder(1.05, 5.0, Plane(origin=(0, 0, L_CAP - 4.5)))
    else:             # L: hollow pin OD17/ID13 + Ø8 cable exit + 2x M2 pilots
        pin = Solid.make_cylinder(PIN_OD / 2, PIN_LEN + 0.5, Plane(origin=(0, 0, -PIN_LEN)))
        pin = pin.fillet(0.5, edges_where(pin, is_circle_at_z(PIN_OD / 2, -PIN_LEN)))
        c = c.fuse(pin).clean()
        c = c - Solid.make_cylinder(PIN_ID / 2, PIN_LEN + 2.5, Plane(origin=(0, 0, -PIN_LEN - 1)))
        c = c - Solid.make_cylinder(CABLE_D / 2, L_CAP + 2, Plane(origin=(0, 0, -1)))
        for sy in (-1, 1):
            c = c - Solid.make_cylinder(0.8, 4.0, Plane(origin=(0, sy * 5.0, L_CAP - 3.5)))
    return check("N07", c)


def cap_n07(side: int):
    """side = -1 -> right cap (−X), +1 -> left cap (+X)."""
    c = cap_local(side)
    return check("N07 placed", Pos(PX + side * X_CAP0, AX_Y, AX_Z) * Rot(0, side * 90, 0) * c)


# ---------------------------------------------------------------------------
def build():
    return [
        PartRec("N01", "Spodný golier", collar_n01(), "black", "neck", "J1", (0, 0, 20),
                note="pevne na trupe; elipsa 52×42, okraj 2.0, nákružok Ø35×1.2, otvor Ø32, "
                     "stredovací krúžok Ø33.7 + 2 kolíky Ø2, lepené VHB"),
        PartRec("N02", "Plast krku", trumpet_n02(), "black", "neck", "J2", (0, 0, 45),
                note="konkávna trúbka r16.5→11.5, stena 2, 2 polovice (delenie YZ), škára 0.5 vpredu/vzadu, "
                     "4 západky na náboj otáčania; otáča sa s hlavou (J2)"),
        PartRec("N06", "Kryt náklonu", tilt_housing_n06(), "black", "neck", "J2", (0, 0, 80),
                note="valec Ø40×36, servo náklonu vnútri (vkladá sa z +X, zátka s ložiskom 6703), "
                     "skrytý čap Ø17.6 na náboj (2× M2), prechod káblov 14×8"),
        PartRec("N07-R", "Koncová krytka pravá", cap_n07(-1), "black", "neck", "J3", (-35, 0, 80),
                note="Ø39×6 klenutá, čap Ø12 do unášača serva, lôžko nálitku hlavy Ø12, skrutka M2.5"),
        PartRec("N07-L", "Koncová krytka ľavá", cap_n07(+1), "black", "neck", "J3", (35, 0, 80),
                note="Ø39×6 klenutá, dutý čap Ø17/13 v ložisku 6703, výstup káblov Ø8 do hlavy"),
    ]


if __name__ == "__main__":
    run_module(build, "neck")
