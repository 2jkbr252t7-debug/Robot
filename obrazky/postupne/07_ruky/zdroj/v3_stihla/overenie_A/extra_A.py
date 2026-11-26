"""Verifier extras for variant A + M2b (and M3 arm side):
 1. cover magnets Ø3x2 + bosses r 2.2 x 2.4 (v1geo concept: u 0.16 / 0.66, 3.5 inside the outline, on the seam) -
    depth left in the flatter cover, back wall over the magnet, clash with the joint parts
 2. assembly sweeps: (a) the cover A_vonk goes on along -local x (its pocket = parts swept along local x);
    (b) drive hub / washer / bearing go into A_vnut along -world X with the cover off
 3. M2b with a hardware-store DIN 912 M4x20 head instead of DIN 7984 (head 4.0 high -> drive-hub cap to 64.1)
 4. shell wall 1.6 instead of the 1.2 rule (drive hub / washer clearance to the shell inside)
 5. top dome above the drive hub, the arm hub's connection to the inner shell, the seam position on the axis
 6. black tip: identical cut of the inner half? (tip plane, sizes for variant 0 and A)"""
import sys, os, json, math, copy, time
T0 = time.time()
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomA as G  # noqa
import own_fit as OF  # noqa
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as PT  # noqa

OUT = {}
SW, SH, SL = OF.arm_surface(0.05)
xS, rS, azS = OF.xr_az(SW)
O = PT.options()
M2b = {p.name: p for p in O["M2b"]["parts"]}
M3 = {p.name: p for p in O["M3"]["parts"]}

# ------------------------------------------------------------------ 0. seam on the axis, local frame directions
ex_loc = G.R.T @ np.array([1.0, 0, 0])
# world x of the seam plane (local x = 0) on lines || X at (y, z)
def seam_x_world(y, z):
    # local x = (Q - ATT) . R[:,0] + A_LOC[0] = 0  -> solve for Q.x
    c = G.R[:, 0]
    rest = (-G.ATT[0]) * c[0] + (y - G.ATT[1]) * c[1] + (z - G.ATT[2]) * c[2] + G.A_LOC[0]
    return -rest / c[0]
OUT["seam"] = dict(world_X_in_local=ex_loc.round(4).tolist(), seam_x_on_axis=round(seam_x_world(3.0, -17.0), 3),
                   seam_x_at_r13_top=round(seam_x_world(3.0, -4.0), 3), seam_x_at_r13_bottom=round(seam_x_world(3.0, -30.0), 3),
                   seam_x_at_r13_front=round(seam_x_world(-10.0, -17.0), 3), seam_x_at_r13_back=round(seam_x_world(16.0, -17.0), 3))
print(f"[{time.time()-T0:.0f}s]", "0.", OUT["seam"])

# ------------------------------------------------------------------ 1. cover magnets
def boss_spots(ko, kw):
    out = []
    for u, sgn in ((0.16, -1), (0.16, 1), (0.66, -1), (0.66, 1)):
        hw, ht = G.prof(u)
        out.append(np.array([0.0, sgn * (kw * float(hw) - 3.5), -G.L * u]))
    return out


def outer_x_at(y, z, ko, kw):
    u = -z / G.L
    hw, ht = G.prof(u)
    w, to = kw * hw, ko * ht
    a = np.clip(np.abs(y) / w, 0, 1)
    return to * (1 - a ** 2.3) ** (1 / 2.3)


mag = {}
for vid, ko, kw in (("0", 1.0, 1.0), ("A", 0.62, 0.95)):
    rows = []
    for m in boss_spots(ko, kw):
        th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        res = {}
        for rr, nm in ((2.2, "boss_r2.2"), (1.55, "pocket_r1.55")):
            yy = m[1] + rr * np.cos(th); zz = m[2] + rr * np.sin(th)
            res[nm] = float(outer_x_at(yy, zz, ko, kw).min())
        res["centre"] = float(outer_x_at(np.array([m[1]]), np.array([m[2]]), ko, kw)[0])
        # cover side: magnet pocket x 0.25..2.30 (0.03 offset + 2.0 + 0.02), boss to 2.65
        rows.append(dict(spot_local=m.round(2).tolist(), outer_skin_x_min_over_boss=round(res["boss_r2.2"], 2),
                         outer_skin_x_min_over_pocket=round(res["pocket_r1.55"], 2), outer_skin_x_centre=round(res["centre"], 2),
                         back_wall_over_magnet=round(res["pocket_r1.55"] - 2.30, 2),
                         boss_end_vs_skin=round(res["boss_r2.2"] - 2.65, 2)))
    mag[vid] = rows
OUT["cover_magnets"] = mag
for vid in mag:
    for r_ in mag[vid]:
        print("1.", vid, r_)

# clash of the cover bosses (variant A spots) with the joint parts of M2b and M3: sample boss cylinders (both halves)
def boss_points(m, h=0.1):
    pts = []
    for side in (1, -1):
        for x in np.arange(0.25, 2.65 + 1e-9, h):
            n = int(2 * np.pi * 2.2 / h)
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            pts.append(np.c_[np.full(n, side * x), m[1] + 2.2 * np.cos(th), m[2] + 2.2 * np.sin(th)])
        for rho in np.arange(0, 2.2 + 1e-9, h):
            n = max(1, int(2 * np.pi * rho / h))
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            pts.append(np.c_[np.full(n, side * 2.65), m[1] + rho * np.cos(th), m[2] + rho * np.sin(th)])
    return np.concatenate(pts)

clash = {}
for oname, P in (("M2b", M2b), ("M3", M3)):
    best = (9e9, None, None)
    for i, m in enumerate(boss_spots(0.62, 0.95)):
        W = G.to_world(boss_points(m))
        for p in P.values():
            if p.role == "torso" or not p.pebble:
                continue
            d = OF.dist_part(W, p).min()
            if d < best[0]:
                best = (float(d), p.name, i)
    clash[oname] = dict(min_dist_boss_to_part=round(best[0], 3), part=best[1], boss=best[2])
OUT["cover_boss_vs_joint"] = clash
print(f"[{time.time()-T0:.0f}s]", "1b.", clash)

# ------------------------------------------------------------------ 2. assembly sweeps
def sweep_min(p, direction_world, tmax, half_mask, h=0.3, dt=0.5, region=None):
    """min signed distance from the part (surface samples) swept by t*direction (t in 0..tmax) to the given half of the
    arm skin (exact meridian distance is not usable once the part leaves the axis -> point cloud + KD tree)"""
    from scipy.spatial import cKDTree
    key = int(half_mask.sum())
    if key not in _TREES:
        _TREES[key] = cKDTree(SW[half_mask])
    tree = _TREES[key]
    Pp = p.surface(h)
    best = (9e9, None)
    for t in np.arange(0, tmax + 1e-9, dt):
        Q = Pp + t * direction_world
        d, _ = tree.query(Q, distance_upper_bound=6.0, workers=2)
        # sign: inside the arm?
        Lq = G.to_local(Q)
        ins = G.inside(Lq)
        sd = np.where(ins, d, -d)
        if region == "cover":
            sd = np.where(Lq[:, 0] >= 0.25, sd, 9e9)
        elif region == "inner":
            sd = np.where(Lq[:, 0] <= -0.25, sd, 9e9)
        k = int(np.argmin(sd))
        if sd[k] < best[0]:
            best = (float(sd[k]), float(t))
    return best

_TREES = {}
seam_dir_world = G.R @ np.array([1.0, 0, 0])            # local +x in world
sweeps = {}
outer_mask = SH
inner_mask = ~SH
# (a) cover on: relative to the cover the parts move along +local x from far below -> pocket = sweep along -local x
#     (distance to the OUTER-half skin must stay >= 1.5 for moving parts, 1.2 for static-to-arm parts) - sweep the
#     parts towards the seam until they are entirely below the seam plane
for nm in ("DRV_unasac", "M4_DIN7984_M4x20", "ARM_podlozka_M12"):
    p = M2b[nm]
    d, t = sweep_min(p, -seam_dir_world, 8.0, outer_mask, region="cover")
    sweeps[f"M2b {nm} cover-on sweep (outer skin)"] = dict(min=round(d, 3), at_t=t)
# (b) drive hub / washer / bearing into A_vnut along -world X (= the part moves +X out of its seat when removed):
#     distance to the INNER-half skin over the path, until the part has passed the seam plane
for nm in ("DRV_unasac", "ARM_podlozka_M12", "BRG_MR128_vonk"):
    p = M2b[nm]
    d, t = sweep_min(p, np.array([1.0, 0, 0]), 14.0, inner_mask, region="inner")
    sweeps[f"M2b {nm} insert along X (inner skin)"] = dict(min=round(d, 3), at_t=t)
OUT["sweeps"] = sweeps
for k, v in sweeps.items():
    print(f"[{time.time()-T0:.0f}s] 2.", k, v)

# ------------------------------------------------------------------ 3. M2b with DIN 912 M4x20 (head 4.0) instead of DIN 7984
P912 = copy.deepcopy(O["M2b"])
for p in P912["parts"]:
    if p.name == "M4_DIN7984_M4x20":
        p.name = "M4_DIN912_M4x20"; p.prof = np.array([(52.5, 0), (52.5, 2.0), (58.9, 2.0), (58.9, 3.5), (62.9, 3.5), (62.9, 0)], float)
    if p.name == "DRV_unasac":
        p.prof = np.array([(58.4, 3.5), (58.4, 13.0), (59.85, 13.0), (59.85, 4.7), (64.1, 4.7), (64.1, 0), (62.9, 0), (62.9, 3.5)], float)
PT_opts_orig = PT.options
def _opts():
    d = PT_opts_orig(); d["M2b_912"] = P912; d["M2b_912"]["title"] = "M2b s DIN 912 M4x20 (hlava 4.0)"; return d
PT.options = _opts
OF.PT.options = _opts
r912 = OF.check_option("M2b_912", SW, SH, verbose=False)
OUT["M2b_with_DIN912"] = dict(fits=r912["fits"], governing=r912["governing_part_margin"],
                              drive_hub=r912["parts"]["DRV_unasac"], screw=r912["parts"]["M4_DIN912_M4x20"])
print(f"[{time.time()-T0:.0f}s]", "3.", OUT["M2b_with_DIN912"])

# ------------------------------------------------------------------ 4. shell 1.6 instead of the 1.2 rule
rM2b = OF.check_option("M2b", SW, SH, verbose=False)
sh = {}
for nm, v in rM2b["parts"].items():
    if nm.startswith("DRV_magnet"):
        continue
    wo, wi = v["wall_outer_skin"], v["wall_inner_skin"]
    slide = v["role"] in ("drive", "static")
    sh[nm] = dict(role=v["role"], clearance_to_shell1p6_outer=round(wo - 1.6, 3), clearance_to_shell1p6_inner=round(wi - 1.6, 3),
                  need=0.3 if slide else 0.0)
OUT["shell_1p6"] = sh
for k, v in sh.items():
    print("4.", k, v)

# ------------------------------------------------------------------ 5. top dome: arm top point, min skin distance above the disc
top = G.to_world(np.array([0.0, 0, 0]))
OUT["arm_top_world"] = top.round(2).tolist()
# drive hub of M2b: distance to the skin in the upper sector az 60..120
d = OF.dist_part(SW, M2b["DRV_unasac"])
m = (azS > 60) & (azS < 120)
k = np.argmin(np.where(m, d, np.inf))
OUT["drive_hub_to_top_dome"] = dict(min=round(float(d[k]), 3), at=dict(x=round(float(xS[k]), 2), r=round(float(rS[k]), 2), az=round(float(azS[k]), 1)))
dM4 = OF.dist_part(SW, M2b["M4_DIN7984_M4x20"])
OUT["screw_head_to_outer_skin"] = round(float(dM4[SH].min()), 3)
# hub-to-shell connection: overlap of the hub tube r 8.5..9.7 (x 52.8..54.7) with a 1.6 shell
hub = M2b["ARM_naboj"]
# inner skin x along the hub tube radii at every azimuth: shell interior starts 1.6 inside the skin
az = np.radians(np.arange(0, 360, 5.0))
conn = []
for r_ in (8.5, 9.1, 9.7):
    xs_ = np.arange(48.0, 60.0, 0.01)
    worst = -9
    for a in az:
        Q = np.c_[xs_, 3.0 + r_ * np.cos(a) + 0 * xs_, -17.0 + r_ * np.sin(a) + 0 * xs_]
        ins = G.inside(G.to_local(Q))
        ins16 = G.inside(G.to_local(Q), inset=1.6)
        x_skin = xs_[ins][0]; x_int = xs_[ins16][0]
        worst = max(worst, x_int)
    conn.append(dict(r=r_, shell_interior_starts_at_x_max_over_az=round(float(worst), 2), hub_tube_starts=52.8,
                     overlap_mm=round(float(worst) - 52.8, 2)))
OUT["hub_tube_shell_overlap"] = conn
print(f"[{time.time()-T0:.0f}s]", "5.", OUT["arm_top_world"], OUT["drive_hub_to_top_dome"], OUT["screw_head_to_outer_skin"], conn)

# ------------------------------------------------------------------ 6. black tip (inner half beyond the tip plane, unchanged plane)
pt = np.array([0.0, 0.0, -G.L * 0.86]); n = np.array([-0.50, -0.35, -0.79]); n /= np.linalg.norm(n)
tip = {}
for vid, ko, kw in (("0", 1.0, 1.0), ("A", 0.62, 0.95)):
    rng = np.random.default_rng(3)
    P = np.c_[rng.uniform(-13, 13, 600000), rng.uniform(-18, 18, 600000), rng.uniform(-73, -40, 600000)]
    ins = G.inside(P, ko, kw)
    inner = ins & (P[:, 0] < -0.25)
    tp = inner & ((P - pt) @ n > 0.25)
    vol_box = 26 * 36 * 33
    tip[vid] = dict(tip_volume_mm3=round(float(tp.mean() * vol_box), 0),
                    tip_extent_local=dict(x=[round(float(P[tp, 0].min()), 1), round(float(P[tp, 0].max()), 1)],
                                          y=[round(float(P[tp, 1].min()), 1), round(float(P[tp, 1].max()), 1)],
                                          z=[round(float(P[tp, 2].min()), 1), round(float(P[tp, 2].max()), 1)]),
                    outer_half_thickness_at_u0_95=round(float(ko * G.prof(0.95)[1]), 2))
OUT["black_tip"] = tip
print(f"[{time.time()-T0:.0f}s]", "6.", tip)
json.dump(OUT, open(os.path.join(HERE, "extra_A.json"), "w"), indent=1, default=float)
