"""Zebra (reflection-line) renders - extended copy of scratchpad/zebra/zebra.py (same shader: reflection Z -> stripes,
env ZF = stripe density) for several STLs at once and with front / top views.
Usage: blender-python zebra_f1.py <out_prefix> <views comma list> <stl> [<stl> ...]"""
import bpy, sys, math, os
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
out, views, stls = args[0], args[1].split(","), args[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
m = bpy.data.materials.new("z"); m.use_nodes = True
nt = m.node_tree; N = nt.nodes; L = nt.links
for n in list(N): N.remove(n)
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = float(os.environ.get("ZF", 28))
sn = N.new("ShaderNodeMath"); sn.operation = "SINE"; gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.0
em = N.new("ShaderNodeEmission"); outn = N.new("ShaderNodeOutputMaterial")
L.new(tc.outputs["Reflection"], sep.inputs[0]); L.new(sep.outputs[os.environ.get("ZAX", "Z")], mul.inputs[0]); L.new(mul.outputs[0], sn.inputs[0])
L.new(sn.outputs[0], gt.inputs[0]); L.new(gt.outputs[0], em.inputs["Strength"]); L.new(em.outputs[0], outn.inputs[0])
objs = []
for s in stls:
    bpy.ops.wm.stl_import(filepath=s)
    o = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    objs.append(o)
sc = bpy.context.scene
w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.3, 0.05, 0.05, 1); sc.world = w
cd = bpy.data.cameras.new("c"); cd.lens = 50; cd.clip_start = 1; cd.clip_end = 5000
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "CYCLES"; sc.cycles.samples = int(os.environ.get("ZS", 8)); sc.render.resolution_x, sc.render.resolution_y = 600, 600
lo = Vector((1e9,) * 3); hi = -lo
for o in objs:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
ctr = (lo + hi) / 2
R = max(hi - lo) * float(os.environ.get("ZR", 2.4))
V = {"zozadu34": (-170, 190, 30), "zozadu": (0, 260, 10), "zboku": (-260, 0, 0), "zozadu_zdola": (-90, 200, -120),
     "zpredu34": (170, -190, 40), "zpredu": (0, -260, 10), "zhora34": (120, -150, 170), "zdola34": (150, -170, -110),
     "zboku_L": (260, 0, 20)}
for nm in views:
    off = Vector(V[nm]).normalized() * R
    cam.location = ctr + off
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{nm}.png"
    bpy.ops.render.render(write_still=True)
