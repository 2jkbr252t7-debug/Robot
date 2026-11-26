"""JUDGE: room for the arm hub inside the approved pebble: largest circle about the shoulder axis inside the pebble (inset 1.2)
as a function of x (dx 0 and -1), and the arm inner skin x on the axis."""
import sys, numpy as np, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import to_local, inside_local
out = {}
for dx in (0.0, -1.0):
    rows = []
    th = np.linspace(0, 2*np.pi, 180, endpoint=False)
    for x in np.arange(48.0, 66.01, 1.0):
        best = 0.0
        for r in np.arange(0.5, 16.01, 0.25):
            Q = np.c_[np.full_like(th, x), 3.0 + r*np.cos(th), -17.0 + r*np.sin(th)]
            if inside_local(to_local(Q, dx=dx), inset=1.2).all(): best = r
            else: break
        rows.append((float(x), float(best)))
    xs = np.arange(45, 60, 0.01); Q = np.c_[xs, np.full_like(xs, 3.0), np.full_like(xs, -17.0)]
    ins = inside_local(to_local(Q, dx=dx)); skin = float(xs[np.argmax(ins)])
    out[f"dx {dx}"] = dict(skin_on_axis=round(skin, 2), r_free_inset1p2=rows)
    print(dx, "skin", round(skin,2), [(x, r) for x, r in rows])
json.dump(out, open("hub.json", "w"), indent=1)
