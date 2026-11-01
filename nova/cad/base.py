"""
NOVA – BASE (B01..B05).  Run:  /opt/venv/cad/bin/python -m nova.cad.base
"""
from __future__ import annotations

import math

from build123d import (Axis, Box, BuildPart, BuildSketch, Cylinder, Face, Locations, Mode, Plane, Pos,
                       RectangleRounded, Rot, SlotCenterToCenter, Solid, extrude, fillet, offset, Circle,
                       Compound, Align)

from nova import spec
from nova.cad.common import PartRec, run_module

B = spec.BASE
W, D, R = B["w"], B["d"], B["plan_r"]
Z0, Z1 = B["z0"], B["z1"]
PH = B["plate_h"]              # 4
WALL = B["shell_wall"]


def rr_prism(w, d, r, z0, h):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        RectangleRounded(w, d, r)
    return extrude(sk.sketch, h)


def shell_b01():
    body = rr_prism(W, D, R, PH, Z1 - PH)
    top = body.edges().group_by(Axis.Z)[-1]
    body = fillet(top, B["top_fillet"])
    bot = body.edges().group_by(Axis.Z)[0]
    body = fillet(bot, B["bottom_fillet"])
    # (offset(..., openings=) fails when the opening face borders a fillet -> hollow + cut the bottom)
    shell = body - offset(body, amount=-WALL)
    shell -= rr_prism(W - 2 * WALL, D - 2 * WALL, R - WALL, PH - 1, WALL + 1.01)

    # turntable seat: shallow circular recess on the top face + through hole for the rotating hub
    seat_d = B["turntable_d"]
    seat_depth = 2.0
    shell -= Pos(0, 0, Z1 - seat_depth) * Cylinder(seat_d / 2, seat_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell -= Pos(0, 0, Z1 - 10) * Cylinder(44 / 2, 20)

    # under-top bearing seat boss (6808-2RS: OD52 ID40 W7) + 4 screw bosses + 2 stiffening ribs
    boss = Pos(0, 0, Z1 - seat_depth - 8) * (Cylinder(60 / 2, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                           - Cylinder(52 / 2, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    shell += boss
    for (x, y) in B["screws"]["xy"]:
        b = Pos(x, y, PH) * (Cylinder(4.0, Z1 - PH - WALL, align=(Align.CENTER, Align.CENTER, Align.MIN))
                             - Cylinder(2.0, Z1 - PH - WALL, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        shell += b

    # front LED window (B03 sits in it)
    L = B["led"]
    with BuildSketch(Plane.XZ.offset(0)) as sk:
        with Locations((0, L["z"])):
            RectangleRounded(L["w"], L["h"], L["h"] / 2 - 0.05)
    cut = extrude(sk.sketch, D / 2 + 5, both=False)  # Plane.XZ normal is -Y -> extrudes toward front
    shell -= cut

    # rear speaker grille (2 x 11 holes), USB-C, power button
    g = B["grille"]
    cols = 11
    xc = 16.0
    for z in g["z"]:
        for i in range(cols):
            x = xc + (i - (cols - 1) / 2) * g["pitch"]
            shell -= Pos(x, D / 2, z) * Rot(90, 0, 0) * Cylinder(g["hole_d"] / 2, 12)
    u = B["usb_c"]
    with BuildSketch(Plane.XZ.offset(-(D / 2 - 6))) as sk:   # plane at y = +D/2-6, normal -Y
        with Locations((-36.0, u["z"])):
            RectangleRounded(u["w"], u["h"], 1.6)
    shell -= extrude(sk.sketch, -12)
    shell -= Pos(-22.0, D / 2, B["button"]["z"]) * Rot(90, 0, 0) * Cylinder(B["button"]["d"] / 2, 12)
    return shell


def led_b03():
    L = B["led"]
    with BuildSketch(Plane.XZ.offset(D / 2 - 0.05)) as sk:    # front face y = -D/2 (+0.05 inset)
        with Locations((0, L["z"])):
            RectangleRounded(L["w"] - 0.2, L["h"] - 0.2, (L["h"] - 0.2) / 2 - 0.05)
    return extrude(sk.sketch, -3.2)                             # toward +Y (inside)


def plate_b02():
    ins = B["plate_inset"]
    w, d, r = W - 2 * ins, D - 2 * ins, R - ins
    p = rr_prism(w, d, r, 0, PH)
    p = fillet(p.edges().group_by(Axis.Z)[0], 1.2)
    # feet pockets
    f = B["feet"]
    for (x, y) in f["xy"]:
        p -= Pos(x, y, 0) * Cylinder(f["d"] / 2 + 0.2, 0.8 * 2, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # countersunk screw holes
    for (x, y) in B["screws"]["xy"]:
        p -= Pos(x, y, 0) * Cylinder(1.7, PH * 3)
        p -= Pos(x, y, 0) * Solid.make_cone(3.2, 1.7, 1.6)
    # vent slots block (BLDC / buck converter) and label recess
    for i in range(9):
        y = (i - 4) * 4.2
        with BuildSketch(Plane.XY) as sk:
            with Locations((38, y)):
                SlotCenterToCenter(20, 2.0)
        p -= extrude(sk.sketch, PH + 1)
    with BuildSketch(Plane.XY) as sk:
        with Locations((-38, 0)):
            RectangleRounded(44, 22, 4)
    p -= extrude(sk.sketch, 0.4)
    return p


def feet_b04():
    f = B["feet"]
    feet = None
    for (x, y) in f["xy"]:
        c = Pos(x, y, spec.FLOOR_Z) * Cylinder(f["d"] / 2, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        c = fillet(c.edges().group_by(Axis.Z)[0], 0.8)
        feet = c if feet is None else feet + c
    return feet


def turntable_b05():
    """Black turntable disc under the torso – rotates with J1 (body yaw)."""
    d = B["turntable_d"] - 1.6   # disc sits in the Ø92 seat
    t = Pos(0, 0, Z1 - 2.0 + 0.2) * Cylinder(d / 2, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    t = fillet(t.edges().group_by(Axis.Z)[-1], 0.6)
    t -= Cylinder(10, 40)   # cable / slip-ring passage
    return t


def build():
    return [
        PartRec("B01", "Horný kryt základne", shell_b01(), "white", "base", "", (0, 0, 0),
                note="biely kryt, mriežka reproduktora, USB-C, vypínač"),
        PartRec("B02", "Spodná doska základne", plate_b02(), "black", "base", "", (0, 0, -45),
                note="4× M3 zápustné, vetranie, lôžka nožičiek"),
        PartRec("B03", "Svetlovod základne", led_b03(), "cyan_led", "base", "", (0, -30, 0),
                note="PMMA opál, 8× WS2812B-2020"),
        PartRec("B04", "Gumové nožičky (4×)", feet_b04(), "rubber", "base", "", (0, 0, -65)),
        PartRec("B05", "Otočný tanier", turntable_b05(), "black", "base", "J1", (0, 0, 25),
                note="spojený s trupom, otáča sa (J1)"),
    ]


if __name__ == "__main__":
    run_module(build, "base")
