"""Judge's independent bevel-gear check (B1 vs B2) - polar bisection of a rack-generated tooth (NOT a raster),
Lewis with tip load along the line of action, Dolan-Broghamer Kf from the generated fillet curvature,
contact ratio, form radius vs start of active profile (tip/fillet interference), undercut.
Everything in module units for the virtual spur gear (Tredgold, mean section)."""
import math, json, sys
import numpy as np

def tooth(zv, alpha, x, ha, hf, rho, nR=500, nphi=5000):
    al = math.radians(alpha); ta = math.tan(al)
    r = zv / 2.0; ra = r + x + ha; rf = r + x - hf; rb = r * math.cos(al)
    dc = hf - rho; uc = math.pi / 4 - dc * ta - rho / math.cos(al); dt = dc + rho * math.sin(al)
    p = math.pi
    phis = np.linspace(-2.2 * 2 * math.pi / zv, 2.2 * 2 * math.pi / zv, nphi)
    c, s = np.cos(phis), np.sin(phis)
    def cut(R, th):
        # point in gear frame, tooth centre line = +y ; gear space centres at +y +- pitch/2 (cutter tooth at u = (k+1/2)p)
        X = R * math.sin(th); Y = R * math.cos(th)
        Xf = c * X - s * Y; Yf = s * X + c * Y
        u = Xf + r * phis; d = (r + x) - Yf
        du = np.abs(np.mod(u, p) - p / 2.0)   # distance to nearest cutter-tooth centre at p/2 + k p
        inflank = (d <= dt) & (du <= p / 4 - d * ta)
        inarc = (d > dt) & (d <= hf) & (du <= uc + np.sqrt(np.maximum(rho ** 2 - (d - dc) ** 2, 0)))
        return bool(np.any(inflank | inarc))
    Rs = np.linspace(rf + 1e-4, ra, nR)
    half = np.full(nR, np.nan)
    for i, R in enumerate(Rs):
        if cut(R, 0.0):
            continue
        lo, hi = 0.0, math.pi / zv * 1.2
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if cut(R, mid): hi = mid
            else: lo = mid
        half[i] = lo
    ok = ~np.isnan(half)
    Rs, half = Rs[ok], half[ok]
    xb = Rs * np.sin(half); yb = Rs * np.cos(half)
    # form radius (involute start) and undercut
    ufl = (dt - x) / math.sin(al)
    undercut = ufl > r * math.sin(al)
    rform = math.sqrt(rb ** 2 + max(r * math.sin(al) - ufl, 0) ** 2)
    return dict(r=r, ra=ra, rf=rf, rb=rb, Rs=Rs, half=half, xb=xb, yb=yb, rform=rform, undercut=bool(undercut), rho=rho, alpha=alpha)

def lewis(T, alpha):
    al = math.radians(alpha)
    xt, yt = T["xb"][-1], T["yb"][-1]; ra = T["ra"]; rb = T["rb"]
    alpha_a = math.acos(rb / ra); bt = math.atan2(xt, yt)
    gam = alpha_a - bt
    yL = yt - xt * math.tan(gam)
    # chord width as function of height y: for each y, narrowest x on the boundary at that height
    ys = np.linspace(T["yb"].min(), yL - 0.02, 2000)
    xb, yb = T["xb"], T["yb"]
    best = None
    for y in ys:
        # intersections of polyline with horizontal line y
        idx = np.nonzero((yb[:-1] - y) * (yb[1:] - y) <= 0)[0]
        if len(idx) == 0: continue
        xs = [xb[k] + (xb[k + 1] - xb[k]) * (y - yb[k]) / (yb[k + 1] - yb[k] + 1e-15) for k in idx]
        t = 2 * min(xs); l = yL - y
        Yraw = t * t / (6 * l)
        if best is None or Yraw < best[0]:
            best = (Yraw, t, l, y)
    Yraw, t, l, yc = best
    Ytipdir = Yraw * math.cos(al) / math.cos(gam)
    # fillet radius at the critical section: circle fit to the boundary within +-0.12 (module) of the critical height
    sel = np.abs(yb - yc) <= 0.12
    rF = float("nan")
    if sel.sum() >= 5:
        Xs, Ys = xb[sel], yb[sel]
        A = np.c_[2 * Xs, 2 * Ys, np.ones_like(Xs)]; bb = Xs ** 2 + Ys ** 2
        cx, cy, cc = np.linalg.lstsq(A, bb, rcond=None)[0]
        rF = float(math.sqrt(cc + cx * cx + cy * cy))
    phi = al
    H, L, M = 0.34 - 0.4583662 * phi, 0.316 - 0.4583662 * phi, 0.290 + 0.4583662 * phi
    Kf = H + (t / rF) ** L * (t / l) ** M
    Kf_rho = H + (t / T["rho"]) ** L * (t / l) ** M
    return dict(Y_tipdir=Ytipdir, Y_raw=Yraw, t=t, l=l, y_crit=yc, gamma_deg=math.degrees(gam), rF=rF, Kf=Kf, Kf_rho=Kf_rho,
                s_tip=2 * xt)

def pair(name, m, z1, z2, alpha, x1, ha, hf, rho, b):
    d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
    r1, r2 = m * z1 / 2, m * z2 / 2; R = math.hypot(r1, r2); f = 1 - 0.5 * b / R; mm = m * f
    zv1, zv2 = z1 / math.cos(d1), z2 / math.cos(d2)
    x2 = -x1
    T1 = tooth(zv1, alpha, x1, ha + 0, hf, rho) if True else None
    T2 = tooth(zv2, alpha, x2, ha, hf, rho)
    # NOTE: ha/hf are the basic-rack values; shift moves both tip and root
    L1, L2 = lewis(T1, alpha), lewis(T2, alpha)
    al = math.radians(alpha)
    # contact ratio virtual pair (module 1 units)
    a = T1["r"] + T2["r"] + (x1 + x2)
    eps = (math.sqrt(T1["ra"] ** 2 - T1["rb"] ** 2) + math.sqrt(T2["ra"] ** 2 - T2["rb"] ** 2) - a * math.sin(al)) / (math.pi * math.cos(al))
    # start of active profile on each member vs its form radius
    rsap1 = math.sqrt(T1["rb"] ** 2 + (a * math.sin(al) - math.sqrt(T2["ra"] ** 2 - T2["rb"] ** 2)) ** 2)
    rsap2 = math.sqrt(T2["rb"] ** 2 + (a * math.sin(al) - math.sqrt(T1["ra"] ** 2 - T1["rb"] ** 2)) ** 2)
    env = dict(pin_crown_r=r1 + (ha + x1) * m * math.cos(d1), pin_crown_z=-17 - (r2 - (ha + x1) * m * math.sin(d1)),
               pin_heel_root_z=-17 - (r2 + (hf - x1) * m * math.sin(d1)),
               pin_toe_z=-17 - ((R - b) * math.cos(d1) - (ha + x1) * m * (R - b) / R * math.sin(d1)),
               pin_toe_r=(R - b) * math.sin(d1) + (ha + x1) * m * (R - b) / R * math.cos(d1),
               gear_crown_r=r2 + (ha + x2) * m * math.cos(d2), gear_crown_x=39 + r1 - (ha + x2) * m * math.sin(d2),
               gear_root_x=39 + r1 + (hf - x2) * m * math.sin(d2),
               gear_toe_x=39 + (R - b) * math.cos(d2) - (ha + x2) * m * (R - b) / R * math.sin(d2))
    rm2 = r2 * f
    out = dict(name=name, m=m, z=(z1, z2), alpha=alpha, x1=x1, ha=ha, hf=hf, rho=rho, b=b, R=R, m_mean=mm, rm2=rm2, zv=(zv1, zv2),
               eps=eps, rform1=T1["rform"], rsap1=rsap1, rform2=T2["rform"], rsap2=rsap2, undercut=(T1["undercut"], T2["undercut"]),
               L1=L1, L2=L2, env=env, tip_land_heel_mm=(L1["s_tip"] * m, L2["s_tip"] * m),
               tip_land_toe_mm=(L1["s_tip"] * m * (R - b) / R, L2["s_tip"] * m * (R - b) / R))
    return out

def stresses(P, T_gear_Nmm):
    Ft = T_gear_Nmm / P["rm2"]
    res = {}
    for k, L in (("pin", P["L1"]), ("gear", P["L2"])):
        s_tip = Ft / (P["b"] * P["m_mean"] * L["Y_tipdir"]); s_raw = Ft / (P["b"] * P["m_mean"] * L["Y_raw"])
        res[k] = dict(lewis_tipdir=s_tip, lewis_raw=s_raw, tipdir_Kf=s_tip * L["Kf"], raw_Kf=s_raw * L["Kf"])
    return Ft, res

if __name__ == "__main__":
    B1 = pair("B1", 0.6667, 12, 18, 25.0, 0.0, 0.9, 1.15, 0.38, 2.8)
    B2 = pair("B2", 0.65, 12, 18, 25.0, 0.25, 1.0, 1.25, 0.38, 2.5)
    V2 = pair("v2printed", 0.5, 16, 24, 20.0, 0.0, 1.0, 1.25, 0.38, 2.4)
    out = {}
    for P in (B1, B2, V2):
        print("=== %s m %.4f z %s a %.0f x1 %+.2f b %.2f R %.3f m_mean %.4f rm2 %.3f zv %.2f/%.2f" % (P["name"], P["m"], P["z"], P["alpha"], P["x1"], P["b"], P["R"], P["m_mean"], P["rm2"], *P["zv"]))
        print("  eps %.3f  rform1 %.3f rsap1 %.3f  rform2 %.3f rsap2 %.3f undercut %s  tip land heel %.3f/%.3f toe %.3f/%.3f mm" % (P["eps"], P["rform1"], P["rsap1"], P["rform2"], P["rsap2"], P["undercut"], *P["tip_land_heel_mm"], *P["tip_land_toe_mm"]))
        for k in ("L1", "L2"):
            L = P[k]
            print("  %s Y(tip dir) %.4f  Y(raw Ft at tip) %.4f  t %.3f l %.3f gamma %.1f  rF %.3f Kf %.3f (Kf with rho %.3f)" % (k, L["Y_tipdir"], L["Y_raw"], L["t"], L["l"], L["gamma_deg"], L["rF"], L["Kf"], L["Kf_rho"]))
        print("  env", {k: round(v, 3) for k, v in P["env"].items()})
        out[P["name"]] = {k: v for k, v in P.items()}
    # cases
    cases = {
        "B1 need 4 Nmm": (B1, 4.0), "B1 running 8": (B1, 8.0), "B1 slip 16 (coin upper)": (B1, 16.0), "B1 slip 17 (judge window upper)": (B1, 17.0),
        "B1 mu-drift 0.4 after calib (x1.6 of 16)": (B1, 25.6),
        "B2 need 4/(1-0.205)": (B2, 4.0 / 0.795), "B2 slip 13.4 dry mu0.25 -> 20.3 at gear": (B2, 13.4 / 0.659),
        "B2 slip 13.4 mu0.15": (B2, 13.4 / 0.795), "B2 jam 8% limit 27.1": (B2, 27.1),
    }
    out["cases"] = {}
    for nm, (P, T) in cases.items():
        Ft, r = stresses(P, T)
        print("%-45s T_gear %5.2f Ft %.2f  pin tipdir %.2f raw %.2f tipdir*Kf %.2f | gear tipdir %.2f raw %.2f tipdir*Kf %.2f" % (nm, T, Ft, r["pin"]["lewis_tipdir"], r["pin"]["lewis_raw"], r["pin"]["tipdir_Kf"], r["gear"]["lewis_tipdir"], r["gear"]["lewis_raw"], r["gear"]["tipdir_Kf"]))
        out["cases"][nm] = dict(T_gear=T, Ft=Ft, **r)
    # torque at the gear for 8.5 MPa
    for P in (B1, B2, V2):
        for basis in ("tipdir", "tipdir_Kf", "raw", "raw_Kf"):
            Ft1, r1 = stresses(P, 1.0)
            smax = max(r1["pin"]["lewis_" + basis] if not basis.endswith("Kf") else r1["pin"][basis], r1["gear"]["lewis_" + basis] if not basis.endswith("Kf") else r1["gear"][basis])
            print("%s gear torque at 8.5 MPa, basis %-10s: %.1f N.mm" % (P["name"], basis, 8.5 / smax))
    def conv(o):
        if isinstance(o, np.ndarray): return o.tolist()
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.bool_,)): return bool(o)
        return str(o)
    json.dump(out, open("/tmp/claude-0/gapwf/fin/R2c/vyber/gear_judge.json", "w"), indent=1, default=conv)
