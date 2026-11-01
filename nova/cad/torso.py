"""
NOVA – TORSO (T01..T06), spec v7.3.  Run:  /opt/venv/cad/bin/python -m nova.cad.torso
                                      (add  --check  to print pairwise interference volumes)

Surfaces
  * side shells: superellipse section (spec.TORSO w/d/n) extruded shell_z0..z1, quarter-round top loop
    r_top and bottom loop r_bottom – identical to spec.torso_section(z).  Wall = spec wall.
  * centre band: the same section and top rounding, but front AND back drop STRAIGHT down to z0
    (spec band_apron, outer bottom edge R bottom_fillet) – no undercut, mouldable with a -Z core pull.
  * the black tray T04 (z0 .. z0+h) carries everything: a 4.5 mm black band shows under the side
    shells' R8 rounding (target photo R01), hidden behind the band aprons front and back.

Part split (all seams 0.6 mm with a 0.3 edge break on both sides, every split is done on the SKIN only
so internal ribs survive).  Internal bosses are the interfaces nova/cad/internals.py builds against (T07
frame, 61805, servos, 6702 sleeves) – see the "interfaces" constants block.
  T01  centre band   = band wall ∩ {|x| <= 35-0.3}: front + over the top + down the back (seams x=±35
                       run the full depth, no cross seam on top), open at the bottom (no floor).
                       Neck hole Ø34, 61805 boss (top wall = outer-ring shoulder) + ribs, 2 pan-bracket
                       bosses, LED slot + T09 locating frame, stepped sensor recess + backing pad + ToF/ALS
                       openings, rear-door opening + frame + 2 magnet bosses, 2 band-screw bosses, 4 hooks.
  T02-R/L side shells = shell ∩ {|x| >= 35+0.3} with a 4 mm bottom flange resting on the tray rim:
                       shoulder bore + counterbore, bearing tube (6702 sleeve), servo-frame bosses + web
                       (T07 towers), seam ledges (back the 0.6 mm seam, carry the band edges), 2 tray bosses.
  T03  rear door     = band wall ∩ rounded-rect prism along +Y; exhaust + inlet slots (spec z lists),
                       2 hook tabs (bottom), magnets in T01 (top), 8 x 1 pry groove, debossed wordmark.
  T04  black tray    = superellipse plate, 6x M2.5 countersunk (4 side shells + 2 band), Ø20 cable hole,
                       cored top with pads/ribs, tongues + corner dams behind the band aprons, spacer ring
                       + 3x M3 (nut pockets) on the J1 PCD down to the turntable B05.
  T05  cyan light guide (flush, through the wall + retention flange) ; T06 frosted sensor window
       (flush, 2 mm, stepped recess with a 0.4 mm reveal; ToF zone thinned to 0.8 mm from inside).
STEP: offset wires are re-fitted as plain B-splines (inset_wire) and __main__ verifies that every STEP
re-imports as exactly one solid.
"""
from __future__ import annotations

import math
import os
import sys

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Edge, Face, Locations, Plane, Pos,
                       RectangleRounded, RegularPolygon, Rot, SlotOverall, Solid, Text, Wire, extrude,
                       fillet, offset)

from nova import spec
from nova.cad.common import PartRec, run_module, superellipse_wire

T = spec.TORSO
Z0, Z1 = T["z0"], T["z1"]                 # tray underside .. top of the white shell
ZS = T["shell_z0"]                        # underside of the white side shells
A, B, N = T["w"] / 2, T["d"] / 2, T["n"]
WALL = T["wall"]
R_TOP, R_BOT = T["r_top"], T["r_bottom"]

BAND = T["band"]
HW = BAND["half_w"]                       # nominal seam plane |x| = 35
HS = BAND["seam"] / 2                     # each side of the seam moves by 0.3
APRON = T.get("band_apron", dict(front=True, back=True, bottom_fillet=2.0))

RD = T["rear_door"]
DHS = RD["seam"] / 2
VENTS_TOP, VENTS_LOW = RD["vents"], RD["vents_low"]

TR = T["tray"]
TA, TB, TN = TR["w"] / 2, TR["d"] / 2, TR["n"]
TRAY_TOP = Z0 + TR["h"]                   # 47.5 = ZS (side shells sit on the tray)
SIDE_SCREWS = TR["screw_xy"]
BAND_SCREWS = TR.get("band_screw_xy", [])
J1_R = TR.get("j1_screw_pcd", 32.0) / 2

LED, SEN, SH = T["led"], T["sensor"], T["shoulder"]
NECK_D = T["neck_hole_d"]
PB = spec.NECK["pan_bearing"]             # 61805: OD37 x 7 from z0
assert abs(PB["z0"] + PB["w"] - (Z1 - WALL)) < 1e-6, "61805 top must meet the T01 top-wall underside"

BASE = spec.BASE
B05_TOP = BASE["z1"] - BASE["turntable_recess"] + 0.2 + 1.6   # top of the B05 disc (see base.py)

# --- local design constants (internal / functional details, not shared) -------------------------
FIT = 0.1             # clearance per side lens/window <-> slot
MID = WALL / 2        # internal ribs are clipped at mid-wall depth so they fuse with the skin
GAP = 0.1             # running clearance hook <-> ledge
LEDGE = 1.6           # thickness of seam ledges / door frame
LEDGE_X = (32.6, 38.5)  # |x| span of the side-shell seam ledges (2.1 mm lap under the band edge)
HOOK_T = 1.1          # snap-hook leg thickness
FLANGE = 4.0          # width of the flat bottom flange of the side shells (rests on the tray rim)
TRAY_R = 1.5          # tray outer edge rounding
TRAY_FLOOR = 2.0      # tray floor thickness (cored from the top)
TRAY_RIM = 7.0        # tray rim width (pocket offset)
J1_RING_W = 8.0       # radial width of the spacer ring on the J1 PCD
TONGUE_CLR = 0.3      # clearance tray tongue <-> band apron (inner face and seam ends)
BOSS_D, BOSS_H = 7.0, 10.0      # tray / band screw bosses (M2.5 heat-set insert)
INSERT_D, INSERT_L = 3.6, 6.0
CSK_D, HOLE_D = 5.0, 2.7        # M2.5 countersunk 90°
LED_FLANGE = 0.6      # T05 retention flange thickness (T05 depth = wall + flange = 3.0)
SEN_DEPTH = 2.0       # T06 window depth (flush, sits on a lip of the band)
SEN_REVEAL = 0.4      # reveal step around the sensor window (width = depth)
DOOR_LAP = 3.0        # band frame reaches 3 mm under the door edge
DOOR_FRAME_OUT = 2.0  # frame beyond the door opening (fused to the band skin)
BACK_Y = 30.0         # door frame / magnet bosses exist only behind y >= this (back wall + rounding)
HOOK_Z = (66.0, 112.0)  # snap hooks on the band front edges
DOOR_HOOK_X = 16.3    # door hook tabs (inside the straight part of the door's bottom edge)
MAG_X = 22.0          # door magnets (Ø6 x 2.2 N52)
N01_PIN_X, N01_PIN_D, N01_PIN_L = 22.5, 2.0, 1.4   # N01 collar anti-rotation pins (neck.py) -> holes
PIN_CLR = 0.1         # radial clearance of the pin holes (depth +0.4)
BIG = 200.0

# --- interfaces to the internal parts (nova/cad/internals.py builds T07 etc. AGAINST these) ----------
# internals.py: 61805 (M2) sits in the T01 boss under the top wall; the T07 pan bracket hangs from the T01
# bosses x = ±27 (underside z PB z0 - 6); the T07 towers bolt (M2 along X) to the T02 servo bosses
# (face |x| = 41, y = ±20); the 6702 sleeves press into the T02 Ø23 bore (tube from |x| = 43, the arm
# servos stop at |x| 42.8); tray screws go into T02 bosses (the T07 cross plate clears them).
# (docs/REVIEW_NOTES.md describes a T07 cup / tower layout instead – see open issues; do not change these
#  without changing internals.py.)
PB_WALL = 2.5         # wall of the pan-bearing boss
PAN_SERVO_X = 27.0    # 2 bosses under the top wall for the pan-servo (J2) bracket, M2 pilots
SERVO_Y = 20.0        # T02 servo-frame screw bosses at y = ±20 on the shoulder axis height
SERVO_BOSS_X = 41.0   # |x| of their end faces (T07 tower standoff blocks)
TUBE_X = 43.0         # |x| where the T02 bearing tube starts
PB_BOSS_BELOW = 0.4   # 61805 boss reaches 0.4 below the bearing (z 132.2): clears the W1 cable at the N03 window
TRAY_BOSS_H = 7.0     # T02 tray bosses z 47.5..54.5: clear of the compute module E1 (z >= 55)
SEN_PAD_Y = -42.4     # flat back face of the T01 sensor pad (internals.py T10/T11 datum)
SEAM_EDGE = 0.3       # edge break on both sides of every visible seam (REVIEW_NOTES: 0.3; R instead of
                      # 45° because OCC cannot chamfer these B-spline edges, the round reads the same)
PRY = (8.0, 1.0)      # T03 pry groove in the bottom seam (w x depth)
TOF_ZONE = dict(x=-6.0, w=9.0, h=3.2, t=0.8)   # T06 polished ToF zone, thinned from inside to 0.8
TOF_OPEN = (9.4, 3.4)  # T01 opening behind the ToF zone (VL53L1X 4.9 x 2.5 passes through)
ALS_OPEN = dict(x=6.0, w=5.0, h=3.2)           # T01 opening behind the ambient-light zone (VEML7700)
T09 = dict(w=38.0, h=10.0, clr=0.2, wall=1.4, depth=9.0)   # frame round the front 4 mm of T09 (y >= -38.5)
DAM_T, DAM_Z, DAM_DEPTH = 1.5, 52.0, 9.0      # T04 corner dams behind the apron ends (close the view
                                              # into the torso under the side-shell R8 rounding)
NUT_AF, NUT_H = 5.6, 2.5                      # M3 nut pockets in the tray (J1 screws from below)


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

_cache: dict = {}


def _cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def _rounded_prism(z0, z1, r_bot=0.0):
    w = superellipse_wire(A, B, N, z0, count=96)
    s = extrude(Face(w), z1 - z0, dir=(0, 0, 1))
    s = fillet(s.edges().group_by(Axis.Z)[-1], R_TOP)
    if r_bot:
        s = fillet(s.edges().group_by(Axis.Z)[0], r_bot)
    assert s.is_valid
    return s


def body():
    """Outer solid of the side shells (R8 bottom rounding at shell_z0)."""
    return _cached("body", lambda: _rounded_prism(ZS, Z1, R_BOT))


def off(d: float):
    """body() offset inward by d (d=0 -> body)."""
    if d <= 0:
        return body()

    def mk():
        o = offset(body(), amount=-d)
        assert o.is_valid and o.volume < body().volume - 1000, f"offset {d} failed"
        return o
    return _cached(("off", round(d, 4)), mk)


def skin(d0: float, d1: float):
    """Region between depth d0 and d1 below the side-shell surface."""
    return _cached(("skin", round(d0, 4), round(d1, 4)), lambda: off(d0) - off(d1))


def shell():
    return _cached("shell", lambda: body() - off(WALL))


# --- band: straight drop to z0 front + back -----------------------------------------------------

def band_outer():
    """Outer solid of the centre band: section + top rounding, straight down to z0 (front/back apron)."""
    def mk():
        straight = _rounded_prism(Z0, Z1, APRON["bottom_fillet"])
        if APRON.get("front", True) and APRON.get("back", True):
            return straight
        keep = body()
        if APRON.get("front", True):
            keep = keep + (straight & bx(-BIG, BIG, -BIG, 0, Z0 - 1, Z1 + 1))
        if APRON.get("back", True):
            keep = keep + (straight & bx(-BIG, BIG, 0, BIG, Z0 - 1, Z1 + 1))
        return keep
    return _cached("band_outer", mk)


def _band_ext():
    """Sharp-bottomed band body extended below z0 – reference for inward offsets (no floor)."""
    return _cached("band_ext", lambda: _rounded_prism(Z0 - 6.0, Z1))


def offs(d: float):
    if d <= 0:
        return _band_ext()

    def mk():
        o = offset(_band_ext(), amount=-d)
        assert o.is_valid and o.volume < _band_ext().volume - 1000, f"band offset {d} failed"
        return o
    return _cached(("offs", round(d, 4)), mk)


def sskin(d0: float, d1: float):
    """Region between depth d0 and d1 below the band surface (straight down to/below z0)."""
    return _cached(("sskin", round(d0, 4), round(d1, 4)), lambda: offs(d0) - offs(d1))


def bwall():
    """Full band-surface wall, open at the bottom."""
    return _cached("bwall", lambda: band_outer() - offs(WALL))


# --- generic solids -----------------------------------------------------------------------------

def bx(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, r, z0, z1):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_x(y, z, r, x0, x1):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_y(x, z, r, y0, y1):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def xz_prism(draw, y0: float, y1: float):
    """Prism along Y (y0..y1) of a profile drawn in the XZ plane (sketch coords = (x, z))."""
    with BuildSketch(Plane.XZ) as sk:
        draw()
    return Pos(0, max(y0, y1), 0) * extrude(sk.sketch, abs(y1 - y0))      # Plane.XZ normal = -Y


def stadium_xz(w, h, zc, y0, y1, xc=0.0):
    def d():
        with Locations((xc, zc)):
            SlotOverall(w, h)
    return xz_prism(d, y0, y1)


def rrect_xz(w, h, r, zc, y0, y1, xc=0.0):
    def d():
        with Locations((xc, zc)):
            RectangleRounded(w, h, r)
    return xz_prism(d, y0, y1)


def inset_wire(wire, inset, count=160):
    """Closed XY wire offset inward by `inset`, RE-FITTED as one periodic B-spline.  (Wire.offset_2d
    gives offset-curve edges that do not survive a STEP round trip: every part touched by them
    re-imported as loose shells instead of a solid.)"""
    w = wire.offset_2d(-inset)
    pts = [w.position_at(i / count) for i in range(count)]
    return Wire([Edge.make_spline(pts, periodic=True)])


def contour_prism(wire, z0, z1, inset=0.0):
    """Prism of a closed XY wire (optionally offset inward by `inset`) from z0 to z1."""
    if inset:
        wire = inset_wire(wire, inset)
    f = Face(wire)
    f = Pos(0, 0, z0 - f.center().Z) * f
    return extrude(f, z1 - z0, dir=(0, 0, 1))          # explicit +Z (bottom-face wires point down)


def tray_wire():
    return superellipse_wire(TA, TB, TN, Z0, count=96)


def shell_bottom_wire():
    """Outline of the flat underside of the side shells (exact offset of the section by r_bottom)."""
    return body().faces().sort_by(Axis.Z)[0].outer_wire()


def union_all(shapes):
    out = shapes[0]
    for sh in shapes[1:]:
        out = out + sh
    return out


def fuse(s, p, what=""):
    """Union with a sanity check (OCC can return overlapping results on B-spline skins)."""
    v0, vp = s.volume, p.volume
    r = s + p
    v1 = r.volume
    tol = max(2.0, 0.025 * vp)            # GProp on B-spline skins is only good to ~1-2 %
    if v1 > v0 + vp + tol or v1 < v0 - tol or len(r.solids()) > len(s.solids()) + len(p.solids()):
        print(f"  ! fuse {what}: {v0:.0f} + {vp:.0f} -> {v1:.0f} ({len(r.solids())} solids)")
    return r


def rr_dist(x, z, w, h, r, zc, xc=0.0):
    """Signed distance of (x, z) to a rounded rectangle w x h (corner r) centred on (xc, zc) in XZ."""
    qx = abs(x - xc) - (w / 2 - r)
    qz = abs(z - zc) - (h / 2 - r)
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r


def break_edges(shape, pick, r=SEAM_EDGE, what=""):
    """Round the outer-skin edges selected by pick(edge) (the visible seam edges).  Falls back to the
    unchanged shape if OCC refuses (never silently: prints a warning)."""
    edges = [e for e in shape.edges() if pick(e)]
    if not edges:
        print(f"  ! edge break {what}: no edges selected")
        return shape
    try:
        out = fillet(edges, r)
        assert out.is_valid and len(out.solids()) == len(shape.solids())
        return out
    except Exception as e:  # pragma: no cover
        print(f"  ! edge break {what} failed ({len(edges)} edges): {e}")
        return shape


def on_plane_x(xv, outside):
    """Edge picker: edge lies in the plane x = xv and on the outer skin (outside(point) is True)."""
    def pick(e):
        bb = e.bounding_box()
        return (bb.max.X - bb.min.X < 1e-3 and abs(bb.min.X - xv) < 1e-3
                and outside(e.position_at(0.5)))
    return pick


def on_door_outline(extra, outside):
    """Edge picker: edge lies on the door outline (offset by `extra`) and on the outer skin."""
    w, h, r = RD["w"] + 2 * extra, RD["h"] + 2 * extra, RD["r"] + extra

    def pick(e):
        p = e.position_at(0.5)
        if p.Y < 10 or not outside(p):
            return False
        q = e.position_at(0.25)
        return abs(rr_dist(p.X, p.Z, w, h, r, RD["zc"])) < 0.02 and abs(rr_dist(q.X, q.Z, w, h, r, RD["zc"])) < 0.02
    return pick


def largest(shape, pid):
    sols = shape.solids()
    if len(sols) <= 1:
        return shape
    sols = sorted(sols, key=lambda s: s.volume, reverse=True)
    print(f"  ! {pid}: {len(sols)} solids, dropping fragments {[round(s.volume, 2) for s in sols[1:]]}")
    return sols[0]


# ---------------------------------------------------------------------------
# split regions
# ---------------------------------------------------------------------------

def band_box(extra: float):
    """|x| <= HW + extra (all y, z)."""
    return bx(-(HW + extra), HW + extra, -BIG, BIG, Z0 - 10, Z1 + 10)


def side_box(sx: int, extra: float):
    """sx*x >= HW + extra."""
    return bx(sx * (HW + extra), sx * BIG, -BIG, BIG, Z0 - 10, Z1 + 10)


def door_prism(extra: float):
    return rrect_xz(RD["w"] + 2 * extra, RD["h"] + 2 * extra, RD["r"] + extra, RD["zc"], 5.0, BIG)


def bottom_opening():
    """Opening in the floor of the side shells (leaves a FLANGE-wide flat rim that sits on the tray)."""
    return contour_prism(shell_bottom_wire(), ZS - 1.0, ZS + WALL + 0.5, inset=FLANGE)


MAG_Z = RD["zc"] + RD["h"] / 2 - 4.5      # magnet bosses behind the door top


# ---------------------------------------------------------------------------
# T01 centre band
# ---------------------------------------------------------------------------

def part_t01():
    clip = offs(MID)
    outside = lambda p: not clip.is_inside(p)                     # noqa: E731
    s = bwall() & band_box(-HS)
    # visible edges first (fillets before booleans): 0.3 edge break on the seam edges x = ±(35-0.3),
    # then the rear-door opening (skin only, 0.6 seam) with the same edge break
    for sx in (1, -1):
        s = break_edges(s, on_plane_x(sx * (HW - HS), outside), what=f"T01 seam {sx:+d}")
    s -= door_prism(DHS) & bwall()
    s = break_edges(s, on_door_outline(DHS, outside), what="T01 door opening")

    # ---- internal features (interfaces used by internals.py, see the constants block) ------------
    # pan bearing boss (61805 OD37 x 7) under the top wall – the top wall is the outer-ring shoulder,
    # the Ø34 neck hole clears the inner ring – + ribs + 2 bosses for the pan-servo bracket (T07)
    pb_r = PB["od"] / 2
    s = fuse(s, cyl_z(0, 0, pb_r + PB_WALL, PB["z0"] - PB_BOSS_BELOW, Z1) & clip, "T01 pan boss")
    ribs = [bx(-0.7, 0.7, sy * (pb_r + 1), sy * B, PB["z0"] + 1.0, Z1) for sy in (1, -1)]
    ribs += [bx(sx * (pb_r + 1), sx * (LEDGE_X[0] - 1.6), -0.7, 0.7, PB["z0"] + 1.0, Z1) for sx in (1, -1)]
    ribs += [cyl_z(sx * PAN_SERVO_X, 0, 3.0, PB["z0"] - 6.0, Z1) for sx in (1, -1)]
    s = fuse(s, union_all(ribs) & clip, "T01 top ribs")
    # rear door frame + magnet bosses (both touch the door's inner face)
    # (clipped to the back: the Y-prism of the outline would otherwise also catch the skin layer under
    #  the flat top wall and put a 1.6 mm slab z 138..139.6 into the 61805 / pan-bracket space)
    back = bx(-BIG, BIG, BACK_Y, BIG, Z0 - 1, Z1 + 1)
    s = fuse(s, (door_prism(DHS + DOOR_FRAME_OUT) - door_prism(-DOOR_LAP)) & sskin(WALL, WALL + LEDGE) & back,
             "T01 door frame")
    mags = cyl_y(-MAG_X, MAG_Z, 4.5, 20.0, BIG) + cyl_y(MAG_X, MAG_Z, 4.5, 20.0, BIG)
    s = fuse(s, mags & sskin(WALL, WALL + 4.5) & back, "T01 magnet bosses")
    # locating frame round the front of the chest-LED carrier T09 (38 x 10 x 8, internals.py), sensor pad
    t9w, t9h = T09["w"] + 2 * T09["clr"], T09["h"] + 2 * T09["clr"]
    s = fuse(s, (rrect_xz(t9w + 2 * T09["wall"], t9h + 2 * T09["wall"], 1.0 + T09["wall"], LED["z"], -BIG, -20)
                 - rrect_xz(t9w, t9h, 1.0, LED["z"], -BIG, -20)) & sskin(MID, WALL + T09["depth"]),
             "T01 T09 frame")
    # (flat back face at y = SEN_PAD_Y: the mounting datum of the sensor holder T10 / gasket T11)
    s = fuse(s, rrect_xz(SEN["w"] + 11.0, SEN["h"] + 8.0, 3.0, SEN["z"], -BIG, SEN_PAD_Y) & offs(MID),
             "T01 sensor pad")
    # bosses for the band screws from below through the tray (+ 2 ribs each to the apron wall)
    bb = []
    for (x, y) in BAND_SCREWS:
        bb.append(cyl_z(x, y, BOSS_D / 2, TRAY_TOP, TRAY_TOP + BOSS_H))
        for dx in (-2.4, 2.4):
            bb.append(bx(x + dx - 0.7, x + dx + 0.7, y, math.copysign(B, y), TRAY_TOP, TRAY_TOP + BOSS_H) & clip)
    if bb:
        s = fuse(s, union_all(bb), "T01 band bosses")
    # snap hooks behind the side-shell ledges (front edges)
    d_leg0 = WALL + LEDGE + GAP
    stems, legs = [], []
    for sx in (1, -1):
        for zc in HOOK_Z:
            stems.append(bx(sx * 28.5, sx * (LEDGE_X[0] - 0.3), -BIG, -20, zc - 3.5, zc + 3.5))
            legs.append(bx(sx * 28.5, sx * (HW - HS - 0.2), -BIG, -20, zc - 3.5, zc + 3.5))
    hooks = (union_all(stems) & sskin(MID, d_leg0 + HOOK_T)) + (union_all(legs) & sskin(d_leg0, d_leg0 + HOOK_T))
    s = fuse(s, hooks, "T01 hooks")

    # ---- cuts ---------------------------------------------------------------------------------
    s -= cyl_z(0, 0, NECK_D / 2, Z1 - 6.0, Z1 + 2)
    s -= cyl_z(0, 0, pb_r, PB["z0"] - 2.0, Z1 - WALL)            # bearing seat (shoulder = top wall)
    for sx in (1, -1):
        s -= cyl_z(sx * N01_PIN_X, 0, N01_PIN_D / 2 + PIN_CLR, Z1 - N01_PIN_L - 0.4, Z1 + 1)  # N01 pins
        s -= cyl_z(sx * PAN_SERVO_X, 0, 0.85, PB["z0"] - 7.0, PB["z0"] + 1.0)        # M2 pilots
    s -= stadium_xz(LED["w"], LED["h"], LED["z"], -BIG, -30)      # T05 slot (through)
    s -= stadium_xz(SEN["w"] + 2 * SEN_REVEAL, SEN["h"] + 2 * SEN_REVEAL, SEN["z"], -BIG, -30) & \
        (band_outer() - offs(SEN_REVEAL))                         # reveal step around T06
    s -= stadium_xz(SEN["w"], SEN["h"], SEN["z"], -BIG, -30) & (band_outer() - offs(SEN_DEPTH))  # T06 seat
    # sensor openings through the lip + pad: ToF (VL53L1X passes into the thinned T06 zone) and ALS
    s -= stadium_xz(*TOF_OPEN, SEN["z"], -BIG, -30, xc=TOF_ZONE["x"])
    s -= stadium_xz(ALS_OPEN["w"], ALS_OPEN["h"], SEN["z"], -BIG, -30, xc=ALS_OPEN["x"])
    # internal ribs fused after the opening was cut (top rib, band-boss ribs) must not refill it:
    # re-trim the inner half of the opening skin (the visible edge break at depth <= 0.3 is untouched)
    s -= door_prism(DHS) & sskin(MID - 0.2, WALL + 0.01)
    for x in (-MAG_X, MAG_X):                                     # Ø6 x 2.2 N52 magnets
        s -= cyl_y(x, MAG_Z, 3.0, 20.0, BIG) & sskin(WALL, WALL + 2.2)
    for (x, y) in BAND_SCREWS:
        s -= cyl_z(x, y, INSERT_D / 2, TRAY_TOP - 1, TRAY_TOP + INSERT_L)
    return largest(s, "T01")


# ---------------------------------------------------------------------------
# T02 side shells
# ---------------------------------------------------------------------------

def part_t02(sx: int):
    """sx = -1 -> T02-R (robot right, -X);  +1 -> T02-L."""
    pid = "T02-R" if sx < 0 else "T02-L"
    clip = off(MID)
    s = shell() & side_box(sx, HS)
    s = break_edges(s, on_plane_x(sx * (HW + HS), lambda p: not clip.is_inside(p)), what=pid + " seam")
    s -= bottom_opening()

    zs, ys = SH["z"], SH["y"]
    xw = sx * (A + 2)
    # shoulder: bearing tube around the bore (holds the 6702 sleeve) + servo-frame bosses (T07 towers) + web
    sh = cyl_x(ys, zs, SH["cbore_d"] / 2 + 2.3, sx * TUBE_X, xw)
    for yy in (-SERVO_Y, SERVO_Y):
        sh += cyl_x(ys + yy, zs, 3.2, sx * SERVO_BOSS_X, xw)
    sh += bx(sx * (TUBE_X + 1.0), xw, ys - SERVO_Y, ys + SERVO_Y, zs - 0.8, zs + 0.8)
    s = fuse(s, sh & clip, pid + " shoulder")
    # tray screw bosses (M2.5 heat-set inserts) + double rib to the side wall
    bosses, ribs = [], []
    for (x, y) in SIDE_SCREWS:
        if x * sx < 0:
            continue
        bosses.append(cyl_z(x, y, BOSS_D / 2, ZS, ZS + TRAY_BOSS_H))
        for dy in (-2.4, 2.4):
            ribs.append(bx(x, xw, y + dy - 0.7, y + dy + 0.7, ZS, ZS + TRAY_BOSS_H - 2.0))
    s = fuse(s, union_all(bosses) + (union_all(ribs) & clip), pid + " tray bosses")
    # seam ledges behind the band edges (front, over the top, back): back the 0.6 mm seam, carry the band
    led = bx(sx * LEDGE_X[0], sx * LEDGE_X[1], -BIG, BIG, ZS + R_BOT, Z1 + 1) & skin(WALL, WALL + LEDGE)
    s = fuse(s, led, pid + " ledges")

    # cuts
    s -= cyl_x(ys, zs, SH["bore_d"] / 2, sx * 30.0, sx * (A + 5))
    s -= cyl_x(ys, zs, SH["cbore_d"] / 2, sx * (A - SH["cbore_depth"]), sx * (A + 5))
    for yy in (-SERVO_Y, SERVO_Y):
        s -= cyl_x(ys + yy, zs, 0.85, sx * (SERVO_BOSS_X - 1), sx * (SERVO_BOSS_X + 6.5))   # M2 pilots
    for (x, y) in SIDE_SCREWS:
        if x * sx > 0:
            s -= cyl_z(x, y, INSERT_D / 2, ZS - 1, ZS + TRAY_BOSS_H - 1.0)
    return largest(s, pid)


# ---------------------------------------------------------------------------
# T03 rear door
# ---------------------------------------------------------------------------

def part_t03():
    clip = offs(MID)
    s = bwall() & door_prism(-DHS)
    s = break_edges(s, on_door_outline(-DHS, lambda p: not clip.is_inside(p)), what="T03 outline")
    # pry groove in the bottom seam (opens the 2 magnets; the frame lap behind it is the fulcrum)
    z_bot = RD["zc"] - RD["h"] / 2 + DHS
    s -= rrect_xz(PRY[0], 2 * PRY[1], 0.5, z_bot, 10, BIG)
    for v in (VENTS_TOP, VENTS_LOW):
        for z in v["z"]:
            s -= stadium_xz(v["w"], v["h"], z, 10, BIG)
    # 2 hook tabs at the bottom: stem above the frame's inner edge, leg down behind the frame
    z_in = RD["zc"] - RD["h"] / 2 + DOOR_LAP              # inner edge of the frame (bottom)
    d_leg0 = WALL + LEDGE + GAP
    for xc in (-DOOR_HOOK_X, DOOR_HOOK_X):
        stem = bx(xc - 2, xc + 2, 10, BIG, z_in + 0.4, z_in + 3.4) & sskin(MID, d_leg0 + HOOK_T)
        leg = bx(xc - 2, xc + 2, 10, BIG, z_in - 5.0, z_in + 3.4) & sskin(d_leg0, d_leg0 + HOOK_T)
        s = fuse(s, stem + leg, "T03 hook")
    # 0.3 mm debossed wordmark between the vent groups (reads correctly from behind)
    zt = (max(VENTS_LOW["z"]) + VENTS_LOW["h"] / 2 + min(VENTS_TOP["z"]) - VENTS_TOP["h"] / 2) / 2
    try:
        font = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
        pl = Plane(origin=(0, 0, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
        with BuildSketch(pl) as sk:
            with Locations((0, zt)):
                Text("NOVA", 5.0, font_path=font if os.path.exists(font) else None)
        txt = extrude(sk.sketch, BIG)
        s -= txt & (band_outer() - offs(0.3))
    except Exception as e:  # pragma: no cover - cosmetic only
        print("  (wordmark skipped:", e, ")")
    return largest(s, "T03")


# ---------------------------------------------------------------------------
# T04 black bottom tray
# ---------------------------------------------------------------------------

def part_t04():
    w = tray_wire()
    p = contour_prism(w, Z0, TRAY_TOP)
    p = fillet(p.edges().group_by(Axis.Z)[0], TRAY_R)
    p = fillet(p.edges().group_by(Axis.Z)[-1], TRAY_R)
    # tongues front/back between the seams: fill the gap to the band aprons (0.3 clearance) and locate
    # the band; hidden behind the aprons in every view except from below
    tongue = contour_prism(superellipse_wire(A, B, N, Z0, count=96), Z0, TRAY_TOP, inset=WALL + TONGUE_CLR) & \
        bx(-(HW - HS - TONGUE_CLR), HW - HS - TONGUE_CLR, -BIG, BIG, Z0 - 1, TRAY_TOP + 1)
    p = fuse(p, tongue - contour_prism(w, Z0 - 1, TRAY_TOP + 1, inset=TRAY_R), "T04 tongues")
    # corner dams on the tongue ends: under the side shells' R8 rounding one could otherwise look past
    # the apron ends into the torso; the black dam reads as the tray band running up to the apron (R01)
    xd1 = HW - HS - TONGUE_CLR
    sec = superellipse_wire(A, B, N, Z0, count=96)
    dam_ring = contour_prism(sec, TRAY_TOP - 0.5, DAM_Z, inset=WALL + TONGUE_CLR) - \
        contour_prism(sec, TRAY_TOP - 1, DAM_Z + 1, inset=WALL + TONGUE_CLR + DAM_DEPTH)
    dams = [dam_ring & bx(sx * (xd1 - DAM_T), sx * xd1, -BIG, BIG, Z0, DAM_Z + 1) for sx in (1, -1)]
    p = fuse(p, union_all(dams), "T04 corner dams")
    screws = list(SIDE_SCREWS) + list(BAND_SCREWS)
    # cored from the top (floor TRAY_FLOOR), solid pads under the bosses and around the cable hole
    pocket = contour_prism(w, Z0 + TRAY_FLOOR, TRAY_TOP + 1, inset=TRAY_RIM)
    for (x, y) in screws:
        pocket -= cyl_z(x, y, BOSS_D / 2 + 1.5, Z0, TRAY_TOP + 2)
    pocket -= cyl_z(0, 0, TR["center_hole_d"] / 2 + 4.0, Z0, TRAY_TOP + 2)
    for k in range(3):                      # ribs from the hub ring to the rim (between the J1 pads)
        a = 30 + 120 * k
        pocket -= Pos(0, 0, (Z0 + TRAY_TOP) / 2) * Rot(0, 0, a) * Box(2 * TA, 1.6, TR["h"] + 2)
    p -= pocket
    # M2.5 countersunk screws from below: 4 into the side shells, 2 into the band
    for (x, y) in screws:
        p -= cyl_z(x, y, HOLE_D / 2, Z0 - 1, TRAY_TOP + 1)
        h = (CSK_D - HOLE_D) / 2
        p -= Pos(x, y, Z0 - 0.01) * Solid.make_cone(CSK_D / 2 + 0.01, HOLE_D / 2, h + 0.01)
    p -= cyl_z(0, 0, TR["center_hole_d"] / 2, Z0 - 1, TRAY_TOP + 1)
    # spacer ring down to the turntable disc B05 (closes the 1.2 mm gap evenly – reads as a shadow line,
    # no visible "feet") + 3 M3 clearance holes on the J1 PCD: torso <-> J1 coupling
    p = fuse(p, cyl_z(0, 0, J1_R + J1_RING_W / 2, B05_TOP, Z0 + 0.5) - cyl_z(0, 0, J1_R - J1_RING_W / 2,
                                                                             B05_TOP - 1, Z0 + 1), "T04 ring")
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = J1_R * math.cos(a), J1_R * math.sin(a)
        p -= cyl_z(x, y, 1.6, B05_TOP - 1, TRAY_TOP + 1)
        # hex pocket from the top for the M3 nut (M3x25 from below through B06 / pulley / B05)
        p -= Pos(x, y, TRAY_TOP - NUT_H) * Rot(0, 0, math.degrees(a)) * \
            extrude(RegularPolygon(NUT_AF / math.sqrt(3), 6), NUT_H + 1)
    return largest(p, "T04")


# ---------------------------------------------------------------------------
# T05 light guide, T06 sensor window
# ---------------------------------------------------------------------------

def part_t05():
    lens = stadium_xz(LED["w"] - 2 * FIT, LED["h"] - 2 * FIT, LED["z"], -BIG, -30) & bwall()
    flange = stadium_xz(LED["w"] + 3.0, LED["h"] + 3.0, LED["z"], -BIG, -30) & sskin(WALL, WALL + LED_FLANGE)
    return lens + flange


def part_t06():
    s = stadium_xz(SEN["w"] - 2 * FIT, SEN["h"] - 2 * FIT, SEN["z"], -BIG, -30) & \
        (band_outer() - offs(SEN_DEPTH))
    # dual zone (REVIEW_NOTES): polished ToF window at x = -6 thinned from the inside to 0.8 mm
    tz = TOF_ZONE
    s -= stadium_xz(tz["w"], tz["h"], SEN["z"], -BIG, -30, xc=tz["x"]) & offs(tz["t"])
    return s


# ---------------------------------------------------------------------------

def build():
    J = "J1"
    S = "torso"
    return [
        PartRec("T01", "Stredový pás", part_t01(), "white", S, J, (0, -60, 20),
                note="biely pás |x|≤35 spredu cez vrch dozadu, škáry 0.6; vpredu aj vzadu rovno dole po z0 "
                     "(forma bez podrezania); otvor krku Ø34, lôžko ložiska 61805, rám dvierok, nesie T05/T06"),
        PartRec("T02-R", "Bočný kryt pravý", part_t02(-1), "white", S, J, (-50, 0, 0),
                note="ramenný otvor Ø23 + zapustenie Ø31.4×1.5, lôžko serva, lišty pod škárou, 2× M2.5"),
        PartRec("T02-L", "Bočný kryt ľavý", part_t02(1), "white", S, J, (50, 0, 0),
                note="ramenný otvor Ø23 + zapustenie Ø31.4×1.5, lôžko serva, lišty pod škárou, 2× M2.5"),
        PartRec("T03", "Zadné dvierka", part_t03(), "white", S, J, (0, 70, 0),
                note="60×84 R12, 5 výfukových + 4 nasávacie štrbiny 28×2 (chladenie Pi 5), 2 háčiky + magnety, "
                     "drážka 8×1 na páčenie v spodnej škáre"),
        PartRec("T04", "Spodná vanička trupu", part_t04(), "black", S, J, (0, 0, -40),
                note="viditeľný čierny pás 4.5 mm, 6× M2.5 zápustné, Ø20 káble, jazýčky + rohové zarážky za zásterami, "
                     "dištančný krúžok + 3× M3 (matice vo vaničke) k B05 (J1)"),
        PartRec("T05", "LED svetlovod hrude", part_t05(), "cyan_led", S, J, (0, -90, 0),
                note="PMMA opál 34×4, zarovno s čelom, poistná príruba"),
        PartRec("T06", "Senzorové okienko", part_t06(), "frost", S, J, (0, -90, 0),
                note="23×4, zarovno s čelom, lepené v osadení; zóna ToF 9×3.2 pri x −6 zoslabená na 0.8 mm, "
                     "za ňou VL53L1X, pri x +6 VEML7700"),
    ]


def check_interference(parts):
    print("  interference check (mm^3):")
    bad = 0
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            try:
                v = (a.shape & b.shape).volume
            except Exception as e:  # pragma: no cover
                v = f"err {e}"
            if not isinstance(v, (int, float)) or v > 0.01:
                bad += 1
                print(f"    {a.id} x {b.id}: {v}")
    print(f"  {bad} interfering pairs")


if __name__ == "__main__":
    import time
    t0 = time.time()
    parts = build()
    print(f"  built in {time.time() - t0:.1f}s")
    for p in parts:
        bb = p.shape.bounding_box()
        print(f"  {p.id}: valid={p.shape.is_valid} solids={len(p.shape.solids())} vol={p.shape.volume:.0f} "
              f"bbox_vol={bb.size.X * bb.size.Y * bb.size.Z:.0f}")
    if "--check" in sys.argv:
        check_interference(parts)
    run_module(lambda: parts, "torso")
    # STEP round trip: every exported part must come back as exactly one closed solid
    from build123d import import_step
    from nova.cad.common import OUT
    for p in parts:
        r = import_step(os.path.join(OUT, "step", f"{p.id}.step"))
        n = len(r.solids())
        print(f"  STEP {p.id}: {'ok' if n == 1 else '!! ' + str(n) + ' solids (' + type(r).__name__ + ')'}")
