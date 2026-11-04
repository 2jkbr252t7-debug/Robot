"""Concept study: tilt axis A) in the head centre via ear pivots + U yoke, B) 15 mm up in the head with a hidden drum.
Both with a smooth conical neck whose base follows the domed torso top. Coordinates: torso top z = 0."""
import json, math, sys
sys.path.insert(0, "/home/user/Robot")
import numpy as np
from build123d import (Axis, Box, BuildSketch, Cylinder, Edge, Face, Location, Plane, Pos, RectangleRounded, Rot, Solid,
                       Vector, Wire, extrude, fillet, revolve)
from nova.cad.common import PartRec, export_parts
from nova_mini import hlava_skrupina as HS
from nova_v8 import klasik as KL
OUT = "/tmp/claude-0/concepts/neckaxis"
torso = KL.loft(KL.torso_secs()).moved(Location((0, 0, -117.0)))
# torso top profile along +X (highest direction): (a, z) of the dome sections
secs = [(a, z - 117.0) for a, b, n, z in KL.torso_secs()]
secs = sorted([s for s in secs if s[1] > -25], key=lambda s: s[0])
def z_dome(r):
    if r <= secs[0][0]:
        return 0.0
    for (a0, z0), (a1, z1) in zip(secs, secs[1:]):
        if a0 <= r <= a1:
            return z0 + (z1 - z0) * (r - a0) / (a1 - a0)
    return secs[-1][1]

def cone(R0, r1, z_top, p=2.0, gap=0.6, rim=0.8):
    """smooth trumpet neck, revolved; the underside follows the torso dome (+gap)"""
    n = 40
    flare = []
    for i in range(n + 1):
        t = i / n
        zb = z_dome(R0) + gap + rim
        z = zb + (z_top - zb) * t
        flare.append((r1 + (R0 - r1) * (1 - t) ** p, z))
    under = [(R0 * (1 - i / 20), z_dome(R0 * (1 - i / 20)) + gap) for i in range(21)]
    pts_out = [Vector(r, 0, z) for r, z in reversed(flare)]          # top -> base rim
    e_fl = Edge.make_spline(pts_out)
    e_rim = Edge.make_line(pts_out[-1], Vector(R0, 0, under[0][1]))
    e_un = Edge.make_spline([Vector(r, 0, z) for r, z in under])
    e_ax = Edge.make_line(Vector(0, 0, under[-1][1]), Vector(0, 0, z_top))
    e_top = Edge.make_line(Vector(0, 0, z_top), pts_out[0])
    face = Face(Wire([e_top, e_fl, e_rim, e_un, e_ax]))
    s = revolve(face, Axis.Z, 360)
    try:
        s = fillet([e for e in s.edges() if abs(e.center().Z - under[0][1]) < rim + 0.2 and e.center().Z < under[0][1] + 1.5
                    and math.hypot(e.center().X, e.center().Y) > R0 - 2], rim)
    except Exception as ex:
        print("rim fillet skipped", ex)
    return s

def head_parts(hb, cut=None):
    s = HS.build_common()
    with BuildSketch(Plane.XZ.offset(-(HS.Y0 - 0.0))) as sk:
        RectangleRounded(HS.OPEN_W - 1.0, HS.OPEN_H - 1.0, HS.OPEN_R - 0.5)
    frame = extrude(sk.sketch, amount=-4.0).moved(Location((0, 0, HS.H / 2)))
    ears = None
    for sx in (-1, 1):
        e = Pos(sx * (HS.W / 2 - 1.0), HS.EAR_Y, HS.EAR_Z) * Rot(0, 90, 0) * Cylinder(HS.EAR_D / 2 - 0.1, 2.0)
        ears = e if ears is None else ears + e
    mv = Location((0, 0, hb))
    s, frame, ears = s.moved(mv), frame.moved(mv), ears.moved(mv)
    if cut is not None:
        s = s - cut
    return s, frame, ears

recs = []
def add(pid, shape, mat):
    recs.append(PartRec(pid, pid, shape, mat, "neck", ""))

add("TORSO", torso, "white")
# ---------------- A: ear pivots + U yoke, axis at the ear centre (head mid-height)
A_HB = 36.0
A_ax_y, A_ax_z = HS.EAR_Y, A_HB + HS.EAR_Z
z_bar = A_ax_z - 53.0                     # bar centre line (head front corner passes 1.4 mm above at 40°)
yoke_w, arm_t, bar_t = 14.0, 6.0, 8.0
xo = HS.W / 2 + 1.0 + arm_t               # outer x of the arms
with BuildSketch(Plane.XZ) as sk:
    RectangleRounded(2 * xo, 2 * (A_ax_z - (z_bar - bar_t / 2)), 22.0)
outer = extrude(sk.sketch, amount=yoke_w / 2, both=True).moved(Location((0, A_ax_y, A_ax_z)))
with BuildSketch(Plane.XZ) as sk:
    RectangleRounded(2 * (xo - arm_t), 2 * (A_ax_z - (z_bar + bar_t / 2)), 16.0)
inner = extrude(sk.sketch, amount=yoke_w, both=True).moved(Location((0, A_ax_y, A_ax_z)))
yoke = (outer - inner) & (Pos(0, A_ax_y, A_ax_z - 100) * Box(300, 100, 200))       # keep below the axis
for sx in (-1, 1):
    yoke = yoke + Pos(sx * (xo - arm_t / 2), A_ax_y, A_ax_z) * Rot(0, 90, 0) * Cylinder(13.0, arm_t)
try:
    yoke = fillet(yoke.edges(), 2.0)
except Exception as ex:
    print("yoke fillet", ex)
A_cone = cone(24.0, 9.0, z_bar - bar_t / 2 + 1.0, p=2.0)
add("A_CONE", A_cone, "black_satin"); add("A_YOKE", yoke, "black_satin")
axA = Axis((0, A_ax_y, A_ax_z), (1, 0, 0))
for tag, ang in (("0", 0), ("D", 40), ("U", -40)):
    h, f, e = head_parts(A_HB)
    if ang:
        h, f = h.rotate(axA, ang), f.rotate(axA, ang)
    add(f"A_HEAD{tag}", h, "white"); add(f"A_FRAME{tag}", f, "black_gloss")
    print("A", tag, "head&yoke", round((h & yoke).volume if (h & yoke) else 0, 2), "head&cone",
          round((h & A_cone).volume if (h & A_cone) else 0, 2), "head&torso", round((h & torso).volume if (h & torso) else 0, 2), flush=True)
# ---------------- B: axis 15 mm up in the head, drum R20 mostly hidden
B_HB = 27.0
B_h, B_R = 12.0, 21.0
B_ax_z = B_HB + B_h
drum = Pos(0, 0, B_ax_z) * Rot(0, 90, 0) * Cylinder(B_R, 36.0)
drum = fillet(drum.edges(), 3.0)
B_cone = cone(25.0, 5.0, B_ax_z - B_R + 1.0, p=0.95)
B_neck = drum + B_cone
add("B_NECK", B_neck, "black_satin")
cutB = Pos(0, 0, B_ax_z) * Rot(0, 90, 0) * Cylinder(B_R + 0.5, 37.0)
axB = Axis((0, 0, B_ax_z), (1, 0, 0))
for tag, ang in (("0", 0), ("D", 40), ("U", -40)):
    h, f, e = head_parts(B_HB, cut=cutB)
    if ang:
        h, f, e = h.rotate(axB, ang), f.rotate(axB, ang), e.rotate(axB, ang)
    add(f"B_HEAD{tag}", h, "white"); add(f"B_FRAME{tag}", f, "black_gloss"); add(f"B_EARS{tag}", e, "black_satin")
    print("B", tag, "head&cone", round((h & B_cone).volume if (h & B_cone) else 0, 2), "head&torso",
          round((h & torso).volume if (h & torso) else 0, 2), flush=True)
export_parts(recs, "na", step=False, out_dir=OUT)
from build123d import export_stl
for r in recs:
    export_stl(r.shape, f"{OUT}/stl/{r.id}.stl", tolerance=0.01, angular_tolerance=0.06)
json.dump(dict(A_ax=[A_ax_y, A_ax_z], B_ax=B_ax_z, A_HB=A_HB, B_HB=B_HB), open(f"{OUT}/meta.json", "w"))
print("ok")
