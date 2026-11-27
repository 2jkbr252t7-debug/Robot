"""NOVA mini - R4 final renders: arm-B rounding variants (B0..B3, R4/tvar/variants_b.py) x shoulder-joint variants (K0..K3,
R4/klb/klb.py).  Runs R4/img/work/scene_v3_r4.py (= R3 scene_v3.py with the R4 shape module) WITHOUT its dispatch and reuses
its scene / material / light / camera functions, so materials, lights and cameras are the approved v3 ones.

usage: /opt/venv/bl/bin/python -B scene_r4.py -- --shot S --res R --samples N --out DIR [--exposure -0.3]
           [--vids B0,B1,..] [--kvids K0,K1,..] [--arm B0] [--joint v3|K0..K3] [--ppm 10] [--deg 90] [--tag x]
shots (one shot type per process, because rig_follow_camera moves the shared lights):
  front    whole robot, ortho from the front, arms hanging, every (vid, joint) pair -> front<tag>_<vid>_<joint>.png
           (--base 0: without the base = "upper robot")
  hero     v3 hero camera (head pan 20, left arm raised --deg, base + floor shadow)  -> hero<tag>_<vid>_<joint>.png
  armlook  the left arm alone in its local frame (upright, no splay): zvonka (+x), spredu (-y), zhora (+z) -> look_<view>_<vid>.png
  kfront   front ortho close-up of the left shoulder (arm --arm, every --kvids joint)    -> kfront_<arm>_<K>.png
  kp34     frontal 3/4 close-up (fixed v3 light rig), arm hanging                      -> kp34_<arm>_<K>.png
  kp34r    same camera, left arm raised --deg                                           -> kp34r_<arm>_<K>.png
  r01      whole robot from the front-left like R01 (--dv, --pan, --deg 0 = arms hanging) -> r01<tag>_<vid>_<joint>.png
joint 'v3' = the original v2 plug of the v3 sheets (img_v2 zatka / zatka_skrutky, both sides); K0..K3 = klb.py parts (both
sides, right side = mirror).  Rotating joint parts get the arm's swing matrix (klb.swing_matrix == g2.V.swing_matrix)."""
import sys, os, math, json, argparse
WK = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(WK, "scene_v3_r4.py")
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

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap2 = argparse.ArgumentParser()
ap2.add_argument("--shot", default="front")
ap2.add_argument("--vids", default="B0,B1,B2,B3")
ap2.add_argument("--kvids", default="K0,K1,K2,K3")
ap2.add_argument("--arm", default="B0")
ap2.add_argument("--joint", default="v3")
ap2.add_argument("--deg", type=float, default=90.0)
ap2.add_argument("--base", type=int, default=1)
ap2.add_argument("--tag", default="")
ap2.add_argument("--span", type=float, default=0.0)
ap2.add_argument("--pan", type=float, default=15.0)
ap2.add_argument("--dv", default="0.50,-1.0,0.22")
B, _ = ap2.parse_known_args(argv)

JOINT_OBJS = []
ROT = {1: [], -1: []}            # rotating joint parts per side (posed with the arm)


def clear_joint():
    for o in list(JOINT_OBJS):
        try:
            remove(o)
        except Exception:
            pass
    JOINT_OBJS.clear(); ROT[1].clear(); ROT[-1].clear()


def load_joint(kvid, sides=(1, -1)):
    """static + rotating parts of joint kvid on both sides ('v3' = original plug, loaded once by the caller)"""
    clear_joint()
    if kvid == "v3":
        return
    v = KL.variant(kvid)
    for p in v["parts"]:
        o = imp(p["stl"], p["id"] + "_L", p["mat"], sm=True, ang=30)
        objs = {1: o}
        if -1 in sides:
            objs[-1] = mirror_copy(o, p["id"] + "_P")
        if 1 not in sides:
            o.hide_render = True
        for s_, ob in objs.items():
            JOINT_OBJS.append(ob)
            if p["role"] == "rotating":
                ROT[s_].append(ob)
    rp = [q for q in KL.VARIANTS[kvid]["parts"] if q["role"] == "rotating"]
    if rp:      # dark filler inside the collar / ring bore (the closed render solid of the arm would show white there)
        prof = rp[0]["profile"]()
        x_end = float(prof[:, 0].min()); r_in = float(prof[prof[:, 0] < x_end + 0.01][:, 1].min())
        sh = KL.arm_dx(kvid) - KL.DX0
        f = xcyl_key("_bore_" + kvid, 0, r_in - 0.05, x_end + 1.6, 54.0 + sh, "tien")
        objs = {1: f}
        if -1 in sides:
            objs[-1] = mirror_copy(f, "_bore_P_" + kvid)
        for s_, ob in objs.items():
            JOINT_OBJS.append(ob); ROT[s_].append(ob)
    vl.update()


def arm_dx(kvid):
    return DX if kvid == "v3" else KL.arm_dx(kvid)


def build_pair(vid, kvid, right=True):
    """both arms of shape vid at the joint's dx (+ joint parts); returns {side: dict of arm objects}"""
    clear_arms()
    Lp = build_arm_variant(vid, arm_dx(kvid))
    arms = {1: Lp}
    if right:
        arms[-1] = {k: mirror_copy(o, o.name.replace("A_", "AP_")) for k, o in Lp.items()}
    for d in arms.values():
        ARM_OBJS.extend(d.values())
    vl.update()
    return arms


def pose_left(arms, deg):
    pose_arm(arms[1], deg, 1)
    Mw = M4(KL.swing_matrix(deg))
    for o in ROT[1]:
        o.matrix_world = Mw
    vl.update()


def pairs():
    out = []
    for v in B.vids.split(","):
        for k in B.joint.split(","):
            out.append((v, k))
    return out


def cam_p34(tgt, dv, span, res, lens=120.0):
    dv = Vector(dv).normalized()
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = res
    CAM.location = Vector(tgt) + dv * (span * lens / 24)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()


def static_scene(pan, base, plug_v3):
    load_t4(T_EXT); load_head(pan)
    if base:
        load_base()
    if plug_v3:
        load_new(["zatka", "zatka_skrutky"])


say("R4 shot", B.shot, B.vids, B.joint, B.kvids, B.arm)
R_ = A.res
if B.shot == "front":
    joints = B.joint.split(",")
    static_scene(0.0, B.base == 1, "v3" in joints)
    dv = (0, -1, 0)
    rig_follow_camera(dv)
    # upper robot (no base): z -90 .. 93 ; whole robot: floor .. 93
    zlo = -90.0 if B.base == 0 else Z_FLOOR - 2.0
    zhi = 93.0
    wmm = 172.0
    hmm = zhi - zlo
    cam_ortho((0, 0, (zlo + zhi) / 2), dv, wmm, (R_, int(round(R_ * hmm / wmm))))
    save_cam("front" + B.tag, dict(zlo=zlo, zhi=zhi, base=B.base))
    for vid, kv in pairs():
        load_joint(kv)
        arms = build_pair(vid, kv)
        render(f"front{B.tag}_{vid}_{kv}")
elif B.shot == "hero":
    joints = B.joint.split(",")
    static_scene(20.0, True, "v3" in joints)
    floor(True)
    dv = Vector((0.95, -0.80, 0.30)).normalized()
    lens = 120
    zf, ztop = Z_FLOOR, 88.0
    tgt = Vector((4.0, -6.0, (zf + ztop) / 2 + 3.0))
    span = (ztop - zf) * 1.22
    W, H = R_, int(R_ * 1.2)
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = W, H
    CAM.location = tgt + dv * (span * lens / 24)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()
    save_cam("hero" + B.tag, dict(deg=B.deg))
    for vid, kv in pairs():
        load_joint(kv)
        arms = build_pair(vid, kv)
        pose_left(arms, B.deg)
        render(f"hero{B.tag}_{vid}_{kv}")
elif B.shot == "r01":
    # whole robot from the front-left like R01 (fixed v3 light rig, floor shadow), head pan --pan, left arm at --deg
    joints = B.joint.split(",")
    static_scene(B.pan, True, "v3" in joints)
    floor(True)
    dv = Vector(tuple(float(t) for t in B.dv.split(","))).normalized()
    lens = 120
    zf, ztop = Z_FLOOR, 88.0
    tgt = Vector((6.0, -4.0, (zf + ztop) / 2 + 2.0))
    span = (ztop - zf) * (B.span or 1.16)
    W, H = R_, int(R_ * 1.2)
    cam_d.type = "PERSP"; cam_d.lens = lens; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
    sc.render.resolution_x, sc.render.resolution_y = W, H
    CAM.location = tgt + dv * (span * lens / 24)
    CAM.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    vl.update()
    save_cam("r01" + B.tag, dict(deg=B.deg, pan=B.pan))
    for vid, kv in pairs():
        load_joint(kv)
        arms = build_pair(vid, kv)
        if B.deg:
            pose_left(arms, B.deg)
        render(f"r01{B.tag}_{vid}_{kv}")
elif B.shot == "armlook":
    views = [("zvonka", (1, 0, 0)), ("spredu", (0, -1, 0)), ("zhora", (0, -1e-4, 1))]
    first = True
    for vid in B.vids.split(","):
        clear_arms()
        d = build_arm_variant(vid, DX, local=True)
        ARM_OBJS.extend(d.values())
        vl.update()
        for view, dv in views:
            rig_follow_camera(dv, (0.0, 0.0, -36.0))
            if view == "zhora":
                cam_ortho((0.0, 0.0, 0.0), dv, 40.0, (int(40 * A.ppm), int(40 * A.ppm)))
            else:
                cam_ortho((0.0, 0.0, -36.0), dv, 40.0, (int(40 * A.ppm), int(82 * A.ppm)))
            vl.update()
            if first:
                save_cam("look_" + view)
            render(f"look_{view}_{vid}")
        first = False
elif B.shot in ("kfront", "kp34", "kp34r"):
    static_scene(0.0, False, False)
    if B.shot == "kfront":
        dv = (0, -1, 0)
        span = B.span or 50.0
        tgt = (52.0, 0.0, -22.0)
        rig_follow_camera(dv, (50, 0, -17))
        cam_ortho(tgt, dv, span, (R_, int(R_ * 1.1)))
        deg = 0.0
    else:
        span = B.span or 56.0
        cam_p34((49.0, -5.0, -21.0), (0.42, -1.0, 0.26), span, (R_, int(R_ * 1.0)))
        deg = 0.0 if B.shot == "kp34" else B.deg
    save_cam(B.shot, dict(deg=deg))
    for kv in B.kvids.split(","):
        load_joint(kv)
        arms = build_pair(B.arm, kv)
        if deg:
            pose_left(arms, deg)
        render(f"{B.shot}_{B.arm}_{kv}")
else:
    say("unknown shot", B.shot)
say("R4 done")
