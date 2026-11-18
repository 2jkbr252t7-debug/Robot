"""NOVA mini - animation-ready model of torso rev. 2 + neck + head (variant B E2).
Run:  /opt/venv/bl/bin/python anim/work/build_glb.py [-- --noanim]
Reads the design STLs (T4/stl, B/stl, anim/work/stl_b) - never writes there.  Writes anim/NOVA_mechanizmy.glb,
anim/kinematics.json and anim/work/build_report.json.
Frame of the STLs: B frame, mm, Z up, FRONT = -Y, rest pose (pan 0, lift 0, tilt 0, J1 0).
Scene: metres (BU = 1 m), Z up; the glTF exporter converts to Y up: (x, y, z)_B -> (x, z, -y)_glTF / 1000."""
import bpy, bmesh, sys, os, json, math, time
from mathutils import Vector, Matrix, Quaternion

T4 = "/tmp/claude-0/gapwf/fin/T4"
BST = "/tmp/claude-0/gapwf/fin/B/stl"
ANIM = os.path.join(T4, "anim")
WORK = os.path.join(ANIM, "work")
SPLIT = os.path.join(WORK, "stl_b")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NOANIM = "--noanim" in argv
SCALE = float([a.split("=")[1] for a in argv if a.startswith("--scale=")][0]) if any(a.startswith("--scale=") for a in argv) else 0.7
T0 = time.time()
MM = 0.001

sys.path.insert(0, WORK)
from kin import JOINTS, PIV, lift_from_theta, theta_from_lift, tilt_down_max, tilt_up_max, b2g   # noqa: E402

DOC = json.load(open(os.path.join(T4, "parts.json")))
REC = {r["name"]: r for r in DOC["parts"]}

# ---------------------------------------------------------------------------------------------------------- membership
OMIT = {"ffc_par": "FFC pár – slučka pan + zdvih (tvar sa mení s pan aj zdvihom)",
        "ffc_A_krk": "koniec FFC-A pri DPS_krk (súčasť pásika)", "ffc_B_krk": "koniec FFC-B pri DPS_krk (súčasť pásika)",
        "ffc_A_nosic": "koniec FFC-A pri nosnej doske (súčasť pásika)", "ffc_B_nosic": "koniec FFC-B pri nosnej doske (súčasť pásika)",
        "pigtail_zdvih": "pigtail serva zdvihu (ohybná slučka, tvar sa mení so zdvihom)",
        "lozisko_6805": "nahradené dvoma krúžkami lozisko_6805_vnutorny / _vonkajsi (vnútorný stojí s podstavcom, vonkajší sa otáča s J1)"}
CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena")
PARENT = {}
for r in DOC["parts"]:
    n, g = r["name"], r["group"]
    if n in OMIT:
        continue
    if g == "Z":
        PARENT[n] = "base_static"
    elif n == "pastorok_J1":
        PARENT[n] = "pinion_J1"
    elif n == "pastorok_pan":
        PARENT[n] = "pan_pinion"
    elif g == "T":
        PARENT[n] = "J1"
    elif n in CRANK:
        PARENT[n] = "crank"
    elif g == "P":
        PARENT[n] = "PAN"
    elif g == "L":
        PARENT[n] = "LIFT"
SRC = {n: os.path.join(T4, "stl", n + ".stl") for n in PARENT}
# B parts (variant B E2, rest pose = T4 lift 0) and split pieces
B_PARTS = {   # name: (source, parent, material, group tag, Slovak label)
    "golier_prstenec": (f"{BST}/golier_prstenec.stl", "J1", "cierna", "shell", "prstenec goliera (pevný v hornej stene trupu)"),
    "golier_kotuc": (f"{BST}/golier_kotuc.stl", "PAN", "cierna", "shell", "kotúč goliera (lepený na šachtu, otáča sa s pan)"),
    "krk_predna_polovica": (f"{BST}/krk_predna_polovica.stl", "LIFT", "cierna", "shell", "krk – predná polovica (lepená na pätku)"),
    "krk_zadna_polovica": (f"{BST}/krk_zadna_polovica.stl", "LIFT", "cierna", "shell", "krk – zadná polovica"),
    "servo_MG90S": (f"{BST}/servo_MG90S.stl", "LIFT", "servo_modra", "mechanism", "servo náklonu MG90S v krku (hriadeľ na osi závesu)"),
    "pena_serva": (f"{BST}/pena_serva.stl", "LIFT", "pena", "bought", "penové vložky serva náklonu"),
    "capy": (f"{BST}/capy.stl", "LIFT", "ocel", "mechanism", "dutý čap závesu + kolík krku"),
    "skrutky_krk": (f"{SPLIT}/skrutky__N.stl", "LIFT", "ocel", "bought", "skrutky a vložky krku (4 + 4)"),
    "kabel_krk": (f"{SPLIT}/kabel__N.stl", "LIFT", "kabel", "electronics", "vodiče v krku (hlava – pevná časť, servo náklonu)"),
    "loziska_MR85_vnutorny": (f"{SPLIT}/loziska_MR85__N.stl", "LIFT", "ocel", "mechanism", "ložisko MR85 – vnútorný krúžok (na čape krku)"),
    "hlava_skrupina": (f"{BST}/hlava_skrupina.stl", "TILT", "biela", "head", "škrupina hlavy"),
    "ram_displeja": (f"{BST}/ram_displeja.stl", "TILT", "cierna_lesk", "head", "rám displeja (čierny lesklý)"),
    "displej": (f"{BST}/displej.stl", "TILT", "sklo", "head", "displej (sklo, LCD, doska)"),
    "pena_displeja": (f"{BST}/pena_displeja.stl", "TILT", "pena", "head", "pena pod displejom"),
    "drziak_displeja": (f"{BST}/drziak_displeja.stl", "TILT", "cierna", "head", "držiak displeja (2 lišty)"),
    "magnety": (f"{BST}/magnety.stl", "TILT", "magnet", "head", "magnety rámu displeja"),
    "usi": (f"{BST}/usi.stl", "TILT", "cierna", "head", "uši hlavy"),
    "led_kruzky": (f"{BST}/led_kruzky.stl", "TILT", "svetlo", "head", "svetelné krúžky uší (LED)"),
    "led_dosky": (f"{BST}/led_dosky.stl", "TILT", "dps", "head", "LED dosky v ušiach"),
    "oci_len_vizualizacia": (f"{BST}/oci_len_vizualizacia.stl", "TILT", "oci", "head", "oči – len vizualizácia obrazu na displeji"),
    "usko_kryt": (f"{BST}/usko_kryt.stl", "TILT", "cierna", "head", "uško závesu −X s krytom páky serva"),
    "usko_lozisko": (f"{BST}/usko_lozisko.stl", "TILT", "cierna", "head", "uško závesu +X s puzdrom ložiska MR85"),
    "paka": (f"{BST}/paka.stl", "TILT", "cierna", "head", "páka serva náklonu (zaklinená v uchu −X, nesie hlavu)"),
    "klzny_kruzok": (f"{BST}/klzny_kruzok.stl", "TILT", "ptfe", "head", "klzný PTFE krúžok závesu"),
    "skrutky_hlava": (f"{SPLIT}/skrutky__H.stl", "TILT", "ocel", "head", "skrutky hlavy (páka, 4 priečne M2x8, nosič displeja)"),
    "kabel_hlava": (f"{SPLIT}/kabel__H.stl", "TILT", "kabel", "head", "vodiče hlavy (otočná časť so slučkou)"),
    "loziska_MR85_vonkajsi": (f"{SPLIT}/loziska_MR85__H.stl", "TILT", "ocel", "head", "ložisko MR85 – vonkajší krúžok (v uchu hlavy)"),
    "lozisko_6805_vnutorny": (f"{SPLIT}/lozisko_6805_vnutorny.stl", "base_static", "ocel", "mechanism",
                              "ložisko 6805 – vnútorný krúžok (na náboji podstavca, stojí)"),
    "lozisko_6805_vonkajsi": (f"{SPLIT}/lozisko_6805_vonkajsi.stl", "J1", "ocel", "mechanism",
                              "ložisko 6805 – vonkajší krúžok s tesneniami (lepený v pätke trupu, otáča sa s J1)"),
}
for n, (src, par, *_r) in B_PARTS.items():
    PARENT[n] = par; SRC[n] = src

# ---------------------------------------------------------------------------------------------------------- materials
MATDEF = {   # key: (base colour, roughness, metallic, emission colour or None)
    "biela": ((0.86, 0.86, 0.845), 0.38, 0.0, None), "cierna": ((0.022, 0.022, 0.025), 0.42, 0.0, None),
    "cierna_lesk": ((0.012, 0.012, 0.014), 0.12, 0.0, None), "sklo": ((0.010, 0.012, 0.016), 0.05, 0.0, None),
    "siva_tmava": ((0.20, 0.20, 0.21), 0.55, 0.0, None), "mosadz": ((0.80, 0.58, 0.25), 0.28, 1.0, None),
    "ocel": ((0.62, 0.63, 0.65), 0.30, 1.0, None), "hlinik": ((0.80, 0.81, 0.83), 0.36, 1.0, None),
    "magnet": ((0.66, 0.66, 0.68), 0.25, 1.0, None), "dps": ((0.03, 0.26, 0.09), 0.45, 0.0, None),
    "servo_modra": ((0.05, 0.14, 0.50), 0.40, 0.0, None), "pena": ((0.09, 0.09, 0.10), 0.90, 0.0, None),
    "kabel": ((0.45, 0.06, 0.04), 0.50, 0.0, None), "plast_biely": ((0.80, 0.78, 0.72), 0.50, 0.0, None),
    "kondenzator": ((0.05, 0.10, 0.30), 0.40, 0.0, None), "pet": ((0.72, 0.76, 0.80), 0.30, 0.0, None),
    "ptfe": ((0.93, 0.93, 0.90), 0.55, 0.0, None), "ffc": ((0.85, 0.48, 0.08), 0.35, 0.0, None),
    "svetlo": ((0.13, 0.88, 1.0), 0.30, 0.0, (0.13, 0.88, 1.0)), "oci": ((1.0, 0.86, 0.62), 0.30, 0.0, (1.0, 0.86, 0.62)),
}
MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    col, rough, metal, emi = MATDEF[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emi:
        b.inputs["Emission Color"].default_value = (*emi, 1.0)
        b.inputs["Emission Strength"].default_value = 1.0
    m.diffuse_color = (*col, 1.0)
    MATS[key] = m
    return m


def t4_mat(n, r):
    m = r.get("mat")
    if n.startswith("servo_"):
        return "servo_modra"
    return {"resin_white": "biela", "resin_black": "cierna", "resin_clear": "svetlo", "resin_grey": "siva_tmava", "brass": "mosadz",
            "steel": "ocel", "alu": "hlinik", "stainless": "ocel", "magnet": "magnet", "pcb": "dps", "ptfe": "ptfe", "fpc": "ffc"
            }.get(m) or {"reproduktor": "cierna", "tesnenie_repro": "pena", "pena_J1_celo": "pena", "vyvod_repro": "kabel",
                         "vyvod_led": "kabel", "DPS_riadenie": "dps", "menic": "dps", "zosilnovac": "dps", "kondenzator": "kondenzator",
                         "usb_predlzovac": "ffc", "konektor_zdvih": "plast_biely", "kabel_zdvih": "kabel", "podlozka_J1_1": "pet",
                         "podlozka_J1_2": "pet", "podlozka_C_J1": "pet"}.get(n, "siva_tmava")


SHELL = {"T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_klb_L", "T_klb_P", "T_svetlovod", "T_mriezka", "T_spodok"}
MECH = {"P_sachta", "P_drziak_serva", "T_paluba", "T_most", "T_cap", "koleso_pan", "pastorok_J1", "pastorok_pan", "rameno_zdvih",
        "cap_kluky", "L_ucho", "L_pata", "servo_J1", "servo_pan", "servo_zdvih", "Z_naboj_test", "Z_koleso_J1", "Z_skrutka_M8",
        "Z_pruzina_1", "Z_pruzina_2", "kolik_dorazu_1", "kolik_dorazu_2", "ptfe_podlozka", "ptfe_cap", "ptfe_pas_capu",
        "T_drziak_led", "T_drziak_repro"} | {f"ptfe_pasik_{i}" for i in range(1, 8)}
ELEC = {"DPS_riadenie", "DPS_led", "DPS_krk", "menic", "zosilnovac", "kondenzator", "reproduktor", "usb_predlzovac", "vyvod_repro",
        "vyvod_led", "konektor_zdvih", "kabel_zdvih"}


def t4_group(n):
    return "shell" if n in SHELL else "mechanism" if n in MECH else "electronics" if n in ELEC else "bought"


# decimation budget (target faces); parts not listed and <= SMALL_CAP keep everything up to SMALL_CAP
CRISP = {"pastorok_J1", "pastorok_pan", "koleso_pan", "Z_koleso_J1", "rameno_zdvih", "cap_kluky", "skr_ramena", "L_ucho", "L_pata",
         "kolik_F12", "skr_F12_1", "kolik_dorazu_1", "kolik_dorazu_2", "kolik_F10", "paka", "P_drziak_serva", "DPS_krk",
         "lozisko_6805_vnutorny", "lozisko_6805_vonkajsi", "loziska_MR85_vnutorny", "loziska_MR85_vonkajsi", "capy", "servo_zdvih",
         "servo_MG90S", "servo_pan", "servo_J1"}
BUDGET = {"T_spodok": 16000, "T_stred": 15000, "T_bok_L": 9000, "T_bok_P": 9000, "T_klb_L": 4000, "T_klb_P": 4000, "T_dvere": 3500,
          "T_cap": 2000, "P_sachta": 9000, "kabel_zdvih": 1500, "T_mriezka": 2500, "Z_naboj_test": 3000,
          "hlava_skrupina": 22000, "ram_displeja": 9000, "usi": 6000, "golier_kotuc": 7000, "golier_prstenec": 4000,
          "krk_predna_polovica": 7000, "krk_zadna_polovica": 7000, "usko_kryt": 4500, "usko_lozisko": 4500, "skrutky_hlava": 5000,
          "skrutky_krk": 2500, "kabel_hlava": 1500, "kabel_krk": 1200, "displej": 4000, "drziak_displeja": 2500, "led_kruzky": 3500,
          "magnety": 2000, "T_svetlovod": 2500, "T_paluba": 2500, "T_most": 2000, "T_drziak_repro": 2000, "T_drziak_led": 2000,
          "DPS_riadenie": 1800, "tesnenie_repro": 800, "ptfe_pas_capu": 800}
SMALL_CAP = 240
for k in list(BUDGET):
    BUDGET[k] = int(BUDGET[k] * SCALE)

# ---------------------------------------------------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; vl = bpy.context.view_layer
sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 1.0
sc.render.fps = 30
EMP = {}


def empty(name, parent, at_mm, label, extra=None):
    o = bpy.data.objects.new(name, None)
    sc.collection.objects.link(o)
    o.empty_display_type = "ARROWS"; o.empty_display_size = 0.01
    o.rotation_mode = "QUATERNION"
    if parent:
        o.parent = EMP[parent]
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.location = Vector(at_mm) * MM - Vector(PIV[parent]) * MM
    else:
        o.location = Vector(at_mm) * MM
    o["label_sk"] = label
    o["group"] = "joint" if name not in ("root", "base_static") else "frame"
    for k, v in (extra or {}).items():
        o[k] = v
    EMP[name] = o
    return o


for jn in ("root", "base_static", "J1", "pinion_J1", "pan_pinion", "PAN", "crank", "LIFT", "TILT"):
    J = JOINTS[jn]
    ex = {}
    if J.get("type"):
        ex = dict(joint_type=J["type"], axis_gltf=list(b2g(J["axis_b"], 1.0)), value_name=J["value"], value_unit=J["unit"],
                  formula=J["formula"])
    empty(jn, J["parent"], PIV[jn], J["label_sk"], ex)
vl.update()


def import_part(name):
    src = SRC[name]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.stl_import(filepath=src, global_scale=MM)
    o = bpy.context.selected_objects[0]
    o.name = name; o.data.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4 if o.scale[0] < 0.01 else 1e-7)
    bm.to_mesh(o.data); bm.free()
    # the STL importer puts global_scale into the object scale: bake it into the vertices (vertices in metres, no node scale)
    o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
    n0 = len(o.data.polygons)
    tgt = None if name in CRISP else BUDGET.get(name, SMALL_CAP)
    if tgt and n0 > tgt:
        vl.objects.active = o
        md = o.modifiers.new("dec", "DECIMATE"); md.decimate_type = "COLLAPSE"; md.ratio = tgt / n0
        md.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=md.name)
    me = o.data
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(32.0))
    return o, n0, len(me.polygons)


REPORT = {"parts": {}, "omitted": OMIT}
for name in PARENT:
    o, n0, n1 = import_part(name)
    if name in B_PARTS:
        _s, par, mk, grp, lab = B_PARTS[name]
        src_note = "B/stl" if _s.startswith(BST) else "anim/work/stl_b (split / visual)"
    else:
        r = REC[name]; par = PARENT[name]; mk = t4_mat(name, r); grp = t4_group(name); lab = r.get("label_sk", name)
        src_note = "T4/stl"
    o.data.materials.clear(); o.data.materials.append(mat(mk))
    o.parent = EMP[par]; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = -Vector(PIV[par]) * MM               # vertices are in model coordinates -> world = identity at rest
    o["label_sk"] = lab; o["group"] = grp; o["part"] = name; o["joint_node"] = par
    REPORT["parts"][name] = dict(parent=par, material=mk, group=grp, faces_src=n0, faces=n1, src=src_note)
vl.update()
print(f"[{time.time() - T0:5.1f}] imported {len(REPORT['parts'])} parts, faces {sum(p['faces'] for p in REPORT['parts'].values())}",
      flush=True)

# world-matrix sanity: every mesh must sit at identity at rest
bad = [o.name for o in sc.objects if o.type == "MESH" and (o.matrix_world - Matrix.Identity(4)).to_quaternion().angle > 1e-9
       or (o.type == "MESH" and o.matrix_world.translation.length > 1e-9)]
REPORT["rest_world_not_identity"] = bad


# ---------------------------------------------------------------------------------------------------------- animations
def set_pose(j1=0.0, pan=0.0, theta=0.0, tilt=0.0):
    """joint values -> node TRS exactly as kinematics.json prescribes (Blender Z-up frame of the same nodes)"""
    lift = lift_from_theta(theta)
    vals = {"J1": j1, "pinion_J1": j1 * JOINTS["pinion_J1"]["ratio"], "PAN": pan, "pan_pinion": pan * JOINTS["pan_pinion"]["ratio"],
            "crank": theta, "LIFT": lift, "TILT": tilt}
    for jn, v in vals.items():
        J = JOINTS[jn]; o = EMP[jn]
        ax_b = Vector(J["axis_b"])
        rest = Vector(PIV[jn]) * MM - Vector(PIV[J["parent"]]) * MM
        if J["type"] == "rotate":
            o.rotation_quaternion = Quaternion(ax_b, math.radians(v)); o.location = rest
        else:
            o.rotation_quaternion = Quaternion(); o.location = rest + ax_b * (v * MM)
    return vals


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def seg(t, pts):
    """piecewise smooth interpolation through (time, value) points"""
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0)) if t1 > t0 else v1
    return pts[-1][1] if t > pts[-1][0] else pts[0][1]


CLIPS = {   # name: (duration s, fn(t) -> (j1, pan, theta, tilt))
    "1_J1_otacanie_trupu": (8.0, lambda t: (seg(t, [(0, 0), (2, 150), (6, -150), (8, 0)]), 0, 0, 0)),
    "2_PAN_otacanie_hlavy": (8.0, lambda t: (0, seg(t, [(0, 0), (2, 85), (6, -85), (8, 0)]), 0, 0)),
    "3_ZDVIH_vysunutie_krku": (7.0, lambda t: (0, 0, seg(t, [(0, 0), (3, 180), (4, 180), (7, 0)]), 0)),
    "4_NAKLON_hlavy": (11.0, lambda t: (0, 0, seg(t, [(0, 0), (2, 180), (9, 180), (11, 0)]),
                                        seg(t, [(0, 0), (2.5, 0), (4, 40), (7, -40), (8.5, 0), (11, 0)]))),
    "5_DEMO_vsetko": (14.0, lambda t: (seg(t, [(0, 0), (7, 90), (14, 0)]), seg(t, [(0, 0), (3, 60), (7.5, -60), (11, 0), (14, 0)]),
                                       seg(t, [(0, 0), (3, 180), (10, 180), (13, 0), (14, 0)]),
                                       seg(t, [(0, 0), (3.5, 0), (5, 30), (7, -35), (9, 0), (14, 0)]))),
}
ANIM_REPORT = {}
if not NOANIM:
    fps = sc.render.fps
    for clip, (dur, fn) in CLIPS.items():
        act = bpy.data.actions.new(clip)
        nfr = int(round(dur * fps))
        worst = 0.0
        for jn in ("J1", "pinion_J1", "PAN", "pan_pinion", "crank", "LIFT", "TILT"):
            o = EMP[jn]
            if o.animation_data is None:
                o.animation_data_create()
            o.animation_data.action = act
            if o.animation_data.action_slot is None:
                slot = act.slots.new(id_type="OBJECT", name=jn)
                o.animation_data.action_slot = slot
        for f in range(nfr + 1):
            j1, pan, th, tilt = fn(f / fps)
            lift = lift_from_theta(th)
            if tilt > tilt_down_max(lift) + 1e-6 or -tilt > tilt_up_max(lift) + 1e-6:
                worst = max(worst, tilt - tilt_down_max(lift), -tilt - tilt_up_max(lift))
            set_pose(j1, pan, th, tilt)
            for jn in ("J1", "pinion_J1", "PAN", "pan_pinion", "crank", "LIFT", "TILT"):
                o = EMP[jn]
                o.keyframe_insert("rotation_quaternion", frame=f)
                o.keyframe_insert("location", frame=f)
        ANIM_REPORT[clip] = dict(frames=nfr + 1, seconds=dur, tilt_limit_violation_deg=round(worst, 4))
        for jn in ("J1", "pinion_J1", "PAN", "pan_pinion", "crank", "LIFT", "TILT"):
            o = EMP[jn]
            slot = o.animation_data.action_slot
            tr = o.animation_data.nla_tracks.new(); tr.name = clip
            st = tr.strips.new(clip, 0, act)
            try:
                st.action_slot = slot
            except Exception as e:
                print("slot assign", e)
            o.animation_data.action = None
            tr.mute = False
    set_pose()
    sc.frame_start, sc.frame_end = 0, 0
    sc.frame_set(0)
REPORT["animations"] = ANIM_REPORT
set_pose()
vl.update()

# ---------------------------------------------------------------------------------------------------------- export
root_extra = EMP["root"]
root_extra["model"] = "NOVA mini – trup rev. 2 + krk + hlava (variant B E2), animačný model"
root_extra["units"] = "meter, glTF Y up (front of the robot = +Z, robot left = +X)"
root_extra["kinematics"] = "kinematics.json (joint nodes J1, pinion_J1, pan_pinion, PAN, crank, LIFT, TILT)"
root_extra["omitted_sk"] = "; ".join(f"{k}: {v}" for k, v in OMIT.items())
out = os.path.join(ANIM, "NOVA_mechanizmy.glb")
kw = dict(filepath=out, export_format="GLB", export_yup=True, export_apply=False, export_extras=True, export_normals=True,
          export_texcoords=False, export_materials="EXPORT", export_animations=not NOANIM, export_animation_mode="ACTIONS",
          export_merge_animation="ACTION", export_force_sampling=True, export_optimize_animation_size=False,
          export_anim_slide_to_zero=False, export_nla_strips=True, export_draco_mesh_compression_enable=False)
bpy.ops.export_scene.gltf(**kw)
REPORT["glb"] = out; REPORT["glb_mb"] = round(os.path.getsize(out) / 1e6, 3)
REPORT["faces_total"] = sum(p["faces"] for p in REPORT["parts"].values())
REPORT["seconds"] = round(time.time() - T0, 1)
json.dump(REPORT, open(os.path.join(WORK, "build_report.json"), "w"), indent=1, ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "NOVA_mechanizmy_build.blend"), compress=True)
print(f"[{time.time() - T0:5.1f}] GLB {REPORT['glb_mb']} MB, faces {REPORT['faces_total']}, not identity: {bad}", flush=True)
