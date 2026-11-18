"""load cases on the pan stage model (fe_build): L1 x 2, L2 (lift 0 chain / landed / lift 20), L8 stall into the stops,
L3 hand twist, lateral head force (per 10 N, lift 0 / 20, 4 directions).  Supports by penalty springs: journal band
(radial, compression only), pivot = gear bore on T_cap (radial, compression only), washer (gear top r <= 4.5, +z only) or PTFE
washer (gear bottom r 5..12, -z only), pinion (tangential at the mesh) or stop pin (tangential on the lug face).
Run: python fe_cases.py [case names]  -> res/<case>.npz (U float32, reactions, active sets)"""
import os, sys, json, math, time, numpy as np
import scipy.sparse as sp
import fe3d, fe_build as FB

os.makedirs("res", exist_ok=True)
PAN_AZ = 254.286                       # pinion direction from the pan axis (stage frame, pan 0)
R_PITCH = 14.4
X_PIN, Y_PIN, Z_PIN0 = -18.65, 23.2, -34.2      # crank pin contact in the ear plate (x), crank axis y, slot centre at rest
NECK_LOW0 = -35.5                      # lowest z of the full neck section (lift 0)
STRIP_TOP = -6.0
NECK_STEP0 = -11.0                     # neck full width (x +-22.5) ends here at lift 0
Z_HEAD = 50.0                          # assumed height of a lateral knock on the head (head shell z 7 .. 86)

m = FB.build()
X = m.X; nb = m.node_body
R = np.hypot(X[:, 0], X[:, 1]); AZ = np.degrees(np.arctan2(X[:, 1], X[:, 0])) % 360
WELL, GEAR, POCK = 0, 1, 2


def sel(cond):
    return np.flatnonzero(cond)


def unit_radial(ids):
    d = np.zeros((len(ids), 3)); d[:, 0] = X[ids, 0] / R[ids]; d[:, 1] = X[ids, 1] / R[ids]; return d


def unit_tang(ids):
    d = np.zeros((len(ids), 3)); d[:, 0] = -X[ids, 1] / R[ids]; d[:, 1] = X[ids, 0] / R[ids]; return d


def ez(n, s=1.0):
    d = np.zeros((n, 3)); d[:, 2] = s; return d


# ---- support node sets
J_ids = sel((nb == WELL) & (R >= 25.9) & (X[:, 2] >= -10.1) & (X[:, 2] <= -2.9))
PIV_ids = sel((nb == GEAR) & (R <= 4.25))
WASH_ids = sel((nb == GEAR) & (np.abs(X[:, 2] + 41.9) < 1e-6) & (R <= 4.7))
PTFE_ids = sel((nb == GEAR) & (np.abs(X[:, 2] + 45.9) < 1e-6) & (R >= 5.0) & (R <= 12.0))
print("support nodes: journal", len(J_ids), "pivot", len(PIV_ids), "washer", len(WASH_ids), "ptfe", len(PTFE_ids))


def mesh_ids(az):
    da = (AZ - az + 180) % 360 - 180
    return sel((nb == GEAR) & (R >= 13.4) & (np.abs(da) <= 8.0))


def lug_ids(face):
    a = 118.3 if face == "cw" else 131.7
    da = (AZ - a + 180) % 360 - 180
    side = (da >= -0.1) & (da <= 1.2) if face == "cw" else (da <= 0.1) & (da >= -1.2)
    return sel((nb == POCK) & side & (R >= 27.8) & (R <= 31.6) & (X[:, 2] <= -44.6) & (X[:, 2] >= -47.3))


# ---- load helpers
def spread(F, ids, vec):
    vec = np.asarray(vec, float)
    if len(ids) == 0:
        raise RuntimeError("empty load set")
    for c in range(3):
        F[3 * ids + c] += vec[c] / len(ids)


def land_nodes(wall, z0, z1):
    zc = (X[:, 2] >= z0 - 1e-6) & (X[:, 2] <= z1 + 1e-6) & (nb == WELL)
    if wall == "front":      # strips x 13.5..16.5 and -16.5..-13.5, face y -10.3
        return [sel(zc & (X[:, 1] >= -10.55) & (X[:, 1] <= -9.95) & (np.abs(X[:, 0]) >= 13.4) & (np.abs(X[:, 0]) <= 16.6) & (np.sign(X[:, 0]) == s)) for s in (1, -1)]
    if wall == "front+":
        return [sel(zc & (X[:, 1] >= -10.55) & (X[:, 1] <= -9.95) & (X[:, 0] >= 13.4) & (X[:, 0] <= 16.6))]
    if wall == "front-":
        return [sel(zc & (X[:, 1] >= -10.55) & (X[:, 1] <= -9.95) & (X[:, 0] <= -13.4) & (X[:, 0] >= -16.6))]
    if wall == "back":       # strip x 10.5..14.5 (z -37..-6) + back_up x -16.5..-13.5 (z -10.2..-6)
        out = [sel(zc & (X[:, 1] >= 9.95) & (X[:, 1] <= 10.55) & (X[:, 0] >= 10.4) & (X[:, 0] <= 14.6))]
        up = sel(zc & (X[:, 1] >= 9.95) & (X[:, 1] <= 10.55) & (X[:, 0] <= -13.4) & (X[:, 0] >= -16.6) & (X[:, 2] >= -10.2))
        if len(up):
            out.append(up)
        return out
    if wall == "back+":
        return [sel(zc & (X[:, 1] >= 9.95) & (X[:, 1] <= 10.55) & (X[:, 0] >= 10.4) & (X[:, 0] <= 14.6))]
    if wall == "back-":
        return [sel(zc & (X[:, 1] >= 9.95) & (X[:, 1] <= 10.55) & (X[:, 0] <= -13.4) & (X[:, 0] >= -16.6) & (X[:, 2] >= -10.2))]
    if wall == "-X":         # strips y +-(5.15..8.15), face x -22.8
        return [sel(zc & (X[:, 0] <= -22.75) & (X[:, 0] >= -23.25) & (np.abs(X[:, 1]) >= 5.05) & (np.abs(X[:, 1]) <= 8.25) & (np.sign(X[:, 1]) == s)) for s in (1, -1)]
    if wall == "+X":         # one strip y 5.15..8.15
        return [sel(zc & (X[:, 0] >= 22.75) & (X[:, 0] <= 23.25) & (X[:, 1] >= 5.05) & (X[:, 1] <= 8.25))]
    raise ValueError(wall)


def land_force(F, wall, z0, z1, vec, log):
    groups = land_nodes(wall, z0, z1)
    groups = [g for g in groups if len(g)]
    for g in groups:
        spread(F, g, np.asarray(vec, float) / len(groups))
    log.append(dict(wall=wall, z=(z0, z1), F=list(np.round(vec, 2)), nodes=[len(g) for g in groups]))


def pocket_pin_force(F, Fz, z_pin, log):
    """vertical crank-pin force Fz (N, on the stage) at x -18.65, y 23.2: MG90S case lever between the keyhole (x -7.5) and
    the F11 tab block (x -2.5)"""
    x_key, x_tab = -7.5, -2.5
    Rk = Fz * (X_PIN - x_tab) / (x_key - x_tab); Rt = Fz - Rk
    dk = np.hypot(X[:, 1] - 23.2, X[:, 2] + 24.2)
    half = (X[:, 2] > -24.2) if Fz > 0 else (X[:, 2] < -24.2)
    k_ids = sel((nb == POCK) & (X[:, 0] >= -8.6) & (X[:, 0] <= -6.4) & (dk >= 5.6) & (dk <= 6.6) & half)
    # Rk acts on the keyhole half facing the force; Rt on the F11 block around the hole
    t_ids = sel((nb == POCK) & (X[:, 0] >= -8.6) & (X[:, 0] <= -2.4) & (np.hypot(X[:, 1] - 23.2, X[:, 2] + 15.85) <= 2.6))
    spread(F, k_ids, (0, 0, Rk)); spread(F, t_ids, (0, 0, Rt))
    log.append(dict(pocket_pin=Fz, R_key=round(Rk, 2), R_tab=round(Rt, 2), n_key=len(k_ids), n_tab=len(t_ids), z_pin=z_pin))


from scipy.optimize import nnls


def group(ids, d):
    d = np.asarray(d, float); d = d / np.linalg.norm(d)
    c = X[ids].mean(0)
    return dict(ids=ids, d=d, c=c)


def solve_groups(groups, Ft, Mt, F, log, tag, signed=False):
    """magnitudes f_i (>= 0 unless signed) of the groups so that sum f_i d_i = Ft and sum f_i c_i x d_i = Mt; then load F"""
    A = np.array([np.concatenate([g["d"], np.cross(g["c"], g["d"])]) for g in groups]).T
    b = np.concatenate([Ft, Mt])
    if signed:
        f, *_ = np.linalg.lstsq(A, b, rcond=None)
    else:                       # least-norm non-negative solution (even sharing between equivalent strips)
        w = 1.0e4
        f, rn = nnls(np.vstack([w * A, np.eye(A.shape[1])]), np.concatenate([w * b, np.zeros(A.shape[1])]))
    res = A @ f - b
    for g, fi in zip(groups, f):
        spread(F, g["ids"], fi * g["d"])
    log.append(dict(tag=tag, f=[round(float(v), 2) for v in f], centroids=[[round(float(v), 2) for v in g["c"]] for g in groups],
                    residual=[round(float(v), 3) for v in res]))
    return f, res


def strip_groups(wall, z0, z1):
    """one group per strip of a wall in the z window, direction = outward (neck pushes the wall)"""
    out = {"front": (0, -1, 0), "back": (0, 1, 0), "-X": (-1, 0, 0), "+X": (1, 0, 0)}[wall]
    gs = []
    for ids in land_nodes(wall, z0, z1):
        if len(ids):
            gs.append(group(ids, out))
    return gs


def pocket_groups(Fz, F, log):
    """pin force Fz (on the stage, vertical) at (x -18.65, y 23.2): keyhole half + F11 block, magnitudes by least squares"""
    dk = np.hypot(X[:, 1] - 23.2, X[:, 2] + 24.2)
    half = (X[:, 2] > -24.2) if Fz > 0 else (X[:, 2] < -24.2)
    k_ids = sel((nb == POCK) & (X[:, 0] >= -8.6) & (X[:, 0] <= -6.4) & (dk >= 5.6) & (dk <= 6.6) & half)
    t_ids = sel((nb == POCK) & (X[:, 0] >= -4.2) & (X[:, 0] <= -2.4) & (np.hypot(X[:, 1] - 23.2, X[:, 2] + 15.85) <= 2.6))
    gs = [group(k_ids, (0, 0, 1)), group(t_ids, (0, 0, 1))]
    A = np.array([[1.0, 1.0], [gs[0]["c"][0], gs[1]["c"][0]]]); b = np.array([Fz, X_PIN * Fz])
    f = np.linalg.solve(A, b)
    for g, fi in zip(gs, f):
        spread(F, g["ids"], fi * g["d"])
    Mp = sum(fi * np.cross(g["c"], g["d"]) for g, fi in zip(gs, f))
    log.append(dict(pocket=Fz, R_key=round(float(f[0]), 2), R_tab=round(float(f[1]), 2), c_key=[round(float(v), 2) for v in gs[0]["c"]],
                    c_tab=[round(float(v), 2) for v in gs[1]["c"]], M_pocket=[round(float(v), 1) for v in Mp]))
    return Mp


def lift_case(F, Fhead, lift, log):
    Mp = pocket_groups(Fhead, F, log)
    zl = NECK_LOW0 + lift
    zux = min(NECK_STEP0 + lift, STRIP_TOP); zuy = STRIP_TOP
    up = Fhead > 0          # L1: neck pushes front + +X at the bottom, back + -X at the top
    gs = []
    gs += strip_groups("front" if up else "back", zl, zl + 1.0)
    gs += strip_groups("back" if up else "front", zuy - 1.0, zuy)
    gs += strip_groups("+X" if up else "-X", zl, zl + 1.0)
    gs += strip_groups("-X" if up else "+X", zux - 1.0, zux)
    # stage total must be Fhead along the axis: lands supply -Mp (pocket force sits at the pin, head force on the axis)
    solve_groups(gs, np.zeros(3), -Mp, F, log, f"lands lift {lift}")
    log.append(dict(lift=lift, z_low=zl, zux=zux, zuy=zuy))


def lateral_case(F, Fl, dirn, lift, log):
    zl = NECK_LOW0 + lift
    s = 1.0 if dirn[0] == "+" else -1.0
    v = np.array([s, 0, 0]) if dirn[1] == "X" else np.array([0, s, 0])
    if dirn[1] == "Y":
        zu = STRIP_TOP
        gs = strip_groups("back" if s > 0 else "front", zu - 1.0, zu) + strip_groups("front" if s > 0 else "back", zl, zl + 1.0)
    else:
        zu = min(NECK_STEP0 + lift, STRIP_TOP)
        gs = strip_groups("+X" if s > 0 else "-X", zu - 1.0, zu) + strip_groups("-X" if s > 0 else "+X", zl, zl + 1.0)
        # a single +X strip: allow the front / back strips at mid height to take the twist (Mz) - add both, small
        gs += strip_groups("front", -7.0, -6.0) + strip_groups("back", -7.0, -6.0)
    rh = np.array([0, 0, Z_HEAD])
    solve_groups(gs, Fl * v, np.cross(rh, Fl * v), F, log, f"lateral {dirn} lift {lift}")
    log.append(dict(lateral=Fl, dir=dirn, lift=lift, z_low=zl, z_up=zu))


def twist_case(F, T, lift, log):
    zl = NECK_LOW0 + lift
    if T > 0:
        gs = strip_groups("back", zl, STRIP_TOP)[:1] + [g for g in strip_groups("front", zl, STRIP_TOP) if g["c"][0] < 0]
    else:
        gs = [g for g in strip_groups("front", -10.2, STRIP_TOP) if g["c"][0] > 0] + [g for g in strip_groups("back", -10.2, STRIP_TOP) if g["c"][0] < 0]
    solve_groups(gs, np.zeros(3), np.array([0, 0, T]), F, log, f"twist {T}", signed=False)
    log.append(dict(twist=T, lift=lift))


def gear_torque(F, T, pan, log):
    """servo torque T (N.mm on the stage, + CCW) applied as tangential tooth force at the mesh (pitch r 14.4) + radial 20 deg"""
    az = (PAN_AZ - pan) % 360
    ids = mesh_ids(az)
    a = math.radians(az); t = np.array([-math.sin(a), math.cos(a), 0.0]); r = np.array([math.cos(a), math.sin(a), 0.0])
    Ft = T / R_PITCH
    spread(F, ids, Ft * t - abs(Ft) * math.tan(math.radians(20)) * r)
    log.append(dict(gear_torque=T, mesh_az=round(az, 2), Ft=round(Ft, 2), nodes=len(ids)))


CASES = {
    "L1_lift0": dict(kind="lift", F=30.0, lift=0.0, axial="washer"),
    "L1_lift20": dict(kind="lift", F=30.0, lift=20.0, axial="washer"),
    "L2_lift20": dict(kind="lift", F=-30.0, lift=20.0, axial="ptfe"),
    "L2_lift0_chain": dict(kind="lift", F=-30.0, lift=0.0, axial="ptfe"),
    "L2_lift0_landed": dict(kind="landed", F=-30.0, axial="ptfe"),
    "L8_stop_m90": dict(kind="stop", T=-880.0, pan=-90.0),
    "L8_stop_p90": dict(kind="stop", T=880.0, pan=90.0),
    "L3_twist_ccw": dict(kind="twist", T=600.0, lift=0.0),
    "L3_twist_cw": dict(kind="twist", T=-600.0, lift=0.0),
    "L3_twist_ccw_l20": dict(kind="twist", T=600.0, lift=20.0),
}
for lift in (0.0, 20.0):
    for d in ("+Y", "-Y", "+X", "-X"):
        CASES[f"LAT{d}_l{int(lift)}"] = dict(kind="lateral", F=10.0, dir=d, lift=lift)

K_J, K_PIV, K_WASH, K_PTFE, K_PIN, K_STOP, K_WEAK = 500.0, 500.0, 2000.0, 300.0, 20000.0, 10000.0, 50.0


def run(name):
    c = CASES[name]; log = []
    F = np.zeros(3 * m.nn)
    pinion = True; stop = None
    if c["kind"] == "lift":
        lift_case(F, c["F"], c["lift"], log)
    elif c["kind"] == "landed":
        ids = sel((nb == WELL) & (X[:, 2] >= -40.85) & (X[:, 2] <= -40.45) & (R >= 6.6) & (R <= 12.5) & (np.abs(X[:, 0]) <= 22.3) & (np.abs(X[:, 1]) <= 9.8))
        spread(F, ids, (0, 0, c["F"])); log.append(dict(landed=c["F"], nodes=len(ids)))
    elif c["kind"] == "stop":
        gear_torque(F, c["T"], c["pan"], log); pinion = False; stop = "cw" if c["T"] < 0 else "ccw"
    elif c["kind"] == "twist":
        twist_case(F, c["T"], c["lift"], log)
    elif c["kind"] == "lateral":
        lateral_case(F, c["F"], c["dir"], c["lift"], log)
    Fsum = F.reshape(-1, 3).sum(0); Msum = np.cross(X, F.reshape(-1, 3)).sum(0)
    log.append(dict(F_applied=list(np.round(Fsum, 3)), M_applied=list(np.round(Msum, 1))))
    # spring sets: (name, ids, dirs, k_per_node, kind) kind: 'both', 'pos' (active when u.d > 0), 'neg' (active when u.d < 0)
    S = [("journal", J_ids, unit_radial(J_ids), K_J, "both"),
         ("pivot", PIV_ids, unit_radial(PIV_ids), K_PIV, "both")]
    ax = c.get("axial", "both")
    if ax in ("washer", "both"):
        S.append(("washer", WASH_ids, ez(len(WASH_ids)), K_WASH, "both"))
    if ax in ("ptfe", "both"):
        S.append(("ptfe", PTFE_ids, ez(len(PTFE_ids)), K_PTFE, "both"))
    if ax == "both":
        S = [s if s[0] not in ("washer", "ptfe") else (s[0], s[1], s[2], s[3] * (K_WEAK / (s[3] * len(s[1]))), "both") for s in S]
    if pinion:
        ids = mesh_ids(PAN_AZ % 360); S.append(("pinion", ids, unit_tang(ids), K_PIN / len(ids), "both"))
    if stop:
        ids = lug_ids(stop); S.append(("stop", ids, unit_tang(ids), K_STOP / len(ids), "both"))
    active = [np.ones(len(s[1]), bool) for s in S]
    if not hasattr(m, "ml"):
        ids = mesh_ids(PAN_AZ % 360)
        pre = [(J_ids, unit_radial(J_ids), K_J), (PIV_ids, unit_radial(PIV_ids), K_PIV), (WASH_ids, ez(len(WASH_ids)), K_WASH),
               (PTFE_ids, ez(len(PTFE_ids)), K_PTFE), (ids, unit_tang(ids), K_PIN / len(ids))]
        fe3d.build_precond(m, pre)
    U = None
    for it in range(3):
        springs = [(s[1][a], s[2][a], s[3]) for s, a in zip(S, active)]
        U = fe3d.solve_pcg(m, F, springs, x0=U, tol=1e-6, maxiter=800)
        changed = 0; reac = {}
        for i, s in enumerate(S):
            u = U.reshape(-1, 3)[s[1]]; ud = (u * s[2]).sum(1)
            if s[4] == "pos":
                new = ud > 0
            elif s[4] == "neg":
                new = ud < 0
            else:
                new = np.ones(len(ud), bool)
            if it == 0 and s[4] != "both":
                new = new | False
            changed += int((new != active[i]).sum()); active[i] = new
            f = -(s[3] * ud[new])[:, None] * s[2][new]          # force of the spring on the stage
            reac[s[0]] = dict(F=list(np.round(f.sum(0), 2)), n_active=int(new.sum()), n=len(s[1]))
        print(f"  {name} it {it}: changed {changed}", flush=True)
        if changed == 0:
            break
    tot = sum(np.array(v["F"]) for v in reac.values())
    log.append(dict(reactions=reac, reaction_sum=list(np.round(tot, 2))))
    np.savez_compressed(f"res/{name}.npz", U=U.astype(np.float32))
    json.dump(dict(case=name, spec=c, log=log, iterations=it + 1, amg_res=float(m.last_res[-1] / m.last_res[0])), open(f"res/{name}.json", "w"), indent=1, default=float)
    print(name, json.dumps(log, default=float)[:1500], flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or list(CASES)
    for n in names:
        t0 = time.time(); run(n); print(f"== {n} done {time.time() - t0:.0f} s", flush=True)
