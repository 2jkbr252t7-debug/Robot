"""fix-back: own BREP measurements for V1 (sight line of the sole / curb gap on the bench), V3, V5, V6, V7"""
import os, json, math
from build123d import import_step, Pos, Cylinder, Box, Location, Rot
T4 = "/tmp/claude-0/gapwf/fin/T4"
ld = lambda n, d="step": import_step(os.path.join(T4, d, n + ".step")).solids()[0]


def vol(a):
    if a is None:
        return 0.0, None
    ss = a.solids() if hasattr(a, "solids") else [s for x in a for s in x.solids()]
    if not ss:
        return 0.0, None
    lo = [min(tuple(s.bounding_box().min)[i] for s in ss) for i in range(3)]; hi = [max(tuple(s.bounding_box().max)[i] for s in ss) for i in range(3)]
    return sum(s.volume for s in ss), tuple(round(v, 3) for v in lo + hi)


W = ld("P_sachta"); M = ld("P_drziak_serva"); E = ld("L_ucho")
box = lambda x0, x1, y0, y1, z0, z1: Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
print("== V1 seat: sole front face of the module / curb face of the well at y 15.1")
for nm, S in (("well", W), ("module", M)):
    for y0, y1 in ((14.6, 15.1), (15.1, 15.6)):
        print("  %s in x -17.5..-6, y %.1f..%.1f, z -41.9..-40.65:" % (nm, y0, y1), vol(S.intersect(box(-17.5, -6.0, y0, y1, -41.9, -40.65))))
print("  sight line along x from the -X side (x -45 .. -16.95, y 15.0 .. 15.2, z -41.85 .. -40.7): well", vol(W.intersect(box(-45, -16.95, 15.0, 15.2, -41.85, -40.7))),
      "module", vol(M.intersect(box(-45, -16.95, 15.0, 15.2, -41.85, -40.7))))
print("  sight line from below (z -60 .. -41.95, x -16.9 .. -8, y 15.0 .. 15.2): well", vol(W.intersect(box(-16.9, -8.0, 15.0, 15.2, -60, -41.95))),
      "module", vol(M.intersect(box(-16.9, -8.0, 15.0, 15.2, -60, -41.95))))
print("== V3 F10_A insert hole: probe cylinder r 1.95 on the axis (4.2, -15.8), y 9.0 .. 15.1")
for y0, y1 in ((9.0, 10.3), (10.3, 11.1), (11.1, 15.1)):
    c = Pos(4.2, (y0 + y1) / 2, -15.8) * Rot(90, 0, 0) * Cylinder(1.95, y1 - y0)
    print("  y %.1f..%.1f: well material inside r 1.95: %s" % (y0, y1, vol(W.intersect(c))))
c = Pos(4.2, 12.0, -15.8) * Rot(90, 0, 0) * Cylinder(2.3, 7.0)
print("  r 2.3, y 8.5..15.5:", vol(W.intersect(c)))
I = ld("vl_F10_A"); print("  insert bbox", vol(I)[1], " screw", vol(ld("skr_F10_A"))[1])
print("== V5 ear flange over the sill / curb")
print("  ear bbox", vol(E)[1]); print("  min distance L_ucho <-> P_sachta: %.4f" % E.distance_to(W))
print("  well top under the flange (x -19.4..-7.5, y 9.9..15.1, z -41..-40.4):", vol(W.intersect(box(-19.4, -7.5, 9.9, 15.1, -41.0, -40.4))))
print("== V7 pan spline tip against the floor")
SP = ld("servo_pan"); PN = ld("pastorok_pan")
print("  servo_pan bbox", vol(SP)[1], " pinion bbox", vol(PN)[1])
pb = PN.bounding_box(); ax = ((pb.min.X + pb.max.X) / 2, (pb.min.Y + pb.max.Y) / 2)
print("  pinion axis", tuple(round(v, 3) for v in ax), "r %.2f az %.1f" % (math.hypot(*ax), math.degrees(math.atan2(ax[1], ax[0])) % 360))
for r in (2.5,):
    for z1 in (-41.9, -41.75, -41.7, -41.65):
        c = Pos(ax[0], ax[1], (-42.7 + z1) / 2) * Cylinder(r, z1 + 42.7)
        print("   cylinder r %.1f on the pinion axis from the modelled tip -42.70 up to %.2f: well material %s" % (r, z1, vol(W.intersect(c))))
top = SP.intersect(box(ax[0] - 3, ax[0] + 3, ax[1] - 3, ax[1] + 3, -47.5, -42.0)); print("  servo_pan near the axis above z -47.5:", vol(top))
