"""Realistic comparison: (1) axis just under the head (current mechanism) with a smooth trumpet neck,
(2) B-lite: axis 8.2 mm in the head (max that fits: display in front, rounded back) – drum Ø34, head back edges R12,
black bezel.  Both with the trumpet neck on the domed torso.  torso top z = 0."""
import json, math, sys
sys.path.insert(0, "/home/user/Robot")
from build123d import (Axis, Box, BuildSketch, Cylinder, Edge, Face, GeomType, Location, Plane, Pos, RectangleRounded,
                       Rot, Solid, Vector, Wire, extrude, fillet, revolve, export_stl)
from nova.cad.common import PartRec, export_parts
from nova_mini import hlava_skrupina as HS
from nova_mini import krk as K1
from nova_mini import krk_b as KB
from nova_v8 import klasik as KL
OUT = "/tmp/claude-0/concepts/neckaxis2"
torso = KL.loft(KL.torso_secs()).moved(Location((0, 0, -117.0)))

def trumpet(R0, s1, z_top, p=1.6, gap=0.6):
    zb = KB.z_dome(R0) + gap + 1.0
    n = 48
    def s(z):
        u = min(1.0, max(0.0, (z_top - z) / (z_top - zb)))
        return s1 + (R0 - s1) * u ** p
    flare = [Vector(s(zb + (z_top - zb) * i / n), 0, zb + (z_top - zb) * i / n) for i in range(n + 1)]
    flare[0] = Vector(R0, 0, zb)
    under = [Vector(R0 * (1 - i / 24), 0, KB.z_dome(R0 * (1 - i / 24)) + gap) for i in range(25)]
    w = Wire([Edge.make_spline(under), Edge.make_line(under[-1], Vector(0, 0, z_top)),
              Edge.make_line(Vector(0, 0, z_top), flare[-1]), Edge.make_spline(list(reversed(flare))),
              Edge.make_line(flare[0], under[0])])
    sol = revolve(Face(w), Axis.Z, 360)
    try:
        sol = fillet([e for e in sol.edges() if e.geom_type == GeomType.CIRCLE and abs(e.radius - R0) < 0.05], 0.5)
    except Exception:
        pass
    return sol

def head_body(r_back):
    outer = HS.body(HS.W, HS.H, HS.D, HS.R_FV, r_back, HS.Y0)
    inner = HS.body(HS.W - 2 * HS.WALL, HS.H - 2 * HS.WALL, HS.D - HS.WALL + 1.0, HS.R_FV - HS.WALL, r_back - HS.WALL,
                    HS.Y0 - 1.0).moved(Location((0, 0, HS.WALL)))
    s = outer - inner
    with BuildSketch(Plane.XZ.offset(-(HS.Y0 - 1))) as sk:
        RectangleRounded(HS.OPEN_W, HS.OPEN_H, HS.OPEN_R)
    s = s - extrude(sk.sketch, amount=-(HS.WALL + 3)).moved(Location((0, 0, HS.H / 2)))
    for sx in (-1, 1):
        s = s - Pos(sx * (HS.W / 2), HS.EAR_Y, HS.EAR_Z) * Rot(0, 90, 0) * Cylinder(HS.EAR_D / 2, 10)
    return s

def frame_ears():
    with BuildSketch(Plane.XZ.offset(-HS.Y0)) as sk:
        RectangleRounded(HS.OPEN_W - 1.0, HS.OPEN_H - 1.0, HS.OPEN_R - 0.5)
    fr = extrude(sk.sketch, amount=-4.0).moved(Location((0, 0, HS.H / 2)))
    ears = None
    for sx in (-1, 1):
        e = Pos(sx * (HS.W / 2 - 1.0), HS.EAR_Y, HS.EAR_Z) * Rot(0, 90, 0) * Cylinder(HS.EAR_D / 2 - 0.1, 2.0)
        ears = e if ears is None else ears + e
    return fr, ears

recs = []
def add(pid, shape, mat):
    recs.append(PartRec(pid, pid, shape, mat, "neck", ""))
add("TORSO", torso, "white")
fr0, ears0 = frame_ears()
# ---------------- (1) axis just under the head: barrel Ø20 + caps (krk.py), trumpet neck
ax1 = K1.AX_Z
s1 = 8.0
core = K1.core_outer()
neck1 = trumpet(25.0, s1, ax1 - math.sqrt(K1.B_R ** 2 - s1 ** 2) + 0.9) + core
caps1 = K1.caps()
head1 = (head_body(HS.R_BACK).moved(Location((0, 0, K1.HEAD_Z0))))
sad, cut = K1.head_saddle_cut()
head1 = (head1 + sad) - cut
add("O_NECK", neck1, "black_satin")
axA = Axis((0, 0, ax1), (1, 0, 0))
for tag, ang in (("0", 0), ("D", 40), ("U", -40)):
    mv = Location((0, 0, K1.HEAD_Z0))
    parts = [("HEAD", head1, "white"), ("FRAME", fr0.moved(mv), "black_gloss"), ("EARS", ears0.moved(mv), "black_satin"),
             ("CAPS", caps1[0] + caps1[1], "black_satin")]
    for nm, sh, mat in parts:
        add(f"O_{nm}{tag}", sh.rotate(axA, ang) if ang else sh, mat)
    x = (head1.rotate(axA, ang) if ang else head1) & neck1
    print("(1)", tag, "head&neck", round(x.volume if x else 0, 2), flush=True)
# ---------------- (2) B-lite: axis 8.2 in the head, drum Ø34 at y +2, head back edges R12, bezel
HB, h, R, yA, L = 30.0, 8.2, 17.0, 2.0, 26.0
ax2 = HB + h
s2 = 6.0
drum = fillet((Pos(0, yA, ax2) * Rot(0, 90, 0) * Cylinder(R, L)).edges(), 3.0)
cone2 = trumpet(25.0, s2, ax2 - math.sqrt(R ** 2 - s2 ** 2) + 0.9).moved(Location((0, yA, 0)))
neck2 = drum + cone2
env = fillet((Pos(0, yA, ax2) * Rot(0, 90, 0) * Cylinder(R + 0.5, L + 1.0)).edges(), 3.5)
with BuildSketch(Plane.XY.offset(HB)) as sk:
    RectangleRounded(50.0, 46.0, 8.0)
opening = extrude(sk.sketch, amount=2.0).moved(Location((0, yA - 1.0, 0)))
with BuildSketch(Plane.XY.offset(HB - 1)) as sk:
    RectangleRounded(50.4, 46.4, 8.2)
hole = extrude(sk.sketch, amount=3.01).moved(Location((0, yA - 1.0, 0)))
head2 = head_body(12.0).moved(Location((0, 0, HB))) - hole - env
bez = opening - env
add("B_NECK", neck2, "black_satin")
axB = Axis((0, yA, ax2), (1, 0, 0))
for tag, ang in (("0", 0), ("D", 40), ("U", -40)):
    mv = Location((0, 0, HB))
    parts = [("HEAD", head2, "white"), ("FRAME", fr0.moved(mv), "black_gloss"), ("EARS", ears0.moved(mv), "black_satin"),
             ("BEZ", bez, "black_satin")]
    for nm, sh, mat in parts:
        add(f"B_{nm}{tag}", sh.rotate(axB, ang) if ang else sh, mat)
    hh = head2.rotate(axB, ang) if ang else head2
    bb = bez.rotate(axB, ang) if ang else bez
    x1, x2 = hh & neck2, bb & neck2
    print("(2)", tag, "head&neck", round(x1.volume if x1 else 0, 2), "bezel&neck", round(x2.volume if x2 else 0, 2),
          "head&torso", round((hh & torso).volume if (hh & torso) else 0, 2), flush=True)
export_parts(recs, "na2", step=False, out_dir=OUT)
for r in recs:
    export_stl(r.shape, f"{OUT}/stl/{r.id}.stl", tolerance=0.01, angular_tolerance=0.06)
# forward shift of the head centre at 40°
c1 = (37.0 - (K1.HEAD_Z0 - K1.AX_Z) * -1) if False else None
print("shift (1):", round((37.0 + (K1.HEAD_Z0 - K1.AX_Z)) * math.sin(math.radians(40)), 1),
      " (2):", round((37.0 - h) * math.sin(math.radians(40)), 1))
