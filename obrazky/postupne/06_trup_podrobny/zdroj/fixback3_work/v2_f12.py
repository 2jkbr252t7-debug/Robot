# NOTE (fix-back): in this FIRST script the rows "screw moved +y by t -> overlap" are WRONG (all 0): the product / boolean of two imported
# Compounds returns a ShapeList whose volume is not summed here.  The valid travel test is fixback3_work/v2_f12b.py (solids, summed volumes).
# The probe-cylinder rows below are valid: r 1.20 passes the module on the F12 axis, r 1.25 does not (key hole D2.4, y 15.1 .. 31.3).
"""fix-back V2: own measurement on the STEP solids (BREP booleans, not mesh sampling): can skr_F12_1 travel along +y past the seated lift module?"""
import os, json
from build123d import import_step, Pos, Cylinder, Axis, Box, Location, Rot, Vector
T4 = "/tmp/claude-0/gapwf/fin/T4"
ld = lambda n, d="step": import_step(os.path.join(T4, d, n + ".step"))
bb = lambda s: tuple(round(v, 3) for v in (*tuple(s.bounding_box().min), *tuple(s.bounding_box().max)))
scr = ld("skr_F12_1"); mod = ld("P_drziak_serva"); ear = ld("L_ucho"); foot = ld("L_pata"); well = ld("P_sachta")
print("skr_F12_1 bbox", bb(scr), "vol", round(scr.volume, 3))
print("L_ucho bbox", bb(ear)); print("L_pata bbox", bb(foot)); print("P_drziak_serva bbox", bb(mod))
b = scr.bounding_box(); ax_x = (b.min.X + b.max.X) / 2; ax_z = (b.min.Z + b.max.Z) / 2
print("axis x %.3f z %.3f ; y %.3f .. %.3f" % (ax_x, ax_z, b.min.Y, b.max.Y))
# head / shank split: slice volumes
for y0, y1 in ((b.min.Y, b.max.Y - 1.35), (b.max.Y - 1.3, b.max.Y)):
    sl = scr & Pos(ax_x, (y0 + y1) / 2, ax_z) * Box(10, y1 - y0, 10)
    q = sl.bounding_box(); print("  slice y %.2f..%.2f: dx %.3f dz %.3f" % (y0, y1, q.max.X - q.min.X, q.max.Z - q.min.Z))
print("seated: overlap screw & module %.4f mm3, & ear %.4f, & foot %.4f (thread in the foot)" % ((scr & mod).volume, (scr & ear).volume, (scr & foot).volume))
rows = []
for t in [0.5, 1.0, 1.5, 2.0, 2.4, 2.5, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 19.5, 20.0, 21.0, 25.0]:
    m = Pos(0, t, 0) * scr
    vm = (m & mod).volume; rows.append((t, round(vm, 4)))
print("screw moved +y by t -> overlap with P_drziak_serva (mm3):", rows)
# free bore on the screw axis through the module: largest cylinder radius that passes, per y station
import numpy as np
print("probe cylinders on the F12 axis (y from the head back %.2f to 45):" % b.max.Y)
for r in (0.65, 1.0, 1.2, 1.25, 1.75, 1.9):
    cyl = Pos(ax_x, 0, ax_z) * Rot(90, 0, 0) * Cylinder(r, 60)          # axis along y, centred y 0 -> shift
    cyl = Pos(0, b.max.Y + 30.0, 0) * cyl
    inter = cyl & mod
    v = inter.volume
    yb = inter.bounding_box() if v > 1e-6 else None
    print("  r %.2f: overlap %.3f mm3" % (r, v), ("y %.2f..%.2f" % (yb.min.Y, yb.max.Y)) if yb else "FREE")
# module front face near the screw axis and the ear flange
print("module (P_drziak_serva) y min near the F12 axis:")
probe = Pos(ax_x, 20, ax_z) * Box(3.4, 30, 3.4)
q = (probe & mod).bounding_box(); print("   within +-1.7 of the axis: y %.3f .. %.3f" % (q.min.Y, q.max.Y))
q = (Pos(ax_x, 10, ax_z) * Box(6, 20, 6) & ear).bounding_box(); print("ear flange around the axis: y %.3f .. %.3f" % (q.min.Y, q.max.Y))
q = (Pos(ax_x, 8, ax_z) * Box(6, 20, 6) & foot).bounding_box(); print("foot around the axis: y %.3f .. %.3f" % (q.min.Y, q.max.Y))
# (the Pos * imported-compound product above gave 0 everywhere: use .moved)
rows = []
for t in [1.0, 2.0, 2.3, 2.4, 2.5, 3.0, 6.0, 12.0, 19.0, 19.7, 19.8, 20.0, 25.0]:
    m = scr.moved(Location((0, t, 0)))
    rows.append((t, round((m & mod).volume, 3), round((m & ear).volume, 3)))
print("screw.moved(+y t) -> (t, overlap with P_drziak_serva, with L_ucho):", rows)
# rev. 2 module for comparison
mod2 = ld("P_drziak_serva", "rev3_backup/step") if os.path.exists(os.path.join(T4, "rev3_backup/step/P_drziak_serva.step")) else None
print("rev. 2 STEP available:", mod2 is not None)
