"""Pose matrices (t1lib kinematics of the final PACK) for the renders + STLs of the few PACK internals that are visible
from outside (rotating J1 skirt, wheels, casters).  Usage: /opt/venv/cad/bin/python pose.py <out.json> '<pose json>'"""
import sys, os, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
from build123d import export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = "/tmp/claude-0/gapwf/fin/T1/pack/layout.json"
VISIBLE = {"T_J1_sukna": "black", "Z_koleso_L": "rubber", "Z_koleso_R": "rubber", "Z_kolieska_P": "black",
           "Z_kolieska_Z": "black", "Z_J1_koleso": "metal", "T_J1_pastorok": "metal"}


def pose_json(pose, out):
    L = T.Layout(PACK)
    d = {"pose": pose, "Z_TT": L.Z_TT, "dz_B": T.b_frame_dz(L.Z_TT),
         "loc": {g: T._loc_matrix(L.loc(g, pose)) for g in T.GROUPS}, "pack_parts": []}
    os.makedirs(os.path.join(HERE, "work", "pack_vis"), exist_ok=True)
    for nm, col in VISIBLE.items():
        fn = os.path.join(HERE, "work", "pack_vis", nm + ".stl")
        if not os.path.exists(fn):
            export_stl(L.raw(nm), fn, tolerance=0.02, angular_tolerance=0.2)
        d["pack_parts"].append({"name": nm, "group": L.comp(nm)["group"], "color": col, "stl": fn})
    json.dump(d, open(out, "w"), indent=1)


if __name__ == "__main__":
    pose_json(json.loads(sys.argv[2]), sys.argv[1])
