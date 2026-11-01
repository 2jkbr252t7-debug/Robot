"""
NOVA – ARMS (A01..A05, right arm "-R" on -X, left arm "-L" on +X).
Run:  /opt/venv/cad/bin/python -m nova.cad.arms

Geometry (spec.ARM, v7.2) – built for the LEFT arm (+X) and mirrored about the YZ plane for the right arm.

  * Shoulder axis // X at y = ARM.axis.y, z = ARM.axis.z.
  * Paddle = "egg": two half-ellipsoids sharing the widest section (C1), broad faces toward ±X.
    Built in a LOCAL frame whose origin is the joint point P = (mid_x, axis.y, axis.z); local +x = outward.
    The inner half (toward the torso) has the full half-thickness; the outer half's base surface is thinner by
    PANEL_H so that the raised lens panel restores the spec half-thickness at its crown (envelope = spec).
    The whole paddle is splayed ARM.abduction_deg (bottom outward) about a Y-parallel axis through P.
  * Exact quadric surfaces: every egg is 4 scaled quarter-spheres (rational B-splines, no loft faceting).
  * Split plane = local x = 0 (|x| = mid_x at the joint, rotated with the splay), 0.6 mm seam:
      A01 outer shell  (white)  local x >= +0.3, raised lens panel + 0.4 shadow-gap groove, inner lip (tongue)
      A02 inner shell  (white)  local x <= -0.3, rebate for the lip, boss OD26/ID22.4 on the shoulder axis,
                                 internal hub web (hex pocket + M3 hole for the servo-horn adapter)
      A03 tip insert   (rubber) plane cap of the egg at the inner/lower/front corner + captive plug
  * The boss bulges beyond the egg near the top (the egg is only 22.8 wide / 12 mm above the axis at the joint,
    the boss is Ø26).  The boss blend body (revolved, coaxial with the shoulder axis) is therefore added to the
    paddle BEFORE the split, so the seam runs through it without any step; junction filleted.
  * A04 joint cover (black) rotates with the arm, A05 transition ring (black) is fixed in the torso counterbore.
"""
from __future__ import annotations

import math

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Edge, Face, Plane, Pos, RegularPolygon, Rot,
                       Solid, Sphere, Vector, Wire, extrude, fillet, mirror, revolve, scale)

from nova import spec
from nova.cad.common import PartRec, run_module

ARM = spec.ARM
AX_Y, AX_Z = ARM["axis"]["y"], ARM["axis"]["z"]
EGG = ARM["egg"]
MID = ARM["mid_x"]
SPLAY = ARM["abduction_deg"]
JC = ARM["joint_cover"]
RING = ARM["ring"]
BOSS = ARM["boss"]
TIP = ARM["tip"]

# egg in the local frame (origin = joint point P, z up, +x outward)
ZC = EGG["widest_z"] - AX_Z                 # local z of the widest section (-28)
C_TOP = EGG["top_z"] - EGG["widest_z"]      # 40
C_BOT = EGG["widest_z"] - EGG["bottom_z"]   # 34
HW = EGG["half_w"]                          # 16  (Y)
HT = EGG["half_t"]                          # 8.5 (X)

# --- local design constants (not in spec) ----------------------------------------------------------
SEAM = 0.6            # A01/A02 parting seam (each side moves 0.3)
WALL = 1.8            # shell wall
PANEL_H = 0.6         # raised lens panel on A01 (outer face)
PANEL_INSET = 3.0     # panel outline inset from the side silhouette
GROOVE_W = 0.4        # shadow-gap groove around the panel foot (width = depth)
LIP_LEN = 2.5         # A01 tongue length past the split plane
LIP_IN, LIP_OUT = 1.1, 1.8   # tongue occupies offset band [1.1, 1.8] below the outer surface
REBATE = 1.0          # A02 wall thickness kept at the rebate (lip side clearance 0.1)
TIP_GAP = 0.3         # half-gap A03 <-> shells
TIP_PAST_SPLIT = 2.0  # A03 wraps this far past the split plane onto the outer half
TIP_SAG = 4.0         # inward bulge of the crescent boundary arc
PLUG = 3.5            # A03 captive plug depth into the cavity
COVER_FILLET = 1.0
BOSS_X0 = JC["x1"] + 0.1                     # boss end face (0.1 mm off the A04 face -> no coplanar faces)
SPIGOT_X1 = JC["x1"] + JC["spigot_len"]      # 71.5
BORE_X1 = SPIGOT_X1 + 0.2                    # boss bore depth (spigot + 0.2)
BOSS_STRAIGHT = 2.0   # straight Ø26 part of the boss blend body beyond BOSS_X0
BOSS_ROUND = (2.6, 3.4)   # elliptical end round of the boss blend body (along x, along r)
BOSS_FILLET = 1.2     # junction fillet boss <-> egg
WEB_T = 1.6           # internal hub web thickness
HEX_AF, HEX_DEPTH = 8.0, 1.0
LOC = Pos(MID, AX_Y, AX_Z) * Rot(0, -SPLAY, 0)   # local -> world (left arm)
BIG = 400.0


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

def octant_egg(a_out: float, a_in: float, b: float, c_top: float, c_bot: float, zc: float = ZC) -> Solid:
    """Egg of 4 scaled quarter-spheres: x>0 semi-axis a_out, x<0 a_in, y semi-axis b,
    z semi-axis c_top above / c_bot below the shared widest section at local z = zc."""
    sph = Sphere(1.0)
    egg = None
    for sx, a in ((1, a_out), (-1, a_in)):
        for sz, c in ((1, c_top), (-1, c_bot)):
            q = sph & (Pos(sx * 1.0, 0, sz * 1.0) * Box(2, 4, 2))
            q = scale(q, by=(a, b, c))
            egg = q if egg is None else egg.fuse(q)
    egg = egg.clean()
    return Pos(0, 0, zc) * egg


def egg_shrunk(d: float) -> Solid:
    """Approximate inward offset of the base egg (outer half without the panel) by d."""
    return octant_egg(HT - PANEL_H - d, HT - d, HW - d, C_TOP - d, C_BOT - d)


def slab_x(x0: float, x1: float) -> Solid:
    """Local half-space slab x0 <= x <= x1 (large in y, z)."""
    return Pos((x0 + x1) / 2, 0, 0) * Box(x1 - x0, BIG, BIG)


def cyl_x(r: float, x0: float, x1: float, y: float = AX_Y, z: float = AX_Z) -> Solid:
    """World cylinder along X from x0 to x1 (x0 < x1)."""
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def silhouette_offset_pts(inset: float, n: int = 160):
    """Side silhouette of the egg (local YZ plane) offset inward by `inset` (true offset curve)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c = C_TOP if math.cos(t) >= 0 else C_BOT
        y, z = HW * math.sin(t), c * math.cos(t)
        dy, dz = HW * math.cos(t), -c * math.sin(t)            # tangent
        nx, nz = dz, -dy                                         # normal candidate
        L = math.hypot(nx, nz)
        nx, nz = nx / L, nz / L
        if nx * y + nz * z < 0:                                  # make it point outward
            nx, nz = -nx, -nz
        pts.append(Vector(0, y - inset * nx, ZC + z - inset * nz))
    return pts


def outline_prism(inset: float, x0: float, x1: float) -> Solid:
    """Prism along local +x of the inset silhouette."""
    pts = silhouette_offset_pts(inset)
    w = Wire([Edge.make_spline(pts, periodic=True)])
    f = Face(w)
    return Pos(x0, 0, 0) * extrude(f, x1 - x0, dir=(1, 0, 0))


def tip_circle():
    """A03 crescent boundary in the local YZ plane: circle through
       A = front silhouette point at z_top (spec)  and  B = bottom silhouette point at y = y_max (spec),
    bulging TIP_SAG toward the inside of the paddle (up/back) -> a crescent with pointed tips."""
    za = TIP["z_top"] - AX_Z
    ya = -HW * math.sqrt(1 - ((TIP["z_top"] - EGG["widest_z"]) / C_BOT) ** 2)
    yb = TIP["y_max"]
    zb = ZC - C_BOT * math.sqrt(1 - (yb / HW) ** 2)
    cy, cz = (ya + yb) / 2, (za + zb) / 2
    dy, dz = yb - ya, zb - za
    c = math.hypot(dy, dz)
    ny, nz = -dz / c, dy / c                     # chord normal
    if ny * (0 - cy) + nz * (ZC - cz) < 0:      # point it toward the egg centre (inside)
        ny, nz = -ny, -nz
    R = (c * c / 4 + TIP_SAG ** 2) / (2 * TIP_SAG)
    return cy - ny * (R - TIP_SAG), cz - nz * (R - TIP_SAG), R


def tip_zone(grow: float, x_grow: float | None = None) -> Solid:
    """Local solid: crescent cylinder (axis // local x) grown by `grow`, limited to x <= TIP_PAST_SPLIT + x_grow."""
    yc, zc, R = tip_circle()
    xg = grow if x_grow is None else x_grow
    x1 = TIP_PAST_SPLIT + xg
    return Pos(-BIG / 4, yc, zc) * Rot(0, 90, 0) * Cylinder(R + grow, BIG / 4 + x1,
                                                            align=(Align.CENTER, Align.CENTER, Align.MIN))


def boss_blend_body() -> Solid:
    """Revolved body around the shoulder axis (world, left arm): Ø26 from BOSS_X0, then an elliptical
    convex round that dives into the egg before the split plane."""
    r0 = BOSS["od"] / 2
    xs = BOSS_X0 + BOSS_STRAIGHT
    ax, ar = BOSS_ROUND
    pts = [(BOSS_X0, 0.0), (BOSS_X0, r0), (xs, r0)]
    for i in range(1, 25):
        a = (math.pi / 2) * i / 24
        pts.append((xs + ax * math.sin(a), r0 - ar + ar * math.cos(a)))
    pts.append((xs + ax, 0.0))
    # sketch in the XZ plane (x along X, second coord = radial along Z), revolve about the X axis
    vecs = [Vector(x, 0, r) for x, r in pts]
    edges = [Edge.make_line(vecs[0], vecs[1]), Edge.make_line(vecs[1], vecs[2]),
             Edge.make_spline(vecs[2:-1]), Edge.make_line(vecs[-2], vecs[-1]), Edge.make_line(vecs[-1], vecs[0])]
    face = Face(Wire(edges))
    body = revolve(face, Axis.X, 360)
    return Pos(0, AX_Y, AX_Z) * body


def boss_profile_r(x: float) -> float:
    """Outer radius of the boss blend body at world x (left arm)."""
    r0 = BOSS["od"] / 2
    xs = BOSS_X0 + BOSS_STRAIGHT
    ax, ar = BOSS_ROUND
    if x <= xs:
        return r0
    if x >= xs + ax:
        return 0.0
    s = (x - xs) / ax
    return r0 - ar + ar * math.sqrt(max(0.0, 1 - s * s))


def egg_implicit_world(p: Vector) -> float:
    """Implicit value of the splayed base egg (x>0 half without panel) at world point p (<1 inside)."""
    loc_inv = LOC.inverse()
    q = (loc_inv * Pos(p.X, p.Y, p.Z)).position
    a = (HT - PANEL_H) if q.X > 0 else HT
    c = C_TOP if q.Z > ZC else C_BOT
    return (q.X / a) ** 2 + (q.Y / HW) ** 2 + ((q.Z - ZC) / c) ** 2


# ---------------------------------------------------------------------------
# one arm (left, +X)
# ---------------------------------------------------------------------------

def build_left():
    # ---------------- local frame ----------------
    egg = egg_shrunk(0.0)
    cavity = egg_shrunk(WALL)

    # raised lens panel (A01): offset envelope ∩ inset prism, crown = spec half-thickness
    panel_env = octant_egg(HT, HT, HW + PANEL_H, C_TOP + PANEL_H, C_BOT + PANEL_H)
    panel = panel_env & outline_prism(PANEL_INSET, 0.5, HT + 3)
    try:
        rim = [e for e in panel.edges() if e.position_at(0.5).X > 1.0 and e.bounding_box().size.Z > 1.0]
        panel_f = fillet(rim, 0.3)
        if panel_f.is_valid and abs(panel_f.volume - panel.volume) < 0.05 * panel.volume:
            panel = panel_f
    except Exception as ex:  # keep the crisp edge
        print("  [arms] panel fillet skipped:", ex)
    groove = (outline_prism(PANEL_INSET - GROOVE_W, 0.3, HT + 3) - outline_prism(PANEL_INSET, 0.2, HT + 4)) \
        - egg_shrunk(GROOVE_W)

    # tongue & rebate
    lip = (egg_shrunk(LIP_IN) - cavity) & slab_x(-LIP_LEN, SEAM / 2 + 0.05)
    rebate = egg_shrunk(REBATE) & slab_x(-(LIP_LEN + 0.1), BIG / 2)
    keepout = (egg_shrunk(REBATE) - egg_shrunk(LIP_OUT + 0.1)) & slab_x(-(LIP_LEN + 0.1), BIG / 2)

    # A03 tip: crescent at the inner / lower / front edge + captive plug inside the cavity
    h_cut = tip_zone(TIP_GAP)
    a03 = (egg & tip_zone(-TIP_GAP)) + (egg_shrunk(WALL + 0.15) & tip_zone(PLUG))

    hs_out = slab_x(SEAM / 2, BIG / 2)       # A01 side
    hs_in = slab_x(-BIG / 2, -SEAM / 2)      # A02 side

    # ---------------- to world ----------------
    W = lambda s: LOC * s
    egg_w, cav_w = W(egg), W(cavity)

    body = egg_w + boss_blend_body()
    body = _fillet_boss_junction(body)
    body -= cyl_x(BOSS["od"] / 2 + 0.3, JC["x0"] - 5, BOSS_X0)          # clearance around A04
    shell = body - cav_w - cyl_x(BOSS["id"] / 2, JC["x0"] - 5, BORE_X1)

    # A02 inner shell
    a02 = (shell & W(hs_in)) - W(rebate) - W(h_cut)
    web = cyl_x(BOSS["id"] / 2 - 0.4, BORE_X1, BORE_X1 + WEB_T) & egg_w & W(hs_in)
    web -= W(keepout)
    web -= W(h_cut)
    a02 = a02 + web
    a02 -= cyl_x(1.6, BORE_X1 - 1, BORE_X1 + WEB_T + 1)                 # M3 clearance
    a02 -= hex_pocket()

    # A01 outer shell
    spigot_clear = cyl_x(BOSS["id"] / 2, JC["x0"] - 5, BORE_X1 + 0.1)
    a01 = (shell & W(hs_out)) + (W(lip) - spigot_clear) + W(panel)
    a01 -= cav_w                     # the panel solid is thick (envelope ∩ prism) -> re-hollow
    a01 -= W(groove)
    a01 -= W(h_cut)

    a03_w = W(a03)
    return dict(A01=a01, A02=a02, A03=a03_w, A04=cover_a04(), A05=ring_a05())


def _fillet_boss_junction(body):
    """Fillet the intersection edges between the boss blend body and the egg."""
    sel = []
    r0 = BOSS["od"] / 2
    for e in body.edges():
        c = e.position_at(0.5)
        if c.X < BOSS_X0 + 0.2:
            continue
        r = math.hypot(c.Y - AX_Y, c.Z - AX_Z)
        if r < 7.0 or abs(r - boss_profile_r(c.X)) > 0.05:
            continue
        if abs(egg_implicit_world(c) - 1.0) < 0.02:
            sel.append(e)
    if not sel:
        print("  [arms] no boss junction edges found")
        return body
    for rad in (BOSS_FILLET, 0.8, 0.5):
        try:
            out = fillet(sel, rad)
            if out.is_valid and abs(out.volume - body.volume) < 0.05 * body.volume:
                print(f"  [arms] boss junction fillet r={rad} on {len(sel)} edges, dV={out.volume - body.volume:.1f}")
                return out
            print(f"  [arms] boss junction fillet r={rad} rejected (valid={out.is_valid})")
        except Exception as ex:
            print(f"  [arms] boss junction fillet r={rad} failed: {ex}")
    return body


def hex_pocket():
    """Hex pocket on the torso-side face of the hub web (torque transfer from the horn adapter)."""
    with BuildSketch(Plane.YZ.offset(BORE_X1)) as sk:
        RegularPolygon(HEX_AF / math.sqrt(3), 6)
    pk = extrude(sk.sketch, HEX_DEPTH)
    return Pos(0, AX_Y, AX_Z) * pk


def cover_a04():
    """Black joint cover: Ø26 x0..x1 on the shoulder axis, spigot Ø22 x 3 into the A02 boss, bore Ø14."""
    r = JC["od"] / 2
    c = cyl_x(r, JC["x0"], JC["x1"])
    c = fillet(c.edges(), COVER_FILLET)
    sp = cyl_x(JC["spigot_od"] / 2, JC["x1"] - 0.5, SPIGOT_X1)
    sp = fillet(sp.edges().filter_by(lambda e: e.center().X > SPIGOT_X1 - 0.1), 0.4)
    c = c + sp
    c -= cyl_x(JC["bore_d"] / 2, JC["x0"] - 1, SPIGOT_X1 + 1)
    # soft chamfer-like rounding of the bore mouth on the torso side
    try:
        mouth = c.edges().filter_by(lambda e: abs(e.center().X - JC["x0"]) < 0.01 and
                                    abs(e.radius - JC["bore_d"] / 2) < 0.01 if e.geom_type.name == "CIRCLE" else False)
        if mouth:
            c = fillet(mouth, 0.5)
    except Exception:
        pass
    return c


def ring_a05():
    """Black transition ring OD31/ID23 x 2.5 in the torso counterbore, outer face at |x| = x_out."""
    x1 = RING["x_out"]
    x0 = x1 - RING["t"]
    r = cyl_x(RING["od"] / 2, x0, x1) - cyl_x(RING["id"] / 2, x0 - 1, x1 + 1)
    outer = r.edges().filter_by(lambda e: abs(e.center().X - x1) < 0.01)
    try:
        r = fillet(outer, 0.5)
    except Exception:
        pass
    return r


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

NAMES = dict(
    A01=("Vonkajšia skrupina ruky", "white", "biela vonkajšia polovica, šošovkový panel 0.6 mm, jazýček (pero) do A02"),
    A02=("Vnútorná skrupina ruky", "white", "biela vnútorná polovica, náboj Ø26/Ø22.4, nosná stena s hex lôžkom + M3"),
    A03=("Vložka špičky", "rubber", "TPU 85A, vnútorná spodná predná hrana, zachytená zátkou medzi skrupinami"),
    A04=("Kryt kĺbu", "black", "Ø26, čap Ø22×3 do náboja A02, otvor Ø14 pre unášač serva; otáča sa s ramenom"),
    A05=("Prechodový krúžok", "black", "Ø31/Ø23×2.5 v zápustení trupu, pevný (J1)"),
)
EXPLODE_R = dict(A05=(-15, 0, 0), A04=(-35, 0, 0), A02=(-60, 0, 0), A01=(-85, 0, 0), A03=(-60, 0, -25))


def build():
    left = build_left()
    parts = []
    for side in ("R", "L"):
        for key in ("A01", "A02", "A03", "A04", "A05"):
            shp = left[key]
            if side == "R":
                shp = mirror(shp, about=Plane.YZ)
            ex = EXPLODE_R[key]
            if side == "L":
                ex = (-ex[0], ex[1], ex[2])
            nm, mat, note = NAMES[key]
            joint = "J1" if key == "A05" else ("J4" if side == "R" else "J5")
            parts.append(PartRec(f"{key}-{side}", nm, shp, mat, f"arm_{side}", joint, ex, note=note))
    return parts


if __name__ == "__main__":
    run_module(build, "arms")
