"""overenie_pevnost - helpers for the STRENGTH verification of the NOVA mini T4 torso (resin, T4_zivica.md).
Own code: nothing is imported from the design / check scripts.  Geometry is MEASURED on the exported STL files
(absolute deflection 0.01 mm): plane sections (area, centroid, second moments by scan-line integration), line probes
(material chords along a line), z-buffers.  Runs under /opt/venv/cad/bin/python (numpy, PIL)."""
import os, struct, json, math
import numpy as np

T4 = "/tmp/claude-0/gapwf/fin/T4"
STL = os.path.join(T4, "stl")
BSTL = "/tmp/claude-0/gapwf/fin/B/stl"
OUT = os.path.join(T4, "overenie_pevnost", "out")
os.makedirs(OUT, exist_ok=True)

# ---- Z2 material model (T4_zivica.md) ---------------------------------------------------------------------------------
UTS, FLEX, E_MOD = 35.0, 50.0, 1800.0        # MPa
A_STATIC, A_NOTCH = 12.0, 6.0                # allowable: static / sustained or un-filleted notch
SF_ABUSE = 2.0                               # Z4: safety factor >= 2 on the allowables for abuse cases (L1..L6)

_CACHE = {}


def load(name):
    """binary STL -> (n, 3, 3) float64"""
    if name in _CACHE:
        return _CACHE[name]
    p = os.path.join(STL, name + ".stl")
    if not os.path.exists(p):
        p = os.path.join(BSTL, name + ".stl")
    with open(p, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        a = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    t = a["v"].astype(np.float64)
    _CACHE[name] = t
    return t


def bbox(t):
    v = t.reshape(-1, 3)
    return v.min(0), v.max(0)


def volume(t):
    return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6.0)


def section(t, axis, val):
    """plane section: segments (m, 2, 2) in the two remaining coordinates (order: x,y,z without `axis`)"""
    k = "xyz".index(axis)
    oth = [i for i in range(3) if i != k]
    d = t[:, :, k] - val
    d = np.where(d == 0.0, 1e-9, d)
    s = d > 0
    cnt = s.sum(1)
    m = (cnt == 1) | (cnt == 2)
    tt, dd, ss = t[m], d[m], s[m]
    # the lone vertex (the one whose sign differs from the other two)
    lone = np.where(ss.sum(1) == 1, np.argmax(ss, 1), np.argmin(ss, 1))
    idx = np.arange(len(tt))
    a = tt[idx, lone]; da = dd[idx, lone]
    b = tt[idx, (lone + 1) % 3]; db = dd[idx, (lone + 1) % 3]
    c = tt[idx, (lone + 2) % 3]; dc = dd[idx, (lone + 2) % 3]
    p = a + (b - a) * (da / (da - db))[:, None]
    q = a + (c - a) * (da / (da - dc))[:, None]
    return np.stack([p[:, oth], q[:, oth]], 1)


def scan(seg, window=None, h=0.02, along=0):
    """scan-line integration of a section (even-odd).  seg (m,2,2) in (u, w); scan lines run along u (along=0) or w
    (along=1).  window = (u0, u1, w0, w1).  Returns dict: A, cu, cw, Iu (about the centroidal axis parallel to u,
    i.e. integral of (w-cw)^2), Iw, Iuw, bounds, and the interval list (for pictures)."""
    if along == 1:
        seg = seg[:, :, ::-1]
        if window is not None:
            window = (window[2], window[3], window[0], window[1])
    lo = np.minimum(seg[:, 0, 1], seg[:, 1, 1]); hi = np.maximum(seg[:, 0, 1], seg[:, 1, 1])
    if window is None:
        window = (seg[:, :, 0].min() - 1, seg[:, :, 0].max() + 1, lo.min(), hi.max())
    u0, u1, w0, w1 = window
    n = max(1, int(round((w1 - w0) / h)))
    hh = (w1 - w0) / n
    A = Su = Sw = Suu = Sww = Suw = 0.0
    iv = []
    order = np.argsort(lo)
    lo_s = lo[order]
    for j in range(n):
        w = w0 + (j + 0.5) * hh + 1.37e-7
        k1 = np.searchsorted(lo_s, w)
        cand = order[:k1]
        cand = cand[hi[cand] > w]
        if len(cand) == 0:
            continue
        s = seg[cand]
        tpar = (w - s[:, 0, 1]) / (s[:, 1, 1] - s[:, 0, 1])
        x = np.sort(s[:, 0, 0] + tpar * (s[:, 1, 0] - s[:, 0, 0]))
        if len(x) % 2:
            x = x[:-1]
        a = np.clip(x[0::2], u0, u1); b = np.clip(x[1::2], u0, u1)
        L = b - a
        keep = L > 1e-9
        a, b, L = a[keep], b[keep], L[keep]
        if len(L) == 0:
            continue
        iv.append((w, a, b))
        A += L.sum() * hh
        Su += ((a + b) / 2 * L).sum() * hh
        Sw += w * L.sum() * hh
        Suu += ((b ** 3 - a ** 3) / 3).sum() * hh
        Sww += (w * w + hh * hh / 12) * L.sum() * hh
        Suw += w * ((a + b) / 2 * L).sum() * hh
    if A <= 0:
        return dict(A=0.0, iv=[], window=window)
    cu, cw = Su / A, Sw / A
    Iu = Sww - A * cw * cw          # about the axis parallel to u through the centroid (bending in the w direction)
    Iw = Suu - A * cu * cu
    Iuw = Suw - A * cu * cw
    us = np.concatenate([np.concatenate([a, b]) for _, a, b in iv]); ws = np.array([w for w, _, _ in iv])
    r = dict(A=A, cu=cu, cw=cw, Iu=Iu, Iw=Iw, Iuw=Iuw, umin=us.min(), umax=us.max(), wmin=ws.min() - hh / 2, wmax=ws.max() + hh / 2,
             iv=iv, window=window, h=hh)
    if along == 1:      # swap names back: caller's u is our w
        r = dict(A=A, cu=cw, cw=cu, Iu=Iw, Iw=Iu, Iuw=Iuw, umin=r["wmin"], umax=r["wmax"], wmin=r["umin"], wmax=r["umax"],
                 iv=iv, window=(window[2], window[3], window[0], window[1]), h=hh, swapped=True)
    return r


def sec(name, axis, val, window=None, h=0.02):
    """section properties of part `name` in the plane axis = val; window in the two remaining coords (order x,y,z)"""
    return scan(section(load(name), axis, val), window, h)


def zmods(r):
    """section moduli: Zu_plus / Zu_minus (bending about the u-parallel axis; fibres at +w / -w) and Zw likewise"""
    return dict(Zu_p=r["Iu"] / max(1e-9, r["wmax"] - r["cw"]), Zu_m=r["Iu"] / max(1e-9, r["cw"] - r["wmin"]),
                Zw_p=r["Iw"] / max(1e-9, r["umax"] - r["cu"]), Zw_m=r["Iw"] / max(1e-9, r["cu"] - r["umin"]))


def picture(r, path, scale=24, grid=1.0, marks=()):
    """PNG of a section (material dark), grid lines every `grid` mm; marks = [(u, w, label)]"""
    from PIL import Image, ImageDraw
    if not r.get("iv"):
        return None
    sw = r.get("swapped", False)
    u0, u1, w0, w1 = r["window"]
    if sw:      # stored intervals are along the caller's w
        W, H = int((u1 - u0) * scale) + 1, int((w1 - w0) * scale) + 1
    else:
        W, H = int((u1 - u0) * scale) + 1, int((w1 - w0) * scale) + 1
    im = Image.new("RGB", (W, H), (255, 255, 255))
    px = im.load()
    for w, a, b in r["iv"]:
        for aa, bb in zip(a, b):
            if not sw:
                y = H - 1 - int((w - w0) * scale)
                xa, xb = int((aa - u0) * scale), int((bb - u0) * scale)
                for yy in range(max(0, y - int(r["h"] * scale / 2) - 1), min(H, y + int(r["h"] * scale / 2) + 1)):
                    for x in range(max(0, xa), min(W, xb + 1)):
                        px[x, yy] = (60, 60, 70)
            else:
                x = int((w - u0) * scale)
                ya, yb = H - 1 - int((bb - w0) * scale), H - 1 - int((aa - w0) * scale)
                for xx in range(max(0, x - int(r["h"] * scale / 2) - 1), min(W, x + int(r["h"] * scale / 2) + 1)):
                    for y in range(max(0, ya), min(H, yb + 1)):
                        px[xx, y] = (60, 60, 70)
    d = ImageDraw.Draw(im)
    g = math.ceil(u0 / grid) * grid
    while g <= u1:
        x = int((g - u0) * scale)
        d.line([(x, 0), (x, H)], fill=(255, 120, 120) if abs(g % 5) < 1e-6 else (200, 220, 255))
        if abs(g % 5) < 1e-6:
            d.text((x + 2, 2), f"{g:g}", fill=(200, 0, 0))
        g += grid
    g = math.ceil(w0 / grid) * grid
    while g <= w1:
        y = H - 1 - int((g - w0) * scale)
        d.line([(0, y), (W, y)], fill=(255, 120, 120) if abs(g % 5) < 1e-6 else (200, 220, 255))
        if abs(g % 5) < 1e-6:
            d.text((2, y + 2), f"{g:g}", fill=(200, 0, 0))
        g += grid
    for u, w, lab in marks:
        x, y = int((u - u0) * scale), H - 1 - int((w - w0) * scale)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(0, 160, 0))
        d.text((x + 5, y - 5), lab, fill=(0, 120, 0))
    im.save(path)
    return path


def probe(t, p0, d):
    """material chords along the line p0 + s*d (|d| normalised): sorted crossings s, list of (s_in, s_out)"""
    p0 = np.asarray(p0, float); d = np.asarray(d, float); d = d / np.linalg.norm(d)
    # jitter against edge hits
    p0 = p0 + np.array([1.3e-6, 2.1e-6, 0.7e-6])
    e1 = t[:, 1] - t[:, 0]; e2 = t[:, 2] - t[:, 0]
    h = np.cross(d, e2)
    a = np.einsum("ij,ij->i", e1, h)
    ok = np.abs(a) > 1e-12
    f = np.zeros_like(a); f[ok] = 1.0 / a[ok]
    s = p0 - t[:, 0]
    u = f * np.einsum("ij,ij->i", s, h)
    q = np.cross(s, e1)
    v = f * (q @ d)
    tt = f * np.einsum("ij,ij->i", e2, q)
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    x = np.sort(tt[m])
    if len(x) % 2:
        # drop near-duplicate hits (shared edge)
        keep = [x[0]]
        for xx in x[1:]:
            if xx - keep[-1] > 1e-6:
                keep.append(xx)
        x = np.array(keep)
    return [(float(x[i]), float(x[i + 1])) for i in range(0, len(x) - 1, 2)]


def chords(name, p0, d, lo=-1e9, hi=1e9):
    """material intervals of part `name` along the line, clipped to [lo, hi], as (start, end, length)"""
    out = []
    for a, b in probe(load(name), p0, d):
        a2, b2 = max(a, lo), min(b, hi)
        if b2 - a2 > 1e-6:
            out.append((round(a2, 3), round(b2, 3), round(b2 - a2, 3)))
    return out


def zbuf(t, x0, x1, y0, y1, h, top=True):
    """z-buffer over an xy window: max z (top=True) or min z of the mesh on a grid of spacing h (nan where empty)"""
    nx, ny = int(round((x1 - x0) / h)), int(round((y1 - y0) / h))
    Z = np.full((ny, nx), -np.inf if top else np.inf)
    mn = t[:, :, :2].min(1); mx = t[:, :, :2].max(1)
    m = (mx[:, 0] >= x0) & (mn[:, 0] <= x1) & (mx[:, 1] >= y0) & (mn[:, 1] <= y1)
    for tri in t[m]:
        a, b, c = tri
        n = np.cross(b - a, c - a)
        if abs(n[2]) < 1e-12:
            continue
        ix0 = max(0, int((min(a[0], b[0], c[0]) - x0) / h)); ix1 = min(nx - 1, int((max(a[0], b[0], c[0]) - x0) / h))
        iy0 = max(0, int((min(a[1], b[1], c[1]) - y0) / h)); iy1 = min(ny - 1, int((max(a[1], b[1], c[1]) - y0) / h))
        if ix1 < ix0 or iy1 < iy0:
            continue
        xs = x0 + (np.arange(ix0, ix1 + 1) + 0.5) * h; ys = y0 + (np.arange(iy0, iy1 + 1) + 0.5) * h
        X, Y = np.meshgrid(xs, ys)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-14:
            continue
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not ins.any():
            continue
        zz = l1 * a[2] + l2 * b[2] + l3 * c[2]
        sub = Z[iy0:iy1 + 1, ix0:ix1 + 1]
        if top:
            sub[ins] = np.maximum(sub[ins], zz[ins])
        else:
            sub[ins] = np.minimum(sub[ins], zz[ins])
    Z[~np.isfinite(Z)] = np.nan
    return Z


# ---- small formula helpers ---------------------------------------------------------------------------------------------
def verdict(sig, allow, abuse=False):
    """ratio of the stress to the allowable; for abuse cases Z4 asks SF >= 2 on the allowable"""
    lim = allow / (SF_ABUSE if abuse else 1.0)
    return dict(sigma=round(sig, 2), allow=allow, limit=round(lim, 2), util=round(sig / lim, 2), ok=bool(sig <= lim))


class Log:
    def __init__(self, name):
        self.path = os.path.join(OUT, name + ".log"); self.rows = []; self.f = open(self.path, "w")

    def __call__(self, *a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True); self.f.write(s + "\n"); self.f.flush()

    def row(self, **k):
        self.rows.append(k)

    def save(self, name):
        json.dump(self.rows, open(os.path.join(OUT, name + ".json"), "w"), indent=1, ensure_ascii=False, default=float)
