"""B0 (R4/tvar/variants_b.py) == variant B of R3/tvar/variants.py ?  own tests (CAD venv)"""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar"); import variants_b as VB
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); import variants as R3
out = {}
us = np.linspace(0, 1, 100001)
a = R3.section("B", us); b = VB.section("B0", us)
out["section_maxdev"] = max(float(np.max(np.abs(np.asarray(x, float) - np.asarray(y, float)))) for x, y in zip(a, b))
wi, wo = VB.half_widths("B0", us)
out["half_widths_vs_w"] = float(max(np.abs(wi - a[3]).max(), np.abs(wo - a[3]).max()))
rng = np.random.default_rng(11)
P = np.c_[rng.uniform(-16, 12, 2_000_000), rng.uniform(-18, 18, 2_000_000), rng.uniform(-74, 2, 2_000_000)]
out["inside_mismatch_2M"] = int((VB.inside_local("B0", P) != R3.inside_local("B", P)).sum())
for ins in (0.0, 1.2, 1.6):
    out[f"inside_mismatch_inset{ins}"] = int((VB.inside_local("B0", P[:500000], ins) != R3.inside_local("B", P[:500000], ins)).sum())
r0 = R3.pebble_rows("B", 300, 400); r1 = VB.pebble_rows("B0", 300, 400)
out["rows_dev"] = float(max(np.abs(r0[0] - r1[0]).max(), np.abs(r0[1] - r1[1]).max(), np.abs(r0[2] - r1[2]).max()))
for h in ("vonk", "vnut"):
    h0 = R3.half_rows("B", h, 200, 150); h1 = VB.half_rows("B0", h, 200, 150)
    out[f"half_rows_{h}_dev"] = float(np.abs(h0[0] - h1[0]).max()) if h0[0].shape == h1[0].shape else "shape differs"
t0 = R3.tip_plane_local("B"); t1 = VB.tip_plane_local("B0")
out["tip_plane_dev"] = float(max(np.abs(t0[0] - t1[0]).max(), np.abs(t0[1] - t1[1]).max()))
Q = rng.uniform(-60, 60, (20000, 3))
out["to_world_dev"] = float(np.abs(VB.to_world(Q, "B0") - R3.to_world(Q, "B")).max())
out["to_world_right_dev"] = float(np.abs(VB.to_world(Q, "B0", sx=-1) - R3.to_world(Q, "B", sx=-1)).max())
out["swing_dev"] = float(max(np.abs(VB.swing(Q, a_) - R3.swing(Q, a_)).max() for a_ in (-51, -45, 30, 135, 140.5)))
out["thickness_dev"] = float(np.abs(VB.thickness("B0", us) - R3.thickness("B", us)).max())
out["faces_dev"] = float(max(np.abs(np.asarray(x) - np.asarray(y)).max() for x, y in zip(VB.faces("B0", us), R3.faces("B", us))))
# B0's numbers against R3 B
T = R3.thickness("B", us); w = R3.profile("B", us)[0]
out["R3B_Tmax"] = round(float(T.max()), 3); out["R3B_Wmax"] = round(float(2 * w.max()), 3)
c, ti, to, w22, _, _ = R3.section("B", 0.22)
out["R3B_cover_inner_joint"] = [round(float(to), 3), round(float(ti), 3)]
out["R3B_params"] = R3.VARIANTS["B"]
print(json.dumps(out, indent=1))
json.dump(out, open("out/repro.json", "w"), indent=1)
