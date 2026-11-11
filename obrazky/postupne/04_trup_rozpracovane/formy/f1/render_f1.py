"""Blender (bpy 5.2, Cycles CPU) renders of the f1 exterior with the REAL neck/head (variant B rev. E2).
Usage: /opt/venv/bl/bin/python render_f1.py --pose <pose.json from pose.py> --out <prefix> --views hero,front,side,back34
       [--res 1100] [--samples 36] [--exposure -0.9] [--only torso,base,arms]
Materials: white satin shells, black joints / plinth / foot, glowing cyan light guides, glossy black display bezel."""
import bpy, sys, os, json, math, argparse
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("--pose", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--views", default="hero")
ap.add_argument("--res", type=int, default=1100)
ap.add_argument("--samples", type=int, default=36)
ap.add_argument("--exposure", type=float, default=-0.9)
ap.add_argument("--no-head", action="store_true")
ap.add_argument("--aspect", type=float, default=0.82)
A = ap.parse_args(argv)
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(A.pose))
PARTS = json.load(open(os.path.join(HERE, "parts.json")))

B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
B_GROUP = {"H": ["hlava_skrupina", "ram_displeja", "displej", "oci_len_vizualizacia", "usi", "led_kruzky",
                 "usko_kryt", "usko_lozisko"],
           "L": ["krk_predna_polovica", "krk_zadna_polovica"],
           "P": ["golier_kotuc"], "T": ["golier_prstenec"]}
B_COLOR = {"hlava_skrupina": "white", "ram_displeja": "gloss_black", "displej": "glass", "usi": "black",
           "led_kruzky": "glow", "oci_len_vizualizacia": "eyes", "usko_kryt": "black", "usko_lozisko": "black",
           "krk_predna_polovica": "black", "krk_zadna_polovica": "black", "golier_kotuc": "black",
           "golier_prstenec": "black"}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = A.samples
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.cycles.max_bounces = 6
sc.render.resolution_x = int(A.res * A.aspect)
sc.render.resolution_y = A.res
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Base Contrast"
except Exception:
    pass
sc.view_settings.exposure = A.exposure
sc.render.film_transparent = True             # floor = shadow catcher; composited on a studio gradient (compose)
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.80, 0.80, 0.79, 1)
bg.inputs[1].default_value = 0.45

MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    spec = {  # base colour, roughness, metallic, coat
        "white": ((0.86, 0.86, 0.84), 0.38, 0.0, 0.15),
        "black": ((0.025, 0.025, 0.028), 0.42, 0.0, 0.0),
        "rubber": ((0.02, 0.02, 0.02), 0.8, 0.0, 0.0),
        "gloss_black": ((0.012, 0.012, 0.014), 0.10, 0.0, 0.6),
        "glass": ((0.006, 0.006, 0.008), 0.05, 0.0, 0.8),
        "grey": ((0.30, 0.31, 0.32), 0.55, 0.0, 0.0),
        "metal": ((0.7, 0.7, 0.72), 0.3, 1.0, 0.0),
        "glow": ((0.25, 0.85, 0.95), 0.3, 0.0, 0.0),
        "eyes": ((1.0, 0.86, 0.62), 0.3, 0.0, 0.0),
    }.get(key, ((0.5, 0.5, 0.5), 0.5, 0.0, 0.0))
    b.inputs["Base Color"].default_value = (*spec[0], 1)
    b.inputs["Roughness"].default_value = spec[1]
    b.inputs["Metallic"].default_value = spec[2]
    try:
        b.inputs["Coat Weight"].default_value = spec[3]
        b.inputs["Coat Roughness"].default_value = 0.25
    except Exception:
        pass
    if key in ("glow", "eyes"):
        b.inputs["Emission Color"].default_value = (*spec[0], 1)
        b.inputs["Emission Strength"].default_value = 6.0 if key == "glow" else 4.0
    MATS[key] = m
    return m


def imp(fn, name, key, M=None, smooth_angle=35):
    bpy.ops.wm.stl_import(filepath=fn)
    o = bpy.context.selected_objects[0]
    o.name = name
    if M is not None:
        o.matrix_world = M
    o.data.materials.clear()
    o.data.materials.append(mat(key))
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(smooth_angle))
    except Exception:
        bpy.ops.object.shade_smooth()
    return o


objs = []
LOC = {g: Matrix(m) for g, m in P["loc"].items()}
for nm, d in PARTS.items():
    objs.append(imp(d["stl"], nm, d["color"], LOC[d["group"]], smooth_angle=30))
for d in P["pack_parts"]:
    objs.append(imp(d["stl"], d["name"], d["color"], LOC[d["group"]]))
if not A.no_head:
    dz = Matrix.Translation((0, 0, P["dz_B"]))
    for g, names in B_GROUP.items():
        for n in names:
            fn = os.path.join(B_STL, n + ".stl")
            if os.path.exists(fn):
                objs.append(imp(fn, "B_" + n, B_COLOR.get(n, "grey"), LOC[g] @ dz))

lo = Vector((1e9, 1e9, 1e9)); hi = -lo
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
ctr = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (hi.z + 0) / 2))
size = max(hi.x - lo.x, hi.y - lo.y, hi.z)

# floor (same tone as the background, catches the contact shadow)
bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
fl = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.74, 0.74, 0.73, 1); fb.inputs["Roughness"].default_value = 0.6
fl.data.materials.append(fm)
fl.is_shadow_catcher = True

cam_d = bpy.data.cameras.new("cam"); cam_d.clip_start = 1; cam_d.clip_end = 1e5
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
LIGHTS = []


def add_area(loc, energy, size, target):
    ld = bpy.data.lights.new("a%d" % len(LIGHTS), "AREA"); ld.energy = energy; ld.size = size
    lo_ = bpy.data.objects.new(ld.name, ld); sc.collection.objects.link(lo_)
    lo_.location = loc
    lo_.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    LIGHTS.append(lo_)


def rig(view_dir):
    """camera-relative 3-light rig (key upper-left of the camera, fill right, rim behind)"""
    for o in LIGHTS:
        bpy.data.objects.remove(o)
    LIGHTS.clear()
    d = Vector(view_dir).normalized()
    up = Vector((0, 0, 1))
    right = d.cross(up).normalized()          # camera right (d points from target to camera)
    right = -right
    t = ctr
    add_area(t + (d * 1.0 - right * 0.9 + up * 1.1).normalized() * 700, 1.6e6, 450, t)    # key
    add_area(t + (d * 1.0 + right * 1.2 + up * 0.2).normalized() * 700, 0.55e6, 600, t)   # fill
    add_area(t + (-d * 1.0 + right * 0.4 + up * 1.2).normalized() * 700, 0.9e6, 400, t)   # rim / back light
    add_area(t + Vector((0, 0, 1)) * 800, 0.35e6, 900, t)                                 # top soft


VIEWS = {  # direction from the target to the camera, ortho?, lens, framing
    "hero": ((0.62, -1.0, 0.20), False, 80),
    "front": ((0, -1, 0), True, 0),
    "side": ((1, 0, 0), True, 0),
    "back34": ((-0.75, 1.0, 0.32), False, 80),
    "persona": ((1.0, -0.62, 0.16), False, 80),
    "top": ((0.0, -0.25, 1.0), False, 80),
    "low": ((0.7, -1.0, -0.02), False, 80),
}
def compose(src, dst):
    """straight-alpha composite over a soft studio gradient (R01-like light warm grey) - done with Pillow (cad venv)"""
    import subprocess
    code = ("import numpy as np; from PIL import Image; im = np.asarray(Image.open(%r).convert('RGBA')).astype(float) / 255;"
            "h, w = im.shape[:2]; y = np.linspace(0, 1, h)[:, None, None];"
            "bg = np.array([0.86, 0.86, 0.85]) * (1 - y) + np.array([0.74, 0.74, 0.73]) * y;"
            "a = im[..., 3:4]; out = im[..., :3] * a + bg * (1 - a);"
            "Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('uint8')).save(%r)") % (src, dst)
    subprocess.run(["/opt/venv/cad/bin/python", "-c", code], check=True)


sc.render.image_settings.color_mode = "RGBA"
info = {}
for v in A.views.split(","):
    d, ortho, lens = VIEWS[v]
    dv = Vector(d).normalized()
    rig(dv)
    tgt = Vector((ctr.x, ctr.y, hi.z * 0.5))
    if ortho:
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = max(hi.z, (hi.x - lo.x) / A.aspect) * 1.12
        cam.location = tgt + dv * 1200
    else:
        cam_d.type = "PERSP"
        cam_d.lens = lens
        cam_d.sensor_fit = "VERTICAL"
        cam_d.sensor_height = 24
        fov = 2 * math.atan(12 / lens)
        dist = (hi.z * 0.62) / math.tan(fov / 2) + 60
        cam.location = tgt + dv * dist
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    sc.render.filepath = f"{A.out}_{v}_rgba.png"
    bpy.ops.render.render(write_still=True)
    compose(f"{A.out}_{v}_rgba.png", f"{A.out}_{v}.png")
    info[v] = {"matrix_world": [list(r) for r in cam.matrix_world], "ortho": ortho}
json.dump(info, open(f"{A.out}_views.json", "w"), indent=1)
print("RENDER DONE", A.out)
