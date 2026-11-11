"""f2 Kapsula - Blender (Cycles CPU) renders with the REAL variant-B head/neck.
Usage: /opt/venv/bl/bin/python render_f2.py --out <prefix> --views hero,front,side,back34,persona [--res 1100]
       [--samples 36] [--pose '{"lift":12.5,"tilt":8,"armR":15,"armL":15}'] [--internals] [--exposure -0.7]
Poses follow t1lib: T = Rz(j1); P = T.Rz(pan); L = P.Tz(lift); H = L.(tilt about X at the hinge axis z 125.5 + 0);
AR/AL = T.(rotation -arm about the shoulder X axis at y 2, z 112).  B head STLs are in the B frame: z_world = z_B + 129."""
import bpy, sys, os, json, math, argparse
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--views", default="hero")
ap.add_argument("--res", type=int, default=1100)
ap.add_argument("--samples", type=int, default=36)
ap.add_argument("--pose", default="")
ap.add_argument("--exposure", type=float, default=-0.55)
ap.add_argument("--parts", default="/tmp/claude-0/gapwf/fin/T1/forma/f2/parts.json")
ap.add_argument("--hide", default="")
A = ap.parse_args(argv)

Z_TT = 133.0
DZ = Z_TT - 4.0
AXZ = -3.5 + DZ
SHY, SHZ = 2.0, 112.0
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
B_GROUP = {"H": ["hlava_skrupina", "ram_displeja", "displej", "drziak_displeja", "oci_len_vizualizacia", "usi",
                 "led_kruzky", "usko_kryt", "usko_lozisko", "klzny_kruzok", "paka"],
           "L": ["krk_predna_polovica", "krk_zadna_polovica"],
           "P": ["golier_kotuc"], "T": ["golier_prstenec"]}
B_COLOR = {"hlava_skrupina": "white", "ram_displeja": "black_gloss", "displej": "glass", "usi": "black",
           "led_kruzky": "glow", "oci_len_vizualizacia": "eyes", "usko_kryt": "black", "usko_lozisko": "black",
           "krk_predna_polovica": "black", "krk_zadna_polovica": "black", "golier_kotuc": "black",
           "golier_prstenec": "black", "drziak_displeja": "black", "klzny_kruzok": "black", "paka": "black"}

POSES = {
    "awake": {"lift": 12.5, "tilt": 8, "pan": 0, "armR": 14, "armL": 14},
    "rest": {},
    "persona": {"j1": 20, "pan": 30, "lift": 15, "tilt": -12, "armR": 128, "armL": 12},
}


def gm(group, p):
    Rz = lambda d: Matrix.Rotation(math.radians(d), 4, "Z")
    Rx = lambda d: Matrix.Rotation(math.radians(d), 4, "X")
    Tt = lambda x, y, z: Matrix.Translation((x, y, z))
    j1 = Rz(p.get("j1", 0.0))
    if group == "B":
        return Matrix.Identity(4)
    if group == "T":
        return j1
    if group == "P":
        return j1 @ Rz(p.get("pan", 0.0))
    if group == "L":
        return j1 @ Rz(p.get("pan", 0.0)) @ Tt(0, 0, p.get("lift", 0.0))
    if group == "H":
        return j1 @ Rz(p.get("pan", 0.0)) @ Tt(0, 0, p.get("lift", 0.0)) @ Tt(0, 0, AXZ) @ Rx(p.get("tilt", 0.0)) \
            @ Tt(0, 0, -AXZ)
    if group in ("AR", "AL"):
        th = p.get("armR" if group == "AR" else "armL", 0.0)
        return j1 @ Tt(0, SHY, SHZ) @ Rx(-th) @ Tt(0, -SHY, -SHZ)
    raise ValueError(group)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = A.samples
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.render.resolution_x = A.res
sc.render.resolution_y = A.res
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.view_settings.exposure = A.exposure
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.80, 0.80, 0.79, 1)
bg.inputs[1].default_value = 0.35

MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    spec = {
        "white": ((0.80, 0.80, 0.78), 0.34, 0.0),
        "black": ((0.018, 0.018, 0.02), 0.42, 0.0),
        "black_gloss": ((0.010, 0.010, 0.012), 0.07, 0.0),
        "grey": ((0.30, 0.31, 0.32), 0.5, 0.0),
        "glass": ((0.005, 0.005, 0.007), 0.05, 0.0),
        "glow": ((0.25, 0.85, 0.95), 0.3, 0.0),
        "eyes": ((1.0, 0.86, 0.62), 0.3, 0.0),
        "floor": ((0.70, 0.70, 0.69), 0.6, 0.0),
    }.get(key, ((0.5, 0.5, 0.5), 0.5, 0.0))
    b.inputs["Base Color"].default_value = (*spec[0], 1)
    b.inputs["Roughness"].default_value = spec[1]
    if key == "white":
        try:
            b.inputs["Coat Weight"].default_value = 0.15
            b.inputs["Coat Roughness"].default_value = 0.25
            b.inputs["Subsurface Weight"].default_value = 0.04
        except Exception:
            pass
    if key in ("black_gloss", "glass"):
        try:
            b.inputs["Coat Weight"].default_value = 0.6
            b.inputs["Coat Roughness"].default_value = 0.03
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
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(smooth_angle))
    except Exception:
        bpy.ops.object.shade_smooth()
    return o


pose = POSES["awake"]
if A.pose:
    pose = POSES[A.pose] if A.pose in POSES else json.loads(A.pose)
meta = json.load(open(A.parts))
hide = set(A.hide.split(",")) if A.hide else set()
objs = []
for p in meta["parts"]:
    if p["name"] in hide:
        continue
    objs.append(imp(p["stl"], p["name"], p["color"], gm(p["group"], pose)))
dz = Matrix.Translation((0, 0, DZ))
for g, names in B_GROUP.items():
    Mg = gm(g, pose) @ dz
    for n in names:
        fn = os.path.join(B_STL, n + ".stl")
        if os.path.exists(fn):
            objs.append(imp(fn, "B_" + n, B_COLOR.get(n, "black"), Mg))

# ---------------------------------------------------------------- studio
lo = Vector((1e9, 1e9, 1e9)); hi = -lo
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
ctr = (lo + hi) / 2
size = max(hi - lo)


def area(loc, energy, sz, tgt=None, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.active_object
    L.data.energy = energy
    L.data.size = sz
    L.data.color = color
    t = Vector(tgt) if tgt is not None else ctr
    L.rotation_euler = (t - L.location).to_track_quat("-Z", "Y").to_euler()
    return L


bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat("floor"))
# a soft curved backdrop is replaced by the world colour; shadows on the floor ground the robot
cam_d = bpy.data.cameras.new("cam")
cam_d.clip_start = 5
cam_d.clip_end = 1e5
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

VIEWS = {  # direction from target to camera, ortho?, lens, target z offset, frame scale
    "hero": ((0.62, -1.0, 0.26), False, 105, 0.0, 1.03),
    "front": ((0.0, -1.0, 0.0), True, 0, 0.0, 1.06),
    "side": ((1.0, 0.0, 0.0), True, 0, 0.0, 1.06),
    "back34": ((-0.75, 1.0, 0.40), False, 105, 0.0, 1.04),
    "persona": ((0.55, -1.0, 0.22), False, 105, 0.0, 1.04),
    "top34": ((0.6, -0.8, 1.1), False, 105, 0.0, 1.08),
    "low": ((0.7, -1.0, 0.08), False, 105, 0.0, 1.08),
}
info = {}
lights = []
for v in A.views.split(","):
    for L in lights:
        bpy.data.objects.remove(L, do_unlink=True)
    d, ortho, lens, tz, fs = VIEWS[v]
    dv = Vector(d).normalized()
    # camera-relative lights: key upper-left of the camera, fill right, rim behind
    up = Vector((0, 0, 1))
    right = dv.cross(up).normalized() * -1
    if right.length == 0:
        right = Vector((1, 0, 0))
    tgt = Vector((0, 0, (lo.z + hi.z) / 2 + tz))
    base = tgt + dv * 700
    lights = [area(tgt + dv * 520 - right * 420 + up * 520, 3.4e6, 520),
              area(tgt + dv * 560 + right * 520 + up * 120, 1.1e6, 700),
              area(tgt - dv * 500 + up * 420 + right * 150, 1.6e6, 420),
              area(tgt + up * 900, 0.9e6, 900)]
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (max(lo.z, 0.0), hi.z)]
    fwd = -dv
    rgt = fwd.cross(up).normalized()
    upc = rgt.cross(fwd).normalized()
    tgt = ctr.copy()
    xs = [(c - tgt).dot(rgt) for c in corners]
    ys = [(c - tgt).dot(upc) for c in corners]
    tgt = tgt + rgt * (max(xs) + min(xs)) / 2 + upc * (max(ys) + min(ys)) / 2
    xs = [(c - tgt).dot(rgt) for c in corners]
    ys = [(c - tgt).dot(upc) for c in corners]
    ds = [(c - tgt).dot(dv) for c in corners]
    if ortho:
        cam.location = tgt + dv * 2000
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = 2 * max(max(map(abs, xs)), max(map(abs, ys))) * fs
    else:
        cam_d.type = "PERSP"
        cam_d.lens = lens
        th = 18.0 / lens
        dist = max(d + max(abs(x), abs(y)) * fs / th for x, y, d in zip(xs, ys, ds))
        cam.location = tgt + dv * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    sc.render.filepath = f"{A.out}_{v}.png"
    bpy.ops.render.render(write_still=True)
    info[v] = {"matrix_world": [list(r) for r in cam.matrix_world], "ortho": ortho,
               "ortho_scale": cam_d.ortho_scale, "lens": cam_d.lens, "res": A.res, "pose": pose}
    print("RENDERED", v, flush=True)
json.dump(info, open(f"{A.out}_views.json", "w"), indent=1)
print("DONE", A.out)
