"""B1: shoulder column under T4 load L5 (10 N along X at the 72 mm arm tip, arm at +135 -> M(z) = 10 (33.9 - z) N.mm, bending
about Y), column alone, Kt 1.3, allowable 8.5 MPa - same load model as the judge's column_calc.py, but with a proper
TRANSFORMED section (steel parts at their real x, neutral axis shifts) instead of the EI-share shortcut.
v2: 2 x D3 silver-steel rods at x 38.0 (needs cutting to 46 / 31 mm -> not allowed).
B1: bonded standard DIN 912 M3 x 40 in the BACK leg only, placed off the centroid at x 39.0 (y 12.35), head in a counterbore
in the column foot (z -78..-75), thread z -75..-35.  The FRONT leg cannot take a screw (cable slot x 37..41.5 / y -17.6..-14.6
at z -66.8..-63.2 below, strut only 4.0 wide above).  Steel M3: stress area 5.03 mm2, minor dia 2.39."""
import json, math
E_R, E_S = 2500.0, 200000.0
n = E_S / E_R


def section(rects, steel=()):
    """rects (x0,x1,y0,y1) resin ; steel = list of (x, A, I_own).  Returns transformed props for bending about Y."""
    A = sum((x1 - x0) * (y1 - y0) for x0, x1, y0, y1 in rects)
    Sx = sum((x1 - x0) * (y1 - y0) * (x0 + x1) / 2 for x0, x1, y0, y1 in rects)
    At = A + sum((n - 1) * a for _, a, _ in steel)           # hole filled by steel: (n-1) A
    xc = (Sx + sum((n - 1) * a * xs for xs, a, _ in steel)) / At
    I = sum((y1 - y0) * (x1 - x0) ** 3 / 12 + (x1 - x0) * (y1 - y0) * ((x0 + x1) / 2 - xc) ** 2 for x0, x1, y0, y1 in rects)
    It = I + sum((n - 1) * (io + a * (xs - xc) ** 2) for xs, a, io in steel)
    c = max(xc - min(r[0] for r in rects), max(r[1] for r in rects) - xc)
    return dict(A=round(A, 1), xc=round(xc, 2), I_tr=round(It, 1), c=round(c, 2))


def M(z):
    return 10.0 * (33.9 - z)


back_full = (34.4, 41.5, 9.2, 15.5); back_top = (34.4, 38.4, 9.2, 15.5)
front_leg = (34.4, 41.5, -20.0, -14.6)
def strut_at(z):
    """strut prism x 34.4..38.4, polygon (y,z): (-20,-44.5) (-9,-44.5) (-9,-21) (-13.5,-25) (-20,-38)"""
    if z <= -38.0: y0 = -20.0
    else: y0 = -20.0 + (z + 38.0) / 13.0 * 6.5
    return (34.4, 38.4, y0, -9.0)
low = [(31.5, 41.5, 9.2, 15.5), (32.7, 41.5, -20.0, -14.6), (30.5, 32.65, -14.6, 9.2)]
rod = lambda x: (x, math.pi * 1.5 ** 2, math.pi * 1.5 ** 4 / 4)
m3 = lambda x: (x, 5.03, math.pi * 2.39 ** 4 / 64)

cases = []
for z, rects, label in ((-66.5, low, "C-channel below deck"), (-72.0, low, "C-channel below deck"),
                        (-48.0, [back_full, front_leg], "legs beside servo top"),
                        (-44.0, [back_full, strut_at(-44.0)], "back leg + strut"),
                        (-40.0, [back_full, strut_at(-40.0)], "back leg + strut"),
                        (-36.0, [back_full, strut_at(-36.0)], "back leg + strut"),
                        (-33.0, [back_top, strut_at(-33.0)], "narrow back leg + strut"),
                        (-30.0, [back_top, strut_at(-30.0)], "narrow back leg + strut")):
    for tag, steel in (("resin only", ()),
                       ("v2 rods D3 @38.0 (back+front)", tuple([rod(38.0)] + ([rod(38.0)] if z <= -47.0 else [])) if z <= -32 else ()),
                       ("B1 M3x40 @39.0 back only", (m3(39.0),) if -75.0 <= z <= -35.0 else ())):
        s = section(rects, steel)
        sig = M(z) * s["c"] / s["I_tr"] * 1.3
        row = dict(z=z, where=label, steel=tag, M_Nmm=round(M(z)), **s, sigma_resin_MPa=round(sig, 2), ok=sig <= 8.5)
        if steel:
            xs = steel[0][0]
            row["steel_sigma_MPa"] = round(n * M(z) * abs(xs - s["xc"]) / s["I_tr"], 1)
            row["screw_force_N"] = round(n * M(z) * abs(xs - s["xc"]) / s["I_tr"] * steel[0][1], 1)
        cases.append(row)
        print(f"z {z:6.1f} {label:26s} {tag:32s} xc {s['xc']:6.2f} I_tr {s['I_tr']:8.1f}  sigma {sig:5.2f} MPa"
              + (f"  screw {row.get('screw_force_N', 0):6.1f} N" if steel else ""))
# bond: the M3 thread must develop the screw force over the embedment above / below the critical section
Fmax = max(r.get("screw_force_N", 0) for r in cases if r["steel"].startswith("B1"))
L_top = -35.0 - (-48.0)                 # embedment above the most loaded section (z -48)
tau = Fmax / (math.pi * 3.0 * L_top)
print(f"max screw force {Fmax:.0f} N ; bond length above z -48: {L_top:.0f} mm -> mean bond shear {tau:.2f} MPa "
      f"(2K epoxy on zinc-plated steel / resin: 5-10 MPa typical, unverified)")
json.dump(dict(cases=cases, bond=dict(F_max_N=Fmax, L_mm=L_top, tau_MPa=round(tau, 2))), open("column_b1.json", "w"), indent=1)
