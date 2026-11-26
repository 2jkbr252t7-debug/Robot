"""B1 - printed gears, screws as shafts, common bearings.  Point models of every NEW / CHANGED drive part (LEFT side, frame B;
right = mirror x -> -x), built with the judge's geo.py helpers.  Kept from v2 (K3j): servo (earless) + pocket column, B1 = MR63
in the tongue, boss, plug envelope, arm placement dx -1.0.

Numbers (mm):
  pinion  12T printed, m 0.6667, PA 25, ha* 0.9, hf* 1.15, b 2.8 (gears.py) - envelope crown r 4.50 / heel root z -23.43 / toe z -20.47
  gear    18T printed, same tooth system - toe x 41.14, crown x 42.50 r 6.33, root x 43.64, back x 44.24
  vertical shaft (printed): hex 4 AF z -39.6..-36.1 in the coupler, D3 journal -36.1..-23.43 (tongue hole + MR63), D2.5 D-key in the pinion
  coupler (printed cup + bonded trimmed servo horn): r 4.5, z -43.7..-35.5
  arm shaft = standard DIN 912 M4x20 (8.8, fully threaded): head bearing face x 60.0 (head x 60.0..64.0, dk 7), tip x 40.0;
        printed 18T gear epoxied on its inner end, A1/A2 inner races bonded on the thread with Loctite 638 + activator
  A1 = MR74 x 44.54..47.04 (0.30 printed shim behind the gear), printed spacer sleeve, A2 = MR74 x 52.60..55.10 (inside the D10
        seat); outer races slip in a D7 bore entered from the cavity side, outboard shoulder at x 55.10
  plug: v2 envelope (neck r 11, body r 13.5, face recessed 1.0, ring D13 to x 52.5) but seat D10 now x 52.5..59.5 with the
        homing stop lug (x 52.5..55.0, r 5.0..6.6, 4.5 wide) ; 6700 at x 55.5..59.5 (outer race bonded in the arm hub)
  drive hub (printed, keyed on the tube D-end, clamped by the M2 screw): boss r 3.4 x 60.0..62.6, disc r 11.0 x 62.6..66.4,
        8 pockets for 5x2 magnets at r 8.0 behind a 0.25 skin ; friction face x 62.6 against a DIN 9021 M8 washer in the arm hub
  column: v2 pocket column, the D3 silver-steel rods replaced by bonded DIN 912 M3 screws (see column_b1.py)"""
import math
import numpy as np
import geo as G

YA, ZA, XV = G.YA, G.ZA, 39.0

PIN = dict(toe_z=-20.467, toe_r=2.752, crown_z=-22.667, crown_r=4.499, root_z=-23.425, root_r=3.362)
GEAR = dict(toe_x=41.141, toe_r=3.874, crown_x=42.501, crown_r=6.333, root_x=43.638, root_r=5.575, back_x=44.238)
COUP = dict(r=4.5, z=(-43.5, -35.5))
SHV = dict(hex_r=2.31, hex_z=(-39.6, -36.1), r=1.5, key_r=1.25)
A1 = dict(x=(44.54, 47.04)); A2 = dict(x=(52.60, 55.10))
SCREW = dict(r=2.0, x=(40.0, 60.0), head_r=3.5, head_x=(60.0, 64.0))          # DIN 912 M4x20
DRIVE = dict(boss_r=4.5, boss_x=(60.0, 62.6), r=11.0, x=(62.6, 65.9), mag_r=7.7, mag_n=8, skin=0.25)
GEAR_BACK_RELIEF = dict(r0=3.0, x=44.038)        # gear back face beyond r 3.0 relieved to x 44.04 (0.5 to the cavity end)
SEAT = dict(r=5.0, x=(52.5, 59.5)); RING = dict(r=6.5, x1=52.5)
LUG = dict(x=(52.5, 55.0), r=(5.0, 6.6), w=4.5)
B6700 = dict(ri=5.0, ro=7.5, x=(55.5, 59.5))
HUB = dict(rib_x=(53.0, 55.0), rib_r=(5.5, 8.5), bore_r=7.5, flange_x=(59.6, 60.6), washer=(5.25, 10.0, 60.6, 62.6),
           cav_r=11.5, wall=(11.5, 12.7, 60.6, 67.0))


def parts_b1(h=0.2):
    out = {}
    out["ROT_V_coupler"] = G.tube("z", XV, YA, 0, COUP["r"], *COUP["z"], h=h)
    out["ROT_V_shaft"] = np.concatenate([G.tube("z", XV, YA, 0, SHV["hex_r"], *SHV["hex_z"], h=h),
                                         G.tube("z", XV, YA, 0, SHV["r"], SHV["hex_z"][1], PIN["root_z"], h=h),
                                         G.tube("z", XV, YA, 0, SHV["key_r"], PIN["root_z"], PIN["toe_z"], h=h)])
    p = PIN
    # back face: annular relief r 1.95..3.6 recessed 0.2 over the MR63 shield + outer race (shim r 1.55..1.9 on the inner race only)
    out["ROT_V_pinion"] = G.rev([(p["toe_z"], 0.0), (p["toe_z"], p["toe_r"]), (p["crown_z"], p["crown_r"]),
                                 (p["root_z"], p["crown_r"]), (p["root_z"], 3.6), (p["root_z"] + 0.2, 3.6),
                                 (p["root_z"] + 0.2, 1.95), (p["root_z"], 1.95), (p["root_z"], 0.0)], "z", XV, YA, h)
    out["ROT_V_shim"] = G.tube("z", XV, YA, 1.55, 1.9, -23.85, p["root_z"], h=h)
    g = GEAR
    xr = GEAR_BACK_RELIEF["x"]
    out["ROT_A_gear"] = G.rev([(g["toe_x"], 0.0), (g["toe_x"], g["toe_r"]), (g["crown_x"], g["crown_r"]),
                               (g["root_x"], g["crown_r"]), (g["root_x"], g["root_r"]), (xr, g["root_r"]),
                               (xr, GEAR_BACK_RELIEF["r0"]), (g["back_x"], GEAR_BACK_RELIEF["r0"]), (g["back_x"], 0.0)],
                              "x", YA, ZA, h)
    out["ROT_A_shaft"] = G.tube("x", YA, ZA, 0, SCREW["r"], *SCREW["x"], h=h)        # M4x20 shank (name kept for chk.py)
    out["ROT_A_shim"] = G.tube("x", YA, ZA, 2.05, 2.9, g["back_x"], A1["x"][0], h=h)
    out["BRG_A1"] = G.tube("x", YA, ZA, 2.0, 3.5, *A1["x"], h=h)
    out["BRG_A2"] = G.tube("x", YA, ZA, 2.0, 3.5, *A2["x"], h=h)
    return out


def arm_side(h=0.2):
    """parts inside the arm (checked against the pebble, hub_b1.py) - ARM_* rotate with the arm, DRV_* with the drive,
    PLG_* are static plug features inside the arm"""
    out = {}
    out["PLG_ring"] = G.tube("x", YA, ZA, 2.3, RING["r"], 49.0, RING["x1"], h=h)
    out["PLG_seat"] = G.tube("x", YA, ZA, 2.5, SEAT["r"], *SEAT["x"], h=h)          # bore D5.0 (0.5 to the M4)
    # stop lug: sector of width w (mm, at r 5.8) centred at azimuth LUG_AZ (deg, 0 = +Y, 90 = +Z about the axis)
    out["PLG_lug"] = sector(LUG["r"][0], LUG["r"][1], LUG["x"][0], LUG["x"][1], LUG_AZ, LUG["w"] / 5.8, h)
    out["ARM_6700"] = G.tube("x", YA, ZA, B6700["ri"], B6700["ro"], *B6700["x"], h=h)
    out["ARM_rib"] = sector(HUB["rib_r"][0], HUB["rib_r"][1], HUB["rib_x"][0], HUB["rib_x"][1], RIB_AZ0, 4.0 / 7.0, h)
    out["ARM_hub_bore_wall"] = G.tube("x", YA, ZA, B6700["ro"], B6700["ro"] + 1.2, B6700["x"][0], HUB["flange_x"][1], h=h)
    out["ARM_flange"] = np.concatenate([G.tube("x", YA, ZA, 6.5, HUB["wall"][1], B6700["x"][1], HUB["flange_x"][1], h=h),
                                        G.tube("x", YA, ZA, 5.0, 6.5, 60.0, HUB["flange_x"][1], h=h)])
    out["ARM_washer"] = G.tube("x", YA, ZA, HUB["washer"][0], HUB["washer"][1], HUB["washer"][2], HUB["washer"][3], h=h)
    out["ARM_wall"] = G.tube("x", YA, ZA, HUB["wall"][0], HUB["wall"][1], HUB["wall"][2], 67.6, h=h)
    out["DRV_boss"] = G.tube("x", YA, ZA, SCREW["head_r"], DRIVE["boss_r"], *DRIVE["boss_x"], h=h)
    out["DRV_disc"] = G.tube("x", YA, ZA, 0.0, DRIVE["r"], *DRIVE["x"], h=h)
    out["DRV_screw_head"] = G.tube("x", YA, ZA, 0, SCREW["head_r"], *SCREW["head_x"], h=h)
    out["DRV_screw_shank"] = G.tube("x", YA, ZA, 0, SCREW["r"], 55.6, SCREW["x"][1], h=h)
    out["ARM_lip"] = G.tube("x", YA, ZA, 4.0, 12.0, 66.4, 67.6, h=h)           # arm-hub outer wall behind the drive hub
    return out


LUG_AZ = 0.0        # set in hub_b1.py from the homing angle
RIB_AZ0 = 0.0


def sector(r0, r1, x0, x1, az_deg, half_width_rad, h=0.2):
    """solid annular sector about the shoulder axis; az measured from +Y toward +Z; full angular width 2*half? -> width"""
    xs = np.arange(x0, x1 + 1e-9, h)
    rs = np.arange(r0, r1 + 1e-9, h)
    pts = []
    a0 = math.radians(az_deg) - half_width_rad / 2; a1 = math.radians(az_deg) + half_width_rad / 2
    for r in rs:
        n = max(2, int((a1 - a0) * r / h) + 1)
        for a in np.linspace(a0, a1, n):
            for x in xs:
                pts.append((x, YA + r * math.cos(a), ZA + r * math.sin(a)))
    return np.array(pts)


if __name__ == "__main__":
    for k, v in {**parts_b1(), **arm_side()}.items():
        print("%-18s n %7d bbox %s" % (k, len(v), np.round(np.r_[v.min(0), v.max(0)], 2)))
