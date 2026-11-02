"""
NOVA mini – KRK (neck) proposal: a SHAPED neck instead of a stick (user: "nechcem aby bol krk len palička").
A revolved "trumpet" profile: wide and soft where it grows out of the shoulders (Ø42 on the collar), a smooth
concave waist, and the black ball Ø32 on top (the head's tilt joint: the head rolls around the ball with a constant
0.5 mm gap).  The waist is just thin enough that the head's underside never touches the neck at tilt ±20°:
for a neck point at radius r and height z (head coordinates, head bottom z = 0, ball centre z = 8) the rule is
    z <= 8 - 9.04 - 0.364 * r      (tilted head-bottom plane + 0.5 mm clearance)
Coordinates: same as the head shell (head bottom z = 0), so the neck reaches down to the collar at z = NECK_Z0.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import (Axis, BuildLine, BuildSketch, Line, Plane, Pos, Solid, Spline, make_face, revolve)  # noqa: E402

from nova_mini import hlava_skrupina as HS  # noqa: E402

NECK_Z0 = -24.0          # neck base (top of the torso collar), 24 mm of visible neck under the head
R_BASE = 21.0            # base radius (blends into the Ø44 collar)
R_WAIST = 9.0            # waist radius just under the ball
Z_WAIST = -6.0


def profile_pts(n=40):
    """(r, z) of the neck surface from the base to the waist: soft concave trumpet (quarter-ellipse-like)."""
    pts = []
    for i in range(n + 1):
        t = i / n                                     # 0 = base, 1 = waist
        z = NECK_Z0 + (Z_WAIST - NECK_Z0) * t
        k = 1 - math.sqrt(max(0.0, 1 - (1 - t) ** 2))  # 1 at the base -> 0 at the waist (vertical tangent at the base side)
        k = (1 - t) ** 2.2                              # smooth concave flare
        pts.append((R_WAIST + (R_BASE - R_WAIST) * k, z))
    return pts


def check_clearance(pts):
    worst = 1e9
    for r, z in pts:
        lim = HS.TILT_Z - 9.04 - 0.364 * r
        worst = min(worst, lim - z)
    return worst            # >= 0 means no contact with the tilted head underside


def build():
    pts = profile_pts()
    zc, rb = HS.TILT_Z, HS.BALL_R
    z_top = zc - math.sqrt(max(0.0, rb ** 2 - R_WAIST ** 2)) + 1.0     # continue 1 mm into the ball
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Line((0, NECK_Z0), (R_BASE, NECK_Z0))
            Spline(*[(r, z) for r, z in pts] + [(R_WAIST, z_top)])
            Line((R_WAIST, z_top), (0, z_top))
            Line((0, z_top), (0, NECK_Z0))
        make_face()
    neck = revolve(sk.sketch, Axis.Z, 360)
    ball = Pos(0, HS.TILT_Y, zc) * Solid.make_sphere(rb)
    return neck, ball, check_clearance(pts)


if __name__ == "__main__":
    n, b, c = build()
    print("neck valid", n.is_valid, "ball", b.is_valid, "min clearance to the tilted head underside", round(c, 2), "mm")
