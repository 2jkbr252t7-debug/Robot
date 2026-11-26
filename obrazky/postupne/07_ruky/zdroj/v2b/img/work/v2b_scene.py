"""NOVA mini - arm drive v2 (judge-final K3): concept renders (Cycles CPU).  Reads T4 / B / T3 / img_v1 (never writes there).
Usage: /opt/venv/bl/bin/python v2_scene.py -- --shot prep|front|rez|vnutro|rozlozene|hero --res 1000 --samples 24 --out DIR
Writes DIR/<shot>.png (transparent film) + DIR/<shot>_cam.json (camera).  'prep' caches the modified torso meshes."""
import bpy, bmesh, sys, os, json, math, argparse, time
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g2b as G
V = G.V
S = V.S
T4 = "/tmp/claude-0/gapwf/fin/T4"
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
V1ST = "/tmp/claude-0/gapwf/fin/R1/img_v1/work/stl"
ST = os.path.join(HERE, "stl_b")
MOD = os.path.join(HERE, "stl_mod")
os.makedirs(MOD, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", default="front")
ap.add_argument("--res", type=int, default=700)
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--out", default=os.path.join(HERE, "r"))
ap.add_argument("--exposure", type=float, default=-0.3)
ap.add_argument("--noren", action="store_true")
ap.add_argument("--ghost", type=float, default=-57.0)
ap.add_argument("--res2", type=int, default=900)
ap.add_argument("--only", default="")
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)
T0 = time.time()
DOC = json.load(open(os.path.join(T4, "parts.json")))
REC = {r["name"]: r for r in DOC["parts"]}
DATA = json.load(open(os.path.join(HERE, "b1p_data.json")))
DX = G.DX

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
    "hlinik": ((0.80, 0.81, 0.83), 0.35, 1.0), "magnet": ((0.66, 0.66, 0.68), 0.2, 1.0), "guma": ((0.03, 0.03, 0.03), 0.65, 0.0),
    "servo": ((0.10, 0.17, 0.30), 0.42, 0.0), "servo_t4": ((0.035, 0.035, 0.04), 0.45, 0.0), "servo_mg": ((0.04, 0.07, 0.20), 0.35, 0.0),
    "dps": ((0.03, 0.20, 0.09), 0.45, 0.0), "dps_modra": ((0.02, 0.07, 0.25), 0.45, 0.0),
    "ffc": ((0.85, 0.48, 0.08), 0.35, 0.0), "ptfe": ((0.93, 0.93, 0.90), 0.55, 0.0), "pena": ((0.10, 0.10, 0.11), 0.9, 0.0),
    "kabel": ((0.55, 0.06, 0.04), 0.5, 0.0), "plast_biely": ((0.80, 0.78, 0.72), 0.5, 0.0),
    "kondenzator": ((0.05, 0.10, 0.30), 0.4, 0.0), "pet": ((0.75, 0.80, 0.85), 0.3, 0.0),
    "drot_r": ((0.70, 0.03, 0.02), 0.45, 0.0), "drot_c": ((0.025, 0.025, 0.025), 0.45, 0.0), "drot_z": ((0.85, 0.62, 0.02), 0.45, 0.0),
    "ocel_cierna": ((0.05, 0.05, 0.055), 0.35, 0.9), "tesnenie": ((0.02, 0.02, 0.025), 0.55, 0.0),
    "tough": ((0.10, 0.34, 0.24), 0.40, 0.0), "zinok": ((0.74, 0.76, 0.80), 0.30, 1.0), "magnet_n": ((0.78, 0.78, 0.80), 0.16, 1.0),
}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    if key == "duch":                           # translucent orange ghost (sweep of the lift servo)
        b.inputs["Base Color"].default_value = (1.0, 0.45, 0.08, 1)
        b.inputs["Alpha"].default_value = 0.45
        b.inputs["Roughness"].default_value = 0.6
        b.inputs["Emission Color"].default_value = (1.0, 0.45, 0.08, 1)
        b.inputs["Emission Strength"].default_value = 0.35
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        MATS[key] = m
        return m
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
    d = {"resin_white": "biela", "resin_black": "cierna", "resin_grey": "cierna", "resin_clear": "svetlo", "steel": "ocel",
         "stainless": "nerez", "brass": "mosadz", "magnet": "magnet", "pcb": "dps", "fpc": "ffc", "alu": "hlinik", "ptfe": "ptfe"}
    if m in d:
        return d[m]
    if name in ("servo_J1", "servo_pan", "reproduktor"):
        return "servo_t4"
    if name == "servo_zdvih":
        return "servo_mg"
    if name in ("DPS_riadenie", "menic"):
        return "dps"
    if name == "kondenzator":
        return "kondenzator"
    if name.startswith(("podlozka_J1", "podlozka_C_J1")):
        return "pet"
    if name.startswith(("pena", "tesnenie")):
        return "pena"
    if name == "usb_predlzovac":
        return "ffc"
    if name == "konektor_zdvih":
        return "plast_biely"
    if name.startswith(("kabel", "vyvod", "pigtail")):
        return "kabel"
    return "ocel"


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


def imp(path, name, key, M=None, sm=True, ang=35):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    o.name = name
    o.data.materials.clear(); o.data.materials.append(mat(key))
    if M is not None:
        o.data.transform(M); o.data.update()
    if sm:
        smooth(o, ang)
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


def quads(K, N):
    F = []
    for k in range(K - 1):
        for j in range(N):
            j1 = (j + 1) % N
            F.append((k * N + j, (k + 1) * N + j, (k + 1) * N + j1, k * N + j1))
    return F


def fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()


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


def bisect(ob, co, no, clear_outer=False, clear_inner=False, fill=False):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(co), plane_no=Vector(no),
                                 clear_outer=clear_outer, clear_inner=clear_inner)
    if fill:
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        try:
            bmesh.ops.edgenet_fill(bm, edges=edges)
        except Exception:
            pass
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
    c = copy(o, name)
    c.modifiers.clear()
    c.data.transform(Matrix.Diagonal((-1, 1, 1, 1)))
    c.data.flip_normals()
    c.data.update()
    for m in o.modifiers:
        if m.type == "BEVEL":
            bevel(c, m.width, m.segments, math.degrees(m.angle_limit))
    return c


def M4(a):
    return Matrix([list(map(float, r)) for r in np.asarray(a)])


def export_obj(o, path):
    bpy.ops.object.select_all(action="DESELECT")
    vl.objects.active = o; o.select_set(True)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, apply_modifiers=True)


# ------------------------------------------------------------------------------------------------ torso (T4 with the v2 changes)
REMOVED = {"T_klb_L", "T_klb_P", "zosilnovac"}
REMOVED_PRE = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14")
F3A2 = ("skr_F3a_2", "pd_F3a_2", "vl_F3a_2")
MODIFIED = ("T_spodok", "T_paluba", "T_bok_L", "T_bok_P", "menic")


def prep():
    """cache the modified T4 meshes (booleans) once"""
    cut = {n: imp(os.path.join(ST, n + ".stl"), n, "tien", sm=False) for n in ("cut_spodok_L", "cut_spodok_P", "cut_menic", "cut_paluba", "cut_bok_L")}
    cutP = mirror_copy(cut["cut_bok_L"], "cut_bok_P")
    for n, cl in (("T_spodok", ["cut_spodok_L", "cut_spodok_P", "cut_menic"]), ("T_paluba", ["cut_paluba"]), ("T_bok_L", ["cut_bok_L"]),
                  ("T_bok_P", [None])):
        o = imp(os.path.join(T4, "stl", n + ".stl"), n, "cierna", sm=False)
        for c in cl:
            t = time.time()
            boolean(o, cut[c] if c else cutP)
            say("cut", n, c, f"{time.time() - t:.1f}s", len(o.data.polygons))
        export_obj(o, os.path.join(MOD, n + ".stl"))
    # buck converter: from the right column, laid flat on the left floor under the servo pocket
    o = imp(os.path.join(T4, "stl", "menic.stl"), "menic", "dps", sm=False)
    o.data.transform(Matrix.Rotation(math.radians(-90), 4, "Y")); o.data.update()
    P = world_verts(o)
    c = (P.min(0) + P.max(0)) / 2
    bx = DATA["buck_box"]
    o.data.transform(Matrix.Translation(Vector(((bx[0] + bx[1]) / 2 - c[0], (bx[2] + bx[3]) / 2 - c[1], bx[5] - P[:, 2].max()))))
    o.data.update()
    P = world_verts(o); say("menic moved bbox", P.min(0).round(2), P.max(0).round(2))
    export_obj(o, os.path.join(MOD, "menic.stl"))


def t4_path(n):
    if n in MODIFIED:
        return os.path.join(MOD, n + ".stl")
    return os.path.join(T4, "stl", n + ".stl")


def keep_t4(n):
    return not (n in REMOVED or n.startswith(REMOVED_PRE))


def load_t4(names):
    out = []
    for n in names:
        if not keep_t4(n):
            continue
        o = imp(t4_path(n), n, t4_key(n))
        if n in F3A2:
            o.location.x = -1.1
        out.append(o)
    return out


B_COLLAR = {"golier_prstenec": "cierna", "golier_kotuc": "cierna"}
B_NECK = {"krk_predna_polovica": "cierna", "krk_zadna_polovica": "cierna"}
B_HEAD = {"hlava_skrupina": "biela", "ram_displeja": "lesk", "displej": "sklo", "oci_len_vizualizacia": "oci", "usi": "cierna",
          "led_kruzky": "svetlo", "usko_kryt": "cierna", "usko_lozisko": "cierna"}
T_EXT = ["T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka", "T_spodok"]


def load_head(pan=0.0, head=True, neck=True):
    Rz = Matrix.Rotation(math.radians(pan), 4, "Z")
    out = [imp(os.path.join(B_STL, "golier_prstenec.stl"), "B_golier_prstenec", "cierna"),
           imp(os.path.join(B_STL, "golier_kotuc.stl"), "B_golier_kotuc", "cierna", Rz)]
    if neck:
        for n, k in B_NECK.items():
            out.append(imp(os.path.join(B_STL, n + ".stl"), "B_" + n, k, Rz))
    if head:
        for n, k in B_HEAD.items():
            out.append(imp(os.path.join(B_STL, n + ".stl"), "B_" + n, k, Rz))
    return out


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


# ------------------------------------------------------------------------------------------------ new drive parts
# name -> (material, group): group S = static torso side, V = vertical drive (turns with the servo), A = arm shaft (turns with
# the shaft), R = rotates with the arm, P = plug cartridge (static)
NEW = {
    "stlp": ("cierna", "S"), "vypln": ("cierna", "S"), "vypln_priecka": ("cierna", "S"), "vlozky": ("mosadz", "S"),
    "vlozka_F3a": ("mosadz", "S"), "servo_telo": ("servo", "S"), "servo_hriadel": ("plast_biely", "S"),
    "B1": ("ocel", "S"), "B1_tesnenie": ("tesnenie", "S"),
    "spojka": ("tough", "V"), "skrutka_spojky": ("ocel_cierna", "V"), "hriadel_zvisly": ("tough", "V"),
    "podlozka_pastorka": ("tough", "V"), "pastorok": ("tough", "V"),
    "koleso": ("tough", "A"), "podlozka_kolesa": ("tough", "A"), "skrutka_M4": ("ocel", "A"), "c_podlozka": ("tough", "A"),
    "unasac": ("tough", "A"), "magnety_spojky": ("magnet_n", "A"),
    "A1": ("ocel", "P"), "A1_tesnenie": ("tesnenie", "P"), "A2": ("ocel", "P"), "A2_tesnenie": ("tesnenie", "P"),
    "puzdro": ("tough", "P"), "zatka": ("cierna", "P"), "zatka_skrutky": ("ocel_cierna", "P"),
    "L6800": ("ocel", "R"), "L6800_tesnenie": ("tesnenie", "R"), "podlozka_M10": ("zinok", "R"), "kruzok": ("biela", "R"),
}
ROT_A = ("koleso", "podlozka_kolesa", "skrutka_M4", "c_podlozka", "unasac", "magnety_spojky", "L6800", "L6800_tesnenie",
         "podlozka_M10", "kruzok")
SIDE = {1: {}, -1: {}}


def load_new(names=None, sides=(1, -1)):
    for n, (k, g) in NEW.items():
        if names is not None and n not in names:
            continue
        o = imp(os.path.join(ST, n + ".stl"), n + "_L", k, sm=not n.startswith("vypln"), ang=32)
        if n.startswith("vypln"):
            vox_smooth(o)
        SIDE[1][n] = o
        if -1 in sides:
            SIDE[-1][n] = mirror_copy(o, n + "_P")
        if 1 not in sides:
            o.hide_render = True
    cab = []
    cols = ("drot_r", "drot_c", "drot_z")
    for k in range(3):
        pts = [(x, y + 0.0, z + 0.62 * (k - 1)) for x, y, z in DATA["cable"]]
        cab.append(curve_tube(f"kabel{k}_L", pts, 0.32, cols[k]))
    SIDE[1]["kabel"] = cab
    if -1 in sides:
        SIDE[-1]["kabel"] = [mirror_copy(c, c.name.replace("_L", "_P")) for c in cab]
    if 1 not in sides:
        for c in cab:
            c.hide_render = True


def vox_smooth(o, vs=0.16, it=14):
    """voxel staircase (0.5 mm) -> remeshed + Laplacian-smoothed surface (concept look; CAD will have real fillets)"""
    m = o.modifiers.new("rm", "REMESH"); m.mode = "VOXEL"; m.voxel_size = vs; m.adaptivity = 0.0; m.use_smooth_shade = True
    apply_mods(o)
    m = o.modifiers.new("ls", "LAPLACIANSMOOTH"); m.iterations = it; m.lambda_factor = 1.0; m.use_volume_preserve = True
    m.use_normalized = True
    apply_mods(o)
    for p in o.data.polygons:
        p.use_smooth = True


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


# ------------------------------------------------------------------------------------------------ arms (passive pebble, dx -1)
WALL = 1.6


def pebble(dx, name, nu=150, nth=220):
    rows, top, bot = V.pebble_rows(nu, nth)
    K, N = rows.shape[:2]
    W = V.to_world(rows.reshape(-1, 3), dx).reshape(K, N, 3)
    return rows_solid(name, W, "biela", c_top=V.to_world(top, dx), c_bot=V.to_world(bot, dx))


def xcyl_obj(name, r, x0, x1, y=G.YA, z=G.ZA, n=96):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rows = np.array([[(x, y + r * math.cos(t), z + r * math.sin(t)) for t in th] for x in (x0, x1)])
    return rows_solid(name, rows, "tien", c_top=(x0, y, z), c_bot=(x1, y, z))


def build_arm_left(dx=DX, internals=True):
    pre = "A_"
    full = pebble(dx, pre + "plny")
    p0 = V.to_world([0, 0, -V.L / 2], dx); nx = V.to_world([1, 0, -V.L / 2], dx) - p0; nx /= np.linalg.norm(nx)
    ptl, ntl = V.tip_plane_local()
    pt = V.to_world(ptl, dx); nt = V.dir_world(ntl)
    outer = copy(full, pre + "vonk"); bisect(outer, p0 + nx * V.SEAM, nx, clear_inner=True)
    inner = copy(full, pre + "vnut"); bisect(inner, p0 - nx * V.SEAM, nx, clear_outer=True)
    tip = copy(inner, pre + "spicka"); bisect(tip, pt + nt * V.SEAM, nt, clear_inner=True)
    bisect(inner, pt - nt * V.SEAM, nt, clear_outer=True)
    tip.data.materials.clear(); tip.data.materials.append(mat("cierna"))
    for o in (outer, inner, tip):
        solidify(o, WALL)
    hole = xcyl_obj("cut_otvor", 7.0, 44.0, 56.0)
    boolean(inner, hole); remove(hole)
    out = dict(vonk=outer, vnut=inner, spicka=tip)
    if internals:
        hub = imp(os.path.join(ST, "naboj_surovy.stl"), pre + "naboj", "biela", sm=False)
        boolean(hub, full, "INTERSECT")
        smooth(hub, 40)
        out["naboj"] = hub
        sh = Matrix.Translation(Vector((dx - V.DX, 0, 0)))
        out["mag_von"] = imp(os.path.join(V1ST, "magnety_von.stl"), pre + "mag_von", "magnet", sh)
        out["mag_vnu"] = imp(os.path.join(V1ST, "magnety_vnu.stl"), pre + "mag_vnu", "magnet", sh)
        out["stl_von"] = imp(os.path.join(V1ST, "stlpiky_von.stl"), pre + "stl_von", "biela", sh)
        out["stl_vnu"] = imp(os.path.join(V1ST, "stlpiky_vnu.stl"), pre + "stl_vnu", "biela", sh)
    for o in (outer, inner, tip):
        bevel(o); smooth(o)
    remove(full)
    return out


def build_arms(right=True, internals=True):
    L = build_arm_left(DX, internals)
    arms = {1: L}
    if right:
        arms[-1] = {k: mirror_copy(o, o.name.replace("A_", "AP_")) for k, o in L.items()}
    return arms


def pose_arm(parts, deg, side=1):
    Mw = np.array(V.swing_matrix(deg))
    if side == -1:
        Dg = np.diag([-1.0, 1, 1, 1]); Mw = Dg @ Mw @ Dg
    for k, o in parts.items():
        o.matrix_world = M4(Mw)
    for n in ROT_A:
        o = SIDE[side].get(n)
        if o is not None:
            o.matrix_world = M4(Mw)
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


area((-380, -520, 430), CTR, 3.4e6, 520, (1.0, 0.985, 0.96))
area((560, -330, 180), CTR, 1.5e6, 620, (0.96, 0.98, 1.0))
area((60, 120, 760), CTR, 1.9e6, 700)
area((330, 520, 330), CTR, 1.8e6, 420)
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
    P = np.concatenate([world_verts(o)[::3] for o in objs])
    for it in range(8):
        vl.update()
        Mi = np.array(CAM.matrix_world.inverted())
        Q = P @ Mi[:3, :3].T + Mi[:3, 3]
        f = cam_d.lens / cam_d.sensor_width
        u = f * Q[:, 0] / -Q[:, 2]; v = f * Q[:, 1] / -Q[:, 2]
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


def save_cam(name, extra=None):
    d = dict(res=[sc.render.resolution_x, sc.render.resolution_y], type=cam_d.type, ortho_scale=cam_d.ortho_scale,
             lens=cam_d.lens, sensor_width=cam_d.sensor_width, sensor_fit=cam_d.sensor_fit, sensor_height=cam_d.sensor_height,
             matrix=[list(r) for r in CAM.matrix_world], extra=extra or {})
    json.dump(d, open(os.path.join(A.out, name + "_cam.json"), "w"), indent=1)


def vis_anchor(objs, target, n_try=8000, pix=None):
    """pixel (u, v) of a camera-visible vertex of objs nearest to the world point target (perspective camera)"""
    for o in sc.objects:
        if o.type == "MESH":
            o.hide_viewport = o.hide_render
    vl.update()
    dg = bpy.context.evaluated_depsgraph_get()
    names = set(o.name for o in objs)
    P = np.concatenate([world_verts(o) for o in objs])
    if pix is not None:
        W_, H_ = sc.render.resolution_x, sc.render.resolution_y
        f = cam_d.lens / cam_d.sensor_width * W_
        R3 = CAM.matrix_world.to_3x3()
        cl0 = CAM.matrix_world.translation
        for rr in np.arange(0.0, 200.0, 4.0):
            for a in np.linspace(0, 2 * np.pi, max(1, int(rr)), endpoint=False):
                u, v = pix[0] + rr * math.cos(a), pix[1] + rr * math.sin(a)
                dvec = (R3 @ Vector(((u - W_ / 2) / f, -(v - H_ / 2) / f, -1.0))).normalized()
                ok, loc, nrm, idx, ob, M = sc.ray_cast(dg, cl0, dvec, distance=5000.0)
                if ok and ob.name in names:
                    say("anchor(pix)", ob.name, np.round(np.array(loc), 1), [round(u, 1), round(v, 1)])
                    return [round(u, 2), round(v, 2)]
        say("pix anchor not found", list(names)[:1])
        t = np.asarray(target, float)
        order = np.argsort(np.linalg.norm(P - t, axis=1))
    else:
        t = np.asarray(target, float)
        order = np.argsort(np.linalg.norm(P - t, axis=1))
    cl = np.array(CAM.matrix_world.translation)
    for i in order[:n_try]:
        p = P[i]
        dvec = p - cl
        dist = float(np.linalg.norm(dvec))
        ok, loc, nrm, idx, ob, M = sc.ray_cast(dg, Vector(cl), Vector(dvec / dist), distance=dist + 1.0)
        if ok and ob.name in names and (Vector(loc) - Vector(p)).length < 0.6:
            say("anchor", list(names)[0], np.round(p, 1), px(p))
            return px(p)
    say("anchor not visible", list(names)[:2], target)
    return px(P[order[0]])


def px(p):
    from bpy_extras.object_utils import world_to_camera_view
    c = world_to_camera_view(sc, CAM, Vector(tuple(map(float, p))))
    return [round(c.x * sc.render.resolution_x, 2), round((1 - c.y) * sc.render.resolution_y, 2)]


def render(name):
    if A.noren:
        say("no render", name); return
    sc.render.filepath = os.path.join(A.out, name + ".png")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    say(f"SHOT {name} {time.time() - t:.0f} s")


# ------------------------------------------------------------------------------------------------ section helper
CAPC = {"biela": (0.95, 0.66, 0.34), "cierna": (0.42, 0.54, 0.70), "servo": (0.58, 0.45, 0.82), "mosadz": (0.92, 0.74, 0.30),
        "ocel": (0.66, 0.68, 0.72), "nerez": (0.66, 0.68, 0.72), "hlinik": (0.72, 0.74, 0.78), "ocel_cierna": (0.36, 0.37, 0.40),
        "tesnenie": (0.25, 0.25, 0.28), "magnet": (0.66, 0.68, 0.72), "servo_t4": (0.50, 0.50, 0.52), "servo_mg": (0.40, 0.45, 0.62),
        "dps": (0.30, 0.58, 0.40), "dps_modra": (0.32, 0.42, 0.66), "pena": (0.30, 0.30, 0.32), "ffc": (0.92, 0.62, 0.30),
        "ptfe": (0.85, 0.85, 0.80), "kabel": (0.80, 0.25, 0.20), "kondenzator": (0.30, 0.38, 0.62), "pet": (0.75, 0.80, 0.85),
        "svetlo": (0.5, 0.8, 0.9), "siva": (0.7, 0.7, 0.7), "plast_biely": (0.85, 0.83, 0.76),
        "tough": (0.36, 0.72, 0.52), "zinok": (0.66, 0.68, 0.72), "magnet_n": (0.86, 0.32, 0.36)}
CAPN = {"zatka_L": (0.20, 0.32, 0.58), "stlp_L": (0.30, 0.44, 0.66), "vypln_L": (0.30, 0.44, 0.66), "vypln_priecka_L": (0.30, 0.44, 0.66),
        "spojka_L": (0.55, 0.84, 0.66), "hriadel_zvisly_L": (0.22, 0.56, 0.40), "pastorok_L": (0.42, 0.78, 0.58), "koleso_L": (0.30, 0.64, 0.46),
        "unasac_L": (0.36, 0.72, 0.52), "puzdro_L": (0.42, 0.78, 0.58), "podlozka_pastorka_L": (0.20, 0.52, 0.36),
        "podlozka_kolesa_L": (0.20, 0.52, 0.36), "c_podlozka_L": (0.20, 0.52, 0.36), "kruzok_L": (0.92, 0.60, 0.28), "T_spodok": (0.42, 0.54, 0.70), "T_paluba": (0.46, 0.56, 0.70),
        "A_vonk": (0.98, 0.74, 0.44), "A_vnut": (0.95, 0.66, 0.34), "A_naboj": (0.92, 0.60, 0.28), "T_bok_L": (0.93, 0.70, 0.42),
        "T_stred": (0.90, 0.68, 0.40)}


def section_y(objs, y0, crop):
    """keep y >= y0 inside the crop box (x0, x1, z0, z1); cap faces coloured per part"""
    x0, x1, z0, z1 = crop
    bpy.ops.mesh.primitive_cube_add(size=1)
    cut = bpy.context.active_object; cut.name = "_rez"
    cut.scale = (x1 - x0, 400.0, z1 - z0); cut.location = ((x0 + x1) / 2, y0 + 200.0, (z0 + z1) / 2)
    capm = cap_mat("tmp", (1, 0, 1)); cut.data.materials.append(capm)
    cut.hide_render = True
    for o in objs:
        if o.type != "MESH" or o == cut or o.hide_render:
            continue
        apply_mods(o)
        P = world_verts(o)
        if len(P) == 0 or P[:, 1].max() <= y0 + 0.01 or P[:, 0].max() < x0 or P[:, 0].min() > x1 or P[:, 2].max() < z0 or P[:, 2].min() > z1:
            o.hide_render = True
            continue
        key = o.data.materials[0].name if o.data.materials else "ocel"
        if P[:, 1].min() >= y0 and P[:, 0].min() > x0 and P[:, 0].max() < x1 and P[:, 2].min() > z0 and P[:, 2].max() < z1:
            continue
        t = time.time()
        boolean(o, cut, "INTERSECT")
        cm = cap_mat(o.name, CAPN.get(o.name, CAPC.get(key, (0.6, 0.6, 0.6))))
        for j, ms in enumerate(o.data.materials):
            if ms and ms.name == capm.name:
                o.data.materials[j] = cm
        if len(o.data.polygons) == 0:
            o.hide_render = True
        if time.time() - t > 3:
            say("  cut", o.name, f"{time.time() - t:.1f}s")
    vl.update()


# ================================================================================================ shots (B1+ fixer)
REZ_CROP = (18.0, 84.0, -84.0, 3.0)
DET_CROP = (31.0, 70.0, -47.5, -2.5)


def shot_rez():
    names = [r["name"] for r in DOC["parts"] if r["bbox"][1] > 18 and r["bbox"][3] > 3.0 and r["bbox"][5] > -86 and r["group"] in "TPL"]
    load_t4(names)
    load_new(sides=(1,))
    arms = build_arms(False, internals=True)
    vl.update()
    objs = [o for o in sc.objects if o.type == "MESH"]
    section_y(objs, G.YA, REZ_CROP)
    dv = (0, -1, 0)
    rig_follow_camera(dv, (50, 0, -40))
    x0, x1, z0, z1 = REZ_CROP
    W = A.res; H = int(W * (z1 - z0) / (x1 - x0))
    cam_ortho(((x0 + x1) / 2, 0, (z0 + z1) / 2), dv, x1 - x0, (W, H))
    save_cam("rez", dict(crop=REZ_CROP))
    render("rez")
    x0, x1, z0, z1 = DET_CROP
    W = A.res2; H = int(W * (z1 - z0) / (x1 - x0))
    cam_ortho(((x0 + x1) / 2, 0, (z0 + z1) / 2), dv, x1 - x0, (W, H))
    save_cam("rez_det", dict(crop=DET_CROP))
    render("rez_det")


# exploded offsets (dx, dz) per part, world mm
RA_DX, RA_DZ = -95.0, -75.0          # second row: the arm sub-assembly
EXP_OFF = {
    "pastorok": (-28, 10), "podlozka_pastorka": (-28, 6), "B1": (-28, 1.5), "B1_tesnenie": (-28, 1.5),
    "hriadel_zvisly": (-28, -10), "skrutka_spojky": (-28, -24), "spojka": (-28, -36), "servo_telo": (-28, -52), "servo_hriadel": (-28, -52),
    "koleso": (8, 0), "podlozka_kolesa": (11, 0), "A1": (14, 0), "A1_tesnenie": (14, 0), "puzdro": (17, 0), "A2": (20, 0),
    "A2_tesnenie": (20, 0), "zatka": (42, 0), "zatka_skrutky": (56, 0), "c_podlozka": (52, 0), "skrutka_M4": (65, 0),
    "L6800": (80 + RA_DX, RA_DZ), "L6800_tesnenie": (80 + RA_DX, RA_DZ), "podlozka_M10": (112 + RA_DX, RA_DZ),
    "unasac": (120 + RA_DX, RA_DZ), "magnety_spojky": (128 + RA_DX, RA_DZ), "kruzok": (133 + RA_DX, RA_DZ),
}
EXP_ARM = {"vnut": 95, "naboj": 95, "stl_vnu": 95, "mag_vnu": 95, "spicka": 95, "mag_von": 152, "vonk": 168, "stl_von": 168}


def shot_rozlozene():
    load_new(sides=(1,))
    arms = build_arms(False, internals=True)
    L = arms[1]
    Sd = SIDE[1]
    for n, (dxo, dzo) in EXP_OFF.items():
        o = Sd.get(n)
        if o is not None:
            o.location = (dxo, 0, dzo)
    # C-shim: turn its opening to the camera (opening +Y -> rotate about the shoulder axis by -120 deg so it faces up-front)
    cs = Sd["c_podlozka"]
    Rx = Matrix.Translation(Vector((0, G.YA, G.ZA))) @ Matrix.Rotation(math.radians(100), 4, "X") @ Matrix.Translation(Vector((0, -G.YA, -G.ZA)))
    cs.matrix_world = Matrix.Translation(Vector((EXP_OFF["c_podlozka"][0], 0, EXP_OFF["c_podlozka"][1]))) @ Rx
    # the arm-side parts that sit on the shoulder axis follow the second-row shift
    for c in Sd["kabel"]:
        c.location = EXP_OFF["servo_telo"][0], 0, EXP_OFF["servo_telo"][1]
    for k, d in EXP_ARM.items():
        if k in L:
            L[k].location = (d + RA_DX, 0, RA_DZ)
    vl.update()
    dv = Vector((0.45, -1.0, 0.45)).normalized()
    rig_follow_camera(dv, (70, 0, -70))
    W, H = A.res, int(A.res * 0.92)
    cam_persp(Vector((70.0, 0.0, -70.0)), dv, 80, 700, (W, H))
    vis = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and o != FLOOR]
    fit_persp(vis, 0.025)

    def A_(n, t):
        o = Sd.get(n) or L.get(n)
        d = EXP_OFF.get(n, (EXP_ARM.get(n, 0) + RA_DX, RA_DZ) if n in EXP_ARM else (0, 0))
        return vis_anchor([o], (t[0] + d[0], t[1], t[2] + d[1]))
    anc = {"stlp": A_("stlp", (36.4, -20.0, -55.0)), "vypln": A_("vypln_priecka", (37.0, -9.0, -31.0)),
           "B1": A_("B1", (41.5, 3.0, -23.9)), "vlozky": A_("vlozky", (38.4, 10.79, -21.5)),
           "pastorok": A_("pastorok", (39.0, -1.0, -18.0)), "podlozka_pastorka": A_("podlozka_pastorka", (40.9, 3.0, -23.4)),
           "hriadel_zvisly": A_("hriadel_zvisly", (39.0, 1.5, -30.0)), "skrutka_spojky": A_("skrutka_spojky", (40.0, 2.0, -38.6)),
           "spojka": A_("spojka", (41.0, -1.0, -41.0)), "servo": A_("servo_telo", (45.05, -6.0, -56.0)),
           "koleso": A_("koleso", (42.5, 3.0, -11.0)), "podlozka_kolesa": A_("podlozka_kolesa", (44.5, 3.0, -14.2)),
           "A1": A_("A1", (47.04, 3.0, -13.6)), "puzdro": A_("puzdro", (50.0, 3.0, -13.5)), "A2": A_("A2", (55.1, 3.0, -13.6)),
           "zatka": A_("zatka", (44.0, -6.0, -6.0)), "zatka_skrutky": A_("zatka_skrutky", (43.7, 3.0, -8.0)),
           "c_podlozka": A_("c_podlozka", (59.95, 3.0, -21.0)), "skrutka_M4": A_("skrutka_M4", (62.0, 3.0, -13.5)),
           "L6800": A_("L6800", (60.3, -4.0, -10.0)), "vnut": A_("vnut", (56.0, -14.0, -40.0)),
           "podlozka_M10": A_("podlozka_M10", (63.2, 0.0, -9.0)), "unasac": A_("unasac", (66.25, 3.0, -6.0)),
           "magnety_spojky": A_("magnety_spojky", (65.5, 3.0, -9.3)), "kruzok": A_("kruzok", (67.55, -5.0, -9.0)),
           "mag_von": A_("mag_von", (66.0, -12.0, -12.0)), "vonk": A_("vonk", (72.0, -14.0, -40.0))}
    rows = {"r1": px((60.0, G.YA, 2.0)), "r2": px((60.0 + 95.0 + RA_DX, G.YA, -48.0 + RA_DZ)),
            "ax1": [px((G.XV, G.YA, G.ZA)), px((64.0 + 65.0, G.YA, G.ZA))],
            "ax2": [px((55.3 + 80 + RA_DX, G.YA, G.ZA + RA_DZ)), px((67.55 + 133 + RA_DX, G.YA, G.ZA + RA_DZ))]}
    save_cam("rozlozene", dict(off={k: list(v) for k, v in EXP_OFF.items()}, arm=EXP_ARM, anchors=anc, rows=rows))
    render("rozlozene")


ICONS = {   # key: (objects, view direction)
    "zatka": (["zatka"], (1.0, -0.9, 0.55)), "spojka": (["spojka"], (0.8, -1.0, 0.9)), "hriadel_zvisly": (["hriadel_zvisly"], (0.9, -1.0, 0.35)),
    "pastorok": (["pastorok"], (0.7, -1.0, 0.75)), "koleso": (["koleso"], (-1.0, -0.8, 0.45)), "puzdro": (["puzdro"], (1.0, -0.9, 0.5)),
    "naboj": (["A_naboj"], (-1.0, -0.75, 0.45)), "kruzok": (["kruzok"], (1.0, -0.9, 0.5)), "unasac": (["unasac", "magnety_spojky"], (1.0, -0.7, 0.5)),
    "unasac_zdola": (["unasac"], (-1.0, -0.7, 0.5)),
    "podlozky": (["podlozka_pastorka", "podlozka_kolesa", "c_podlozka"], (1.0, -0.8, 0.5)),
    "servo": (["servo_telo", "servo_hriadel"], (0.9, -1.0, 0.6)), "MR63": (["B1", "B1_tesnenie"], (0.7, -1.0, 0.9)),
    "MR74": (["A1", "A1_tesnenie"], (1.0, -0.9, 0.5)), "L6800": (["L6800", "L6800_tesnenie"], (1.0, -0.9, 0.5)),
    "M4": (["skrutka_M4"], (1.0, -1.4, 0.6)), "M2_spojka": (["skrutka_spojky"], (0.8, -1.0, 0.9)),
    "M2_zapustne": (["zatka_skrutky"], (1.0, -0.6, 0.5)), "vlozky": (["vlozky"], (1.0, -0.6, 0.5)),
    "M10": (["podlozka_M10"], (1.0, -0.9, 0.5)), "magnety": (["magnety_spojky"], (1.0, -0.9, 0.5)),
    "stlp": (["stlp", "vypln", "vypln_priecka", "B1", "vlozky"], (1.0, -1.0, 0.6)),
}


def shot_diely():
    load_new(sides=(1,))
    arms = build_arms(False, internals=True)
    Sd = SIDE[1]
    for c in Sd["kabel"]:
        c.hide_render = True
    allm = [o for o in sc.objects if o.type == "MESH"]
    # small shims: spread them for the icon (they sit on different axes)
    ps, gs, cs = Sd["podlozka_pastorka"], Sd["podlozka_kolesa"], Sd["c_podlozka"]
    zc = sum(G.PSHIM["z"]) / 2
    ps.matrix_world = Matrix.Translation(Vector((44.4, G.YA - 7.0, G.ZA))) @ Matrix.Rotation(math.radians(90), 4, "Y") @ \
        Matrix.Translation(Vector((-G.XV, -G.YA, -zc)))
    xc = sum(G.CSHIM["x"]) / 2
    cs.matrix_world = Matrix.Translation(Vector((44.4 - xc, 10.0, 0))) @ Matrix.Translation(Vector((0, G.YA, G.ZA))) @ \
        Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation(Vector((0, -G.YA, -G.ZA)))
    out = {}
    sc.render.film_transparent = True
    for key, (names, dv) in ICONS.items():
        if A.only and key not in A.only.split(","):
            continue
        objs = [Sd.get(n) or OBJ.get(n) for n in names]
        objs = [o for o in objs if o is not None]
        for o in allm:
            o.hide_render = True
        for o in objs:
            o.hide_render = False
        P = np.concatenate([world_verts(o) for o in objs])
        c = (P.min(0) + P.max(0)) / 2
        dvv = Vector(dv).normalized()
        rig_follow_camera(dvv, tuple(c))
        cam_ortho(Vector(tuple(c)), dvv, 10.0, (A.res, A.res))
        Mi = np.array(CAM.matrix_world.inverted())
        Q = P @ Mi[:3, :3].T + Mi[:3, 3]
        span = max(Q[:, 0].max() - Q[:, 0].min(), Q[:, 1].max() - Q[:, 1].min()) * 1.12
        cu, cv = (Q[:, 0].max() + Q[:, 0].min()) / 2, (Q[:, 1].max() + Q[:, 1].min()) / 2
        R3 = CAM.matrix_world.to_3x3()
        CAM.location = CAM.location + R3 @ Vector((cu, cv, 0))
        cam_d.ortho_scale = span
        vl.update()
        sc.render.filepath = os.path.join(A.out, f"ikona_{key}.png")
        if not A.noren:
            t = time.time()
            bpy.ops.render.render(write_still=True)
            say("icon", key, f"{time.time() - t:.0f}s")
        out[key] = dict(px_per_mm=A.res / span)
    json.dump(out, open(os.path.join(A.out, "ikony.json"), "w"), indent=1)


say("start", A.shot)
if A.shot == "rez":
    shot_rez()
elif A.shot == "rozlozene":
    shot_rozlozene()
elif A.shot == "diely":
    shot_diely()
say("done")
