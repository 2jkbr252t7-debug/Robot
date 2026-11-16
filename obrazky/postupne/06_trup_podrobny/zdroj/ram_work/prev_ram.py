"""quick Blender preview of the RAM module (STL of parts_ram.json):  /opt/venv/bl/bin/python prev_ram.py [views...]
views: iso, iso_zad, zdola, rez_x (section x = cut_x, seen from +X), rez_y (section y = 0, seen from the front), ..."""
import bpy, sys, os, json, math
from mathutils import Vector
T4 = "/tmp/claude-0/gapwf/fin/T4"
argv = [a for a in sys.argv[1:] if not a.startswith("-")]
VIEWS = argv or ["iso", "iso_zad", "zdola", "rez_x", "rez_y"]
RES, SPP = 600, 16
doc = json.load(open(os.path.join(T4, "parts_ram.json")))
COL = {"T_spodok": (0.07, 0.07, 0.08), "T_ram": (0.25, 0.42, 0.62), "T_paluba": (0.15, 0.55, 0.50), "T_prichytka_fpc": (0.9, 0.75, 0.1),
       "Z_naboj_test": (0.45, 0.50, 0.42), "servo_J1": (0.10, 0.10, 0.14), "servo_pan": (0.12, 0.12, 0.30), "DPS_riadenie": (0.05, 0.40, 0.18),
       "menic": (0.10, 0.35, 0.55), "zosilnovac": (0.30, 0.15, 0.55), "kondenzator": (0.05, 0.05, 0.25), "lozisko_6805": (0.65, 0.66, 0.70),
       "pena_J1": (0.9, 0.5, 0.6), "pena_J1_celo": (0.9, 0.5, 0.6)}
MAT = {"brass": (0.80, 0.60, 0.20), "steel": (0.72, 0.72, 0.74), "ptfe": (0.95, 0.95, 0.95), "petg": (0.3, 0.45, 0.6), "bought": (0.4, 0.4, 0.4),
       "resin_black": (0.07, 0.07, 0.08)}

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.exposure = -0.9
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.95, 0.94, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    return sc

def material(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.55
    if name in ("brass", "steel"):
        b.inputs["Metallic"].default_value = 0.8; b.inputs["Roughness"].default_value = 0.35
    return m

def load(skip=()):
    objs = {}
    mats = {}
    for p in doc["parts"]:
        n = p["name"]
        if n in skip:
            continue
        bpy.ops.wm.stl_import(filepath=os.path.join(T4, "stl", n + ".stl"))
        o = bpy.context.selected_objects[0]; o.name = n
        key = n if n in COL else p["mat"]
        if key not in mats:
            mats[key] = material(key, COL.get(n, MAT.get(p["mat"], (0.5, 0.5, 0.5))))
        o.data.materials.append(mats[key])
        objs[n] = o
    return objs

def cut(objs, axis, offset, keep):
    """remove the half-space on the `keep`-opposite side of plane axis = offset"""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    c = bpy.context.active_object; c.scale = (400, 400, 400)
    i = "xyz".index(axis); loc = [0, 0, -50]
    loc[i] = offset + (200 if keep == "neg" else -200)
    c.location = loc; c.display_type = "WIRE"; c.hide_render = True
    red = material("cutface", (0.85, 0.25, 0.2))
    for o in objs.values():
        m = o.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier="cut")
        except Exception as e:
            print("cut failed", o.name, e)

def camera(sc, direction, target=(0, 0, -62), scale=135.0):
    cam = bpy.data.cameras.new("cam"); ob = bpy.data.objects.new("cam", cam); sc.collection.objects.link(ob); sc.camera = ob
    cam.type = "ORTHO"; cam.ortho_scale = scale; cam.clip_start = 1.0; cam.clip_end = 5000.0
    d = Vector(direction).normalized(); t = Vector(target)
    ob.location = t + d * 800.0
    ob.rotation_euler = (t - ob.location).to_track_quat("-Z", "Y").to_euler()
    for k, (dv, e) in enumerate((((0.3, -0.5, 1.0), 3.0), ((-0.8, 0.3, 0.4), 1.2), ((0.6, 0.8, -0.3), 0.8))):
        L = bpy.data.lights.new(f"s{k}", "SUN"); L.energy = e; L.angle = 0.5
        lo = bpy.data.objects.new(f"s{k}", L); sc.collection.objects.link(lo)
        # light direction relative to the camera frame
        q = ob.rotation_euler.to_quaternion()
        v = q @ Vector((dv[0], dv[2], -dv[1])) if False else (d * 1.0 + q @ Vector((dv[0] * 0.8, dv[2] * 0.8, 0.0)))
        lo.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()

SPEC = {  # view: (direction to the camera, cut (axis, offset, keep) or None, target, scale, skip)
    "iso": ((0.9, -1.0, 0.7), None, (0, 0, -58), 150.0, ()),
    "iso_zad": ((-0.9, 1.0, 0.7), None, (0, 0, -58), 150.0, ()),
    "zdola": ((0.5, -0.6, -1.0), None, (0, 0, -70), 150.0, ("Z_naboj_test", "Z_koleso_J1", "Z_skrutka_M8", "Z_pruzina_1", "Z_pruzina_2")),
    "rez_x": ((1.0, 0.0, 0.0), ("x", 0.0, "neg"), (0, 0, -60), 130.0, ()),
    "rez_x18": ((1.0, 0.0, 0.0), ("x", -18.0, "neg"), (0, 0, -60), 130.0, ()),
    "rez_y": ((0.0, -1.0, 0.0), ("y", 0.0, "pos"), (0, 0, -60), 130.0, ()),
    "rez_y21": ((0.0, -1.0, 0.0), ("y", -20.79, "pos"), (0, 0, -60), 130.0, ()),
    "zhora": ((0.0, -0.001, 1.0), None, (0, 0, -60), 120.0, ()),
    "det_J1": ((0.0, -1.0, 0.0), ("y", 0.0, "pos"), (-8, 0, -88), 62.0, ()),
    "det_J1_zdola": ((0.25, -0.35, -1.0), None, (-6, 0, -90), 80.0, ("Z_naboj_test", "Z_koleso_J1", "Z_skrutka_M8", "Z_pruzina_1", "Z_pruzina_2")),
    "det_pan": ((1.0, 0.0, 0.0), ("x", 14.0, "neg"), (0, -14, -62), 62.0, ()),
    "det_fpc": ((0.0, -0.001, 1.0), None, (0, 8, -45), 70.0, ()),
    "det_paluba": ((0.35, -0.6, 1.0), None, (0, 4, -46), 75.0, ("servo_pan", "pastorok_pan", "skr_pastorok_pan")),
    "bok_L": ((1.0, 0.0, 0.0), None, (0, 0, -58), 130.0, ()),
    "bok_P": ((-1.0, 0.0, 0.0), None, (0, 0, -58), 130.0, ()),
    "spredu": ((0.0, -1.0, 0.0), None, (0, 0, -58), 130.0, ()),
    "zozadu": ((0.0, 1.0, 0.0), None, (0, 0, -58), 130.0, ()),
}
for v in VIEWS:
    d, c, tgt, scale, skip = SPEC[v]
    sc = setup(); objs = load(skip)
    if c:
        cut(objs, *c)
    camera(sc, d, tgt, scale)
    sc.render.filepath = os.path.join(T4, f"prev_ram_{v}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", v, flush=True)
