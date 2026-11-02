"""
NOVA mini – KRK presne podľa predlohy používateľa R04 (referencie/R04_krk_golier.png), proportions measured from
the image (front view: barrel length 353 px = 49 mm):
  N06 kryt náklonu – horizontal barrel 49 long: domed end caps Ø17.2 x 7.5, core Ø15, 0.7 grooves
  N02 plášť krku   – FLAT OVAL neck: wide left-right (27.5 at the top), slim front-back (14 at the top); the back is
                     nearly vertical, the FRONT sweeps forward and down into the collar (side view of R04)
  N01 golier       – oval plate 51 x 35.5 x 5.5 with a fine step line around the outer edge
  Collar + neck + barrel turn together with the head pan (J2) on a hidden round turntable in the torso top;
  the head tilts about the barrel axis (head bottom has a coaxial groove, 0.5 mm gap).
World coords of the robot: torso top z 117.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import Axis, Cylinder, Edge, Pos, Rot, Solid, Vector, Wire, fillet  # noqa: E402

from nova.cad.common import superellipse_pts  # noqa: E402

ZT = 117.0
# N01 collar
C_A, C_B, C_H = 25.5, 19.5, 5.0
C_CY = -2.0                        # collar centre slightly forward (the neck sweeps forward)
C_STEP = 0.9                       # fine step line around the outer edge
# N02 neck (flat oval, front sweep)
N_TOP = (13.75, 8.6)               # half axes at the top (X, Y)
N_BOT = (17.5, 14.0)               # half axes at the bottom
N_BOT_DY = -5.0                    # bottom centre forward: back edge +9 (near vertical), front edge -19 (long front sweep)
N_H = 16.5
# N06 barrel
CAP_R, CAP_L, CAP_GAP, B_R, B_LEN = 9.0, 7.8, 0.6, 8.6, 49.0
B_CORE_L = B_LEN - 2 * (CAP_L + CAP_GAP)
Z_C0 = ZT                          # collar bottom on the torso top
Z_N0 = Z_C0 + C_H - 1.0
Z_N1 = Z_N0 + N_H
AX_Z = Z_N1 + B_R - 2.0            # barrel sits ON the neck (neck top tucks 2 mm under the core)
HEAD_Z0 = AX_Z + 2.5               # head bottom (barrel top enters the head groove)


def _w(a, b, z, n=2.0, cy=0.0, count=96):
    return Wire([Edge.make_spline([Vector(x, cy + y, z) for x, y in superellipse_pts(a, b, n, count)], periodic=True)])


def collar():
    """Two tiers as in R04/R07: a THIN oval plate with a fine step line + a narrow raised oval ring the neck enters."""
    cy = C_CY
    plate = Solid.make_loft([_w(C_A - C_STEP, C_B - C_STEP, Z_C0, cy=cy), _w(C_A - C_STEP, C_B - C_STEP, Z_C0 + 0.9, cy=cy),
                             _w(C_A, C_B, Z_C0 + 0.95, cy=cy), _w(C_A, C_B, Z_C0 + 1.6, cy=cy)]
                            + [_w(C_A - 1.6 * (1 - math.cos(t * math.pi / 2)), C_B - 1.6 * (1 - math.cos(t * math.pi / 2)),
                                  Z_C0 + 1.6 + 1.0 * math.sin(t * math.pi / 2), cy=cy) for t in (0.25, 0.5, 0.75, 1.0)])
    ra, rb, rcy = N_BOT[0] + 2.2, N_BOT[1] + 2.2, N_BOT_DY
    ring = Solid.make_loft([_w(ra, rb, Z_C0 + 2.0, cy=rcy), _w(ra, rb, Z_C0 + C_H - 0.8, cy=rcy),
                            _w(ra - 0.4, rb - 0.4, Z_C0 + C_H - 0.2, cy=rcy), _w(ra - 1.0, rb - 1.0, Z_C0 + C_H, cy=rcy)])
    c = plate + ring
    from build123d import BuildSketch, Plane, SlotOverall, extrude
    rec = Solid.make_loft([_w(C_A - 3.5, C_B - 3.5, Z_C0 - 0.1, cy=cy), _w(C_A - 3.5, C_B - 3.5, Z_C0 + 1.0, cy=cy)])
    c = c - rec
    with BuildSketch(Plane.XY.offset(Z_C0 - 1)) as sk:
        SlotOverall(15.0, 6.5)
    return c - extrude(sk.sketch, amount=C_H + 4)


def neck():
    secs = []
    for i in range(12):
        t = i / 11                                          # 0 bottom -> 1 top
        k = (1 - t) ** 2.3                                  # smooth bell/trumpet flare (R04 front view)
        a = N_TOP[0] + (N_BOT[0] - N_TOP[0]) * k
        b = N_TOP[1] + (N_BOT[1] - N_TOP[1]) * k
        cy = N_BOT_DY * k
        secs.append(_w(a, b, Z_N0 + N_H * t, n=2.15, cy=cy))
    return Solid.make_loft(secs)


def barrel():
    core = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R, B_CORE_L + 0.4)
    out = core
    for sx in (-1, 1):
        xc = sx * (B_CORE_L / 2 + CAP_GAP + CAP_L / 2)
        cap = Pos(xc, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(CAP_R, CAP_L)
        try:
            cap = fillet([e for e in cap.edges() if abs(e.center().X - (xc + sx * CAP_L / 2)) < 0.01], 5.0)
            cap = fillet([e for e in cap.edges() if abs(e.center().X - (xc - sx * CAP_L / 2)) < 0.01], 0.9)
        except Exception:  # noqa: BLE001
            pass
        link = Pos(sx * (B_CORE_L / 2 + CAP_GAP / 2), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R - 1.2, CAP_GAP + 0.4)
        out = out + cap + link
    return out


def head_groove():
    g = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + 0.5, B_CORE_L + 2 * CAP_GAP + 0.2)
    for sx in (-1, 1):
        xc = sx * (B_CORE_L / 2 + CAP_GAP + CAP_L / 2)
        g = g + Pos(xc, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(CAP_R + 0.5, CAP_L + 1.0)
    return g


if __name__ == "__main__":
    for nm, f in (("collar", collar), ("neck", neck), ("barrel", barrel)):
        s = f()
        bb = s.bounding_box()
        print(f"{nm:7s} valid={s.is_valid} x[{bb.min.X:.1f},{bb.max.X:.1f}] y[{bb.min.Y:.1f},{bb.max.Y:.1f}] z[{bb.min.Z:.1f},{bb.max.Z:.1f}]")
    print("axis", AX_Z, "head bottom", HEAD_Z0, "neck visible", round(HEAD_Z0 - ZT, 1))
