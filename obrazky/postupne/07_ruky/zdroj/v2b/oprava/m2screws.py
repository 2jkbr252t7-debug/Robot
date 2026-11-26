"""FIXER: plug screw lengths (countersunk M2, DIN 965 / ISO 7046-1; length includes the head) at r 9.0, 12/4/8 o'clock.
plug face x = t4_common.x_surface(y, z) - 1.0 (recess), boss x 34.4..38.4, insert M2 L 4.0 glued from x 38.4 inward (x 34.4..38.4).
engagement = 38.4 - tip_x (capped at the insert length); tip must stay >= 0.3 inside the boss back face (x >= 34.7)."""
import sys, json, math
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v2/work")
import t4_common as C, g2 as G
out = {}
for hh in (12, 4, 8):
    y, z = G.clock_pt(hh, 9.0)
    face = float(C.x_surface(y, z)) - 1.0
    row = dict(y=round(y, 2), z=round(z, 2), face_x=round(face, 2))
    for L in (6, 8, 10, 12, 16):
        tip = face - L
        row[f"M2x{L}"] = dict(tip_x=round(tip, 2), engaged=round(min(38.4 - tip, 4.0), 2), tip_inside_boss=bool(tip >= 34.7))
    out[f"{hh} o'clock"] = row
    print(hh, json.dumps(row))
json.dump(out, open("m2screws.json", "w"), indent=1)
