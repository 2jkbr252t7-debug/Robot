"""fix-back V7: clearance of the STS3032 spline tip (modelled top -42.70) under the stage floor over the pan sweep (stage frame)"""
import os, math
from build123d import import_step, Pos, Cylinder
T4 = "/tmp/claude-0/gapwf/fin/T4"
W = import_step(os.path.join(T4, "step", "P_sachta.step")).solids()[0]
print("P_sachta bbox", tuple(round(v, 2) for v in (*tuple(W.bounding_box().min), *tuple(W.bounding_box().max))))


def vol(a):
    if a is None:
        return 0.0
    ss = a.solids() if hasattr(a, "solids") else [s for x in a for s in x.solids()]
    return sum(s.volume for s in ss)


R, AZ0, RS = 21.6, 254.286, 2.5         # pinion axis radius / azimuth at pan 0, probe radius (spline D4.8 -> r 2.4 + 0.1)
for pan in (-90, -80, -60, -45, -30, -15, 0, 15, 30, 45, 60, 80, 90, 100, 102, 105):
    az = math.radians(AZ0 - pan); x, y = R * math.cos(az), R * math.sin(az)
    out = []
    for z1 in (-41.90, -41.72, -41.68, -41.5):
        c = Pos(x, y, (-42.7 + z1) / 2) * Cylinder(RS, z1 + 42.7)
        out.append("%.2f: %.3f" % (z1, vol(W.intersect(c))))
    print("pan %4d  stage az %6.1f (x %6.2f y %6.2f): well material in the probe r %.1f from z -42.70 up to  %s" % (pan, (AZ0 - pan) % 360, x, y, RS, "  ".join(out)))
