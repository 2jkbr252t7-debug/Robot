"""
NOVA – TORSO (T01..T06), spec v7.2.  Run:  /opt/venv/cad/bin/python -m nova.cad.torso
                                      (add  --check  to print pairwise interference volumes)

Outer surface of the WHITE shell: superellipse section (spec.TORSO w/d/n) extruded shell_z0..z1,
quarter-round loops r_top (fillet top loop first) and r_bottom – identical to spec.torso_section(z).
Wall = spec wall.  The black tray T04 (z0 .. z0+h) carries the white body, so a 4.5 mm black band shows
under the white shell (target photo R01).

Part split (all seams 0.6 mm, every split is done on the SKIN only so internal ribs survive):
  T01  centre band   = shell ∩ {|x| <= 35-0.3}: front + over the top + down the back (seams x=±35 run
                       the full depth, no cross seam on top).  At the FRONT it drops down over the tray
                       to z0 as an apron that is flush with the tray outline (the tray is notched there).
                       Neck hole, LED slot, stepped sensor recess, rear-door opening + frame, magnet
                       bosses, pan-bearing boss (61805) with ribs, 4 snap hooks behind the side ledges.
  T02-R/L side shells = shell ∩ {|x| >= 35+0.3}: shoulder bore + counterbore, bearing tube, servo-frame
                       bosses, seam ledges (back the 0.6 mm seam, carry the band edges), 2 tray bosses each
                       (M2.5 heat-set inserts) – the tray screws hold the side shells.
  T03  rear door     = shell ∩ rounded-rect prism along +Y; 5 exhaust + 4 inlet slots, 2 hook tabs,
                       0.3 mm debossed wordmark.
  T04  black tray    = superellipse plate, 4x M2.5 countersunk, Ø20 cable hole, cored top, front notch
                       for the T01 apron, 3 spacer pads down to the turntable disc B05.
  T05  cyan light guide (flush, through the wall + retention flange), T06 frosted sensor window (flush,
       2 mm deep, sits in a stepped recess).
"""
from __future__ import annotations

import math
import os
import sys

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Face, Locations, Plane, Pos,
                       RectangleRounded, Rot, SlotOverall, Solid, Text, extrude, fillet, offset)

from nova import spec
from nova.cad.common import PartRec, run_module, superellipse_wire

T = spec.TORSO
Z0, Z1 = T["z0"], T["z1"]                 # tray underside .. top of the white shell
ZS = T["shell_z0"]                        # underside of the white shell
A, B, N = T["w"] / 2, T["d"] / 2, T["n"]
WALL = T["wall"]

BAND = T["band"]
HW = BAND["half_w"]                       # nominal seam plane |x| = 35
HS = BAND["seam"] / 2                     # each side of the seam moves by 0.3

RD = T["rear_door"]
DHS = RD["seam"] / 2
VENTS_TOP, VENTS_LOW = RD["vents"], RD["vents_low"]

TR = T["tray"]
TA, TB, TN = TR["w"] / 2, TR["d"] / 2, TR["n"]
TRAY_TOP = Z0 + TR["h"]                   # 47.5 = ZS (white shell sits on the tray)

LED, SEN, SH = T["led"], T["sensor"], T["shoulder"]
NECK_D = T["neck_hole_d"]
PB = spec.NECK["pan_bearing"]             # 61805: OD37 x 7 at z0

BASE = spec.BASE
B05_TOP = BASE["z1"] - BASE["turntable_recess"] + 0.2 + 1.6   # top of the B05 disc (see base.py)

# --- local design constants (internal / functional details, not shared) -------------------------
FIT = 0.1             # clearance per side lens/window <-> slot
MID = WALL / 2        # internal ribs are clipped at mid-wall depth so they fuse with the skin
GAP = 0.1             # clearance between a ledge and the skin of the neighbouring part
LEDGE = 1.6           # thickness of seam ledges / door frame
LEDGE_X = (32.6, 38.5)  # |x| span of the side-shell seam ledges (lap 2.1 under the band edge)
HOOK_T = 1.1          # snap-hook leg thickness
FLANGE = 4.0          # width of the flat bottom flange of the white shell (rests on the tray rim)
APRON_T = 1.8         # wall of the T01 front apron (flush with the tray outline)
TRAY_CLR = 0.3        # tray notch clearance behind the apron
TRAY_R = 1.5          # tray outer edge rounding
TRAY_FLOOR = 2.0      # tray floor thickness (cored from the top)
TRAY_RIM = 7.0        # tray rim width (pocket offset)
BOSS_D, BOSS_H = 7.0, 10.0      # tray screw bosses on the side shells (M2.5 heat-set insert)
INSERT_D, INSERT_L = 3.6, 6.0
CSK_D, HOLE_D = 5.0, 2.7        # M2.5 countersunk 90°
LED_FLANGE = 0.6      # T05 retention flange thickness (T05 depth = wall + flange = 3.0)
SEN_DEPTH = 2.0       # T06 window depth (flush, sits on a lip of the band)
SEN_APERTURE = (17.0, 2.2)      # ToF/ALS aperture behind the window
DOOR_LAP = 3.0        # band frame reaches 3 mm under the door edge
DOOR_FRAME_OUT = 2.0  # frame beyond the door opening (fused to the band skin)
PB_WALL = 2.5         # wall of the pan-bearing boss
SERVO_Y = 20.0        # servo-frame screw bosses at y = ±20 on the shoulder axis height
BIG = 200.0


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

_cache: dict = {}


def body():
    """Outer solid of the white shell (no wall)."""
    if "body" not in _cache:
        w = superellipse_wire(A, B, N, ZS, count=96)
        s = extrude(Face(w), Z1 - ZS)
        s = fillet(s.edges().group_by(Axis.Z)[-1], T["r_top"])
        s = fillet(s.edges().group_by(Axis.Z)[0], T["r_bottom"])
        assert s.is_valid
        _cache["body"] = s
    return _cache["body"]


def off(d: float):
    """Body offset inward by d (d=0 -> body)."""
    if d <= 0:
        return body()
    key = ("off", round(d, 4))
    if key not in _cache:
        o = offset(body(), amount=-d)
        assert o.is_valid and o.volume < body().volume - 1000, f"offset {d} failed"
        _cache[key] = o
    return _cache[key]


def skin(d0: float, d1: float):
    """Region between depth d0 and d1 below the outer surface (follows the surface exactly)."""
    key = ("skin", round(d0, 4), round(d1, 4))
    if key not in _cache:
        _cache[key] = off(d0) - off(d1)
    return _cache[key]


def shell():
    if "shell" not in _cache:
        _cache["shell"] = body() - off(WALL)
    return _cache["shell"]


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


def contour_prism(wire, z0, z1, inset=0.0):
    """Prism of a closed XY wire (optionally offset inward by `inset`) from z0 to z1."""
    if inset:
        wire = wire.offset_2d(-inset)
    f = Face(wire)
    f = Pos(0, 0, z0 - f.center().Z) * f
    return extrude(f, z1 - z0, dir=(0, 0, 1))          # explicit +Z (bottom-face wires point down)


def tray_wire():
    return superellipse_wire(TA, TB, TN, Z0, count=96)


def shell_bottom_wire():
    """Outline of the flat underside of the white shell (exact offset of the section by r_bottom)."""
    return body().faces().sort_by(Axis.Z)[0].outer_wire()


def Compound_(shapes):
    """Boolean union of a list of (possibly overlapping) solids."""
    out = shapes[0]
    for sh in shapes[1:]:
        out = out + sh
    return out


def fuse(s, p, what=""):
    """Union with a sanity check (OCC sometimes returns overlapping/duplicated results on B-spline skins)."""
    v0, vp = s.volume, p.volume
    r = s + p
    v1 = r.volume
    if v1 > v0 + vp + 1.0 or v1 < v0 - 1.0 or len(r.solids()) > len(s.solids()) + len(p.solids()):
        print(f"  ! fuse {what}: {v0:.0f} + {vp:.0f} -> {v1:.0f} ({len(r.solids())} solids)")
    return r


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
    """Opening in the floor of the white shell (leaves a FLANGE-wide flat rim that sits on the tray)."""
    return contour_prism(shell_bottom_wire(), ZS - 1.0, ZS + WALL + 0.5, inset=FLANGE)


def vent_zs(v):
    return [v["z0"] + i * v["pitch"] for i in range(v["n"])]      # upward from z0


def apron_outer():
    """Front apron of T01 below the white shell: flush with the tray outline, z0 .. into the shell."""
    if "apron" not in _cache:
        p = contour_prism(tray_wire(), Z0, ZS + 6.0)
        p = fillet(p.edges().group_by(Axis.Z)[0], TRAY_R)
        _cache["apron"] = p & bx(-(HW - HS), HW - HS, -BIG, 0.0, Z0 - 1, ZS + 7.0)
    return _cache["apron"]


def apron_inner():
    return contour_prism(tray_wire(), Z0 - 1.0, ZS + WALL + 1.0, inset=APRON_T) & \
        bx(-BIG, BIG, -BIG, 0.0, Z0 - 2, ZS + 10)


def door_frame():
    """Frame behind the rear-door opening (part of T01): the door rests on it."""
    return (door_prism(DHS + DOOR_FRAME_OUT) - door_prism(-DOOR_LAP)) & skin(WALL, WALL + LEDGE)


MAG_Z = RD["zc"] + RD["h"] / 2 - 4.5      # magnet bosses behind the door top
MAG_X = 22.0


# ---------------------------------------------------------------------------
# T01 centre band
# ---------------------------------------------------------------------------

HOOK_Z = (66.0, 112.0)                    # snap hooks on the band front edges


def part_t01():
    outer = body() + apron_outer()
    s = outer - off(WALL)
    s -= apron_inner()                    # no floor at the front: the apron covers the tray front
    s = s & band_box(-HS)
    s -= bottom_opening()

    # ---- internal features --------------------------------------------------------------------
    clip = off(MID)
    # pan bearing boss (61805 OD37 x 7) under the top wall + ribs
    pb_r = PB["od"] / 2
    s = fuse(s, cyl_z(0, 0, pb_r + PB_WALL, PB["z0"] - 1.0, Z1) & clip, "T01 pan boss")
    ribs = None
    for sy in (1, -1):
        r = bx(-0.7, 0.7, sy * (pb_r + 1), sy * B, PB["z0"] + 1.0, Z1)
        ribs = r if ribs is None else ribs + r
    for sx in (1, -1):
        ribs += bx(sx * (pb_r + 1), sx * (LEDGE_X[0] - 1.6), -0.7, 0.7, PB["z0"] + 1.0, Z1)
    s = fuse(s, ribs & clip, "T01 top ribs")
    # rear door frame + magnet bosses (both touch the door's inner face)
    s = fuse(s, door_frame(), "T01 door frame")
    mags = cyl_y(-MAG_X, MAG_Z, 4.5, 20.0, BIG) + cyl_y(MAG_X, MAG_Z, 4.5, 20.0, BIG)
    s = fuse(s, mags & skin(WALL, WALL + 4.5), "T01 magnet bosses")
    # LED light box (rib around the T05 flange), sensor backing pad
    s = fuse(s, (stadium_xz(LED["w"] + 6.6, LED["h"] + 6.6, LED["z"], -BIG, -20)
                 - stadium_xz(LED["w"] + 3.6, LED["h"] + 3.6, LED["z"], -BIG, -20)) & skin(MID, WALL + 5.0),
             "T01 LED box")
    s = fuse(s, rrect_xz(SEN["w"] + 11.0, SEN["h"] + 8.0, 3.0, SEN["z"], -BIG, -20) & skin(MID, WALL + 1.2),
             "T01 sensor pad")
    # snap hooks behind the side-shell ledges (front edges)
    d_leg0 = WALL + LEDGE + GAP
    stems, legs = [], []
    for sx in (1, -1):
        for zc in HOOK_Z:
            stems.append(bx(sx * 28.5, sx * (LEDGE_X[0] - 0.3), -BIG, -20, zc - 3.5, zc + 3.5))
            legs.append(bx(sx * 28.5, sx * (HW - HS - 0.2), -BIG, -20, zc - 3.5, zc + 3.5))
    hooks = (Compound_(stems) & skin(MID, d_leg0 + HOOK_T)) + (Compound_(legs) & skin(d_leg0, d_leg0 + HOOK_T))
    s = fuse(s, hooks, "T01 hooks")

    # ---- cuts ---------------------------------------------------------------------------------
    s -= cyl_z(0, 0, NECK_D / 2, Z1 - 6.0, Z1 + 2)
    s -= cyl_z(0, 0, pb_r, PB["z0"] - 2.0, Z1 - WALL)            # bearing seat (shoulder = top wall)
    s -= stadium_xz(LED["w"], LED["h"], LED["z"], -BIG, -30)      # T05 slot (through)
    s -= stadium_xz(SEN["w"], SEN["h"], SEN["z"], -BIG, -30) & (body() - off(SEN_DEPTH))   # T06 recess
    s -= stadium_xz(*SEN_APERTURE, SEN["z"], -BIG, -30)           # sensor aperture through lip + pad
    s -= door_prism(DHS) & (body() - off(WALL))                   # rear door opening (skin only)
    for x in (-MAG_X, MAG_X):                                     # Ø6 x 2.2 N52 magnets
        s -= cyl_y(x, MAG_Z, 3.0, 20.0, BIG) & skin(WALL, WALL + GAP + 2.2)
    for (x, y) in TR["screw_xy"]:                                 # relief for the side-shell tray bosses
        s -= bx(math.copysign(HW - 3.2, x), math.copysign(HW + 6, x), y - (BOSS_D / 2 + 0.4),
                y + (BOSS_D / 2 + 0.4), ZS - 1, ZS + BOSS_H + 0.5)
    return largest(s, "T01")


# ---------------------------------------------------------------------------
# T02 side shells
# ---------------------------------------------------------------------------

def part_t02(sx: int):
    """sx = -1 -> T02-R (robot right, -X);  +1 -> T02-L."""
    pid = "T02-R" if sx < 0 else "T02-L"
    s = shell() & side_box(sx, HS)
    s -= bottom_opening()

    clip = off(MID)
    zs, ys = SH["z"], SH["y"]
    xw = sx * (A + 2)
    # shoulder: bearing tube around the bore + servo-frame screw bosses + web
    sh = cyl_x(ys, zs, SH["cbore_d"] / 2 + 2.3, sx * 43.0, xw)
    for yy in (-SERVO_Y, SERVO_Y):
        sh += cyl_x(ys + yy, zs, 3.2, sx * 41.0, xw)
    sh += bx(sx * 44.0, xw, ys - SERVO_Y, ys + SERVO_Y, zs - 0.8, zs + 0.8)
    s = fuse(s, sh & clip, pid + " shoulder")
    # tray screw bosses (M2.5 heat-set inserts) + ribs to the side wall and to the front/back wall
    bosses, ribs = [], []
    for (x, y) in TR["screw_xy"]:
        if x * sx < 0:
            continue
        bosses.append(cyl_z(x, y, BOSS_D / 2, ZS, ZS + BOSS_H))
        ribs.append(bx(x, xw, y - 0.8, y + 0.8, ZS, ZS + BOSS_H - 2.0))
        xr = x + sx * 1.2
        ribs.append(bx(xr - 0.8, xr + 0.8, y, math.copysign(B, y), ZS, ZS + BOSS_H - 3.0))
    s = fuse(s, Compound_(bosses) + (Compound_(ribs) & clip), pid + " tray bosses")
    # seam ledges behind the band edges (front, over the top, back): back the 0.6 mm seam, carry the band
    led = bx(sx * LEDGE_X[0], sx * LEDGE_X[1], -BIG, BIG, ZS + 4.5, Z1 + 1) & skin(WALL, WALL + LEDGE)
    s = fuse(s, led, pid + " ledges")

    # cuts
    s -= cyl_x(ys, zs, SH["bore_d"] / 2, sx * 30.0, sx * (A + 5))
    s -= cyl_x(ys, zs, SH["cbore_d"] / 2, sx * (A - SH["cbore_depth"]), sx * (A + 5))
    for yy in (-SERVO_Y, SERVO_Y):
        s -= cyl_x(ys + yy, zs, 0.85, sx * 40.0, sx * 47.5)          # M2 self-tapping pilots
    for (x, y) in TR["screw_xy"]:
        if x * sx > 0:
            s -= cyl_z(x, y, INSERT_D / 2, ZS - 1, ZS + INSERT_L)
    return largest(s, pid)


# ---------------------------------------------------------------------------
# T03 rear door
# ---------------------------------------------------------------------------

def part_t03():
    s = shell() & door_prism(-DHS)
    for v in (VENTS_TOP, VENTS_LOW):
        for z in vent_zs(v):
            s -= stadium_xz(v["w"], v["h"], z, 10, BIG)
    # 2 hook tabs at the bottom: stem above the frame's inner edge, leg down behind the frame
    z_in = RD["zc"] - RD["h"] / 2 + DOOR_LAP              # inner edge of the frame (bottom)
    d_leg0 = WALL + LEDGE + GAP
    for xc in (-16.3, 16.3):
        stem = bx(xc - 2, xc + 2, 10, BIG, z_in + 0.4, z_in + 3.4) & skin(MID, d_leg0 + HOOK_T)
        leg = bx(xc - 2, xc + 2, 10, BIG, z_in - 5.0, z_in + 3.4) & skin(d_leg0, d_leg0 + HOOK_T)
        s = s + stem + leg
    # 0.3 mm debossed wordmark between the vent groups (reads correctly from behind)
    try:
        font = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
        pl = Plane(origin=(0, 0, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
        with BuildSketch(pl) as sk:
            with Locations((0, RD["zc"] - 4.0)):
                Text("NOVA", 5.0, font_path=font if os.path.exists(font) else None)
        txt = extrude(sk.sketch, BIG)
        s -= txt & (body() - off(0.3))
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
    # front notch for the T01 apron (between the seams)
    notch = bx(-(HW + HS), HW + HS, -BIG, 0.0, Z0 - 1, TRAY_TOP + 1) - \
        contour_prism(w, Z0 - 2, TRAY_TOP + 2, inset=APRON_T + TRAY_CLR)
    p -= notch
    # cored from the top (floor TRAY_FLOOR), solid pads under the bosses and around the cable hole
    pocket = contour_prism(w, Z0 + TRAY_FLOOR, TRAY_TOP + 1, inset=TRAY_RIM)
    for (x, y) in TR["screw_xy"]:
        pocket -= cyl_z(x, y, BOSS_D / 2 + 1.5, Z0, TRAY_TOP + 2)
    pocket -= cyl_z(0, 0, TR["center_hole_d"] / 2 + 4.0, Z0, TRAY_TOP + 2)
    for k in range(3):                      # ribs from the hub ring to the rim
        a = math.radians(30 + 120 * k)
        rib = Pos(0, 0, (Z0 + TRAY_TOP) / 2) * Rot(0, 0, math.degrees(a)) * Box(2 * TA, 1.6, TR["h"] + 2)
        pocket -= rib
    p -= pocket
    # M2.5 countersunk screws from below into the side-shell bosses
    for (x, y) in TR["screw_xy"]:
        p -= cyl_z(x, y, HOLE_D / 2, Z0 - 1, TRAY_TOP + 1)
        h = (CSK_D - HOLE_D) / 2
        p -= Pos(x, y, Z0 - 0.01) * Solid.make_cone(CSK_D / 2 + 0.01, HOLE_D / 2, h + 0.01)
    p -= cyl_z(0, 0, TR["center_hole_d"] / 2, Z0 - 1, TRAY_TOP + 1)
    # 3 spacer pads (Ø8) down to the turntable disc B05 + M3 clearance holes: torso <-> J1 coupling
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = 16.0 * math.cos(a), 16.0 * math.sin(a)
        p += cyl_z(x, y, 4.0, B05_TOP, Z0 + 0.5)
        p -= cyl_z(x, y, 1.6, B05_TOP - 1, TRAY_TOP + 1)
    return largest(p, "T04")


# ---------------------------------------------------------------------------
# T05 light guide, T06 sensor window
# ---------------------------------------------------------------------------

def part_t05():
    lens = stadium_xz(LED["w"] - 2 * FIT, LED["h"] - 2 * FIT, LED["z"], -BIG, -30) & (body() - off(WALL))
    flange = stadium_xz(LED["w"] + 3.0, LED["h"] + 3.0, LED["z"], -BIG, -30) & skin(WALL, WALL + LED_FLANGE)
    return lens + flange


def part_t06():
    return stadium_xz(SEN["w"] - 2 * FIT, SEN["h"] - 2 * FIT, SEN["z"], -BIG, -30) & (body() - off(SEN_DEPTH))


# ---------------------------------------------------------------------------

def build():
    J = "J1"
    S = "torso"
    return [
        PartRec("T01", "Stredový pás", part_t01(), "white", S, J, (0, -60, 20),
                note="biely pás |x|≤35 spredu cez vrch dozadu, škáry 0.6; vpredu zástera cez vaničku; "
                     "otvor krku Ø34, lôžko ložiska 61805, rám dvierok, nesie T05/T06"),
        PartRec("T02-R", "Bočný kryt pravý", part_t02(-1), "white", S, J, (-50, 0, 0),
                note="ramenný otvor Ø23 + zapustenie Ø31.4×1.5, lôžko serva, 2 výstupky M2.5 pre vaničku"),
        PartRec("T02-L", "Bočný kryt ľavý", part_t02(1), "white", S, J, (50, 0, 0),
                note="ramenný otvor Ø23 + zapustenie Ø31.4×1.5, lôžko serva, 2 výstupky M2.5 pre vaničku"),
        PartRec("T03", "Zadné dvierka", part_t03(), "white", S, J, (0, 70, 0),
                note="60×76 R12, 5 výfukových + 4 nasávacie štrbiny 28×2 (chladenie Pi 5), 2 háčiky + magnety"),
        PartRec("T04", "Spodná vanička trupu", part_t04(), "black", S, J, (0, 0, -40),
                note="viditeľný čierny pás 4.5 mm, 4× M2.5 zápustné, Ø20 káble, 3 pätky k B05"),
        PartRec("T05", "LED svetlovod hrude", part_t05(), "cyan_led", S, J, (0, -90, 0),
                note="PMMA opál 34×4, zarovno s čelom, poistná príruba"),
        PartRec("T06", "Senzorové okienko", part_t06(), "frost", S, J, (0, -90, 0),
                note="23×4, ToF VL53L1X + VEML7700, zarovno s čelom, lepené v osadení"),
    ]


def check_interference(parts):
    print("  interference check (mm^3):")
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            try:
                v = (a.shape & b.shape).volume
            except Exception as e:  # pragma: no cover
                v = f"err {e}"
            if not isinstance(v, float) or v > 0.01:
                print(f"    {a.id} x {b.id}: {v}")


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
