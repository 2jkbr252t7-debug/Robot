"""
NOVA – NECK (N01, N02, N06, N07-R, N07-L).  Run:  /opt/venv/cad/bin/python -m nova.cad.neck

Spec v7.3 (spec.NECK, spec.TILT_AXIS, spec.PAN_AXIS, docs/REVIEW_NOTES.md).  Kinematics / function:
  N01  Spodný golier      – fixed on the torso top (J1).  Elliptical 52 x 42 sloped flange (outer edge 2.0),
                            concave top rising to a groove line and a raised inner lip Ø35 x 1.2, bore Ø32.
                            Underside cored (1.5 wall) with radial ribs; Ø33.7 locating ring into the torso
                            Ø34 neck hole + 2 anti-rotation pins Ø2; bonded (VHB) to the torso top.
  N02  Plast krku         – ONE-piece cosmetic concave trumpet, r(z) = r_top + (r_bot - r_top) *
                            ((z1 - z)/(z1 - z0))^2, wall 2.  Slid over the pan hub N03 and resting on its
                            Ø30 flange (z 149); 2 key tabs into flange notches keep the saddle aligned;
                            4 crush ribs centre it on the N06 spigot.  The top edge is a saddle trimmed 0.4 mm
                            (static moulded seam) off the barrel so the cone runs into the N06 underside.  J2.
  N06  Kryt náklonu       – horizontal barrel Ø42 x 36 // X on the tilt axis, NO visible stem, wall 2.
                            −X end: window for the SCS0009 tilt servo (top face flush with the barrel end,
                            spline into the Al insert of N07-R), cradle rib + end-stop rib inside.
                            +X end: Ø32 opening (servo / N05 plug with the 6703 bearing, 3 key notches).
                            Hidden Ø18.4 spigot under the barrel (inside N02) down to the N03 hub top (z 149):
                            2x M2.5 through-holes + 14 x 8 cable passage.  0.6 grooves 3 mm from each end,
                            labyrinth ring ribs on both end faces (the 0.6 cap gap is not see-through).  J2.
  N07-R/L Koncové krytky  – Ø41 x 6 domed caps, 0.6 gap to the barrel, Ø18 x 5.8 hub (x 24.6 -> 30.4) through
                            the Ø18.4 hole of the head recess wall into the H11 cheek (J3).
                            R: Ø20 pocket for the Al spline insert, hub with 2x M2 + 2x Ø2 pins (PCD 11, = H11).
                            L: integral hollow pin OD17 in the 6703 bearing, Ø13 cable tunnel straight through
                            pin + cap + hub, 2 key notches on the hub end (torque), spring slot on the pin.
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
# N02  Plast krku – one-piece concave trumpet with a saddle top
# ---------------------------------------------------------------------------
K_Z0, K_Z1 = CN["z0"], CN["z1"]
K_RB, K_RT, K_W = CN["r_bottom"], CN["r_top"], CN["wall"]
R_BAR, L_BAR = TH["barrel_d"] / 2, TH["barrel_len"]        # 21, 36
TOP_GAP = 0.4                # N02 saddle top edge <-> barrel surface (static moulded seam 0.4)
N03_FLANGE_R = 15.0          # N03 hub flange Ø30 x 1.5 at z 147.5..149 (REVIEW_NOTES) – N02 rests on it
N03_FLANGE_Z0 = K_Z0 - 1.5
KEY_W, KEY_R0 = 3.0, 12.9    # 2 key tabs (±X) hanging into notches of the N03 flange
SKIRT_T, SKIRT_L = 0.6, 1.0  # skirt r 15.05..15.65, z 148..149 (0.35 radial play to the N01 bore Ø32)
SPIG_R = 9.2                 # N06 hidden spigot radius: must pass the N02 top opening (min inner r 9.67)
#                              downward during assembly -> 0.47 clearance, taken up by the crush ribs
CRUSH_T = 0.8                # 4 crush ribs centring N02 on the spigot


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


def cone_r_in(z):
    """Inner wall radius at height z (interpolated from the normal-offset points)."""
    pts = [cone_inner_pt(K_Z0 + (K_Z1 - K_Z0) * i / 64) for i in range(65)]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return pts[0][0] if z < pts[0][1] else pts[-1][0]


def trumpet_n02():
    n = 32
    zs = [K_Z0 + (K_Z1 - K_Z0) * i / n for i in range(n + 1)]
    out_pts = [Vector(PX + cone_r(z), PY, z) for z in zs]
    inn = [cone_inner_pt(z) for z in zs]
    (r0, z0), (r1, z1) = inn[0], inn[1]
    r_in_bot = r0 + (r1 - r0) * (K_Z0 - z0) / (z1 - z0)          # inner offset extended to z = K_Z0
    inn = [(r_in_bot, K_Z0)] + [p for p in inn if K_Z0 + 0.05 < p[1] < K_Z1 - 0.05] + [(K_RT - K_W, K_Z1)]
    in_pts = [Vector(PX + r, PY, z) for r, z in reversed(inn)]
    e_out = Edge.make_spline(out_pts)
    e_top = Edge.make_line(out_pts[-1], in_pts[0])
    e_in = Edge.make_spline(in_pts)
    e_bot = Edge.make_line(in_pts[-1], out_pts[0])
    s = check("N02 rev", revolve_profile([e_out, e_top, e_in, e_bot]))
    s = s.fillet(0.3, edges_where(s, is_circle_at_z(K_RB, K_Z0)))
    s = s.fillet(0.2, edges_where(s, is_circle_at_z(r_in_bot, K_Z0)))
    # saddle top: trimmed by the barrel cylinder grown by TOP_GAP -> the cone runs into the barrel
    s = check("N02 saddle", s - cyl_x(R_BAR + TOP_GAP, PX - L_BAR, PX + L_BAR))
    try:   # 0.3 break on the outer saddle edge (seam edge chamfer per REVIEW_NOTES)
        sad = edges_where(s, lambda e: bb(e).max.Z > K_Z0 + 8 and bb(e).size.Z > 1.0
                          and max(bb(e).size.X, bb(e).size.Y) > 2 * cone_r(K_Z1) - 0.2)
        s2 = s.fillet(0.3, sad)
        if s2.is_valid and abs(s2.volume - s.volume) < 5:
            s = s2
    except Exception:
        pass
    # locating skirt on the N03 flange OD (also closes the line of sight through the 0.5 gap to N01)
    sk = ring_z(N03_FLANGE_R + 0.05, N03_FLANGE_R + 0.05 + SKIRT_T, K_Z0 - SKIRT_L, K_Z0 + 0.5)
    sk = sk.fillet(0.2, edges_where(sk, lambda e: abs(bb(e).max.Z - (K_Z0 - SKIRT_L)) < 0.02))
    s = s.fuse(sk).clean()
    # 2 key tabs at ±X hanging into notches of the N03 flange (keep the saddle aligned to the barrel)
    for sx in (1, -1):
        r_mid = (KEY_R0 + r_in_bot + 0.4) / 2
        tab = Pos(PX + sx * r_mid, PY, (N03_FLANGE_Z0 + 0.2 + K_Z0 + 0.6) / 2) * \
            Box(r_in_bot + 0.4 - KEY_R0, KEY_W, K_Z0 + 0.6 - (N03_FLANGE_Z0 + 0.2))
        s = s.fuse(tab)
    # 4 crush ribs inside (45°, 135°…) touching the N06 spigot (line-to-line + 0.05)
    zr0, zr1 = K_Z0 + 3.0, K_Z0 + 9.0
    r_out = cone_r_in(zr1) + 0.6
    for k in range(4):
        rib = Pos(PX, PY, (zr0 + zr1) / 2) * Rot(0, 0, 45 + 90 * k) * \
            Pos((SPIG_R + 0.05 + r_out) / 2, 0, 0) * Box(r_out - SPIG_R - 0.05, CRUSH_T, zr1 - zr0)
        s = s.fuse(rib & cone_solid_outer())
    return check("N02", s.clean())


def cone_solid_outer():
    """Solid of revolution bounded by the outer trumpet profile (used to clip internal ribs)."""
    zs = [K_Z0 + (K_Z1 - K_Z0) * i / 32 for i in range(33)]
    pts = [Vector(PX + cone_r(z), PY, z) for z in zs]
    return revolve_profile([Edge.make_spline(pts), Edge.make_line(pts[-1], Vector(PX, PY, K_Z1)),
                            Edge.make_line(Vector(PX, PY, K_Z1), Vector(PX, PY, K_Z0)),
                            Edge.make_line(Vector(PX, PY, K_Z0), pts[0])])


# ---------------------------------------------------------------------------
# N06  Kryt náklonu – barrel // X, no stem, R2 ends, grooves, servo window, hidden spigot
# ---------------------------------------------------------------------------
W_N06 = 2.0
R_IN = R_BAR - W_N06          # 19 (inner Ø38, SCS0009 corner r ~18.5 on the axis)
END_R = 2.0                   # barrel end edge rounds (spec "edges R2")
GROOVE_X = 3.0                # groove centre distance from each barrel end
OPEN_D = 32.0                 # +X end opening (N05 plug spigot Ø32 with the 6703 bearing)
SPIG_Z0 = K_Z0                # spigot bottom = N03 hub top (flange top z 149)
RIB_RI, RIB_RO = 18.0, 18.8   # labyrinth ring rib on the barrel end faces
RIB_H = 0.9                   # protrudes 0.9 beyond the barrel end into the cap recess
# SCS0009 tilt servo (no ears) – shaft on the tilt axis, body up (+Z), top face flush at x = -L/2
SV_W, SV_L, SV_H = 12.1, 23.2, 25.25   # body Y x Z x X
SV_SHAFT = 5.9                # shaft axis distance from the lower body end
SV_CLR = 0.15
CRADLE_X = -6.0               # cradle rib (window = body + clearance)
STOP_X = PX - L_BAR / 2 + SV_H  # end-stop rib face (servo bottom end, x = +7.25)
RIB_T = 1.5
SV_RELIEF_DROP, SV_RELIEF_W = 2.0, 3.4   # servo cable strain relief: 2.0 below the body, 3.4 wide (internals)
SCREW_Y, SCREW_D = 6.4, 2.7   # 2x M2.5 through the spigot into N03
CABLE_DX = 1.0                # cable passage centre shifted +X: the Ø4 bundle (W1-N) runs at x 5.6 over the
#                               off-axis N03 channel (x 2.5..9.5) -> 0.4 clearance in the slot end, wall 1.2
SPOT_D, SPOT_Z = 4.8, 0.4     # flat spot face for the pan heads, 0.4 below r_in at the axis (no break-through)


def servo_window(x0, x1, grow=SV_CLR):
    zlo, zhi = AX_Z - SV_SHAFT - grow, AX_Z + SV_L - SV_SHAFT + grow
    return Pos((x0 + x1) / 2, AX_Y, (zlo + zhi) / 2) * Box(x1 - x0, SV_W + 2 * grow, zhi - zlo)


def tilt_housing_n06():
    x0, x1 = PX - L_BAR / 2, PX + L_BAR / 2
    t = cyl_x(R_BAR, x0, x1)
    t = t.fillet(END_R, edges_where(t, lambda e: bb(e).size.Z > 2 * R_BAR - 0.1))
    t = check("N06 barrel", t)
    # circumferential grooves 3 mm from each barrel end
    for sx in (-1, 1):
        xc = PX + sx * (L_BAR / 2 - GROOVE_X)
        t = t - ring_x(R_BAR - GROOVE_D, R_BAR + 1, xc - SEAM / 2, xc + SEAM / 2)
    # hollow: cavity r 19 between the −X end wall and the +X end lip
    t = t - cyl_x(R_IN, x0 + W_N06, x1 - W_N06)
    # labyrinth ring ribs on both end faces (enter the cap recess)
    for sx in (-1, 1):
        xe = PX + sx * L_BAR / 2
        xa, xb = sorted((xe - sx * 0.3, xe + sx * RIB_H))
        t = t.fuse(ring_x(RIB_RI, RIB_RO, xa, xb))
    # internal ribs: cradle (window = servo body) and end stop (ring r 9..19) – cable notch at the bottom
    cradle = cyl_x(R_IN + 0.5, CRADLE_X - RIB_T / 2, CRADLE_X + RIB_T / 2)
    stop = ring_x(9.0, R_IN + 0.5, STOP_X, STOP_X + RIB_T)
    notch = Pos(PX, AX_Y, AX_Z - R_IN) * Box(2 * L_BAR, 14.0, 2 * (R_IN - 7.0))
    t = t.fuse((cradle + stop) - notch)
    t = check("N06 ribs", t.clean())
    # −X end: servo window through the end wall, the cradle rib and the −X rib ring, plus a notch at the
    # bottom for the cable strain relief that hangs 2.0 under the far end of the servo during insertion
    t = t - servo_window(x0 - 2, CRADLE_X + RIB_T)
    zr0 = AX_Z - SV_SHAFT - SV_RELIEF_DROP - SV_CLR - 0.15
    t = t - Pos((x0 - 2 + CRADLE_X + RIB_T) / 2, AX_Y, (zr0 + AX_Z - SV_SHAFT) / 2) * \
        Box(CRADLE_X + RIB_T - x0 + 2, SV_RELIEF_W + 2 * SV_CLR + 0.3, AX_Z - SV_SHAFT - zr0)
    # +X end: Ø32 opening + 3 key notches for the N05 plug
    t = t - cyl_x(OPEN_D / 2, x1 - W_N06 - 1, x1 + 2)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        t = t - Pos(x1 - 0.6, AX_Y + (OPEN_D / 2) * math.cos(a), AX_Z + (OPEN_D / 2) * math.sin(a)) * \
            Rot(math.degrees(a) - 90, 0, 0) * Box(2.0, 3.0, 1.6)
    t = check("N06 hollow", t)
    # hidden spigot under the barrel (inside N02) down to the N03 hub top + cable passage 14 x 8 (long // X)
    z_in = AX_Z - R_IN + 0.5
    spig = cyl_z(SPIG_R, SPIG_Z0, z_in)
    spig = spig.fillet(0.4, edges_where(spig, is_circle_at_z(SPIG_R, SPIG_Z0)))
    t = t.fuse(spig).clean()
    sw, sh = TH["cable_slot"]
    with BuildSketch(Plane(origin=(PX + CABLE_DX, PY, SPIG_Z0 - 1))) as sk:
        SlotOverall(sw, sh)
    t = t - extrude(sk.sketch, z_in - SPIG_Z0 + 3)
    # 2x M2.5 clearance holes through the spigot + spot faces inside the barrel (screws driven from inside)
    for sy in (-1, 1):
        t = t - cyl_z(SCREW_D / 2, SPIG_Z0 - 1, AX_Z, y=PY + sy * SCREW_Y)
        t = t - cyl_z(SPOT_D / 2, AX_Z - R_IN + SPOT_Z, AX_Z, y=PY + sy * SCREW_Y)
    return check("N06", t.clean())


# ---------------------------------------------------------------------------
# N07  Koncové krytky – domed caps with the Ø18 hub (tilt with the head)
# ---------------------------------------------------------------------------
R_CAP, L_CAP, DOME, GAP = CP["d"] / 2, CP["len"], CP["dome"], CP["gap"]
HUB_R, HUB_L = CP["hub_d"] / 2, CP["hub_len"]
X_CAP0 = L_BAR / 2 + GAP                        # 18.6 inner face
CAP_EDGE_R = 2.5
CAP_REC_R, CAP_REC_T = RIB_RO + 0.5, 1.2        # inner-face recess for the barrel rib (0.5 radial / 0.9 axial)
CAP_CORE_R, CAP_CORE_Z = 18.0, 3.0              # deep core under the dome (walls >= 1.5)
CAP_HUB_IN = 12.0                               # solid centre (Al insert pocket / hollow pin) inside the core
INSERT_D, INSERT_DEPTH = 20.0, 5.0              # R: Al spline insert (25T, servo spline engages 2.9)
PCD_R = 5.5                                     # R hub: 2x M2 + 2x Ø2 pins on PCD 11 (matches the H11 cheek)
# hole angles a in the YZ plane around the tilt axis: dy = r sin a, dz = r cos a (same convention as H11)
HUB_M2_ANG = (90.0, 330.0)                      # M2 pilots Ø1.6 x 5 (screws from the H11 cheek side)
HUB_PIN_ANG = (30.0, 210.0)                     # Ø2 x 3 pin holes (H11 pins Ø1.9 x 2.6)
M2_PILOT_D, M2_PILOT_L = 1.6, 5.0
HUB_PIN_D, HUB_PIN_L = 2.0, 3.0
PIN_OD, PIN_ID = 17.0, 13.0                     # L: hollow pin in the 6703 bearing (ID 17)
PIN_X_END = 9.0                                 # L: pin reaches x = +9 (spring seat x 9.5 .. 12.5)


def yz_to_local(side: int, dy: float, dz: float):
    """Global offset (dy, dz) from the tilt axis -> (x, y) in the cap_local frame.
    cap_n07 places the local frame with Rot(0, side*90, 0): side -1 maps local x -> +Z, side +1 maps
    local x -> -Z; local y stays global Y."""
    return (dz, dy) if side < 0 else (-dz, dy)


def cap_local(side: int):
    """Cap in a local frame: axis = +Z (outward), inner face at z=0, dome apex at z=L_CAP."""
    zc = L_CAP - DOME
    c = Solid.make_cylinder(R_CAP, zc)
    rs = (R_CAP ** 2 + DOME ** 2) / (2 * DOME)
    sph = Solid.make_sphere(rs, Plane(origin=(0, 0, L_CAP - rs)))
    dome = sph & Solid.make_cylinder(R_CAP, DOME + 1, Plane(origin=(0, 0, zc)))
    c = c.fuse(dome).clean()
    c = c.fillet(CAP_EDGE_R, edges_where(c, is_circle_at_z(R_CAP, zc)))
    c = c.fillet(0.5, edges_where(c, is_circle_at_z(R_CAP, 0.0)))
    # Ø18 hub through the head-recess wall to the H11 cheek (end face at L_CAP + HUB_L)
    hub = Solid.make_cylinder(HUB_R, HUB_L + 1.0, Plane(origin=(0, 0, L_CAP - 1.0)))
    hub = hub.fillet(0.5, edges_where(hub, is_circle_at_z(HUB_R, L_CAP + HUB_L)))
    c = c.fuse(hub).clean()
    sag = HUB_R ** 2 / (2 * rs)
    try:
        c2 = c.fillet(0.8, edges_where(c, lambda e: abs(bb(e).size.X - 2 * HUB_R) < 0.1
                                       and abs(bb(e).min.Z - (L_CAP - sag)) < 0.1))
        if c2.is_valid:
            c = c2
    except Exception:
        pass
    # inner face: rib recess + deep core with 6 radial ribs, solid centre
    core = Solid.make_cylinder(CAP_REC_R, CAP_REC_T + 1, Plane(origin=(0, 0, -1)))
    core = core.fuse(Solid.make_cylinder(CAP_CORE_R, CAP_CORE_Z + 1, Plane(origin=(0, 0, -1))))
    core = core - Solid.make_cylinder(CAP_HUB_IN, 10, Plane(origin=(0, 0, -2)))
    for k in range(6):
        core = core - Rot(0, 0, 30 + 60 * k) * Pos(R_CAP / 2 + 3, 0, CAP_REC_T + 6) * Box(R_CAP, 1.2, 12)
    c = c - core
    z_end = L_CAP + HUB_L
    if side < 0:      # R: Al spline insert pocket, hub with 2x M2 pilots + 2x Ø2 pin holes (H11 pattern)
        c = c - Solid.make_cylinder(INSERT_D / 2, INSERT_DEPTH + 1, Plane(origin=(0, 0, -1)))
        for angs, d, ln in ((HUB_M2_ANG, M2_PILOT_D, M2_PILOT_L), (HUB_PIN_ANG, HUB_PIN_D, HUB_PIN_L)):
            for a in angs:
                lx, ly = yz_to_local(side, PCD_R * math.sin(math.radians(a)), PCD_R * math.cos(math.radians(a)))
                c = c - Solid.make_cylinder(d / 2, ln + 0.01, Plane(origin=(lx, ly, z_end - ln)))
    else:             # L: hollow pin OD17 into the 6703, Ø13 cable tunnel, 2 key notches, spring slot
        pin_len = X_CAP0 - PIN_X_END
        pin = Solid.make_cylinder(PIN_OD / 2, pin_len + 0.5, Plane(origin=(0, 0, -pin_len)))
        pin = pin.fillet(0.5, edges_where(pin, is_circle_at_z(PIN_OD / 2, -pin_len)))
        c = c.fuse(pin).clean()
        c = c - Solid.make_cylinder(PIN_ID / 2, pin_len + z_end + 2, Plane(origin=(0, 0, -pin_len - 1)))
        c = c - Pos(0, PIN_OD / 2 - 1.0, -pin_len + 1.5) * Box(0.6, 3.0, 3.2)       # spring inner-end slot
        for sy in (-1, 1):
            c = c - Pos(0, sy * (HUB_R + PIN_ID / 2) / 2, z_end) * Box(3.0, HUB_R - PIN_ID / 2 + 1, 3.0)
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
                note="jeden kus, konkávna trúbka r16.5→11.5, stena 2, sedí na prírube N03 (2 kľúče), "
                     "sedlový horný okraj 0.4 od valca; otáča sa s hlavou (J2)"),
        PartRec("N06", "Kryt náklonu", tilt_housing_n06(), "black", "neck", "J2", (0, 0, 80),
                note="valec Ø42×36 (vnútri Ø38), servo SCS0009 na osi (okno na −X, čelo zarovno), "
                     "otvor Ø32 na +X pre zátku N05 s ložiskom 6703, skrytý čap Ø18.4 na N03 (2× M2.5), "
                     "prechod káblov 14×8"),
        PartRec("N07-R", "Koncová krytka pravá", cap_n07(-1), "black", "neck", "J3", (-35, 0, 80),
                note="Ø41×6 klenutá, náboj Ø18×5.8 do H11 (2× M2 + 2 kolíky Ø2, PCD 11), "
                     "lôžko Al vložky Ø20 s drážkovaním serva"),
        PartRec("N07-L", "Koncová krytka ľavá", cap_n07(+1), "black", "neck", "J3", (35, 0, 80),
                note="Ø41×6 klenutá, náboj Ø18×5.8 do H11 (2 drážky na kľúč), dutý čap Ø17 v ložisku 6703, "
                     "kanál káblov Ø13 skrz"),
    ]


if __name__ == "__main__":
    run_module(build, "neck")
