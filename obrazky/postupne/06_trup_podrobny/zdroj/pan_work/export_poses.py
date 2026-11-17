"""pose STLs of the PAN module for previews / the integrator: pan_work/poses/lift<L>/<part>.stl (pan 0) for L = 10, 20 and the
FPC alone in the extreme / mid poses: pan_work/poses/fpc/fpc_zdvih_<L>.stl (L 0 / 10 / 20), fpc_pan_<P>.stl (P -85 / 0 / 85)"""
import os, sys, shutil
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_pan as M, t4_common as C
import build123d as bd
W = "/tmp/claude-0/gapwf/fin/T4/pan_work/poses"
parts = M.build()
for lift in (10.0, 20.0):
    d = os.path.join(W, f"lift{int(lift)}"); os.makedirs(d, exist_ok=True)
    S = {n: p["shape"] for n, p in parts.items()}
    S.update(M.pose_parts(lift))
    S["fpc_pan"] = M.one(M.fuse([M.fpc_lift(lift), M.fpc_stage(), M.fpc_loop(0.0)]))
    for n, s in S.items():
        M.export_stl_abs(s, os.path.join(d, n + ".stl"))
    print("lift", lift, len(S), "parts")
d = os.path.join(W, "fpc"); os.makedirs(d, exist_ok=True)
rep = {}
for lift in (0.0, 10.0, 20.0):
    s = M.fpc_lift(lift); M.export_stl_abs(s, os.path.join(d, f"fpc_zdvih_{int(lift)}.stl"))
    bb = s.bounding_box(); rep[f"fpc_zdvih_{int(lift)}"] = [round(v, 2) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)]
for pan in (-85.0, 0.0, 85.0):
    s = M.fpc_loop(pan); M.export_stl_abs(s, os.path.join(d, f"fpc_pan_{int(pan)}.stl"))
    bb = s.bounding_box(); rep[f"fpc_pan_{int(pan)}"] = [round(v, 2) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)]
    print("pan", pan, "inner / outer free run, U-turn az:", [round(v, 2) for v in M.loop_lengths(pan)])
import json; json.dump(rep, open(os.path.join(W, "fpc_bbox.json"), "w"), indent=1); print(rep)
