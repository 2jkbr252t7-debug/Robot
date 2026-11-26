"""Lewis tooth-root bending check of a straight bevel pair (Sigma 90 deg) printed in resin.
sigma = Ft_mean / (b * m_mean * Y(z_v)),  Y = Lewis form factor (20 deg full depth, load at tip, Shigley tab. 14-2),
z_v = z / cos(delta).  Ft_mean = T_gear / r_mean_gear.  Simple, conservative-ish (no load sharing, Kv = 1)."""
import math, json
import numpy as np
YT = {12:.245,13:.261,14:.277,15:.290,16:.296,17:.303,18:.309,19:.314,20:.322,21:.328,22:.331,24:.337,
      26:.346,28:.353,30:.359,34:.371,38:.384,43:.397,50:.409,60:.422,75:.435,100:.447,150:.460,300:.472}
ks = np.array(sorted(YT)); vs = np.array([YT[k] for k in ks])
Y = lambda z: float(np.interp(z, ks, vs))
UTS = 32.1      # Elegoo Tough, tensile (Amazon.de listing, +-10 %)
ALLOW = 8.5     # project allowable
cases = {"arm need 0.004": 0.004, "homing limit 15 % (0.043 at arm)": 0.043, "clutch 0.06": 0.06}
pairs = [  # (label, m, z1 pinion, z2 gear, b)
    ("K3 m0.5 16/24 b2.4", 0.5, 16, 24, 2.4),
    ("m0.6 13/20 b2.4", 0.6, 13, 20, 2.4),
    ("m0.75 11/16 b2.4", 0.75, 11, 16, 2.4),
    ("m0.8 10/15 b2.4", 0.8, 10, 15, 2.4),
    ("m0.5 16/24 b3.0", 0.5, 16, 24, 3.0),
    ("m0.6 16/24 b2.9 (d 9.6/14.4, bigger)", 0.6, 16, 24, 2.9),
    ("miter m0.5 16/16 b2.4", 0.5, 16, 16, 2.4),
]
out = []
for lab, m, z1, z2, b in pairs:
    d1, d2 = m*z1, m*z2
    g1 = math.atan2(z1, z2); g2 = math.pi/2 - g1
    R = 0.5*math.hypot(d1, d2)
    f = 1 - 0.5*b/R
    mm = m*f; rm2 = 0.5*d2*f
    zv1, zv2 = z1/math.cos(g1), z2/math.cos(g2)
    row = dict(pair=lab, d1=d1, d2=d2, cone_R=round(R,2), b_over_R=round(b/R,2), m_mean=round(mm,3), zv1=round(zv1,1), zv2=round(zv2,1),
               Y1=round(Y(zv1),3), Y2=round(Y(zv2),3), toe_module=round(m*(1-b/R),3),
               tooth_height_px_19um=round(2.25*m/0.019,0))
    for cl, T in cases.items():
        Ft = T*1000/rm2  # N  (T in N.m, r in mm)
        s1 = Ft/(b*mm*Y(zv1)); s2 = Ft/(b*mm*Y(zv2))
        row[cl] = dict(Ft_N=round(Ft,2), sigma_pinion_MPa=round(s1,1), sigma_gear_MPa=round(s2,1))
    # torque at the arm gear that gives ALLOW and UTS in the pinion
    Ft_allow = ALLOW*b*mm*Y(zv1); Ft_uts = UTS*b*mm*Y(zv1)
    row["T_arm_at_8.5MPa_Nm"] = round(Ft_allow*rm2/1000, 4)
    row["T_arm_at_UTS32_Nm"] = round(Ft_uts*rm2/1000, 4)
    out.append(row)
for r in out:
    print(f"{r['pair']:38s} R {r['cone_R']:5.2f} b/R {r['b_over_R']:.2f} zv {r['zv1']:5.1f}/{r['zv2']:5.1f} "
          f"need {r['arm need 0.004']['sigma_pinion_MPa']:5.1f}  home {r['homing limit 15 % (0.043 at arm)']['sigma_pinion_MPa']:5.1f}  clutch {r['clutch 0.06']['sigma_pinion_MPa']:5.1f} MPa | "
          f"T@8.5 {r['T_arm_at_8.5MPa_Nm']:.4f}  T@UTS {r['T_arm_at_UTS32_Nm']:.4f} N.m  toe m {r['toe_module']}")
json.dump(out, open('/tmp/claude-0/gapwf/fin/R2c/prieskum_tlacene/gear_lewis.json','w'), indent=1)
