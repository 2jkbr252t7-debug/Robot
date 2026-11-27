"""R4/klb: inner half A_vnut of arm B with the variant's opening (frame B, left side, rest pose) -> stl/<vid>/A_vnut_otvor_<vid>.stl
Shell as in R3 scene_v3.shot_rezv (open dome solidified 1.6 inwards, black tip cut off), opening = cylinder r arm_hole_r
x 44 .. 56 about the shoulder axis.  The M2b hub (part of A_vnut in R3) is NOT included: in K1/K3 it is the black
printed part ARM_naboj_* glued into this opening.   /opt/venv/bl/bin/python -B exp_avnut.py -- --noren"""
import sys, os, json
SRC = "/tmp/claude-0/gapwf/fin/R3/img/work/scene_v3.py"
code = open(SRC).read()
code = code[:code.index('say("start", A.shot)')]
g = {"__file__": SRC, "__name__": "scene"}
exec(compile(code, SRC, "exec"), g)
globals().update({k: v for k, v in g.items() if not k.startswith("__")})
import bpy, bmesh
KD = "/tmp/claude-0/gapwf/fin/R4/klb"
sys.path.insert(0, KD)
import klb as KL

rep = {}
for vid in ("K0", "K1", "K3", "K3v"):
    v = KL.variant(vid)
    dx = KL.arm_dx(vid)
    si = half_solid("A_vnut_" + vid, "B", "vnut", "biela", dx, open_seam=True)
    ptl, ntl = VA.tip_plane_local("B")
    pt = VA.to_world(ptl, "B", dx); nt = VA.dir_world(ntl)
    bisect(si, pt - nt * VA.SEAM, nt, clear_outer=True)
    solidify(si, 1.6)
    hole = xcyl_key("cut_" + vid, 0, v["arm_hole_r"], 44.0, 56.0 + (dx - KL.DX0), "tien")
    boolean(si, hole); remove(hole)
    bm = bmesh.new(); bm.from_mesh(si.data)
    bad = sum(1 for e in bm.edges if not e.is_manifold); vol = abs(bm.calc_volume(signed=True)); bm.free()
    p = os.path.join(KD, "stl", vid, f"A_vnut_otvor_{vid}.stl")
    export_obj(si, p)
    rep[vid] = dict(hole_d=round(2 * v["arm_hole_r"], 2), nonmanifold_edges=bad, volume=round(vol, 1), stl=p)
    say("A_vnut", vid, rep[vid])
    remove(si)
json.dump(rep, open(os.path.join(KD, "exp_avnut.json"), "w"), indent=1)
