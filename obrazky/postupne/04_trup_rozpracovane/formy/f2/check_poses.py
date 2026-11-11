"""clash + gap check of the render poses (awake hero, personality) with the f2 shells -> merged into check.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_fit as C

POSES = {
    "awake_hero": {"lift": 12.5, "tilt": 8, "pan": 0, "armR": 14, "armL": 14},
    "persona": {"j1": 20, "pan": 30, "lift": 15, "tilt": -12, "armR": 125, "armL": 12},
    "rest": {},
}
P = C.f2_parts()
L = C.layout(P)
HEAD = ["B_hlava", "B_usi", "B_ram_tvar", "B_uska"]
out = {}
for nm, p in POSES.items():
    cl = L.clashes(p, 0.5, only_moving=True)
    g = C.gaps(L, p, ["A_R_vnutorna", "A_R_vonkajsia", "A_R_kryt"], HEAD)
    out[nm] = {"pose": p, "moving_clashes": cl, "armR_to_head_envelope_mm": round(g[0], 2)}
    print(nm, out[nm], flush=True)
C.merge("render_poses", out)
