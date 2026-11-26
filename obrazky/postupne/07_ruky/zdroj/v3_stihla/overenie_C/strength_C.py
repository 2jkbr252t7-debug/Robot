"""overenie_C/strength_C.py - hand-level strength sanity of a 1.6 mm shell of variant C (vs the approved arm 0).
Sections are rasterised (0.02 mm pixels) from the exact asymmetric superellipse; the wall is the TRUE inward normal offset
(pixels within 1.6 of the outer contour).  Two section models:
  closed : cover glued to the inner half (best case, NOT the design: the cover is held by magnets)
  open   : the inner half A_vnut alone (x <= seam - 0.25), i.e. the cover carries nothing (design case, conservative)
Loads (T4 strength review, case L5): 10 N at the arm tip (72 mm from the axis), lateral (local x, towards / away from the
torso) and fore-aft (local y: reacted by the stop rib when the arm sits on a stop; otherwise the clutch slips at ~0.3 N).
Material (T4 review Z2): tough ABS-like resin UTS 35 MPa, E 1.8 GPa, allowable 12 MPa static, 6 MPa for abuse cases.
Drop: energy estimate (elastic capacity of the cantilever shell vs the impact energy), clearly only an order of magnitude."""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomC as G

T_WALL, PIX = 1.6, 0.02
UTS, E_MOD, ALLOW, ABUSE = 35.0, 1800.0, 12.0, 6.0
F_TIP, U_LOAD = 10.0, 0.97          # 10 N applied near the tip


def section_props(shp, u, model):
    c, ti, to, w = (float(v) for v in shp.sec(u))
    th = np.linspace(0, 2 * np.pi, 6000, endpoint=False)
    ring = shp.ring(u, th)[:, :2]
    tr = cKDTree(ring)
    xs = np.arange(c - ti - PIX, c + to + PIX, PIX); ys = np.arange(-w - PIX, w + PIX, PIX)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); X = X.ravel(); Y = Y.ravel()
    ins = shp.inside(np.c_[X, Y, np.full(len(X), -G.L * u)])
    X, Y = X[ins], Y[ins]
    d, _ = tr.query(np.c_[X, Y])
    m = d <= T_WALL
    if model == "open":
        m &= X <= c - 0.25
    X, Y = X[m], Y[m]
    dA = PIX * PIX
    A = len(X) * dA
    xc, yc = X.mean(), Y.mean()
    Iyy = ((X - xc) ** 2).sum() * dA          # lateral force (x) -> stress varies with x
    Ixx = ((Y - yc) ** 2).sum() * dA          # fore-aft force (y) -> stress varies with y
    cx = max(X.max() - xc, xc - X.min()); cy = max(np.abs(Y - yc).max(), 1e-9)
    per = np.sum(np.linalg.norm(np.diff(np.r_[ring, ring[:1]], axis=0), axis=1))
    return dict(u=u, A=A, xc=xc, Iyy=Iyy, Ixx=Ixx, cx=cx, cy=cy, perim=per, thick=ti + to, width=2 * w)


def arm_area_mass(shp):
    us = np.linspace(0.0005, 0.9995, 2000)
    per = []
    for u in us:
        th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
        r = shp.ring(u, th)[:, :2]
        per.append(np.sum(np.linalg.norm(np.diff(np.r_[r, r[:1]], axis=0), axis=1)))
    per = np.array(per)
    # meridian arc element: dz plus the change of the section size
    secs = np.array([shp.sec(u) for u in us])
    dz = G.L * np.gradient(us)
    dr = np.gradient(0.5 * (secs[:, 1] + secs[:, 2] + 2 * secs[:, 3]) / 2)
    area = float(np.sum(per * np.sqrt(dz ** 2 + dr ** 2)))
    return area, area * T_WALL * 1.18e-3       # g (shell only)


def run(vid):
    shp = G.SHAPE_C if vid == "C" else G.SHAPE_0
    out = dict(variant=vid, sections=[])
    us = np.round(np.arange(0.40, 0.905, 0.05), 3)
    for model in ("closed", "open"):
        for u in us:
            p = section_props(shp, float(u), model)
            lever = G.L * (U_LOAD - u)
            M = F_TIP * lever
            s_lat = M * p["cx"] / p["Iyy"]; s_fa = M * p["cy"] / p["Ixx"]
            out["sections"].append(dict(model=model, u=float(u), thick=round(p["thick"], 2), width=round(p["width"], 2),
                                        A=round(p["A"], 1), Iyy=round(p["Iyy"], 1), Ixx=round(p["Ixx"], 1),
                                        lever=round(lever, 1), s_lat_MPa=round(s_lat, 2), s_fa_MPa=round(s_fa, 2)))
    for model in ("closed", "open"):
        rows = [r for r in out["sections"] if r["model"] == model]
        out[f"max_{model}"] = dict(lateral=max(rows, key=lambda r: r["s_lat_MPa"]), fore_aft=max(rows, key=lambda r: r["s_fa_MPa"]))
    # cantilever (root at u 0.40 = edge of the hub backing, assumed rigid) : stiffness + elastic energy capacity at UTS
    uu = np.linspace(0.40, U_LOAD, 60)
    for model in ("closed", "open"):
        Iy, Ix, cx, cy = [], [], [], []
        for u in uu:
            p = section_props(shp, float(u), model)
            Iy.append(p["Iyy"]); Ix.append(p["Ixx"]); cx.append(p["cx"]); cy.append(p["cy"])
        Iy, Ix, cx, cy = map(np.array, (Iy, Ix, cx, cy))
        z = G.L * (uu - uu[0]); Lc = G.L * (U_LOAD - uu[0])
        res = {}
        for nm, I, cc in (("lateral", Iy, cx), ("fore_aft", Ix, cy)):
            # tip deflection for a unit force: integral of (Lc - z)^2 / (E I) dz
            f = (Lc - z) ** 2 / (E_MOD * I)
            comp = float(np.trapezoid(f, z))                       # mm / N
            lever = np.maximum(Lc - z, 1e-6)
            F_uts = float(np.min(UTS * I[:-1] / (cc[:-1] * lever[:-1])))   # tip force that reaches UTS somewhere
            F_6 = F_uts * ABUSE / UTS
            res[nm] = dict(k_N_per_mm=round(1 / comp, 1), F_at_UTS_N=round(F_uts, 0), F_at_6MPa_N=round(F_6, 1),
                           U_elastic_at_UTS_J=round(F_uts ** 2 * comp / 2 / 1000, 3), defl_10N_mm=round(10 * comp, 3))
        out[f"cantilever_{model}"] = res
    area, mass = arm_area_mass(shp)
    out["shell_area_mm2"] = round(area, 0); out["shell_mass_g"] = round(mass, 1)
    return out


if __name__ == "__main__":
    R = {v: run(v) for v in ("C", "0")}
    for v, o in R.items():
        print(f"\n== variant {v}: shell area {o['shell_area_mm2']} mm2, shell mass (1.6 wall) {o['shell_mass_g']} g")
        for model in ("closed", "open"):
            ml, mf = o[f"max_{model}"]["lateral"], o[f"max_{model}"]["fore_aft"]
            print(f"  {model:6s}: 10 N tip  lateral max {ml['s_lat_MPa']} MPa at u {ml['u']} (I {ml['Iyy']})   "
                  f"fore-aft max {mf['s_fa_MPa']} MPa at u {mf['u']} (I {mf['Ixx']})")
            print("          cantilever:", o[f"cantilever_{model}"])
    E_robot = 1.1 * 9.81 * 1.0
    for v, o in R.items():
        E_arm = (o["shell_mass_g"] + 6.0) / 1000 * 9.81 * 1.0
        R[v]["drop"] = dict(E_robot_1m_J=round(E_robot, 1), E_arm_alone_1m_J=round(E_arm, 3),
                            note="arm alone = shell + ~6 g hub/bearing/washer (assumed)")
        print(v, R[v]["drop"])
    json.dump(R, open(os.path.join(HERE, "strength_C.json"), "w"), indent=1)
