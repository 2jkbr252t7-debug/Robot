"""B2: arm pebble room around the shoulder axis (dx -1): skin x (inset 0) and inner shell x (inset 1.2) vs radius about the axis,
min/max over azimuth; outer skin on the axis.  writes armroom.json"""
import sys, json, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import to_local, inside_local
DX = -1.0
th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
xs = np.arange(48.0, 75.0, 0.02)
out = {"dx": DX, "rows": []}
for r in (0.0, 2.0, 4.0, 5.0, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0):
    row = {"r": r}
    for inset in (0.0, 1.2):
        first, last = [], []
        for t in (th if r > 0 else [0.0]):
            Q = np.c_[xs, np.full_like(xs, 3.0 + r * np.cos(t)), np.full_like(xs, -17.0 + r * np.sin(t))]
            ins = inside_local(to_local(Q, dx=DX), inset=inset)
            if ins.any():
                first.append(xs[np.argmax(ins)]); last.append(xs[len(ins) - 1 - np.argmax(ins[::-1])])
            else:
                first.append(np.nan); last.append(np.nan)
        first, last = np.array(first), np.array(last)
        row[f"inset{inset}"] = dict(x_in_min=round(float(np.nanmin(first)), 2), x_in_max=round(float(np.nanmax(first)), 2),
                                    x_out_min=round(float(np.nanmin(last)), 2), x_out_max=round(float(np.nanmax(last)), 2),
                                    n_miss=int(np.isnan(first).sum()))
    out["rows"].append(row)
    print(row)
json.dump(out, open("armroom.json", "w"), indent=1)
