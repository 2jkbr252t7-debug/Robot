"""JUDGE: hand check of the new shoulder column under T4 load L5 (10 N along X at the arm tip, 72 mm from the axis, arm at
+135 deg -> tip z +33.9; M(z) = 10 (33.9 - z) N.mm), column alone (no help from the side cap), Kt 1.3, allowable 8.5 MPa (T4).
Sections in the x-y plane, bending about Y.  Rectangles (x0, x1, y0, y1).  Optional D3 steel rods (E 200 GPa) vs resin E 2.5 GPa."""
import json, math
E_R, E_S = 2500.0, 200000.0
def sec(rects, rods=()):
    A = sum((x1 - x0) * (y1 - y0) for x0, x1, y0, y1 in rects)
    xc = sum((x1 - x0) * (y1 - y0) * (x0 + x1) / 2 for x0, x1, y0, y1 in rects) / A
    I = sum((y1 - y0) * (x1 - x0) ** 3 / 12 + (x1 - x0) * (y1 - y0) * ((x0 + x1) / 2 - xc) ** 2 for x0, x1, y0, y1 in rects)
    c = max(xc - min(r[0] for r in rects), max(r[1] for r in rects) - xc)
    EI_r = E_R * I
    EI_s = sum(E_S * (math.pi * 1.5 ** 4 / 4 + math.pi * 1.5 ** 2 * (xr - xc) ** 2) for xr in rods)
    return dict(A=round(A, 1), xc=round(xc, 2), I=round(I, 1), Z=round(I / c, 1), share_resin=round(EI_r / (EI_r + EI_s), 3))
def M(z): return 10.0 * (33.9 - z)
out = {}
low = [(31.5, 41.5, 9.2, 15.5), (32.7, 41.5, -20.0, -14.6), (30.5, 32.65, -14.6, 9.2)]     # below the deck: C channel
up = [(34.4, 41.5, 9.2, 15.5), (34.4, 41.5, -20.0, -14.6)]                                  # beside the servo top: 2 legs
k3 = [(34.4, 42.0, 9.5, 15.5), (34.4, 42.0, -21.0, -14.6)]                                  # K3 as published (2 legs)
for name, rects, z in (("judge C-channel z -66.5", low, -66.5), ("judge C-channel z -72", low, -72.0),
                       ("judge legs z -48", up, -48.0), ("judge legs z -40", up, -40.0), ("judge legs z -30", up, -30.0),
                       ("K3 legs z -48", k3, -48.0), ("K3 legs z -66.5", k3, -66.5)):
    for rods in ((), (38.0, 38.0)):
        s = sec(rects, rods)
        sig = M(z) * 1.3 / s["Z"] * s["share_resin"]
        key = f"{name}{' + 2 rods D3' if rods else ''}"
        out[key] = dict(M_Nmm=round(M(z)), **s, sigma_MPa=round(sig, 2), ok=sig <= 8.5)
        if rods:
            out[key]["rod_sigma_MPa"] = round(M(z) * (1 - s["share_resin"]) / 2 / (math.pi * 3 ** 3 / 32), 1)
        print(key, out[key])
json.dump(out, open("column_calc.json", "w"), indent=1)
