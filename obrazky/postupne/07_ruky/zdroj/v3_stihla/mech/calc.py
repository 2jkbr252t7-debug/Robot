"""R3/mech/calc.py - function and strength numbers for the packaging options (own computation; inputs marked).
1 magnet clutch: per-magnet force through the printed skin (surface-charge disc model of B1 magnets.py, re-implemented here,
  calibrated to the catalogue pull of a 5x2 N38 disc = 4.9 N as B1 did), torque per magnet, magnet counts that hit the
  torque window, balanced patterns, spacer fine tuning.  Both windows: the brief's 0.0124-0.0170 N.m and the fixer's newer
  0.0082-0.0113 N.m (R2c/oprava/final_B1plus_fix.json).
2 strength: stop contact, seat bending under L5, bearings vs L5, washer bond, drive-hub key, press-fit retention (scaled from
  the B1/judge numbers), tilt threshold (judge method).
3 M3: room for a clutch in the torso drive line (free-space map of the fixer, read only).
Writes out/calc.json"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MU0 = 4e-7 * math.pi
out = {}


# ------------------------------------------------------------------------------------------------------- 1 magnets
def disc_pts(n=26):
    r_edges = np.linspace(0, 1.0, n + 1)
    pts, w = [], []
    for i in range(n):
        r0, r1 = r_edges[i], r_edges[i + 1]; rc = 0.5 * (r0 + r1)
        m = max(6, int(2 * math.pi * rc / (1.0 / n)))
        ph = (np.arange(m) + 0.5) * 2 * math.pi / m
        pts.append(np.c_[rc * np.cos(ph), rc * np.sin(ph)]); w.append(np.full(m, math.pi * (r1 ** 2 - r0 ** 2) / m))
    return np.concatenate(pts), np.concatenate(w)


P1, W1 = disc_pts()


def disc_force(a, d, s1, s2):
    p = P1 * a; w = W1 * a * a
    dx = p[:, None, 0] - p[None, :, 0]; dy = p[:, None, 1] - p[None, :, 1]
    I = np.sum(w[:, None] * w[None, :] * d / (dx * dx + dy * dy + d * d) ** 1.5)
    return MU0 * s1 * s2 / (4 * math.pi) * I * 1e-6


def magnet_plate(D, h, Br, g):
    """attraction (N) of an axial disc magnet D x h (mm) to an ideal iron half-space at face gap g (image method)"""
    M = Br / MU0; a = D / 2; F = 0.0
    for z1, s1 in ((0.0, 1), (-h, -1)):
        for z2, s2 in ((2 * g, -1), (2 * g + h, 1)):
            F += disc_force(a, z2 - z1, s1 * M, s2 * M)
    return -F


CAL = 4.9 / magnet_plate(5, 2, 1.23, 0.02)          # catalogue / ideal for 5x2 N38 (B1 calibration)
SKIN = 0.25
KW = (0.6, 0.85)                                      # finite washer / partial saturation (B1 range)
MU = (0.25, 0.40)                                     # resin skin on zinc steel, clean dry (B1 range)
mags = {"5x2 N38": (5, 2, 1.23), "5x1 N38": (5, 1, 1.23), "5x1 N35": (5, 1, 1.19), "6x1 N38": (6, 1, 1.23), "4x1 N38": (4, 1, 1.23)}
out["magnets"] = {"calibration_catalogue_over_ideal": round(CAL, 3), "skin": SKIN, "KW": KW, "mu": MU, "per_type": {}}
for k, (D, h, Br) in mags.items():
    f0 = magnet_plate(D, h, Br, 0.02)
    fs = magnet_plate(D, h, Br, SKIN)
    sp = {s: round(magnet_plate(D, h, Br, SKIN + s) / fs, 3) for s in (0.2, 0.4)}
    out["magnets"]["per_type"][k] = dict(ideal_contact_N=round(f0, 2), est_catalogue_pull_N=round(CAL * f0, 2),
                                         through_skin_N=[round(CAL * fs * kw, 3) for kw in KW], spacer_factor=sp)

WINDOWS = {"brief 0.0124-0.0170": (0.0124, 0.0170), "fixer 0.0082-0.0113": (0.0082, 0.0113)}
# clutch layouts: (magnet type, radius of the magnet circle, pockets, balanced counts)
LAYOUT = {"M1 (B1+)": ("5x2 N38", 7.7, 8, [2, 4, 6, 8]),
          "M2 (6700 + M14)": ("5x1 N38", 10.5, 10, [2, 4, 5, 6, 7, 8, 9, 10]),
          "M2 with 5x2 (does not fit 16)": ("5x2 N38", 10.5, 10, [2, 4, 5, 6, 7, 8, 9, 10]),
          "M2b (MR128 + M12)": ("5x1 N38", 9.25, 8, [2, 4, 6, 8]),
          "M4 (= M2 clutch)": ("5x1 N38", 10.5, 10, [2, 4, 5, 6, 7, 8, 9, 10])}
out["clutch"] = {}
for name, (mt, r, npk, bal) in LAYOUT.items():
    Fs = out["magnets"]["per_type"][mt]["through_skin_N"]
    sp = out["magnets"]["per_type"][mt]["spacer_factor"]
    row = dict(magnet=mt, r_mm=r, pockets=npk, balanced_counts=bal, per_magnet_Nm={}, windows={})
    cases = {"low (F lo, mu 0.25)": Fs[0] * MU[0], "mid": 0.5 * (Fs[0] + Fs[1]) * 0.5 * (MU[0] + MU[1]), "high (F hi, mu 0.40)": Fs[1] * MU[1]}
    for cn, Fmu in cases.items():
        row["per_magnet_Nm"][cn] = round(Fmu * r * 1e-3, 5)
    for wn, (lo, hi) in WINDOWS.items():
        wr = {}
        for cn, Fmu in cases.items():
            t1 = Fmu * r * 1e-3
            # reachable with n full-force magnets (balanced) or n magnets with some on 0.2 / 0.4 spacers
            hits = [n for n in bal if lo <= n * t1 <= hi]
            levels = sorted(set(round(t1 * (a + b * sp[0.2] + c * sp[0.4]), 5) for n in bal for a in range(n + 1)
                                for b in range(n + 1 - a) for c in [n - a - b] if True))
            hit_sp = [v for v in levels if lo <= v <= hi]
            wr[cn] = dict(T_per_magnet=round(t1, 5), max_all_pockets=round(npk * t1, 4), full_magnet_counts_in_window=hits,
                          with_spacers_any_in_window=bool(hit_sp), min_needed=math.ceil(lo / t1), fits=bool(hits or hit_sp) and math.ceil(lo / t1) <= npk)
        row["windows"][wn] = wr
    out["clutch"][name] = row

# ------------------------------------------------------------------------------------------------------- 2 strength
S = {}
# stop contact (radial face of the rib meets the radial face of the lug); torque at the arm
stops = {"M1 B1+ (judge-final)": (2.0 * 1.1, 6.05), "M1 fixer 6800 hub": (2.7, 6.1), "M2 / M2b / M3": (1.5 * 1.4, 6.0)}
for k, (A, rm) in stops.items():
    S[f"stop {k}"] = {"area_mm2": round(A, 2), "r_mm": rm,
                      "homing at 0.017 N.m [MPa]": round(17.0 / rm / A, 2),
                      "push 3 N at the tip (0.216 N.m) [MPa]": round(216.0 / rm / A, 1),
                      "push 10 N at the tip (0.72 N.m) [MPa]": round(720.0 / rm / A, 1)}
# rib root shear (rib 32.7 deg wide, root at r 8.5 into the hub, axial length L)
for k, L in (("M1", 2.0), ("M2/M3/M2b", 1.5)):
    A = math.radians(32.7) * 8.5 * L
    S[f"rib root shear {k}"] = {"area_mm2": round(A, 2), "push 3 N tip [MPa]": round(216.0 / 6.0 / A, 1)}
# seat bending under L5 (0.72 N.m couple from the arm) - printed section only
def Z(do, di):
    return math.pi * (do ** 4 - di ** 4) / (32 * do)
S["seat bending L5 (0.72 N.m)"] = {
    "B1+/M2/M3 D10 with D7 bore (A2 zone, A2 steel race ignored)": round(720 / Z(10, 7), 1),
    "B1+ D10/D5 (judge row)": round(720 / Z(10, 5), 1),
    "M2/M3 D10 with D7.6 counterbore under the 6700 (about half the couple)": round(360 / Z(10, 7.6), 1),
    "M2b root D10/D5 (stop zone, A2 moved)": round(720 / Z(10, 5), 1),
    "M2b D8/D5 under the MR128 (about half the couple)": round(360 / Z(8, 5), 1),
    "M2b if the seat were D8/D5 all along (rejected first draft)": round(720 / Z(8, 5), 1),
    "M4 D10/D5 root (A2 moved), counterbore D7.6 under the bearing (half couple)": [round(720 / Z(10, 5), 1), round(360 / Z(10, 7.6), 1)],
    "allowable": "8.5 long-term, ~20 short-term (B1 convention)"}
# bearings: static equivalent of the L5 couple on one deep-groove row, F ~ 2 M / Dpw  (rough)
brg = {"6700ZZ 10x15x4": (12.5, 0.85, "Cr ~0.73-0.93 kN (EZO stainless 729 N, search snippet)"),
       "MR128ZZ 8x12x3.5": (10.0, 0.545, "Cr 545 N (EZO, Albeco listing)"),
       "6800ZZ 10x19x5 (fixer)": (14.5, 1.72, "Cr ~1.7 kN (typical)")}
for k, (dpw, Cr, src) in brg.items():
    C0 = 0.5 * Cr * 1000
    F = 2 * 720 / dpw
    S[f"bearing {k} under L5"] = {"F_equiv_N": round(F, 0), "C0_est_N": round(C0, 0), "F/C0": round(F / C0, 2), "source": src}
# tilt threshold (judge method): magnets hold the friction face square until F_mag * r_face / 72 at the tip
for k, (Fmag, rf, w) in {"M1 B1+": ((6.0, 9.0), 10.0, 4.0), "M2 (5x1, face to r 14)": ((3.0, 8.0), 13.5, 4.0),
                         "M2b (5x1, face to r 12)": ((3.0, 7.0), 11.5, 3.5)}.items():
    S[f"tilt {k}"] = {"threshold_tip_N": [round(f * rf / 72.0, 2) for f in Fmag],
                      "tilt_after_threshold_tip_mm": round((0.03 / w + math.radians(0.15)) * 72.0, 2)}
# washer bonds (epoxy, 2 MPa allowable in shear for a printed/steel bond as B1)
S["washer bond M2 (M14 on 6700 OD 2.2 long + hub face r 7.5..14)"] = {
    "area_mm2": round(math.pi * 15 * 2.2 + math.pi * (14 ** 2 - 7.5 ** 2), 0),
    "magnet pull 13 N + torque 0.017 N.m -> stress MPa": round(13 / (math.pi * (14 ** 2 - 7.5 ** 2)) + 17 / 10.75 / (math.pi * 15 * 2.2 + math.pi * (14 ** 2 - 7.5 ** 2)), 3)}
# drive hub key (hex 3 AF printed key in the DIN 912 socket, 3 flats carry, lever 1.3, depth 2.0) and 2.5 AF in DIN 7984
for k, (af, depth) in (("3 AF in DIN 912 (M2/M4)", (3.0, 2.0)), ("2.5 AF in DIN 7984 (M2b)", (2.5, 1.6))):
    a_, d_ = af, depth
    S[f"drive key {k}"] = {"bearing stress at 0.017 N.m [MPa]": round(17.0 / (3 * 0.43 * a_) / (0.58 * a_ * d_), 2)}
# press-fit retention on the head: B1/judge fresh 45-120 N, relaxed 13-60 N for a 4.0 grip; scale with the grip length
for k, g in (("B1+ (grip 4.0)", 4.0), ("M2 (grip 2.1, head recessed 1.6)", 2.1), ("M4 (grip 1.8)", 1.8), ("M2b DIN 7984 (grip 2.8, plain head)", 2.8)):
    S[f"retention {k}"] = {"fresh_N": [round(45 * g / 4, 0), round(120 * g / 4, 0)], "relaxed_N": [round(13 * g / 4, 0), round(60 * g / 4, 0)],
                           "note": "scaled from the B1/judge estimate (unverified, coupon test needed)"}
out["strength"] = S

# ------------------------------------------------------------------------------------------------------- 3 M3 torso room
try:
    F = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/free_L.npz")
    xs, ys, zs = F["xs"], F["ys"], F["zs"]; h = 0.5
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    rv = np.hypot(X - 39.0, Y - 3.0)
    # column fill (B1+ judge merge, read only)
    Pf = np.load("/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_L.npz")["P"].astype(float)
    rows = []
    for z in np.arange(-44.75, -32.0, 1.0):
        kz = int(np.argmin(abs(zs - z)))
        fr = (F["ds"][:, :, kz] >= 0.30 + h / 2) & (F["dm"][:, :, kz] >= 1.0 + h / 2) & (F["dl"][:, :, kz] >= 0.5 + h / 2)
        fr &= X <= (F["capmin"][:, kz][None, :] - 0.3 - h / 2)
        fz = Pf[abs(Pf[:, 2] - zs[kz]) < 0.26]
        for p in fz:
            i = int(round((p[0] - xs[0]) / h)); j = int(round((p[1] - ys[0]) / h))
            if 0 <= i < len(xs) and 0 <= j < len(ys):
                fr[i, j] = False
        best = 0.0
        for r in np.arange(0.5, 12.01, 0.25):
            ring = (rv >= r - 0.25) & (rv < r + 0.25)
            if fr[ring].all():
                best = r
            else:
                break
        rows.append(dict(z=round(float(zs[kz]), 2), full_circle_free_r=best,
                         free_fraction_r6=round(float(fr[(rv >= 5.75) & (rv < 6.25)].mean()), 2),
                         free_fraction_r8=round(float(fr[(rv >= 7.75) & (rv < 8.25)].mean()), 2)))
    out["M3_torso_room"] = dict(rows=rows, note="free = not hard (T4 static), >= 1.0 from the neck pan/lift sweep, >= 0.5 from the "
                                "T_stred lowering path, inside the side cap, minus the B1+ column fill; the existing coupler (r 4.5, "
                                "z -43.5..-35.5) and the vertical shaft are not subtracted (they would be replaced)")
except Exception as e:
    out["M3_torso_room"] = dict(error=str(e))
# what a clutch at the servo coupler would need (servo side torque = arm torque / 1.5)
need = {}
for wn, (lo, hi) in WINDOWS.items():
    Ts = (lo / 1.5, hi / 1.5)
    t1 = out["magnets"]["per_type"]["5x2 N38"]["through_skin_N"][0] * MU[0]
    need[wn] = dict(servo_side_Nm=[round(Ts[0], 5), round(Ts[1], 5)],
                    magnet_circle_r_for_8x5x2_mm=round(Ts[0] / (8 * t1) * 1e3, 1),
                    spring_preload_N_at_r_eff_2p8_mu_0p25=round(Ts[1] / (0.25 * 0.0028), 1))
out["M3_needs"] = need
json.dump(out, open(os.path.join(HERE, "out", "calc.json"), "w"), indent=1, ensure_ascii=False)
if __name__ == "__main__":
    print(json.dumps(out["magnets"], indent=1))
    for k, v in out["clutch"].items():
        print(k, v["magnet"], "r", v["r_mm"], v["per_magnet_Nm"])
        for wn, w in v["windows"].items():
            print("    ", wn, {c: (x["full_magnet_counts_in_window"], x["min_needed"], x["fits"]) for c, x in w.items()})
    for k, v in out["strength"].items():
        print(k, v)
    for r in out["M3_torso_room"].get("rows", []):
        print(r)
    print(out["M3_needs"])
