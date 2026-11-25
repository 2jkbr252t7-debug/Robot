"""K2 x-budget, both sides, two map variants (see concept.md).  For a LOW servo with its output shaft parallel to the
shoulder axis (plain belt / cord between parallel shafts) the pulley plane must be the same at both ends.
Shoulder end: outer face of the pulley plane xb1 <= value at which a disc r_f about (y 3, z -17) clears the side-cap wall
(true 2.2 offset of the approved outer surface) by 0.5 (xbudget.json A).  Servo end: case [x_face - H, x_face] with
x_face = xb1 - w - 0.3.  Here: for each side / variant / pulley option the LARGEST case depth H_max that fits anywhere
in the lower torso (z <= -48), for the SCS0009 section 23.2 x 12.1 and the KST X06 section 20 x 7 (both orientations,
shaft on the width centre, 5.9 / 5.0 from one end).  Writes xbudget2.json"""
import json, time
import numpy as np
from scipy import ndimage as ndi
from scipy.ndimage import maximum_filter
t0 = time.time()
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H, n = D["lo"], float(D["h"]), tuple(D["n"])
label, static, interior, dm, lower = D["label"], D["static"], D["interior"], D["dm"], D["lower"]
names = [str(s) for s in D["lab_names"]]
X = lo[0] + (np.arange(n[0]) + 0.5) * H; Y = lo[1] + (np.arange(n[1]) + 0.5) * H; Z = lo[2] + (np.arange(n[2]) + 0.5) * H
XX, YY, ZZ = np.meshgrid(X, Y, Z, indexing="ij")
A = json.load(open("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/xbudget.json"))["A_xb1_max"]
soft_names = {"T_klb_L", "T_klb_P", "zosilnovac", "menic", "kondenzator", "usb_predlzovac"}
soft_names |= {s for s in names if s.startswith(("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14",
                                                 "skr_F3a_2", "pd_F3a_2", "vl_F3a_2", "skr_F1", "pd_F1"))}
soft_lab = np.array([nm in soft_names for nm in names])
sp = label == names.index("T_spodok")
tub = (np.abs(XX) / 39.55) ** 2.66 + (np.abs(YY) / 25.49) ** 2.66 < 1.0
pin_posts = ((np.hypot(XX - 27.09, YY - 12.89) <= 4.0) | (np.hypot(XX + 21.37, YY + 21.06) <= 4.0)) & (ZZ >= -62.0)
soft_sp = sp & (ZZ >= -82.3) & ((ZZ >= -78.0) | tub) & ((XX >= 26.0) | (XX <= -32.4)) & ~pin_posts
hard0 = static & ~soft_lab[label] & ~soft_sp
# optimistic: J1 plug reservation only z >= -57.3, bumper post thinned to a 1.2 wall (x <= 17.9), T_stred path ignored
j1 = label == names.index("servo_J1")
plug_low = j1 & (XX > 15.75) & (ZZ < -57.3)
bump = sp & (XX > 17.9) & (XX < 18.5) & (np.abs(YY) <= 4.5) & (ZZ <= -69.5) & (ZZ >= -83.5)
bumpR = sp & (XX < -17.9) & (XX > -18.5) & (np.abs(YY) <= 4.5) & (ZZ <= -69.5) & (ZZ >= -83.5)   # (no such post on -X)
hard1 = hard0 & ~plug_low & ~bump
VAR = {}
for vn, hd, use_lower in (("as_reserved", hard0, True), ("optimistic", hard1, False)):
    ds = ndi.distance_transform_edt(~hd, sampling=H).astype(np.float32)
    F = interior & ~hd & (ds >= 0.55) & (dm >= 1.25)
    if use_lower: F &= ~lower
    VAR[vn] = F
    print(vn, "free cm3", F.sum() * H ** 3 / 1000, f"{time.time()-t0:.0f}s", flush=True)
def xin_avail(F, xmax, side):
    """per (y, z): smallest |x| from which the run up to |x| = xmax is free (side +1 = left, -1 = right, mirrored)"""
    if side > 0:
        i0 = np.searchsorted(X, 0.0); sub = F[i0:]; Xs = X[i0:]
    else:
        i1 = np.searchsorted(X, 0.0); sub = F[:i1][::-1]; Xs = -X[:i1][::-1]
    k = np.searchsorted(Xs, xmax); sub = sub[:k + 1]
    b = ~sub
    any_b = b.any(0)
    last = sub.shape[0] - 1 - np.argmax(b[::-1], axis=0)
    xa = np.where(any_b, Xs[np.clip(last, 0, len(Xs) - 1)] + H / 2, Xs[0])
    xa = np.where(any_b & (last == sub.shape[0] - 1), np.nan, xa)
    return xa
SECT = {"SCS0009": (23.2, 12.1, 5.9), "KST_X06": (20.0, 7.0, 5.0)}
def best(F, xmax, side, sect):
    L_, W_, E_ = SECT[sect]
    xa = xin_avail(F, xmax, side); A2 = np.where(np.isnan(xa), 1e3, xa)
    zok = (Z <= -48.0)
    out = (1e3, None)
    for orient in ("L_y", "L_z"):
        for sense in (1, -1):
            if orient == "L_y":
                dy0, dy1 = sorted((-E_ * sense, (L_ - E_) * sense)); dz0, dz1 = -W_ / 2, W_ / 2
            else:
                dz0, dz1 = sorted((-E_ * sense, (L_ - E_) * sense)); dy0, dy1 = -W_ / 2, W_ / 2
            ky = int(round((dy1 - dy0) / H)); kz = int(round((dz1 - dz0) / H))
            M = maximum_filter(A2, size=(ky, kz), mode="constant", cval=1e3)
            M[:, ~zok] = 1e3
            j, k = np.unravel_index(np.argmin(M), M.shape)
            if M[j, k] < out[0]:
                out = (float(M[j, k]), dict(orient=orient, sense=sense, shaft_y=round(float(Y[j] - 0.5 * (dy0 + dy1)), 2),
                                            shaft_z=round(float(Z[k] - 0.5 * (dz0 + dz1)), 2)))
    return out
rows = []
for side in (1, -1):
    for vn, F in VAR.items():
        for (w, pn) in ((3.0, "Dyneema drum 3.0"), (4.6, "GT2 3 mm + flanges 4.6"), (7.6, "GT2 6 mm + flanges 7.6")):
            for rf in (5.0, 7.0):
                xb1 = A[f"wall2.2_rf{rf}"]; xf = xb1 - w - 0.3
                for sect in SECT:
                    xin, where = best(F, xf, side, sect)
                    Hmax = xf - xin if xin < 999 else None
                    r = dict(side="L" if side > 0 else "R", variant=vn, pulley=pn, r_f=rf, xb1=xb1, x_face=round(xf, 2), servo=sect,
                             x_in_min=round(xin, 2) if xin < 999 else None, H_max=round(Hmax, 2) if Hmax is not None else None, at=where)
                    rows.append(r)
                    print(r, flush=True)
json.dump(dict(note=__doc__, rows=rows, need=dict(SCS0009_case_depth=[21.5, 25.25], KST_X06=[16.6, "+ spline/boss ~3 UNVERIFIED"],
                                                    MG90S=22.7)),
          open("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/xbudget2.json", "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
