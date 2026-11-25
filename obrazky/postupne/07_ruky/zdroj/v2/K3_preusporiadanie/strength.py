"""K3 hand estimates (Lewis bending at the mean radius for straight bevels, shafts, bearings, ring, column legs).  -> strength.json"""
import math, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
m, z1, z2, F = 0.5, 16, 24, 2.4
r1, r2 = m * z1 / 2, m * z2 / 2; d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1; Re = math.hypot(r1, r2)
k = 1 - 0.5 * F / Re; mm = m * k; rm1, rm2 = r1 * k, r2 * k
zv1, zv2 = z1 / math.cos(d1), z2 / math.cos(d2)
def Y(z):   # Lewis form factor (20 deg full depth), interpolated table
    T = [(12, .245), (14, .277), (16, .296), (18, .309), (20, .322), (24, .337), (28, .353), (34, .371), (40, .389), (50, .408)]
    for (a, ya), (b, yb) in zip(T, T[1:]):
        if a <= z <= b: return ya + (yb - ya) * (z - a) / (b - a)
    return T[-1][1]
out = dict(gear=dict(m=m, z=(z1, z2), ratio=z2 / z1, face=F, Re=round(Re, 3), mean_module=round(mm, 3), rm=(round(rm1, 3), round(rm2, 3)),
                     z_virtual=(round(zv1, 1), round(zv2, 1)), Y=(round(Y(zv1), 3), round(Y(zv2), 3))))
rows = []
for T_arm in (0.01, 0.04, 0.06, 0.10, 0.15):
    Ft = T_arm / (rm2 / 1000)
    s1 = Ft / (F * mm * Y(zv1)); s2 = Ft / (F * mm * Y(zv2))
    rows.append(dict(T_arm_Nm=T_arm, Ft_N=round(Ft, 1), sigma_pinion_MPa=round(s1, 1), sigma_gear_MPa=round(s2, 1)))
out["lewis"] = rows
out["allowable_MPa"] = dict(POM_static_short=40, POM_fatigue=20, brass_C3604_static=100, steel_pinion=200)
T_slip = 0.06
Ft = T_slip / (rm2 / 1000); Fr1 = Ft * math.tan(math.radians(20)) * math.cos(d1); Fa1 = Ft * math.tan(math.radians(20)) * math.sin(d1)
Fr2, Fa2 = Fa1, Fr1
out["mesh_forces_at_slip_N"] = dict(Ft=round(Ft, 1), pinion_radial=round(Fr1, 1), pinion_axial_down=round(Fa1, 1),
                                     gear_radial=round(Fr2, 1), gear_axial_outboard=round(Fa2, 1))
# vertical shaft d3: torque + bending over 3.5 mm overhang above B1
Tp = T_slip / (z2 / z1) * 1000
Fres = math.hypot(Ft, Fr1)
out["vertical_shaft_d3"] = dict(torque_Nmm=round(Tp, 1), tau_MPa=round(16 * Tp / (math.pi * 27), 1),
                                bending_Nmm=round(Fres * 3.5 + Fa1 * rm1, 1), sigma_MPa=round(32 * (Fres * 3.5 + Fa1 * rm1) / (math.pi * 27), 1))
Ta = T_slip * 1000
Mb = math.hypot(Ft, Fr2) * 3.5 + Fa2 * rm2
out["arm_shaft_d4"] = dict(torque_Nmm=Ta, tau_MPa=round(16 * Ta / (math.pi * 64), 1), bending_Nmm=round(Mb, 1), sigma_MPa=round(32 * Mb / (math.pi * 64), 1))
# bearings: radial loads at slip (A1 near the gear carries ~ all, A2 small)
out["bearings_at_slip_N"] = dict(B1_radial=round(Fres * 1.3, 1), B1_axial=round(Fa1, 1), A1_radial=round(math.hypot(Ft, Fr2) * 1.6, 1),
                                 A1_axial=round(Fa2, 1), note="MR63ZZ C ~ 0.3 kN, C0 ~ 0.1 kN; MR74ZZ C ~ 0.4 kN, C0 ~ 0.15 kN (catalogue order of magnitude)")
# ring (resin) under an arm side push: 10 N radial at the 6700 (x 56) -> root at the plug face x 45.8
F_side = 10.0; lever = 56.0 - 45.8
Zr = math.pi * (13 ** 4 - 7 ** 4) / (32 * 13); Zs = math.pi * (10 ** 4 - 4.6 ** 4) / (32 * 10)
out["ring_resin"] = dict(side_push_N=F_side, M_root_Nmm=round(F_side * lever, 1), sigma_root_MPa=round(F_side * lever / Zr, 2),
                         sigma_seat_neck_MPa=round(F_side * 4.0 / Zs, 2), note="Elegoo Tough ~ 30-40 MPa tensile; creep limit ~ 5-8 MPa")
# arm pushed toward the torso at the tip (60 mm below the axis): moment carried by 6700 + A1/A2 couple
M_tip = 10 * 60.0
out["arm_tip_push_10N_along_X"] = dict(moment_Nmm=M_tip, couple_6700_to_A1_mm=56.0 - 45.8, bearing_force_N=round(M_tip / (56.0 - 45.8), 1),
                                       note="before that the arm touches the torso (gap 1-4 mm) and the load goes into the shell")
# column legs: 10 N at the shoulder (z -17), legs fixed at the floor (z -82.3): two legs 7.6 x 6
L = 82.3 - 17.0; b, t = 7.6, 6.0
I1 = b * t ** 3 / 12; I2 = t * b ** 3 / 12
out["column_legs"] = dict(load_N=10, lever_mm=round(L, 1), sigma_bend_Y_MPa=round(10 * L / 2 * (t / 2) / I1, 1),
                          sigma_bend_X_MPa=round(10 * L / 2 * (b / 2) / I2, 1), note="cantilever per leg, half the load each, no help from the shell or the servo")
# clutch
mu, rmf, n = 0.12, 3.6e-3, 2
out["clutch"] = dict(T_slip_target_Nm=T_slip, faces=n, mu_greased_steel_brass=mu, r_mean_mm=3.6,
                     preload_N=round(T_slip / (n * mu * rmf), 0), check="spring scale 1.0-1.4 N at 50 mm from the axis")
# servo
out["servo"] = dict(stall_5V_Nm=0.19, at_arm_stall_Nm=round(0.19 * z2 / z1, 3), arm_need_Nm=0.004, homing_torque_limit_pct=15,
                    homing_at_arm_Nm=round(0.19 * 0.15 * z2 / z1, 3), arm_range_deg=round(300 / (z2 / z1), 0), resolution_deg=round(0.293 / (z2 / z1), 3))
json.dump(out, open(os.path.join(HERE, "strength.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
