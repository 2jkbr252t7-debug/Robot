"""NOVA – body after the user's sheets R05 (torso), R02/R11 (arm), R01 (whole robot) with the finished head + neck.
Procedural meshes (numpy -> Blender), real panel gaps (3-part torso: centre band + 2 side caps), Cycles renders.
Usage: /opt/venv/bl/bin/python build_scene.py --out <dir> --shots hero_r01,front,right,... [--res 900] [--samples 40]"""
import bpy, bmesh, sys, os, math, argparse
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shape as S

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--shots", default="hero_r01")
ap.add_argument("--res", type=int, default=900)
ap.add_argument("--samples", type=int, default=40)
ap.add_argument("--lift", type=float, default=12.5)
ap.add_argument("--exposure", type=float, default=0.0)
ap.add_argument("--blend", default="")
ap.add_argument("--glb", default="")
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)
TOP = S.TOP
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
GAP = 0.28                 # half seam gap
THICK = 1.6
Z_BOT = TOP - float(S.CP[-1, 0])        # underside of the black bottom cap
PLINTH = 1.5
Z_BASE_TOP = Z_BOT - PLINTH
Z_FLOOR = Z_BASE_TOP - S.BASE_H - S.FOOT_H
SH_DROP, SH_Y = 21.0, 3.0   # shoulder axis: below TOP, behind the centre (R05 side view)
AXZ = -3.5

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COL = {}
for n in ("torso", "arms", "base", "head", "neck", "stage", "cutters"):
    c = bpy.data.collections.new(n); sc.collection.children.link(c); COL[n] = c
MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    spec = {"biela": ((0.86, 0.86, 0.845), 0.30), "cierna": ((0.018, 0.018, 0.02), 0.30), "tien": ((0.006, 0.006, 0.007), 0.9),
            "lesk": ((0.010, 0.010, 0.012), 0.06), "sklo": ((0.008, 0.008, 0.01), 0.04), "siva": ((0.62, 0.62, 0.62), 0.5),
            "svetlo": ((0.13, 0.88, 1.0), 0.3), "oci": ((1.0, 0.86, 0.62), 0.3), "podlaha": ((0.78, 0.765, 0.75), 0.9)}
    c, r = spec[key]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = r
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


# ------------------------------------------------------------------------------------------------ mesh helpers
def quads(K, N, closed_n=True, closed_k=False, flip=False):
    F = []
    for k in range(K if closed_k else K - 1):
        k1 = (k + 1) % K
        for j in range(N if closed_n else N - 1):
            j1 = (j + 1) % N
            q = (k * N + j, k1 * N + j, k1 * N + j1, k * N + j1)
            F.append(q[::-1] if flip else q)
    return F


def make(name, verts, faces, key, col, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    COL[col].objects.link(ob)
    me.materials.append(mat(key))
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def rows_solid(name, rows, key, col, c_top=None, c_bot=None, flip=False):
    """closed solid from rings (K, N, 3) + fan caps to the given centre points"""
    K, N = rows.shape[:2]
    V = rows.reshape(-1, 3).tolist()
    F = quads(K, N, flip=flip)
    if c_top is not None:
        V.append(list(c_top)); c = len(V) - 1
        F += [((c, j, (j + 1) % N)[::-1] if flip else (c, j, (j + 1) % N)) for j in range(N)]
    if c_bot is not None:
        V.append(list(c_bot)); c = len(V) - 1; o = (K - 1) * N
        F += [((c, o + (j + 1) % N, o + j)[::-1] if flip else (c, o + (j + 1) % N, o + j)) for j in range(N)]
    return make(name, np.array(V), F, key, col)


def fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()


def bisect(ob, co, no, clear_outer=False, clear_inner=False):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no,
                           clear_outer=clear_outer, clear_inner=clear_inner)
    bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons:
        p.use_smooth = True


def copy(ob, name, col=None):
    o = ob.copy(); o.data = ob.data.copy(); o.name = name
    COL[col or ob.users_collection[0].name].objects.link(o)
    return o


def solidify(ob, t=THICK):
    m = ob.modifiers.new("sol", "SOLIDIFY"); m.thickness = t; m.offset = -1.0; m.use_even_offset = True; m.use_rim = True
    return m


def boolean(ob, cutter, op="DIFFERENCE"):
    m = ob.modifiers.new("bool", "BOOLEAN"); m.object = cutter; m.operation = op; m.solver = "EXACT"
    cutter.hide_render = True
    return m


def bevel(ob, w=0.30, seg=3, ang=38):
    m = ob.modifiers.new("bev", "BEVEL"); m.width = w; m.segments = seg; m.limit_method = "ANGLE"
    m.angle_limit = math.radians(ang); m.harden_normals = False
    return m


def autosmooth(ob, ang=35):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(ang))
    except Exception:
        bpy.ops.object.shade_smooth()


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


def rrect_outline(w, h, r, n=24):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-(w / 2 - r), h / 2 - r, 90), (-(w / 2 - r), -(h / 2 - r), 180),
                       (w / 2 - r, -(h / 2 - r), 270)):
        for i in range(n + 1):
            t = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return np.array(pts)


def prism_y(name, outline, x, z, y0, y1, key="tien", col="cutters"):
    """outline (N, 2) in the x-z plane extruded from y0 to y1"""
    N = len(outline)
    rows = np.array([[(x + px, y, z + pz) for px, pz in outline] for y in (y0, y1)])
    ob = rows_solid(name, rows, key, col, c_top=(x, y0, z), c_bot=(x, y1, z))
    fix_normals(ob)
    return ob


def lathe_x(name, prof, y, z, key, col, sx=1, n=96):
    """profile [(x, r), ...] revolved about the X axis through (y, z); x multiplied by sx"""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rows = np.array([[(sx * px, y + r * np.cos(t), z + r * np.sin(t)) for t in th] for px, r in prof])
    ob = rows_solid(name, rows, key, col, c_top=(sx * prof[0][0], y, z), c_bot=(sx * prof[-1][0], y, z))
    fix_normals(ob)
    return ob


def imp(fn, key, col, mw=None):
    bpy.ops.wm.stl_import(filepath=fn)
    o = bpy.context.selected_objects[0]
    for c in o.users_collection:
        c.objects.unlink(o)
    COL[col].objects.link(o)
    if mw is not None:
        o.matrix_world = mw
    o.data.materials.clear(); o.data.materials.append(mat(key))
    autosmooth(o, 40)
    return o


# ------------------------------------------------------------------------------------------------ TORSO
st_w = S.stations(0.0, S.S_WHITE)
rows_w = np.array([S.section(s) for s in st_w])
K, N = rows_w.shape[:2]
shell = make("T_shell_tmp", rows_w.reshape(-1, 3), quads(K, N), "biela", "torso")
centre = copy(shell, "T_stred"); bisect(centre, (S.XS - GAP, 0, 0), (1, 0, 0), clear_outer=True)
bisect(centre, (-(S.XS - GAP), 0, 0), (-1, 0, 0), clear_outer=True)
capL = copy(shell, "T_bok_L"); bisect(capL, (S.XS + GAP, 0, 0), (1, 0, 0), clear_inner=True)       # +X = robot LEFT
capR = copy(shell, "T_bok_P"); bisect(capR, (-(S.XS + GAP), 0, 0), (-1, 0, 0), clear_inner=True)
bpy.data.objects.remove(shell)
for o in (centre, capL, capR):
    solidify(o)
# dark body behind the seams + plug source (light bar, grille)
st_all = S.stations(0.0, S.S_END)
inner = rows_solid("T_tien", np.array([S.section(s, 1.15) for s in st_all]), "tien", "torso",
                   c_top=(0, 0, TOP - 1.15), c_bot=(0, 0, Z_BOT + 1.15))
plugsrc = rows_solid("T_plugsrc", np.array([S.section(s, 0.9) for s in st_all]), "svetlo", "cutters",
                     c_top=(0, 0, TOP - 0.9), c_bot=(0, 0, Z_BOT + 0.9))
BAR = (31.0, 4.2, 36.5)            # width, height, drop (R05: 0.32 W wide at 43 % of the height)
SLOT = (21.0, 3.2, 52.0)           # grille slot (R05: 0.21 W at 61 %)
for nm, (w, h, drop), key in (("svetlo", BAR, "svetlo"), ("mriezka", SLOT, "siva")):
    yf = S.y_front(0.0, drop)
    cut = prism_y(f"cut_{nm}", pill_outline(w, h), 0, TOP - drop, yf - 20, yf + 3.2)
    boolean(centre, cut)
    plug = copy(plugsrc, f"T_{nm}", "torso"); plug.data.materials.clear(); plug.data.materials.append(mat(key))
    pc = prism_y(f"cutp_{nm}", pill_outline(w - 0.5, h - 0.5), 0, TOP - drop, yf - 20, yf + 6.0)
    boolean(plug, pc, "INTERSECT"); plug.hide_render = False
# back service door (R05 ZOZADU): rounded-rectangle seam on the back of the centre band
DOOR = (56.0, 60.0, 10.0, 46.0)     # w, h, corner r, centre drop
N_D = len(rrect_outline(1, 1, 0.2))
o_out, o_in = rrect_outline(DOOR[0] + 0.5, DOOR[1] + 0.5, DOOR[2] + 0.25), rrect_outline(DOOR[0], DOOR[1], DOOR[2])
ring_rows = np.array([[(px, y, TOP - DOOR[3] + pz) for px, pz in o] for o, y in ((o_out, 20), (o_out, 60), (o_in, 60), (o_in, 20))])
door = make("cut_dvere", ring_rows.reshape(-1, 3), quads(4, len(o_out), closed_k=True), "tien", "cutters")
fix_normals(door)
boolean(centre, door)
# shoulder sockets + joints (R05: black stepped cylinders, flange D25 at ~27 % of the height)
drop_s = SH_DROP
_, a_sh, b_sh, n_sh = S.prof(S.s_of_drop(drop_s))
x_sh = a_sh * (1 - (abs(SH_Y) / b_sh) ** n_sh) ** (1 / n_sh)
ZS = TOP - drop_s
for sx, cap in ((1, capL), (-1, capR)):
    cut = lathe_x(f"cut_rameno_{sx}", [(x_sh - 14, 14.0), (x_sh + 14, 14.0)], SH_Y, ZS, "tien", "cutters", sx)
    boolean(cap, cut)
    J = [(x_sh - 9.0, 13.5), (x_sh + 3.4, 13.5), (x_sh + 4.2, 12.7), (x_sh + 4.2, 11.4), (x_sh + 4.8, 11.0),
         (x_sh + 11.2, 11.0), (x_sh + 12.0, 10.2), (x_sh + 12.0, 0.01)]
    j = lathe_x(f"T_klb_{sx}", J, SH_Y, ZS, "cierna", "torso", sx)
    bevel(j, 0.35, 3, 30); autosmooth(j, 35)
for o in (centre, capL, capR):
    bevel(o); autosmooth(o)
# black bottom cap (R05: the round continues in black) + plinth ring (J1 gap)
s_b0 = S.S_WHITE + 0.12
st_b = S.stations(s_b0, S.S_END, ds=0.5)
rows_b = np.array([S.section(s) for s in st_b])
bot = rows_solid("T_spodok", rows_b, "cierna", "torso", c_bot=(0, 0, Z_BOT))
solidify(bot, 1.4); bevel(bot, 0.25, 2); autosmooth(bot)
th = np.linspace(0, 2 * np.pi, 128, endpoint=False)
pl = rows_solid("T_plint", np.array([[(24.0 * np.cos(t), 24.0 * np.sin(t), z) for t in th] for z in (Z_BOT + 0.6, Z_BASE_TOP - 0.2)]),
                "cierna", "torso", c_top=(0, 0, Z_BOT + 0.6), c_bot=(0, 0, Z_BASE_TOP - 0.2))
fix_normals(pl); autosmooth(pl)
# finished collar parts (static ring in the torso; disc turns with the neck but is drawn at pan 0)
imp(os.path.join(B_STL, "golier_prstenec.stl"), "cierna", "torso")
imp(os.path.join(B_STL, "golier_kotuc.stl"), "cierna", "torso")

# ------------------------------------------------------------------------------------------------ ARMS (R02 / R11)
SPLAY, SWING = 12.0, 3.0
u_att = 0.22
_, ht_att = S.arm_profile(u_att)
A_loc = np.array([-float(ht_att) + 5.0, 0.0, -S.ARM_L * u_att])


def arm_xf(P, sx):
    """arm-local points -> world (left arm built at +X, the right arm mirrored)"""
    q = np.asarray(P, float) - A_loc
    a, b = math.radians(-SPLAY), math.radians(-SWING)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    q = q @ Ry.T @ Rx.T
    q = q + np.array([x_sh + 9.0, SH_Y, ZS])
    q[..., 0] *= sx
    return q


for sx in (1, -1):
    rows, ct, cb = S.arm_points()
    Kr, Nr = rows.shape[:2]
    W = arm_xf(rows.reshape(-1, 3), sx).reshape(Kr, Nr, 3)
    flip = sx < 0
    full = rows_solid(f"A_tmp_{sx}", W, "biela", "arms", c_top=arm_xf(ct, sx), c_bot=arm_xf(cb, sx), flip=flip)
    # split plane = local x = 0 (the pebble's equator seam, R02)
    p0 = arm_xf(np.array([0.0, 0, -S.ARM_L / 2]), sx)
    nx = arm_xf(np.array([1.0, 0, -S.ARM_L / 2]), sx) - p0
    nx = Vector(nx).normalized()
    outer = copy(full, f"A_vonk_{sx}"); bisect(outer, Vector(p0) + nx * GAP, nx, clear_inner=True)
    innerh = copy(full, f"A_vnut_{sx}"); bisect(innerh, Vector(p0) - nx * GAP, nx, clear_outer=True)
    # black tip insert (R02 / R11 item 03): lower inner-front part of the inner half
    pt = arm_xf(np.array([0.0, 0.0, -S.ARM_L * 0.86]), sx)
    nt = Vector(arm_xf(np.array([-0.50, -0.35, -S.ARM_L * 0.86 - 0.79]), sx) - pt).normalized()
    tip = copy(innerh, f"A_spicka_{sx}"); bisect(tip, Vector(pt) + nt * GAP, nt, clear_inner=True)
    bisect(innerh, Vector(pt) - nt * GAP, nt, clear_outer=True)
    tip.data.materials.clear(); tip.data.materials.append(mat("cierna"))
    bpy.data.objects.remove(full)
    for o in (outer, innerh, tip):
        solidify(o, 1.4); bevel(o, 0.28, 3); autosmooth(o)
    rin, cti, cbi = S.arm_points(inset=1.0)
    core = rows_solid(f"A_tien_{sx}", arm_xf(rin.reshape(-1, 3), sx).reshape(rin.shape), "tien", "arms",
                      c_top=arm_xf(cti, sx), c_bot=arm_xf(cbi, sx), flip=flip)

# ------------------------------------------------------------------------------------------------ BASE (R01)
be, bz = S.base_stations()
rows_base = np.array([np.column_stack([S.base_section(e), np.full(480, Z_BASE_TOP - z)]) for e, z in zip(be, bz)])
base = rows_solid("Z_podstavec", rows_base, "biela", "base", c_top=(0, 0, Z_BASE_TOP), c_bot=(0, 0, Z_BASE_TOP - S.BASE_H))
BBAR = (36.0, 3.4, 15.5)
yb = -S.BASE_D / 2
boolean(base, prism_y("cut_zsvetlo", pill_outline(BBAR[0], BBAR[1]), 0, Z_BASE_TOP - BBAR[2], yb - 10, yb + 1.0))
bevel(base, 0.25, 2, 50); autosmooth(base)
prism_y("Z_svetlo", pill_outline(BBAR[0] - 0.4, BBAR[1] - 0.4), 0, Z_BASE_TOP - BBAR[2], yb + 0.8, yb + 4.0, "svetlo", "base")
foot_o = S.base_section(7.5)
foot = rows_solid("Z_patka", np.array([np.column_stack([foot_o, np.full(480, z)]) for z in (Z_BASE_TOP - S.BASE_H + 1.0, Z_FLOOR)]),
                  "cierna", "base", c_top=(0, 0, Z_BASE_TOP - S.BASE_H + 1.0), c_bot=(0, 0, Z_FLOOR))
fix_normals(foot); autosmooth(foot)

# ------------------------------------------------------------------------------------------------ HEAD + NECK (finished)
lift = Matrix.Translation((0, 0, A.lift))
for n, k in {"hlava_skrupina": "biela", "ram_displeja": "lesk", "displej": "sklo", "oci_len_vizualizacia": "oci",
             "usi": "cierna", "led_kruzky": "svetlo", "usko_kryt": "cierna", "usko_lozisko": "cierna"}.items():
    imp(os.path.join(B_STL, n + ".stl"), k, "head", lift)
for n in ("krk_predna_polovica", "krk_zadna_polovica"):
    imp(os.path.join(B_STL, n + ".stl"), "cierna", "neck", lift)

# ------------------------------------------------------------------------------------------------ stage, lights, render
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = A.exposure
sc.render.film_transparent = True
COL["cutters"].hide_render = True
W_ = bpy.data.worlds.new("w"); sc.world = W_; W_.use_nodes = True
W_.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.56, 1)
W_.node_tree.nodes["Background"].inputs[1].default_value = 0.22
bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, Z_FLOOR))
floor = bpy.context.active_object
for c in floor.users_collection:
    c.objects.unlink(floor)
COL["stage"].objects.link(floor); floor.data.materials.append(mat("podlaha")); floor.is_shadow_catcher = True


def area(loc, tgt, energy, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.active_object
    L.data.energy, L.data.size, L.data.color = energy, size, color
    L.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return L


CTR = (0, 0, (Z_FLOOR + 90) / 2)
area((-380, -520, 430), CTR, 3.4e6, 520, (1.0, 0.985, 0.96))     # key: front-left, high
area((560, -330, 180), CTR, 1.5e6, 620, (0.96, 0.98, 1.0))       # fill: front-right, low
area((60, 120, 760), CTR, 1.9e6, 700)                            # top
area((330, 520, 330), CTR, 1.8e6, 420)                            # rim from behind
cam_d = bpy.data.cameras.new("cam"); cam_d.clip_start = 5; cam_d.clip_end = 1e5
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
ALL = ("torso", "arms", "base", "head", "neck")
# name: (visible collections, direction to camera, ortho?, target z mode, lens, ortho scale, aspect h/w, up)
SHOTS = {
    "hero_r01": (ALL, (0.22, -1.0, 0.20), False, "full", 150, None, 1.38, None),
    "hero_torso": (("torso", "head", "neck"), (0.22, -1.0, 0.20), False, "torso", 150, None, 1.25, None),
    "back34": (ALL, (-0.55, 1.0, 0.25), False, "full", 150, None, 1.38, None),
    "front_full": (ALL, (0, -1, 0), True, "full", 0, 250, 1.30, None),
    "side_full": (ALL, (1, 0, 0), True, "full", 0, 250, 1.30, None),
    "front": (("torso", "head", "neck"), (0, -1, 0), True, "torso", 0, 215, 1.30, None),
    "back": (("torso", "head", "neck"), (0, 1, 0), True, "torso", 0, 215, 1.30, None),
    "right": (("torso", "head", "neck"), (-1, 0, 0), True, "torso", 0, 215, 1.30, None),
    "left": (("torso", "head", "neck"), (1, 0, 0), True, "torso", 0, 215, 1.30, None),
    "t_front": (("torso", "neck"), (0, -1, 0), True, "tonly", 0, 150, 0.842, None),
    "t_back": (("torso", "neck"), (0, 1, 0), True, "tonly", 0, 150, 0.842, None),
    "t_right": (("torso", "neck"), (-1, 0, 0), True, "tonly", 0, 150, 0.842, None),
    "t_left": (("torso", "neck"), (1, 0, 0), True, "tonly", 0, 150, 0.842, None),
    "t_top": (("torso", "neck"), (0, -0.30, 1), True, "tonly", 0, 150, 0.842, None),
    "t_34": (("torso", "neck"), (0.5, -1.0, 0.35), False, "tonly", 150, None, 0.95, None),
}
for name in A.shots.split(","):
    vis, d, ortho, mode, lens, oscale, asp, _ = SHOTS[name]
    for k in ALL:
        COL[k].hide_render = k not in vis
    zf = Z_FLOOR if "base" in vis else Z_BASE_TOP
    floor.location.z = zf
    ztop = 86 + A.lift if "head" in vis else TOP + 12
    tgt = Vector((0, 0, (zf + ztop) / 2))
    dv = Vector(d).normalized()
    cam.location = tgt + dv * 1500
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = A.res; sc.render.resolution_y = int(A.res * asp)
    if ortho:
        cam_d.type = "ORTHO"; cam_d.ortho_scale = oscale
    else:
        cam_d.type = "PERSP"; cam_d.lens = lens
        span = (ztop - zf) * (1.16 if mode != "tonly" else 1.9)
        cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
        dist = span * lens / 24
        cam.location = tgt + dv * dist
    sc.render.filepath = os.path.join(A.out, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)
if A.blend:
    bpy.ops.wm.save_as_mainfile(filepath=A.blend)
print("DONE z_floor", Z_FLOOR, "total height rest", 86 - Z_FLOOR)
