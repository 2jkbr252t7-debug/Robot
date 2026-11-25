"""NOVA mini - arm proposal v1: concept renders (Cycles CPU).  Reads T4 / B / T3 (never writes there).
Usage: /opt/venv/bl/bin/python v1_scene.py -- --shot front_A|front_B|rez|rozlozena|rozsah|hero --res 1000 --samples 24 --out DIR
Writes DIR/<shot>[_part].png (transparent film) + DIR/<shot>_cam.json (camera + projected anchors)."""
import bpy, bmesh, sys, os, json, math, argparse, time
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v1geo as V
S = V.S
T4 = "/tmp/claude-0/gapwf/fin/T4"
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
ST = os.path.join(HERE, "stl")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", default="front_B")
ap.add_argument("--res", type=int, default=700)
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--out", default=os.path.join(HERE, "r"))
ap.add_argument("--exposure", type=float, default=-0.1)
ap.add_argument("--noren", action="store_true")
ap.add_argument("--parts", default="")            # rozsah: comma list of sub-renders
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)
T0 = time.time()
DOC = json.load(open(os.path.join(T4, "parts.json")))
REC = {r["name"]: r for r in DOC["parts"]}
DATA = json.load(open(os.path.join(HERE, "v1_data.json")))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
vl = bpy.context.view_layer
MATS = {}
OBJ = {}
Z_BASE_TOP = -86.0
Z_FLOOR = Z_BASE_TOP - S.BASE_H - S.FOOT_H          # -116.5


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


# ------------------------------------------------------------------------------------------------ materials
SPEC = {
    "biela": ((0.86, 0.86, 0.845), 0.30, 0.0), "cierna": ((0.018, 0.018, 0.02), 0.30, 0.0),
    "lesk": ((0.010, 0.010, 0.012), 0.06, 0.0), "sklo": ((0.008, 0.008, 0.01), 0.04, 0.0),
    "siva": ((0.62, 0.62, 0.62), 0.5, 0.0), "svetlo": ((0.13, 0.88, 1.0), 0.3, 0.0), "oci": ((1.0, 0.86, 0.62), 0.3, 0.0),
    "podlaha": ((0.78, 0.765, 0.75), 0.9, 0.0), "tien": ((0.006, 0.006, 0.007), 0.9, 0.0),
    "ocel": ((0.62, 0.63, 0.65), 0.28, 1.0), "nerez": ((0.70, 0.71, 0.72), 0.22, 1.0), "mosadz": ((0.80, 0.58, 0.25), 0.25, 1.0),
    "magnet": ((0.66, 0.66, 0.68), 0.2, 1.0), "guma": ((0.03, 0.03, 0.03), 0.65, 0.0),
    "servo": ((0.16, 0.24, 0.36), 0.42, 0.0), "konektor": ((0.86, 0.82, 0.70), 0.5, 0.0),
    "drot_r": ((0.70, 0.03, 0.02), 0.45, 0.0), "drot_c": ((0.025, 0.025, 0.025), 0.45, 0.0), "drot_z": ((0.85, 0.62, 0.02), 0.45, 0.0),
    "dps": ((0.03, 0.20, 0.09), 0.45, 0.0), "dps_modra": ((0.02, 0.07, 0.25), 0.45, 0.0), "servo_t4": ((0.035, 0.035, 0.04), 0.45, 0.0),
    "ffc": ((0.85, 0.48, 0.08), 0.35, 0.0), "pena": ((0.10, 0.10, 0.11), 0.9, 0.0),
}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c, r, met = SPEC[key]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = r
    b.inputs["Metallic"].default_value = met
    if key == "biela":
        b.inputs["Coat Weight"].default_value = 0.30; b.inputs["Coat Roughness"].default_value = 0.10
    if key in ("lesk", "cierna"):
        b.inputs["Coat Weight"].default_value = 1.0 if key == "lesk" else 0.4
        b.inputs["Coat Roughness"].default_value = 0.04 if key == "lesk" else 0.15
    if key in ("svetlo", "oci"):
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 2.0 if key == "svetlo" else 4.0
    MATS[key] = m
    return m


def cap_mat(key, rgb):
    k = "cap_" + key
    if k in MATS:
        return MATS[k]
    m = bpy.data.materials.new(k); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.8
    MATS[k] = m
    return m


def t4_key(name):
    r = REC.get(name, {})
    m = r.get("mat", "")
    if name == "T_mriezka":
        return "siva"
    return {"resin_white": "biela", "resin_black": "cierna", "resin_grey": "cierna", "resin_clear": "svetlo", "steel": "ocel",
            "stainless": "nerez", "brass": "mosadz", "magnet": "magnet", "pcb": "dps", "fpc": "ffc", "alu": "nerez"}.get(m, "ocel" if name.startswith(("skr", "podl", "vl_", "pd_")) else "servo_t4")


# ------------------------------------------------------------------------------------------------ mesh helpers
def link(ob):
    sc.collection.objects.link(ob)
    return ob


def smooth(o, ang=35):
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        bpy.ops.object.select_all(action="DESELECT")
        vl.objects.active = o; o.select_set(True)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(ang))
    except Exception:
        pass


def imp(path, name, key, M=None, sm=True):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    o.name = name
    o.data.materials.clear(); o.data.materials.append(mat(key))
    if M is not None:
        o.data.transform(M); o.data.update()
    if sm:
        smooth(o)
    OBJ[name] = o
    return o


def make(name, verts, faces, key, sm=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], faces)
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    me.materials.append(mat(key))
    if sm:
        for p in me.polygons:
            p.use_smooth = True
    OBJ[name] = ob
    return ob


def quads(K, N, flip=False):
    F = []
    for k in range(K - 1):
        for j in range(N):
            j1 = (j + 1) % N
            q = (k * N + j, (k + 1) * N + j, (k + 1) * N + j1, k * N + j1)
            F.append(q[::-1] if flip else q)
    return F


def rows_solid(name, rows, key, c_top=None, c_bot=None):
    K, N = rows.shape[:2]
    Vv = rows.reshape(-1, 3).tolist()
    F = quads(K, N)
    if c_top is not None:
        Vv.append(list(c_top)); c = len(Vv) - 1
        F += [(c, j, (j + 1) % N) for j in range(N)]
    if c_bot is not None:
        Vv.append(list(c_bot)); c = len(Vv) - 1; o = (K - 1) * N
        F += [(c, o + (j + 1) % N, o + j) for j in range(N)]
    ob = make(name, np.array(Vv), F, key)
    fix_normals(ob)
    return ob


def fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()


def bisect(ob, co, no, clear_outer=False, clear_inner=False):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(co), plane_no=Vector(no),
                           clear_outer=clear_outer, clear_inner=clear_inner)
    bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons:
        p.use_smooth = True


def copy(ob, name):
    o = ob.copy(); o.data = ob.data.copy(); o.name = name
    link(o)
    OBJ[name] = o
    return o


def apply_mods(o):
    bpy.ops.object.select_all(action="DESELECT")
    vl.objects.active = o; o.select_set(True)
    for m in list(o.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            say("modifier apply failed", o.name, m.name, e)


def solidify(o, t):
    m = o.modifiers.new("sol", "SOLIDIFY"); m.thickness = t; m.offset = -1.0; m.use_even_offset = True; m.use_rim = True
    apply_mods(o)


def bevel(o, w=0.28, seg=3, ang=38):
    m = o.modifiers.new("bev", "BEVEL"); m.width = w; m.segments = seg; m.limit_method = "ANGLE"
    m.angle_limit = math.radians(ang); m.harden_normals = False


def boolean(o, cutter, op="DIFFERENCE", apply=True):
    m = o.modifiers.new("bool", "BOOLEAN"); m.object = cutter; m.operation = op; m.solver = "EXACT"
    try:
        m.use_hole_tolerant = True
    except Exception:
        pass
    try:
        m.material_mode = "TRANSFER"
    except Exception:
        pass
    if apply:
        bpy.ops.object.select_all(action="DESELECT")
        vl.objects.active = o; o.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            say("boolean failed", o.name, e)


def remove(o):
    for k in [k for k, v in OBJ.items() if v == o]:
        del OBJ[k]
    bpy.data.objects.remove(o, do_unlink=True)


def world_verts(o):
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def mirror_copy(o, name):
    """mirror x -> -x (mesh data), fix the winding"""
    c = copy(o, name)
    c.modifiers.clear()
    c.data.transform(Matrix.Diagonal((-1, 1, 1, 1)))
    c.data.flip_normals()
    c.data.update()
    for m in o.modifiers:                     # re-add render-only bevels
        if m.type == "BEVEL":
            bevel(c, m.width, m.segments, math.degrees(m.angle_limit))
    return c


def M4(a):
    return Matrix([list(map(float, r)) for r in np.asarray(a)])


# ------------------------------------------------------------------------------------------------ torso / head / base
T_EXT = ["T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_klb_L", "T_klb_P", "T_svetlovod", "T_mriezka", "T_spodok"] + \
        [f"magnet_klb_{s}{i}" for s in "LP" for i in (1, 2, 3)]
B_COLLAR = {"golier_prstenec": "cierna", "golier_kotuc": "cierna"}
B_NECK = {"krk_predna_polovica": "cierna", "krk_zadna_polovica": "cierna"}
B_HEAD = {"hlava_skrupina": "biela", "ram_displeja": "lesk", "displej": "sklo", "oci_len_vizualizacia": "oci", "usi": "cierna",
          "led_kruzky": "svetlo", "usko_kryt": "cierna", "usko_lozisko": "cierna"}


def load_torso(names=None):
    for n in (names or T_EXT):
        imp(os.path.join(T4, "stl", n + ".stl"), n, t4_key(n))


def load_head(pan=0.0, head=True):
    Rz = Matrix.Rotation(math.radians(pan), 4, "Z")
    imp(os.path.join(B_STL, "golier_prstenec.stl"), "B_golier_prstenec", "cierna")
    imp(os.path.join(B_STL, "golier_kotuc.stl"), "B_golier_kotuc", "cierna", Rz)
    for n, k in B_NECK.items():
        imp(os.path.join(B_STL, n + ".stl"), "B_" + n, k, Rz)
    if head:
        for n, k in B_HEAD.items():
            imp(os.path.join(B_STL, n + ".stl"), "B_" + n, k, Rz)


def pill_outline(w, h, n=64):
    r = h / 2
    pts = []
    for i in range(n // 2 + 1):
        t = -math.pi / 2 + math.pi * i / (n // 2)
        pts.append((w / 2 - r + r * math.cos(t), r * math.sin(t)))
    for i in range(n // 2 + 1):
        t = math.pi / 2 + math.pi * i / (n // 2)
        pts.append((-(w / 2 - r) + r * math.cos(t), r * math.sin(t)))
    return np.array(pts)


def prism_y(name, outline, x, z, y0, y1, key):
    rows = np.array([[(x + px, y, z + pz) for px, pz in outline] for y in (y0, y1)])
    return rows_solid(name, rows, key, c_top=(x, y0, z), c_bot=(x, y1, z))


def load_base():
    """approved base slab of T3 (shape only) - same recipe as T3/build_scene.py"""
    be, bz = S.base_stations()
    rows = np.array([np.column_stack([S.base_section(e), np.full(S.COUNT, Z_BASE_TOP - z)]) for e, z in zip(be, bz)])
    base = rows_solid("Z_podstavec", rows, "biela", c_top=(0, 0, Z_BASE_TOP), c_bot=(0, 0, Z_BASE_TOP - S.BASE_H))
    BBAR = (36.0, 3.4, 15.5)
    yb = -S.BASE_D / 2
    cut = prism_y("cut_zsvetlo", pill_outline(BBAR[0], BBAR[1]), 0, Z_BASE_TOP - BBAR[2], yb - 10, yb + 1.0, "tien")
    boolean(base, cut); remove(cut)
    bevel(base, 0.25, 2, 50); smooth(base)
    prism_y("Z_svetlo", pill_outline(BBAR[0] - 0.4, BBAR[1] - 0.4), 0, Z_BASE_TOP - BBAR[2], yb + 0.8, yb + 4.0, "svetlo")
    fo = S.base_section(7.5)
    rows_solid("Z_patka", np.array([np.column_stack([fo, np.full(S.COUNT, z)]) for z in (Z_BASE_TOP - S.BASE_H + 1.0, Z_FLOOR)]),
               "cierna", c_top=(0, 0, Z_BASE_TOP - S.BASE_H + 1.0), c_bot=(0, 0, Z_FLOOR))


# ------------------------------------------------------------------------------------------------ arms
ROT = {1: [], -1: []}          # objects that turn with the arm, per side
STAT = {1: [], -1: []}         # arm-side objects that stay with the torso (bush, springs, wires in the torso)


def pebble(dx, sx, name, nu=150, nth=220):
    rows, top, bot = V.pebble_rows(nu, nth)
    K, N = rows.shape[:2]
    W = V.to_world(rows.reshape(-1, 3), dx, sx).reshape(K, N, 3)
    return rows_solid(name, W, "biela", c_top=V.to_world(top, dx, sx), c_bot=V.to_world(bot, dx, sx))


def build_arm_left(dx, v1, internals=True):
    """left arm at rest (sx = +1).  v1: shells with 2.0 wall + cover + servo + ...; approved: T3 look"""
    sx = 1
    pre = "A_"
    full = pebble(dx, sx, pre + "plny")
    p0 = V.to_world([0, 0, -V.L / 2], dx); nx = V.to_world([1, 0, -V.L / 2], dx) - p0; nx /= np.linalg.norm(nx)
    ptl, ntl = V.tip_plane_local()
    pt = V.to_world(ptl, dx); nt = V.dir_world(ntl)
    wall = V.WALL if v1 else 1.4
    outer = copy(full, pre + "vonk"); bisect(outer, p0 + nx * V.SEAM, nx, clear_inner=True)
    inner = copy(full, pre + "vnut"); bisect(inner, p0 - nx * V.SEAM, nx, clear_outer=True)
    tip = copy(inner, pre + "spicka"); bisect(tip, pt + nt * V.SEAM, nt, clear_inner=True)
    bisect(inner, pt - nt * V.SEAM, nt, clear_outer=True)
    tip.data.materials.clear(); tip.data.materials.append(mat("cierna"))
    for o in (outer, inner, tip):
        solidify(o, wall)
    out = dict(vonk=outer, vnut=inner, spicka=tip)
    if not v1:
        rin, cti, cbi = S.arm_points(inset=1.0)
        K, N = rin.shape[:2]
        core = rows_solid(pre + "tien", V.to_world(rin.reshape(-1, 3), dx).reshape(K, N, 3), "tien",
                          c_top=V.to_world(cti, dx), c_bot=V.to_world(cbi, dx))
        out["tien"] = core
        for o in (outer, inner, tip):
            bevel(o); smooth(o)
        remove(full)
        return out
    # ---- v1: cover trimmed by the pebble, hole in the inner shell, internals
    cover = imp(os.path.join(ST, "kryt_surovy.stl"), pre + "kryt", "cierna", sm=False)
    boolean(cover, full)
    smooth(cover, 40)
    out["kryt"] = cover
    cav = imp(os.path.join(ST, "dutina.stl"), "cut_dutina", "tien", sm=False)
    boolean(inner, cav); remove(cav)
    for o in (outer, inner, tip):
        bevel(o); smooth(o)
    remove(full)
    out["oring"] = imp(os.path.join(ST, "o_kruzok.stl"), pre + "oring", "guma")
    if internals:
        out["servo"] = imp(os.path.join(ST, "servo_telo.stl"), pre + "servo", "servo", sm=False)
        smooth(out["servo"], 40)
        out["hriadel"] = imp(os.path.join(ST, "servo_hriadel.stl"), pre + "hriadel", "mosadz")
        out["konektor"] = imp(os.path.join(ST, "konektor.stl"), pre + "konektor", "konektor", sm=False)
        out["lozko"] = imp(os.path.join(ST, "lozko.stl"), pre + "lozko", "biela", sm=False); fix_normals(out["lozko"])
        out["mag_von"] = imp(os.path.join(ST, "magnety_von.stl"), pre + "mag_von", "magnet")
        out["mag_vnu"] = imp(os.path.join(ST, "magnety_vnu.stl"), pre + "mag_vnu", "magnet")
        out["stl_von"] = imp(os.path.join(ST, "stlpiky_von.stl"), pre + "stl_von", "biela")
        out["stl_vnu"] = imp(os.path.join(ST, "stlpiky_vnu.stl"), pre + "stl_vnu", "biela")
        # static (torso side)
        out["puzdro"] = imp(os.path.join(ST, "puzdro.stl"), pre + "puzdro", "cierna")
        out["pruz1"] = imp(os.path.join(ST, "pruzinka_1.stl"), pre + "pruz1", "nerez")
        out["pruz2"] = imp(os.path.join(ST, "pruzinka_2.stl"), pre + "pruz2", "nerez")
        out["kruzok"] = imp(os.path.join(ST, "kruzok.stl"), pre + "kruzok", "nerez")
        # wires (Blender curves -> meshes)
        cols = ("drot_r", "drot_c", "drot_z")
        for k, pts in enumerate(DATA["wires"]):
            out[f"drot{k}"] = curve_tube(pre + f"drot{k}", pts, 0.3, cols[k])
        for k, pts in enumerate(DATA["lead"]):
            out[f"vyvod{k}"] = curve_tube(pre + f"vyvod{k}", pts, 0.3, cols[k])
    return out


def curve_tube(name, pts, r, key):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = r; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1.0)
    sp.order_u = 3; sp.use_endpoint_u = True; sp.resolution_u = 8
    ob = link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat(key))
    bpy.ops.object.select_all(action="DESELECT")
    vl.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object; ob.name = name
    OBJ[name] = ob
    return ob


ROTATING = ("vonk", "vnut", "spicka", "tien", "kryt", "oring", "servo", "hriadel", "konektor", "lozko", "mag_von", "mag_vnu",
            "stl_von", "stl_vnu", "vyvod0", "vyvod1", "vyvod2")


def build_arms(dx, v1, internals=True, right=True):
    L = build_arm_left(dx, v1, internals)
    arms = {1: L}
    if right:
        Rr = {}
        for k, o in L.items():
            Rr[k] = mirror_copy(o, o.name.replace("A_", "AP_"))
        arms[-1] = Rr
    return arms


def pose_arm(parts, deg):
    Mw = M4(V.swing_matrix(deg))
    for k, o in parts.items():
        if k in ROTATING:
            o.matrix_world = Mw
    vl.update()


# ------------------------------------------------------------------------------------------------ studio
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = A.exposure
sc.render.film_transparent = True
sc.render.threads_mode = "FIXED"; sc.render.threads = 3
W_ = bpy.data.worlds.new("w"); sc.world = W_; W_.use_nodes = True
W_.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.56, 1)
W_.node_tree.nodes["Background"].inputs[1].default_value = 0.22
LIGHTS = []
CTR = Vector((0, 0, -40.0))


def area(loc, tgt, energy, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    Lt = bpy.context.active_object
    Lt.data.energy, Lt.data.size, Lt.data.color = energy, size, color
    Lt.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    LIGHTS.append(Lt)
    return Lt


area((-380, -520, 430), CTR, 3.4e6, 520, (1.0, 0.985, 0.96))     # key: front-left, high
area((560, -330, 180), CTR, 1.5e6, 620, (0.96, 0.98, 1.0))       # fill: front-right, low
area((60, 120, 760), CTR, 1.9e6, 700)                            # top
area((330, 520, 330), CTR, 1.8e6, 420)                            # rim from behind
cam_d = bpy.data.cameras.new("cam"); cam_d.clip_start = 5; cam_d.clip_end = 1e5
CAM = link(bpy.data.objects.new("cam", cam_d)); sc.camera = CAM
FLOOR = None


def floor(on, z=Z_FLOOR):
    global FLOOR
    if FLOOR is None:
        bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, z))
        FLOOR = bpy.context.active_object; FLOOR.name = "podlaha"
        FLOOR.data.materials.append(mat("podlaha")); FLOOR.is_shadow_catcher = True
    FLOOR.hide_render = not on
    FLOOR.location.z = z


def rig_follow_camera(dv, ctr=None):
    ctr = Vector(ctr) if ctr is not None else CTR
    dv = Vector(dv).normalized()
    up = Vector((0, 0, 1)) if abs(dv.z) < 0.95 else Vector((0, 1, 0))
    right = dv.cross(up).normalized(); up2 = right.cross(dv).normalized()
    pos = [(-0.55, 0.62, 0.75), (0.85, 0.25, 0.5), (0.1, 1.0, 0.25), (0.45, 0.45, -0.8)]
    for Lt, (a, b, c) in zip(LIGHTS, pos):
        p = ctr + (right * a + up2 * b + dv * c).normalized() * 800
        Lt.location = p
        Lt.rotation_euler = (ctr - p).to_track_quat("-Z", "Y").to_euler()


def cam_ortho(tgt, dv, scale, res):
    dv = Vector(dv).normalized()
    sc.render.resolution_x, sc.render.resolution_y = res
    cam_d.type = "ORTHO"; cam_d.ortho_scale = scale; cam_d.sensor_fit = "HORIZONTAL"
    CAM.location = Vector(tgt) + dv * 1500
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()


def cam_persp(tgt, dv, lens, dist, res):
    dv = Vector(dv).normalized()
    sc.render.resolution_x, sc.render.resolution_y = res
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "HORIZONTAL"; cam_d.sensor_width = 36
    CAM.location = Vector(tgt) + dv * dist
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()


def fit_persp(objs, margin=0.05):
    """re-centre the target and set the distance so the objects fill the frame (perspective camera, fixed direction)"""
    P = np.concatenate([world_verts(o)[::5] for o in objs])
    for it in range(6):
        vl.update()
        Mi = np.array(CAM.matrix_world.inverted())
        Q = P @ Mi[:3, :3].T + Mi[:3, 3]
        f = cam_d.lens / cam_d.sensor_width
        u = f * Q[:, 0] / -Q[:, 2]; v = f * Q[:, 1] / -Q[:, 2]          # half-width units: frame spans u in [-0.5, 0.5]
        asp = sc.render.resolution_y / sc.render.resolution_x
        cu, cv = (u.min() + u.max()) / 2, (v.min() + v.max()) / 2
        su = (u.max() - u.min()) / (1 - 2 * margin); sv = (v.max() - v.min()) / (asp * (1 - 2 * margin))
        s = max(su, sv)
        R3 = CAM.matrix_world.to_3x3()
        dist = (CAM.location - Vector(P.mean(0))).length
        CAM.location = CAM.location + R3 @ Vector((cu * dist / f, cv * dist / f, 0))
        fwd = R3 @ Vector((0, 0, -1))
        CAM.location = CAM.location - fwd * (dist * (s - 1))
    vl.update()


def px(p):
    c = world_to_camera_view(sc, CAM, Vector(p))
    return [round(c.x * sc.render.resolution_x, 2), round((1 - c.y) * sc.render.resolution_y, 2)]


def save_cam(name, anchors=None, lines=None):
    d = dict(res=[sc.render.resolution_x, sc.render.resolution_y], type=cam_d.type, ortho_scale=cam_d.ortho_scale,
             lens=cam_d.lens, sensor_width=cam_d.sensor_width, matrix=[list(r) for r in CAM.matrix_world],
             anchors={k: px(v) for k, v in (anchors or {}).items()},
             lines={k: [px(p) for p in v] for k, v in (lines or {}).items()})
    json.dump(d, open(os.path.join(A.out, name + "_cam.json"), "w"), indent=1)


def render(name):
    if A.noren:
        say("no render", name); return
    sc.render.filepath = os.path.join(A.out, name + ".png")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    say(f"SHOT {name} {time.time() - t:.0f} s")


def show_only(objs):
    keep = set(id(o) for o in objs)
    for o in sc.objects:
        if o.type == "MESH" and o != FLOOR:
            o.hide_render = id(o) not in keep


# ================================================================================================ shots
def shot_front(which):
    v1 = which == "B"
    dx = V.DX if v1 else 0.0
    load_torso(); load_head(0.0); load_base()
    arms = build_arms(dx, v1, internals=False)
    vl.update()
    dv = (0, -1, 0)
    rig_follow_camera(dv)
    zc = (Z_FLOOR + 86.0) / 2
    W, H = A.res, int(A.res * 1.12)
    cam_ortho((0, 0, zc), dv, 250.0, (W, H))
    xa = 78.67 if not v1 else 90.67
    anchors = {"podstavec": (-52.0, -56.0, Z_BASE_TOP - 13.0), "kryt": (57.5, -12.0, -24.0), "klb_A": (48.6, -11.0, -24.0),
               "ruka_L": (xa - 6, 0, -40.0), "ruka_P": (-(xa - 6), 0, -40.0), "hlava": (0, -30, 60.0),
               "w_left": (-xa, 0, zc), "w_right": (xa, 0, zc), "b_left": (-S.BASE_W / 2, 0, zc), "b_right": (S.BASE_W / 2, 0, zc),
               "floor_c": (0, 0, Z_FLOOR), "arm_tip_L": (V.to_world([0, 0, -V.L], dx))[[0, 1, 2]].tolist(),
               "head_top": (0, 0, 86.0)}
    save_cam("front_" + which, anchors)
    render("front_" + which)


def shot_rez():
    names = [r["name"] for r in DOC["parts"] if r["group"] in ("T", "P", "L")
             and r["bbox"][1] > 22 and r["bbox"][0] < 96 and r["bbox"][3] > 2.5 and r["bbox"][4] < 9 and r["bbox"][5] > -72]
    say("section torso parts:", names)
    load_torso(names)
    arms = build_arms(V.DX, True, internals=True, right=False)
    parts = list(OBJ.values())
    # crop + cut: keep y >= 3 inside x 22..98, z -72..10
    bpy.ops.mesh.primitive_cube_add(size=1)
    cut = bpy.context.active_object; cut.name = "_rez"
    cut.scale = (76.0, 300.0, 92.0); cut.location = (60.0, V.SH_Y + 150.0, -26.0)
    capm = cap_mat("tmp", (1, 0, 1)); cut.data.materials.append(capm)
    cut.hide_render = True
    CAPS = {"biela": (0.93, 0.56, 0.18), "cierna": (0.27, 0.47, 0.72), "servo": (0.56, 0.40, 0.80), "guma": (0.62, 0.12, 0.14),
            "nerez": (0.60, 0.62, 0.66), "ocel": (0.60, 0.62, 0.66), "magnet": (0.60, 0.62, 0.66), "mosadz": (0.85, 0.70, 0.35),
            "konektor": (0.92, 0.88, 0.76), "drot_r": (0.9, 0.2, 0.15), "drot_c": (0.25, 0.25, 0.25), "drot_z": (0.95, 0.8, 0.2),
            "servo_t4": (0.5, 0.5, 0.5), "dps": (0.3, 0.55, 0.35), "dps_modra": (0.3, 0.4, 0.6), "ffc": (0.9, 0.6, 0.3),
            "svetlo": (0.5, 0.8, 0.9), "siva": (0.7, 0.7, 0.7), "pena": (0.4, 0.4, 0.4)}
    SHADE = {"A_puzdro": (0.16, 0.62, 0.66), "A_kryt": (0.10, 0.22, 0.46), "T_spodok": (0.50, 0.60, 0.72), "T_klb_L": (0.36, 0.58, 0.84),
             "A_vnut": (0.93, 0.56, 0.18), "A_vonk": (0.96, 0.66, 0.30), "A_lozko": (0.93, 0.56, 0.18), "A_spicka": (0.27, 0.47, 0.72),
             "T_bok_L": (0.90, 0.62, 0.30), "T_stred": (0.86, 0.58, 0.28), "A_stl_von": (0.96, 0.66, 0.30), "A_stl_vnu": (0.93, 0.56, 0.18)}
    for o in parts:
        if o.type != "MESH" or o == cut:
            continue
        apply_mods(o)
        P = world_verts(o)
        if P[:, 1].max() <= V.SH_Y + 0.01 or P[:, 0].max() < 22 or P[:, 0].min() > 98:
            o.hide_render = True
            continue
        key = o.data.materials[0].name if o.data.materials else "ocel"
        if P[:, 1].min() >= V.SH_Y and P[:, 0].min() > 22 and P[:, 0].max() < 98 and P[:, 2].min() > -72 and P[:, 2].max() < 20:
            continue                                    # entirely behind the plane and inside the crop: keep whole
        boolean(o, cut, "INTERSECT")
        cm = cap_mat(o.name, SHADE.get(o.name, CAPS.get(key, (0.6, 0.6, 0.6))))
        for j, ms in enumerate(o.data.materials):
            if ms and ms.name == capm.name:
                o.data.materials[j] = cm
        if len(o.data.polygons) == 0:
            o.hide_render = True
    vl.update()
    dv = (0, -1, 0)
    rig_follow_camera(dv, (60, 0, -28))
    x0, x1, z0, z1 = 27.0, 95.0, -67.0, 17.0
    W = A.res; H = int(W * (z1 - z0) / (x1 - x0))
    cam_ortho(((x0 + x1) / 2, 0, (z0 + z1) / 2), dv, x1 - x0, (W, H))
    yz = lambda a, b=0.0: V.ab_to_yz(a, b)
    def P3(x, a=0.0, b=0.0):
        y, z = yz(a, b); return (x, float(V.SH_Y), float(z))
    anchors = {"axis_l": (x0, V.SH_Y, V.ZS), "axis_r": (x1, V.SH_Y, V.ZS)}
    save_cam("rez", anchors)
    render("rez")


def shot_rozlozena():
    load_torso(["T_stred", "T_bok_L", "T_bok_P", "T_spodok", "T_klb_L", "T_klb_P", "T_svetlovod", "T_mriezka"] +
               [f"magnet_klb_{s}{i}" for s in "LP" for i in (1, 2, 3)])
    imp(os.path.join(B_STL, "golier_prstenec.stl"), "B_golier_prstenec", "cierna")
    imp(os.path.join(B_STL, "golier_kotuc.stl"), "B_golier_kotuc", "cierna")
    for n, k in B_NECK.items():
        imp(os.path.join(B_STL, n + ".stl"), "B_" + n, k)
    arms = build_arms(V.DX, True, internals=True, right=False)
    L = arms[1]
    OFF = {"kruzok": 14.0, "pruz1": 18.0, "pruz2": 21.0, "puzdro": 28.0, "T_klb_L": 54.0, "oring": 78.0, "kryt": 88.0,
           "servo": 108.0, "hriadel": 108.0, "konektor": 108.0, "vyvod0": 108.0, "vyvod1": 108.0, "vyvod2": 108.0,
           "vnut": 142.0, "lozko": 142.0, "stl_vnu": 142.0, "mag_vnu": 156.0, "spicka": 142.0,
           "mag_von": 174.0, "vonk": 194.0, "stl_von": 194.0}
    DZ = {"spicka": -16.0, "konektor": 9.0, "vyvod0": 9.0, "vyvod1": 9.0, "vyvod2": 9.0}
    for k in ("magnet_klb_L1", "magnet_klb_L2", "magnet_klb_L3"):
        OFF[k] = 54.0
    for k in [k for k in L if k.startswith("drot")]:
        L[k].hide_render = True
    for k, d in OFF.items():
        o = L.get(k) or OBJ.get(k)
        if o is None:
            continue
        o.location = (d, 0, DZ.get(k, 0.0))
    vl.update()
    dv = Vector((0.62, -1.0, 0.55)).normalized()
    rig_follow_camera(dv, (90, 0, -20))
    tgt = Vector((110.0, 0.0, -24.0))
    W, H = A.res, int(A.res * 0.56)
    cam_persp(tgt, dv, 85, 760, (W, H))
    fit_persp([o for o in sc.objects if o.type == "MESH" and not o.hide_render and o != FLOOR], 0.04)
    def c(k, p):
        return (Vector(p) + Vector((OFF.get(k, 0.0), 0, DZ.get(k, 0.0)))).to_tuple()
    ax = lambda x, a=0.0, b=0.0: (x, float(V.ab_to_yz(a, b)[0]), float(V.ab_to_yz(a, b)[1]))
    anchors = {
        "T_klb": c("T_klb_L", ax(55.0, -11.0)), "kruzok": c("kruzok", ax(39.6, -4.9)), "pruz": c("pruz2", ax(41.7, -4.9)),
        "puzdro": c("puzdro", ax(50.0, -4.0)), "oring": c("oring", ax(56.4, -11.9)), "kryt": c("kryt", ax(58.0, -15.0)),
        "servo": c("servo", ax(72.0, 6.0, -6.05)), "konektor": c("konektor", ax(68.0, -10.4)),
        "vnut": c("vnut", V.to_world([-9.0, -6.0, -30.0]).tolist()), "spicka": c("spicka", V.to_world([-5.0, -4.0, -66.0]).tolist()),
        "mag_vnu": c("mag_vnu", V.to_world(V.magnet_spots_local()[0] + np.array([-1.0, 0, 0])).tolist()),
        "mag_von": c("mag_von", V.to_world(V.magnet_spots_local()[0] + np.array([1.0, 0, 0])).tolist()),
        "vonk": c("vonk", V.to_world([10.0, -6.0, -30.0]).tolist()), "trup": (40.0, -30.0, -30.0),
        "drazka": c("puzdro", ax(57.85, 0.0, 0.0)),
    }
    lines = {"os": [(30.0, V.SH_Y, V.ZS), (250.0, V.SH_Y, V.ZS)]}
    save_cam("rozlozena", anchors, lines)
    render("rozlozena")


def shot_rozsah():
    load_torso(); load_head(0.0)
    load_base()
    arms = build_arms(V.DX, True, internals=False)
    L = arms[1]
    vl.update()
    dv = (1, 0, 0)
    rig_follow_camera(dv)
    zc = (Z_FLOOR + 90.0) / 2 + 2
    W, H = A.res, int(A.res * 1.0)
    cam_ortho((0, -4.0, zc), dv, 232.0, (W, H))
    tipL = V.to_world([0, 0, -V.L])
    anchors = {"axis": (100.0, V.SH_Y, V.ZS)}
    lines = {}
    for deg in (-45, 0, 90, 135):
        Mw = np.array(V.swing_matrix(deg))
        p = Mw[:3, :3] @ tipL + Mw[:3, 3]
        anchors[f"tip_{deg}"] = tuple(p)
        cen = V.to_world([0, 0, -V.L * 0.55]); q = Mw[:3, :3] @ cen + Mw[:3, 3]
        anchors[f"mid_{deg}"] = tuple(q)
    anchors["head_low"] = (60.0, -13.0, 17.2)
    save_cam("rozsah", anchors, lines)
    LEFT = [o for k, o in L.items()]
    others = [o for o in sc.objects if o.type == "MESH" and o not in LEFT and o != FLOOR]
    jobs = A.parts.split(",") if A.parts else ["telo", "0", "-45", "90", "135"]
    for j in jobs:
        if j == "telo":
            show_only(others)
            render("rozsah_telo")
        else:
            pose_arm(L, float(j))
            show_only(LEFT)
            render(f"rozsah_{j.replace('-', 'm')}")


def shot_hero():
    load_torso(); load_head(20.0); load_base()
    arms = build_arms(V.DX, True, internals=False)
    pose_arm(arms[1], 90.0)
    floor(True)
    dv = Vector((0.95, -0.80, 0.30)).normalized()
    lens = 120
    zf, ztop = Z_FLOOR, 88.0
    tgt = Vector((4.0, -6.0, (zf + ztop) / 2 + 3.0))
    span = (ztop - zf) * 1.22
    W, H = A.res, int(A.res * 1.2)
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = W, H
    CAM.location = tgt + dv * (span * lens / 24)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()
    Mw = np.array(V.swing_matrix(90.0))
    kr = Mw[:3, :3] @ np.array([60.0, -12.0, -26.0]) + Mw[:3, 3]
    anchors = {"kryt_L": (55.0, -12.4, -17.0), "kryt_P": (-55.0, -12.4, -17.0), "ruka_L": tuple(Mw[:3, :3] @ V.to_world([0, -10, -50]) + Mw[:3, 3]),
               "hlava": (20.0, -28.0, 60.0)}
    save_cam("hero", anchors)
    render("hero")


say("start", A.shot)
if A.shot in ("front_A", "front_B"):
    shot_front(A.shot[-1])
elif A.shot == "rez":
    shot_rez()
elif A.shot == "rozlozena":
    shot_rozlozena()
elif A.shot == "rozsah":
    shot_rozsah()
elif A.shot == "hero":
    shot_hero()
say("done")
