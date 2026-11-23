"""fix-back V2, own measurement on the STEP solids: travel of skr_F12_1 along +y against the seated lift module and the ear"""
import os
from build123d import import_step, Pos, Cylinder, Box, Location, Rot, Plane
T4 = "/tmp/claude-0/gapwf/fin/T4"
ld = lambda n, d="step": import_step(os.path.join(T4, d, n + ".step"))
scr = ld("skr_F12_1"); mod = ld("P_drziak_serva"); ear = ld("L_ucho")
S = scr.solids()[0]; M = mod.solids()[0]; E = ear.solids()[0]


def vol(a):
    if a is None:
        return 0.0, None
    ss = a.solids() if hasattr(a, "solids") else [s for x in a for s in x.solids()]
    if not ss:
        return 0.0, None
    lo = [min(tuple(s.bounding_box().min)[i] for s in ss) for i in range(3)]; hi = [max(tuple(s.bounding_box().max)[i] for s in ss) for i in range(3)]
    return sum(s.volume for s in ss), tuple(round(v, 2) for v in lo + hi)


for t in [0.0, 1.0, 2.0, 2.3, 2.4, 2.45, 2.5, 3.0, 6.0, 12.0, 18.5, 18.6, 18.7, 19.0, 20.0, 25.0]:
    m = S.moved(Location((0, t, 0)))
    va, ba = vol(m.intersect(M)); vb, bb_ = vol(m.intersect(E))
    print("t %5.2f  & module %.4f %s  & ear %.4f %s" % (t, va, ba or "", vb, bb_ or ""))
for y0, y1 in ((9.9, 11.4), (11.4, 12.0), (12.0, 13.0), (13.0, 14.0), (14.0, 15.1), (15.1, 17.0), (17.0, 25.1)):
    v, q = vol(E.intersect(Pos(-13, (y0 + y1) / 2, -36) * Box(30, y1 - y0, 20)))
    print("ear slab y %.1f..%.1f: vol %.2f bbox %s" % (y0, y1, v, q))
