import numpy as np
def inside_poly(P, poly):
    """even-odd point in polygon (vectorised)"""
    x, y = P[:, 0], P[:, 1]; ins = np.zeros(len(P), bool); n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = (x2 - x1) * (y - y1) / (y2 - y1) + x1
        ins ^= c & (x < xi)
    return ins
