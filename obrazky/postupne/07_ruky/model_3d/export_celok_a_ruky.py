"""Export: whole NOVA mini exactly as in the v3 renders (GLB per arm variant) + printable look-test arm shells A/B/C.
Runs the R3 scene code (read only) without its shot dispatch."""
import sys, os, math
SRC = "/tmp/claude-0/gapwf/fin/R3/img/work/scene_v3.py"
code = open(SRC).read()
code = code[:code.index('say("start", A.shot)')]
g = {"__file__": SRC, "__name__": "scene"}
exec(compile(code, SRC, "exec"), g)
globals().update({k: v for k, v in g.items() if not k.startswith("__")})
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

OUT = os.environ.get("EXP_OUT", "/tmp/claude-0/-home-user-Robot/e2af8646-c6f1-5ece-963d-7005cfdf5589/scratchpad/exp/out")
MODE = os.environ.get("EXP_MODE", "glb")
VIDS = os.environ.get("EXP_VIDS", "A,B,C").split(",")
os.makedirs(OUT, exist_ok=True)


def scene_objs():
    return [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE") and not o.hide_render]


def export_glb(path):
    root = bpy.data.objects.new("NOVA_mini", None); bpy.context.scene.collection.objects.link(root)
    root.scale = (0.001, 0.001, 0.001); root.location = (0, 0, -Z_FLOOR * 0.001)
    objs = scene_objs()
    for o in objs:
        if o.parent is None:
            o.parent = root
    # curves (cables) are not exported as meshes by glTF -> convert
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                              export_cameras=False, export_lights=False, export_extras=False)
    for o in objs:
        o.parent = None
    bpy.data.objects.remove(root)


if MODE == "glb":
    load_t4(T_EXT); load_head(0.0); load_base()
    load_new(["zatka", "zatka_skrutky"])
    for o in list(bpy.context.scene.objects):
        if o.type == "LIGHT" or o.type == "CAMERA":
            pass
    for vid in VIDS:
        clear_arms()
        build_arms_variant(vid, True)
        vl.update()
        p = os.path.join(OUT, f"NOVA_mini_celok_ruka_{vid}.glb")
        export_glb(p)
        say("GLB", p, os.path.getsize(p) // 1024, "kB", len(scene_objs()), "objects")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NOVA_mini_celok.blend"))

elif MODE == "arms":
    WALL_OUT, WALL_IN = 1.2, 1.6

    def boolean(o, cutter, op="DIFFERENCE"):
        m = o.modifiers.new("b", "BOOLEAN"); m.object = cutter; m.operation = op; m.solver = "MANIFOLD"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name)

    def half_closed(name, vid, half):
        rows, c0, c1 = VA.half_rows(vid, half, 170, 120, 0.0)
        K, N = rows.shape[:2]
        W = VA.to_world(rows.reshape(-1, 3), vid, DX).reshape(K, N, 3)
        o = rows_solid(name, W, "biela", c_top=VA.to_world(c0, vid, DX), c_bot=VA.to_world(c1, vid, DX))
        fix_normals(o)
        return o

    def inset_pebble(name, vid, inset):
        rows, top, bot = VA.pebble_rows(vid, 170, 160, inset=inset)
        K, N = rows.shape[:2]
        W = VA.to_world(rows.reshape(-1, 3), vid, DX).reshape(K, N, 3)
        o = rows_solid(name, W, "tien", c_top=VA.to_world(top, vid, DX), c_bot=VA.to_world(bot, vid, DX))
        fix_normals(o)
        return o

    def halfspace_box(name, pt, n, size=400.0):
        bpy.ops.mesh.primitive_cube_add(size=size)
        b = bpy.context.active_object; b.name = name
        n = Vector(n).normalized()
        q = Vector((0, 0, 1)).rotation_difference(n)
        b.rotation_euler = q.to_euler()
        b.location = Vector(pt) + n * (size / 2)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return b

    def to_local_mesh(o, vid, mirror=False):
        M = o.matrix_world
        P = np.array([tuple(M @ v.co) for v in o.data.vertices])
        Q = np.asarray(VA.to_local(P, vid, DX), float)
        # upright print frame: arm top at z = 72, bottom at 0
        Q[:, 2] += VA.L
        if mirror:
            Q[:, 0] *= -1
        for v, q in zip(o.data.vertices, Q):
            v.co = Vector(q)
        o.matrix_world = Matrix.Identity(4)
        if mirror:
            bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()

    def export_stl(o, path):
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, apply_modifiers=True, ascii_format=False)

    def manifold_report(o):
        bm = bmesh.new(); bm.from_mesh(o.data)
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        vol = bm.calc_volume(signed=True); bm.free()
        return bad, vol

    import json
    rep = {}
    for vid in VIDS:
        nm = {"A": "A_mierne_stihlejsia", "B": "B_stihla", "C": "C_najstihlejsia", "0": "0_sucasna"}[vid]
        outer = half_closed("kryt", vid, "vonk")
        inner = half_closed("vnut", vid, "vnut")
        cut_o = inset_pebble("ins_o", vid, WALL_OUT); boolean(outer, cut_o); remove(cut_o)
        cut_i = inset_pebble("ins_i", vid, WALL_IN); boolean(inner, cut_i); remove(cut_i)
        hole = xcyl_obj("diera", 7.0, 44.0, 58.0); fix_normals(hole); boolean(inner, hole); remove(hole)
        ptl, ntl = VA.tip_plane_local(vid)
        pt = VA.to_world(ptl, vid, DX); nt = VA.dir_world(ntl)
        tip = copy(inner, "spicka")
        hs = halfspace_box("hs", pt, nt); boolean(tip, hs, "INTERSECT"); boolean(inner, hs, "DIFFERENCE"); remove(hs)
        for part, o in (("vonkajsi_kryt", outer), ("vnutorna_cast", inner), ("cierna_spicka", tip)):
            bad_w, vol_w = manifold_report(o)
            for side, mir in (("lava", False), ("prava", True)):
                c = copy(o, f"{part}_{side}")
                to_local_mesh(c, vid, mir)
                bad, vol = manifold_report(c)
                p = os.path.join(OUT, f"ruka_{nm}_{side}_{part}.stl")
                export_stl(c, p)
                rep[f"{vid}/{part}/{side}"] = dict(nonmanifold_edges=bad, volume_mm3=round(abs(vol), 1),
                                                   dims=[round(float(x), 2) for x in c.dimensions])
                remove(c)
            remove(o) if part != "vnutorna_cast" else None
        remove(inner)
        say("arms", vid, json.dumps({k: v for k, v in rep.items() if k.startswith(vid)}))
    json.dump(rep, open(os.path.join(OUT, "ruky_kontrola.json"), "w"), indent=1)
say("EXP done")
