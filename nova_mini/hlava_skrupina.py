"""
NOVA mini – DIEL 1: škrupina hlavy (step-by-step design, user review)

návrh 4 (build_v4, 2026-11-03): bottom adapted to the one-piece neck nova_mini/krk.py – an inner saddle with a groove
  coaxial with the tilt barrel (0.5 mm gap), two tight pockets for the barrel end caps (screwed to the head 1x M2 each
  from inside), a window for the tilt servo that stands up into the head, cable window.  No ball, no pivot walls.

návrh 3:

návrh 3 (user: "aby ten krk tam sadol, žiadne diery navyše, žiadne medzery navyše, hladko, moderne"):
  * BALL NECK: the neck ends in a black ball Ø32 whose centre IS the tilt axis (8 mm above the head bottom).
    The head bottom has one round opening that follows the ball surface (spherical cut, 0.5 mm gap) – when the
    head tilts ±20° it rolls around the ball, so the gap stays 0.5 mm all the time.  No oval, no extra opening.
  * inside: two thin pivot walls left/right of the ball with Ø3.2 pin holes on the axis.
(návrh 2 notes kept below for reference)

User feedback on návrh 1: the underside (big pocket, slanted relief, 2 screws, vent slots) "vyzerá hrozne, je to nutné?"
-> návrh 2 keeps only what is FUNCTIONALLY needed, nothing else:
  * outer form unchanged (front view 106 x 74, corners R26, depth 66, back edges R20), wall 2 mm, ONE piece
  * front: opening for the black front frame that carries the Waveshare ESP32-S3-Touch-LCD-3.5B(-C) board
    (board ~85.5 x 55.5 – verify on the real part); the frame CLIPS in (4 hidden snap catches inside the rim) –
    NO screws anywhere
  * underside: ONE small oval opening for the neck column (Ø25.6) – it is oval because the head tilts ±20° about
    a horizontal axis 16 mm above the head bottom (the tilt joint is fully INSIDE the head, nothing sticks out)
  * sides: Ø24 holes for the ear light modules (separate parts later)
  * inside: two pivot walls with Ø3.2 pin holes on the tilt axis (the head turns on two pins), nothing else
    (the tilt servo mount comes with the tilt-mechanism part)
Coordinates of this part: mm, head bottom at z = 0, centre x = y = 0, front = -Y.
Run:  /opt/venv/cad/bin/python -m nova_mini.hlava_skrupina   -> obrazky/postupne/01_hlava_skrupina/*_navrh3.stl
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import (Axis, Box, BuildSketch, Cylinder, Location, Plane, Pos, RectangleRounded, Rot, SlotOverall,  # noqa: E402
                       export_step, export_stl, extrude, fillet)

# ---- parameters (this part) ---------------------------------------------------------------------------------------
W, H, D = 106.0, 74.0, 66.0          # front-view width x height, depth along Y
R_FV = 26.0                          # front-view corner radius
R_BACK = 20.0                        # back edge round
R_FRONT = 1.2                        # small round at the front rim (meets the black frame)
WALL = 2.0
OPEN_W, OPEN_H, OPEN_R = 102.0, 70.0, 24.0     # front opening (frame 101 x 69 R23.5 + 0.5 clearance)
EAR_D, EAR_Y, EAR_Z = 24.0, -3.0, 37.0         # ear module holes
TILT_Y, TILT_Z = 0.0, 8.0                      # tilt axis = ball centre (8 above the head bottom)
BALL_R, BALL_GAP = 16.0, 0.5                   # neck ball Ø32, constant gap to the head opening
COLUMN_D, TILT_DEG = 19.0, 20.0                # neck column below the ball, tilt range ±
PIVOT_X = BALL_R + 0.8                          # pivot walls inner faces (0.8 mm beside the ball)
PIVOT_T, PIVOT_PIN_D = 3.0, 3.2
CATCH_W, CATCH_H, CATCH_T = 10.0, 1.6, 1.2      # snap catch ledges inside the rim (4x)

Y0, Y1 = -D / 2, D / 2


def body(w, h, d, r_fv, r_back, y0):
    with BuildSketch(Plane.XZ.offset(-y0)) as sk:          # Plane.XZ normal is -Y -> offset(-y0) puts it at y = y0
        RectangleRounded(w, h, r_fv)
    s = extrude(sk.sketch, amount=-d)                       # towards +Y
    s = s.moved(Location((0, 0, h / 2)))
    back = [e for e in s.edges() if abs(e.center().Y - (y0 + d)) < 0.01]
    return fillet(back, r_back)


def build():
    outer = body(W, H, D, R_FV, R_BACK, Y0)
    inner = body(W - 2 * WALL, H - 2 * WALL, D - WALL + 1.0, R_FV - WALL, R_BACK - WALL, Y0 - 1.0).moved(Location((0, 0, WALL)))
    shell = outer - inner
    # front opening (through the front rim region) – the inner body already opens the front; trim to the frame size
    with BuildSketch(Plane.XZ.offset(-(Y0 - 1))) as sk:
        RectangleRounded(OPEN_W, OPEN_H, OPEN_R)
    opening = extrude(sk.sketch, amount=-(WALL + 3)).moved(Location((0, 0, H / 2)))
    shell = shell - opening
    # ear holes
    for sx in (-1, 1):
        shell = shell - Pos(sx * (W / 2), EAR_Y, EAR_Z) * Rot(0, 90, 0) * Cylinder(EAR_D / 2, 10)
    # underside: ONE round opening that follows the neck ball (spherical cut) -> constant 0.5 mm gap while tilting
    from build123d import Solid as _Solid
    slot_len = 2 * ((BALL_R + BALL_GAP) ** 2 - TILT_Z ** 2) ** 0.5
    shell = shell - Pos(0, TILT_Y, TILT_Z) * _Solid.make_sphere(BALL_R + BALL_GAP)
    # pivot walls with pin holes on the tilt axis
    for sx in (-1, 1):
        x0 = sx * (PIVOT_X + PIVOT_T / 2)
        wall = Pos(x0, TILT_Y, (TILT_Z + 9) / 2 + WALL / 2) * Box(PIVOT_T, 22, TILT_Z + 9 - WALL)
        wall = fillet(wall.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], 4)
        wall = wall - Pos(x0, TILT_Y, TILT_Z) * Rot(0, 90, 0) * Cylinder(PIVOT_PIN_D / 2, PIVOT_T + 2)
        shell = shell + wall
    # snap catches (4 small ledges inside the front rim, top + bottom)
    for sx in (-1, 1):
        for zc, sz in ((H - WALL - CATCH_T / 2, -1), (WALL + CATCH_T / 2, 1)):
            shell = shell + Pos(sx * 28, Y0 + 6.5, zc) * Box(CATCH_W, CATCH_H, CATCH_T)
    front = [e for e in shell.edges() if abs(e.center().Y - Y0) < 0.01]
    try:
        shell = fillet(front, R_FRONT)
    except Exception:  # noqa: BLE001
        try:
            from build123d import chamfer
            shell = chamfer(front, 0.5)
        except Exception as ex:  # noqa: BLE001
            print("front rim round skipped:", ex)
    return shell, slot_len


def build_common():
    """Shell + front opening + ear holes + snap catches + front rim round – no neck interface (návrh 4 adds it)."""
    outer = body(W, H, D, R_FV, R_BACK, Y0)
    inner = body(W - 2 * WALL, H - 2 * WALL, D - WALL + 1.0, R_FV - WALL, R_BACK - WALL, Y0 - 1.0).moved(Location((0, 0, WALL)))
    shell = outer - inner
    with BuildSketch(Plane.XZ.offset(-(Y0 - 1))) as sk:
        RectangleRounded(OPEN_W, OPEN_H, OPEN_R)
    shell = shell - extrude(sk.sketch, amount=-(WALL + 3)).moved(Location((0, 0, H / 2)))
    for sx in (-1, 1):
        shell = shell - Pos(sx * (W / 2), EAR_Y, EAR_Z) * Rot(0, 90, 0) * Cylinder(EAR_D / 2, 10)
    for sx in (-1, 1):
        for zc in (H - WALL - CATCH_T / 2, WALL + CATCH_T / 2):
            shell = shell + Pos(sx * 28, Y0 + 6.5, zc) * Box(CATCH_W, CATCH_H, CATCH_T)
    front = [e for e in shell.edges() if abs(e.center().Y - Y0) < 0.01]
    try:
        shell = fillet(front, R_FRONT)
    except Exception:  # noqa: BLE001
        pass
    return shell


def build_v4():
    """návrh 4 – head bottom for the one-piece neck (nova_mini/krk.py): a saddle inside the head with a groove coaxial
    with the tilt barrel (0.5 mm gap) and two tight pockets for the end caps (the caps are screwed to the head from
    inside, 1x M2 each) + a cable window. Head coordinates: bottom at z = 0."""
    from nova_mini import krk as K
    s = build_common()
    saddle, cut = K.head_saddle_cut()
    mv = Location((0, 0, -K.HEAD_Z0))
    return (s + saddle.moved(mv)) - cut.moved(mv)


if __name__ == "__main__":
    s, slot_len = build()
    bb = s.bounding_box()
    print("valid", s.is_valid, "size", round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1),
          "vol", round(s.volume / 1000, 1), "cm3", "bottom opening Ø", round(slot_len, 1))
    out = os.path.join(ROOT, "obrazky", "postupne", "01_hlava_skrupina")
    os.makedirs(out, exist_ok=True)
    export_step(s, os.path.join(out, "NOVA_mini_01_hlava_skrupina_navrh3.step"))
    export_stl(s, os.path.join(out, "NOVA_mini_01_hlava_skrupina_navrh3.stl"), tolerance=0.03, angular_tolerance=0.15)
    print("written")
