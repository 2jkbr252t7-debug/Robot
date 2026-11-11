"""export fine STLs of the bare outer lofts (and front-facing copies rotated 180 deg about Z, because zebra.py looks
from the back / the robot's right) for the zebra (reflection-line) check -> tmp/zb_*.stl"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exterior as E
from build123d import Rot, Pos, Location, export_stl


def scaled(s, f):
    c = s.bounding_box().center()
    return Pos(c.X, c.Y, c.Z) * (Pos(-c.X, -c.Y, -c.Z) * s).scale(f)

OUT = os.path.dirname(os.path.abspath(__file__))
items = {
    "torso": E.torso_outer(),
    "torso_front": Rot(0, 0, 180) * E.torso_outer(),
    "base": E.base_outer(),
    "base_front": Rot(0, 0, 180) * E.base_outer(),
    "arm_in": scaled(E.arm_outer_L(), 1.6),                 # zboku camera (-X) sees the inner face of the left arm
    "arm_out": scaled(Rot(0, 0, 180) * E.arm_outer_L(), 1.6),   # rotated: the outer face looks to -X
    "torso_top": Rot(-90, 0, 0) * E.torso_outer(),          # +Z -> +Y: the 'zozadu' cameras look at the top
    "base_top": Rot(-90, 0, 0) * E.base_outer(),
}
if len(sys.argv) > 1:
    items = {k: v for k, v in items.items() if k in sys.argv[1:]}
for k, s in items.items():
    export_stl(s, f"{OUT}/tmp/zb_{k}.stl", tolerance=0.002, angular_tolerance=0.02)
    print("zebra stl", k, flush=True)
