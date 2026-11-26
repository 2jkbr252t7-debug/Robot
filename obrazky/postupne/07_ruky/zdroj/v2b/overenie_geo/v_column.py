"""VERIFIER: column legs under L5 including the torsion from the off-axis tip load (judge hand check: bending about Y only).
L5 = 10 N along X at the arm tip, arm at +135 deg.  Tip at 53.75 mm from the shoulder axis (v_arm.json) -> y_tip = 3 - 38.0,
z_tip = -17 + 38.0.  At the shoulder: Fx 10, My = 10*38, Mz = 10*38 (torsion about Z).  Per z slice of the merged fill voxels the
back (y > 0) and front (y < 0) legs are separated; My(z) split by EI, torsion as an x shear couple V = Mz/d; leg moment from V
taken as V*h/2 (fixed-guided, h = column height 52) and V*(z_top - z) (top free) as bounds.  Kt 1.3.  Column alone (no side cap)."""
import json, math, sys
import numpy as np
side = sys.argv[1] if len(sys.argv) > 1 else "L"
P = np.load(f"/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_{side}.npz")["P"].astype(float)
if side == "R": P[:, 0] *= -1
h = 0.5
tip = 53.75; a = math.radians(135.0)
y_tip, z_tip = 3.0 - tip * math.sin(a), -17.0 - tip * math.cos(a)
Fx = 10.0; My0 = Fx * (z_tip + 17.0); Mz = Fx * abs(y_tip - 3.0)
rows = []
for z in np.unique(P[:, 2]):
    S = P[P[:, 2] == z]
    legs = {}
    for nm, m in (("back", S[:, 1] > 0), ("front", S[:, 1] < 0)):
        Q = S[m]
        if len(Q) == 0: continue
        A = len(Q) * h * h; xc = Q[:, 0].mean(); yc = Q[:, 1].mean()
        I = ((Q[:, 0] - xc) ** 2).sum() * h * h + len(Q) * h ** 4 / 12
        c = max(xc - (Q[:, 0].min() - h / 2), Q[:, 0].max() + h / 2 - xc)
        legs[nm] = dict(A=A, xc=xc, yc=yc, I=I, Z=I / c)
    if len(legs) < 2: continue
    d = abs(legs["back"]["yc"] - legs["front"]["yc"])
    V = Mz / d
    My = My0 + Fx * (-17.0 - z)
    It = legs["back"]["I"] + legs["front"]["I"]
    out = dict(z=float(z), d=round(d, 1), V_couple=round(V, 1), My=round(My, 0))
    for nm in ("back", "front"):
        L = legs[nm]
        Mb = My * L["I"] / It
        for lab, Mv in (("guided", V * 52.0 / 2), ("free", V * (-26.0 - z + 9.0))):
            out[f"{nm}_{lab}_MPa"] = round(1.3 * (Mb + Mv) / L["Z"], 2)
        out[f"{nm}_noTorsion_MPa"] = round(1.3 * Mb / L["Z"], 2)
        out[f"{nm}_Z"] = round(L["Z"], 1)
    rows.append(out)
mx = {k: max(r[k] for r in rows) for k in rows[0] if k.endswith("MPa")}
res = dict(side=side, y_tip=round(y_tip, 2), z_tip=round(z_tip, 2), My_shoulder=round(My0, 0), Mz=round(Mz, 0), max=mx,
           worst_rows=sorted(rows, key=lambda r: -max(r["back_guided_MPa"], r["front_guided_MPa"]))[:4])
print(json.dumps(res, indent=1))
json.dump(res, open(f"v_column_{side}.json", "w"), indent=1)
