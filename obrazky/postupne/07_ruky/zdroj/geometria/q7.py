"""Q7: mass / CG / inertia of a 2.0 mm pebble shell (1.2 g/cm3) about the shoulder axis + servo torque estimates"""
import json
from armgeo import *
from math import gamma
RHO = 1.2e-3          # g/mm3
WALL = 2.0
h = 0.2
# analytic solid volume (superellipse n = 2.3 area = 4ab G(1+1/n)^2 / G(1+2/n))
n = 2.3; kA = 4 * gamma(1 + 1 / n) ** 2 / gamma(1 + 2 / n)
uu = np.linspace(0, 1, 200001); hw, ht = prof(uu)
V_solid = np.trapezoid(kA * hw * ht, uu) * L
# voxel integration of the shell in the local frame
xs = np.arange(-12.0, 12.0 + h, h) + h / 2; ys = np.arange(-17.5, 17.5 + h, h) + h / 2; zs = np.arange(-L, 0 + h, h) + h / 2
Ms = 0.0; Mv = 0.0; S1 = np.zeros(3); Ixx = 0.0; Vsol = 0.0
X, Y = np.meshgrid(xs, ys, indexing="ij"); X = X.ravel(); Y = Y.ravel()
for z in zs:
    P = np.column_stack([X, Y, np.full(len(X), z)])
    ins = inside_local(P)
    if not ins.any(): continue
    P = P[ins]; Vsol += len(P) * h ** 3
    sd = sdf_local(P, dmax=2.5)
    sh = sd > -WALL
    Q = to_world(P[sh])
    m = h ** 3 * RHO
    Ms += m * len(Q); S1 += m * Q.sum(0)
    Ixx += m * ((Q[:, 1] - SH_Y) ** 2 + (Q[:, 2] - ZS) ** 2).sum()
cg = S1 / Ms
r_cg = math.hypot(cg[1] - SH_Y, cg[2] - ZS)
Vs = Ms / RHO
print("solid pebble volume analytic %.0f mm3, voxel %.0f mm3" % (V_solid, Vsol))
print("shell 2.0: volume %.0f mm3 = %.2f cm3, mass %.2f g; CG world %s -> %.3f below the axis (radial %.3f), lateral x %.2f; I_axis %.0f g.mm2" %
      (Vs, Vs / 1000, Ms, cg.round(3), ZS - cg[2], r_cg, cg[0], Ixx))
g = 9.81
theta = math.pi / 2; T = 0.25
alpha = 4 * theta / T ** 2; wmax = 2 * theta / T
print("triangular profile 90 deg in 0.25 s: alpha %.2f rad/s2, peak omega %.2f rad/s (%.1f rpm, %.3f s/60deg at peak)" % (alpha, wmax, wmax * 60 / 2 / math.pi, math.radians(60) / wmax))
rows = []
for ms in (6.0, 10.0, 14.0):
    for lay, d in (("A on axis", 0.0), ("B 14 mm below", 14.0)):
        m_tot = Ms + ms + 3.0
        # gravity: shell CG at r_cg, servo at d, small parts at 0
        M_g = (Ms * r_cg + ms * d) / 1000 * g / 1000      # N.m  (g -> kg, mm -> m)
        I = (Ixx + ms * d ** 2) * 1e-9                    # kg.m2
        T_in = I * alpha
        rows.append(dict(servo_g=ms, layout=lay, mass_total_g=round(m_tot, 2), hold_Nm=round(M_g, 5), hold_kgcm=round(M_g / g * 100, 3),
                         I_kgm2=I, inertial_Nm=round(T_in, 5), peak_Nm=round(T_in + M_g, 5), peak_kgcm=round((T_in + M_g) / g * 100, 3)))
        print("servo %4.1f g %-14s total %.1f g | hold (arm horizontal) %.4f N.m = %.3f kg.cm | I %.3e kg.m2 -> I*alpha %.4f N.m | worst sum %.4f N.m = %.3f kg.cm" %
              (ms, lay, m_tot, M_g, M_g / g * 100, I, T_in, T_in + M_g, (T_in + M_g) / g * 100))
# box correction for a servo case on the axis (layout A): case inertia about the shaft (dims in the y-z plane L x W, shaft 'e' from the case centre)
for nm, (Lc, Wc, ms, s) in (("S1 6 g", (19.9, 8.8, 6.0, 4.7)), ("S3 10 g", (23.0, 12.0, 10.0, 6.0)), ("S2 14 g", (23.2, 12.2, 14.0, 5.9))):
    e = Lc / 2 - s
    Ib = ms * ((Lc ** 2 + Wc ** 2) / 12 + e ** 2)
    print("box correction %s: I_case about the shaft %.0f g.mm2 (%.1f %% of the shell) -> +%.5f N.m" % (nm, Ib, 100 * Ib / Ixx, Ib * 1e-9 * alpha))
json.dump(dict(V_solid=V_solid, V_shell=Vs, m_shell=Ms, cg=cg.tolist(), r_cg=r_cg, drop_cg=ZS - cg[2], I_gmm2=Ixx, alpha=alpha, wmax=wmax, rows=rows),
          open("q7_out.json", "w"), indent=1)
