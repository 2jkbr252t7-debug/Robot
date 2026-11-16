"""quick Blender preview of the OBAL module: imports stl/<name>.stl of parts_obal.json, renders iso / back / sections.
Sections are camera-clipped ortho views; back faces (= cut solids) are drawn in a flat 'cut' colour per material.
Usage: /opt/venv/bl/bin/python prev_obal.py -- --views iso,back,sec_x,sec_y [--res 600] [--samples 12] [--hide a,b] [--out prefix]"""
import bpy, sys, os, json, math, argparse
from mathutils import Vector

T4 = "/tmp/claude-0/gapwf/fin/T4"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--views", default="iso,sec_x")
ap.add_argument("--res", type=int, default=600)
ap.add_argument("--samples", type=int, default=12)
ap.add_argument("--hide", default="")
ap.add_argument("--only", default="")
ap.add_argument("--out", default=os.path.join(T4, "prev_obal_"))
ap.add_argument("--extra", default="")          # extra STL files (comma separated path:matkey)
ap.add_argument("--clip", type=float, default=0.0)   # section plane offset
ap.add_argument("--with-ram", action="store_true")   # also load the RAM module (parts_ram.json) for context
ap.add_argument("--tag", default="")                 # suffix of the output file names
A = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COLS = {  # mat: (base colour, roughness, metallic, cut colour)
    "resin_white": ((0.82, 0.82, 0.80), 0.35, 0.0, (0.95, 0.50, 0.15)),
    "resin_black": ((0.03, 0.03, 0.035), 0.35, 0.0, (0.30, 0.30, 0.42)),
    "resin_clear": ((0.35, 0.85, 0.95), 0.25, 0.0, (0.10, 0.60, 0.85)),
    "resin_grey": ((0.45, 0.45, 0.45), 0.5, 0.0, (0.55, 0.55, 0.20)),
    "petg": ((0.10, 0.10, 0.12), 0.5, 0.0, (0.45, 0.25, 0.55)),
    "pom": ((0.90, 0.86, 0.70), 0.4, 0.0, (0.75, 0.65, 0.20)),
    "magnet": ((0.75, 0.75, 0.80), 0.25, 1.0, (0.85, 0.15, 0.15)),
    "steel": ((0.60, 0.60, 0.62), 0.3, 1.0, (0.55, 0.55, 0.60)),
    "brass": ((0.85, 0.62, 0.20), 0.3, 1.0, (0.85, 0.62, 0.20)),
    "pcb": ((0.05, 0.35, 0.12), 0.5, 0.0, (0.05, 0.55, 0.15)),
    "bought": ((0.16, 0.16, 0.20), 0.5, 0.0, (0.20, 0.35, 0.60)),
}
MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    c, r, me, cut = COLS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = r; b.inputs["Metallic"].default_value = me
    out = nt.nodes["Material Output"]
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*cut, 1); em.inputs[1].default_value = 0.9
    geo = nt.nodes.new("ShaderNodeNewGeometry"); mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0]); nt.links.new(b.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    MATS[key] = m
    return m


recs = json.load(open(os.path.join(T4, "parts_obal.json")))
recs = recs["parts"] if isinstance(recs, dict) else recs
if A.with_ram and os.path.exists(os.path.join(T4, "parts_ram.json")):
    rj = json.load(open(os.path.join(T4, "parts_ram.json")))
    recs = recs + [r for r in (rj["parts"] if isinstance(rj, dict) else rj) if os.path.exists(os.path.join(T4, "stl", r["name"] + ".stl"))]
hide = set(A.hide.split(",")) if A.hide else set()
only = set(A.only.split(",")) if A.only else None
n = 0
for r in recs:
    if r["name"] in hide or (only and r["name"] not in only):
        continue
    fn = os.path.join(T4, "stl", r["name"] + ".stl")
    bpy.ops.wm.stl_import(filepath=fn)
    o = bpy.context.selected_objects[0]; o.name = r["name"]
    o.data.materials.clear(); o.data.materials.append(mat(r["mat"] if r["mat"] in COLS else "bought"))
    try:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
    except Exception:
        pass
    n += 1
for e in [x for x in A.extra.split(",") if x]:
    fn, key = e.split(":")
    bpy.ops.wm.stl_import(filepath=fn)
    o = bpy.context.selected_objects[0]
    o.data.materials.clear(); o.data.materials.append(mat(key))
print("imported", n, flush=True)

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
sc.render.threads_mode = "FIXED"; sc.render.threads = 2
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.6
sc.render.film_transparent = False
W = bpy.data.worlds.new("w"); sc.world = W; W.use_nodes = True
W.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.93, 0.95, 1)
W.node_tree.nodes["Background"].inputs[1].default_value = 0.9
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.type = "ORTHO"; cam_d.clip_end = 5000
sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 2.5; sun_d.angle = math.radians(20)
sun = bpy.data.objects.new("sun", sun_d); sc.collection.objects.link(sun)
CTR = Vector((0, 0, -42))
VIEWS = {   # name: (direction to camera, ortho scale, clip plane offset along the view dir from the centre or None, aspect)
    "iso": ((0.55, -1.0, 0.45), 150, None, 1.0),
    "back": ((-0.55, 1.0, 0.40), 150, None, 1.0),
    "under": ((0.3, -0.5, -1.0), 150, None, 1.0),
    "front": ((0, -1, 0), 135, None, 0.9),
    "sec_x": ((1, 0, 0), 125, 0.0, 1.0),        # section x = clip, seen from +X (left side of the robot)
    "sec_y": ((0, 1, 0), 135, 0.0, 0.9),        # section y = clip, seen from the back
    "sec_y_front": ((0, -1, 0), 135, 0.0, 0.9),
    "sec_z": ((0, 0, 1), 135, 0.0, 0.9),        # horizontal section, seen from above
    "sec_iso": ((0.9, -0.5, 0.35), 150, 0.0, 1.0),
    "inside_back": ((-0.35, 1.0, 0.25), 120, None, 1.0),     # looking into the door opening (hide T_dvere)
    "inside_front": ((0.0, 1.0, 0.12), 110, 0.0, 0.9),       # front wall from the inside (section y = clip)
    "side": ((1, 0, 0.0), 125, None, 1.0),
    "top": ((0, -0.001, 1), 135, None, 0.9),
}
for name in A.views.split(","):
    d, scale, clip, asp = VIEWS[name]
    dv = Vector(d).normalized()
    ctr = CTR.copy()
    if name == "sec_z":
        ctr = Vector((0, 0, 0))
    cam.location = ctr + dv * 600
    up = "Y"
    cam.rotation_euler = (-dv).to_track_quat("-Z", up).to_euler()
    cam_d.ortho_scale = scale
    cam_d.clip_start = 1.0 if clip is None else 600 - (clip + A.clip)
    sun.rotation_euler = (dv + Vector((0.25, 0.1, 0.5))).normalized().to_track_quat("Z", "Y").to_euler()
    sc.render.resolution_x = A.res; sc.render.resolution_y = int(A.res * asp)
    sc.render.filepath = A.out + name + A.tag + ".png"
    bpy.ops.render.render(write_still=True)
    print("VIEW", name, flush=True)
