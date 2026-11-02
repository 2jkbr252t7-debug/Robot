"""
NOVA mini – KRK podľa predlohy R04 (user's reference referencie/R04_krk_golier.png + R07_kryty_krku.png):
  N01 golier   – flat OVAL flared collar on the torso top (fixed to the torso, J1)
  N02 plášť    – trumpet-shaped neck shell, round (turns with the head pan, J2)
  N06 kryt     – horizontal tilt barrel with rounded end caps + short stub into the neck shell (J2); the head sits on
                 it: the head bottom has a coaxial groove (stepped for the caps) -> constant 0.5 mm gap while tilting.
Sizes are scaled from R04 to the 106 mm head.  World coords of the KLASIK robot: torso top z 117.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import (Axis, BuildLine, BuildSketch, Cylinder, Ellipse, Line, Location, Plane, Pos, Rot, Solid,  # noqa: E402
                       Spline, extrude, fillet, loft, make_face, revolve, Sketch, Wire, Edge, Vector)

from nova.cad.common import superellipse_pts  # noqa: E402

ZT = 117.0                        # torso top
# N01 collar (oval, flared)
C_A, C_B, C_H = 26.0, 19.5, 5.0   # outer half axes at the bottom, height
C_RIM = 15.5                      # inner rim radius at the top (neck shell bottom sits in it)
# N02 neck shell (trumpet)
N_R0, N_R1, N_H = 15.0, 9.6, 10.5  # bottom radius (in the collar rim), top radius, height
# N06 tilt barrel
B_R, B_L = 7.0, 33.0               # core radius, core length
CAP_R, CAP_L, CAP_GAP = 8.4, 7.5, 0.7
STUB_R = 6.0
Z_C0 = ZT - 0.5                    # collar bottom (slightly sunk into the torso top)
Z_N0 = Z_C0 + C_H - 1.0            # neck shell bottom (inside the collar rim)
Z_N1 = Z_N0 + N_H
AX_Z = Z_N1 + B_R + 0.5            # tilt axis (barrel sits right on the neck shell, stub hidden)
HEAD_Z0 = AX_Z + 2.0               # head bottom (barrel top 5 mm into the head groove)


def _se_wire(a, b, z, n=2.0, count=96):
    return Wire([Edge.make_spline([Vector(x, y, z) for x, y in superellipse_pts(a, b, n, count)], periodic=True)])


def collar():
    """Oval flared plate: oval at the bottom -> concave flare -> round rim at the top (R01/R04 look)."""
    secs = []
    for i in range(13):
        t = i / 12
        q = 1 - (1 - t) ** 2.4                       # concave flare (fast rise near the rim)
        a = C_A + (C_RIM - C_A) * q
        b = C_B + (C_RIM - C_B) * q
        n = 2.0
        z = Z_C0 + C_H * (t ** 0.9) if i else Z_C0
        if i == 0:
            secs.append(_se_wire(a, b, Z_C0))
            secs.append(_se_wire(a, b, Z_C0 + 0.8))  # thin vertical edge (the fine rim line in R04)
            continue
        secs.append(_se_wire(a, b, max(z, Z_C0 + 0.8 + 0.1 * i)))
    s = Solid.make_loft(secs)
    hole = Pos(0, 0, Z_C0 + C_H / 2) * Cylinder(C_RIM - 1.6, C_H + 4)
    return s - hole


def neck_shell():
    """Trumpet profile (concave), round."""
    pts = []
    for i in range(16):
        t = i / 15
        r = N_R1 + (N_R0 - N_R1) * (1 - t) ** 2.0
        pts.append((r, Z_N0 + N_H * t))
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Line((0, Z_N0), pts[0])
            Spline(*pts)
            Line(pts[-1], (0, pts[-1][1]))
            Line((0, pts[-1][1]), (0, Z_N0))
        make_face()
    return revolve(sk.sketch, Axis.Z, 360)


def barrel():
    core = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R, B_L)
    parts = [core]
    for sx in (-1, 1):
        xc = sx * (B_L / 2 + CAP_GAP + CAP_L / 2)
        cap = Pos(xc, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(CAP_R, CAP_L)
        outer = cap.edges().sort_by(Axis.X)[-1 if sx > 0 else 0]
        try:
            cap = fillet([e for e in cap.edges() if abs(e.center().X - (xc + sx * CAP_L / 2)) < 0.01], 3.6)
            cap = fillet([e for e in cap.edges() if abs(e.center().X - (xc - sx * CAP_L / 2)) < 0.01 and e.radius > 8], 0.8)
        except Exception:  # noqa: BLE001
            pass
        link = Pos(sx * (B_L / 2 + CAP_GAP / 2), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R - 1.0, CAP_GAP + 0.2)
        parts += [cap, link]
    stub = Pos(0, 0, (Z_N1 - 0.5 + AX_Z) / 2) * Cylinder(STUB_R, AX_Z - Z_N1 + 0.5)
    out = parts[0]
    for p in parts[1:] + [stub]:
        out = out + p
    return out


def head_groove():
    """Cut for the head bottom: coaxial with the barrel, 0.5 mm gap (stepped for the caps)."""
    g = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + 0.5, B_L + 2 * CAP_GAP + 0.2)
    for sx in (-1, 1):
        xc = sx * (B_L / 2 + CAP_GAP + CAP_L / 2)
        g = g + Pos(xc, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(CAP_R + 0.5, CAP_L + 1.0)
    return g


if __name__ == "__main__":
    for nm, f in (("collar", collar), ("neck", neck_shell), ("barrel", barrel)):
        s = f()
        bb = s.bounding_box()
        print(f"{nm:7s} valid={s.is_valid} size=({bb.size.X:.1f},{bb.size.Y:.1f},{bb.size.Z:.1f}) z[{bb.min.Z:.1f},{bb.max.Z:.1f}]")
    print("tilt axis z", AX_Z, "head bottom z", HEAD_Z0, "visible neck from torso top", round(HEAD_Z0 - ZT, 1))
