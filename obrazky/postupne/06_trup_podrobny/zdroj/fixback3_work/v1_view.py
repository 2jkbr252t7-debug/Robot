"""fix-back V1: is the sole / curb line visible from BELOW the stage on the bench (light test), and reachable by a feeler?"""
import os
from build123d import import_step, Pos, Box
T4 = "/tmp/claude-0/gapwf/fin/T4"
ld = lambda n: import_step(os.path.join(T4, "step", n + ".step")).solids()[0]
W, M, G = ld("P_sachta"), ld("P_drziak_serva"), ld("koleso_pan")
box = lambda x0, x1, y0, y1, z0, z1: Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def vol(a):
    if a is None:
        return 0.0, None
    ss = a.solids() if hasattr(a, "solids") else [s for x in a for s in x.solids()]
    if not ss:
        return 0.0, None
    lo = [min(tuple(s.bounding_box().min)[i] for s in ss) for i in range(3)]; hi = [max(tuple(s.bounding_box().max)[i] for s in ss) for i in range(3)]
    return round(sum(s.volume for s in ss), 3), tuple(round(v, 2) for v in lo + hi)


for nm, S in (("well", W), ("module", M), ("gear", G)):
    print(nm, "below the seat line, slab y 14.0..16.5, x -16.9..-8.9, z -60..-41.95:", vol(S.intersect(box(-16.9, -8.9, 14.0, 16.5, -60, -41.95))))
    print(nm, "                     wider y 12..20:", vol(S.intersect(box(-16.9, -8.9, 12.0, 20.0, -60, -41.95))))
print("slit top open to the window (well material in x -16.9..-8.9, y 13.0..15.1, z -40.6..-38):", vol(W.intersect(box(-16.9, -8.9, 13.0, 15.1, -40.6, -38.0))))
print("module behind the seat (x -16.9..-8.9, y 15.1..15.6, z -40.6..-38):", vol(M.intersect(box(-16.9, -8.9, 15.1, 15.6, -40.6, -38.0))))
