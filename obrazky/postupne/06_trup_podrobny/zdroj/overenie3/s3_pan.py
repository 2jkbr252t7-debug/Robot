# pan sweep: rigid rotation of the stage group about z through (0,0); own sampling + exact point-triangle distances
import json, os, sys, numpy as np, time, pickle
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
p = json.load(open(T4 + '/parts.json'))
info = {q['name']: q for q in p['parts']}
ROT = [n for n, q in info.items() if q['group'] in ('P', 'L') and n not in ('ffc_par',)]
def rmax(bb):  # bb = x0,x1,y0,y1,z0,z1
    return max(np.hypot(x, y) for x in bb[:2] for y in bb[2:4])
def rmin(bb):
    dx = 0 if bb[0] <= 0 <= bb[1] else min(abs(bb[0]), abs(bb[1])); dy = 0 if bb[2] <= 0 <= bb[3] else min(abs(bb[2]), abs(bb[3]))
    return np.hypot(dx, dy)
zr = (min(info[n]['bbox'][4] for n in ROT), max(info[n]['bbox'][5] for n in ROT)); Rm = max(rmax(info[n]['bbox']) for n in ROT)
print("rotating:", len(ROT), "z", zr, "rmax", round(Rm, 2))
STA = [n for n, q in info.items() if q['group'] == 'T' and rmin(q['bbox']) < Rm + 1.5 and q['bbox'][4] < zr[1] + 1.5 and q['bbox'][5] > zr[0] - 1.5]
print("static candidates:", STA)
hR, hS = 0.3, 0.25
rp = []; rid = []
for i, n in enumerate(ROT):
    P = sample_surface(load_stl(f"{T4}/stl/{n}.stl"), hR, thin=0.8); rp.append(P); rid.append(np.full(len(P), i))
RP = np.concatenate(rp); RID = np.concatenate(rid)
sm = {}; sp = []; sid = []
for i, n in enumerate(STA):
    tr = load_stl(f"{T4}/stl/{n}.stl")
    c = tr.mean(1); m = (np.hypot(c[:, 0], c[:, 1]) < Rm + 4) & (c[:, 2] > zr[0] - 4) & (c[:, 2] < zr[1] + 4)
    if not m.any(): continue
    M = Mesh(tr[m], hS); M.full = Mesh(tr, hS); sm[i] = M
    sp.append(M.samp); sid.append(np.full(len(M.samp), i))
SP = np.concatenate(sp); SID = np.concatenate(sid)
tree = cKDTree(SP)
print("rot samples", len(RP), "static samples", len(SP), flush=True)
fine = lambda a, b, s: list(np.round(np.arange(a, b + 1e-9, s), 3))
angles = sorted(set(fine(-100, -91, 0.5) + fine(-91, -88, 0.1) + fine(-88, 88, 1.0) + fine(88, 91, 0.1) + fine(91, 100, 0.5)))
res = {}   # (rot, sta) -> list of (angle, dist, point(stage frame, rotated), inside)
t0 = time.time()
for a in angles:
    Q = rotz(RP, a)
    d, j = tree.query(Q, k=1, distance_upper_bound=1.6)
    ok = np.isfinite(d)
    if not ok.any(): continue
    qi = np.nonzero(ok)[0]; pr = RID[qi] * 1000 + SID[j[qi]]
    for code in np.unique(pr):
        m = qi[pr == code]; ri, si = int(code // 1000), int(code % 1000)
        # exact refine of the closest 150 candidates
        mm = m[np.argsort(d[m])[:150]]
        de, _ = sm[si].dist(Q[mm], k=8)
        ins = sm[si].full.inside(Q[mm]) if d[mm].min() < 0.5 else np.zeros(len(mm), bool)
        k = np.argmin(de)
        depth = float(de[ins].max()) if ins.any() else 0.0
        res.setdefault((ROT[ri], STA[si]), []).append((a, float(de[k]), Q[mm][k].round(2).tolist(), int(ins.sum()), depth))
    if abs(a - round(a)) < 1e-6 and int(round(a)) % 15 == 0: print("angle", a, round(time.time() - t0, 1), "s", flush=True)
pickle.dump(res, open(os.path.join(os.path.dirname(__file__), "s3_pan.pkl"), "wb"))
print("\nPAIR SUMMARY within the range -90.0 .. +90.0 (min clearance; inside counts) and at the ends")
for (r, s), L in sorted(res.items()):
    A = np.array([x[0] for x in L]); D = np.array([x[1] for x in L]); I = np.array([x[3] for x in L]); DP = np.array([x[4] for x in L])
    inr = (A >= -90.0001) & (A <= 90.0001)
    if not inr.any(): 
        k = np.argmin(D); print(f"{r:16s} x {s:16s} only outside +-90: min {D[k]:.3f} at {A[k]}"); continue
    k = np.nonzero(inr)[0][np.argmin(D[inr])]
    def at(ang):
        m = np.nonzero(np.abs(A - ang) < 1e-6)[0]
        return f"{D[m[0]]:.3f}{'(in %d, depth %.2f)' % (I[m[0]], DP[m[0]]) if I[m[0]] else ''}" if len(m) else "  -  "
    pen = f"  PEN max depth {DP[inr].max():.3f} at {A[inr][np.argmax(DP[inr])]}" if I[inr].any() else ""
    print(f"{r:16s} x {s:16s} min {D[k]:.3f} at pan {A[k]:7.2f} pt {L[k][2]} | -90: {at(-90.0)}  0: {at(0.0)}  +90: {at(90.0)}{pen}")
