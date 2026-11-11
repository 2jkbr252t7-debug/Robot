"""Quick Blender preview of an exported T1 layout (t1lib.Layout.export).
Usage: /opt/venv/bl/bin/python t1_preview.py --dir <export dir> --out <png prefix> [--real-head] [--res 700] [--samples 16]
        [--views iso,front,side,top,back,cut] [--cut-names T_shell,Z_base] [--cut-axis x] [--cut-keep neg]
  --real-head : replace the B_* envelopes by the real neck/head STLs of variant B rev. E2 (posed like their group)
  cut view    : the listed objects get a boolean cut (half removed) so the internals are visible; others stay whole
Writes <prefix>_<view>.png (opaque light-grey background) and <prefix>_views.json (camera matrices for labels:
use bpy_extras world_to_camera_view logic: px = (x_ndc * W, (1 - y_ndc) * H))."""
import bpy, sys, os, json, math, argparse
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--real-head", action="store_true")
ap.add_argument("--res", type=int, default=700)
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--views", default="iso,front,side,cut")
ap.add_argument("--cut-names", default="")
ap.add_argument("--cut-axis", default="x")
ap.add_argument("--cut-keep", default="neg")
ap.add_argument("--exposure", type=float, default=-0.6)
A = ap.parse_args(argv)
A.out = os.path.abspath(A.out)
A.dir = os.path.abspath(A.dir)

B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
B_GROUP = {"H": ["hlava_skrupina", "ram_displeja", "displej", "drziak_displeja", "magnety", "pena_displeja",
                 "oci_len_vizualizacia", "usi", "led_kruzky", "led_dosky", "usko_kryt", "usko_lozisko", "klzny_kruzok",
                 "paka"],
           "L": ["krk_predna_polovica", "krk_zadna_polovica", "servo_MG90S", "pena_serva", "capy", "kabel", "skrutky",
                 "loziska_MR85"],
           "P": ["golier_kotuc"], "T": ["golier_prstenec"]}
B_COLOR = {"hlava_skrupina": "white", "ram_displeja": "gloss_black", "displej": "glass", "usi": "black",
           "led_kruzky": "glow", "oci_len_vizualizacia": "eyes", "usko_kryt": "black", "usko_lozisko": "black",
           "krk_predna_polovica": "black", "krk_zadna_polovica": "black", "golier_kotuc": "black",
           "golier_prstenec": "black", "servo_MG90S": "servo", "kabel": "cable"}
COL = {"white": (0.92, 0.92, 0.90), "black": (0.06, 0.06, 0.07), "grey": (0.45, 0.46, 0.48),
       "servo": (0.16, 0.30, 0.62), "servo_bus": (0.10, 0.10, 0.12), "battery": (0.20, 0.55, 0.32),
       "pcb": (0.10, 0.42, 0.22), "elec": (0.12, 0.35, 0.65), "metal": (0.70, 0.70, 0.72), "cable": (0.95, 0.45, 0.10),
       "glow": (0.25, 0.85, 0.95), "rubber": (0.10, 0.10, 0.10), "motor": (0.75, 0.62, 0.30), "red": (0.85, 0.15, 0.12),
       "yellow": (0.95, 0.80, 0.15), "glass": (0.02, 0.02, 0.03), "gloss_black": (0.02, 0.02, 0.02),
       "eyes": (1.0, 0.85, 0.6)}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = A.samples
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = A.res
sc.view_settings.exposure = A.exposure
sc.render.film_transparent = False
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.93, 0.92, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = COL.get(key, COL["grey"])
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = 0.12 if key in ("glass", "gloss_black") else 0.42
    if key in ("glow", "eyes"):
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 3.0
    if key == "metal":
        b.inputs["Metallic"].default_value = 1.0
    MATS[key] = m
    return m


def imp(fn, name, key, M=None):
    bpy.ops.wm.stl_import(filepath=fn)
    o = bpy.context.selected_objects[0]
    o.name = name
    if M is not None:
        o.matrix_world = M
    o.data.materials.clear()
    o.data.materials.append(mat(key))
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    except Exception:
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
    return o


meta = json.load(open(os.path.join(A.dir, "parts.json")))
objs = []
for p in meta["parts"]:
    if A.real_head and p["name"].startswith("B_"):
        continue
    objs.append(imp(p["stl"], p["name"], p["color"]))
if A.real_head:
    dz = Matrix.Translation((0, 0, meta["dz_B"]))
    for g, names in B_GROUP.items():
        Mg = Matrix(meta["loc"][g]) @ dz
        for n in names:
            fn = os.path.join(B_STL, n + ".stl")
            if os.path.exists(fn):
                objs.append(imp(fn, "B_" + n, B_COLOR.get(n, "grey"), Mg))
# ---------------------------------------------------------------- bounds, lights
lo = Vector((1e9, 1e9, 1e9)); hi = -lo
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
ctr = (lo + hi) / 2
size = max(hi - lo)
bpy.ops.object.light_add(type="AREA", location=(ctr.x - 300, ctr.y - 400, ctr.z + 500))
key = bpy.context.active_object; key.data.energy = 2.2e6; key.data.size = 400
key.rotation_euler = (Vector(ctr) - key.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(ctr.x + 450, ctr.y + 150, ctr.z + 250))
fill = bpy.context.active_object; fill.data.energy = 9e5; fill.data.size = 500
fill.rotation_euler = (Vector(ctr) - fill.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat("floor") if False else bpy.data.materials.new("floor"))
floor.is_shadow_catcher = False
fm = floor.data.materials[0]; fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.86, 0.86, 0.85, 1)
cam_d = bpy.data.cameras.new("cam"); cam_d.clip_start = 1; cam_d.clip_end = 1e5
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {"iso": ((1.0, -1.45, 0.75), False), "front": ((0, -1, 0.0), True), "side": ((1, 0, 0), True),
         "back": ((0, 1, 0), True), "top": ((0, -0.001, 1), True), "cut": ((1.0, -1.45, 0.6), False),
         "cut_front": ((0, -1, 0), True), "cut_side": ((1, 0, 0), True), "iso_back": ((-1.0, 1.4, 0.7), False),
         "low": ((0.9, -1.5, 0.15), False)}
cutbox = None
info = {}
for v in A.views.split(","):
    d, ortho = VIEWS[v]
    if v.startswith("cut") and cutbox is None and A.cut_names:
        bpy.ops.mesh.primitive_cube_add(size=1)
        cutbox = bpy.context.active_object
        cutbox.scale = (3000, 3000, 3000)
        ax = "xyz".index(A.cut_axis)
        loc = [0, 0, 0]; loc[ax] = 1500 if A.cut_keep == "neg" else -1500
        cutbox.location = loc
        cutbox.hide_render = cutbox.hide_viewport = True
        for n in A.cut_names.split(","):
            o = bpy.data.objects.get(n)
            if o:
                md = o.modifiers.new("cut", "BOOLEAN"); md.object = cutbox; md.operation = "DIFFERENCE"
                md.solver = "EXACT"
    dv = Vector(d).normalized()
    cam.location = ctr + dv * size * 3.2
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    cam_d.type = "ORTHO" if ortho else "PERSP"
    cam_d.ortho_scale = size * 1.18
    cam_d.lens = 85
    bpy.context.view_layer.update()
    sc.render.filepath = f"{A.out}_{v}.png"
    bpy.ops.render.render(write_still=True)
    info[v] = {"matrix_world": [list(r) for r in cam.matrix_world], "ortho": ortho, "ortho_scale": cam_d.ortho_scale,
               "lens": cam_d.lens, "res": A.res}
json.dump(info, open(f"{A.out}_views.json", "w"), indent=1)
print("PREVIEW DONE", A.out)
