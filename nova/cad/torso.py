"""
NOVA – TORSO (T01..T06).  Run:  /opt/venv/cad/bin/python -m nova.cad.torso

Outer surface: superellipse section (spec.TORSO w/d/n) extruded z0..z1, quarter-round top/bottom loops
(fillet r_top, r_bottom) – identical to spec.torso_section(z).  Wall = spec wall.

Part split (all 0.6 mm seams, every cut is a "skin" region so internal ribs survive the split):
  T02 core shell  = shell + internal ribs/bosses  - front panel band - rear door - bottom opening
  T01 front panel = shell ∩ {|x| <= 38} ∩ {y <= -21}   (+ 4 snap hooks behind the T02 ledges)
  T03 rear door   = shell ∩ rounded-rect prism along +Y (+ 2 hook tabs at the bottom, 5 vents at the top)
  T04 bottom plate (black superellipse, 4x M2.5 countersunk, Ø20 cable hole, 3 spacer pads to B05)
  T05 cyan light guide, T06 frosted sensor window – flush with the front surface, retained by a flange.
"""
from __future__ import annotations

import math
import os

from build123d import (Align, Axis, Box, BuildSketch, Cylinder, Face, FontStyle, Locations, Plane, Pos,
                       RectangleRounded, Rot, SlotOverall, Solid, Text, extrude, fillet, chamfer, offset)

from nova import spec
from nova.cad.common import PartRec, run_module, superellipse_wire

T = spec.TORSO
Z0, Z1 = T["z0"], T["z1"]
A, B, N = T["w"] / 2, T["d"] / 2, T["n"]
WALL = T["wall"]

FP = T["front_panel"]
HW, YC = FP["half_w"], FP["y_cut"]
HS = FP["seam"] / 2                     # half seam: each side of the nominal split moves by 0.3

RD = T["rear_door"]
RDV = RD["vents"]
DHS = RD["seam"] / 2

BP = T["bottom_plate"]
LED, SEN, SH = T["led"], T["sensor"], T["shoulder"]
NECK_D = T["neck_hole_d"]

# --- local design constants (not in spec; internal / functional details) -------------------------
FIT = 0.1             # clearance per side between a lens/window and its slot
PLATE_GAP = 0.3       # clearance per side between T04 and the bottom opening of T01/T02
MID = WALL / 2        # internal ribs are clipped at mid-wall depth so they fuse with the shell
LEDGE = 1.6           # thickness of the internal ledges the panel / door rest on
HOOK_T = 1.1          # snap-hook leg thickness (behind the ledges, 0.1 mm play)
LED_DEPTH = 3.4       # T05 total depth (lens through wall + 1 mm retention flange)
SEN_FLANGE = 0.8      # T06 retention flange
BOSS_H = 9.0          # height of the 4 bottom-plate screw bosses above T04
B05_TOP = spec.BASE["z1"] - spec.BASE["turntable_recess"] + 0.2 + 1.6   # top of B05 disc (base.py)
DOOR_LAP = 4.0       # how far the T02 door frame reaches under the door edge
HOOK_Z = (25.0, 67.0) # T01 snap hooks, height above Z0
BIG = 200.0


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

_cache: dict = {}


def body():
    """Outer solid of the torso (no wall)."""
    if "body" not in _cache:
        w = superellipse_wire(A, B, N, Z0, count=96)
        s = extrude(Face(w), Z1 - Z0)
        s = fillet(s.edges().group_by(Axis.Z)[-1], T["r_top"])
        s = fillet(s.edges().group_by(Axis.Z)[0], T["r_bottom"])
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


def bx(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, r, z0, z1):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_x(y, z, r, x0, x1):
    """Cylinder along X from x0 to x1 (any order)."""
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_y(x, z, r, y0, y1):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def xz_prism(draw, y0: float, y1: float):
    """Prism along Y (y0..y1) of a profile drawn in the XZ plane (sketch coords = (x, z))."""
    with BuildSketch(Plane.XZ) as sk:
        draw()
    return Pos(0, y1, 0) * extrude(sk.sketch, y1 - y0)      # Plane.XZ normal = -Y


def stadium_xz(w, h, zc, y0, y1):
    def d():
        with Locations((0, zc)):
            SlotOverall(w, h)
    return xz_prism(d, y0, y1)


def rrect_xz(w, h, r, zc, y0, y1):
    def d():
        with Locations((0, zc)):
            RectangleRounded(w, h, r)
    return xz_prism(d, y0, y1)


def superellipse_prism(a, b, n, z0, z1):
    return extrude(Face(superellipse_wire(a, b, n, z0, count=96)), z1 - z0)


def shell():
    if "shell" not in _cache:
        _cache["shell"] = body() - off(WALL)
    return _cache["shell"]


def largest(shape):
    sols = shape.solids()
    if len(sols) <= 1:
        return shape
    return max(sols, key=lambda s: s.volume)


# ---------------------------------------------------------------------------
# split regions
# ---------------------------------------------------------------------------

def front_box(extra: float):
    """|x| <= HW+extra, y <= YC+extra (all z)."""
    return bx(-(HW + extra), HW + extra, -BIG, YC + extra, Z0 - 10, Z1 + 10)


def door_prism(extra: float):
    return rrect_xz(RD["w"] + 2 * extra, RD["h"] + 2 * extra, RD["r"] + extra, RD["zc"], 5.0, BIG)


def bottom_opening():
    return superellipse_prism(BP["w"] / 2 + PLATE_GAP, BP["d"] / 2 + PLATE_GAP, BP["n"],
                              Z0 - 1.0, Z0 + BP["h"] + 0.1)


def vent_zs():
    return [RDV["z0"] - i * RDV["pitch"] for i in range(RDV["n"])]   # 110, 106 ... downward


# ---------------------------------------------------------------------------
# T02 internals
# ---------------------------------------------------------------------------

def t02_internals():
    parts = []
    clip = off(MID)                       # everything below fuses into the wall at mid depth
    zs = SH["z"]

    for sx in (1, -1):
        # shoulder bearing tube around the Ø23 bore (A05 ring + bearing seat), wall reinforcement
        parts.append(cyl_x(SH["y"], zs, 18.0, sx * 43.0, sx * (A + 2)) & clip)
        # 2 screw bosses for the arm-servo frame (M2 self-tapping, pilot Ø1.7)
        for yy in (-23.0, 23.0):
            parts.append(cyl_x(yy, zs, 3.4, sx * 41.0, sx * (A + 2)) & clip)
        # vertical web joining tube and bosses (stiffens the side wall under the arm load)
        parts.append(bx(min(sx * 45.0, sx * (A + 2)), max(sx * 45.0, sx * (A + 2)), -23.0, 23.0,
                        zs - 0.8, zs + 0.8) & clip)

    # neck tube under the Ø40 hole: carries N01 collar + pan-servo plate, supports T01 top edge
    parts.append(cyl_z(0, 0, 22.5, Z1 - 11.0, Z1 + 1) & clip)

    # 4 bosses for the T04 screws (M2.5 heat-set inserts) + ribs to the side walls + long ribs
    for (x, y) in BP["screw_xy"]:
        sx = 1 if x > 0 else -1
        parts.append(cyl_z(x, y, 3.6, Z0 + BP["h"], (Z0 + BP["h"] + BOSS_H)))
        parts.append(bx(min(x, sx * (A + 2)), max(x, sx * (A + 2)), y - 0.8, y + 0.8,
                        Z0 + BP["h"], (Z0 + BP["h"] + BOSS_H) - 2.0) & clip)
    for x in (-24.0, 24.0):
        parts.append(bx(x - 0.8, x + 0.8, -17.0, 17.0, Z0 + BP["h"], (Z0 + BP["h"] + BOSS_H) - 3.0))

    # ledges under the vertical front-panel seams (x = ±38) and under its top edge (y = -21)
    led = skin(MID, WALL + LEDGE)
    for sx in (1, -1):
        parts.append(bx(min(sx * (HW - 4.5), sx * (HW + 4.0)), max(sx * (HW - 4.5), sx * (HW + 4.0)),
                        -BIG, -8.0, Z0 + 7.0, Z1 - 7.0) & led)
    parts.append(bx(-(HW + 4.0), HW + 4.0, YC - 4.5, YC + 4.5, Z1 - T["r_top"], Z1 + 1) & led)

    # frame behind the rear door opening (door rests on it) + 2 magnet bosses at the top
    ring = door_prism(4.0 + DHS) - door_prism(-(DOOR_LAP + DHS))
    parts.append(ring & led)
    zt = RD["zc"] + RD["h"] / 2 - 3.5
    for x in (-22.0, 22.0):
        mb = cyl_y(x, zt, 4.5, 20.0, BIG) & (off(MID) - off(WALL + 5.0))
        parts.append(mb)
    return parts


def t02_holes(s):
    zs = SH["z"]
    for sx in (1, -1):
        s -= cyl_x(SH["y"], zs, SH["bore_d"] / 2, sx * 30.0, sx * (A + 5))
        s -= cyl_x(SH["y"], zs, SH["cbore_d"] / 2, sx * (A - SH["cbore_depth"]), sx * (A + 5))
        for yy in (-23.0, 23.0):
            s -= cyl_x(yy, zs, 0.85, sx * 40.0, sx * 47.0)
    # neck hole
    s -= cyl_z(0, 0, NECK_D / 2, Z1 - 15.0, Z1 + 2)
    # T04 heat-set insert holes
    for (x, y) in BP["screw_xy"]:
        s -= cyl_z(x, y, 1.8, Z0, Z0 + BP["h"] + 6.0)
    # magnet pockets (Ø6 x 2.2 N52 discs) facing the door
    zt = RD["zc"] + RD["h"] / 2 - 3.5
    for x in (-22.0, 22.0):
        s -= cyl_y(x, zt, 3.0, 20.0, 60.0) & (off(MID) - off(WALL + 2.2))
    return s


def part_t02():
    s = shell()
    for p in t02_internals():
        s = s + p
    s -= front_box(HS) - off(WALL)          # front panel band incl. 0.6 seam (skin only)
    s -= door_prism(DHS) - off(WALL)        # rear door incl. seam
    s -= bottom_opening()
    s = t02_holes(s)
    return largest(s)


# ---------------------------------------------------------------------------
# T01 front panel
# ---------------------------------------------------------------------------

def part_t01():
    s = shell() & front_box(-HS)
    s -= bottom_opening()
    s -= stadium_xz(LED["w"], LED["h"], LED["z"], -BIG, -10)
    s -= stadium_xz(SEN["w"], SEN["h"], SEN["z"], -BIG, -10)
    # 4 snap hooks (stem through the ledge gap, leg behind the T02 ledge)
    for sx in (1, -1):
        for zc in (Z0 + HOOK_Z[0], Z0 + HOOK_Z[1]):
            stem = bx(min(sx * (HW - 8.5), sx * (HW - 5.5)), max(sx * (HW - 8.5), sx * (HW - 5.5)),
                      -BIG, -20, zc - 4, zc + 4) & skin(MID, WALL + LEDGE + 0.1 + HOOK_T)
            leg = bx(min(sx * (HW - 8.5), sx * (HW - 1.5)), max(sx * (HW - 8.5), sx * (HW - 1.5)),
                     -BIG, -20, zc - 4, zc + 4) & skin(WALL + LEDGE + 0.1, WALL + LEDGE + 0.1 + HOOK_T)
            s = s + stem + leg
    return largest(s)


# ---------------------------------------------------------------------------
# T03 rear door
# ---------------------------------------------------------------------------

def part_t03():
    s = shell() & door_prism(-DHS)
    for z in vent_zs():
        s -= stadium_xz(RDV["w"], RDV["h"], z, 10, BIG)
    # 2 hook tabs at the bottom: stem above the frame's inner edge, leg down behind the frame
    z_in = RD["zc"] - RD["h"] / 2 + DOOR_LAP + DHS          # inner edge of the T02 frame (bottom)
    for xc in (-21.0, 21.0):
        stem = bx(xc - 3, xc + 3, 10, BIG, z_in + 0.6, z_in + 3.6) & skin(MID, WALL + LEDGE + 0.1 + HOOK_T)
        leg = bx(xc - 3, xc + 3, 10, BIG, z_in - 7.0, z_in + 3.6) & skin(WALL + LEDGE + 0.1,
                                                                        WALL + LEDGE + 0.1 + HOOK_T)
        s = s + stem + leg
    # debossed wordmark (0.3 mm) near the bottom of the door
    try:
        font = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
        with BuildSketch(Plane.XZ) as sk:
            with Locations((0, RD["zc"] - RD["h"] / 2 + 12.0)):
                Text("NOVA", 6.0, font_path=font if os.path.exists(font) else None)
        txt = Pos(0, BIG, 0) * extrude(sk.sketch, BIG - 10)
        s -= txt & (body() - off(0.3))
    except Exception as e:  # pragma: no cover - cosmetic only
        print("  (wordmark skipped:", e, ")")
    return largest(s)


# ---------------------------------------------------------------------------
# T04 bottom plate
# ---------------------------------------------------------------------------

def part_t04():
    z0, h = Z0, BP["h"]
    p = superellipse_prism(BP["w"] / 2, BP["d"] / 2, BP["n"], z0, z0 + h)
    p = fillet(p.edges().group_by(Axis.Z)[0], 0.8)
    for (x, y) in BP["screw_xy"]:            # M2.5 countersunk (90°)
        p -= cyl_z(x, y, 1.4, z0 - 1, z0 + h + 1)
        p -= Pos(x, y, z0 - 0.01) * Solid.make_cone(2.75, 1.25, 1.51)
    p -= cyl_z(0, 0, BP["center_hole_d"] / 2, z0 - 1, z0 + h + 1)
    # 3 spacer pads (Ø8) down to the turntable disc B05 + M3 holes: torso <-> J1 coupling
    pad_h = z0 - B05_TOP
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = 16.0 * math.cos(a), 16.0 * math.sin(a)
        p += cyl_z(x, y, 4.0, z0 - pad_h, z0 + 0.5)
        p -= cyl_z(x, y, 1.6, z0 - pad_h - 1, z0 + h + 1)
        p -= cyl_z(x, y, 2.9, z0 + h - 1.6, z0 + h + 1)          # screw-head counterbore (inside)
    # shallow label recess
    p -= bx(-14, 14, 12.5, 22.5, z0 - 1, z0 + 0.3)
    return p


# ---------------------------------------------------------------------------
# T05 light guide, T06 sensor window
# ---------------------------------------------------------------------------

def part_t05():
    lens = stadium_xz(LED["w"] - 2 * FIT, LED["h"] - 2 * FIT, LED["z"], -BIG, -10) & (body() - off(LED_DEPTH))
    flange = stadium_xz(LED["w"] + 4.0, LED["h"] + 4.0, LED["z"], -BIG, -10) & skin(WALL, LED_DEPTH)
    return lens + flange


def part_t06():
    d1 = WALL + SEN_FLANGE
    win = stadium_xz(SEN["w"] - 2 * FIT, SEN["h"] - 2 * FIT, SEN["z"], -BIG, -10) & (body() - off(d1))
    flange = stadium_xz(SEN["w"] + 4.0, SEN["h"] + 4.0, SEN["z"], -BIG, -10) & skin(WALL, d1)
    return win + flange


# ---------------------------------------------------------------------------

def build():
    J = "J1"
    return [
        PartRec("T01", "Predný panel", part_t01(), "white", "torso", J, (0, -60, 0),
                note="biely čelný pás |x|≤38, škára 0.6, 4 zámky, nesie T05 a T06"),
        PartRec("T02", "Telo trupu (jadro)", part_t02(), "white", "torso", J, (0, 0, 0),
                note="nosné jadro: ramenné otvory Ø23/Ø31.4, otvor krku Ø40, rám dvierok, výstuhy"),
        PartRec("T03", "Zadné dvierka", part_t03(), "white", "torso", J, (0, 60, 0),
                note="servisné dvierka 76×76 R14, 5 vetracích štrbín, 2 háčiky + 2 magnety"),
        PartRec("T04", "Spodná doska trupu", part_t04(), "black", "torso", J, (0, 0, -40),
                note="4× M2.5 zápustné, Ø20 káble zo zberacieho krúžku, 3 dištančné pätky k B05"),
        PartRec("T05", "LED svetlovod hrude", part_t05(), "cyan_led", "torso", J, (0, -90, 0),
                note="PMMA opál, zarovno s čelom, poistná príruba"),
        PartRec("T06", "Senzorové okienko", part_t06(), "frost", "torso", J, (0, -90, 0),
                note="ToF VL53L1X + VEML7700, zarovno s čelom"),
    ]


if __name__ == "__main__":
    parts = build()
    for p in parts:
        print(f"  {p.id}: valid={p.shape.is_valid} solids={len(p.shape.solids())}")
    run_module(lambda: parts, "torso")
