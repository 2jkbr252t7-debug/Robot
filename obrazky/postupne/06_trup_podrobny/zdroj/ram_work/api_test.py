import sys, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
import build123d as bd
t=time.time()
a = C.box(0,10,0,10,0,10); b = C.cyl_z(3,5,15,5,5); c = C.box(8,20,2,4,2,4)
f = a.fuse(b, c)
print(type(f), f.is_valid, len(f.solids()), round(f.volume,2), time.time()-t)
g = a + [b, c]
print(type(g), g.is_valid, len(g.solids()), round(g.volume,2))
h = f.cut(C.cyl_z(1,-1,20,5,5), C.box(9,21,2.5,3.5,2.5,3.5))
print(type(h), h.is_valid, len(h.solids()), round(h.volume,2))
# polygon prism
pts=[bd.Vector(0,0,0), bd.Vector(5,0,0), bd.Vector(5,0,5)]
w = bd.Wire.make_polygon(pts, close=True); fc = bd.Face(w)
p = bd.extrude(fc, amount=3, dir=(0,1,0))
print(type(p), p.is_valid, p.volume, p.bounding_box())
p2 = bd.extrude(fc, amount=3, dir=(0,-1,0)); print(p2.bounding_box())
# loft ruled
import numpy as np
w1 = C._wire(np.array([[10*np.cos(t),6*np.sin(t),0] for t in np.linspace(0,2*np.pi,40,endpoint=False)]))
w2 = C._wire(np.array([[9*np.cos(t),5*np.sin(t),1] for t in np.linspace(0,2*np.pi,40,endpoint=False)]))
l = bd.Solid.make_loft([w1,w2], True); print("loft", l.is_valid, l.volume)
# cone
k = bd.Cone(3,1,2); print(k.bounding_box())
t=time.time(); cb = C.cap_blank(); print("cap_blank load", time.time()-t, cb.is_valid)
