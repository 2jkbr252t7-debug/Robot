"""Blender (Cycles CPU) renders of P_sachta for the strength review: bottom view, section x = 0 (assembly), section through
the slim corner (horizontal z -30 + radial plane through the corner arc centre (21, 8.5)).  Writes <shot>.png (raw, no text)
and <shot>_anchors.json (pixel positions of label points).  Usage: blender-python bl_render.py -- --shot zdola --res 1200"""
import bpy, bmesh, sys, os, json, math, argparse, time
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
T4 = "/tmp/claude-0/gapwf/fin/T4"; OUT = os.path.join(T4, "sachta_a", "img")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser(); ap.add_argument("--shot", default="zdola"); ap.add_argument("--res", type=int, default=1200)
ap.add_argument("--samples", type=int, default=32); ap.add_argument("--asp", type=float, default=1.0)
A = ap.parse_args(argv); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; vl = bpy.context.view_layer
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.3
sc.render.film_transparent = True; sc.render.threads_mode = "FIXED"; sc.render.threads = 2
W = bpy.data.worlds.new("w"); sc.world = W; W.use_nodes = True
W.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.62, 1); W.node_tree.nodes["Background"].inputs[1].default_value = 0.35
MATS = {}
COL = {"well": ((0.30, 0.31, 0.33), 0.45, 0.0), "brass": ((0.80, 0.58, 0.25), 0.3, 1.0), "alu": ((0.80, 0.81, 0.83), 0.35, 1.0),
       "steel": ((0.62, 0.63, 0.65), 0.3, 1.0), "ptfe": ((0.93, 0.93, 0.90), 0.55, 0.0), "resin": ((0.55, 0.40, 0.40), 0.5, 0.0),
       "resin2": ((0.62, 0.55, 0.70), 0.5, 0.0), "servo": ((0.05, 0.05, 0.06), 0.5, 0.0), "tcap": ((0.35, 0.62, 0.40), 0.5, 0.0),
       "cap_well": ((1.0, 0.50, 0.10), 0.6, 0.0), "cap_other": ((0.75, 0.75, 0.78), 0.6, 0.0)}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    c, r, met = COL[key]; b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = r; b.inputs["Metallic"].default_value = met
    MATS[key] = m; return m


OBJ = {}


def imp(name, key):
    p = os.path.join(T4, "stl", name + ".stl")
    bpy.ops.wm.stl_import(filepath=p); o = bpy.context.selected_objects[0]; o.name = name
    o.data.materials.clear(); o.data.materials.append(mat(key))
    for poly in o.data.polygons:
        poly.use_smooth = False
    OBJ[name] = o; return o


def cut(o, normal, off, capkey, keep="neg"):
    """boolean-cut o by the plane n.p = off; keeps n.p < off ('neg') or > off ('pos'); cap faces get capkey"""
    bpy.ops.mesh.primitive_cube_add(size=1); c = bpy.context.active_object; c.name = "_cut_" + o.name
    big = 400.0; c.scale = (big, big, big)
    n = Vector(normal).normalized()
    c.rotation_euler = n.to_track_quat("Z", "Y").to_euler()
    c.location = n * (off + (big / 2 if keep == "neg" else -big / 2))
    c.data.materials.append(mat(capkey)); c.hide_render = True; c.hide_viewport = True
    md = o.modifiers.new("rez", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = c; md.solver = "EXACT"
    try:
        md.material_mode = "TRANSFER"
    except Exception:
        pass
    vl.objects.active = o; bpy.ops.object.modifier_apply(modifier="rez")


LIGHTS = []
def rig(ctr, dv):
    for L in LIGHTS:
        bpy.data.objects.remove(L, do_unlink=True)
    LIGHTS.clear()
    dv = Vector(dv).normalized(); up = Vector((0, 0, 1)) if abs(dv.z) < 0.95 else Vector((0, 1, 0))
    right = dv.cross(up).normalized(); up2 = right.cross(dv).normalized()
    for (a, b, c), e, s in (((-0.55, 0.62, 0.75), 3.0e6, 500), ((0.85, 0.25, 0.5), 1.4e6, 600), ((0.1, 1.0, 0.25), 1.4e6, 600), ((0.3, -0.6, 0.6), 0.9e6, 600)):
        p = Vector(ctr) + (right * a + up2 * b + dv * c).normalized() * 800
        bpy.ops.object.light_add(type="AREA", location=p); L = bpy.context.active_object
        L.data.energy, L.data.size = e, s; L.rotation_euler = (Vector(ctr) - p).to_track_quat("-Z", "Y").to_euler(); LIGHTS.append(L)


cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.clip_start = 1; cam_d.clip_end = 5000
CAM = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM


def camera(ctr, dv, up, scale, res):
    sc.render.resolution_x, sc.render.resolution_y = res
    dv = Vector(dv).normalized(); CAM.location = Vector(ctr) + dv * 1000
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    # roll so that 'up' is image up
    q = (-dv).to_track_quat("-Z", "Y")
    CAM.rotation_euler = q.to_euler()
    cur_up = q @ Vector((0, 1, 0)); want = Vector(up) - dv * Vector(up).dot(dv); want.normalize()
    ang = cur_up.angle(want); s = 1 if dv.dot(cur_up.cross(want)) < 0 else -1
    CAM.rotation_euler.rotate_axis("Z", s * ang)
    cam_d.ortho_scale = scale; vl.update()
    rig(ctr, dv)


def px(p):
    c = world_to_camera_view(sc, CAM, Vector(p)); return [round(c.x * sc.render.resolution_x, 1), round((1 - c.y) * sc.render.resolution_y, 1)]


def render(name, anchors):
    json.dump(dict(anchors={k: px(v) for k, v in anchors.items()}, res=[sc.render.resolution_x, sc.render.resolution_y],
                   mm_per_px=cam_d.ortho_scale / max(sc.render.resolution_x, sc.render.resolution_y)),
              open(os.path.join(OUT, name + "_anchors.json"), "w"), indent=1)
    sc.render.filepath = os.path.join(OUT, name + ".png"); t = time.time()
    bpy.ops.render.render(write_still=True); print("SHOT", name, round(time.time() - t), "s", flush=True)


R = A.res
if A.shot == "zdola":
    imp("P_sachta", "well")
    camera((0, 0, -40), (0, 0, -1), (0, 1, 0), 60.0, (R, R))
    an = {"hub": (0, -9.5, -41.9), "hub_in": (0, -6.5, -41.9), "floor": (12, 9, -41.9), "groove": (20.0, 5.2, -41.6), "shroud": (-3.0, 16.0, -45.6),
          "lip": (-8.6, 14.9, -42.5), "front": (-15, -11.8, -40.9), "endm": (-24.3, -3.0, -40.9), "corner_fl": (-23.99, -9.57, -40.9),
          "corner_fr": (23.95, -9.67, -40.9), "corner_bl": (-23.99, 9.55, -40.9), "corner_br": (23.95, 9.65, -41.9), "lens": (0, -11.8, -41.9), "endp": (24.3, -2.0, -40.9),
          "backwall": (4.0, 12.0, -41.9), "rail": (5.0, 14.0, -41.9), "pillar": (24.3, 6.0, -41.9), "winback": (-13.7, 11.8, -40.65),
          "axis": (0, 0, -41.9), "ring_band": (0, -26.3, -10.0)}
    render("zdola", an)
elif A.shot == "rez_x0":
    for n, k in (("P_sachta", "well"), ("koleso_pan", "brass"), ("T_cap", "tcap"), ("ptfe_cap", "ptfe"), ("pd_F15", "steel"), ("skr_F15", "steel"),
                 ("T_most", "alu"), ("ptfe_podlozka", "ptfe"), ("T_paluba", "resin2"), ("P_drziak_serva", "resin"), ("L_pata", "alu"), ("servo_J1", "servo"),
                 ("ptfe_pas_capu", "ptfe")):
        o = imp(n, k); cut(o, (1, 0, 0), 0.0, "cap_well" if n == "P_sachta" else "cap_other", keep="neg")
    camera((0, 2.5, -26.0), (1, 0, 0), (0, 0, 1), 62.0, (R, int(R * A.asp)))
    an = {"hub_f": (0, -9.6, -40.65), "hub_b": (0, 8.0, -40.65), "front_wall": (0, -11.8, -30), "front_root": (0, -10.7, -40.4), "back_wall": (0, 12.0, -30),
          "back_root": (0, 10.7, -40.4), "rail": (0, 14.0, -38.0), "groove": (0, 14.5, -37.9), "shroud": (0, 16.1, -44.0), "lip": (0, 17.1, -42.2),
          "gear": (0, -12.0, -44.0), "bond": (0, -9.0, -41.9), "tcap": (0, -3.2, -44.5), "washer": (0, -4.2, -41.4), "screw_thread": (0, 1.0, -46.6),
          "most": (0, 6.0, -47.2), "ptfe": (0, 8.0, -46.05), "foot": (0, -7.7, -38.5), "gap": (0, 7.6, -40.58), "top_plate": (0, -15.0, -2.75),
          "ring": (0, -25.4, -6.0), "journal": (0, -26.4, -6.5), "pocket": (0, 16.1, -25.0), "servo": (0, -5, -49.0), "paluba": (0, 22.0, -47.0),
          "front_edge": (0, -11.8, -40.9)}
    render("rez_x0", an)
elif A.shot == "rez_z30":
    o = imp("P_sachta", "well"); cut(o, (0, 0, 1), -30.0, "cap_well", keep="neg")
    g = imp("koleso_pan", "brass")
    camera((0, 0, -35), (0, 0, 1), (0, 1, 0), 60.0, (R, R))
    an = {"c_br": (23.9, 9.6, -30), "c_bl": (-23.9, 9.6, -30), "c_fl": (-23.9, -9.6, -30), "c_fr": (23.9, -9.6, -30), "front": (0, -11.8, -30),
          "back": (2.0, 12.0, -30), "endm": (-24.3, 0, -30), "endp_pillar": (24.3, 6.0, -30), "win_end": (24.3, -2.0, -30), "win_back": (-13.7, 11.8, -30),
          "land_f": (15.0, -10.65, -30), "land_e": (-23.15, 6.6, -30), "padB": (18.0, 14.5, -30), "rail": (5, 14, -34), "hub": (0, -9.5, -40.65), "floor": (10, 6, -40.65)}
    render("rez_z30", an)
elif A.shot == "rez_roh":
    az = math.degrees(math.atan2(8.5, 21.0)); a = math.radians(az)
    nrm = (-math.sin(a), math.cos(a), 0.0)
    for n, k in (("P_sachta", "well"), ("koleso_pan", "brass"), ("ptfe_pas_capu", "ptfe")):
        o = imp(n, k); cut(o, nrm, 0.0, "cap_well" if n == "P_sachta" else "cap_other", keep="neg")
    e = (math.cos(a), math.sin(a), 0.0)
    camera((e[0] * 13, e[1] * 13, -24.0), nrm, (0, 0, 1), 50.0, (R, int(R * A.asp)))
    P = lambda rr, z: (e[0] * rr, e[1] * rr, z)
    an = {"wall_mid": P(25.8, -25.0), "wall_band": P(25.8, -6.0), "junction": P(25.15, -40.65), "floor": P(20.0, -41.3), "hub": P(9.5, -41.3),
          "top": P(25.0, -2.75), "ring": P(25.4, -9.0), "shroud": P(16.1, -44.0), "gear": P(12.0, -44.0), "wall_low": P(25.8, -38.0), "edge": P(25.8, -41.9)}
    render("rez_roh", an)
