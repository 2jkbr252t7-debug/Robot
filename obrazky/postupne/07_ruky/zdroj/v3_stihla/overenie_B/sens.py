"""M2b in variant B: sensitivity of the governing cover wall (drive-hub cap, required 1.5 = 1.2 cover + 0.3 clearance) to an
outward axial shift of the drive hub (print / press / gauge tolerance), and the DIN 912 M4x20 case (head 4.0 instead of 2.8:
cap end 1.2 further out)."""
import sys, math, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/overenie_B"); import armsurf as AS
VA = AS.VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech"); import parts as PT
YA, ZA = 3.0, -17.0
vid = sys.argv[1] if len(sys.argv) > 1 else "B"
ARM = AS.ArmSurf(vid, 0.0, 0.5, 0.04)
drv = [p for p in PT.options()["M2b"]["parts"] if p.name == "DRV_unasac"][0]
def rev(prof, h=0.05):
    P = np.asarray(prof, float); E = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]; n = max(1, int(math.ceil(np.hypot(*(b - a)) / h)))
        E.append(a + np.linspace(0, 1, n, endpoint=False)[:, None] * (b - a))
    E = np.concatenate(E); out = []
    for x, r in E:
        n = max(1, int(2 * math.pi * r / h) + 1) if r > 1e-6 else 1
        ph = np.linspace(0, 2 * np.pi, n, endpoint=False)
        out.append(np.c_[np.full(n, x), YA + r * np.cos(ph), ZA + r * np.sin(ph)])
    return np.concatenate(out)
res = {}
for nm, shift, cap_extra in (("nominal", 0.0, 0.0), ("+0.1", 0.1, 0.0), ("+0.2", 0.2, 0.0), ("DIN912_M4x20_head4.0", 0.0, 1.2)):
    P = drv.prof.copy()
    P[:, 0] += shift
    P[P[:, 0] >= 61.7 + shift - 1e-9, 0] += cap_extra      # cap / head region grows outward
    Q = rev(P)
    Pl = VA.to_local(Q, vid, -1.0)
    ins = ARM.inside(Pl)
    dc, kc = ARM.dist(Pl, "cover"); di, ki = ARM.dist(Pl, "inner")
    w = np.where(ins, np.minimum(dc, di), -np.minimum(dc, di))
    cand = np.argsort(w)[:6]
    best = 1e9
    for c in cand:
        if w[c] > 0:
            side = "cover" if dc[c] <= di[c] else "inner"
            best = min(best, ARM.refine(Pl[c], side, kc[c] if side == "cover" else ki[c])[0])
        else:
            best = min(best, float(w[c]))
    res[nm] = dict(min_wall=round(best, 3), margin_vs_1p5=round(best - 1.5, 3))
    print(nm, res[nm])
json.dump(res, open(f"sens_{vid}_M2b.json", "w"), indent=1)
