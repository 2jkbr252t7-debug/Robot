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
C_A, C_B, C_H = 25.5, 19.5, 4.5
C_CY = -4.0                        # collar centre forward (the neck bell sweeps forward)
C_STEP = 0.9                       # fine step line around the outer edge
# N02 neck (flat oval, front sweep)
N_TOP = (13.75, 8.6)               # half axes at the top (X, Y)
N_BOT = (21.0, 15.0)               # half axes at the bottom = BELL edge on the collar
N_BOT_DY = -4.0                    # bell centre forward: back edge +11, front edge -19 (long front sweep)
N_H = 14.0
# N06 barrel
CAP_R, CAP_L, CAP_GAP, B_R, B_LEN = 9.8, 7.8, 0.6, 9.6, 49.0
B_CORE_L = B_LEN - 2 * (CAP_L + CAP_GAP)
Z_C0 = ZT                          # collar bottom on the torso top
Z_N0 = Z_C0 + C_H - 0.4
Z_N1 = Z_N0 + N_H
AX_Z = Z_N1 + B_R - 2.0            # barrel sits ON the neck (neck top tucks 2 mm under the core)
HEAD_Z0 = AX_Z + 2.5               # head bottom (barrel top enters the head groove)


def _w(a, b, z, n=2.0, cy=0.0, count=96):
    return Wire([Edge.make_spline([Vector(x, cy + y, z) for x, y in superellipse_pts(a, b, n, count)], periodic=True)])


def collar():
    """R04: a THIN oval plate under the neck bell, fine step line around the bottom edge, deep recess underneath."""
    cy = C_CY
    secs = [_w(C_A - C_STEP, C_B - C_STEP, Z_C0, cy=cy), _w(C_A - C_STEP, C_B - C_STEP, Z_C0 + 0.9, cy=cy),
            _w(C_A, C_B, Z_C0 + 0.95, cy=cy), _w(C_A, C_B, Z_C0 + C_H - 1.3, cy=cy)]
    for t in (0.3, 0.6, 0.85, 1.0):                        # rounded top edge
        e = 1.3 * (1 - math.cos(t * math.pi / 2))
        secs.append(_w(C_A - e, C_B - e, Z_C0 + C_H - 1.3 + 1.3 * math.sin(t * math.pi / 2), cy=cy))
    c = Solid.make_loft(secs)
    from build123d import BuildSketch, Plane, SlotOverall, extrude
    rec = Solid.make_loft([_w(C_A - 3.4, C_B - 3.4, Z_C0 - 0.1, cy=cy), _w(C_A - 3.4, C_B - 3.4, Z_C0 + 2.8, cy=cy)])
    c = c - rec
    with BuildSketch(Plane.XY.offset(Z_C0 - 1)) as sk:
        SlotOverall(15.0, 6.5)
    return c - extrude(sk.sketch, amount=C_H + 4)


# separate profiles (R04): left-right = slim column + strong BELL at the bottom (front view);
# front-back = back edge nearly vertical, FRONT edge a long concave ramp down to the collar front (side view)
NX_TOP, NX_BOT = 13.8, 21.0
NYF_TOP, NYF_BOT = -9.8, -22.0       # front edge
NYB_TOP, NYB_BOT = 9.8, 12.0         # back edge


def neck():
    secs = []
    for i in range(18):
        t = i / 17                                          # 0 bottom -> 1 top
        kx = (1 - t) ** 3.0                                 # bell (front view)
        ky = (1 - t) ** 1.35                                # long ramp (side view)
        a = NX_TOP + (NX_BOT - NX_TOP) * kx
        yf = NYF_TOP + (NYF_BOT - NYF_TOP) * ky
        yb = NYB_TOP + (NYB_BOT - NYB_TOP) * kx
        secs.append(_w(a, (yb - yf) / 2, Z_N0 + N_H * t, n=2.15, cy=(yb + yf) / 2))
    return Solid.make_loft(secs)


def barrel():
    core = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R, B_CORE_L + 0.4)
    out = core
    for sx in (-1, 1):
        xc = sx * (B_CORE_L / 2 + CAP_GAP + CAP_L / 2)
        cap = Pos(xc, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(CAP_R, CAP_L)
        try:
            cap = fillet([e for e in cap.edges() if abs(e.center().X - (xc + sx * CAP_L / 2)) < 0.01], 6.0)
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
