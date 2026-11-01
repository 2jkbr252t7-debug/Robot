"""
NOVA Blender renderer (Cycles, CPU).  Run with:

    /opt/venv/bl/bin/python nova/render/render.py <job.json>      # or  --job '{...json...}'

Job keys (all optional except "out"):
  out        : output directory for PNGs
  parts      : list of part ids or glob patterns ("H*", "A0?-R") – default all non-internal parts
  subs       : list of subassemblies to include (base, torso, neck, head, arm_R, arm_L, internal)
  exclude    : list of ids/patterns to drop
  internal   : include internal parts (electronics) – default False
  views      : list of view names: front back right left top bottom iso iso_back hero hero2 hero_low
               or dicts {"name":..., "loc":[x,y,z] mm, "target":[x,y,z] mm, "lens":mm, "ortho":bool}
  res        : [w, h] pixels (default [1200, 1200])
  samples    : Cycles samples (default 96)
  pose       : {"J1": deg, "J2": deg, "J3": deg, "J4": deg, "J5": deg}
  explode    : factor multiplying each part's explode vector (default 0)
  explode_override : {part_id: [dx,dy,dz]}  (mm, replaces manifest vector)
  section    : {"axis": "x"|"y", "offset": mm, "keep": "pos"|"neg"} – boolean cut of all parts with cap colour
  xray       : make white/black shells semi transparent (to show internals)
  scale_fit  : "shared" (all ortho views use one scale, default) | "each"
  ortho_scale: explicit ortho scale in mm (overrides fitting)
  margin     : fractional margin around the object for ortho fit (default 0.12)
  shadow     : True -> shadow catcher on floor for side views (default True)
  transparent: film transparent (default True; compose onto background later)
  manifest_dir: default build/manifest ; glb_dir root default build
  isolate_pose_parts : ignore pose for these subs (keep local)
  write_meta : write <out>/views.json with camera matrices + pixel scale (for dimension overlays)
"""
from __future__ import annotations

import fnmatch
import glob
import json
import math
import os
import sys
import time

import bpy
import addon_utils
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from nova import spec  # noqa: E402

MM = 0.001


# ---------------------------------------------------------------------------
# scene + materials
# ---------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("cycles", default_set=True)
    addon_utils.enable("io_scene_gltf2", default_set=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 6
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.unit_settings.system = "METRIC"
    return sc


def make_material(key: str):
    m = spec.MATERIALS[key]
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    rgb = m["rgb"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = m.get("rough", 0.4)
    b.inputs["Metallic"].default_value = m.get("metallic", 0.0)
    if "clearcoat" in m:
        for nm in ("Coat Weight", "Clearcoat"):
            if nm in b.inputs:
                b.inputs[nm].default_value = m["clearcoat"]
                break
        if "Coat Roughness" in b.inputs:
            b.inputs["Coat Roughness"].default_value = 0.12
    if "spec" in m and "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = m["spec"]
    if key == "white":
        # soft subsurface feel of painted PC/ABS
        if "Subsurface Weight" in b.inputs:
            b.inputs["Subsurface Weight"].default_value = 0.04
    if key == "glass":
        b.inputs["Specular IOR Level"].default_value = 0.6 if "Specular IOR Level" in b.inputs else 0.5
        if "IOR" in b.inputs:
            b.inputs["IOR"].default_value = 1.52
    if "emit" in m:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = m["emit"]
        b.inputs["Base Color"].default_value = (*rgb, 1)
    return mat


_MATS = {}


def mat(key):
    if key not in _MATS:
        _MATS[key] = make_material(key)
    return _MATS[key]


def cap_material():
    if "section_cap" in _MATS:
        return _MATS["section_cap"]
    m = bpy.data.materials.new("section_cap")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.50, 0.09, 0.012, 1)
    b.inputs["Roughness"].default_value = 0.7
    _MATS["section_cap"] = m
    return m


def setup_world(sc, strength=1.0):
    w = bpy.data.worlds.new("studio")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    # vertical gradient: brighter above, slightly darker below -> nice reflections on glossy white
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    # dark studio below the horizon, soft bright "sky" only near the zenith -> deep black glass/bezel
    ramp.color_ramp.elements[0].position = 0.72
    ramp.color_ramp.elements[0].color = (0.035, 0.036, 0.04, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = -1
    mapr.inputs["From Max"].default_value = 1
    nt.links.new(tc.outputs["Generated"] if False else tc.outputs["Normal"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    # reflections (glossy rays) see a much darker studio -> piano-black glass and bezel like R01
    lp = nt.nodes.new("ShaderNodeLightPath")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY_ADD"
    mul.inputs[1].default_value = -0.85
    mul.inputs[2].default_value = 1.0
    nt.links.new(lp.outputs["Is Glossy Ray"], mul.inputs[0])
    strength_mul = nt.nodes.new("ShaderNodeMath")
    strength_mul.operation = "MULTIPLY"
    strength_mul.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], strength_mul.inputs[0])
    nt.links.new(strength_mul.outputs[0], bg.inputs["Strength"])
    nt.links.new(bg.outputs[0], out.inputs[0])


def add_area_light(name, loc, target, size, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, type="AREA")
    ld.size = size
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


LIGHT_RIG = {}


def place_lights_camera_relative(target, right, up, fwd, radius):
    """Re-position the 4 lights in camera space so every orthographic view is lit identically
    (key from the upper-left-front of the image, soft fill from the right, rim from behind)."""
    r = max(radius, 0.03)
    t = Vector(target)
    rel = {
        "key": (-1.5, 1.7, -2.6),   # (right, up, toward camera)
        "fill": (2.4, 0.2, -1.6),
        "rim": (0.6, 1.8, 2.6),
        "top": (0.2, 3.2, -0.6),
    }
    for name, (a, b, c) in rel.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        # fwd points from the camera to the target; c<0 = camera side, c>0 = behind the object
        loc = t + right * (a * r) + up * (b * r) + fwd * (c * r)
        ob.location = loc
        d = t - loc
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup_lights(center, radius, scale=1.0):
    """Three-point product lighting scaled to the object radius (metres)."""
    c = Vector(center)
    r = max(radius, 0.03)
    k = (r / 0.15) ** 2 * scale
    add_area_light("key", c + Vector((-1.8, -2.4, 2.2)) * r, c, 1.3 * r, 36 * k)
    add_area_light("fill", c + Vector((2.6, -1.4, 0.6)) * r, c, 3.0 * r, 4 * k)
    add_area_light("rim", c + Vector((0.8, 2.6, 2.0)) * r, c, 1.6 * r, 22 * k)
    add_area_light("top", c + Vector((0.3, 0.2, 3.4)) * r, c, 2.6 * r, 9 * k)
    for nm in ("key", "fill", "rim", "top"):
        ob = bpy.data.objects[nm]
        LIGHT_RIG[nm] = (ob.location.copy(), ob.rotation_euler.copy())


def restore_world_lights():
    for nm, (loc, rot) in LIGHT_RIG.items():
        ob = bpy.data.objects.get(nm)
        if ob:
            ob.location = loc
            ob.rotation_euler = rot


# ---------------------------------------------------------------------------
# parts
# ---------------------------------------------------------------------------

def load_manifest(manifest_dir):
    recs = []
    for fn in sorted(glob.glob(os.path.join(manifest_dir, "*.json"))):
        with open(fn) as f:
            recs.extend(json.load(f))
    return recs


def match(pid, patterns):
    return any(fnmatch.fnmatchcase(pid, p) for p in patterns)


def select_parts(recs, job):
    out = []
    for r in recs:
        if job.get("parts") and not match(r["id"], job["parts"]):
            continue
        if job.get("subs") and r["sub"] not in job["subs"]:
            continue
        if job.get("exclude") and match(r["id"], job["exclude"]):
            continue
        if r.get("internal") and not job.get("internal", False):
            continue
        out.append(r)
    return out


FIX = Matrix.Rotation(math.radians(-90), 4, "X")   # glTF import (X,-Z,Y) -> CAD (X,Y,Z)


def import_part(rec, glb_root):
    """Import the STL export (raw CAD coordinates, mm) -> metres, smooth by angle."""
    path = os.path.join(glb_root, "stl", rec["id"] + ".stl")
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path, global_scale=MM, use_mesh_validate=True)
    new = [o for o in bpy.data.objects if o not in before]
    ob = new[0]
    ob.name = rec["id"]
    me = ob.data
    # merge duplicated vertices of the triangle soup, then smooth with sharp edges by angle
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00002)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(rec.get("smooth_deg", 32)))
    except Exception:
        pass
    me.materials.clear()
    me.materials.append(mat(rec["mat"]))
    ob["sub"] = rec["sub"]
    ob["joint"] = rec.get("joint", "")
    ob["internal"] = bool(rec.get("internal", False))
    return ob


# ---------------------------------------------------------------------------
# pose / explode / section
# ---------------------------------------------------------------------------

def pivot_matrix(axis_vec, origin_mm, deg):
    o = Vector(origin_mm) * MM
    return Matrix.Translation(o) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis_vec)) @ Matrix.Translation(-o)


def joint_chain(joint):
    """Which joint transforms (outermost last) apply to a part of the given joint group."""
    chains = {
        "": [], "J0": [],
        "J1": ["J1"], "J2": ["J1", "J2"], "J3": ["J1", "J2", "J3"],
        "J4": ["J1", "J4"], "J5": ["J1", "J5"],
    }
    return chains.get(joint, [])


def apply_pose(objs, pose):
    if not pose:
        return
    ax = spec.ARM["axis"]
    defs = {
        "J1": ((0, 0, 1), (0, 0, 0)),
        "J2": ((0, 0, 1), (spec.PAN_AXIS["x"], spec.PAN_AXIS["y"], 0)),
        "J3": ((1, 0, 0), (0, spec.TILT_AXIS["y"], spec.TILT_AXIS["z"])),
        # arms: positive angle = arm swings forward/up (front is -Y)
        "J4": ((1, 0, 0), (0, ax["y"], ax["z"])),
        "J5": ((1, 0, 0), (0, ax["y"], ax["z"])),
    }
    # sign convention (user-facing degrees):
    #   J1 +  = body turns to robot's left (CCW from top)     -> +rot about Z
    #   J2 +  = head turns to robot's left                    -> +rot about Z
    #   J3 +  = head looks UP                                 -> -rot about X
    #   J4/J5 + = arm swings FORWARD/UP (front is -Y)         -> -rot about X
    sign = {"J1": 1, "J2": 1, "J3": -1, "J4": -1, "J5": -1}
    for o in objs:
        chain = joint_chain(o.get("joint", ""))
        M = Matrix.Identity(4)
        # world = P_J1 @ P_J2 @ P_J3 @ part   (innermost joint applied first)
        for j in chain:
            if pose.get(j):
                axis, org = defs[j]
                M = M @ pivot_matrix(axis, org, sign[j] * pose[j])
        o.matrix_world = M @ o.matrix_world


def apply_explode(objs, recs_by_id, factor, override):
    if not factor and not override:
        return
    for o in objs:
        v = override.get(o.name) if override else None
        if v is None:
            v = recs_by_id[o.name].get("explode", [0, 0, 0])
            v = [c * (factor or 0) for c in v]
        o.location = o.location + Vector(v) * MM


def apply_section(objs, sec):
    axis = sec.get("axis", "x").lower()
    off = sec.get("offset", 0.0) * MM
    keep = sec.get("keep", "pos")
    big = 2.0
    bpy.ops.mesh.primitive_cube_add(size=1)
    cutter = bpy.context.object
    cutter.name = "_cutter"
    cutter.scale = (big, big, big)
    idx = {"x": 0, "y": 1, "z": 2}[axis]
    loc = [0.0, 0.0, 0.0]
    # remove the half we do NOT keep
    loc[idx] = off + (big / 2 if keep == "neg" else -big / 2)
    cutter.location = loc
    cutter.data.materials.append(cap_material())
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    orig = {}
    for o in objs:
        mn, mx = world_bbox([o])
        orig[o.name] = (mn.copy(), mx.copy())
        m = o.modifiers.new("section", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = cutter
        m.solver = "EXACT"
        try:
            m.use_hole_tolerant = True
        except Exception:
            pass
        try:
            m.material_mode = "TRANSFER"
        except Exception:
            pass
    # apply modifiers so empty results can be removed
    for o in list(objs):
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier="section")
        except Exception as e:
            print("section failed", o.name, e)
        if len(o.data.polygons) == 0:
            objs.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        # recolour the cap faces: covers = orange family, internals = blue-grey family, slight per-part tint
        try:
            idx = [i for i, ms in enumerate(o.data.materials) if ms and ms.name == "section_cap"]
            if idx:
                import hashlib
                h = int(hashlib.md5(o.name.encode()).hexdigest()[:4], 16) / 65535.0
                cm = bpy.data.materials.new("cap_" + o.name)
                cm.use_nodes = True
                cb = cm.node_tree.nodes["Principled BSDF"]
                k = 0.75 + 0.5 * h
                if o.get("internal"):
                    col = (0.10 * k, 0.17 * k, 0.26 * k, 1)
                else:
                    col = (0.50 * k, 0.10 * k, 0.015 * k, 1)
                cb.inputs["Base Color"].default_value = col
                cb.inputs["Roughness"].default_value = 0.7
                for i in idx:
                    o.data.materials[i] = cm
        except Exception as e:
            print("cap recolour failed", o.name, e)
        # guard: a non-manifold input can make EXACT return the cutter itself -> drop that part
        bpy.context.view_layer.update()
        mn, mx = world_bbox([o])
        omn, omx = orig[o.name]
        if any(mn[i] < omn[i] - 0.001 or mx[i] > omx[i] + 0.001 for i in range(3)):
            print("section produced garbage for", o.name, "-> removed")
            objs.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    return objs


def apply_xray(objs, alpha=0.18):
    for o in objs:
        if o.get("internal") or o.get("sub") == "internal":
            continue
        key = o.data.materials[0].name if o.data.materials else ""
        if key.startswith("xr_"):
            continue
        base = o.data.materials[0]
        m = base.copy()
        m.name = "xr_" + base.name
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Alpha"].default_value = alpha
        for nm in ("Specular IOR Level", "Coat Weight", "Subsurface Weight"):
            if nm in b.inputs:
                b.inputs[nm].default_value = 0.0
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        o.data.materials[0] = m
        try:
            o.visible_shadow = False
        except Exception:
            pass


# ---------------------------------------------------------------------------
# cameras
# ---------------------------------------------------------------------------
VIEW_DIRS = {
    # name: (camera direction FROM target, up vector)
    "front": ((0, -1, 0), (0, 0, 1)),
    "back": ((0, 1, 0), (0, 0, 1)),
    "right": ((-1, 0, 0), (0, 0, 1)),   # robot's right side (-X)
    "left": ((1, 0, 0), (0, 0, 1)),     # robot's left side (+X)
    "top": ((0, 0, 1), (0, 1, 0)),      # front of robot at the bottom of the image
    "bottom": ((0, 0, -1), (0, 1, 0)),  # front of robot at the bottom of the image (mirrored)
    "iso": ((0.62, -0.78, 0.42), (0, 0, 1)),        # front-left (robot's left) like the target photo
    "iso_r": ((-0.62, -0.78, 0.42), (0, 0, 1)),     # front-right
    "iso_back": ((-0.65, 0.75, 0.45), (0, 0, 1)),
    "iso_back_l": ((0.65, 0.75, 0.45), (0, 0, 1)),
    "iso_low": ((0.55, -0.80, -0.35), (0, 0, 1)),
}


def look_at(cam_ob, loc, target, up=(0, 0, 1)):
    loc = Vector(loc)
    target = Vector(target)
    fwd = (target - loc).normalized()
    upv = Vector(up)
    if abs(fwd.dot(upv.normalized())) > 0.999:
        upv = Vector((0, 1, 0))
    right = fwd.cross(upv).normalized()
    true_up = right.cross(fwd).normalized()
    R = Matrix((right, true_up, -fwd)).transposed()
    cam_ob.matrix_world = Matrix.Translation(loc) @ R.to_4x4()


def world_bbox(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
            mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
    return mn, mx


def projected_extent(objs, right, up):
    """Extent of the objects' world-space vertices along camera right/up axes (metres)."""
    rs, us = [], []
    for o in objs:
        mw = o.matrix_world
        me = o.data
        n = len(me.vertices)
        step = max(1, n // 4000)
        for i in range(0, n, step):
            w = mw @ me.vertices[i].co
            rs.append(w.dot(right))
            us.append(w.dot(up))
    return min(rs), max(rs), min(us), max(us)


def cam_axes(d, up):
    fwd = -Vector(d).normalized()
    upv = Vector(up)
    if abs(fwd.dot(upv)) > 0.999:
        upv = Vector((0, 1, 0))
    right = fwd.cross(upv).normalized()
    true_up = right.cross(fwd).normalized()
    return fwd, right, true_up


def ortho_need(w_extent, h_extent, aspect):
    """Blender's ortho_scale spans the LARGER image dimension (sensor fit AUTO)."""
    if aspect >= 1.0:
        return max(w_extent, h_extent * aspect)
    return max(h_extent, w_extent / aspect)


def make_shadow_catcher(z):
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, z))
    pl = bpy.context.object
    pl.name = "_floor"
    pl.is_shadow_catcher = True
    return pl


# ---------------------------------------------------------------------------
# ID pass: flat unique colours per part -> visible-pixel anchors for callouts
# ---------------------------------------------------------------------------

def id_color(i):
    """8-bit sRGB colour for part index i (1-based), unique for i < 1000."""
    return (40 + (i % 10) * 21, 40 + ((i // 10) % 10) * 21, 40 + ((i // 100) % 10) * 21)


def srgb_to_linear(v):
    c = v / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def render_id_pass(sc, objs, path):
    saved = {o.name: [ms for ms in o.data.materials] for o in objs}
    vt, look, expo = sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure
    samples, den = sc.cycles.samples, sc.cycles.use_denoising
    fw = sc.cycles.filter_width
    world = sc.world
    hidden = []
    for ob in sc.objects:
        if ob.type == "LIGHT" or ob.name == "_floor":
            if not ob.hide_render:
                ob.hide_render = True
                hidden.append(ob)
    black = bpy.data.worlds.get("_id_black") or bpy.data.worlds.new("_id_black")
    black.use_nodes = True
    black.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    sc.world = black
    id_map = {}
    for i, o in enumerate(objs, start=1):
        c = id_color(i)
        id_map[o.name] = list(c)
        m = bpy.data.materials.get("_id_%d" % i) or bpy.data.materials.new("_id_%d" % i)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        lin = [srgb_to_linear(v) for v in c]
        em.inputs["Color"].default_value = (*lin, 1)
        em.inputs["Strength"].default_value = 1.0
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], outn.inputs[0])
        for k in range(len(o.data.materials)):
            o.data.materials[k] = m
    sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    sc.view_settings.exposure = 0.0
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.filter_width = 0.01
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # restore
    for o in objs:
        for k, ms in enumerate(saved[o.name]):
            o.data.materials[k] = ms
    for ob in hidden:
        ob.hide_render = False
    sc.world = world
    sc.view_settings.view_transform, sc.view_settings.exposure = vt, expo
    try:
        sc.view_settings.look = look
    except Exception:
        pass
    sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.filter_width = samples, den, fw
    return id_map


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run(job):
    t0 = time.time()
    sc = reset_scene()
    out = job["out"]
    os.makedirs(out, exist_ok=True)
    build_root = job.get("glb_dir", os.path.join(ROOT, "build"))
    recs = load_manifest(job.get("manifest_dir", os.path.join(build_root, "manifest")))
    sel = select_parts(recs, job)
    if not sel:
        raise SystemExit("no parts selected")
    recs_by_id = {r["id"]: r for r in sel}
    objs = [import_part(r, build_root) for r in sel]
    apply_pose(objs, job.get("pose"))
    apply_explode(objs, recs_by_id, job.get("explode", 0), job.get("explode_override"))
    if job.get("section"):
        objs = apply_section(objs, job["section"])
    if job.get("xray"):
        apply_xray(objs, job.get("xray_alpha", 0.15))
    bpy.context.view_layer.update()

    mn, mx = world_bbox(objs)
    center = (mn + mx) / 2
    if job.get("center"):
        center = Vector(job["center"]) * MM
    radius = (mx - mn).length / 2
    setup_world(sc, job.get("world", 0.5))
    setup_lights(center, radius, job.get("light", 1.0))
    sc.view_settings.exposure = job.get("exposure", -1.5)
    floor_z = job.get("floor_z")
    floor_z = (floor_z * MM) if floor_z is not None else mn.z - 0.0002
    floor = None
    if job.get("shadow", True):
        floor = make_shadow_catcher(floor_z)

    res = job.get("res", [1200, 1200])
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = job.get("samples", 96)
    sc.render.film_transparent = job.get("transparent", True)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_data.clip_start = 0.001
    cam_data.clip_end = 50

    views = job.get("views", ["front", "back", "right", "left", "top", "bottom"])
    margin = job.get("margin", 0.12)
    aspect = res[0] / res[1]

    # shared ortho scale
    ortho_views = [v for v in views if isinstance(v, str) and v in ("front", "back", "right", "left", "top", "bottom")]
    shared = None
    if job.get("ortho_scale"):
        shared = job["ortho_scale"] * MM
    elif job.get("scale_fit", "shared") == "shared" and ortho_views:
        need = 0
        for v in ortho_views:
            d, up = VIEW_DIRS[v]
            fwd, right, tup = cam_axes(d, up)
            r0, r1, u0, u1 = projected_extent(objs, right, tup)
            need = max(need, ortho_need(r1 - r0, u1 - u0, aspect))
        shared = need * (1 + 2 * margin)

    meta = {}
    for v in views:
        if isinstance(v, dict):
            name = v["name"]
            loc = Vector(v["loc"]) * MM
            tgt = Vector(v.get("target", list(center / MM))) * MM
            cam_data.type = "ORTHO" if v.get("ortho") else "PERSP"
            cam_data.lens = v.get("lens", 85)
            if v.get("ortho"):
                cam_data.ortho_scale = v.get("ortho_scale", 300) * MM
            look_at(cam, loc, tgt, v.get("up", (0, 0, 1)))
            restore_world_lights()
            if floor:
                floor.hide_render = not v.get("shadow", True)
        else:
            name = v
            d, up = VIEW_DIRS[v]
            fwd, right, tup = cam_axes(d, up)
            ortho = v in ("front", "back", "right", "left", "top", "bottom")
            if ortho:
                cam_data.type = "ORTHO"
                r0, r1, u0, u1 = projected_extent(objs, right, tup)
                cr, cu = (r0 + r1) / 2, (u0 + u1) / 2
                depth_c = center.dot(fwd)
                tgt = right * cr + tup * cu + fwd * depth_c
                if shared:
                    cam_data.ortho_scale = shared
                else:
                    cam_data.ortho_scale = ortho_need(r1 - r0, u1 - u0, aspect) * (1 + 2 * margin)
                loc = tgt - fwd * (radius * 6 + 0.5)
                look_at(cam, loc, tgt, tup)
                if job.get("cam_lights", True):
                    place_lights_camera_relative(center, right, tup, fwd, radius)
                if floor:
                    floor.hide_render = v in ("bottom", "top")
            else:
                restore_world_lights()
                cam_data.type = "PERSP"
                cam_data.lens = job.get("lens", 70)
                dist_f = job.get("dist", 1.0)
                # distance so that the object fits: use bounding sphere
                fov = 2 * math.atan(36 / 2 / cam_data.lens)
                dist = radius * (1 + margin * 2) / math.sin(fov / 2) * dist_f
                loc = center + Vector(d).normalized() * dist
                look_at(cam, loc, center, (0, 0, 1))
                if floor:
                    floor.hide_render = False
        sc.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        id_map = None
        if job.get("id_pass"):
            id_map = render_id_pass(sc, objs, os.path.join(out, f"{name}_id.png"))
        # metadata for overlays: world->pixel mapping
        meta[name] = dict(type=cam_data.type, ortho_scale_mm=cam_data.ortho_scale / MM,
                          lens=cam_data.lens, sensor=cam_data.sensor_width,
                          matrix_world=[list(r) for r in cam.matrix_world], res=res,
                          mm_per_px=(cam_data.ortho_scale / MM) / max(res) if cam_data.type == "ORTHO" else None,
                          id_map=id_map)
        print(f"rendered {name} ({time.time() - t0:.1f}s)")
    if job.get("write_meta", True):
        bb = dict(min=list(mn / MM), max=list(mx / MM))
        with open(os.path.join(out, "views.json"), "w") as f:
            json.dump(dict(views=meta, bbox_mm=bb, parts=[r["id"] for r in sel]), f, indent=1)
    print(f"done {len(views)} views in {time.time() - t0:.1f}s")


def main():
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if argv and argv[0] == "--job":
        job = json.loads(argv[1])
    else:
        with open(argv[0]) as f:
            job = json.load(f)
    run(job)


if __name__ == "__main__":
    main()
