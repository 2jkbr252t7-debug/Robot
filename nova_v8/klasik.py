"""
NOVA mini v9.0 "KLASIK" (user's choice 2026-11-02, concept c1 "Klasik R01+": obrazky/v8_koncept/v8_4_navrhy.png,
column 1) – shared OUTER FORMS of the base, torso, arms and visible neck.  All numbers come from
nova_v8/spec.py KLASIK; the engineering modules (cad_base, cad_torso, ...) build their shells from these
functions so the product looks exactly like the chosen concept.

  base_secs(inset)   -> sections (a, b, n, z) of the white base slab (squircle, drafted side, elliptical top round)
  foot_secs()        -> sections of the recessed black foot plate (underglow ring sits just outside it)
  torso_secs(inset)  -> sections of the torso (squircle n 3.4, bottom round, slight taper, shoulder dome -> flat
                        circle under the collar)
  torso_half(z)      -> (a, b) half-sizes of the torso at height z
  arm_secs(inset), arm_profile(u)  -> paddle arm sections in LOCAL coords (shoulder at origin, length along Z)
  place_arm(shape, side)           -> yaw + splay + move to the shoulder (side +1 = left/+X, -1 = right/-X)
  loft(secs)         -> Solid
A shell = loft(secs(0)) - loft(secs(wall)) (fast, no OCC offset of lofts).
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from build123d import Axis, Edge, Plane, Pos, Solid, Vector, Wire  # noqa: E402

from nova.cad.common import superellipse_pts  # noqa: E402
from nova_v8 import spec as S8  # noqa: E402

K = S8.KLASIK


def se_wire(a, b, n, z, count=96, roll=0.25):
    raw = superellipse_pts(a, b, n, count)
    k = int(round(roll * count)) % count          # spline seam at the BACK centre (+Y), away from all cuts
    raw = raw[k:] + raw[:k]
    return Wire([Edge.make_spline([Vector(x, y, z) for x, y in raw], periodic=True)])


def loft(secs, count=96):
    return Solid.make_loft([se_wire(*s, count=count) for s in secs])


# ---------------------------------------------------------------- base
def base_secs(inset=0.0):
    B = K["base"]
    ba, bb, bn = B["w"] / 2, B["d"] / 2, B["n"]
    z0, z1, rb, tp, rh, rv = B["z0"], B["z1"], B["r_bot"], B["draft"], B["r_top_h"], B["r_top_v"]
    zb, zt = z0 + rb, z1 - rv
    out = []
    for i in range(7):                                   # bottom round
        th = math.pi / 2 * i / 6
        out.append((z0 + rb * (1 - math.cos(th)), tp + rb * (1 - math.sin(th))))
    k = max(2, math.ceil((zt - zb) / 3.5))
    for i in range(1, k + 1):                            # straight drafted side
        t = i / k
        out.append((zb + t * (zt - zb), tp * (1 - t)))
    for i in range(1, 13):                               # elliptical top round
        u = math.sin(math.pi / 2 * i / 12)
        out.append((zt + rv * u, rh * (1 - math.sqrt(max(0.0, 1 - u * u)))))
    return [(ba - s - inset, bb - s - inset, bn, z) for z, s in out]


def foot_secs():
    F, B = K["foot"], K["base"]
    fa, fb, n, z0 = F["w"] / 2, F["d"] / 2, B["n"], F["z0"]
    secs = [(fa - 1.2 + 1.2 * math.sin(math.pi / 2 * i / 4), fb - 1.2 + 1.2 * math.sin(math.pi / 2 * i / 4), n,
             z0 + 1.2 * (1 - math.cos(math.pi / 2 * i / 4))) for i in range(5)]
    return secs + [(fa, fb, n, B["z0"] + 0.6)]


# ---------------------------------------------------------------- torso
def torso_secs(inset=0.0):
    T = K["torso"]
    ta, tb, tn = T["w"] / 2, T["d"] / 2, T["n"]
    z0 = K["base"]["z1"] + T["gap"]
    z1 = z0 + T["h"]
    rb, rv, rtop, tpa, tpb = T["r_bot"], T["dome_v"], T["top_r"], T["taper_a"], T["taper_b"]
    zb0, zd = z0 + rb, z1 - rv
    out = []
    for i in range(10):                                  # bottom round
        th = math.pi / 2 * i / 9
        s = rb * (1 - math.sin(th))
        out.append((ta - s, tb - s, tn, z0 + rb * (1 - math.cos(th))))
    k = max(2, math.ceil((zd - zb0) / 3.5))
    for i in range(1, k + 1):                            # body, subtle taper (top narrower)
        t = i / k
        out.append((ta - tpa * t * t, tb - tpb * t * t, tn, zb0 + t * (zd - zb0)))
    ad, bd = ta - tpa, tb - tpb
    for i in range(1, 15):                               # shoulder dome -> flat circle under the collar
        u = math.sin(math.pi / 2 * i / 14)
        g = 1 - math.sqrt(max(0.0, 1 - u * u))
        out.append((ad - (ad - rtop) * g, bd - (bd - rtop) * g, tn - (tn - 2.0) * g ** 0.8, zd + rv * u))
    if inset:
        zc, f = (z0 + z1) / 2, (T["h"] - 2 * inset) / T["h"]
        out = [(a - inset, b - inset, n, zc + (z - zc) * f) for a, b, n, z in out]
    return out


def torso_z():
    z0 = K["base"]["z1"] + K["torso"]["gap"]
    return z0, z0 + K["torso"]["h"]


def torso_half(z, inset=0.0):
    secs = torso_secs(inset)
    for s0, s1 in zip(secs, secs[1:]):
        if s0[3] <= z <= s1[3]:
            t = (z - s0[3]) / (s1[3] - s0[3])
            return s0[0] + t * (s1[0] - s0[0]), s0[1] + t * (s1[1] - s0[1])
    return secs[-1][0], secs[-1][1]


# ---------------------------------------------------------------- arms (R01 paddles)
def arm_profile(u):
    A = K["arm"]
    u0, p, p2 = 0.40, 2.3, 2.8
    v = u / (2 * u0) if u < u0 else 0.5 + (u - u0) / (2 * (1 - u0))
    e = max(0.0, 1 - abs(2 * v - 1) ** p) ** (1 / p)
    e2 = max(0.0, 1 - abs(2 * v - 1) ** p2) ** (1 / p2)
    return A["half_t"] * e2 * (1 - 0.12 * u), A["half_w"] * e * (1 - 0.16 * u ** 1.5)


def arm_secs(inset=0.0):
    A = K["arm"]
    m, out = 36, []
    for i in range(m + 1):
        u = 0.003 + 0.994 * (0.5 - 0.5 * math.cos(math.pi * i / m))
        a, b = arm_profile(u)
        out.append((max(a - inset, 0.25), max(b - inset, 0.35), A["n"], (u - A["shoulder_u"]) * A["length"]))
    return out


def arm_centre_x():
    A = K["arm"]
    a_s, _ = arm_profile(A["shoulder_u"])
    return A["inner_face_x"] + a_s / math.cos(math.radians(A["yaw"]))


def place_arm(shape, side=1):
    """Local arm (shoulder at origin, length along Z, thickness along X) -> assembly position.
    side=+1 left arm (+X), side=-1 right arm (-X, mirrored)."""
    A, sh = K["arm"], K["shoulder"]
    s = shape.rotate(Axis.Z, -A["yaw"]).rotate(Axis.Y, -A["splay"])
    s = Pos(arm_centre_x(), sh["y"], sh["z"]) * s
    return s if side > 0 else s.mirror(Plane.YZ)


if __name__ == "__main__":
    import time
    t0 = time.time()
    for nm, secs in (("base", base_secs()), ("foot", foot_secs()), ("torso", torso_secs()), ("arm", arm_secs())):
        s = loft(secs, count=72 if nm == "arm" else 96)
        bb = s.bounding_box()
        print(f"{nm:6s} valid={s.is_valid} size=({bb.size.X:.1f},{bb.size.Y:.1f},{bb.size.Z:.1f}) z[{bb.min.Z:.1f},{bb.max.Z:.1f}]")
    print("torso z", torso_z(), "half at shoulder", tuple(round(v, 2) for v in torso_half(K["shoulder"]["z"])),
          "arm centre x", round(arm_centre_x(), 2), f"{time.time() - t0:.1f}s")
