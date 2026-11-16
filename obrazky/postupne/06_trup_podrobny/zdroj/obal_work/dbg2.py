import sys, os, json, math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
T4 = "/tmp/claude-0/gapwf/fin/T4"
sys.path.insert(0, T4)
import t4_common as C
import t4_obal as O
def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(T4, "stl", name + ".stl"))
    o = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(o.data); bpy.data.objects.remove(o); return bm
T={n:BVHTree.FromBMesh(load(n), epsilon=0.0) for n in ["T_stred","T_bok_L","T_spodok","T_ram"]}
for zz in (-80.75,-80.25,-79.75,-79.25,-78.75,-78.25,-77.75):
    p0=np.array([33.3, C.y_surface(33.3, zz, -1), zz]); n0=Vector(O.normal(np.array([p0]))[0])
    g=Vector((1,0,0)); d0=-n0; d0=(d0-g*d0.dot(g)).normalized(); t=g.cross(d0)
    out=[]
    for ang in (0,20,-20,40,-40):
        d=(d0*math.cos(math.radians(ang))+t*math.sin(math.radians(ang))).normalized()
        hits=[]
        for n,tr in T.items():
            h=tr.ray_cast(Vector(p0)-d*3.0, d, 60.0)
            if h[0] is not None: hits.append((round(h[3]-3,2), n))
        hits.sort()
        out.append((ang, [round(v,2) for v in d], hits[:2]))
    print(zz, [round(float(v),2) for v in p0], 'n', [round(v,2) for v in n0])
    for o in out: print('    ', o)
