"""
NOVA mini v8.3 "soft forms" – shared outer-surface definitions of the base ("pebble plate") and the torso ("bulb").
Both are lofts of superellipse sections whose numbers come from nova_v8/spec.py BASE["form"] / TORSO["form"].

    sections = base_sections(inset)   / torso_sections(inset)    -> [(a, b, n, z), ...]
    solid    = loft(sections)

inset > 0 gives the matching INNER surface (each section shrunk by `inset` on both half-axes – practically a
parallel offset for these gentle shapes), so a shell is simply  loft(sections(0)) - loft(sections(wall))  –
fast and robust (no OCC offset of B-spline lofts needed).  Sections are <= ~4 mm apart (CLAUDE.md loft rule).
Prototype renders: obrazky/v8_koncept/v8_makke_tvary.png
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from build123d import Edge, Solid, Vector, Wire  # noqa: E402

from nova.cad.common import superellipse_pts  # noqa: E402
from nova_v8 import spec as S8  # noqa: E402


def se_wire(a, b, n, z, count=96):
    pts = [Vector(x, y, z) for x, y in superellipse_pts(a, b, n, count)]
    return Wire([Edge.make_spline(pts, periodic=True)])


def loft(secs):
    return Solid.make_loft([se_wire(*s) for s in secs])


def base_sections(inset=0.0, z_from=None, z_to=None):
    """Pebble plate: plan superellipse (a, b, n) at the top edge, straight conical side shrinking to `taper`
    at the skirt edge z0, round R `r_top` into the flat top at z1.  inset shrinks every section."""
    B, F = S8.BASE, S8.BASE["form"]
    a, b, n, r, tp = B["w"] / 2, B["d"] / 2, F["n"], F["r_top"], F["taper"]
    z0, z1 = B["skirt_z0"], B["z1"]
    zt = z1 - r
    zs = [z0 + i * (zt - z0) / max(1, math.ceil((zt - z0) / 3.5)) for i in range(math.ceil((zt - z0) / 3.5) + 1)]
    zs += [zt + r * math.sin(math.pi / 2 * i / 10) for i in range(1, 11)]
    out = []
    for z in zs:
        if z <= zt:
            k = tp + (1 - tp) * (z - z0) / (zt - z0)
            sa, sb = a * k, b * k
        else:
            u = min(1.0, (z - zt) / r)
            s = r * (1 - math.sqrt(max(0.0, 1 - u * u)))
            sa, sb = a - s, b - s
        out.append((sa - inset, sb - inset, n, z))
    if z_from is not None:
        out = [s for s in out if s[3] >= z_from - 1e-6]
    if z_to is not None:
        out = [s for s in out if s[3] <= z_to + 1e-6]
    return out


def torso_z0():
    """Torso foot plane: it stands in the circular dish of the base top with a 1 mm gap."""
    F = S8.BASE["form"]
    return S8.BASE["z1"] - F["dish_d"] + S8.TORSO["form"]["gap"]


def torso_sections(inset=0.0):
    """Bulb: round foot (circle r_foot at the dish) flaring with a quarter-round profile to the belly superellipse
    (a, b, n) over `flare` mm, a convex barrel narrowing by (ka, kb) up to z1 - r_top, then a round R `r_top`
    into the small flat top under the neck collar."""
    T, F = S8.TORSO, S8.TORSO["form"]
    a, b, n, r, z1 = T["w"] / 2, T["d"] / 2, F["n"], F["r_top"], T["z1"]
    rf, fl, ka, kb = F["foot_r"], F["flare"], F["ka"], F["kb"]
    z0 = torso_z0()
    zf, zt = z0 + fl, z1 - r
    out = []
    for i in range(10):
        t = i / 9
        q = math.sqrt(max(0.0, 1 - (1 - t) ** 2))
        fa = rf + (a - rf) * q
        fb = rf + (b - rf) * q
        fn = 2.0 + (n - 2.0) * q
        out.append((fa - inset, fb - inset, fn, z0 + t * (zf - z0)))
    nb = max(2, math.ceil((zt - zf) / 4.0))
    for i in range(1, nb + 1):
        t = i / nb
        out.append((a - ka * t * t - inset, b - kb * t * t - inset, n, zf + t * (zt - zf)))
    for i in range(1, 11):
        u = math.sin(math.pi / 2 * i / 10)
        s = r * (1 - math.sqrt(max(0.0, 1 - u * u)))
        out.append((a - ka - s - inset, b - kb - s - inset, n, zt + r * u))
    return out


def torso_half_width(z, inset=0.0):
    """(a, b) of the torso section at height z (linear interpolation of the sections) – e.g. for the shoulders."""
    secs = torso_sections(inset)
    for s0, s1 in zip(secs, secs[1:]):
        if s0[3] <= z <= s1[3]:
            t = (z - s0[3]) / max(1e-9, s1[3] - s0[3])
            return s0[0] + t * (s1[0] - s0[0]), s0[1] + t * (s1[1] - s0[1])
    return secs[-1][0], secs[-1][1]


if __name__ == "__main__":
    import time
    t0 = time.time()
    bo, bi = loft(base_sections()), loft(base_sections(S8.BASE["wall"]))
    to, ti = loft(torso_sections()), loft(torso_sections(S8.TORSO["wall"]))
    for nm, s in (("base outer", bo), ("base inner", bi), ("torso outer", to), ("torso inner", ti)):
        bb = s.bounding_box()
        print(f"{nm:12s} valid={s.is_valid} size=({bb.size.X:.1f}, {bb.size.Y:.1f}, {bb.size.Z:.1f}) zmin={bb.min.Z:.1f}")
    print("torso half-width at the shoulder axis z", S8.ARM["axis"]["z"], "->",
          tuple(round(v, 2) for v in torso_half_width(S8.ARM["axis"]["z"])), f"{time.time() - t0:.1f}s")
