"""
NOVA mini – DIEL 1: škrupina hlavy, návrh 2  (step-by-step design, user review)

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
Run:  /opt/venv/cad/bin/python -m nova_mini.hlava_skrupina   -> obrazky/postupne/01_hlava_skrupina/*_navrh2.stl
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
TILT_Y, TILT_Z = 0.0, 16.0                     # tilt axis (inside the head, 16 above the bottom)
NECK_D, TILT_DEG = 25.6, 20.0                  # neck column diameter, tilt range ±
SLOT_CLR = 0.8
PIVOT_X = 17.0                                  # pivot walls inner faces at x = ±17 (barrel Ø30 x 30 between them)
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
    # underside oval opening for the neck column (sweep of ±TILT_DEG about the axis 16 above the bottom)
    import math
    sweep = TILT_Z * math.tan(math.radians(TILT_DEG))
    slot_len = NECK_D + 2 * sweep + 2 * SLOT_CLR
    with BuildSketch(Plane.XY.offset(-1)) as sk:
        SlotOverall(slot_len, NECK_D + 2 * SLOT_CLR, rotation=90)
    shell = shell - extrude(sk.sketch, amount=WALL + 2)
    # pivot walls with pin holes on the tilt axis
    for sx in (-1, 1):
        x0 = sx * (PIVOT_X + PIVOT_T / 2)
        wall = Pos(x0, TILT_Y, (TILT_Z + 9) / 2 + WALL / 2) * Box(PIVOT_T, 24, TILT_Z + 9 - WALL)
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


if __name__ == "__main__":
    s, slot_len = build()
    bb = s.bounding_box()
    print("valid", s.is_valid, "size", round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1),
          "vol", round(s.volume / 1000, 1), "cm3", "slot", round(slot_len, 1), "x", NECK_D + 2 * SLOT_CLR)
    out = os.path.join(ROOT, "obrazky", "postupne", "01_hlava_skrupina")
    os.makedirs(out, exist_ok=True)
    export_step(s, os.path.join(out, "NOVA_mini_01_hlava_skrupina_navrh2.step"))
    export_stl(s, os.path.join(out, "NOVA_mini_01_hlava_skrupina_navrh2.stl"), tolerance=0.03, angular_tolerance=0.15)
    print("written")
