"""B vs the approved pebble: approved-section level of B's surface (<= 1 = inside) per u band, and how far B leaves it"""
import sys, json
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/overenie_B"); import armsurf as AS
VA = AS.VA
us = np.r_[np.geomspace(1e-5, 0.03, 400), np.linspace(0.03, 0.5, 2000), np.linspace(0.5, 1 - 1e-5, 1500)]
th = np.linspace(-np.pi, np.pi, 2880, endpoint=False)
out = {}
for lo, hi in ((0, 0.03), (0.03, 0.5), (0.5, 1.0)):
    m = (us >= lo) & (us <= hi)
    lev = []
    for u in us[m]:
        P = AS.surf_pt("B", np.full(len(th), u), th)
        hw, ht = VA._base(u)
        lev.append(float(((np.abs(P[:, 0]) / ht) ** 2.3 + (np.abs(P[:, 1]) / hw) ** 2.3).max()))
    lev = np.array(lev)
    out[f"u{lo}-{hi}"] = dict(max_level=round(float(lev.max()), 8), at_u=round(float(us[m][lev.argmax()]), 4))
print(json.dumps(out))
# inner face on the centre line vs approved (-ht)
for u in (0.03, 0.05, 0.1, 0.22, 0.3, 0.4, 0.5, 0.6, 0.8):
    fi, fo, sx = VA.faces("B", u); hw, ht = VA._base(u)
    print(u, "inner face", round(float(fi), 3), "approved", round(-float(ht), 3), "outer", round(float(fo), 3), "approved", round(float(ht), 3), "seam", round(float(sx), 3))
json.dump(out, open("subset_B.json", "w"), indent=1)
