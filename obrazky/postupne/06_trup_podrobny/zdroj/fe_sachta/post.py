"""post-processing of one FE case: true-surface stresses of P_sachta and P_drziak_serva (points sampled on the STL, ~0.13 mm
spacing), per named critical spot the maximum principal stress s1 averaged over 0.4 mm (the averaging distance of the review
sachta_a/summarize_v3.py) x 1.04 (FE reproduces plain bending of 1.25-1.6 walls 2-4 % low: sachta_a/fe_test5.log), the gear bond
tractions (peel at the edge and shear, 0.6 mm average as sachta_a/post_bond.py) and the allowable by load class
(T4_zivica.md Z2: normal 8.5, abuse 12.9, unfilleted notch 4.3 / 6.45; bond 2.7)."""
import os, json, math, numpy as np
from scipy.spatial import cKDTree
import fe3d, femodel as FM

KFE = 1.04
R_AVG = 0.4
ALLOW = {"normal": (8.5, 4.3), "abuse": (12.9, 6.45), "failsafe": (25.8, 25.8)}     # (filleted, sharp notch); failsafe = lower-bound strength
BOND_ALLOW = {"normal": 2.7, "abuse": 4.0}      # LD1: nominal average shear / tension over the bonded area (epoxy 8 MPa / 3 and / 2)
BOND_EDGE_INFO = 2.7                            # the 0.6 mm edge peak is reported for information only (axial retention is positive)
CONTACT_CLEAR = 1.0                             # LD1: structure rows are taken >= 1.0 mm away from the edge of an ACTIVE contact patch


def surface_points(stl_dir, name, cache_dir, seed=1, area=0.017):
    st = FM.stl_stamp(stl_dir, (name,))
    f = os.path.join(cache_dir, f"surf_{name}_{st}.npz")
    if os.path.exists(f):
        d = np.load(f); return d["P"], d["N"]
    T = FM.read_part(stl_dir, name)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); A = 0.5 * np.linalg.norm(n, axis=1); nu = n / (2 * A[:, None] + 1e-30)
    rng = np.random.default_rng(seed)
    k = np.maximum(1, np.ceil(A / area).astype(int))
    idx = np.repeat(np.arange(len(T)), k)
    r1 = rng.random(len(idx)); r2 = rng.random(len(idx)); s = np.sqrt(r1)
    P = (1 - s)[:, None] * a[idx] + (s * (1 - r2))[:, None] * b[idx] + (s * r2)[:, None] * c[idx]
    N = nu[idx]
    os.makedirs(cache_dir, exist_ok=True)
    np.savez_compressed(f, P=P.astype(np.float32), N=N.astype(np.float32))
    return P.astype(np.float32), N.astype(np.float32)


def well_spots(P, D):
    """named critical spots of P_sachta: name -> (mask, sharp)"""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]; R = np.hypot(x, y)
    S = D.get("spots", {})
    we = S.get("win_end", dict(y=(-7.0, 3.4), z_top=-15.0)); wb = S.get("win_back", dict(x=(-20.9, -6.5), z_top=-10.9, z_sill=-40.65))
    rl = S.get("rail", dict(x=(-6.6, 16.6), z=(-41.88, -33.6)))
    sharp = S.get("sharp", ["win_end", "win_back", "corner_floor"])
    cr = np.hypot(np.abs(x) - 21.0, np.abs(y) - 8.5)
    corner = (np.abs(x) > 21) & (np.abs(y) > 8.5) & (cr >= 2.3) & (cr <= 4.0)
    we_c = (x > 22.4) & (x < 25.3) & ((np.abs(y - we["y"][1]) < 2.2) | (np.abs(y - we["y"][0]) < 2.2)) & (z > we["z_top"] - 2.4) & (z < we["z_top"] + 0.8)
    wb_c = (y > 10.9) & (y < 13.1) & ((np.abs(x - wb["x"][1]) < 2.2) | (np.abs(x - wb["x"][0]) < 2.2)) & \
           ((np.abs(z - wb["z_top"]) < 2.2) | ((z < wb["z_sill"] + 2.2) & (z > wb["z_sill"] - 0.4)))
    rail = (y > 13.0) & (z >= rl["z"][0]) & (z <= rl["z"][1]) & (x > rl["x"][0]) & (x < rl["x"][1])
    lens = (np.abs(x) <= 9.0) & (y <= -9.9) & (y >= -12.7) & (z <= -39.3) & (z >= -41.95)
    F = [
        ("lens: hub ring <-> front wall junction", lens, False),
        ("hub ring / lip (floor r <= 12.8)", (z <= -40.5) & (R <= 12.8) & (np.abs(y) < 10.6) & ~lens, False),
        ("front wall lower zone above the lens (z -39.3..-30)", (np.abs(x) <= 9.0) & (y <= -10.2) & (z > -39.3) & (z <= -30), False),
        ("back floor (r > 12.8)", (z <= -40.5) & (z >= -41.95) & (y >= 3.0) & (R > 12.8) & (y < 10.9) & (x < 22.9), False),
        ("back floor <-> back wall junction R1.0", (y >= 10.0) & (y <= 11.3) & (z >= -40.8) & (z <= -39.3) & (x > wb["x"][1] + 2.2) & (x < 19), False),
        ("corner (+X,+Y) arc <-> floor joint", (x > 21) & (y > 8.5) & (np.hypot(x - 21.0, y - 8.5) >= 1.2) & (np.hypot(x - 21.0, y - 8.5) <= 3.0) & (z >= -40.9) & (z <= -39.3), "corner_floor" in sharp),
        ("+X end-window top corners", we_c, "win_end" in sharp),
        ("back-window corners (top + sill / jamb)", wb_c, "win_back" in sharp),
        ("slim corner arcs 1.34 (z -40.2..-10.8)", corner & (z > -40.2) & (z < -10.8), False),
        ("slim corner arcs in the journal band zone", corner & (z >= -10.8) & (z < -3.4), False),
        ("+X pillar (window jamb) below the window top", (x > 22.4) & (y > we["y"][1] - 0.1) & (y < 8.5) & (z < we["z_top"] - 2.4) & (z > -40.5), False),
        ("+X end wall / lintel above the window", (x > 22.4) & (np.abs(y) < 8.5) & (z >= we["z_top"] + 0.8) & (z < -3.4), False),
        ("-X end wall", (x < -22.9) & (np.abs(y) < 8.5) & (z > -40.95) & (z < -3.4), False),
        ("front wall (rest)", (y < -10.2) & (np.abs(x) < 21) & (z > -40.95) & (z < -3.4), False),
        ("rail / ledge of the lift module (lips, groove, roots)", rail, False),
        ("F10 pads", (y > 13.0) & (z > -41.88) & (z < -3.4), False),
        ("back wall (rest)", (y > 10.3) & (y < 13.05) & (np.abs(x) < 21) & (z > -39.3) & (z < -3.4), False),
        ("drum shroud + lip + web (z < -41.9)", (z < -41.92), False),
        ("journal band (r > 25.9)", (R > 25.9) & (z >= -10.1) & (z <= -2.9), False),
        ("top plate / ribs / ring (z > -10.1)", (z > -10.1), False),
        ("thin floor 0.95 zone (FFC groove)", (x >= 15.0) & (x <= 23.5) & (y >= 3.2) & (y <= 7.3) & (z <= -40.4) & (z >= -41.7), False),
    ]
    out = {}; free = np.ones(len(P), bool)
    for name, m, shp in F:                         # priority order: a point belongs to the first spot that claims it
        mm = m & free
        if name.startswith("thin floor"):
            mm = m                                 # overlay spot (also part of the back floor)
        else:
            free &= ~m
        out[name] = (mm, bool(shp))
    return out


def pocket_spots(P, D):
    """named spots of P_drziak_serva (priority order).  rev3 round 1c: the whole part is covered (before: only the plate and the lug)"""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]; R = np.hypot(x, y)
    Lg = D["lug"]
    F = [("P_drziak_serva stop lug + low bridge (z <= -41)", (R >= Lg["r"][0] - 2.0) & (z <= -41.0) & (y > 0)),
         ("P_drziak_serva roof beam (z > -13.25)", z > -13.25),
         ("P_drziak_serva sole + high bridge (z <= -36)", (z <= -36.0) & (x <= -6.45)),
         ("P_drziak_serva F11 block + nut slot", (x > -6.45) & (x <= -2.4) & (y > 17.2) & (z >= -18.1)),
         ("P_drziak_serva turret wall around the keyhole", (x <= -6.45) & (y > 17.2)),
         ("P_drziak_serva plate (incl. fin, notch, low plate, dowel hole)", y <= 17.2)]
    out = {}; free = np.ones(len(P), bool)
    for name, m in F:
        out[name] = (m & free, False); free &= ~m
    out["P_drziak_serva (rest)"] = (free, False)
    return out


def avg_max(P, tree, v, idx, r=R_AVG, ntop=80, sign=1.0):
    if not len(idx):
        return None
    vv = sign * v[idx]
    top = idx[np.argsort(-vv)[:ntop]]
    a = np.array([np.nanmean(v[tree.query_ball_point(P[i], r)]) for i in top])
    k = int(np.nanargmax(sign * a))
    return float(a[k]), top[k], float(sign * np.nanmax(vv))


def internal_forces(m, U, body):
    b = m.bodies[m.names.index(body)]
    K0, _, _ = fe3d.element(m.h, b["nu"])
    en = b["enodes"]
    ue = np.stack([U[3 * en], U[3 * en + 1], U[3 * en + 2]], 2).reshape(len(en), 24)
    fe = ue @ K0.T
    if len(b.get("part", [])):
        fe[b["part"]] = np.einsum("nij,nj->ni", b["Kpart"], ue[b["part"]])
    fe *= b["E"]
    f = np.zeros((m.nn, 3))
    for a in range(8):
        for c in range(3):
            np.add.at(f[:, c], en[:, a], fe[:, 3 * a + c])
    return f


def bond(stage, U):
    m = stage.m; X = m.X; nb = m.node_body
    fg = internal_forces(m, U, "gear")
    ids = np.flatnonzero((nb == stage.WELL) & (np.abs(X[:, 2] - FM.Z_BOND) < 1e-6) & (np.linalg.norm(fg, axis=1) > 0) & m.bond_fn(X))
    fb = fg[ids]; A = m.h ** 2
    tz = fb[:, 2] / A; ts = np.hypot(fb[:, 0], fb[:, 1]) / A
    t = cKDTree(X[ids, :2])
    nbr = t.query_ball_point(X[ids, :2], 0.6)
    tz_s = np.array([tz[n].mean() for n in nbr]); ts_s = np.array([ts[n].mean() for n in nbr])
    k = int(np.argmax(tz_s)); ks = int(np.argmax(ts_s))
    nt = int((fb[:, 2] > 0).sum())
    return dict(n_nodes=int(len(ids)), area=round(m.bond_area, 1), Fz=round(float(fb[:, 2].sum()), 2),
                tension_area=round(nt * A, 1), tension_avg_zone=round(float(fb[fb[:, 2] > 0, 2].sum() / max(nt * A, 1e-9)), 4),
                tension_avg_all=round(float(fb[fb[:, 2] > 0, 2].sum() / max(m.bond_area, 1e-9)), 4),
                tension_sum=round(float(fb[fb[:, 2] > 0, 2].sum()), 2), mean_tension=round(float(fb[:, 2].sum() / max(m.bond_area, 1e-9)), 4),
                peel_avg06=round(float(tz_s[k]), 3), peel_at=[round(float(v), 2) for v in X[ids[k]]], peel_node=round(float(tz.max()), 3),
                shear_avg06=round(float(ts_s[ks]), 3), shear_at=[round(float(v), 2) for v in X[ids[ks]]],
                torque_z=round(float((X[ids, 0] * fb[:, 1] - X[ids, 1] * fb[:, 0]).sum()), 1),
                mean_shear=round(float(np.hypot(fb[:, 0], fb[:, 1]).sum() / max(m.bond_area, 1e-9)), 4))


def contact_rows(stage, rs, cls):
    """LD1 (a): nominal bearing pressure of every joint contact = pair force / engaged area (design.json 'bearing'), against the
    allowable of the load class; tension in an F10 screw = shear of the bonded insert (2.7 / 4.0)"""
    D = stage.D; B = D.get("bearing", {}); case = rs["case"]; pf = rs["pair_forces_on_pocket"]; rows = []
    allow = ALLOW[cls][0]

    def add(spot, F, area, note, al=allow):
        if not area or abs(F) < 0.05:
            return
        p = abs(F) / area
        rows.append(dict(spot=spot, part="joint", case=case, cls=cls, kind="contact", stress=round(p, 2), allowable=al, ok=bool(p <= al),
                         margin=round(al / p, 2), force_N=round(abs(F), 2), area_mm2=round(area, 2), at=None, note=note, sharp=False))
    g = lambda n: pf.get(n, {}).get("sum", 0.0)
    if "ledge_up_z" in B:
        add("contact: module UP stop (pocket block on the ledge rib)", g("ledge_up_z"), B["ledge_up_z"], "pair force / bearing face")
    if "shelf_dn_z" in B:
        add("contact: module DOWN stop (plate edge on the shelf)", g("shelf_dn_z"), B["shelf_dn_z"], "pair force / bearing face")
    dw = B.get("dowel")
    if dw:
        Fd = float(np.hypot(g("dowel_x"), g("dowel_z")))
        add("contact: F10 dowel D2 in the well pad (steel in resin, d x engaged length)", Fd, dw["d"] * dw["well"], f"resultant of x / z; {dw['well']} engaged")
        add("contact: F10 dowel D2 in the pocket boss (steel in resin, d x engaged length)", Fd, dw["d"] * dw["pocket"], f"{dw['pocket']} engaged")
    for nm, lab in (("rail_y", "plateau mid band"), ("padC_y", "pad C"), ("curb_y", "sill curb (sole front face, LD7)"), ("padD_y", "pad D (block front under the ledge)"), ("padE_y", "pad E (plate top, +X)")):
        if nm in B and g(nm) > 0:
            add(f"contact: pocket plate on the {lab} (y, compression only)", g(nm), B[nm], "pair force / face area")
    ins = B.get("insert"); bal = BOND_ALLOW.get(cls, 8.0)
    for nm in ("padA_y", "padB_y"):
        F = g(nm)
        if F > 0 and nm in B:
            add(f"contact: pocket plate on F10 {nm[:4]} (y, compression)", F, B[nm], "pair force / pad area")
        elif F < 0 and ins:
            add(f"contact: F10 screw tension at {nm[:4]} -> bonded M2 insert (shear of the epoxy, pi x OD x L)", F, math.pi * ins["od"] * ins["len"],
                "preload not included (K12 torque rows)", al=bal)
    st = rs["reactions"].get("stop")
    if st and "stop" in B:
        Fs = float(np.linalg.norm(st["F"]))
        add("contact: stop pin D3 on the lug face (projected d x engaged length)", Fs, B["stop"]["d"] * B["stop"]["engaged"], "pin force from the FE")
    rec = next((l for l in rs["log"] if isinstance(l, dict) and "R_key" in l), None)
    if rec and "keyhole" in B:
        add("contact: MG90S boss in the keyhole (d x wall)", rec["R_key"], B["keyhole"]["d"] * B["keyhole"]["t"],
            "pin force on the keyhole; the couple about y goes along x (R3 SERVO_SEAT)" if rec.get("seat") else "servo lever: pin x -18.65, keyhole x -7.5, tab x -3.3")
        T = rec.get("T_x"); es = B.get("endstop"); f11 = B.get("f11")
        if T and rec["pocket"] > 0 and f11:            # L1: F11 tension + case corner on the turret wall
            add("contact: F11 nut on the +X wall of its slot (L1 couple, screw tension)", T, f11["nut_area"], f"T = Fz x {f11['arm_pin']} / {rec.get('arm_z')}")
        elif T and es:                                 # L2: tab on the block + case end on the proud dowel end
            dw_ = B["dowel"]
            add("contact: MG90S tab on the block face (L2 couple)", T, es["tab_area"], f"T = Fz x {B['f11']['arm_pin']} / {rec.get('arm_z')}")
            add("contact: MG90S case end on the proud end of the F10 dowel (steel, d x proud)", T, es["d"] * es["proud"],
                f"gap {es['gap']} nominal; bought servo case (nylon) on a steel pin")
            add("contact: F10 dowel in the plate hole under the L2 end-stop force (d x 2.0)", T, es["d"] * dw_["pocket"], "plate 2.0")
            Mpry = T * es["lever"]; ppry = 6.0 * Mpry / (es["d"] * dw_["well"] ** 2)
            rows.append(dict(spot="contact: F10 dowel prying in the well pad under the L2 end-stop couple (6 M / (d L^2))", part="joint", case=case, cls=cls, kind="contact",
                             stress=round(ppry, 2), allowable=allow, ok=bool(ppry <= allow), margin=round(allow / ppry, 2), force_N=round(T, 2),
                             area_mm2=None, at=None, sharp=False, note=f"M = T x {es['lever']} = {Mpry:.1f} N.mm over the bonded depth {dw_['well']}"))
        elif not rec.get("seat"):                      # rev. 2 description (vertical lever)
            if rec["R_tab"] > 0 and "seat" in B:
                add("contact: MG90S case end on the block underside (L2 seat)", rec["R_tab"], B["seat"]["area"], "vertical lever (rev. 2 model)")
    return rows


def evaluate(stage, U, rs, stl_dir, cache_dir, out_dir, save_surf=True):
    """rows for results.json.  kind 'structure': one per (spot, case), max principal stress (0.4 average x 1.04) of the surface points
    that are >= CONTACT_CLEAR (+ h / 2) away from every node of an ACTIVE joint contact (LD1 b); the peak inside the contact zone is
    kept as 'contact_zone_peak' (information, mesh dependent).  kind 'contact': nominal bearing pressures (LD1 a).  kind 'bond'."""
    m = stage.m; D = stage.D; case = rs["case"]; cls = rs["spec"]["cls"]
    cz = [v for v in getattr(stage, "contact_pts", {}).values() if len(v)]
    ctree = cKDTree(np.vstack(cz).astype(np.float64)) if cz else None
    rows = []
    for body, part, spot_fn in (("well", "P_sachta", well_spots), ("pocket", "P_drziak_serva", pocket_spots)):
        P, N = surface_points(stl_dir, part, cache_dir)
        P = P.astype(np.float64); N = N.astype(np.float64)
        sig, ok, el = fe3d.point_stress_fc(m, U, body, P, N)
        s1, s2, s3, vm = fe3d.principal(np.nan_to_num(sig))
        s1[~ok] = np.nan; s3[~ok] = np.nan
        near = np.zeros(len(P), bool)
        if ctree is not None:
            dd, _ = ctree.query(P, distance_upper_bound=CONTACT_CLEAR + 0.5 * m.h + 1e-9)
            near = np.isfinite(dd)
        s1f = s1.copy(); s1f[near] = np.nan; s3f = s3.copy(); s3f[near] = np.nan
        tree = cKDTree(P)
        for name, (msk, sharp) in spot_fn(P, D).items():
            idx = np.flatnonzero(msk & ok & ~near)
            r = avg_max(P, tree, s1f, idx)
            if r is None:
                continue
            a, i, raw = r
            allow = ALLOW[cls][1 if sharp else 0]
            stress = KFE * a
            rc = avg_max(P, tree, s3f, idx, sign=-1.0)
            pk = avg_max(P, tree, s1, np.flatnonzero(msk & ok & near))
            rows.append(dict(spot=name, part=part, case=case, cls=cls, kind="structure", stress=round(stress, 2), raw_max=round(raw, 2), allowable=allow,
                             sharp=sharp, ok=bool(stress <= allow), margin=round(allow / stress, 2) if stress > 0 else None,
                             at=[round(float(v), 2) for v in P[i]], s3_avg=round(KFE * rc[0], 2), n_pts=int(len(idx)),
                             contact_zone_peak=round(KFE * pk[0], 2) if pk else None,
                             contact_zone_at=[round(float(v), 2) for v in P[pk[1]]] if pk else None))
        if save_surf and body == "well":
            np.savez_compressed(os.path.join(out_dir, case + "_surf.npz"), s1=s1.astype(np.float32), s3=s3.astype(np.float32))
    rows += contact_rows(stage, rs, cls)
    if stage.GEAR >= 0 and not stage.nobond:
        b = bond(stage, U)
        rs["bond"] = b
        al = BOND_ALLOW.get(cls, 2.7)
        for nm, key, info, at in (("gear bond: average tension over the tensile part of the bonded area", "tension_avg_zone", "peel_avg06", "peel_at"),
                                  ("gear bond: average shear over the bonded area", "mean_shear", "shear_avg06", "shear_at")):
            v = max(b[key], 0.0)
            rows.append(dict(spot=nm, part="bond", case=case, cls=cls, kind="bond", stress=round(v, 3), allowable=al, sharp=False, ok=bool(v <= al),
                             margin=round(al / v, 2) if v > 0 else None, at=b[at], edge_peak_06=b[info],
                             note="LD1: nominal value is the acceptance; the 0.6 mm edge peak (edge_peak_06) is information only"))
    rs["rows"] = rows
    json.dump(rs, open(os.path.join(out_dir, case + ".json"), "w"), indent=1, default=float)
    return rows
