"""NOVA mini - R3 slim-arm comparison renders (copy of R3/tvar/scene_tvar.py = v2_scene.py + variant arms).
Reads T4 / B / T3 / img_v1 / img_v2 / R2c img (B1+ torso side) / R3 tvar + mech (never writes there).
Usage: /opt/venv/bl/bin/python scene_v3.py -- --shot front|hero|armfront|armonly|rezv --vids 0,A,B,C --res 700 --samples 16 --out DIR
  rezv: one variant (--vids X) with one joint option (--opt M1|M2b), --plane v (y = 3, seen from the front) or h (z = -17, from above)
Writes DIR/<shot>_<vid>.png (transparent film) + DIR/<shot>_cam.json (camera)."""
import bpy, bmesh, sys, os, json, math, argparse, time
import numpy as np
from mathutils import Vector, Matrix

HERE = "/tmp/claude-0/gapwf/fin/R1/img_v2/work"          # READ ONLY source of the v2 scene data / STLs
TV = "/tmp/claude-0/gapwf/fin/R3/tvar"                   # READ ONLY: variants.py (shape module)
WK = os.path.dirname(os.path.abspath(__file__))           # R3/img/work
MECH = "/tmp/claude-0/gapwf/fin/R3/mech/stl"              # READ ONLY: joint option meshes
STB = "/tmp/claude-0/gapwf/fin/R2c/img/work/stl_b"        # READ ONLY: B1+ torso-side meshes (plug body, column, A1)
sys.path.insert(0, TV)
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import variants as VA
import g2 as G
V = G.V
S = V.S
T4 = "/tmp/claude-0/gapwf/fin/T4"
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
V1ST = "/tmp/claude-0/gapwf/fin/R1/img_v1/work/stl"
ST = os.path.join(HERE, "stl")
MOD = os.path.join(HERE, "stl_mod")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", default="front")
ap.add_argument("--res", type=int, default=700)
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--out", default=os.path.join(WK, "prev"))
ap.add_argument("--opt", default="M2b")
ap.add_argument("--plane", default="v")
ap.add_argument("--wall_out", type=float, default=1.2)
ap.add_argument("--wall_in", type=float, default=1.6)
ap.add_argument("--ppm", type=float, default=20.0)
ap.add_argument("--vids", default="0,A,B,C")
ap.add_argument("--tgt", default="62,0,-5")
ap.add_argument("--scale", type=float, default=20.0)
ap.add_argument("--dir", default="0,-1,0")
ap.add_argument("--raise_deg", type=float, default=90.0)
ap.add_argument("--exposure", type=float, default=-0.3)
ap.add_argument("--noren", action="store_true")
ap.add_argument("--ghost", type=float, default=-57.0)
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)
T0 = time.time()
DOC = json.load(open(os.path.join(T4, "parts.json")))
REC = {r["name"]: r for r in DOC["parts"]}
DATA = json.load(open(os.path.join(HERE, "v2_data.json")))
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
    "zivica_siva": ((0.30, 0.31, 0.33), 0.40, 0.0),
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
    raise SystemExit("R3/tvar: prep disabled (would write into img_v2/stl_mod)")
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
    "stlp": ("cierna", "S"), "tyce": ("ocel", "S"), "vlozky": ("mosadz", "S"), "vlozka_F3a": ("mosadz", "S"), "koliky": ("ocel", "S"),
    "poron": ("pena", "S"),
    "servo_telo": ("servo", "S"), "servo_hriadel": ("mosadz", "S"),
    "spojka_paka": ("cierna", "V"), "spojka_puzdro": ("mosadz", "V"), "spojka_skrutka": ("ocel_cierna", "V"),
    "hriadel_zvisly": ("ocel", "V"), "B1": ("ocel", "S"), "B1_tesnenie": ("tesnenie", "S"), "podlozka_B1": ("ocel", "V"),
    "pastorok": ("mosadz", "V"),
    "koleso": ("mosadz", "A"), "podlozka_A1": ("ocel", "A"), "hriadel_ruky": ("ocel", "A"), "poistka": ("ocel_cierna", "A"),
    "A1": ("ocel", "P"), "A1_tesnenie": ("tesnenie", "P"), "A2": ("ocel", "P"), "A2_tesnenie": ("tesnenie", "P"),
    "zatka": ("cierna", "P"), "zatka_skrutky": ("ocel_cierna", "P"), "doraz_kolik": ("ocel", "P"),
    "L6700": ("ocel", "P"), "L6700_tesnenie": ("tesnenie", "P"),
    "podlozka_1": ("ocel", "A"), "priruba": ("mosadz", "R"), "podlozka_2": ("ocel", "A"), "pruzina": ("ocel", "A"),
    "podlozka_3": ("ocel", "A"), "skrutka_ruky": ("ocel", "A"),
}
SIDE = {1: {}, -1: {}}


def load_new(names=None, sides=(1, -1)):
    for n, (k, g) in NEW.items():
        if names is not None and n not in names:
            continue
        o = imp(os.path.join(ST, n + ".stl"), n + "_L", k, sm=True, ang=32)
        SIDE[1][n] = o
        if -1 in sides:
            SIDE[-1][n] = mirror_copy(o, n + "_P")
        if 1 not in sides:
            o.hide_render = True
    if -1 in sides and (names is None or "stena_P" in names):
        SIDE[-1]["stena"] = imp(os.path.join(ST, "stena_P.stl"), "stena_P", "cierna")
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
        bisect(hub, p0 - nx * V.SEAM, nx, clear_outer=True, fill=True)
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
    for n in ("hriadel_ruky", "koleso", "podlozka_A1", "poistka", "podlozka_1", "priruba", "podlozka_2", "pruzina", "podlozka_3",
              "skrutka_ruky"):
        o = SIDE[side].get(n)
        if o is not None:
            o.matrix_world = M4(Mw)
    vl.update()




# ------------------------------------------------------------------------------------------------ R3: slim variants
ARM_OBJS = []


def _pw(P, vid, dx, local):
    P = np.asarray(P, float)
    return P.copy() if local else VA.to_world(P, vid, dx)


def _dw(v, local):
    return np.asarray(v, float) if local else VA.dir_world(v)


def half_solid(name, vid, half, key, dx, local=False, open_seam=False):
    """closed half solid of a variant (rows = dome arcs closed by the seam chord).  open_seam: the faces lying on the flat
    seam face are deleted after the normals are made consistent (outward), leaving an open dome for solidify"""
    rows, c0, c1 = VA.half_rows(vid, half, 170, 120, VA.SEAM)
    K, N = rows.shape[:2]
    W = _pw(rows.reshape(-1, 3), vid, dx, local).reshape(K, N, 3)
    ob = rows_solid(name, W, key, c_top=_pw(c0, vid, dx, local), c_bot=_pw(c1, vid, dx, local))
    if open_seam:
        Q = (K - 1) * N
        kill = set([k * N + N - 1 for k in range(K - 1)] + [Q + N - 1, Q + N + N - 1])
        bm = bmesh.new(); bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sorted(kill)], context="FACES")
        bm.to_mesh(ob.data); bm.free()
        for p_ in ob.data.polygons:
            p_.use_smooth = True
    return ob


def full_pebble(name, vid, dx, local=False, key="tien"):
    rows, top, bot = VA.pebble_rows(vid, 150, 200)
    K, N = rows.shape[:2]
    W = _pw(rows.reshape(-1, 3), vid, dx, local).reshape(K, N, 3)
    return rows_solid(name, W, key, c_top=_pw(top, vid, dx, local), c_bot=_pw(bot, vid, dx, local))


def build_arm_variant(vid, dx=DX, local=False):
    pre = "A_"
    outer = half_solid(pre + "vonk", vid, "vonk", "biela", dx, local)
    inner = half_solid(pre + "vnut", vid, "vnut", "biela", dx, local)
    ptl, ntl = VA.tip_plane_local(vid)
    pt = _pw(ptl, vid, dx, local); nt = _dw(ntl, local)
    tip = copy(inner, pre + "spicka")
    bisect(tip, pt + nt * VA.SEAM, nt, clear_inner=True, fill=True)
    bisect(inner, pt - nt * VA.SEAM, nt, clear_outer=True, fill=True)
    tip.data.materials.clear(); tip.data.materials.append(mat("cierna"))
    out = dict(vonk=outer, vnut=inner, spicka=tip)
    for o in out.values():
        fix_normals(o); bevel(o, 0.3, 3, 40); smooth(o, 40)
    # dark core (stands for the internal seam lip / hub): only visible through the 0.5 seam, so the seam reads as a
    # dark line instead of a see-through slot
    rows, top, bot = VA.pebble_rows(vid, 120, 160, inset=0.7)
    K, N = rows.shape[:2]
    Wc = _pw(rows.reshape(-1, 3), vid, dx, local).reshape(K, N, 3)
    out["jadro"] = rows_solid(pre + "jadro", Wc, "tien", c_top=_pw(top, vid, dx, local), c_bot=_pw(bot, vid, dx, local))
    return out


def build_arms_variant(vid, right=True):
    Lp = build_arm_variant(vid, DX)
    arms = {1: Lp}
    if right:
        arms[-1] = {k: mirror_copy(o, o.name.replace("A_", "AP_")) for k, o in Lp.items()}
    for d in arms.values():
        ARM_OBJS.extend(d.values())
    return arms


def clear_arms():
    for o in list(ARM_OBJS):
        try:
            remove(o)
        except Exception:
            pass
    ARM_OBJS.clear()


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
    if dv.z > 0.99:            # straight down: image right = +X, image up = +Y (back), front at the bottom
        CAM.rotation_euler = (0.0, 0.0, 0.0)
    else:
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
        "svetlo": (0.5, 0.8, 0.9), "siva": (0.7, 0.7, 0.7), "plast_biely": (0.85, 0.83, 0.76)}
CAPN = {"zatka_L": (0.20, 0.32, 0.58), "stlp_L": (0.30, 0.44, 0.66), "T_spodok": (0.42, 0.54, 0.70), "T_paluba": (0.46, 0.56, 0.70),
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
        keep = o.data.copy()
        boolean(o, cut, "INTERSECT")
        if len(o.data.polygons) == 0:                              # exact solver gave up (self-intersecting shell): FAST
            o.data = keep
            m = o.modifiers.new("bool", "BOOLEAN"); m.object = cut; m.operation = "INTERSECT"; m.solver = "FLOAT"
            try:
                m.material_mode = "TRANSFER"
            except Exception:
                pass
            apply_mods(o)
            say("  FAST fallback", o.name, len(o.data.polygons))
        cm = cap_mat(o.name, CAPN.get(o.name, CAPC.get(key, (0.6, 0.6, 0.6))))
        for j, ms in enumerate(o.data.materials):
            if ms and ms.name == capm.name:
                o.data.materials[j] = cm
        if len(o.data.polygons) == 0:
            o.hide_render = True
        if time.time() - t > 3:
            say("  cut", o.name, f"{time.time() - t:.1f}s")
    vl.update()


# ================================================================================================ shots
def shot_front():
    load_t4(T_EXT); load_head(0.0); load_base()
    load_new(["zatka", "zatka_skrutky"])
    dv = (0, -1, 0)
    rig_follow_camera(dv)
    zc = (Z_FLOOR + 86.0) / 2
    W, H = A.res, int(A.res * 1.12)
    cam_ortho((0, 0, zc), dv, 250.0, (W, H))
    save_cam("front")
    for vid in A.vids.split(","):
        clear_arms()
        build_arms_variant(vid, True)
        vl.update()
        render("front_" + vid)


def shot_rez():
    names = [r["name"] for r in DOC["parts"] if r["bbox"][1] > 18 and r["bbox"][3] > 3.0 and r["bbox"][5] > -86 and r["group"] in "TPL"]
    load_t4(names)
    load_new(sides=(1,))
    arms = build_arms(False, internals=True)
    vl.update()
    objs = [o for o in sc.objects if o.type == "MESH"]
    crop = (18.0, 84.0, -84.0, 3.0)
    section_y(objs, G.YA, crop)
    dv = (0, -1, 0)
    rig_follow_camera(dv, (50, 0, -40))
    x0, x1, z0, z1 = crop
    W = A.res; H = int(W * (z1 - z0) / (x1 - x0))
    cam_ortho(((x0 + x1) / 2, 0, (z0 + z1) / 2), dv, x1 - x0, (W, H))
    save_cam("rez", dict(crop=crop))
    render("rez")


def ghost_sweep(deg):
    """lift servo + its holder at the pan angle closest to the left column (translucent)"""
    out = []
    Rz = Matrix.Rotation(math.radians(deg), 4, "Z")
    for n in ("servo_zdvih", "P_drziak_serva", "rameno_zdvih"):
        o = imp(os.path.join(T4, "stl", n + ".stl"), "duch_" + n, "duch", Rz)
        o.visible_shadow = False
        out.append(o)
    return out


def closest_pan():
    o = imp(os.path.join(T4, "stl", "servo_zdvih.stl"), "_probe", "ocel", sm=False)
    P = world_verts(o); remove(o)
    best = None
    for d in np.arange(-90.0, 90.01, 1.0):
        c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
        X = P[:, 0] * c - P[:, 1] * s
        Y = P[:, 0] * s + P[:, 1] * c
        m = (Y > -21) & (Y < 16)
        if m.any():
            v = X[m].max()
            if best is None or v > best[1]:
                best = (float(d), float(v))
    say("closest pan", best)
    return best


def shot_vnutro():
    keepT = ["T_spodok", "T_paluba", "T_most", "T_cap", "T_bok_P", "T_dvere", "servo_J1", "pastorok_J1", "lozisko_6805", "servo_pan",
             "pastorok_pan", "ptfe_podlozka", "ptfe_cap", "kolik_dorazu_1", "kolik_dorazu_2", "DPS_riadenie", "usb_predlzovac",
             "kondenzator", "menic", "T_stred"]
    names = [r["name"] for r in DOC["parts"] if r["name"] in keepT or r["group"] in ("P", "L") or
             (r["name"].startswith(("skr_F", "pd_F", "vl_F", "podlozka_J1", "podlozka_C", "pena_J1", "ffc_A_nosic", "ffc_B_nosic", "skr_F15", "pd_F15")))]
    objs = load_t4(names)
    load_new()
    arms = build_arms(True, internals=True)
    for o in arms[1].values():
        o.hide_render = True
    for n in ("L6700", "L6700_tesnenie", "podlozka_1", "priruba", "podlozka_2", "pruzina", "podlozka_3", "skrutka_ruky"):
        SIDE[1][n].hide_render = True
    # T_stred: keep only the back part (y > 8); T_bok_P: keep the back half too
    for n, y0 in (("T_stred", 8.0), ("T_bok_P", 3.0), ("T_dvere", -100.0)):
        o = OBJ.get(n)
        if o is None:
            continue
        if y0 > -99:
            bpy.ops.mesh.primitive_cube_add(size=1)
            cut = bpy.context.active_object; cut.name = "_c_" + n
            cut.scale = (300, 300, 300); cut.location = (0, y0 + 150.0, -40.0)
            cut.data.materials.append(cap_mat("rezbiela", (0.93, 0.70, 0.42)))
            cut.hide_render = True
            boolean(o, cut, "INTERSECT")
    best = closest_pan()
    gh = ghost_sweep(best[0])
    vl.update()
    dv = Vector((1.0, -0.72, 0.50)).normalized()
    rig_follow_camera(dv, (20, 0, -40))
    W, H = A.res, int(A.res * 0.80)
    cam_persp(Vector((18.0, -2.0, -40.0)), dv, 70, 600, (W, H))
    vis = [OBJ[n] for n in ("T_spodok", "T_bok_P", "T_dvere", "P_sachta") if n in OBJ] + [SIDE[1]["zatka"], SIDE[1]["stlp"]]
    fit_persp(vis, 0.035)
    L = SIDE[1]
    gv = np.concatenate([world_verts(o) for o in gh])
    gm = gv[gv[:, 2] > -30.0]
    gt = gm[np.argmax(gm[:, 0])] + np.array([-3.0, 0.0, 0.0])
    anc = {"sachta": vis_anchor([OBJ["P_sachta"]], (8.0, -26.0, -25.0)),
           "duch": vis_anchor(gh, gt, pix=(960.0, 560.0)),
           "servo_pan": vis_anchor([OBJ["servo_pan"]], (0.0, -27.0, -60.0)),
           "servo_J1": vis_anchor([OBJ["servo_J1"]], (0.0, -12.3, -70.0)),
           "dps": vis_anchor([OBJ["DPS_riadenie"]], (-10.0, 16.5, -60.0)),
           "bokP": vis_anchor([arms[-1]["vonk"], arms[-1]["vnut"]], (-60.0, -10.0, -30.0), pix=(300.0, 420.0)),
           "menic": vis_anchor([OBJ["menic"]], (35.0, -10.4, -72.0)),
           "servo": vis_anchor([L["servo_telo"]], (45.05, -8.0, -55.0)),
           "noha": vis_anchor([L["stlp"]], (41.5, -18.0, -66.0)),
           "vzpera": vis_anchor([L["stlp"]], (38.4, -16.0, -34.0)),
           "boss": vis_anchor([L["stlp"]], (38.0, -20.0, -47.0)),
           "zatka": vis_anchor([L["zatka"]], (46.0, 12.0, -10.0)),
           "kruzok": vis_anchor([L["zatka"]], (52.0, -3.5, -17.0)),
           "spojka": vis_anchor([L["spojka_puzdro"], L["hriadel_zvisly"]], (42.0, 1.0, -38.0)),
           "paluba": vis_anchor([OBJ["T_paluba"]], (10.0, -17.0, -43.0))}
    save_cam("vnutro", dict(pan_ghost=best, anchors=anc))
    render("vnutro")


def shot_rozlozene():
    load_new(sides=(1,))
    arms = build_arms(False, internals=True)
    L = arms[1]
    Sd = SIDE[1]
    OFF = {  # (dx, dz) per part (world mm)
        "servo_telo": (15, -50), "servo_hriadel": (15, -50), "spojka_paka": (15, -33), "spojka_puzdro": (15, -33), "spojka_skrutka": (15, -33),
        "hriadel_zvisly": (15, -18), "B1": (0, 0), "B1_tesnenie": (0, 0), "podlozka_B1": (0, 0), "pastorok": (0, 0),
        "koleso": (31, -27), "podlozka_A1": (31, -27), "hriadel_ruky": (31, -27),
        "A1": (18, 0), "A1_tesnenie": (18, 0), "zatka": (30, 0), "zatka_skrutky": (30, 0),
        "doraz_kolik": (30, 0), "A2": (44, 0), "A2_tesnenie": (44, 0), "poistka": (50, 0),
        "L6700": (62, 0), "L6700_tesnenie": (62, 0), "podlozka_1": (70, 0), "priruba": (82, 0), "podlozka_2": (100, 0),
        "pruzina": (104, 0), "podlozka_3": (108, 0), "skrutka_ruky": (114, 0),
    }
    ARM = {"vnut": 82, "naboj": 82, "stl_vnu": 82, "mag_vnu": 82, "spicka": 82, "mag_von": 126, "vonk": 132, "stl_von": 132}
    for n, (dxo, dzo) in OFF.items():
        o = Sd.get(n)
        if o is not None:
            o.location = (dxo, 0, dzo)
    for c in Sd["kabel"]:
        c.location = (15, 0, -50)
    for n in ("poron",):
        Sd[n].hide_render = True
    for k, d in ARM.items():
        if k in L:
            L[k].location = (d, 0, 0)
    vl.update()
    dv = Vector((0.50, -1.0, 0.48)).normalized()
    rig_follow_camera(dv, (100, 0, -30))
    W, H = A.res, int(A.res * 0.62)
    cam_persp(Vector((100.0, 0.0, -35.0)), dv, 80, 700, (W, H))
    vis = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and o != FLOOR]
    fit_persp(vis, 0.03)

    def A_(n, t):
        o = Sd.get(n) or L.get(n)
        d = OFF.get(n, (ARM.get(n, 0), 0))
        return vis_anchor([o], (t[0] + d[0], t[1], t[2] + d[1]))
    anc = {"stlp": A_("stlp", (36.4, -20.0, -55.0)), "pastorok": A_("pastorok", (38.0, -1.0, -21.0)),
           "hriadel_zvisly": A_("hriadel_zvisly", (39.0, 1.5, -33.0)), "spojka": A_("spojka_puzdro", (39.0, 0.0, -40.0)),
           "servo": A_("servo_telo", (39.0, -14.3, -56.0)), "koleso": A_("koleso", (42.0, 3.0, -23.0)),
           "A1": A_("A1", (45.8, -0.5, -17.0)), "zatka": A_("zatka", (44.0, -6.0, -6.0)), "A2": A_("A2", (49.8, -0.5, -17.0)),
           "poistka": A_("poistka", (51.4, -0.6, -17.0)), "L6700": A_("L6700", (55.5, -4.5, -17.0)),
           "podlozka_1": A_("podlozka_1", (57.9, 0.0, -17.0)), "vnut": A_("vnut", (56.0, -14.0, -40.0)),
           "podlozka_2": A_("podlozka_2", (59.5, -0.6, -17.0)), "pruzina": A_("pruzina", (60.0, -1.0, -17.0)),
           "podlozka_3": A_("podlozka_3", (60.5, -0.4, -17.0)), "skrutka_ruky": A_("skrutka_ruky", (61.4, 1.1, -17.0)),
           "mag_von": A_("mag_von", (66.0, -12.0, -12.0)), "vonk": A_("vonk", (72.0, -14.0, -40.0))}
    save_cam("rozlozene", dict(off={k: list(v) for k, v in OFF.items()}, arm=ARM, anchors=anc))
    render("rozlozene")


def shot_detail():
    load_t4(["T_stred", "T_bok_L", "T_spodok", "T_svetlovod"]); load_head(0.0)
    load_new(["zatka", "zatka_skrutky"], sides=(1,))
    arms = build_arms(False, internals=False)
    vl.update()
    dv = (0, -1, 0)
    rig_follow_camera(dv)
    cam_ortho((48.0, 0, -17.0), dv, 44.0, (A.res, A.res))
    save_cam("detail")
    render("detail")


def shot_hero():
    load_t4(T_EXT); load_head(20.0); load_base()
    load_new(["zatka", "zatka_skrutky"])
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
    save_cam("hero")
    for vid in A.vids.split(","):
        clear_arms()
        arms = build_arms_variant(vid, True)
        pose_arm(arms[1], A.raise_deg, 1)
        vl.update()
        render("hero_" + vid)


def shot_heroarm():
    """hero camera direction, framed on the raised left arm + shoulder"""
    load_t4(T_EXT); load_head(20.0); load_base()
    load_new(["zatka", "zatka_skrutky"])
    floor(True)
    dv = Vector((0.95, -0.80, 0.30)).normalized()
    lens = 120
    tgt = Vector((52.0, -22.0, -22.0))
    span = 105.0
    W, H = A.res, int(A.res * 0.85)
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = W, H
    CAM.location = tgt + dv * (span * lens / 24 * 0.85)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()
    save_cam("heroarm")
    for vid in A.vids.split(","):
        clear_arms()
        arms = build_arms_variant(vid, True)
        pose_arm(arms[1], A.raise_deg, 1)
        vl.update()
        render("heroarm_" + vid)


def shot_zoom():
    load_t4(["T_stred", "T_bok_L", "T_spodok"]); load_head(0.0, head=False)
    load_new(["zatka", "zatka_skrutky"], sides=(1,))
    dv = tuple(float(v) for v in A.dir.split(","))
    rig_follow_camera(dv)
    cam_ortho(tuple(float(v) for v in A.tgt.split(",")), dv, A.scale, (A.res, A.res))
    for vid in A.vids.split(","):
        clear_arms()
        build_arms_variant(vid, False)
        vl.update()
        render("zoom_" + vid)


def shot_armfront():
    """front ortho close-up of the left shoulder + arm (all variants, same camera)"""
    load_t4(["T_stred", "T_bok_L", "T_spodok", "T_svetlovod", "T_dvere", "T_mriezka"]); load_head(0.0, head=False)
    load_new(["zatka", "zatka_skrutky"], sides=(1,))
    dv = (0, -1, 0)
    rig_follow_camera(dv)
    cam_ortho((57.0, 0, -36.0), dv, 64.0, (A.res, int(A.res * 1.25)))
    save_cam("armfront")
    for vid in A.vids.split(","):
        clear_arms()
        build_arms_variant(vid, False)
        vl.update()
        render("armfront_" + vid)


def shot_side():
    """robot seen from its left side (+X), arms at rest - shows the outer cover face"""
    load_t4(T_EXT); load_head(0.0); load_base()
    load_new(["zatka", "zatka_skrutky"])
    dv = (1, 0, 0)
    rig_follow_camera(dv)
    zc = (Z_FLOOR + 86.0) / 2
    W, H = A.res, int(A.res * 1.12)
    cam_ortho((0, 0, zc), dv, 250.0, (W, H))
    for vid in A.vids.split(","):
        clear_arms()
        build_arms_variant(vid, True)
        vl.update()
        render("side_" + vid)


def shot_top():
    load_t4(T_EXT); load_head(0.0, head=False, neck=True); load_base()
    load_new(["zatka", "zatka_skrutky"])
    dv = (0, -0.0001, 1)
    rig_follow_camera(dv)
    W, H = A.res, A.res
    cam_ortho((0, 0, 0), dv, 190.0, (W, H))
    for vid in A.vids.split(","):
        clear_arms()
        build_arms_variant(vid, True)
        vl.update()
        render("top_" + vid)


# ================================================================================================ R3 shots
def xcyl_key(name, r0, r1, x0, x1, key, y=G.YA, z=G.ZA, n=96):
    """solid (r0 = 0) or tube (r0 > 0) || X about the shoulder axis"""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    if r0 <= 0:
        rows = np.array([[(x, y + r1 * math.cos(t), z + r1 * math.sin(t)) for t in th] for x in (x0, x1)])
        return rows_solid(name, rows, key, c_top=(x0, y, z), c_bot=(x1, y, z))
    V_ = []
    for x in (x0, x1):
        for r in (r1, r0):
            V_ += [(x, y + r * math.cos(t), z + r * math.sin(t)) for t in th]
    V_ = np.array(V_)
    F = []
    def ring(a, b, flip=False):
        for j in range(n):
            j1 = (j + 1) % n
            f = (a * n + j, b * n + j, b * n + j1, a * n + j1)
            F.append(f[::-1] if flip else f)
    ring(0, 2); ring(1, 3, True); ring(0, 1, True); ring(2, 3)
    ob = make(name, V_, F, key)
    fix_normals(ob)
    return ob


def section_box(objs, lo, hi, plane=None):
    """keep the part of every object inside the box lo..hi (the section plane is one face of the box); the cut faces get
    the per-part cap colour"""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    bpy.ops.mesh.primitive_cube_add(size=1)
    cut = bpy.context.active_object; cut.name = "_rez"
    cut.scale = tuple(hi - lo); cut.location = tuple((hi + lo) / 2)
    capm = cap_mat("tmp", (1, 0, 1)); cut.data.materials.append(capm)
    cut.hide_render = True
    for o in objs:
        if o.type != "MESH" or o == cut or o.hide_render:
            continue
        apply_mods(o)
        P = world_verts(o)
        if len(P) == 0 or (P.max(0) < lo).any() or (P.min(0) > hi).any():
            o.hide_render = True
            continue
        key = o.data.materials[0].name if o.data.materials else "ocel"
        if (P.min(0) > lo).all() and (P.max(0) < hi).all():
            continue
        t = time.time()
        keep = o.data.copy()
        boolean(o, cut, "INTERSECT")
        if len(o.data.polygons) == 0:                              # exact solver gave up (self-intersecting shell): FAST
            o.data = keep
            m = o.modifiers.new("bool", "BOOLEAN"); m.object = cut; m.operation = "INTERSECT"; m.solver = "FLOAT"
            try:
                m.material_mode = "TRANSFER"
            except Exception:
                pass
            apply_mods(o)
            say("  FAST fallback", o.name, len(o.data.polygons))
        cm = cap_mat(o.name, CAPN.get(o.name, CAPC.get(key, (0.6, 0.6, 0.6))))
        for j, ms in enumerate(o.data.materials):
            if ms and ms.name == capm.name:
                o.data.materials[j] = cm
        if plane is not None and len(o.data.polygons):             # faces on the section plane = cap (FAST fallback too)
            ax, val = plane
            if cm.name not in [m_.name for m_ in o.data.materials if m_]:
                o.data.materials.append(cm)
            ci = [m_.name if m_ else "" for m_ in o.data.materials].index(cm.name)
            Mw = np.array(o.matrix_world)
            for pg in o.data.polygons:
                cw = Mw[:3, :3] @ np.array(pg.center) + Mw[:3, 3]
                nw = Mw[:3, :3] @ np.array(pg.normal)
                if abs(cw[ax] - val) < 2e-3 and abs(nw[ax]) > 0.98 * np.linalg.norm(nw):
                    pg.material_index = ci
        if len(o.data.polygons) == 0:
            o.hide_render = True
        if os.environ.get("DBG"):
            say("  cut", o.name, len(P), "->", len(o.data.polygons))
        if time.time() - t > 3:
            say("  cut", o.name, f"{time.time() - t:.1f}s")
    vl.update()


X_PLUG = 46.756 - 1.0
COLMAP = {"black": "cierna", "white": "biela", "grey": "zivica_siva", "steel": "ocel", "magnet": "magnet"}
REZ_CROP = {"v": (44.0, 79.0, -41.0, 3.0), "h": (44.0, 79.0, -16.0, 22.0)}


def shot_rezv():
    vid = A.vids.split(",")[0]
    opt, pl, dx = A.opt, A.plane, DX
    CAPC["magnet"] = (0.86, 0.40, 0.42)
    CAPC["zivica_siva"] = (0.45, 0.68, 0.52)
    for n in ("ARM_naboj", "ARM_rebro"):
        CAPN[n] = (0.92, 0.60, 0.28)
    for n in ("TB_zatka", "PLG_kruzok", "PLG_cap", "PLG_doraz"):
        CAPN[n] = (0.20, 0.32, 0.58)
    CAPN["TB_stlp"] = (0.30, 0.44, 0.66)
    CAPN["A_spicka"] = (0.30, 0.36, 0.46)
    # ---- torso side (B1+ column / plug body / A1 from the R2c img meshes; side cover = img_v2 modified T_bok_L)
    load_t4(["T_bok_L"])
    for n, k in (("stlp", "cierna"), ("zatka", "cierna"), ("A1", "ocel")):
        imp(os.path.join(STB, n + ".stl"), "TB_" + n, k, sm=True, ang=32)
    bpy.ops.mesh.primitive_cube_add(size=1)
    cz = bpy.context.active_object; cz.name = "_cz"; cz.scale = (60.0, 80.0, 80.0); cz.location = (X_PLUG + 30.0, 3.0, -17.0)
    boolean(OBJ["TB_zatka"], cz, "DIFFERENCE"); remove(cz)     # plug body inside the torso only (ring/seat = option parts)
    say("zatka body", len(OBJ["TB_zatka"].data.polygons), world_verts(OBJ["TB_zatka"]).max(0).round(2))
    # ---- joint option parts
    idx = json.load(open(os.path.join(MECH, "index.json")))["options"][opt]
    for n, rec in idx.items():
        imp(os.path.join(MECH, opt, n + ".stl"), n, COLMAP[rec["color"]], sm=True, ang=32)
    tipx = {"M1": 40.0, "M2b": 38.9}.get(opt, 40.0)
    xcyl_key("M4_driek", 0, 2.0, tipx, 52.5, "ocel")
    for n in [k for k in idx if k.startswith("DRV_magnet")]:      # pockets for the magnets (avoid coplanar caps)
        boolean(OBJ["DRV_unasac"], OBJ[n], "DIFFERENCE")
    a2 = [k for k in idx if k.startswith("BRG_A2")][0]
    xcyl_key("puzdro", 2.55, 3.5, 47.06, idx[a2]["bbox"][0] - 0.02, "zivica_siva")
    # ---- arm shells (open domes, solidified inwards; cover wall_out, inner half wall_in), black tip, hole r 7, hub
    so = half_solid("A_vonk", vid, "vonk", "biela", dx, open_seam=True)
    si = half_solid("A_vnut", vid, "vnut", "biela", dx, open_seam=True)
    ptl, ntl = VA.tip_plane_local(vid)
    pt = VA.to_world(ptl, vid, dx); nt = VA.dir_world(ntl)
    tp = copy(si, "A_spicka")
    bisect(tp, pt + nt * VA.SEAM, nt, clear_inner=True)
    bisect(si, pt - nt * VA.SEAM, nt, clear_outer=True)
    tp.data.materials.clear(); tp.data.materials.append(mat("cierna"))
    solidify(so, A.wall_out); solidify(si, A.wall_in); solidify(tp, A.wall_in)
    # where a joint part pokes through the cover (variant C) show the part, not two overlapping caps
    for n in [k for k in idx if k.startswith(("DRV_unasac", "M4_"))]:
        keep = so.data.copy(); npre = len(so.data.polygons)
        boolean(so, OBJ[n], "DIFFERENCE")
        if len(so.data.polygons) == 0:
            so.data = keep
        say("cover minus", n, npre, "->", len(so.data.polygons))
    hole = xcyl_key("cut_otvor", 0, 7.0, 44.0, 56.0, "tien")
    boolean(si, hole); remove(hole)
    full = full_pebble("_plny", vid, dx)
    for n in ("ARM_naboj", "ARM_rebro"):
        if n in OBJ:
            boolean(OBJ[n], full, "INTERSECT")
            npre = len(si.data.polygons)
            boolean(si, OBJ[n], "UNION")                          # the printed hub is part of A_vnut
            say("union", n, npre, "->", len(si.data.polygons))
            remove(OBJ[n])
    remove(full)
    vl.update()
    objs = [o for o in sc.objects if o.type == "MESH"]
    c = REZ_CROP[pl]
    if pl == "v":
        x0, x1, z0, z1 = c
        section_box(objs, (x0, G.YA, z0), (x1, 500.0, z1), (1, G.YA))
        dv = (0, -1, 0)
        tgt = ((x0 + x1) / 2, 0.0, (z0 + z1) / 2)
        res = (int(round((x1 - x0) * A.ppm)), int(round((z1 - z0) * A.ppm)))
    else:
        x0, x1, y0, y1 = c
        section_box(objs, (x0, y0, -500.0), (x1, y1, G.ZA), (2, G.ZA))
        dv = (0, -1e-4, 1)
        tgt = ((x0 + x1) / 2, (y0 + y1) / 2, 0.0)
        res = (int(round((x1 - x0) * A.ppm)), int(round((y1 - y0) * A.ppm)))
    rig_follow_camera(dv, (60.0, 3.0, -17.0))
    cam_ortho(tgt, dv, x1 - x0, res)
    name = f"rez{pl}_{vid}_{opt}"
    save_cam(name, dict(crop=list(c), plane=pl, vid=vid, opt=opt, wall_out=A.wall_out, wall_in=A.wall_in))
    if os.environ.get("DBG"):
        for o in sc.objects:
            if o.type == "MESH" and ("magnet" in o.name or "unasac" in o.name):
                say("DBG", o.name, o.hide_render, len(o.data.polygons), [m.name if m else None for m in o.data.materials])
    render(name)


def shot_armonly():
    """the single left arm of each variant in its LOCAL frame (upright, no splay): front (from -y) and top (from +z)"""
    first = True
    for vid in A.vids.split(","):
        clear_arms()
        d = build_arm_variant(vid, DX, local=True)
        ARM_OBJS.extend(d.values())
        vl.update()
        for view, dv, tgt, span in (("armF", (0, -1, 0), (0.0, 0.0, -36.0), 88.0), ("armT", (0, -1e-4, 1), (0.0, 0.0, 0.0), 40.0)):
            rig_follow_camera(dv, (0.0, 0.0, -36.0))
            cam_ortho(tgt, dv, 44.0, (int(44 * A.ppm), int(span * A.ppm)))
            if first:
                save_cam(view)
            render(f"{view}_{vid}")
        first = False



say("start", A.shot)
if A.shot == "prep":
    prep()
elif A.shot == "front":
    shot_front()
elif A.shot == "rez":
    shot_rez()
elif A.shot == "vnutro":
    shot_vnutro()
elif A.shot == "rozlozene":
    shot_rozlozene()
elif A.shot == "hero":
    shot_hero()
elif A.shot == "heroarm":
    shot_heroarm()
elif A.shot == "zoom":
    shot_zoom()
elif A.shot == "armfront":
    shot_armfront()
elif A.shot == "side":
    shot_side()
elif A.shot == "top":
    shot_top()
elif A.shot == "rezv":
    shot_rezv()
elif A.shot == "armonly":
    shot_armonly()
elif A.shot == "detail":
    shot_detail()
say("done")
