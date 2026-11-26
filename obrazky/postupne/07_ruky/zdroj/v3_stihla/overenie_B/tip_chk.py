"""black tip A_spicka (= inner half A_vnut beyond the tip plane, as scene_tvar / v2_scene build it): size, and where it meets
the seam, for the approved arm and variant B (Monte Carlo on the analytic inside test)"""
import sys, json
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); import variants as VA
rng = np.random.default_rng(3)
out = {}
for vid in ("0", "B"):
    pt, n = VA.tip_plane_local(vid)
    P = np.c_[rng.uniform(-14, 14, 2_000_000), rng.uniform(-18, 18, 2_000_000), rng.uniform(-72, -40, 2_000_000)]
    ins = VA.inside_local(vid, P)
    u = -P[:, 2] / VA.L
    inner = P[:, 0] < VA.seam_x(vid, u)
    tip = ins & inner & (((P - pt) @ n) > 0)
    vol = tip.mean() * 28 * 36 * 32
    T = P[tip]
    # thickness of the tip piece along the plane normal at its thickest
    h = (T - pt) @ n
    out[vid] = dict(volume_mm3=round(float(vol), 0), max_depth_along_normal=round(float(h.max()), 2),
                    z_range=[round(float(T[:, 2].min()), 2), round(float(T[:, 2].max()), 2)],
                    y_range=[round(float(T[:, 1].min()), 2), round(float(T[:, 1].max()), 2)],
                    x_range=[round(float(T[:, 0].min()), 2), round(float(T[:, 0].max()), 2)])
    print(vid, out[vid])
json.dump(out, open("tip_chk.json", "w"), indent=1)
