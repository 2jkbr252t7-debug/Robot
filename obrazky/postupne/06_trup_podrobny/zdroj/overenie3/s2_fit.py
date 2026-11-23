import json, os, sys, numpy as np, time
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
p = json.load(open(T4 + '/parts.json'))
bbs = {q['name']: np.array(q['bbox'])[[0, 2, 4, 1, 3, 5]] for q in p['parts']}
def bbgap(a, b):
    g = np.maximum(np.maximum(a[:3] - b[3:], b[:3] - a[3:]), 0)
    return float(np.linalg.norm(g))
def pen(A, B, h=0.12):
    """samples of A's surface inside B: returns max depth, n inside, location; plus min clearance of outside samples"""
    lo = B.bb[:3] - 1.0; hi = B.bb[3:] + 1.0
    tr = A.tr
    m = np.all(tr.max(1) >= lo, axis=1) & np.all(tr.min(1) <= hi, axis=1)
    if not m.any(): return None
    P = sample_surface(tr[m], h)
    P = P[np.all((P >= lo) & (P <= hi), axis=1)]
    if len(P) == 0: return None
    ins = B.inside(P)
    d, Q = B.dist(P, k=6, dmax=1.5)
    out = dict(n=len(P), n_in=int(ins.sum()))
    if ins.any():
        di = d[ins]; j = np.argmax(di)
        out.update(depth=float(di[j]), at=P[ins][j].round(2).tolist(), n_deep=int((di > 0.05).sum()))
        dp = P[ins][di > 0.05]
        if len(dp): out.update(deep_bb=np.concatenate([dp.min(0), dp.max(0)]).round(2).tolist())
    do = d[~ins]
    if len(do):
        j = np.argmin(do); out.update(clear=float(do[j]), clear_at=P[~ins][j].round(2).tolist())
    return out
targets = sys.argv[1:] or ["P_sachta", "P_drziak_serva", "T_cap", "T_paluba"]
done = set()
for t in targets:
    A = part(t, 'stl', 0.2)
    for n in sorted(bbs):
        if n == t or (n, t) in done: continue
        if bbgap(bbs[t], bbs[n]) > 1.0: continue
        done.add((t, n))
        B = part(n, 'stl', 0.2)
        t0 = time.time()
        r1 = pen(A, B); r2 = pen(B, A)
        def f(r):
            if r is None: return "-"
            s = f"in {r['n_in']}/{r['n']}"
            if 'depth' in r: s += f" depth {r['depth']:.3f} at {r['at']} n>0.05: {r['n_deep']}" + (f" bb {r['deep_bb']}" if 'deep_bb' in r else "")
            if 'clear' in r: s += f" | clear {r['clear']:.3f} at {r['clear_at']}"
            return s
        flag = "  <<<" if any(r and r.get('depth', 0) > 0.05 for r in (r1, r2)) else ""
        print(f"{t} x {n}{flag}\n    A in B: {f(r1)}\n    B in A: {f(r2)}   ({time.time()-t0:.1f}s)", flush=True)
