"""r01: Blender (Cycles CPU) renders of P_sachta for the lens-B report.  Run:
    /opt/venv/bl/bin/python r01_render.py <view> [samples]
views: zdola (bottom view, ortho), rez_x0 (section x = 0, x <= 0 half kept, seen from +X),
       rez_roh (section through the slim corner: vertical plane through the axis at az 22.04 deg).
Writes r01_<view>_raw.png (transparent) + r01_<view>_anchors.json (pixel positions of named world points)."""
import sys, os, json, math
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

OUT = "/tmp/claude-0/gapwf/fin/T4/sachta_b"
STL = "/tmp/claude-0/gapwf/fin/T4/stl"
view = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else "zdola")
samples = int(sys.argv[2]) if len(sys.argv) > 2 and "--" not in sys.argv else 24
RES = (1200, 1000)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.film_transparent = True
sc.view_settings.view_transform = "AgX"
sc.view_settings.exposure = -0.4
sc.render.threads_mode = "FIXED"; sc.render.threads = 3


def mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = dict(well=mat("well", (0.50, 0.52, 0.56), 0.55), cut=mat("cut", (0.95, 0.33, 0.12), 0.6),
         brass=mat("brass", (0.80, 0.58, 0.22), 0.35, 1.0), alu=mat("alu", (0.78, 0.80, 0.83), 0.35, 1.0),
         steel=mat("steel", (0.35, 0.36, 0.38), 0.3, 1.0), ptfe=mat("ptfe", (0.97, 0.97, 0.95), 0.6),
         cap=mat("capm", (0.18, 0.18, 0.2), 0.5), cutm=mat("cutm", (0.95, 0.75, 0.15), 0.6))
CAPM = dict(brass=mat("c_brass", (0.93, 0.72, 0.20), 0.8), alu=mat("c_alu", (0.55, 0.70, 0.88), 0.8),
            steel=mat("c_steel", (0.12, 0.12, 0.14), 0.8), ptfe=mat("c_ptfe", (0.98, 0.98, 0.98), 0.8),
            cap=mat("c_cap", (0.30, 0.22, 0.45), 0.8))


def load(name, material):
    bpy.ops.wm.stl_import(filepath=f"{STL}/{name}.stl")
    ob = bpy.context.selected_objects[0]; ob.name = name
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(ob.data); bm.free()
    ob.data.materials.clear(); ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def cut_half(ob, plane_co, plane_no, cap_mat):
    """remove the half-space on the +plane_no side with an EXACT boolean; the cap faces get cap_mat"""
    n = Vector(plane_no).normalized()
    bpy.ops.mesh.primitive_cube_add(size=400.0)
    c = bpy.context.active_object; c.name = "cutter_" + ob.name
    c.data.materials.append(cap_mat)
    rot = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
    c.matrix_world = Matrix.Translation(Vector(plane_co) + n * 200.0) @ rot
    mod = ob.modifiers.new("cut", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.solver = "EXACT"; mod.object = c
    try:
        mod.material_mode = "TRANSFER"
    except Exception:
        pass
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(c, do_unlink=True)


def look_at(cam, loc, target, up):
    loc, target, up = Vector(loc), Vector(target), Vector(up)
    f = (target - loc).normalized(); r = f.cross(up).normalized(); u = r.cross(f)
    R = Matrix(((r.x, u.x, -f.x), (r.y, u.y, -f.y), (r.z, u.z, -f.z)))
    cam.matrix_world = Matrix.Translation(loc) @ R.to_4x4()


ctx = ["koleso_pan", "T_cap", "ptfe_cap", "pd_F15", "skr_F15", "T_most", "ptfe_podlozka", "L_pata"]
cmat = dict(koleso_pan="brass", T_cap="cap", ptfe_cap="ptfe", pd_F15="steel", skr_F15="steel", T_most="alu", ptfe_podlozka="ptfe",
            L_pata="alu")
W = load("P_sachta", M["well"])
obs = [W]
anchors = {}
if view == "zdola":
    cam_loc, cam_tgt, cam_up, oscale = (28, -40, -200), (0, -4.0, -24), (0, 1, 0), 76.0
    T = load("T_cap", M["cap"]); obs.append(T)
    pts = dict(hub_front=(0, -9.5, -41.9), hub_back_floor=(-3, 9.0, -41.9), hub_bore=(0, -6.5, -41.9), shroud=(16.1 * math.cos(math.radians(70)), 16.1 * math.sin(math.radians(70)), -45.6),
               shroud_end=(15.8, 2.3, -45.6), lip=(17.1 * math.cos(math.radians(100)), 17.1 * math.sin(math.radians(100)), -42.5),
               groove=(20.5, 5.25, -41.6), front_wall=(-15, -11.8, -40.9), back_wall=(18, 12.0, -41.9), end_wall=(-24.3, 0, -40.9),
               corner=(24.6, 9.9, -41.9), corner2=(-24.6, -9.9, -40.9), pad_A=(7.0, 14.5, -15.8), rail=(5.0, 14.0, -41.9),
               win_back=(-13.7, 12.0, -40.65), win_end=(24.3, -2.0, -40.9), junction=(5.5, -11.6, -41.9), tcap=(0, 0, -46.2),
               floor_open=(-14, 3.0, -41.0), journal=(0, -26.4, -6.0))
elif view in ("rez_x0", "rez_x0_full"):
    if view == "rez_x0":
        cam_loc, cam_tgt, cam_up, oscale = (200, 2.6, -36.6), (0, 2.6, -36.6), (0, 0, 1), 38.0
    else:
        cam_loc, cam_tgt, cam_up, oscale = (200, 0, -24), (0, 0, -24), (0, 0, 1), 64.0
    for n in ctx:
        obs.append(load(n, M[cmat[n]]))
    for ob in obs:
        cut_half(ob, (0, 0, 0), (1, 0, 0), M["cut"] if ob is W else CAPM[cmat[ob.name]])
    pts = dict(hub_front=(0, -9.5, -41.3), hub_back=(0, 9.5, -41.3), floor_back=(0, 11.8, -41.3), front_wall=(0, -11.8, -25), back_wall=(0, 12.0, -22),
               rail=(0, 14.0, -35.0), groove=(0, 14.4, -37.9), shroud=(0, 16.1, -44.5), lip=(0, 17.1, -42.2), top_plate=(0, -18, -2.75),
               ring=(0, -25.4, -6.0), rib=(0, 18.0, -7.0), gear=(0, -13.0, -43.9), bond=(0, -9.5, -41.9), tcap=(0, -3.0, -44.0),
               ptfe_tape=(0, 3.92, -43.5), washer=(0, 4.2, -41.4), screw_head=(0, 1.5, -40.2), thread=(0, 1.2, -46.6), most=(0, -10.0, -47.2),
               ptfe_w=(0, 8.0, -46.05), foot=(0, -8.0, -38.5), rest_gap=(0, -8.0, -40.575), junction=(0, -11.8, -41.3), pad=(0, 14.0, -33.3))
elif view == "rez_roh":
    az = math.radians(22.04)
    u = Vector((math.cos(az), math.sin(az), 0)); nrm = Vector((-math.sin(az), math.cos(az), 0))
    cam_loc = tuple(-nrm * 200 + Vector((0, 0, -24.5)) + u * 11.0); cam_tgt = (u.x * 11, u.y * 11, -24.5); cam_up, oscale = (0, 0, 1), 54.0
    RES = (1200, 1200); sc.render.resolution_x, sc.render.resolution_y = RES
    for n in ("koleso_pan", "T_cap", "ptfe_cap", "pd_F15", "skr_F15", "T_most", "ptfe_podlozka"):
        obs.append(load(n, M[cmat[n]]))
    for ob in obs:
        cut_half(ob, (0, 0, 0), tuple(-nrm), M["cut"] if ob is W else CAPM[cmat[ob.name]])
    P = lambda r, z: (u.x * r, u.y * r, z)
    pts = dict(corner_band=P(25.76, -6.0), corner_low=P(25.83, -25.0), corner_bot=P(25.83, -39.5), ring_in=P(24.37, -6.0), plate=P(15.0, -2.75),
               floor=P(13.0, -41.3), groove=P(17.7, -41.1), floor_edge=P(22.0, -41.3), hub=P(9.5, -41.3), shroud=P(16.1, -44.5), gear=P(12.0, -43.9),
               tcap=P(-3.0, -44.0), screw=P(0.0, -44.0), journal=P(26.43, -9.0), win_end=P(25.0, -20.0), most=P(-8.0, -47.2))
else:
    raise SystemExit("unknown view " + view)

# camera + camera-relative lights
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = oscale; cd.clip_end = 2000.0
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
look_at(cam, cam_loc, cam_tgt, cam_up)
Rc = cam.matrix_world.to_3x3()
for (dx, dy, e, name) in ((-0.6, 0.8, 4.0, "key"), (0.9, 0.2, 1.6, "fill"), (0.1, -0.9, 1.0, "rim")):
    ld = bpy.data.lights.new(name, "SUN"); ld.energy = e; ld.angle = math.radians(8)
    lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo)
    d = (Rc @ Vector((dx, dy, 1.0))).normalized()            # light coming from the camera side, offset
    lo.matrix_world = Vector((0, 0, 0)).to_track_quat("Z", "Y").to_matrix().to_4x4()
    lo.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
wd = bpy.data.worlds.new("w"); sc.world = wd; wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

sc.render.filepath = f"{OUT}/r01_{view}_raw.png"
bpy.ops.render.render(write_still=True)
for k, p in pts.items():
    c = world_to_camera_view(sc, cam, Vector(p))
    anchors[k] = (round(c.x * RES[0], 1), round((1 - c.y) * RES[1], 1))
# scale: px per mm
anchors["_px_per_mm"] = RES[0] / oscale
json.dump(anchors, open(f"{OUT}/r01_{view}_anchors.json", "w"), indent=1)
print("done", view)
