"""B2 (max print): point models of every NEW / CHANGED drive part, LEFT side, frame B (right = mirror x -> -x).
Same conventions as the judge's geo.py (dense solid samples; ROT_* rotate, STAT_* static, SERVO*).
Changes vs v2 (judge-final K3):
  * printed bevel pair m 0.65, z 12/18, alpha 25 deg, x +0.25/-0.25, b 2.5, apex O = (39, 3, -17)  (v2: brass m0.5 16/24)
  * printed one-piece PINION-SHAFT: printed 20T spline coupler r 3.5 z -43.5..-40.0 | shaft D4 | collar r 3.0 z -24.05..-23.21 |
    pinion.  Hangs on its collar on the printed U-insert (no steel shaft, no MR63, no brass coupler, no grub screw)
  * tongue = C open to +X, r 3.2..4.6 (v2: closed ring r 3.0..4.4 with MR63); printed U-insert r 2.05..3.2 (journal D4.1)
  * plug keeper finger (closes the insert opening, 0.5 to the shaft) + hold-down post 0.5 above the pinion toe
  * boss slot widened to |y-3| <= 5.1 (pinion crown r 4.58)
  * printed GEAR-SPINDLE (gear + D8 journals in the plug ring bore D8.1, x 44.21..61.0 + hex stub to 62.2) instead of the
    steel D4 shaft + 2x MR74 + e-clip
  * back leg widened toward -Y to y 7.5 above the servo top (z -44.5..-26) for the column with screws (column_b2.py)
  * servo hangs on the pinion-shaft (no floor PORON); position as v2 (earless, top z -45.0)
The plug ring / arm hub / clutch disc are inside the arm and the plug (checked in armroom_b2.py, not against the torso)."""
import math
import numpy as np
import geo as G0

YA, ZA = 3.0, -17.0
XV = 39.0
box, tube, rev = G0.box, G0.tube, G0.rev
mirror = G0.mirror

B2 = dict(m=0.65, z1=12, z2=18, alpha=25.0, x1=0.25, b=2.5,
          coupler=dict(r=3.5, z=(-43.5, -40.0)), shaft=dict(r=2.0, z=(-40.0, -24.05)), collar=dict(r=2.7, z=(-24.05, None)),
          tongue=dict(ri=3.2, ro=4.6, z=(-26.85, -24.05)), insert=dict(ri=2.05, ro=3.2),
          keeper=(41.5, 44.0, 1.1, 4.9, -26.6, -24.6), post=(38.6, 40.0, 1.5, 4.5, None, -10.5),
          spindle=dict(r=4.0, x1=62.2), gear_web=0.5, lift=4.2,
          servo=dict(L=23.2, W=12.1, H=21.5, sh=5.9, z_top=-45.0, boss_r=3.5, boss_h=1.0, spl_r=1.975, spl_top=-40.25))


def bevel_b2(p=B2):
    m, z1, z2, b, x1 = p["m"], p["z1"], p["z2"], p["b"], p["x1"]
    x2 = -x1
    d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
    r1, r2 = m * z1 / 2, m * z2 / 2
    Re = math.hypot(r1, r2); k = (Re - b) / Re
    ha1, hf1 = (1 + x1) * m, (1.25 - x1) * m
    ha2, hf2 = (1 + x2) * m, (1.25 - x2) * m
    # pinion: axial distance below O
    cr1 = (r2 - ha1 * math.sin(d1), r1 + ha1 * math.cos(d1))
    rt1 = (r2 + hf1 * math.sin(d1), r1 - hf1 * math.cos(d1))
    cr2 = (r1 - ha2 * math.sin(d2), r2 + ha2 * math.cos(d2))
    rt2 = (r1 + hf2 * math.sin(d2), r2 - hf2 * math.cos(d2))
    pin = dict(toe_z=ZA - k * cr1[0], toe_r=k * cr1[1], crown_z=ZA - cr1[0], crown_r=cr1[1], root_z=ZA - rt1[0], root_r=rt1[1])
    gear = dict(toe_x=XV + k * cr2[0], toe_r=k * cr2[1], crown_x=XV + cr2[0], crown_r=cr2[1], root_x=XV + rt2[0], root_r=rt2[1])
    return dict(d1=math.degrees(d1), d2=math.degrees(d2), Re=Re, k=k, r1=r1, r2=r2, pin=pin, gear=gear)


def parts(p=B2, h=0.2, with_column=True):
    bv = bevel_b2(p)
    pi, ge = bv["pin"], bv["gear"]
    out = {}
    s = p["servo"]
    y0, y1 = YA - (s["L"] - s["sh"]), YA + s["sh"]
    x0, x1 = XV - s["W"] / 2, XV + s["W"] / 2
    zt = s["z_top"]; zb = zt - s["H"]
    out["SERVO"] = np.concatenate([box(x0, x1, y0, y1, zb, zt, 0.3),
                                   tube("z", XV, YA, 0, s["boss_r"], zt, zt + s["boss_h"], h),
                                   tube("z", XV, YA, 0, s["spl_r"], zt + s["boss_h"], s["spl_top"], h)])
    out["SERVO_cable"] = box(XV - 2.0, XV + 2.0, y0 - 3.0, y0, zb, zb + 3.0, 0.25)
    c = p["coupler"]
    out["ROT_V_coupler"] = tube("z", XV, YA, 0, c["r"], c["z"][0], c["z"][1], h)
    out["ROT_V_shaft"] = tube("z", XV, YA, 0, p["shaft"]["r"], p["shaft"]["z"][0], p["shaft"]["z"][1], h)
    out["ROT_V_collar"] = tube("z", XV, YA, 0, p["collar"]["r"], p["collar"]["z"][0], pi["root_z"], h)
    prof = [(pi["toe_z"], 0.0), (pi["toe_z"], pi["toe_r"]), (pi["crown_z"], pi["crown_r"]), (pi["root_z"], pi["crown_r"]),
            (pi["root_z"], 0.0)]
    out["ROT_V_pinion"] = rev(prof, "z", XV, YA, h)
    gb = ge["root_x"] + p["gear_web"]
    prof = [(ge["toe_x"], 0.0), (ge["toe_x"], ge["toe_r"]), (ge["crown_x"], ge["crown_r"]), (ge["root_x"], ge["crown_r"]),
            (ge["root_x"], ge["root_r"]), (gb, ge["root_r"]), (gb, 0.0)]
    out["ROT_A_gear"] = rev(prof, "x", YA, ZA, h)
    out["ROT_A_spindle"] = tube("x", YA, ZA, 0, p["spindle"]["r"], gb, p["spindle"]["x1"], h)
    # tongue C (open to +X) and the printed U-insert
    t = p["tongue"]
    T = tube("z", XV, YA, t["ri"], t["ro"], t["z"][0], t["z"][1], h)
    T = T[~((T[:, 0] > XV) & (np.abs(T[:, 1] - YA) < t["ri"]))]
    out["STAT_tongue"] = T
    ins = p["insert"]
    I = tube("z", XV, YA, ins["ri"], ins["ro"], t["z"][0], t["z"][1], h)
    I = I[~((I[:, 0] > XV) & (np.abs(I[:, 1] - YA) < ins["ri"]))]
    out["STAT_insert"] = I
    out["STAT_keeper"] = box(*p["keeper"], h=0.2)
    kp = p["post"]
    out["STAT_post"] = box(kp[0], kp[1], kp[2], kp[3], pi["toe_z"] + 0.5, kp[5], 0.2)
    # boss (solid r <= 12.8 minus slot |y-3| <= 5.1 for z -24.55..-15.5 and the shaft hole) - only the surface matters
    Bt = np.concatenate([tube("x", YA, ZA, 8.3, 12.8, 34.4, 38.4, h), tube("x", YA, ZA, 11.6, 12.8, 38.4, 39.1, h)])
    out["STAT_boss"] = Bt
    if with_column:
        out["STAT_leg_back"] = np.concatenate([box(34.4, 41.5, 9.2, 15.5, -72.0, -33.0, 0.3), box(34.4, 38.4, 9.2, 15.5, -33.0, -26.0, 0.3),
                                               box(31.5, 34.4, 9.2, 15.5, -72.0, -48.5, 0.3)])
        out["STAT_leg_back_ext"] = np.concatenate([box(34.4, 41.5, 7.5, 9.2, -44.5, -33.0, 0.25), box(34.4, 38.4, 7.5, 9.2, -33.0, -26.0, 0.25)])
        out["STAT_leg_front"] = np.concatenate([box(34.4, 41.5, -20.0, -14.6, -72.0, -44.5, 0.3), box(32.7, 34.4, -20.0, -14.6, -72.0, -48.5, 0.3)])
        out["STAT_web"] = box(30.5, 32.65, -14.6, 9.2, -72.0, -48.5, 0.3)
        out["STAT_strut"] = box(34.4, 38.4, -20.0, -9.0, -44.5, -25.0, 0.3)
        out["STAT_pad"] = box(32.65, 44.0, -14.6, 9.2, -69.0, -66.8, 0.3)
    return out, bv


def lifted(P, dz):
    Q = P.copy(); Q[:, 2] += dz
    return Q


if __name__ == "__main__":
    P, bv = parts()
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in bv.items()})
    for k, v in P.items():
        print("%-18s n %7d bbox %s" % (k, len(v), np.round(np.r_[v.min(0), v.max(0)], 2)))
