import json, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
p = json.load(open(T4 + '/parts.json'))
pb = json.load(open(T4 + '/rev3_backup/parts.json.bak'))
new = {q['name']: q for q in p['parts']} if isinstance(p['parts'], list) else p['parts']
old = {q['name']: q for q in pb['parts']} if isinstance(pb['parts'], list) else pb['parts']
print("n new", len(new), "n old", len(old))
print("only new:", sorted(set(new) - set(old)))
print("only old:", sorted(set(old) - set(new)))
rows = []
for n in sorted(new):
    q = new[n]
    fn = T4 + '/stl/' + n + '.stl'; fo = T4 + '/rev3_backup/stl/' + n + '.stl'
    if not os.path.exists(fn): print("MISSING new stl", n); continue
    tn = load_stl(fn); vn = volume(tn); bn = bbox(tn)
    if not os.path.exists(fo):
        rows.append((n, q.get('printed'), 'NEW', vn, None, bn, None)); continue
    to = load_stl(fo); vo = volume(to); bo = bbox(to)
    same = (tn.shape == to.shape) and np.allclose(tn, to, atol=1e-4)
    if same: continue
    rows.append((n, q.get('printed'), 'CHG', vn, vo, bn, bo))
for r in rows:
    n, pr, st, vn, vo, bn, bo = r
    print(f"{st} {n:28s} printed={pr!s:5s} V {vn:10.2f} " + (f"(old {vo:10.2f}, d {vn-vo:+8.2f})" if vo is not None else "") )
    print("     bbox new", np.round(bn, 3), "" if bo is None else "\n     bbox old " + str(np.round(bo, 3)) + "  d " + str(np.round(bn - bo, 3)))
