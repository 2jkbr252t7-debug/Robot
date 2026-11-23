"""load cases, supports and contacts of the pan stage FE (see femodel.py).  One process = one case:
    python cases.py --stl DIR --h 0.4 --design current --out res/<tag> CASE [--nobond]
writes <out>/<case>.json (reactions, contact forces, convergence) and <out>/<case>.npz (U float32)."""
import os, sys, json, time, math, argparse
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from scipy.optimize import nnls
import femodel as FM, fe_design as FD
import fe3d

PAN_AZ = 254.286                       # pinion direction from the pan axis (stage frame, pan 0)
R_PITCH = 14.4
NECK_LOW0 = -35.5                      # lowest z of the full neck section (lift 0)
STRIP_TOP = -6.0
NECK_STEP0 = -11.0                     # neck full width (x +-22.5) ends here at lift 0
ZC = 3.0                               # collar-disc guide height (lift 20): see sachta_a/fe_cases_v3.py
GAP_J = 0.145                          # radial play of the taped journal band in the T_stred bore (K5)
T_STALL = 216.0                        # MG90S stall torque N.mm (h03_toggle)
# penalty stiffness (N/mm per node unless noted) - as sachta_a
K_JG, K_PIV, K_WASH, K_PTFE, K_PIN, K_STOP, K_WEAK = 40.0, 500.0, 2000.0, 300.0, 20000.0, 10000.0, 50.0

# load classes (lead decision LD2, opravy3.md): L1 (15 N x 2 up) / L2 (30 N down) are NORMAL use (8.5) at the parked neck (lift 0-2);
# with the neck extended the same forces are ABUSE (12.9) - firmware parks the neck when idle / before power-off, "carry the robot by
# the torso"; normal use at the extended neck = one third (5 N up / 10 N down), covered by linear scaling (12.9 / 3 = 4.3 <= 8.5).
# The pan servo stalling into a hard stop is a FAULT (firmware range +-85, stops +-90) = abuse; L3 hand twist = abuse.
CASES = {
    "L1_lift0": dict(kind="lift", F=30.0, lift=0.0, axial="washer", cls="normal"),
    "L1_lift20c": dict(kind="lift_collar", F=30.0, lift=20.0, axial="washer", cls="abuse"),
    "L2_lift0_chain": dict(kind="lift", F=-30.0, lift=0.0, axial="ptfe", cls="normal"),
    "L2_lift0_landed": dict(kind="landed", F=-30.0, axial="ptfe", cls="normal"),
    "L2_lift10": dict(kind="lift", F=-30.0, lift=10.0, axial="ptfe", cls="abuse"),
    "L2_lift20c": dict(kind="lift_collar", F=-30.0, lift=20.0, axial="ptfe", cls="abuse"),
    "L3_twist_ccw": dict(kind="twist", T=600.0, lift=0.0, cls="abuse"),
    "L3_twist_cw": dict(kind="twist", T=-600.0, lift=0.0, cls="abuse"),
    "L8_stop_p90": dict(kind="stop", T=880.0, pan=90.0, cls="abuse"),
    "L8_stop_m90": dict(kind="stop", T=-880.0, pan=-90.0, cls="abuse"),
    # fail-safe case (R3-2): the gear bond has failed completely, the robot is lifted by the head (the gear is left out)
    "L1_lift20c_nobond": dict(kind="lift_collar", F=30.0, lift=20.0, axial="washer", cls="failsafe", nobond=True),
    "L1_lift0_nobond": dict(kind="lift", F=30.0, lift=0.0, axial="washer", cls="failsafe", nobond=True),
    # extra (sachta_a names) for the validation against results_v4.json
    "L1_lift20": dict(kind="lift", F=30.0, lift=20.0, axial="washer", cls="normal"),
}
ACCEPT = ["L1_lift0", "L1_lift20c", "L2_lift0_chain", "L2_lift0_landed", "L2_lift10", "L2_lift20c", "L3_twist_ccw", "L3_twist_cw",
          "L8_stop_p90", "L8_stop_m90"]


def in_shape(shape, x, z):
    k = shape[0]
    if k == "circle":
        _, cx, cz, ro, ri = shape
        r = np.hypot(x - cx, z - cz); return (r <= ro + 1e-6) & (r >= ri - 1e-6)
    if k == "box":
        _, x0, x1, z0, z1 = shape
        return (x >= x0 - 1e-6) & (x <= x1 + 1e-6) & (z >= z0 - 1e-6) & (z <= z1 + 1e-6)
    if k == "stadium":
        _, cx, z0, z1, r = shape
        return np.hypot(x - cx, z - np.clip(z, z0, z1)) <= r + 1e-6
    raise ValueError(k)


def face_mask(face, x, z):
    m = in_shape(face["shape"], x, z)
    for s in face.get("plus", []):
        m |= in_shape(s, x, z)
    for s in face.get("minus", []):
        m &= ~in_shape(s, x, z)
    return m


class Stage:
    def __init__(self, stl_dir, h, design, cache, nobond=False, collar=True, log=print):
        self.D = D = design; self.log = log; self.h = h; self.nobond = nobond; self.collar = collar
        self.m = m = FM.build(stl_dir, h, cache, bonded=not nobond, with_gear=not nobond, with_collar=collar, log=log)
        self.X = X = m.X; self.nb = nb = m.node_body
        self.R = np.hypot(X[:, 0], X[:, 1]); self.AZ = np.degrees(np.arctan2(X[:, 1], X[:, 0])) % 360
        self.WELL = m.names.index("well"); self.POCK = m.names.index("pocket")
        self.GEAR = m.names.index("gear") if "gear" in m.names else -1
        R = self.R
        self.J_ids = np.flatnonzero((nb == self.WELL) & (R >= 25.9) & (X[:, 2] >= -10.1) & (X[:, 2] <= -2.9))
        self.PIV_ids = np.flatnonzero((nb == self.GEAR) & (R <= 4.25))
        zp = self._layer(-45.9)                 # gear bottom face (lattice plane at h 0.4; nearest node layer otherwise)
        self.PTFE_ids = np.flatnonzero((nb == self.GEAR) & (np.abs(X[:, 2] - zp) < 1e-6) & (R >= 5.0) & (R <= 12.0))
        ax = D["axial"]
        if ax["kind"] == "gear_top":
            self.WASH_ids = np.flatnonzero((nb == self.GEAR) & (np.abs(X[:, 2] - FM.Z_BOND) < 1e-6) & (R <= ax["r_max"]))
        else:                                   # retention washer on the well's inner lip (top face z)
            zl = self._layer(ax["z"])
            self.WASH_ids = np.flatnonzero((nb == self.WELL) & (np.abs(X[:, 2] - zl) < 1e-6) & (R >= ax["r"][0] - 0.3 * h) & (R <= ax["r"][1] + 0.3 * h))
            self.LIP_ids = np.flatnonzero((nb == self.WELL) & (R <= ax["r"][0] + 0.75 * h) & (X[:, 2] <= ax["z"] + 1e-6))
        # ---- module joint: coincident nodes well <-> pocket
        A, B = FM.coincident(m, "well", "pocket"); P = X[A]
        self.k_pair = 2.0 * FM.E_RESIN * h
        pairs = []
        on_face = np.abs(P[:, 1] - FM.Y_PAD) < 1e-6
        for f in D["faces"]:
            msk = on_face & face_mask(f, P[:, 0], P[:, 2])
            pairs.append((f["name"], A[msk], B[msk], (0, 1, 0), f["kind"]))
        for t in D["tongues"]:
            tb = (P[:, 0] >= t["x"][0]) & (P[:, 0] <= t["x"][1]) & (P[:, 1] >= t["y"][0]) & (P[:, 1] <= t["y"][1])
            for nm, zf, kind in ((t["name"] + "_up_z", t["z_up"], "pos"), (t["name"] + "_lo_z", t["z_lo"], "neg")):
                zl = self._nearest_layer(P[tb, 2], zf)
                msk = tb & (np.abs(P[:, 2] - zl) < 1e-6)
                pairs.append((nm, A[msk], B[msk], (0, 0, 1), kind))
            xe = t.get("x_end")                 # round +X end of the tongue in the round groove end: +x stop with a gap (normal = radial)
            if xe:
                rr = np.hypot(P[:, 0] - xe["xc"], P[:, 2] - xe["zc"])
                msk = (P[:, 1] >= t["y"][0]) & (P[:, 1] <= t["y"][1]) & (P[:, 0] >= xe["xc"] + 0.5 * xe["r"]) & (np.abs(rr - xe["r"]) <= 0.75 * h)
                dn = np.stack([(P[msk, 0] - xe["xc"]) / rr[msk], 0 * rr[msk], (P[msk, 2] - xe["zc"]) / rr[msk]], 1)
                pairs.append((t["name"] + "_xend", A[msk], B[msk], dn, "pos", xe["gap"]))
        for zs in D.get("zstops", []):        # rev3: vertical stops of the lift module with a gap (ledge rib above the block, floor below the plate)
            zb = (P[:, 0] >= zs["x"][0] - 1e-6) & (P[:, 0] <= zs["x"][1] + 1e-6) & (P[:, 1] >= zs["y"][0] - 1e-6) & (P[:, 1] <= zs["y"][1] + 1e-6) & (np.abs(P[:, 2] - zs["z"]) <= 1.01 * h)
            zl = self._nearest_layer(P[zb, 2], zs["z"])
            msk = zb & (np.abs(P[:, 2] - zl) < 1e-6)
            pairs.append((zs["name"], A[msk], B[msk], (0, 0, 1), zs["kind"], zs["gap"]))
        dw = D["dowel"]
        dm = (np.hypot(P[:, 0] - dw["c"][0], P[:, 2] - dw["c"][1]) <= dw["r"]) & (P[:, 1] >= dw["y"][0]) & (P[:, 1] <= dw["y"][1])
        pairs += [("dowel_x", A[dm], B[dm], (1, 0, 0), "both"), ("dowel_z", A[dm], B[dm], (0, 0, 1), "both")]
        self.pairs = pairs
        log("  pairs " + json.dumps({p[0]: int(len(p[1])) for p in pairs}))
        log(f"  supports: journal {len(self.J_ids)} pivot {len(self.PIV_ids)} washer {len(self.WASH_ids)} ptfe {len(self.PTFE_ids)}")
        # collar glue land ring (lift 20 upper guide)
        self.RING = np.flatnonzero((nb == self.WELL) & (X[:, 2] >= -2.0 - 1e-6) & (R >= 24.0) & (R <= 26.4))

    # ---- helpers -------------------------------------------------------------------------------------------------
    def _layer(self, z, axis=2):
        o = self.m.o[axis]; return o + round((z - o) / self.h) * self.h

    def _nearest_layer(self, vals, face, axis=2):
        """lattice coordinate (of the coincident nodes given) nearest to the contact face"""
        if len(vals) == 0:
            return self._layer(face, axis)
        u = np.unique(np.round(vals, 6))
        return float(u[np.argmin(np.abs(u - face))])

    def sel(self, cond):
        return np.flatnonzero(cond)

    def unit_radial(self, ids):
        d = np.zeros((len(ids), 3)); d[:, 0] = self.X[ids, 0] / self.R[ids]; d[:, 1] = self.X[ids, 1] / self.R[ids]; return d

    def unit_tang(self, ids):
        d = np.zeros((len(ids), 3)); d[:, 0] = -self.X[ids, 1] / self.R[ids]; d[:, 1] = self.X[ids, 0] / self.R[ids]; return d

    def mesh_ids(self, az):
        da = (self.AZ - az + 180) % 360 - 180
        return self.sel((self.nb == self.GEAR) & (self.R >= 13.4) & (np.abs(da) <= 8.0))

    def lug_ids(self, face):
        Lg = self.D["lug"]; X = self.X
        if "planes" in Lg:                      # rev3: planar stop faces normal to x; the pin touches along a vertical line at y = contact y
            pl = Lg["planes"][face]
            cand = (self.nb == self.POCK) & (X[:, 2] <= Lg["z"][1]) & (X[:, 2] >= Lg["z"][0]) & (np.abs(X[:, 1] - pl["y"]) <= max(0.6, 1.01 * self.h))
            xs = np.unique(np.round(X[cand & (np.abs(X[:, 0] - pl["x"]) <= 1.01 * self.h), 0], 6))
            xl = xs[np.argmin(np.abs(xs - pl["x"]))]
            return self.sel(cand & (np.abs(X[:, 0] - xl) < 1e-6))
        a = Lg[face]
        da = (self.AZ - a + 180) % 360 - 180
        side = (da >= -0.1) & (da <= 1.2) if face == "cw" else (da <= 0.1) & (da >= -1.2)
        return self.sel((self.nb == self.POCK) & side & (np.abs(self.R - Lg["pin_r"]) <= max(0.6, 1.01 * self.h)) &
                        (X[:, 2] <= Lg["z"][1]) & (X[:, 2] >= Lg["z"][0]))

    @staticmethod
    def spread(F, ids, vec):
        vec = np.asarray(vec, float)
        if len(ids) == 0:
            raise RuntimeError("empty load set")
        for c in range(3):
            F[3 * ids + c] += vec[c] / len(ids)

    def land_nodes(self, wall, z0, z1):
        X = self.X; Ld = self.D["lands"]; yl = Ld["yi"] - Ld["h"]; xl = Ld["xi"] - Ld["h"]
        zc = (X[:, 2] >= z0 - 1e-6) & (X[:, 2] <= z1 + 1e-6) & (self.nb == self.WELL)
        fy = lambda s: (s * X[:, 1] >= yl - 0.35) & (s * X[:, 1] <= yl + 0.25)
        fx = lambda s: (s * X[:, 0] >= xl - 0.05) & (s * X[:, 0] <= xl + 0.45)
        if wall == "front":
            return [self.sel(zc & fy(-1) & (X[:, 0] >= a + 0.4) & (X[:, 0] <= b - 0.4)) for a, b in Ld["front"]]
        if wall == "back":
            out = [self.sel(zc & fy(1) & (X[:, 0] >= a + 0.4) & (X[:, 0] <= b - 0.4)) for a, b in Ld["back"]]
            bu = Ld["back_up"]
            up = self.sel(zc & fy(1) & (X[:, 0] >= bu["x"][0] + 0.4) & (X[:, 0] <= bu["x"][1] - 0.4) & (X[:, 2] >= bu["z_min"]))
            return out + ([up] if len(up) else [])
        if wall == "-X":
            return [self.sel(zc & fx(-1) & (X[:, 1] >= a + 0.15) & (X[:, 1] <= b - 0.15)) for a, b in Ld["endm"]]
        if wall == "+X":
            hi = Ld.get("endp_hi")          # rev3: the lintel of the +X end window is a taped land too (one contact band with the pillar land)
            if hi and z1 >= hi["z_min"]:
                msk = zc & fx(1) & (((X[:, 1] >= hi["y"][0]) & (X[:, 1] <= hi["y"][1]) & (X[:, 2] >= hi["z_min"])) |
                                    np.any([(X[:, 1] >= a + 0.15) & (X[:, 1] <= b - 0.15) for a, b in Ld["endp"]], axis=0))
                return [self.sel(msk)]
            return [self.sel(zc & fx(1) & (X[:, 1] >= a + 0.15) & (X[:, 1] <= b - 0.15)) for a, b in Ld["endp"]]
        raise ValueError(wall)

    def group(self, ids, d):
        d = np.asarray(d, float); d = d / np.linalg.norm(d)
        return dict(ids=ids, d=d, c=self.X[ids].mean(0))

    def strip_groups(self, wall, z0, z1):
        out = {"front": (0, -1, 0), "back": (0, 1, 0), "-X": (-1, 0, 0), "+X": (1, 0, 0)}[wall]
        return [self.group(ids, out) for ids in self.land_nodes(wall, z0, z1) if len(ids)]

    def solve_groups(self, groups, Ft, Mt, F, log, tag):
        A = np.array([np.concatenate([g["d"], np.cross(g["c"], g["d"])]) for g in groups]).T
        b = np.concatenate([Ft, Mt]); w = 1.0e4
        f, _ = nnls(np.vstack([w * A, np.eye(A.shape[1])]), np.concatenate([w * b, np.zeros(A.shape[1])]))
        for g, fi in zip(groups, f):
            self.spread(F, g["ids"], fi * g["d"])
        log.append(dict(tag=tag, f=[round(float(v), 2) for v in f], centroids=[[round(float(v), 2) for v in g["c"]] for g in groups],
                        residual=[round(float(v), 3) for v in (A @ f - b)]))

    def pocket_groups(self, Fz, lift, F, log):
        """crank-pin force Fz (on the stage, vertical) at x -18.65: keyhole half + F11 tab block (lever along x); at mid lift the pin
        is offset in y from the servo shaft: the servo torque (capped at the stall torque) is reacted in the keyhole (lobe + boss, y)"""
        X = self.X; D = self.D; kh, tb, pn = D["keyhole"], D["tab"], D["pin"]
        dk = np.hypot(X[:, 1] - kh["c"][0], X[:, 2] - kh["c"][1])
        half = (X[:, 2] > kh["c"][1]) if Fz > 0 else (X[:, 2] < kh["c"][1])
        ring = (self.nb == self.POCK) & (X[:, 0] >= kh["x"][0]) & (X[:, 0] <= kh["x"][1]) & (dk >= kh["r"][0]) & (dk <= kh["r"][1])
        k_ids = self.sel(ring & half)
        self.load_pts = {"load_keyhole": X[k_ids]}
        sv = D.get("servo")
        if sv:
            # rev3 / LD1: the MG90S is seated by an x COUPLE (not by the vertical lever keyhole / tab of sachta_a): the keyhole carries the pin
            # force Fz; the moment Fz x arm_pin about y is reacted by  L1 (up): F11 tension (nut on the +X wall of its slot) + lower case corner
            # on the turret wall;  L2 (down): tab face on the block + far case end on the F10 dowel (-> wall of the plate hole)
            pk = self.nb == self.POCK; h = self.h
            def patch(p, face_x=True):
                if "c" in p:
                    return self.sel(pk & (np.hypot(X[:, 0] - p["c"][0], X[:, 2] - p["c"][1]) <= p["r"]) & (X[:, 1] >= p["y"][0] - 1e-6) & (X[:, 1] <= p["y"][1] + 1e-6))
                xs = np.unique(np.round(X[pk & (np.abs(X[:, 0] - p["x"]) <= 1.01 * h), 0], 6)); xl = xs[np.argmin(np.abs(xs - p["x"]))]
                return self.sel(pk & (np.abs(X[:, 0] - xl) < 1e-6) & (X[:, 1] >= p["y"][0]) & (X[:, 1] <= p["y"][1]) & (X[:, 2] >= p["z"][0]) & (X[:, 2] <= p["z"][1]))
            if Fz > 0:
                a_ids, b_ids = patch(sv["nut_wall"]), patch(sv["corner"]); sa, sb = 1.0, -1.0; nm = ("load_nut_wall", "load_corner")
            else:
                a_ids, b_ids = patch(sv["tab_face"]), patch(sv["endstop"]); sa, sb = -1.0, 1.0; nm = ("load_tab_face", "load_endstop")
            arm = abs(X[a_ids, 2].mean() - X[b_ids, 2].mean()); T = abs(Fz) * sv["arm_pin"] / arm
            self.spread(F, k_ids, (0, 0, Fz)); self.spread(F, a_ids, (sa * T, 0, 0)); self.spread(F, b_ids, (sb * T, 0, 0))
            # the pin force acts at x pin: moment about y of the applied set = Fz at the keyhole + couple; the remainder (x offset of the
            # keyhole patch centroid from the wall centre) is closed by adjusting T so that sum M_y equals the moment of Fz at the pin
            ck = X[k_ids].mean(0); My_need = -pn["x"] * Fz; My_have = -ck[0] * Fz + (X[a_ids, 2].mean() * sa * T + X[b_ids, 2].mean() * sb * T)
            dT = (My_need - My_have) / (X[a_ids, 2].mean() * sa + X[b_ids, 2].mean() * sb)
            self.spread(F, a_ids, (sa * dT, 0, 0)); self.spread(F, b_ids, (sb * dT, 0, 0)); T += dT
            self.load_pts.update({nm[0]: X[a_ids], nm[1]: X[b_ids]})
            Fv = np.zeros((len(X), 3)); Fv[k_ids, 2] = Fz / len(k_ids); Fv[a_ids, 0] += sa * T / len(a_ids); Fv[b_ids, 0] += sb * T / len(b_ids)
            Mp = np.cross(X, Fv).sum(0)
            rec = dict(pocket=Fz, seat="x-couple", R_key=round(float(Fz), 2), R_tab=0.0, T_x=round(float(T), 2), arm_z=round(float(arm), 2),
                       patches={nm[0]: int(len(a_ids)), nm[1]: int(len(b_ids))}, M_pocket=[round(float(v), 1) for v in Mp])
            th = math.acos(max(-1.0, min(1.0, 1.0 - lift / pn["rc"]))); dy = -pn["rc"] * math.sin(th)
            if abs(dy) > 0.05:
                Mx = dy * Fz; Mx_eff = math.copysign(min(abs(Mx), T_STALL), Mx)
                lobe = self.sel(pk & (X[:, 0] >= kh["x"][0]) & (X[:, 0] <= kh["x"][1]) & (np.hypot(X[:, 1] - kh["lobe"][0], X[:, 2] - kh["lobe"][1]) <= 3.6) & (X[:, 2] < kh["lobe"][1] + 1.0))
                ring_ids = self.sel(ring); arm2 = X[ring_ids, 2].mean() - X[lobe, 2].mean(); fy = Mx_eff / arm2
                self.spread(F, lobe, (0, fy, 0)); self.spread(F, ring_ids, (0, -fy, 0))
                Mc = np.cross(X[lobe].mean(0), (0, fy, 0)) + np.cross(X[ring_ids].mean(0), (0, -fy, 0))
                rec.update(pin_dy=round(dy, 2), Mx_full=round(Mx, 1), Mx_applied=round(Mx_eff, 1), stall_cap=T_STALL, couple=[round(float(v), 1) for v in Mc])
                self.load_pts.update(load_lobe=X[lobe], load_keyring=X[ring_ids]); Mp = Mp + Mc
            log.append(rec)
            return Mp
        t_ids = self.sel((self.nb == self.POCK) & (X[:, 0] >= tb["x"][0]) & (X[:, 0] <= tb["x"][1]) & (np.hypot(X[:, 1] - tb["c"][0], X[:, 2] - tb["c"][1]) <= tb["r"]))
        gs = [self.group(k_ids, (0, 0, 1)), self.group(t_ids, (0, 0, 1))]
        A = np.array([[1.0, 1.0], [gs[0]["c"][0], gs[1]["c"][0]]]); b = np.array([Fz, pn["x"] * Fz])
        f = np.linalg.solve(A, b)
        for g, fi in zip(gs, f):
            self.spread(F, g["ids"], fi * g["d"])
        Mp = sum(fi * np.cross(g["c"], g["d"]) for g, fi in zip(gs, f))
        rec = dict(pocket=Fz, R_key=round(float(f[0]), 2), R_tab=round(float(f[1]), 2), M_pocket=[round(float(v), 1) for v in Mp])
        th = math.acos(max(-1.0, min(1.0, 1.0 - lift / pn["rc"]))); dy = -pn["rc"] * math.sin(th)          # pin y offset from the shaft
        if abs(dy) > 0.05:
            Mx = dy * Fz                                 # moment about x of Fz at (y_shaft + dy) relative to the keyhole/tab line (y_shaft)
            Mx_eff = math.copysign(min(abs(Mx), T_STALL), Mx)
            # couple in the keyhole: lobe (5.6 below the boss) and boss, forces along y
            lobe = self.sel((self.nb == self.POCK) & (X[:, 0] >= kh["x"][0]) & (X[:, 0] <= kh["x"][1]) & (np.hypot(X[:, 1] - kh["lobe"][0], X[:, 2] - kh["lobe"][1]) <= 3.6) & (X[:, 2] < kh["lobe"][1] + 1.0))
            ring_ids = self.sel(ring)
            arm = self.X[ring_ids, 2].mean() - self.X[lobe, 2].mean()
            fy = Mx_eff / arm                           # +fy on the lobe, -fy on the boss ring: M_x = fy * arm
            self.spread(F, lobe, (0, fy, 0)); self.spread(F, ring_ids, (0, -fy, 0))
            Mc = np.cross(self.X[lobe].mean(0), (0, fy, 0)) + np.cross(self.X[ring_ids].mean(0), (0, -fy, 0))
            rec.update(pin_dy=round(dy, 2), Mx_full=round(Mx, 1), Mx_applied=round(Mx_eff, 1), stall_cap=T_STALL, lobe_nodes=int(len(lobe)),
                       couple=[round(float(v), 1) for v in Mc],
                       note="vertical pin force applied in full; the servo torque about x is capped at the MG90S stall torque "
                            "(beyond it the head sinks to the landing - spec 17.10)")
            Mp = Mp + Mc
        log.append(rec)
        return Mp

    def lift_case(self, F, Fhead, lift, log):
        Mp = self.pocket_groups(Fhead, lift, F, log)
        zl = NECK_LOW0 + lift
        zux = min(NECK_STEP0 + lift, STRIP_TOP); zuy = STRIP_TOP
        up = Fhead > 0
        gs = self.strip_groups("front" if up else "back", zl, zl + 1.0) + self.strip_groups("back" if up else "front", zuy - 1.0, zuy)
        gs += self.strip_groups("+X" if up else "-X", zl, zl + 1.0) + self.strip_groups("-X" if up else "+X", zux - 1.0, zux)
        self.solve_groups(gs, np.zeros(3), -Mp, F, log, f"lands lift {lift}")

    def collar_pattern(self, d, p):
        d = np.asarray(d, float); p = np.asarray(p, float)
        P_ = self.X[self.RING]; c0 = P_.mean(0); n = len(self.RING)
        f = np.zeros((n, 3)); f[:] = d / n
        M = np.cross(p - c0, d)
        dx, dy = P_[:, 0] - c0[0], P_[:, 1] - c0[1]
        f[:, 2] += M[0] * dy / (dy ** 2).sum() - M[1] * dx / (dx ** 2).sum()
        if abs(M[2]) > 1e-9:
            rr = np.hypot(dx, dy); t = np.stack([-dy / rr, dx / rr, 0 * rr], 1)
            f += M[2] * t / rr.sum()
        return f

    def lift_case_collar(self, F, Fhead, lift, log):
        Mp = self.pocket_groups(Fhead, lift, F, log)
        zl = NECK_LOW0 + lift; up = Fhead > 0
        gs = self.strip_groups("front" if up else "back", zl, zl + 1.0) + self.strip_groups("+X" if up else "-X", zl, zl + 1.0)
        # the neck may bear anywhere along the straight edges of the collar opening (45.5 x 20.5): three candidate points per edge - with
        # the centre points only (round 1) L2 at lift 20 had NO equilibrium (single back land at x 12.8 -> yaw) and the NNLS residual
        # (about 100 N sideways) was applied as a net load
        ye = 10.25 if up else -10.25; xe = -22.75 if up else 22.75
        pats = [((0, 1, 0) if up else (0, -1, 0), (xx, ye, ZC)) for xx in (0.0, -15.0, 15.0)] + \
               [((-1, 0, 0) if up else (1, 0, 0), (xe, yy, ZC)) for yy in (0.0, -6.0, 6.0)]
        cols = [np.concatenate([g["d"], np.cross(g["c"], g["d"])]) for g in gs]
        cols += [np.concatenate([np.asarray(d, float), np.cross(np.asarray(p, float), np.asarray(d, float))]) for d, p in pats]
        A = np.array(cols).T; b = np.concatenate([np.zeros(3), -Mp]); w = 1.0e4
        fmag, _ = nnls(np.vstack([w * A, np.eye(A.shape[1])]), np.concatenate([w * b, np.zeros(A.shape[1])]))
        for g, fi in zip(gs, fmag[:len(gs)]):
            self.spread(F, g["ids"], fi * g["d"])
        for (d, p), fi in zip(pats, fmag[len(gs):]):
            fp = self.collar_pattern(d, p) * fi
            for cc in range(3):
                np.add.at(F, 3 * self.RING + cc, fp[:, cc])
        log.append(dict(tag=f"lands lift {lift} + collar (z {ZC})", f=[round(float(v), 2) for v in fmag],
                        centroids=[[round(float(v), 2) for v in g["c"]] for g in gs] + [list(p) for d, p in pats],
                        residual=[round(float(v), 3) for v in (A @ fmag - b)]))

    def twist_case(self, F, T, lift, log):
        zl = NECK_LOW0 + lift
        if T > 0:
            gs = self.strip_groups("back", zl, STRIP_TOP)[:1] + [g for g in self.strip_groups("front", zl, STRIP_TOP) if g["c"][0] < 0]
        else:
            gs = [g for g in self.strip_groups("front", -10.2, STRIP_TOP) if g["c"][0] > 0] + [g for g in self.strip_groups("back", -10.2, STRIP_TOP) if g["c"][0] < 0]
        self.solve_groups(gs, np.zeros(3), np.array([0, 0, T]), F, log, f"twist {T}")

    def gear_torque(self, F, T, pan, log):
        az = (PAN_AZ - pan) % 360
        ids = self.mesh_ids(az)
        a = math.radians(az); t = np.array([-math.sin(a), math.cos(a), 0.0]); r = np.array([math.cos(a), math.sin(a), 0.0])
        Ft = T / R_PITCH
        self.spread(F, ids, Ft * t - abs(Ft) * math.tan(math.radians(20)) * r)
        log.append(dict(gear_torque=T, mesh_az=round(az, 2), Ft=round(Ft, 2), nodes=int(len(ids))))

    # ---- one case ------------------------------------------------------------------------------------------------
    def run(self, name, out_dir, tol=2e-6, inner=150, max_outer=60):
        c = CASES[name]; log = []; m = self.m; X = self.X
        F = np.zeros(3 * m.nn); pinion = self.GEAR >= 0; stop = None
        if c["kind"] == "lift":
            self.lift_case(F, c["F"], c["lift"], log)
        elif c["kind"] == "lift_collar":
            self.lift_case_collar(F, c["F"], c["lift"], log)
        elif c["kind"] == "landed":
            hb = self.D["hub"]; zt = self._layer(hb["z_top"])
            ids = self.sel((self.nb == self.WELL) & (np.abs(X[:, 2] - zt) <= 0.51 * self.h) & (self.R >= hb["r"][0]) & (self.R <= hb["r"][1]) &
                           (np.abs(X[:, 0]) <= 22.3) & (np.abs(X[:, 1]) <= 9.8))
            self.spread(F, ids, (0, 0, c["F"])); log.append(dict(landed=c["F"], nodes=int(len(ids))))
        elif c["kind"] == "stop":
            self.gear_torque(F, c["T"], c["pan"], log); pinion = False; stop = "cw" if c["T"] < 0 else "ccw"
        elif c["kind"] == "twist":
            self.twist_case(F, c["T"], c["lift"], log)
        Fv = F.reshape(-1, 3)
        log.append(dict(F_applied=[round(float(v), 3) for v in Fv.sum(0)], M_applied=[round(float(v), 1) for v in np.cross(X, Fv).sum(0)]))
        C = FM.Contact
        S = [C("journal", "pos", K_JG, ids=self.J_ids, dirs=self.unit_radial(self.J_ids), gap=GAP_J)]
        if self.GEAR >= 0:
            S.append(C("pivot", "both", K_PIV, ids=self.PIV_ids, dirs=self.unit_radial(self.PIV_ids)))
        else:                                    # bond failed, gear left out: the lip bore runs on the spacer washers / T_cap (radial)
            S.append(C("pivot", "both", K_PIV, ids=self.LIP_ids, dirs=self.unit_radial(self.LIP_ids)))
            ids = self.sel((self.nb == self.WELL) & (self.R <= 13.0) & (X[:, 2] <= -41.5))
            S.append(C("weak_tang", "both", K_WEAK / max(len(ids), 1), ids=ids, dirs=self.unit_tang(ids)))      # removes the free rotation only
        ax = c.get("axial", "both"); nw = max(len(self.WASH_ids), 1); npf = max(len(self.PTFE_ids), 1)
        well_lip = self.D["axial"]["kind"] != "gear_top"
        ez = lambda n, s=1.0: np.tile([0.0, 0.0, s], (n, 1))
        if ax in ("washer", "both"):
            # the washer is above the gear top / the lip top: it stops upward motion only
            S.append(C("washer", "pos" if ax == "washer" else "both", K_WASH if ax == "washer" else K_WEAK / nw, ids=self.WASH_ids, dirs=ez(len(self.WASH_ids))))
        if ax in ("ptfe", "both") and self.GEAR >= 0:
            S.append(C("ptfe", "pos" if ax == "ptfe" else "both", K_PTFE if ax == "ptfe" else K_WEAK / npf, ids=self.PTFE_ids, dirs=ez(len(self.PTFE_ids), -1.0)))
        if pinion:
            ids = self.mesh_ids(PAN_AZ % 360); S.append(C("pinion", "both", K_PIN / len(ids), ids=ids, dirs=self.unit_tang(ids)))
        if stop:
            ids = self.lug_ids(stop)
            if "planes" in self.D["lug"]:
                d = np.tile(np.asarray(self.D["lug"]["planes"][stop]["d"], float), (len(ids), 1))    # motion of the lug INTO the pin
            else:
                d = self.unit_tang(ids) * (-1.0 if stop == "cw" else 1.0)
            # the lug is pushed INTO the pin: cw face moves clockwise (-t), ccw face counter-clockwise (+t); compression only
            S.append(C("stop", "pos", K_STOP / max(len(ids), 1), ids=ids, dirs=d))
            log.append(dict(stop_face=stop, stop_nodes=int(len(ids)), r_mean=round(float(self.R[ids].mean()), 2)))
        Fpin = c.get("F", 0.0) if c["kind"] in ("lift", "lift_collar") else 0.0
        for pr in self.pairs:
            nm, a, b, d, kind = pr[:5]; gap = pr[5] if len(pr) > 5 else 0.0
            if gap != 0.0:
                # stop with a clearance: first guess closed only where the pin force of the case pushes the module onto it (up -> ledge,
                # down -> floor); a very soft bilateral spring (2e-4 k) keeps the module from floating freely inside the clearance
                closed = (Fpin > 0 and kind == "pos") or (Fpin < 0 and kind == "neg")
                S.append(C(nm, kind, self.k_pair, a=a, b=b, d=d, gap=gap, init_closed=closed))
                S.append(C(nm + "_reg", "both", 2e-4 * self.k_pair, a=a, b=b, d=d))
            else:
                S.append(C(nm, kind, self.k_pair, a=a, b=b, d=d, init_closed=not (kind != "both" and nm.endswith("_y"))))
        U, info = FM.solve_contact(m, F, S, log=self.log, tol=tol, inner=inner, max_outer=max_outer, tag=name)
        Uv = U.reshape(-1, 3); reac = {}; pf = {}
        for s in S:
            f = s.force_on(Uv)
            if s.pair:
                pf[s.name] = dict(sum=round(float((f * s.d).sum()), 2), F=[round(float(v), 2) for v in f.sum(0)], n_active=int(s.act.sum()), n=int(s.n))
            else:
                fr = f
                reac[s.name] = dict(F=[round(float(v), 2) for v in fr.sum(0)], M=[round(float(v), 1) for v in np.cross(X[s.ids], fr).sum(0)],
                                    n_active=int(s.act.sum()), n=int(s.n), max_u_dir=round(float(s.rel(Uv).max()), 4) if s.n else 0.0)
        tot = sum(np.array(v["F"]) for v in reac.values()); totM = sum(np.array(v["M"]) for v in reac.values())
        # LD1: nodes of the ACTIVE one-sided contacts of the module joint (+ the stop line, + both ends of the dowel): post.py keeps the
        # structure rows >= 1.0 mm away from them
        cz = {}
        for s in S:
            if s.name.endswith("_reg") or not s.n:
                continue
            f = np.linalg.norm(s.force_on(Uv), axis=1)
            if s.pair:                                   # one-sided contacts, the dowel AND the clamped F10 pads (tied faces: the pad edge is a contact edge)
                on = s.act & (f > 1e-9)
                cz[s.name] = X[s.a[on]]
            elif s.name == "stop":
                on = s.act & (f > 1e-9)
                cz[s.name] = X[s.ids[on]]
        for zs in self.D.get("zstops", []):                      # the TRUE bearing rectangle of an active vertical stop (the lattice nodes of a
            if zs["name"] in cz and len(cz[zs["name"]]):         # 1.2 .. 2.2 wide strip sit up to h / 2 inside its edges)
                gx = np.arange(zs["x"][0], zs["x"][1] + 1e-9, 0.2); gy = np.arange(zs["y"][0], zs["y"][1] + 1e-9, 0.2)
                GX, GY = np.meshgrid(gx, gy, indexing="ij")
                cz[zs["name"] + "_patch"] = np.stack([GX.ravel(), GY.ravel(), np.full(GX.size, zs["z"])], 1)
        # fixer 1d (LD1): a clamped F10 screw joint is a contact pair too - the DIN 433 washer (r 2.25) on the plate back and the pad /
        # M2 insert face on the plate front clamp the plate ring around the screw hole.  Its TRUE patch (disc r <= 2.25 about the screw
        # axis, both plate faces) belongs to the contact zone (the lattice nodes of the tied ring r >= 2.05 sit up to h inside its edge)
        yb_ = self.D.get("servo", {}).get("endstop", {}).get("y", (FM.Y_PAD, FM.Y_PAD + 2.0))
        for f in self.D["faces"]:
            if f["kind"] != "both" or f["name"] not in cz or not len(cz[f["name"]]):
                continue
            circ = [sh for sh in [f["shape"]] + list(f.get("plus", [])) if sh[0] == "circle"]
            for sh in circ[-1:]:
                rr_, tt_ = np.meshgrid(np.arange(0.0, 2.25 + 1e-9, 0.25), np.radians(np.arange(0.0, 360.0, 15.0)), indexing="ij")
                for yy_ in (yb_[0], yb_[1]):
                    cz[f["name"] + f"_washer_{yy_:.1f}"] = np.stack([sh[1] + rr_.ravel() * np.cos(tt_.ravel()), np.full(rr_.size, yy_), sh[2] + rr_.ravel() * np.sin(tt_.ravel())], 1)
        for k, v in getattr(self, "load_pts", {}).items():       # applied servo loads = contact patches of the MG90S in the pocket
            if len(v) and c["kind"] in ("lift", "lift_collar"):
                cz[k] = np.asarray(v)
        np.savez_compressed(os.path.join(out_dir, name + "_contact.npz"), **{k: v.astype(np.float32) for k, v in cz.items()})
        self.contact_pts = cz
        resid = [l["residual"] for l in log if isinstance(l, dict) and "residual" in l]
        equil = all(max(abs(v) for v in r[:3]) <= 0.05 and max(abs(v) for v in r[3:]) <= 1.0 for r in resid)
        rs = dict(case=name, spec=c, design=self.D.get("name"), h=self.h, stl_stamp=m.stamp, nodes=int(m.nn), bond_area=round(m.bond_area, 1),
                  nobond=self.nobond, collar_body=self.collar, equilibrated=bool(equil), log=log, reactions=reac, reaction_sum=[round(float(v), 2) for v in tot],
                  reaction_moment_sum=[round(float(v), 1) for v in totM], pair_forces_on_pocket=pf, solver=info,
                  max_disp=round(float(np.abs(U).max()), 4), uz_axis=round(float(Uv[self.WASH_ids, 2].mean()), 4) if len(self.WASH_ids) else None)
        # displacements used by the K12 rows: stage rise (well), rise of the stop lug (engagement), stage-side deflection of the lift chain
        Lg = self.D["lug"]; kh = self.D["keyhole"]; hb = self.D["hub"]
        wl = self.nb == self.WELL
        lug = self.sel((self.nb == self.POCK) & (self.R >= Lg["r"][0]) & (X[:, 2] <= Lg["z"][1]) & (X[:, 1] > 0))
        dk = np.hypot(X[:, 1] - kh["c"][0], X[:, 2] - kh["c"][1])
        key = self.sel((self.nb == self.POCK) & (X[:, 0] >= kh["x"][0]) & (X[:, 0] <= kh["x"][1]) & (dk >= kh["r"][0]) & (dk <= kh["r"][1]))
        hub = self.sel(wl & (np.abs(X[:, 2] - self._layer(hb["z_top"])) <= 0.51 * self.h) & (self.R >= hb["r"][0]) & (self.R <= hb["r"][1]))
        rs["disp"] = dict(uz_well_max=round(float(Uv[wl, 2].max()), 4), uz_well_min=round(float(Uv[wl, 2].min()), 4),
                          uz_lug=round(float(Uv[lug, 2].mean()), 4) if len(lug) else None,
                          uz_keyhole=round(float(Uv[key, 2].mean()), 4) if len(key) else None, uz_hub=round(float(Uv[hub, 2].mean()), 4) if len(hub) else None)
        os.makedirs(out_dir, exist_ok=True)
        np.savez_compressed(os.path.join(out_dir, name + ".npz"), U=U.astype(np.float32))
        json.dump(rs, open(os.path.join(out_dir, name + ".json"), "w"), indent=1, default=float)
        self.log(f"  [{name}] reactions {json.dumps(reac)[:900]}")
        self.log(f"  [{name}] pairs {json.dumps(pf)}  solver outer {info['outer']} cg {info['cg_total']} res {info['rel_res']:.1e} conv {info['converged']} {info['seconds']} s")
        return U, rs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stl", required=True); ap.add_argument("--h", type=float, default=0.4)
    ap.add_argument("--design", default=None); ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=os.path.join(FM.HERE, "cache")); ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--max-outer", type=int, default=60); ap.add_argument("--tol", type=float, default=2e-6)
    ap.add_argument("--no-collar", action="store_true", help="without the collar-disc body (sachta_a model: guide forces only)")
    ap.add_argument("cases", nargs="+")
    a = ap.parse_args()
    D = FD.load(a.design)
    log = lambda s: print(s, flush=True)
    groups = {}
    for cname in a.cases:
        groups.setdefault(bool(CASES[cname].get("nobond")), []).append(cname)
    for nobond, names in groups.items():
        st = Stage(a.stl, a.h, D, a.cache, nobond=nobond, collar=not a.no_collar, log=log)
        for cname in names:
            t0 = time.time(); U, rs = st.run(cname, a.out, tol=a.tol, inner=a.inner, max_outer=a.max_outer)
            import post
            rows = post.evaluate(st, U, rs, a.stl, a.cache, a.out)
            for r in sorted(rows, key=lambda r: -(r["stress"] / r["allowable"])):
                log(f"   {r['spot']:58s} {r['stress']:7.2f} / {r['allowable']:5.2f}  {'ok ' if r['ok'] else 'FAIL'} at {r['at']}")
            log(f"== {cname} done {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
