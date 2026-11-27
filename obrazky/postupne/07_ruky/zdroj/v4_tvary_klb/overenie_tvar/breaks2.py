"""C1 / C2 breaks of the outline lines along the arm (own numerics).  For f(u) in mm, z = -72 u:
left / right one-sided second derivatives (5-point stencils) at step du and du/4; a true curvature break keeps its jump,
a smooth (but fast-changing) curvature gives a jump that shrinks with the step.  Reports breaks with jump(du/4) >= 0.6 jump(du)."""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
L = 72.0


def lines(vid, u):
    c, ti, to, wi, wo, ni, no = AS.secf(vid, u)
    return dict(outer=c + to, inner=c - ti, side_in=wi, side_out=wo, seam=c, ti=ti, to=to)


def onesided(vid, key, u, du):
    f = lambda k: lines(vid, u + k * du)[key]
    f0, l1, l2, l3, r1, r2, r3 = f(0), f(-1), f(-2), f(-3), f(1), f(2), f(3)
    dz = L * du
    d2l = (2 * f0 - 5 * l1 + 4 * l2 - l3) / dz ** 2
    d2r = (2 * f0 - 5 * r1 + 4 * r2 - r3) / dz ** 2
    d1l = (3 * f0 - 4 * l1 + l2) / (2 * dz)
    d1r = (-3 * f0 + 4 * r1 - r2) / (2 * dz)
    return d2l, d2r, d1l, d1r


OUT = {}
for vid in (sys.argv[1].split(",") if len(sys.argv) > 1 else ["B0", "B1", "B2", "B3"]):
    R = {}
    u = np.linspace(0.025, 0.975, 190001)
    for key in ("outer", "inner", "side_in", "side_out", "seam"):
        a = onesided(vid, key, u, 2e-3); b = onesided(vid, key, u, 5e-4)
        ja = np.abs(a[0] - a[1]); jb = np.abs(b[0] - b[1])
        sa = np.degrees(np.abs(np.arctan(a[2]) - np.arctan(a[3]))); sb = np.degrees(np.abs(np.arctan(b[2]) - np.arctan(b[3])))
        found = []
        jj = jb.copy()
        for _ in range(6):
            k = int(np.argmax(jj))
            if jj[k] < 1e-4:
                break
            win = np.abs(u - u[k]) < 0.004
            ratio = jb[k] / max(ja[win].max(), 1e-12)
            # curvature level around the spot (to judge visibility): |f''| (1/mm) averaged left/right
            lvl = 0.5 * (abs(b[0][k]) + abs(b[1][k]))
            found.append(dict(u=round(float(u[k]), 4), jump_1_per_mm=round(float(jb[k]), 5), ratio_fine_coarse=round(float(ratio), 2),
                              true_break=bool(ratio > 0.6), radius_left=round(float(1 / max(abs(b[0][k]), 1e-9)), 1),
                              radius_right=round(float(1 / max(abs(b[1][k]), 1e-9)), 1), slope_jump_deg=round(float(sb[k]), 4)))
            jj[np.abs(u - u[k]) < 0.01] = 0
        R[key] = dict(max_slope_jump_deg=round(float(sb.max()), 5), at_u=round(float(u[int(np.argmax(sb))]), 4), d2=found)
    OUT[vid] = R
    print(vid)
    for key, v in R.items():
        tb = [d for d in v["d2"] if d["true_break"]]
        print("  %-8s max slope jump %.4f deg @u %.4f | true C2 breaks:" % (key, v["max_slope_jump_deg"], v["at_u"]),
              [(d["u"], d["jump_1_per_mm"], d["radius_left"], d["radius_right"]) for d in tb])
json.dump(OUT, open("out/breaks2.json", "w"), indent=1)
