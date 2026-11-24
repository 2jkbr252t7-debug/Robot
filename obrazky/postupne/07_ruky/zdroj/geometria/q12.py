"""Q1 frames + Q2 pebble table (left arm, rest pose, frame B)"""
from armgeo import *
np.set_printoptions(precision=3, suppress=True)
# --- Q1: replicate T3 arm_xf literally and compare with armgeo.to_world
def arm_xf_T3(P, sx=1):
    _, ht_att = S.arm_profile(U_ATT)
    A_loc = np.array([-float(ht_att) + 5.0, 0.0, -S.ARM_L * U_ATT])
    q = np.asarray(P, float) - A_loc
    a, b = math.radians(-SPLAY), math.radians(-SWING)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    q = q @ Ry.T @ Rx.T
    q = q + np.array([x_sh_T3 + 9.0, SH_Y, ZS]); q[..., 0] *= sx
    return q
P = np.random.default_rng(1).normal(size=(50, 3)) * 20
print("max |T3 arm_xf - armgeo.to_world| =", np.abs(arm_xf_T3(P) - to_world(P)).max(), "(x_sh T3 %.5f vs X_SH T4 %.3f)" % (x_sh_T3, X_SH_T4))
print("T3: TOP %.1f ZS %.2f SH_Y %.1f Z_BOT %.2f Z_BASE_TOP %.2f desk %.2f" % (TOP, ZS, SH_Y, Z_BOT, Z_BASE_TOP, Z_DESK))
A = a_loc(); print("A_loc (local) =", A, " ht_att = %.4f hw_att = %.4f" % (prof(U_ATT)[1], prof(U_ATT)[0]))
print("attach point world =", to_world(A))
for nm, p in (("top tip", [0, 0, 0]), ("bottom tip", [0, 0, -L]), ("centre u_att", [0, 0, -L * U_ATT]),
              ("inner surface centre u_att", [-prof(U_ATT)[1], 0, -L * U_ATT]), ("outer surface centre u_att", [prof(U_ATT)[1], 0, -L * U_ATT])):
    w = to_world(np.array(p, float)); r = math.hypot(w[1] - SH_Y, w[2] - ZS)
    print("%-28s world %s  r from axis %.3f  drop below axis %.3f" % (nm, w, r, ZS - w[2]))
dirv = R @ np.array([0, 0, -1.0]); print("arm long-axis direction (world):", dirv, "angle to -Z %.3f deg; in y-z plane %.3f deg fwd" %
      (math.degrees(math.acos(-dirv[2])), math.degrees(math.atan2(-dirv[1], -dirv[2]))))
print("local x (thickness, outward) in world:", R @ np.array([1.0, 0, 0]), " local y (width):", R @ np.array([0, 1.0, 0]))
# base top
print("base: W %.1f D %.1f H %.1f top z %.2f, flat top region (e>=13): |x|<=%.1f |y|<=%.1f; underside of feet = desk z %.2f" %
      (S.BASE_W, S.BASE_D, S.BASE_H, Z_BASE_TOP, S.BASE_W / 2 - 13, S.BASE_D / 2 - 13, Z_DESK))

# --- Q2 table
def ray_x(y, z, kt=1.0, kw=1.0, inset=0.0, xr=(20.0, 110.0), n=40001):
    """entry / exit x of the line || X through (y, z) with the pebble (analytic)"""
    xs = np.linspace(*xr, n)
    Q = np.column_stack([xs, np.full(n, y), np.full(n, z)])
    ins = inside_local(to_local(Q, kt), kt, kw, inset)
    if not ins.any():
        return None, None
    i = np.nonzero(ins)[0]
    return xs[i[0]], xs[i[-1]]

us = list(np.round(np.arange(0.05, 0.951, 0.05), 3))
uu = np.linspace(0, 1, 200001)
hw_all, ht_all = prof(uu)
u_t = float(uu[ht_all.argmax()]); u_w = float(uu[hw_all.argmax()])
print("max thickness 2ht = %.3f at u %.4f (z_local %.2f); max width 2hw = %.3f at u %.4f; nominal ARM_T %.1f ARM_W %.1f" %
      (2 * ht_all.max(), u_t, -L * u_t, 2 * hw_all.max(), u_w, S.ARM_T, S.ARM_W))
us = sorted(set(us + [U_ATT, round(u_t, 4), round(u_w, 4)]))
rows = []
print(" u      drop_ax  r_ax   thick  width | station-normal x_in x_out | horiz-line x_in x_out (centre pt y,z)")
for u in us:
    hw, ht = prof(u)
    c = to_world(np.array([0, 0, -L * u]))
    xi = to_world(np.array([-ht, 0, -L * u]))[0]; xo = to_world(np.array([ht, 0, -L * u]))[0]
    a, b = ray_x(c[1], c[2])
    r = math.hypot(c[1] - SH_Y, c[2] - ZS)
    rows.append(dict(u=u, dist_below_axis_mm=round(ZS - c[2], 2), r_from_axis=round(r, 2), thickness_mm=round(2 * ht, 2), width_mm=round(2 * hw, 2),
                     x_inner=round(a, 2), x_outer=round(b, 2), x_in_st=round(xi, 2), x_out_st=round(xo, 2), y=round(c[1], 2), z=round(c[2], 2)))
    print("%.4f %7.2f %7.2f %6.2f %6.2f | %7.2f %7.2f | %7.2f %7.2f  (%.2f, %.2f)" % (u, ZS - c[2], r, 2 * ht, 2 * hw, xi, xo, a, b, c[1], c[2]))
import json; json.dump(rows, open("q2_table.json", "w"), indent=1)
# on the shoulder axis
a, b = ray_x(SH_Y, ZS); print("ON THE SHOULDER AXIS: pebble inner x %.3f outer x %.3f (span %.3f)" % (a, b, b - a))
# extremes in world
T = to_world(pebble_cloud(0.3))
print("pebble world bbox:", T.min(0), T.max(0))
i = T[:, 0].argmax(); print("max x (lateral reach) %.3f at" % T[i, 0], T[i], " min x %.3f" % T[:, 0].min(), T[T[:, 0].argmin()])
print("lowest point z %.3f at" % T[:, 2].min(), T[T[:, 2].argmin()], "-> above base top %.2f, above desk %.2f" % (T[:, 2].min() - Z_BASE_TOP, T[:, 2].min() - Z_DESK))
