import bpy, bmesh, sys, os, math
sys.argv = [sys.argv[0], "--", "--shot", "none"]
__file__ = "/tmp/claude-0/gapwf/fin/R2c/img/work/v2b_scene.py"; sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R2c/img/work")
os.chdir("/tmp/claude-0/gapwf/fin/R2c/img/work")
exec(open("v2b_scene.py").read().split("# ================================================================================================ shots (B1+ fixer)")[0])
o = imp(os.path.join(ST, "vypln.stl"), "vypln_L", "cierna", sm=False)
bm = bmesh.new(); bm.from_mesh(o.data)
print("raw verts", len(bm.verts), "nonmanifold edges", sum(1 for e in bm.edges if not e.is_manifold))
bm.free()
vox_smooth(o)
bm = bmesh.new(); bm.from_mesh(o.data)
print("smoothed verts", len(bm.verts), "faces", len(bm.faces), "nonmanifold edges", sum(1 for e in bm.edges if not e.is_manifold))
P = world_verts(o); print("bbox", P.min(0).round(2), P.max(0).round(2))
bm.free()
names = [o.name for o in sc.objects]
section_y([o], G.YA, REZ_CROP if "REZ_CROP" in dir() else (18.0, 84.0, -84.0, 3.0))
bm = bmesh.new(); bm.from_mesh(o.data)
print("after cut verts", len(bm.verts), "faces", len(bm.faces), "nonmanifold", sum(1 for e in bm.edges if not e.is_manifold))
mats = [m.name if m else None for m in o.data.materials]
cnt = {}
for f in bm.faces:
    cnt[f.material_index] = cnt.get(f.material_index, 0) + 1
print("materials", mats, cnt)
P = world_verts(o); print("bbox", P.min(0).round(2), P.max(0).round(2))
