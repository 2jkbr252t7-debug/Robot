"""R4/klb: preview renders of the shoulder-joint variants (Blender).  Runs R3/img/work/scene_v3.py (read only) without its
shot dispatch and reuses its scene / material / camera functions; arm = variant "B" of R3/tvar/variants.py.
usage: /opt/venv/bl/bin/python -B scene_klb.py -- --res 500 --samples 16 --out prev [--exposure -0.3]
env:   KLB_SHOTS=front,p34,p34r   KLB_VIDS=K0,K1,K2,K3   KLB_RAISE=90
Writes <out>/<shot>_<vid>.png (transparent film) + <out>/<shot>_cam.json."""
import sys, os, math, json
SRC = "/tmp/claude-0/gapwf/fin/R3/img/work/scene_v3.py"
code = open(SRC).read()
code = code[:code.index('say("start", A.shot)')]
g = {"__file__": SRC, "__name__": "scene"}
exec(compile(code, SRC, "exec"), g)
globals().update({k: v for k, v in g.items() if not k.startswith("__")})
import bpy
import numpy as np
from mathutils import Vector, Matrix

KD = "/tmp/claude-0/gapwf/fin/R4/klb"
sys.path.insert(0, KD)
import klb as KL

SHOTS = os.environ.get("KLB_SHOTS", "front,p34,p34r").split(",")
VIDS_R = os.environ.get("KLB_VIDS", "K0,K1,K2,K3").split(",")
RAISE = float(os.environ.get("KLB_RAISE", "90"))
ARM_VID = os.environ.get("KLB_ARM", "B")
HEAD_PAN = float(os.environ.get("KLB_PAN", "20"))

# ------------------------------------------------------------------ static scene (torso exterior, head, neck, no plug)
load_t4(T_EXT)
load_head(HEAD_PAN)
if os.environ.get("KLB_BASE", "0") == "1":
    load_base()
VAR_OBJS = []


def build_variant(vid):
    """arm B (left) at the variant's dx + the variant's joint parts; returns the dict of rotating objects"""
    for o in list(VAR_OBJS):
        try:
            remove(o)
        except Exception:
            pass
    VAR_OBJS.clear()
    v = KL.variant(vid)
    arm = build_arm_variant(ARM_VID, KL.arm_dx(vid))
    VAR_OBJS.extend(arm.values())
    rot = dict(arm)
    for p in v["parts"]:
        o = imp(p["stl"], p["id"] + "_L", p["mat"], sm=True, ang=30)
        VAR_OBJS.append(o)
        if p["role"] == "rotating":
            rot[p["id"]] = o
    # dark filler inside the bore of a collar / ring: the real arm is hollow there (closed render solid would show white)
    rp = [p for p in v["parts"] if p["role"] == "rotating"]
    if rp:
        prof = [q for q in KL.VARIANTS[vid]["parts"] if q["role"] == "rotating"][0]["profile"]()
        x_end = float(prof[:, 0].min()); r_in = float(prof[prof[:, 0] < x_end + 0.01][:, 1].min())
        sh = KL.arm_dx(vid) - KL.DX0
        f = xcyl_key("_bore_" + vid, 0, r_in - 0.05, x_end + 1.6, 54.0 + sh, "tien")
        VAR_OBJS.append(f); rot["_bore"] = f
    vl.update()
    return rot


def pose(rot, deg):
    Mw = M4(KL.swing_matrix(deg))
    for o in rot.values():
        o.matrix_world = Mw
    vl.update()


def cam_p34(tgt, dv, span, res, lens=120.0):
    dv = Vector(dv).normalized()
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = res
    CAM.location = Vector(tgt) + dv * (span * lens / 24)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()


R = A.res
for shot in SHOTS:
    if shot == "front":                      # front ortho close-up of the left shoulder, arm hanging
        dv = (0, -1, 0); rig_follow_camera(dv, (50, 0, -17)); cam_ortho((50.0, 0, -17.0), dv, 36.0, (R, R)); deg = 0.0
    elif shot == "frontw":                   # wider front ortho (shoulder + whole arm)
        dv = (0, -1, 0); rig_follow_camera(dv, (50, 0, -30)); cam_ortho((52.0, 0, -32.0), dv, 64.0, (R, int(R * 1.25))); deg = 0.0
    elif shot == "top":                      # from above (ortho), arm hanging
        dv = (0, -1e-4, 1); rig_follow_camera(dv, (50, 3, -17)); cam_ortho((50.0, 3.0, 0.0), dv, 44.0, (R, R)); deg = 0.0
    elif shot in ("p34", "p34r"):            # 3/4 from the front-left-above (hero direction), hanging / raised
        cam_p34((50.0, -6.0, -20.0), (0.62, -1.0, 0.32), 58.0, (R, int(R * 0.86)))
        deg = 0.0 if shot == "p34" else RAISE
    elif shot in ("hero", "heror"):          # hero direction of the R3 sheets (front-left-above), wider
        cam_p34((48.0, -10.0, -22.0), (0.95, -0.80, 0.30), 70.0, (R, int(R * 0.86)))
        deg = 0.0 if shot == "hero" else RAISE
    elif shot in ("p34b", "p34br"):          # 3/4 from the back-left-above
        cam_p34((50.0, 6.0, -19.0), (0.85, 0.95, 0.40), 52.0, (R, int(R * 0.86)))
        deg = 0.0 if shot == "p34b" else RAISE
    elif shot in ("p34f", "p34fr"):          # frontal 3/4 like R01 (front-left, slightly above)
        cam_p34((49.0, -5.0, -19.0), (0.42, -1.0, 0.26), 50.0, (R, int(R * 0.86)))
        deg = 0.0 if shot == "p34f" else RAISE
    elif shot in ("low", "lowr"):            # from the front-left, slightly below (shows the lower half of the joint)
        cam_p34((50.0, -4.0, -20.0), (0.75, -1.0, -0.22), 52.0, (R, int(R * 0.86)))
        deg = 0.0 if shot == "low" else RAISE
    else:
        say("unknown shot", shot); continue
    save_cam(shot, dict(deg=deg))
    for vid in VIDS_R:
        rot = build_variant(vid)
        pose(rot, deg)
        render(f"{shot}_{vid}")
say("KLB done")
