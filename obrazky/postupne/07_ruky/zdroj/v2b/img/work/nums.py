import sys, json, numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2 as G
import t4_common as C
V = G.V
out = {}
rows, top, bot = V.pebble_rows(200, 300)
for dx in (0.0, -1.0):
    W = V.to_world(rows.reshape(-1, 3), dx)
    out[f"xmax_dx{dx}"] = float(W[:, 0].max())
    out[f"xmin_dx{dx}"] = float(W[:, 0].min())
    out[f"zrange_dx{dx}"] = [float(W[:, 2].min()), float(W[:, 2].max())]
    # front-view silhouette gap per z
    zs = np.arange(-60, 0, 0.5)
    g = []
    for z in zs:
        m = np.abs(W[:, 2] - z) < 0.35
        if not m.any():
            continue
        xa = W[m, 0].min()
        ys = np.linspace(-34, 34, 681)
        xt = max(C.x_surface(y, z) for y in ys)
        g.append((float(z), float(xa), float(xt), float(xa - xt)))
    g = np.array(g)
    k = int(np.argmin(g[:, 3]))
    out[f"front_gap_dx{dx}"] = g[k].tolist()
    out[f"front_gap_at_axis_dx{dx}"] = g[np.argmin(abs(g[:, 0] + 17))].tolist()
print(json.dumps(out, indent=1))
json.dump(out, open("nums.json", "w"), indent=1)
