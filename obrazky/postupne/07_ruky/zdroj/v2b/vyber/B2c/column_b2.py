"""B2: hand check of the v2 shoulder column with STANDARD SCREWS instead of the cut silver-steel rods (rule a/b).
Method = judge's column_calc.py (T4 load L5: 10 N along X at the arm tip, arm at +135 deg -> tip z +33.9,
M(z) = 10 (33.9 - z) N.mm; column alone; Kt 1.3; allowable 8.5 MPa; sections in the x-y plane, bending about Y;
steel transformed by E ratio 200/2.5 GPa).
Reinforcement B2 (left; right = mirror):
  back leg : DIN 912 M3x40 from the T_spodok underside, head in a 3.2 deep counterbore at z -78 -> thread z -75 .. -35,
             axis (38.0, 12.35), bonded with 2K epoxy in a printed D3.3 blind hole
  front leg: DIN 912 M3x30, same way -> z -75 .. -45, axis (38.0, -17.3)
  screw core d3 = 2.387 mm (ISO 724) for stiffness; a 5 mm development length is removed at the screw top
  (no credit for the last 5 mm), so the back screw counts only up to z -40, the front one up to z -50.
Geometry rows:
  'judge' = the judge's simplified 2-leg section (both legs x 34.4..41.5) - for comparison with column_calc.json
  'v2 real' = back leg x 34.4..41.5 (x 34.4..38.4 above z -33), front leg x 34.4..41.5 below z -44.5, strut x 34.4..38.4,
              y -20..-9 above z -44.5
  'B2' = 'v2 real' + back leg widened toward -Y to y 7.5 for z > -44.5 (above the servo top; clear of the coupler r 3.5 and
         of the pinion-shaft insertion path, checked in chk/paths), + strut widened to x 34.4..39.6 for z -44.5..-33
         (the strut must stay >= 0.5 from T_bok_L, 0.70 in v2 at x 38.4 -> checked)
writes column_b2.json"""
import json, math, os
E_R, E_S = 2500.0, 200000.0
D3 = 2.387
DEV = 5.0


def sec(rects, rods=()):
    A = sum((x1 - x0) * (y1 - y0) for x0, x1, y0, y1 in rects)
    xc = sum((x1 - x0) * (y1 - y0) * (x0 + x1) / 2 for x0, x1, y0, y1 in rects) / A
    I = sum((y1 - y0) * (x1 - x0) ** 3 / 12 + (x1 - x0) * (y1 - y0) * ((x0 + x1) / 2 - xc) ** 2 for x0, x1, y0, y1 in rects)
    c = max(xc - min(r[0] for r in rects), max(r[1] for r in rects) - xc)
    EI_r = E_R * I
    a = math.pi * D3 ** 2 / 4; i0 = math.pi * D3 ** 4 / 64
    EI_s = sum(E_S * (i0 + a * (xr - xc) ** 2) for xr in rods)
    return dict(A=round(A, 1), xc=round(xc, 2), I=round(I, 1), Z=round(I / c, 1), share_resin=round(EI_r / (EI_r + EI_s), 3))


def M(z):
    return 10.0 * (33.9 - z)


def rects(z, kind):
    if kind == "judge":
        return [(34.4, 41.5, 9.2, 15.5), (34.4, 41.5, -20.0, -14.6)]
    back = (34.4, 41.5 if z <= -33.0 else 38.4, 9.2, 15.5)
    if kind == "B2" and z > -44.5:
        back = (back[0], back[1], 7.5, 15.5)
    front = (34.4, 41.5, -20.0, -14.6) if z <= -44.5 else (34.4, 39.6 if (kind == "B2" and z <= -33.0) else 38.4, -20.0, -9.0)
    return [back, front]


def screws(z):
    out = []
    if -75.0 <= z <= -35.0 - DEV:
        out.append(38.0)
    if -75.0 <= z <= -45.0 - DEV:
        out.append(38.0)
    return out


out = {}
for kind in ("judge", "v2 real", "B2"):
    for z in (-48.0, -46.0, -44.0, -42.0, -40.0, -38.0, -36.0, -34.0, -32.0, -30.0, -28.0):
        for reinf in (False, True):
            rods = screws(z) if reinf else ()
            s = sec(rects(z, kind), rods)
            sig = M(z) * 1.3 / s["Z"] * s["share_resin"]
            key = f"{kind} z {z}{' + M3 screws' if reinf else ''}"
            out[key] = dict(M_Nmm=round(M(z)), n_screws=len(rods), **s, sigma_MPa=round(sig, 2), ok=sig <= 8.5)
            if rods:
                out[key]["screw_core_sigma_MPa"] = round(M(z) * (1 - s["share_resin"]) / len(rods) / (math.pi * D3 ** 3 / 32), 1)
            print(key, out[key])
# bond of the screw thread in resin (epoxy): axial force in the back screw at z -48 (steel share of the moment over the
# lever between the screw and the resin centroid ~ the screw takes F = sigma_s * A); development over 25 mm of thread
s = sec(rects(-48.0, "B2"), [38.0, 38.0])
F_screw = M(-48.0) * (1 - s["share_resin"]) / 2 / max(abs(38.0 - s["xc"]), 1.0)
tau = F_screw / (math.pi * 3.0 * 25.0)
out["bond"] = dict(F_axial_per_screw_N=round(F_screw, 1), tau_bond_MPa_over_25mm=round(tau, 3),
                   note="2K epoxy lap shear on resin ~5-10 MPa; thread interlock adds mechanical key")
print("bond", out["bond"])
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "column_b2.json"), "w"), indent=1)
