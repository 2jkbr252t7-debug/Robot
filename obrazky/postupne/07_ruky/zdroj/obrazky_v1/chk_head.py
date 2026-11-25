"""v1 (pebble dx 12 + joint cover) vs head (B, pan 0, lift 0, tilt 0) and vs torso, over the swing -45..135"""
import sys, numpy as np, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3"); sys.path.insert(0, ".")
import vlib, v1geo as V
from scipy.spatial import cKDTree
HEAD = ["hlava_skrupina", "ram_displeja", "displej", "usi", "usko_kryt", "usko_lozisko", "led_kruzky", "krk_predna_polovica", "krk_zadna_polovica"]
H = np.concatenate([vlib.sample_surface(vlib.load_stl(f"/tmp/claude-0/gapwf/fin/B/stl/{n}.stl"), 0.4) for n in HEAD])
H = H[H[:, 0] > 10]
th = cKDTree(H)
TOR = ["T_bok_L", "T_stred", "T_spodok", "T_dvere"]
Tp = np.concatenate([vlib.sample_surface(vlib.load_stl(f"/tmp/claude-0/gapwf/fin/T4/stl/{n}.stl"), 0.4) for n in TOR])
Tp = Tp[Tp[:, 0] > 20]
tt = cKDTree(Tp)
rows, top, bot = V.pebble_rows(160, 200)
Pp = V.to_world(rows.reshape(-1, 3))
cov = vlib.sample_surface(vlib.load_stl("stl/kryt_surovy.stl"), 0.7)
cov = cov[~V.inside_local(V.to_local(cov))]
res = {}
print("cover pts", len(cov), flush=True)
for nm, P in (("pebble", Pp), ("kryt", cov)):
    out = []
    for deg in range(-45, 136, 5):
        M = V.swing_matrix(deg)
        Q = P @ M[:3, :3].T + M[:3, 3]
        dh = th.query(Q)[0].min(); dt = tt.query(Q)[0].min()
        out.append((deg, round(float(dh), 2), round(float(dt), 2)))
    res[nm] = out
    print(nm, "min to head", min(o[1] for o in out), "at", min(out, key=lambda o: o[1])[0], "| min to torso shell", min(o[2] for o in out), "at", min(out, key=lambda o: o[2])[0])
json.dump(res, open("chk_head.json", "w"))
