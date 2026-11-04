"""Soft, pillow-like head (user reference photo): superellipse sections along the depth, big round back,
rounded front rim, black glass face recessed 1.5 mm inside the white rim. Head coordinates: bottom z=0 at the
middle, y=0 head centre, front -Y."""
import math, sys
sys.path.insert(0, "/home/user/Robot")
from build123d import Edge, Wire, Vector, Solid, Pos, Rot, Cylinder, Box
from nova.cad.common import superellipse_pts

W, H, D = 106.0, 74.0, 66.0
YF, YB = -D / 2, D / 2
N = 3.0                       # front-view squareness (lower = rounder)
R_BACK, R_FRONT = 30.0, 9.0   # side-profile rounds (back big, front smaller)
GLASS_IN, GLASS_REC, GLASS_T = 3.2, 1.5, 6.0


def factor(y):
    f = 1.0
    if y > YB - R_BACK:                                   # big round back
        s = min(1.0, (y - (YB - R_BACK)) / R_BACK)
        f = 0.30 + 0.70 * math.sqrt(max(0.0, 1 - s * s))
    if y < YF + R_FRONT:                                  # soft front rim
        s = min(1.0, ((YF + R_FRONT) - y) / R_FRONT)
        f = min(f, 0.86 + 0.14 * math.sqrt(max(0.0, 1 - s * s)))
    return f


def sec(y, shrink=0.0, count=120):
    k = factor(y)
    a, b = W / 2 * k - shrink, H / 2 * (0.25 + 0.75 * k) - shrink
    pts = [Vector(x, y, H / 2 + z) for x, z in superellipse_pts(a, b, N, count)]
    return Wire([Edge.make_spline(pts, periodic=True, parameters=[i / len(pts) for i in range(len(pts) + 1)])])


def ys(y0, y1, n):
    # denser near the ends (rounds)
    return [y0 + (y1 - y0) * (0.5 - 0.5 * math.cos(math.pi * i / n)) for i in range(n + 1)]


def outer():
    return Solid.make_loft([sec(y) for y in ys(YF, YB - 0.4, 34)])


def glass_cut():
    """the front recess (filled by the black glass) – a shrunken front section prism"""
    s0 = sec(YF + R_FRONT, shrink=GLASS_IN)
    w0 = s0.moved(Pos(0, -R_FRONT - 2.0, 0))
    w1 = s0.moved(Pos(0, GLASS_T - R_FRONT, 0))
    return Solid.make_loft([w0, w1])


def glass():
    s0 = sec(YF + R_FRONT, shrink=GLASS_IN + 0.15)
    w0 = s0.moved(Pos(0, -R_FRONT + GLASS_REC, 0))
    w1 = s0.moved(Pos(0, GLASS_T - R_FRONT, 0))
    return Solid.make_loft([w0, w1])


def ears(ear_y=-1.0, ear_z=37.0):
    """black ear disc with a cyan LED ring, sitting on the bulged side"""
    k = factor(ear_y)
    xs = W / 2 * k
    disc, ring = None, None
    for sx in (-1, 1):
        d = Pos(sx * (xs + 1.2), ear_y, ear_z) * Rot(0, 90, 0) * Cylinder(13.0, 7.0)     # ear sticks out ~4.7 mm
        r = Pos(sx * (xs + 4.85), ear_y, ear_z) * Rot(0, 90, 0) * (Cylinder(10.5, 0.4) - Cylinder(8.6, 0.6))
        disc = d if disc is None else disc + d
        ring = r if ring is None else ring + r
    return disc, ring


if __name__ == "__main__":
    import time
    t = time.time()
    o = outer(); print("outer", o.is_valid, o.bounding_box().min, o.bounding_box().max, round(time.time() - t, 1))
    g = glass(); c = glass_cut(); print("glass", g.is_valid, c.is_valid)
    w = o - c; print("white", w.is_valid, round(w.volume))


VISOR_T, VISOR_IN = 7.0, 2.5


def white_cut():
    """everything in front of the white shell's front face"""
    return Pos(0, YF + VISOR_T / 2 - 1.0, H / 2) * Box(W + 4, VISOR_T + 2.0, H + 4)


def visor():
    return Solid.make_loft([sec(y, shrink=VISOR_IN) for y in ys(YF, YF + VISOR_T + 0.4, 10)])
