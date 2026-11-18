"""list the BREP faces of P_sachta (type, radius, bbox) - finds the real fillet radii and the faces at the well bottom"""
import json, sys
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Torus, GeomAbs_Plane, GeomAbs_Cone, GeomAbs_BSplineSurface
name = sys.argv[1] if len(sys.argv) > 1 else "P_sachta"
s = bd.import_step(f"/tmp/claude-0/gapwf/fin/T4/step/{name}.step")
sol = s.solids()[0] if hasattr(s, "solids") else s
print(name, "valid", sol.is_valid, "volume", round(sol.volume, 2), "faces", len(sol.faces()))
TN = {GeomAbs_Cylinder: "cyl", GeomAbs_Torus: "torus", GeomAbs_Plane: "plane", GeomAbs_Cone: "cone", GeomAbs_BSplineSurface: "bspl"}
rows = []
for f in sol.faces():
    a = BRepAdaptor_Surface(f.wrapped); t = a.GetType(); bb = f.bounding_box()
    r = None; ax = None
    if t == GeomAbs_Cylinder:
        c = a.Cylinder(); r = c.Radius(); d = c.Axis().Direction(); p = c.Axis().Location(); ax = [round(d.X(), 3), round(d.Y(), 3), round(d.Z(), 3), round(p.X(), 3), round(p.Y(), 3), round(p.Z(), 3)]
    elif t == GeomAbs_Torus:
        c = a.Torus(); r = (c.MajorRadius(), c.MinorRadius())
    elif t == GeomAbs_Cone:
        c = a.Cone(); r = (c.RefRadius(), c.SemiAngle())
    rows.append(dict(type=TN.get(t, str(t)), r=r, ax=ax, area=round(f.area, 3),
                     bb=[round(v, 3) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)]))
json.dump(rows, open(f"g01_faces_{name}.json", "w"), indent=0)
from collections import Counter
print(Counter(r["type"] for r in rows))
# small cylinders (fillet candidates) r <= 3
for r in sorted(rows, key=lambda q: q["bb"][4]):
    if r["type"] in ("cyl", "torus", "bspl", "cone") and (r["type"] != "cyl" or r["r"] < 3.0):
        print(r["type"], r["r"] if not isinstance(r["r"], float) else round(r["r"], 3), r["ax"], r["area"], r["bb"])
