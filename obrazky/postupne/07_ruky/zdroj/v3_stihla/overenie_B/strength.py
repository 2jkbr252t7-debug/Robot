"""Independent verifier (R3/overenie_B): shell strength sanity (hand / beam level) of the 1.6 mm resin arm shell, variant vs
the approved arm.  Thin-wall midline method on the analytic sections of variants.section():
  closed  = whole pebble shell (cover A_vonk acts together with A_vnut through the seam rim / lip)
  open    = A_vnut alone (the cover is only held by magnets and carries nothing) - worst case
Loads: 10 N at the tip (local z -70) laterally (towards the torso, local x) and fore-aft (local y; the clutch slips at about
0.3 N at the tip, so a 10 N fore-aft push only reaches the shell with the arm against a stop).
Allowables (project Z2, Elegoo Tough lower-bound UTS 25.8 MPa): normal 8.5, abuse 12.9 MPa; E 1800 MPa.
Drop: arm mass, local shell stiffness (Reissner shallow shell), energy estimate - order of magnitude only.
usage: strength.py -> strength.json"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armsurf as AS  # noqa: E402
VA = AS.VA
T = 1.6
E = 1800.0
NU = 0.38
RHO = 1.18e-3            # g/mm3 cured resin (listing 1.1-1.2)
F = 10.0
Z_TIP = -70.0


def section_curve(vid, u, n=1440):
    th = np.linspace(-np.pi, np.pi, n, endpoint=False)
    P = AS.surf_pt(vid, np.full(n, u), th)[:, :2]
    return th, P


def midline(P, t):
    """offset a closed CCW-or-CW polygon inward by t/2 along the vertex normals"""
    d1 = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    nrm = np.c_[d1[:, 1], -d1[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    c = P.mean(0)
    s = np.sign(np.sum((P - c) * nrm, axis=1)).mean()      # outward-pointing sign
    return P - s * nrm * t / 2


def props(Mpts, t, closed=True):
    seg = np.roll(Mpts, -1, 0) - Mpts if closed else np.diff(Mpts, axis=0)
    mid = (Mpts + np.roll(Mpts, -1, 0)) / 2 if closed else (Mpts[:-1] + Mpts[1:]) / 2
    ds = np.linalg.norm(seg, axis=1)
    A = float((t * ds).sum())
    xc, yc = (mid * (t * ds)[:, None]).sum(0) / A
    Iyy = float((t * ds * (mid[:, 0] - xc) ** 2).sum())        # about the axis || y (lateral load in x)
    Ixx = float((t * ds * (mid[:, 1] - yc) ** 2).sum())        # about the axis || x (fore-aft load in y)
    J = None
    if closed:                                                  # Bredt: J = 4 Am^2 t / s
        x, y = Mpts[:, 0], Mpts[:, 1]
        Am = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        J = 4 * Am ** 2 * t / ds.sum()
    else:
        J = float((ds * t ** 3).sum() / 3)
    return dict(A=A, xc=xc, yc=yc, Iyy=Iyy, Ixx=Ixx, J=J, s=float(ds.sum()))


def station(vid, u):
    th, P = section_curve(vid, u)
    M = midline(P, T)
    cl = props(M, T, True)
    # open: A_vnut alone = inner half (|th| >= pi/2) incl. the seam rim
    k = np.cos(th) <= 0
    order = np.argsort(np.where(th[k] < 0, th[k] + 2 * np.pi, th[k]))
    Mo = M[k][order]
    op = props(Mo, T, False)
    lever = (-VA.L * u) - Z_TIP
    Mb = F * lever                                              # N.mm
    out = dict(u=u, lever=round(lever, 2), M_Nmm=round(Mb, 1))
    for nm, pr in (("closed", cl), ("open_Avnut", op)):
        P2 = P if nm == "closed" else P[k]
        cx = float(np.abs(P2[:, 0] - pr["xc"]).max()); cy = float(np.abs(P2[:, 1] - pr["yc"]).max())
        out[nm] = dict(A=round(pr["A"], 2), Iyy=round(pr["Iyy"], 1), Ixx=round(pr["Ixx"], 1), J=round(pr["J"], 2),
                       sig_lateral=round(Mb * cx / pr["Iyy"], 2), sig_foreaft=round(Mb * cy / pr["Ixx"], 2))
    # open section, fore-aft load through the centre line: shear centre offset -> torsion (rough: e = distance between the
    # centroid and the web, x2 for a channel-like section)
    xw = float(P[k][:, 0].min())
    e = 2.0 * abs(op["xc"] - xw)
    tau = F * e * T / op["J"]
    out["open_Avnut"]["torsion_tau_if_cover_carries_nothing"] = round(tau, 2)
    out["open_Avnut"]["shear_centre_offset_est"] = round(e, 2)
    return out


def area_mass(vid):
    us = np.linspace(1e-4, 1 - 1e-4, 1500)
    A = 0.0
    prev = None
    for u in us:
        th, P = section_curve(vid, u, 720)
        P3 = np.c_[P, np.full(len(P), -VA.L * u)]
        if prev is not None:
            a = prev; b = P3
            A += 0.5 * np.linalg.norm(np.cross(np.roll(a, -1, 0) - a, b - a), axis=1).sum()
            A += 0.5 * np.linalg.norm(np.cross(np.roll(b, -1, 0) - b, np.roll(a, -1, 0) - b), axis=1).sum()
        prev = P3
    return A


OUT = {}
for vid in ("0", "B"):
    R = dict(stations=[station(vid, u) for u in (0.40, 0.50, 0.60, 0.70, 0.80, 0.90)])
    A = area_mass(vid)
    m_shell = A * T * RHO
    R["surface_mm2"] = round(A, 0); R["shell_mass_g"] = round(m_shell, 1)
    # flat-ness of the crown: radius of curvature of the section at the outer centre line and at the fore-aft edge (u 0.5)
    u = 0.5
    c, ti, to, w, ni, no = [float(np.asarray(v)) for v in VA.section(vid, u)]
    # chord-sagitta over +-5 mm across the crown (outer centre) and over +-2 mm at the edge
    def sag_R(yh):
        x0 = c + to; x1 = c + to * (1 - (yh / w) ** no) ** (1 / no)
        s = x0 - x1
        return (yh ** 2 + s ** 2) / (2 * s)
    R["crown_radius_pm5mm_u05"] = round(sag_R(5.0), 1)
    R["cover_depth_u05"] = round(to, 2); R["section_u05"] = dict(thick=round(ti + to, 2), width=round(2 * w, 2))
    OUT[vid] = R
    s = R["stations"]
    print(vid, "shell area", round(A), "mm2, shell mass", round(m_shell, 1), "g, crown R(+-5)", R["crown_radius_pm5mm_u05"])
    for st in s:
        print("  u %.2f M %6.1f  closed: lat %5.2f fa %5.2f | open A_vnut: lat %5.2f fa %5.2f tors %5.2f" % (
            st["u"], st["M_Nmm"], st["closed"]["sig_lateral"], st["closed"]["sig_foreaft"], st["open_Avnut"]["sig_lateral"],
            st["open_Avnut"]["sig_foreaft"], st["open_Avnut"]["torsion_tau_if_cover_carries_nothing"]))
# ---- drop estimates (order of magnitude)
D = {}
for vid in ("0", "B"):
    m_arm = OUT[vid]["shell_mass_g"] + 6.3 + 1.3 + 2.0           # + DIN 125 M12 washer 6.3 g, MR128ZZ 1.3 g, printed hub ~2 g
    Ekin = m_arm * 1e-3 * 9.81 * 1.0 * 1e3                           # N.mm from 1 m
    out = dict(arm_mass_g=round(m_arm, 1), E_1m_Nmm=round(Ekin, 1))
    for nm, Rloc in (("edge_R8", 8.0), ("crown", OUT[vid]["crown_radius_pm5mm_u05"])):
        k = 4 * E * T ** 2 / (Rloc * math.sqrt(3 * (1 - NU ** 2)))   # N/mm, point load on a shallow shell (Reissner)
        Fpk = math.sqrt(2 * k * Ekin)
        # plate-type bending stress under a blunt contact (r0 3 mm, support span 10 mm)
        sig = 3 * Fpk / (2 * math.pi * T ** 2) * ((1 + NU) * math.log(10 / 3.0) + 1)
        out[nm] = dict(R=round(Rloc, 1), k_Nmm=round(k, 0), F_peak_N=round(Fpk, 0), sig_local_MPa=round(sig, 0))
    D[vid] = out
    print(vid, "drop:", out)
OUT["drop_arm_alone_1m"] = D
OUT["robot_drop_1m_on_arm_Nmm"] = round(1.1 * 9.81 * 1000, 0)
json.dump(OUT, open(os.path.join(HERE, "strength.json"), "w"), indent=1)

# ---- tip deflection under the 10 N lateral push (cantilever from u 0.30 = edge of the hub region, rigid hub assumed)
DEF = {}
for vid in ("0", "B"):
    us = np.linspace(0.30, 0.97, 68)
    I_c, I_o = [], []
    for u in us:
        th, P = section_curve(vid, u, 720)
        M = midline(P, T)
        I_c.append(props(M, T, True)["Iyy"])
        k = np.cos(th) <= 0
        order = np.argsort(np.where(th[k] < 0, th[k] + 2 * np.pi, th[k]))
        I_o.append(props(M[k][order], T, False)["Iyy"])
    s = VA.L * us; s_tip = VA.L * 0.97
    out = {}
    for nm, I in (("closed", np.array(I_c)), ("open_Avnut", np.array(I_o))):
        f = (s_tip - s) ** 2 / (E * I)
        out[nm] = round(float(F * np.trapezoid(f, s)), 3)
    DEF[vid] = out
    print(vid, "tip deflection under 10 N lateral (mm, shell only):", out)
OUT["tip_deflection_10N_lateral_mm"] = DEF
json.dump(OUT, open(os.path.join(HERE, "strength.json"), "w"), indent=1)
