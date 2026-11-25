"""K2 feasibility: the x-budget of a LOW arm servo whose output shaft is parallel to the shoulder axis (needed for a
plain belt / cord between parallel shafts).
A) shoulder end: the outermost belt plane xb1 at which a pulley disc r_f about the shoulder axis (y 3, z -17) clears the
   side-cap wall (true inner offset of the approved outer surface, wall 2.2 nominal / 1.2 local minimum) by 0.5.
B) servo end: for every placement of the servo case cross-section (23.2 x 12.1, both orientations, shaft 5.9 from one end,
   on the case width centre) in the lower torso, the most inboard x at which the case may start (hard map = map1 static
   minus the parts this concept may move: column, T_klb, amplifier, buck, capacitor, USB, F8/F14/F3a_2/F1 fasteners),
   with the T_stred lowering path counted as blocked (variant 'strict') or not (variant 'after_T5').
   required case start x_in = xb0 - delta - H  (xb0 = xb1 - w, w = pulley width, delta = 0.3 pulley-to-case-face gap)
   margin = x_in(required) - x_in(available)   (>= 0 means the case fits)
Writes xbudget.json."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); import os; os.chdir("/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
OUT = "/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/xbudget.json"
res = {}
# ---------------------------------------------------------------- A) shoulder end
def disc_clear(xc, r, wall, n=72):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    Q = np.stack([np.full(n, xc), 3.0 + r * np.cos(th), -17.0 + r * np.sin(th)], 1)
    return float(C.clearance_to_shell(Q, wall=wall).min())
A = {}
for wall in (2.2, 1.2):
    for r in (4.5, 5.0, 6.0, 7.0, 8.0):
        lo, hi = 36.0, 47.0
        for _ in range(30):
            m = 0.5 * (lo + hi)
            if disc_clear(m, r, wall) >= 0.5: lo = m
            else: hi = m
        A[f"wall{wall}_rf{r}"] = round(lo, 2)
res["A_xb1_max"] = A
print("A xb1_max (disc r_f clear of the wall by 0.5):", A)
# ---------------------------------------------------------------- B) servo end
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H, n = D["lo"], float(D["h"]), D["n"]
Hd = np.load("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/hard.npz")
free_h = Hd["free_h"]; lower = D["lower"]; label = D["label"]; names = [str(s) for s in D["lab_names"]]
X = lo[0] + (np.arange(n[0]) + 0.5) * H; Y = lo[1] + (np.arange(n[1]) + 0.5) * H; Z = lo[2] + (np.arange(n[2]) + 0.5) * H
def xin_avail(F, xmax=40.0):
    """for each (y, z): the smallest x such that every voxel in [x, xmax] is free (left side). nan if xmax itself is blocked"""
    i1 = np.searchsorted(X, xmax)
    sub = F[:i1 + 1]                       # x up to xmax
    blocked = ~sub
    # last blocked index along x (from the inboard side) -> free run starts after it
    idx = np.where(blocked.any(0), sub.shape[0] - 1 - np.argmax(blocked[::-1], axis=0), -1)
    xa = np.where(idx >= 0, X[np.clip(idx, 0, None)] + H / 2, X[0])
    xa[idx == sub.shape[0] - 1] = np.nan
    return xa                               # shape (ny, nz)
variants = {}
plug = label == names.index("servo_J1")
XX = X[:, None, None]
Fs = free_h & ~lower
variants["strict (T_stred path blocked)"] = Fs
variants["after_T5 (servo fitted after T_stred, from the side)"] = free_h.copy()
# J1 plug reservation shrunk to the top 9 mm (x 15.7..27, z >= -57.3): optimistic, connector geometry UNVERIFIED
Zg = Z[None, None, :]
plug_box = (XX > 15.7) & (XX < 27.3) & (np.abs(Y)[None, :, None] <= 8.3) & (Zg < -57.3) & (Zg > -66.8)
v3 = free_h | (plug_box & ~lower & D["interior"])
variants["after_T5 + J1 plug zone shrunk to z >= -57.3"] = v3
L_, W_, E_ = 23.2, 12.1, 5.9
from scipy.ndimage import maximum_filter
def best_xin(F, xmax):
    xa = xin_avail(F, xmax)
    ny, nz = xa.shape
    A2 = np.where(np.isnan(xa), 1e3, xa)
    out = []
    for orient in ("L_along_y", "L_along_z"):
        for sense in (1, -1):
            if orient == "L_along_y":
                dy0, dy1 = sorted((-E_ * sense, (L_ - E_) * sense)); dz0, dz1 = -W_ / 2, W_ / 2
            else:
                dz0, dz1 = sorted((-E_ * sense, (L_ - E_) * sense)); dy0, dy1 = -W_ / 2, W_ / 2
            ky = int(round((dy1 - dy0) / H)); kz = int(round((dz1 - dz0) / H))
            M = maximum_filter(A2, size=(ky, kz), mode="constant", cval=1e3)
            cy = 0.5 * (dy0 + dy1); cz = 0.5 * (dz0 + dz1)
            jj, kk = np.nonzero(M < 999)
            for j, k in zip(jj, kk):
                out.append((float(M[j, k]), orient, sense, float(Y[j] - cy), float(Z[k] - cz)))
    out.sort()
    return out
tab = []
for Hc in (21.5, 25.25):
    for (w, nm) in ((3.0, "Dyneema drum 3.0"), (4.6, "GT2 3 mm belt + 0.8 flanges"), (7.6, "GT2 6 mm belt + flanges")):
        for r in (5.0, 7.0):
            xb1 = A[f"wall2.2_rf{r}"]
            xface = xb1 - w - 0.3
            need = xface - Hc
            row = dict(H_case=Hc, pulley=nm, r_f=r, xb1=xb1, x_face=round(xface, 2), x_in_required=round(need, 2))
            for vn, F in variants.items():
                o = best_xin(F, xface)
                row["margin " + vn] = round(need - o[0][0], 2) if o else None
                row["best " + vn] = (round(o[0][0], 2), o[0][1], o[0][2], round(o[0][3], 1), round(o[0][4], 1)) if o else None
            tab.append(row); print(row)
res["C_budget"] = tab
json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
