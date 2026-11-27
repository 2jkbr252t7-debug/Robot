"""half-plane slices (x, r) through the shoulder axis at a given azimuth -> PNG with several meshes overlaid"""
import sys, os, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw
import mio
YA, ZA = 3.0, -17.0


def slice_xr(T, az):
    t = math.radians(az)
    e = np.array([0.0, math.cos(t), math.sin(t)])          # in-plane radial direction
    n = np.array([0.0, -math.sin(t), math.cos(t)])         # plane normal
    O = np.array([0.0, YA, ZA])
    d = (T - O) @ n                                         # (N, 3)
    segs = []
    for k in range(len(T)):
        dk = d[k]
        s = np.sign(dk)
        if (s > 0).all() or (s < 0).all():
            continue
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dk[i] == 0:
                pts.append(T[k, i])
            if dk[i] * dk[j] < 0:
                a = dk[i] / (dk[i] - dk[j]); pts.append(T[k, i] + a * (T[k, j] - T[k, i]))
        if len(pts) >= 2:
            p, q = pts[0], pts[1]
            rp, rq = (p - O) @ e, (q - O) @ e
            if rp >= 0 or rq >= 0:
                segs.append(((p[0], rp), (q[0], rq)))
    return segs


def draw(layers, az, box, scale, path, title=""):
    x0, x1, r0, r1 = box
    W, H = int((x1 - x0) * scale) + 40, int((r1 - r0) * scale) + 60
    im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
    def P(x, r):
        return 20 + (x - x0) * scale, H - 20 - (r - r0) * scale
    for gx in np.arange(math.ceil(x0), x1 + 1e-9, 1.0):
        dr.line([P(gx, r0), P(gx, r1)], fill=(235, 235, 235) if gx % 5 else (200, 200, 200))
    for gr in np.arange(math.ceil(r0), r1 + 1e-9, 1.0):
        dr.line([P(x0, gr), P(x1, gr)], fill=(235, 235, 235) if gr % 5 else (200, 200, 200))
    for T, col in layers:
        for (a, b) in slice_xr(T, az):
            dr.line([P(*a), P(*b)], fill=col, width=2)
    dr.text((10, 5), f"{title} az {az}  grid 1 mm (5 mm darker)  x {x0}..{x1}  r {r0}..{r1}", fill="black")
    im.save(path)


if __name__ == "__main__":
    import json
    spec = json.loads(sys.argv[1])
    layers = [(mio.load(p), tuple(c)) for p, c in spec["layers"]]
    draw(layers, spec["az"], spec["box"], spec.get("scale", 40), spec["out"], spec.get("title", ""))
