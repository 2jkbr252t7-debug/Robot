"""conflict 3: REAL head (B STL vertices) vs the T4 torso top over pan x lift x tilt (numeric pre-check of K9)."""
import sys, json, math, time, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/fit")
import t4_common as C
from stlio import load_stl
T0 = time.time()
V = []
for n in ("hlava_skrupina", "ram_displeja", "displej", "usi", "led_kruzky"):
    T = load_stl(f"{C.B_STL}/{n}.stl").reshape(-1, 3)
    V.append(np.unique(np.round(T, 3), axis=0))
V = np.concatenate(V)
print("head vertices", len(V), "z min", V[:, 2].min())
# also mid-edge points of the coarse flat bottom are not needed: the head underside is densely meshed? check spacing
lowv = V[V[:, 2] < 12]
print("vertices below z 12:", len(lowv))
P, _ = C.outer_cloud()
r = np.hypot(P[:, 0], P[:, 1])
shell = P[(P[:, 2] > -30) & ~((P[:, 2] > C.TOP - 1e-6) & (r < C.R_RIM - 1e-6))]       # white surface (no collar plateau)
# shoulder joints (black, static)
th = np.linspace(0, 2 * np.pi, 180, endpoint=False)
J = []
for sx in (1, -1):
    for x in np.arange(C.X_SEAT, C.X_KLB_END + 0.01, 0.25):
        rr = 13.5 if x < C.X_SH + 3.4 else 11.0
        J.append(np.stack([np.full(180, sx * x), C.SH_Y + rr * np.cos(th), C.SH_Z + rr * np.sin(th)], 1))
shell = np.concatenate([shell] + J)
tree = cKDTree(shell)
AXZ = -3.5
B_TABLE = {20.0: (40, 40), 12.5: (30, 40), 7.5: (20, 30), 0.0: (5, 10)}       # lift: (max tilt down +, max tilt up -)


def pose(V, tilt, lift, pan):
    a = math.radians(tilt); c, s = math.cos(a), math.sin(a)
    y, z = V[:, 1], V[:, 2] - AXZ
    Q = np.stack([V[:, 0], y * c - z * s, y * s + z * c + AXZ + lift], 1)
    return C.np_rot_z(Q, pan)


def clear(tilt, lift, pan):
    Q = pose(V, tilt, lift, pan)
    Q = Q[Q[:, 2] < C.TOP + 3.0]
    if not len(Q):
        return 3.0, 3.0, None
    rq = np.hypot(Q[:, 0], Q[:, 1])
    pl = Q[rq < C.R_RIM]
    g_pl = float((pl[:, 2] - C.TOP).min()) if len(pl) else 3.0          # gap over the collar plateau (B-verified zone)
    out = Q[rq >= C.R_RIM - 0.3]
    if not len(out):
        return 3.0, g_pl, None
    d, _ = tree.query(out); k = int(d.argmin())
    inside = C.inside_outer(out[k:k + 1])[0]
    return (-float(d[k]) if inside else float(d[k])), g_pl, out[k].round(2).tolist()


REP = {"criterion": 0.5, "poses": [], "limits": {}}
PANS = list(range(-85, 86, 5))
for lift, (tdn, tup) in B_TABLE.items():
    tilts = list(range(-tup, tdn + 1, 5))
    grid = {}
    for pan in PANS:
        for t in tilts:
            g, gp, at = clear(t, lift, pan)
            grid[(pan, t)] = (g, gp, at)
    worst = min(grid.items(), key=lambda kv: kv[1][0])
    worstp = min(grid.items(), key=lambda kv: kv[1][1])
    print(f"lift {lift:4.1f}: tilt {-tup}..+{tdn}: min gap to the white shell / joints {worst[1][0]:.2f} at pan {worst[0][0]} tilt {worst[0][1]} {worst[1][2]};"
          f" min over the collar plateau {worstp[1][1]:.2f} (pan {worstp[0][0]} tilt {worstp[0][1]})")
    lim = {}
    for pan in PANS:
        dn = max([t for t in tilts if t >= 0 and all(grid[(pan, u)][0] >= 0.5 for u in tilts if 0 <= u <= t)], default=None)
        up = min([t for t in tilts if t <= 0 and all(grid[(pan, u)][0] >= 0.5 for u in tilts if t <= u <= 0)], default=None)
        lim[pan] = (dn, up)
    REP["limits"][str(lift)] = {str(p): v for p, v in lim.items()}
    REP["poses"].append(dict(lift=lift, b_table=(tdn, tup), min_gap=round(worst[1][0], 3), at_pan=worst[0][0], at_tilt=worst[0][1],
                             point=worst[1][2], min_plateau=round(worstp[1][1], 3)))
    red = {p: v for p, v in lim.items() if v != (tdn, -tup)}
    print("      pans with a reduced tilt range (down, up):", red if red else "none")
    # profile of the minimum gap vs pan at the table limits
    print("      gap at +limit by pan:", " ".join(f"{grid[(p, tdn)][0]:.1f}" for p in PANS[::2]))
    print("      gap at -limit by pan:", " ".join(f"{grid[(p, -tup)][0]:.1f}" for p in PANS[::2]))
REP["time_s"] = round(time.time() - T0, 1)
json.dump(REP, open("/tmp/claude-0/gapwf/fin/T4/fit/head_check.json", "w"), indent=1)
print("done", REP["time_s"])
