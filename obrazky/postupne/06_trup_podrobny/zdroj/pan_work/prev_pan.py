"""quick Blender preview of the PAN module:  /opt/venv/bl/bin/python prev_pan.py [views...]  (600 px, 16 samples)
context parts (finished neck / collar disc, T_paluba, T_stred ...) are loaded from stl/ and B/stl when a view asks for them"""
import bpy, sys, os, json, math
from mathutils import Vector
T4 = "/tmp/claude-0/gapwf/fin/T4"; BS = "/tmp/claude-0/gapwf/fin/B/stl"
argv = [a for a in sys.argv[1:] if not a.startswith("-")]
VIEWS = argv or ["iso", "rez_x"]
RES, SPP = 600, 16
doc = json.load(open(os.path.join(T4, "parts_pan.json")))
COL = {"P_sachta": (0.16, 0.17, 0.20), "P_koleso": (0.75, 0.45, 0.15), "P_drziak_serva": (0.25, 0.42, 0.62), "P_kluka": (0.80, 0.20, 0.20),
       "L_pata": (0.20, 0.60, 0.35), "L_jazyk": (0.55, 0.75, 0.25), "L_ucho": (0.90, 0.85, 0.75), "servo_zdvih": (0.12, 0.20, 0.45),
       "fpc_pan": (0.95, 0.55, 0.05), "spoj_zdvih": (0.05, 0.45, 0.2), "kabel_zdvih": (0.7, 0.1, 0.5),
       "golier_kotuc": (0.85, 0.85, 0.83), "krk_predna_polovica": (0.80, 0.80, 0.78), "krk_zadna_polovica": (0.70, 0.72, 0.75),
       "T_paluba": (0.15, 0.55, 0.50), "T_ram": (0.35, 0.45, 0.55), "T_stred": (0.92, 0.92, 0.90), "T_spodok": (0.07, 0.07, 0.08),
       "T_prichytka_fpc": (0.9, 0.75, 0.1), "servo_pan": (0.12, 0.12, 0.30), "pastorok_pan": (0.80, 0.60, 0.20), "cap_pan": (0.72, 0.72, 0.74),
       "T_dvere": (0.9, 0.9, 0.88), "golier_prstenec": (0.6, 0.6, 0.6), "servo_J1": (0.10, 0.10, 0.14), "T_bok_L": (0.9, 0.9, 0.9), "T_bok_P": (0.9, 0.9, 0.9)}
MAT = {"brass": (0.80, 0.60, 0.20), "steel": (0.72, 0.72, 0.74), "ptfe": (0.97, 0.97, 0.97), "petg": (0.3, 0.45, 0.6), "bought": (0.4, 0.4, 0.4),
       "resin_black": (0.07, 0.07, 0.08), "fpc": (0.95, 0.55, 0.05), "pom": (0.9, 0.85, 0.75)}
LGRP = {p["name"]: p["group"] for p in doc["parts"]}

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

def load(skip=(), ctx=(), stl_dir=None, lift=0.0, extra=()):
    objs = {}; mats = {}
    items = [(p["name"], p["mat"], os.path.join(stl_dir or os.path.join(T4, "stl"), p["name"] + ".stl")) for p in doc["parts"] if p["name"] not in skip]
    for n in ctx:
        f = os.path.join(BS, n + ".stl") if os.path.exists(os.path.join(BS, n + ".stl")) and not n.startswith("T_") else os.path.join(T4, "stl", n + ".stl")
        items.append((n, "ctx", f))
    for n, f in extra:
        items.append((n, "fpc", f))
    for n, mat, f in items:
        if not os.path.exists(f):
            print("missing", f); continue
        bpy.ops.wm.stl_import(filepath=f)
        o = bpy.context.selected_objects[0]; o.name = n
        key = n if n in COL else mat
        if key not in mats:
            mats[key] = material(key, COL.get(n, MAT.get(mat, (0.5, 0.5, 0.5))))
        o.data.materials.append(mats[key])
        if lift and n.startswith("krk_"):
            o.location.z += lift
        objs[n] = o
    return objs

def cut(objs, axis, offset, keep):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    c = bpy.context.active_object; c.scale = (400, 400, 400)
    i = "xyz".index(axis); loc = [0, 0, -50]
    loc[i] = offset + (200 if keep == "neg" else -200)
    c.location = loc; c.display_type = "WIRE"; c.hide_render = True
    for o in objs.values():
        m = o.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier="cut")
        except Exception as e:
            print("cut failed", o.name, e)

def camera(sc, direction, target=(0, 0, -25), scale=90.0):
    cam = bpy.data.cameras.new("cam"); ob = bpy.data.objects.new("cam", cam); sc.collection.objects.link(ob); sc.camera = ob
    cam.type = "ORTHO"; cam.ortho_scale = scale; cam.clip_start = 1.0; cam.clip_end = 5000.0
    d = Vector(direction).normalized(); t = Vector(target)
    ob.location = t + d * 800.0
    ob.rotation_euler = (t - ob.location).to_track_quat("-Z", "Y").to_euler()
    for k, (dv, e) in enumerate((((0.3, -0.5, 1.0), 3.0), ((-0.8, 0.3, 0.4), 1.2), ((0.6, 0.8, -0.3), 0.8))):
        L = bpy.data.lights.new(f"s{k}", "SUN"); L.energy = e; L.angle = 0.5
        lo = bpy.data.objects.new(f"s{k}", L); sc.collection.objects.link(lo)
        q = ob.rotation_euler.to_quaternion()
        v = d * 1.0 + q @ Vector((dv[0] * 0.8, dv[2] * 0.8, 0.0))
        lo.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()

NECK = ("golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica")
SPEC = {  # view: (direction to the camera, cut or None, target, scale, skip, context, stl dir override)
    "iso": ((-0.9, 1.0, 0.7), None, (0, 4, -24), 88.0, (), NECK, None),                       # from the back-right: lift module
    "iso_pred": ((0.9, -1.0, 0.7), None, (0, 4, -24), 88.0, (), NECK, None),                  # from the front-left: FPC lift loop
    "bez_krku": ((-0.6, 1.0, 1.0), None, (0, 4, -24), 88.0, (), (), None),
    "rez_x": ((1.0, 0.0, 0.0), ("x", 0.0, "neg"), (0, 4, -24), 80.0, (), NECK, None),          # section x = 0 seen from +X
    "rez_kluka": ((-1.0, 0.0, 0.0), ("x", -15.8, "pos"), (0, 8, -26), 70.0, (), NECK, None),   # section through the crank arm, seen from -X
    "rez_y": ((0.0, -1.0, 0.0), ("y", 0.0, "pos"), (0, 0, -24), 80.0, (), NECK, None),         # section y = 0 seen from the front
    "zdola": ((0.3, -0.4, -1.0), None, (0, 4, -40), 80.0, (), (), None),
    "zhora": ((0.0, -0.001, 1.0), None, (0, 4, -20), 80.0, (), (), None),
    "zozadu": ((0.0, 1.0, 0.0), None, (0, 0, -24), 80.0, (), NECK, None),
    "bok_fpc": ((1.0, 0.0, 0.0), None, (0, 4, -27), 70.0, (), NECK, None),
    "v_trupe": ((1.0, 0.0, 0.0), ("x", 0.0, "neg"), (0, 0, -40), 130.0, (), NECK + ("T_stred", "T_spodok", "T_ram", "T_paluba", "T_dvere", "servo_pan", "pastorok_pan", "cap_pan", "golier_prstenec", "servo_J1", "T_prichytka_fpc"), None),
    "v_trupe_y": ((0.0, -1.0, 0.0), ("y", 2.0, "pos"), (0, 0, -40), 130.0, (), NECK + ("T_stred", "T_spodok", "T_ram", "T_paluba", "T_bok_L", "T_bok_P", "cap_pan", "golier_prstenec", "servo_J1", "T_prichytka_fpc"), None),
    "det_fpc": ((0.0, -0.001, 1.0), ("z", -42.5, "neg"), (0, 6, -45), 62.0, ("P_sachta",), ("T_paluba", "T_prichytka_fpc", "pastorok_pan", "cap_pan"), None),
}
PO = os.path.join(T4, "pan_work", "poses")
SPEC["zdvih20"] = ((-0.9, 1.0, 0.7), None, (0, 4, -18), 96.0, (), NECK, os.path.join(PO, "lift20"))
SPEC["rez_kluka_10"] = ((-1.0, 0.0, 0.0), ("x", -14.4, "pos"), (0, 8, -26), 70.0, (), NECK, os.path.join(PO, "lift10"))
SPEC["rez_kluka_20"] = ((-1.0, 0.0, 0.0), ("x", -14.4, "pos"), (0, 8, -22), 78.0, (), NECK, os.path.join(PO, "lift20"))
SPEC["rez_kluka"] = ((-1.0, 0.0, 0.0), ("x", -14.4, "pos"), (0, 8, -26), 70.0, (), NECK, None)
SPEC["det_fpc_pozy"] = ((0.0, -0.001, 1.0), ("z", -42.5, "neg"), (0, 6, -45), 62.0, ("P_sachta", "fpc_pan"), ("T_paluba", "T_prichytka_fpc", "pastorok_pan", "cap_pan"), None)
LIFT = {"zdvih20": 20.0, "rez_kluka_10": 10.0, "rez_kluka_20": 20.0}
EXTRA = {"det_fpc_pozy": [(f"fpc_pan_{a}", os.path.join(PO, "fpc", f"fpc_pan_{a}.stl")) for a in (-85, 0, 85)]}
for v in VIEWS:
    d, c, tgt, scale, skip, ctx, sd = SPEC[v]
    sc = setup(); objs = load(skip, ctx, sd, LIFT.get(v, 0.0), EXTRA.get(v, ()))
    if c:
        cut(objs, *c)
    camera(sc, d, tgt, scale)
    sc.render.filepath = os.path.join(T4, f"prev_pan_{v}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", v, flush=True)
