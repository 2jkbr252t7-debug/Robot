"""
NOVA – ARMS (A01..A05, right arm "-R" on -X, left arm "-L" on +X).
Run:  /opt/venv/cad/bin/python -m nova.cad.arms

Geometry (spec.ARM, v7.3) – built for the LEFT arm (+X) and mirrored about the YZ plane for the right arm.

  * Shoulder axis // X at y = ARM.axis.y, z = ARM.axis.z.
  * Paddle = "egg": two half-ellipsoids sharing the widest section (C1), broad faces toward ±X.
    Built in a LOCAL frame whose origin is the joint point P = (mid_x, axis.y, axis.z); local +x = outward.
    The inner half (toward the torso) has the full half-thickness; the outer half's base surface is thinner by
    PANEL_H so that the raised lens panel restores the spec half-thickness at its crown (envelope = spec).
    The whole paddle is splayed ARM.abduction_deg (bottom outward) about a Y-parallel axis through P.
  * Exact quadric surfaces: every egg is 4 scaled quarter-spheres (rational B-splines, no loft faceting).
  * Split plane = local x = 0 (|x| = mid_x at the joint, rotated with the splay), 0.6 mm seam with a
    0.3 x 45° chamfer on both outer edges (docs/REVIEW_NOTES.md §Škáry):
      A01 outer shell  (white)  local x >= +0.3, raised lens panel 0.6 (inset 3) + 0.4 shadow-gap groove,
                                 tongue 2.5 x 0.7 into the A02 rebate with a 0.3 snap bead along front/back
      A02 inner shell  (white)  local x <= -0.3, rebate + snap groove, boss OD26/ID22.4 on the shoulder axis,
                                 internal hub web with 2x M2 clearance holes on PCD 16 (A06 driver flange)
      A03 tip insert   (rubber) black patch on the inner / lower / front corner.  Boundary = egg ∩ plane through
                                 the spec tips A (front silhouette at the split, z = tip.z_top) and B (under the
                                 bottom, chosen so the patch reaches exactly tip.y_max), tilted TIP_TILT toward
                                 the inner face -> broad crescent on the inner face (R01 far arm / R02), thin
                                 sliver seen past the front edge from outside (R01 near arm), lens-shaped wrap
                                 <= 2 mm past the split.  Seam walls are cut RADIALLY (cone from an inner apex)
                                 so they stand ~perpendicular to the skin (no feather edges); 0.6 seam; captive
                                 flange 1.5 mm under the shell edges, trapped in the A01/A02 parting plane.
    Assembly (docs/REVIEW_NOTES.md §Ruky): A05 into the torso counterbore; driver A06 on the servo spline (axial
    M2 through the Ø23 bore); A04 glued into the A02 boss (spigot Ø22 in Ø22.4); A02 + A04 slid onto A06 (shaft
    Ø14 in the A04 bore, flange Ø20 x 2 in the A04 spigot pocket) and fixed by 2x M2x5 from inside A02 through
    the hub web; A03 placed into A02 from inside; A01 snaps on (tongue + beads).  No visible fasteners.
  * The boss bulges beyond the egg near the top (the egg is only 22.8 wide / 12 mm above the axis at the joint,
    the boss is Ø26).  The boss blend body (revolved, coaxial with the shoulder axis) is therefore added to the
    paddle BEFORE the split, so the seam runs through it without any step; junction filleted.
  * A04 joint cover (black) rotates with the arm, A05 transition ring (black) is fixed in the torso counterbore.
"""
from __future__ import annotations

import math

import numpy as np
from build123d import (Align, Axis, Box, Cylinder, Edge, Face, GeomType, Plane, Pos, Rot, Solid, Sphere, Vector,
                       Vertex, Wire, chamfer, extrude, fillet, mirror, revolve, scale)

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
OFFS_K = (1.85 / 1.8, 1.9 / 1.8, 3.4 / 1.8)   # semi-axis reduction factors of the offset ellipsoids (x, y, z)
PANEL_H = 0.6         # raised lens panel on A01 (outer face)
PANEL_INSET = 3.0     # panel outline inset from the side silhouette
GROOVE_W = 0.4        # shadow-gap groove around the panel foot (width = depth)
LIP_LEN = 2.5         # A01 tongue length past the split plane
LIP_IN = 1.1          # tongue occupies the offset band [LIP_IN, WALL] below the outer surface
REBATE = 1.0          # A02 wall thickness kept at the rebate (lip side clearance 0.1)
TIP_GAP = 0.3         # half-gap A03 <-> shells (0.6 seam)
TIP_TILT = 45.0       # A03 boundary plane: tilted this much from "parallel to local x" toward the inner face
                      # (-> broad crescent on the inner face, ~2 mm lens-shaped wrap past the split on the outer side)
TIP_FLANGE = 1.5      # captive flange of A03 under the shell edges (inside the cavity)
TIP_DEPTH = 3.5       # A03 body depth below the outer surface (offset-egg depth, thicker at the very tip)
TIP_NPTS = 96         # samples of the A03 boundary curve
COVER_FILLET = 1.0
BOSS_X0 = JC["x1"] + 0.1                     # boss end face (0.1 mm off the A04 face -> no coplanar faces)
SPIGOT_X1 = JC["x1"] + JC["spigot_len"]      # 71.5
BORE_X1 = SPIGOT_X1 + 0.2                    # boss bore depth (spigot + 0.2)
BOSS_STRAIGHT = 2.0   # straight Ø26 part of the boss blend body beyond BOSS_X0
BOSS_ROUND = (2.6, 3.4)   # elliptical end round of the boss blend body (along x, along r)
BOSS_FILLET = 1.5     # junction fillet boss <-> egg
WEB_T = 3.0           # internal hub web thickness
# arm driver A06 (docs/REVIEW_NOTES.md): shaft Ø14 through A04, flange Ø20 x 2 with 2x M2 on PCD 16;
# A02 + A04 are fixed to the flange by 2x M2x5 from inside A02 (through the hub web)
A06_FLANGE_D, A06_FLANGE_T, A06_PCD = 20.0, 2.0, 16.0
M2_CLEAR = 2.4        # M2 clearance hole in the hub web
FLANGE_POCKET = (A06_FLANGE_D + 0.4, A06_FLANGE_T + 1.2)   # pocket in the A04 spigot end (Ø, depth incl. screw-tip room)
SNAP_X = -1.4         # local x of the snap bead (middle of the tongue)
SNAP_H = 0.3          # bead height on the tongue (A02 groove is 0.2 deeper / 0.2 wider)
SNAP_Y_MIN = 9.0      # beads only along the front and back edges (|y| >= 9)
SEAM_CHAMFER = 0.3    # 0.3 x 45° on both edges of the visible A01/A02 seam (docs/REVIEW_NOTES.md §Škáry)
SPHERE_ROT = 180.0    # parametric seam of the base sphere moved to the inner side (OCC chamfers the A02 seam then)
LOC = Pos(MID, AX_Y, AX_Z) * Rot(0, -SPLAY, 0)   # local -> world (left arm)
BIG = 400.0


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

def octant_egg(a_out: float, a_in: float, b: float, c_top: float, c_bot: float, zc: float = ZC) -> Solid:
    """Egg of 4 scaled quarter-spheres: x>0 semi-axis a_out, x<0 a_in, y semi-axis b,
    z semi-axis c_top above / c_bot below the shared widest section at local z = zc."""
    sph = Rot(0, 0, SPHERE_ROT) * Sphere(1.0)
    egg = None
    for sx, a in ((1, a_out), (-1, a_in)):
        for sz, c in ((1, c_top), (-1, c_bot)):
            q = sph & (Pos(sx * 1.0, 0, sz * 1.0) * Box(2, 4, 2))
            q = scale(q, by=(a, b, c))
            egg = q if egg is None else egg.fuse(q)
    egg = egg.clean()
    return Pos(0, 0, zc) * egg


def egg_shrunk(d: float) -> Solid:
    """Approximate inward offset of the base egg (outer half without the panel) by d.
    Per-axis factors compensate the slender tips (a plain "semi-axes - d" ellipsoid thins the wall to
    ~0.74 d near the top/bottom); with OFFS_K the cavity (d = WALL) keeps a wall of >= ~0.97 WALL."""
    kx, ky, kz = OFFS_K
    return octant_egg(HT - PANEL_H - d * kx, HT - d * kx, HW - d * ky, C_TOP - d * kz, C_BOT - d * kz)


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


# ---------------------------------------------------------------------------
# A03 tip insert: boundary = (tilted plane through the spec tips) ∩ egg, cut RADIALLY (cone from an inner apex)
# so that the seam walls stand ~perpendicular to the surface (no feather edges on the TPU part or the shells)
# ---------------------------------------------------------------------------

def _semi(P):
    """Octant semi-axes (a along x, c along z) of the base egg at local points P (..., 3)."""
    a = np.where(P[..., 0] > 0, HT - PANEL_H, HT)
    c = np.where(P[..., 2] > ZC, C_TOP, C_BOT)
    return a, c


def _f(P, d: float = 0.0):
    """Implicit value of egg_shrunk(d) at local points P (< 1 inside)."""
    a, c = _semi(P)
    kx, ky, kz = OFFS_K
    return (P[..., 0] / (a - d * kx)) ** 2 + (P[..., 1] / (HW - d * ky)) ** 2 + \
        ((P[..., 2] - ZC) / (c - d * kz)) ** 2


def _grad(P):
    a, c = _semi(P)
    g = np.stack([P[..., 0] / a ** 2, P[..., 1] / HW ** 2, (P[..., 2] - ZC) / c ** 2], -1)
    return g / np.linalg.norm(g, axis=-1, keepdims=True)


def _tip_plane(yb: float):
    """Plane through tip A (front silhouette at the split, z = tip.z_top) and B (under the bottom at the split,
    local y = yb), tilted TIP_TILT toward the inner face.  Returns (A, B, unit normal toward the A03 side)."""
    za = TIP["z_top"] - AX_Z
    ya = -HW * math.sqrt(1 - ((TIP["z_top"] - EGG["widest_z"]) / C_BOT) ** 2)
    A = np.array([0.0, ya, za])
    B = np.array([0.0, yb, ZC - C_BOT * math.sqrt(1 - (yb / HW) ** 2)])
    d = (B - A) / np.linalg.norm(B - A)
    m = np.array([0.0, -d[2], d[1]])
    if np.dot(m, (A + B) / 2 - np.array([0.0, 0.0, ZC])) < 0:
        m = -m
    t = math.radians(TIP_TILT)
    return A, B, math.cos(t) * m + math.sin(t) * np.array([-1.0, 0.0, 0.0])


def _plane_ring(A, B, n, k: int = 720):
    """Closed curve plane ∩ egg (vectorised bisection along rays in the plane from the section centroid)."""
    e1 = (B - A) / np.linalg.norm(B - A)
    e2 = np.cross(n, e1)
    ps = np.linspace(0, 2 * math.pi, k, endpoint=False)
    dirs = np.cos(ps)[:, None] * e1 + np.sin(ps)[:, None] * e2
    M = (A + B) / 2
    for _ in range(2):                         # 2nd pass from the centroid -> well-spread rays
        lo, hi = np.zeros(k), np.full(k, 40.0)
        for _ in range(48):
            mid = (lo + hi) / 2
            inside = _f(M + mid[:, None] * dirs) < 1
            lo, hi = np.where(inside, mid, lo), np.where(inside, hi, mid)
        pts = M + lo[:, None] * dirs
        M = pts.mean(0)
    return pts, M


def tip_boundary():
    """A03 seam centre-line on the egg surface.  B is chosen so that the curve reaches exactly tip.y_max.
    Returns (points (TIP_NPTS x 3, arc-length spaced), centroid, plane normal)."""
    lo, hi = -6.0, TIP["y_max"]
    for _ in range(30):
        yb = (lo + hi) / 2
        pts, _ = _plane_ring(*_tip_plane(yb), k=360)
        lo, hi = (lo, yb) if pts[:, 1].max() > TIP["y_max"] else (yb, hi)
    A, B, n = _tip_plane(lo)
    pts, cen = _plane_ring(A, B, n)
    seg = np.linalg.norm(np.roll(pts, -1, 0) - pts, axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    idx = np.searchsorted(s, np.linspace(0, s[-1], TIP_NPTS, endpoint=False), side="right") - 1
    return pts[idx], cen, n


def _tangents(P):
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    return t / np.linalg.norm(t, axis=1, keepdims=True)


def tip_offset(P, cen, delta: float):
    """Offset the closed surface curve P by delta along the surface (+ = away from the patch), re-projected."""
    N = _grad(P)
    b = np.cross(_tangents(P), N)
    b /= np.linalg.norm(b, axis=1, keepdims=True)
    b *= np.sign(np.sum(b * (P - cen), axis=1))[:, None]
    Q = P + delta * b
    for _ in range(6):                         # Newton projection back onto the egg surface
        a, c = _semi(Q)
        g = np.stack([2 * Q[:, 0] / a ** 2, 2 * Q[:, 1] / HW ** 2, 2 * (Q[:, 2] - ZC) / c ** 2], -1)
        Q = Q - ((_f(Q) - 1) / np.sum(g * g, axis=1))[:, None] * g
    return Q


def tip_apex(P, cen):
    """Apex of the radial cut: the inner point (>= TIP_DEPTH + 1 deep) that makes the cut surface closest to
    perpendicular to the egg surface along the whole boundary (min-max deviation)."""
    g = np.arange(-3.0, 3.01, 0.5)
    C = np.stack(np.meshgrid(g, np.arange(-4.0, 6.01, 0.5), np.arange(0.0, 16.01, 0.5), indexing="ij"),
                 -1).reshape(-1, 3) + cen
    C = C[_f(C, TIP_DEPTH + 1.0) < 1.0]
    N, T = _grad(P), _tangents(P)
    R = P[None] - C[:, None]
    R /= np.linalg.norm(R, axis=2, keepdims=True)
    K = np.cross(R, T[None])
    K /= np.linalg.norm(K, axis=2, keepdims=True)
    dev = 90.0 - np.degrees(np.arccos(np.clip(np.abs(np.sum(K * N[None], axis=2)), 0, 1)))
    i = int(np.argmin(dev.max(axis=1)))
    return C[i], float(dev[i].max())


def tip_cone(P, O, cen, n) -> Solid:
    """Closed double cone: apex O -> curve P pushed 2.5 mm outside the egg (radially from O) -> far apex."""
    D = P - O
    L = np.linalg.norm(D, axis=1, keepdims=True)
    far = O + D * (1 + 2.5 / L)
    w = Wire([Edge.make_spline([Vector(*p) for p in far], periodic=True)])
    return Solid.make_loft([Vertex(*O), w, Vertex(*(cen + 25.0 * n))], ruled=True)


def boss_blend_body() -> Solid:
    """Revolved body around the shoulder axis (world, left arm): Ø26 from BOSS_X0, then an elliptical
    convex round that dives into the egg before the split plane."""
    r0 = BOSS["od"] / 2
    xs = BOSS_X0 + BOSS_STRAIGHT
    ax = BOSS_ROUND[0]
    pts = [(BOSS_X0, 0.0), (BOSS_X0, r0), (xs, r0)]
    for i in range(1, 25):                       # angular spacing -> dense samples near the steep end
        x = xs + ax * math.sin((math.pi / 2) * i / 24)
        pts.append((x, boss_profile_r(x) if i < 24 else r0 - BOSS_ROUND[1]))
    pts.append((xs + ax, 0.0))
    # sketch in the XZ plane (x along X, second coord = radial along Z), revolve about the X axis
    vecs = [Vector(x, 0, r) for x, r in pts]
    edges = [Edge.make_line(vecs[0], vecs[1]), Edge.make_line(vecs[1], vecs[2]),
             Edge.make_spline(vecs[2:-1]), Edge.make_line(vecs[-2], vecs[-1]), Edge.make_line(vecs[-1], vecs[0])]
    face = Face(Wire(edges))
    body = revolve(face, Axis.X, 360)
    return Pos(0, AX_Y, AX_Z) * body


def snap_band(h_out: float, h_in: float, half_w: float, y_min: float = SNAP_Y_MIN) -> Solid:
    """Offset band of the base egg between depths h_out (outer) and h_in (inner), centred on local x = SNAP_X
    (width 2*half_w), only along the front and back edges (|y| >= y_min): snap beads / grooves."""
    band = (egg_shrunk(h_out) - egg_shrunk(h_in)) & slab_x(SNAP_X - half_w, SNAP_X + half_w)
    sides = Pos(0, y_min + BIG / 4, 0) * Box(BIG, BIG / 2, BIG) + \
        Pos(0, -(y_min + BIG / 4), 0) * Box(BIG, BIG / 2, BIG)
    return band & sides


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
            print(f"  [arms] lens panel rim fillet 0.3 on {len(rim)} edges")
    except Exception as ex:  # keep the crisp edge
        print("  [arms] panel fillet skipped:", ex)
    groove = (outline_prism(PANEL_INSET - GROOVE_W, 0.3, HT + 3) - outline_prism(PANEL_INSET, 0.2, HT + 4)) \
        - egg_shrunk(GROOVE_W)

    # tongue & rebate
    lip = (egg_shrunk(LIP_IN) - cavity) & slab_x(-LIP_LEN, SEAM / 2 + 0.05)
    rebate = egg_shrunk(REBATE) & slab_x(-(LIP_LEN + 0.1), BIG / 2)

    # A03 tip: crescent on the inner / lower / front corner, radial seam walls, captive flange in the cavity
    tp, tcen, tn = tip_boundary()
    apex, dev = tip_apex(tp, tcen)
    h_cut = tip_cone(tip_offset(tp, tcen, TIP_GAP), apex, tcen, tn)                   # cut from the shells
    a03 = (egg & tip_cone(tip_offset(tp, tcen, -TIP_GAP), apex, tcen, tn)) - egg_shrunk(TIP_DEPTH)
    flange = (egg_shrunk(WALL + 0.15) & tip_cone(tip_offset(tp, tcen, TIP_GAP + TIP_FLANGE), apex, tcen, tn)) \
        - egg_shrunk(TIP_DEPTH)
    a03 = a03 + flange
    print(f"  [arms] A03 boundary: local y {tp[:, 1].min():.1f}..{tp[:, 1].max():.1f}, "
          f"z {tp[:, 2].min() + AX_Z:.1f}..{tp[:, 2].max() + AX_Z:.1f} (unsplayed), wrap past split "
          f"{tp[:, 0].max():.2f}; radial cut deviation <= {dev:.0f} deg")

    hs_out = slab_x(SEAM / 2, BIG / 2)       # A01 side
    hs_in = slab_x(-BIG / 2, -SEAM / 2)      # A02 side

    # ---------------- to world ----------------
    W = lambda s: LOC * s
    egg_w, cav_w = W(egg), W(cavity)

    body = egg_w + boss_blend_body()
    body = _fillet_boss_junction(body)
    body -= cyl_x(BOSS["od"] / 2 + 0.3, JC["x0"] - 5, BOSS_X0)          # clearance around A04
    shell = body - cav_w - cyl_x(BOSS["id"] / 2, JC["x0"] - 5, BORE_X1)
    # no tongue/rebate inside the boss zone (the boss + web carry the joint there; avoids sliver faces)
    boss_zone = cyl_x(BOSS["od"] / 2 + 0.5, JC["x0"] - 5, MID + HT)
    # the A01 tongue/beads stop 0.3 before the un-rebated A02 wall inside the boss zone (no face contact)
    boss_zone_lip = cyl_x(BOSS["od"] / 2 + 0.8, JC["x0"] - 5, MID + HT)

    # A02 inner shell
    a02 = _seam_chamfer(shell & W(hs_in), -SEAM / 2) - (W(rebate) - boss_zone) - W(h_cut)
    # hub web: clipped at mid-wall so it fuses into the shell without coincident surfaces
    web = cyl_x(BOSS["od"] / 2 - 0.6, BORE_X1, BORE_X1 + WEB_T) & W(egg_shrunk(WALL / 2)) & W(hs_in)
    a02 = a02 + web
    for sy in (-1, 1):                                                 # 2x M2x5 into the A06 flange
        a02 -= cyl_x(M2_CLEAR / 2, BORE_X1 - 1, BORE_X1 + WEB_T + 1, y=AX_Y + sy * A06_PCD / 2)
    a02 -= W(snap_band(REBATE - SNAP_H - 0.2, REBATE + 0.05, 0.5)) - boss_zone     # snap groove

    # A01 outer shell
    bead = snap_band(LIP_IN - SNAP_H, LIP_IN + 0.05, 0.4, SNAP_Y_MIN + 0.3)   # ends 0.3 inside the groove
    a01 = _seam_chamfer(shell & W(hs_out), SEAM / 2) + (W(lip + bead) - boss_zone_lip) + W(panel)
    a01 -= cav_w                     # the panel solid is thick (envelope ∩ prism) -> re-hollow
    a01 -= W(groove)
    a01 -= W(h_cut)

    a03_w = W(a03)
    return dict(A01=a01, A02=a02, A03=a03_w, A04=cover_a04(), A05=ring_a05())


def _to_local(v) -> np.ndarray:
    q = (LOC.inverse() * Pos(v.X, v.Y, v.Z)).position
    return np.array([q.X, q.Y, q.Z])


def _seam_chamfer(half, x_seam: float):
    """0.3 x 45° chamfer on the OUTER edges of the A01/A02 seam face (local x = x_seam), done right after the
    split (before tongue, panel and A03 cut).  Falls back to the square edge if OCC refuses."""
    sel = []
    for e in half.edges():
        ps = [_to_local(e.position_at(t)) for t in (0.1, 0.5, 0.9)]
        if all(abs(p[0] - x_seam) < 2e-3 for p in ps) and all(_f(p, WALL) > 1.02 for p in ps):
            sel.append(e)
    try:
        out = chamfer(sel, SEAM_CHAMFER)
        if out.is_valid and len(out.solids()) == 1:
            print(f"  [arms] seam chamfer {SEAM_CHAMFER} on {len(sel)} edges (x={x_seam:+.1f}), dV={out.volume - half.volume:.1f}")
            return out
        print("  [arms] seam chamfer rejected (invalid)")
    except Exception as ex:
        print(f"  [arms] seam chamfer failed ({x_seam:+.1f}): {ex}")
    return half


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


def cover_a04():
    """Black joint cover: Ø26 x0..x1 on the shoulder axis, spigot Ø22 x 3 into the A02 boss, bore Ø14."""
    r = JC["od"] / 2
    c = cyl_x(r, JC["x0"], JC["x1"])
    c = fillet(c.edges().filter_by(GeomType.CIRCLE), COVER_FILLET)
    sp = cyl_x(JC["spigot_od"] / 2, JC["x1"] - 0.5, SPIGOT_X1)
    sp = fillet(sp.edges().filter_by(GeomType.CIRCLE).filter_by(lambda e: e.center().X > SPIGOT_X1 - 0.1), 0.4)
    c = c + sp
    c -= cyl_x(JC["bore_d"] / 2, JC["x0"] - 1, SPIGOT_X1 + 1)
    # pocket for the A06 driver flange (+ room for the M2x5 screw tips behind it)
    c -= cyl_x(FLANGE_POCKET[0] / 2, SPIGOT_X1 - FLANGE_POCKET[1], SPIGOT_X1 + 1)
    # soft rounding of the bore mouth on the torso side (servo-horn adapter lead-in)
    mouth = c.edges().filter_by(GeomType.CIRCLE).filter_by(
        lambda e: abs(e.center().X - JC["x0"]) < 0.01 and abs(e.radius - JC["bore_d"] / 2) < 0.01)
    if mouth:
        c = fillet(mouth, 0.5)
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
    A02=("Vnútorná skrupina ruky", "white", "biela vnútorná polovica, náboj Ø26/Ø22.4, nosná stena: 2× M2×5 do príruby unášača A06 (PCD 16)"),
    A03=("Vložka špičky", "rubber", "TPU 85A, vnútorná spodná predná časť (nárazník), príruba zachytená v deliacej rovine A01/A02"),
    A04=("Kryt kĺbu", "black", "Ø26, čap Ø22×3 vlepený do náboja A02, otvor Ø14 pre driek A06, lôžko Ø20.4 pre prírubu A06; otáča sa s ramenom"),
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
