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
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.normal_update(); bpy.data.objects.remove(o); return bm
T={}
for n in ["T_stred","T_bok_L","T_dvere"]:
    T[n]=BVHTree.FromBMesh(load(n), epsilon=0.0)
for zz in (-50.0,-10.0):
  for side in (-1,1):
    for xx in (33.0, 33.2, 33.3, 33.4, 33.6):
        p0=np.array([xx, C.y_surface(xx, zz, side), zz]); n0=Vector(O.normal(np.array([p0]))[0])
        out=[]
        for n,t in T.items():
            h=t.ray_cast(Vector(p0)+n0*4, -n0, 30)
            out.append((n, None if h[0] is None else round(h[3]-4,3)))
        print(zz, side, xx, [round(float(v),3) for v in n0], out)
# door seam
for zz in (-42.0,):
    for xx in (27.9, 28.05, 28.125, 28.2, 28.4):
        p0=np.array([xx, C.y_surface(xx, zz, 1), zz]); n0=Vector(O.normal(np.array([p0]))[0])
        out=[]
        for n,t in T.items():
            h=t.ray_cast(Vector(p0)+n0*4, -n0, 30)
            out.append((n, None if h[0] is None else round(h[3]-4,3)))
        print('door', xx, [round(float(v),3) for v in n0], out)
