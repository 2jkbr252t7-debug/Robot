import sys, time, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
bd = C._bd()
# local frame
pl = bd.Plane(origin=(25, 34.4, -24), x_dir=(0.935, -0.354, 0), z_dir=(-0.349, -0.922, -0.166))
loc = pl.location
b = loc * (bd.Pos(0, 0, 5.95) * bd.Cylinder(4.0, 2.5))
print("local cyl", type(b), b.volume, b.bounding_box())
# cone
c = bd.Pos(0, 0, -6.6 + 4.8) * bd.Cone(30.6, 30.6 + 9.6, 9.6)
print("cone", c.volume, c.bounding_box())
# wedge
w = bd.extrude(bd.Face(bd.Wire.make_polygon([bd.Vector(0, 0, -12), bd.Vector(80 * np.cos(np.radians(50)), 80 * np.sin(np.radians(50)), -12),
                                             bd.Vector(80 * np.cos(np.radians(130)), 80 * np.sin(np.radians(130)), -12)], close=True)), amount=17)
print("wedge", w.volume, w.bounding_box(), type(w))
g = c & w
print("gusset", type(g), g.volume)
# revolve
pts = [(38.4, 0), (38.4, 11), (40.6, 11), (40.6, 13.5), (50, 13.5), (50, 0)]
f = bd.Face(bd.Wire.make_polygon([bd.Vector(x, r, 0) for x, r in pts], close=True))
r = bd.revolve(f, axis=bd.Axis.X, revolution_arc=360)
print("revolve", type(r), r.volume, r.is_valid, r.bounding_box())
m = bd.mirror(r, about=bd.Plane.YZ)
print("mirror", type(m), m.volume, m.bounding_box())
# spline extrude along X
th = np.linspace(0, 2 * np.pi, 60, endpoint=False)
wsp = bd.Wire([bd.Edge.make_spline([bd.Vector(33.05, 20 * np.cos(t), 30 * np.sin(t)) for t in th], periodic=True)])
e = bd.extrude(bd.Face(wsp), amount=2.0, dir=(-1, 0, 0))
print("extr", type(e), e.volume, e.bounding_box())
# multi fuse / cut
a = C.box(0, 10, 0, 10, 0, 10)
r2 = a.fuse(C.cyl_z(2, 5, 15, 5, 5), C.cyl_x(2, 5, 15, 5, 5))
print("fuse", type(r2), r2.volume, len(r2.solids()))
r3 = a.cut(C.cyl_z(2, -1, 11, 5, 5), C.cyl_x(2, -1, 11, 5, 5))
print("cut", type(r3), r3.volume, len(r3.solids()))
# loft of two rect wires
def rect(y, hx, hz, zc):
    return bd.Wire.make_polygon([bd.Vector(-hx, y, zc - hz), bd.Vector(hx, y, zc - hz), bd.Vector(hx, y, zc + hz), bd.Vector(-hx, y, zc + hz)], close=True)
l = bd.Solid.make_loft([rect(-30.9, 14.4, 1.5, -32.5), rect(-37.5, 15.5, 2.1, -32.5)])
print("loft", l.volume, l.is_valid)
print("screw", C.screw("M2", 6, (19.5, -29.4, -32.5), "y", -1).bounding_box())
print("insert", C.insert("M2.5", (29, 19, -81), "z", 1).bounding_box())
